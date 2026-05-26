"""Route chat messages to DB predictions, RAG (internal), and Gemini."""
from __future__ import annotations

import json

from ai_engine.gemini.client import GeminiClient
from ai_engine.rag.retriever import KnowledgeRetriever
from ai_engine.response_formatter import format_prediction_response, format_preference_list
from recommendation_engine.engine import PredictionEngine, PredictionRequest
from recommendation_engine.normalization import (
    normalize_category,
    normalize_rank_type,
    normalize_state,
    parse_rank_from_text,
)
from recommendation_engine.schemas import PredictionResponse


def _human_category_label(category: str | None) -> str:
    category_value = (category or "").strip().upper()
    labels = {
        "GENERAL": "General",
        "OBC": "OBC",
        "SC": "SC",
        "ST": "ST",
        "EWS": "EWS",
        "CRL": "Common Rank",
    }
    return labels.get(category_value, category_value.title().replace("_", " "))


def _human_quota_label(quota: str | None) -> str:
    quota_value = (quota or "").strip().upper()
    labels = {
        "OS": "Other-State",
        "HS": "Home-State",
        "AI": "All-India",
        "ALL_INDIA": "All India",
        "GQ": "General quota",
        "GE": "General",
    }
    return labels.get(quota_value, quota_value.title().replace("_", " "))


def _reference_cutoff_label(category: str | None, quota: str | None) -> str:
    category_label = _human_category_label(category)
    quota_label = _human_quota_label(quota)
    if category_label and quota_label:
        return f"{category_label} {quota_label}"
    return category_label or quota_label or "Verified cutoff"


def _confidence_reason(requested_category: str, selected_category: str) -> str:
    if selected_category.strip().upper() == requested_category.strip().upper():
        return "Verified category-specific cutoff available."
    if selected_category.strip().upper() == "GENERAL":
        return "General cutoff used as a benchmark because exact category data was unavailable."
    return "Fallback comparison used because exact category-specific cutoff could not be found."


def _build_cutoff_explanation(requested_category: str, selected_category: str, selected_quota: str) -> tuple[str, str, str]:
    label = _reference_cutoff_label(selected_category, selected_quota)
    requested_label = _human_category_label(requested_category)
    if selected_category.strip().upper() != requested_category.strip().upper():
        return (
            label,
            f"ℹ️ Verified {requested_label} cutoff data was unavailable for this branch, so the system used {label} as a reference benchmark.",
            _confidence_reason(requested_category, selected_category),
        )

    return (
        label,
        f"This comparison uses verified {label} data for your requested category and branch.",
        _confidence_reason(requested_category, selected_category),
    )


class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class ChatContext:
    def __init__(
        self,
        rank: int | None = None,
        category: str | None = None,
        gender: str = "GENDER_NEUTRAL",
        home_state: str = "",
        branch_preferences: list | None = None,
        year: int | None = None,
        exam_type: str | None = None,
        rank_type: str | None = None,
        round: str | None = None,
        student_goals: str = "",
        focused_college: str = "",
        sidebar_colleges: list | None = None,
        session_id: str | None = None,
        selected_card: dict | None = None,
    ):
        self.rank = rank
        self.category = category
        self.gender = gender
        self.home_state = home_state or ""
        self.branch_preferences = branch_preferences or []
        self.year = year
        self.exam_type = exam_type or "JEE_MAIN"
        self.rank_type = rank_type or "CRL"
        self.round = round or "LATEST"
        self.student_goals = student_goals or ""
        self.focused_college = focused_college or ""
        self.sidebar_colleges = sidebar_colleges or []
        self.session_id = session_id
        self.selected_card = selected_card


class CounsellingOrchestrator:
    def __init__(self):
        self.retriever = KnowledgeRetriever()
        self.gemini = GeminiClient()
        self.engine = PredictionEngine()

    def handle(
        self,
        message: str,
        context: ChatContext | None = None,
        history: list[ChatMessage] | None = None,
    ) -> dict:
        context = context or ChatContext()
        
        # 1. Intent Classification Router BEFORE RAG
        query_system_type = self._classify_query_system(message)
        intent = self._detect_intent(message)
        
        self._enrich_context_from_message(message, context)

        if not context.focused_college:
            context.focused_college = self._extract_college_from_message(
                message, context.sidebar_colleges
            )

        # 2. Entity Extraction
        entities = self._extract_entities(message, context)
        colleges = entities["colleges"]
        branches = entities["branches"]

        # Resolve PredictionSession data
        from counselling.models import PredictionSession, College, Cutoff
        from django.db.models import Q, Max
        session_obj = None

        if context.session_id:
            try:
                session_obj = PredictionSession.objects.get(id=context.session_id)
            except (PredictionSession.DoesNotExist, ValueError, TypeError):
                pass

        # If no session was found but we have enough info to run prediction, do it to create a session!
        prediction: PredictionResponse | None = None
        preference_payload: dict | None = None
        if not session_obj and context.rank and context.category:
            prediction = self._run_prediction(context)
            if prediction and prediction.session_id:
                try:
                    session_obj = PredictionSession.objects.get(id=prediction.session_id)
                except PredictionSession.DoesNotExist:
                    pass

            if intent == "preference":
                preference_payload = self._build_preference_list(context)
        elif session_obj:
            if intent == "preference":
                preference_payload = self._build_preference_list(context)

        # Reconstruct prediction response from session results if we don't have it already
        if session_obj and not prediction:
            results_data = session_obj.results or []
            from recommendation_engine.schemas import CollegePrediction, PredictionResponse

            reconstructed_preds = []
            for r in results_data:
                reconstructed_preds.append(
                    CollegePrediction(
                        college_id=r.get("college_id"),
                        college_name=r.get("college_name"),
                        category=r.get("category"),
                        state=r.get("state"),
                        program_id=r.get("program_id"),
                        program_name=r.get("program_name"),
                        branch=r.get("branch"),
                        year=r.get("year"),
                        round=r.get("round"),
                        seat_category=r.get("seat_category"),
                        quota=r.get("quota"),
                        gender=r.get("gender"),
                        opening_rank=r.get("opening_rank"),
                        closing_rank=r.get("closing_rank"),
                        tier=r.get("tier"),
                        margin=r.get("margin"),
                        probability_score=r.get("probability_score"),
                        rating=r.get("rating"),
                        recommendation_score=r.get("recommendation_score"),
                        why_recommended=r.get("why_recommended"),
                        avg_package_inr=r.get("avg_package_inr"),
                        fees_inr=r.get("fees_inr"),
                        placement_rate=r.get("placement_rate"),
                        ug_fee=r.get("ug_fee"),
                    )
                )

            prediction = PredictionResponse(
                rank=session_obj.rank,
                seat_category=session_obj.category,
                rank_type=session_obj.rank_type,
                gender=session_obj.gender,
                year=session_obj.year,
                home_state=session_obj.home_state,
                total_eligible=len(reconstructed_preds),
                all=reconstructed_preds,
                dream=[p for p in reconstructed_preds if p.tier == "DREAM"][:40],
                target=[p for p in reconstructed_preds if p.tier == "TARGET"][:40],
                safe=[p for p in reconstructed_preds if p.tier == "SAFE"][:40],
                unlikely=[p for p in reconstructed_preds if p.tier == "UNLIKELY"][:40],
                trace=session_obj.trace or {},
                session_id=str(session_obj.id),
            )

        # 3. Build Verified Cards (Structured Truth calculations on backend)
        verified_cards = []
        
        # Check if the user query mentions other colleges that do NOT match the selected card
        query_colleges = self._detect_mentioned_colleges(message)
        use_selected_card_context = False
        if context.selected_card and not query_colleges:
            use_selected_card_context = True

        if use_selected_card_context:
            card = context.selected_card
            col_name = card.get("college") or card.get("college_name", "")
            prog_name = card.get("program") or card.get("program_name", "")
            br_name = card.get("branch", "")
            
            # Resolve database object for profiling/scoring
            col_obj = College.objects.filter(canonical_name__icontains=col_name.strip()).first() if col_name else None
            colleges = [col_obj] if col_obj else []
            branches = [br_name]
            
            margin_val = 0
            c_rank = card.get("closing_rank")
            if c_rank and context.rank:
                margin_val = int(c_rank) - context.rank
                
            reference_label, cutoff_explanation, confidence_reason = _build_cutoff_explanation(
                context.category or "GENERAL",
                card.get("category") or context.category or "GENERAL",
                card.get("quota") or ""
            )
            confidence_level = (
                "HIGH" if (card.get("category") or context.category or "").strip().upper() == (context.category or "").strip().upper()
                else "MEDIUM"
            )
            verified_cards = [{
                "college_name": col_name,
                "program_name": prog_name,
                "branch": br_name,
                "user_rank": context.rank,
                "closing_rank": c_rank,
                "margin": margin_val,
                "classification": card.get("classification") or card.get("tier", "SAFE"),
                "round": card.get("round") or 5,
                "category": card.get("category") or context.category,
                "quota": card.get("quota") or "",
                "reference_cutoff_label": reference_label,
                "cutoff_explanation": cutoff_explanation,
                "confidence_level": confidence_level,
                "confidence_reason": confidence_reason,
            }]
        elif context.rank and context.category:
            category = normalize_category(entities["category"] or context.category)
            exam_type = context.exam_type or "JEE_MAIN"
            rank_type = context.rank_type or "CRL"
            year = context.year or self.engine._default_cutoff_year()

            if rank_type == "CRL":
                db_category = "GENERAL"
                db_rank_type = f"{exam_type}_CRL"
            else:
                db_category = category
                db_rank_type = f"{exam_type}_{category}"

            # Resolve Round
            round_val = entities["round"]
            if round_val and str(round_val).isdigit():
                resolved_round = int(round_val)
            else:
                max_round = Cutoff.objects.filter(year=year, exam_type=exam_type).aggregate(Max("round"))["round__max"]
                resolved_round = max_round or 5

            # Try finding matches from the prediction session first if it exists
            session_matches = []
            if session_obj:
                all_matches = session_obj.results or []
                for col in colleges:
                    col_name_lower = col.canonical_name.lower()
                    col_matches = [m for m in all_matches if col_name_lower in m.get("college_name", "").lower()]

                    if branches:
                        for br in branches:
                            for m in col_matches:
                                m_branch = (m.get("branch") or "").upper()
                                m_prog = (m.get("program_name") or "").upper()
                                match_ok = False
                                if br == "CSE":
                                    match_ok = "COMPUTER" in m_prog or "CSE" in m_branch
                                elif br == "ECE":
                                    match_ok = "ELECTRONICS" in m_prog or "ECE" in m_branch
                                elif br == "IT":
                                    match_ok = "INFORMATION" in m_prog or "IT" in m_branch
                                else:
                                    match_ok = br in m_branch or br in m_prog

                                if match_ok:
                                    session_matches.append(m)
                    else:
                        session_matches.extend(col_matches[:3])

            # Format session matches into verified cards
            for sm in session_matches:
                if not any(vc["program_name"] == sm.get("program_name") and vc["college_name"] == sm.get("college_name") for vc in verified_cards):
                    selected_category = sm.get("seat_category") or context.category or "GENERAL"
                    selected_quota = sm.get("quota") or ""
                    reference_label, cutoff_explanation, confidence_reason = _build_cutoff_explanation(
                        category,
                        selected_category,
                        selected_quota,
                    )
                    confidence_level = (
                        "HIGH" if selected_category.strip().upper() == category.strip().upper() else "MEDIUM"
                    )
                    verified_cards.append({
                        "college_name": sm.get("college_name"),
                        "program_name": sm.get("program_name"),
                        "branch": sm.get("branch"),
                        "user_rank": context.rank,
                        "closing_rank": sm.get("closing_rank"),
                        "margin": sm.get("margin"),
                        "classification": sm.get("tier"),
                        "round": sm.get("round"),
                        "category": selected_category,
                        "quota": selected_quota,
                        "reference_cutoff_label": reference_label,
                        "cutoff_explanation": cutoff_explanation,
                        "confidence_level": confidence_level,
                        "confidence_reason": confidence_reason,
                    })

            # Direct database query fallback for any mentioned colleges and branches not found in verified_cards
            for col in colleges:
                col_existing = [vc for vc in verified_cards if vc["college_name"] == col.canonical_name]

                if branches:
                    for br in branches:
                        is_found = False
                        for ec in col_existing:
                            ec_branch = (ec["branch"] or "").upper()
                            ec_prog = (ec["program_name"] or "").upper()
                            if br == "CSE":
                                is_found = "COMPUTER" in ec_prog or "CSE" in ec_branch
                            elif br == "ECE":
                                is_found = "ELECTRONICS" in ec_prog or "ECE" in ec_branch
                            elif br == "IT":
                                is_found = "INFORMATION" in ec_prog or "IT" in ec_branch
                            else:
                                is_found = br in ec_branch or br in ec_prog
                            if is_found:
                                break

                        if not is_found:
                            branch_terms = []
                            if br == "CSE":
                                branch_terms = ["COMPUTER", "CSE"]
                            elif br == "ECE":
                                branch_terms = ["ELECTRONICS", "ECE"]
                            elif br == "IT":
                                branch_terms = ["INFORMATION", "IT"]
                            else:
                                branch_terms = [br]

                            branch_q = Q()
                            for term in branch_terms:
                                branch_q |= Q(program__branch_canonical__icontains=term)
                                branch_q |= Q(program__program_name__icontains=term.replace("_", " "))
                                branch_q |= Q(program__program_name__icontains=term)

                            cutoffs_qs = Cutoff.objects.filter(
                                program__college=col,
                                year=year,
                                round=resolved_round,
                                category=db_category,
                                rank_type=db_rank_type,
                            ).filter(branch_q)

                            if context.gender == "FEMALE_ONLY":
                                cutoffs_qs = cutoffs_qs.filter(gender="FEMALE_ONLY")
                            else:
                                cutoffs_qs = cutoffs_qs.filter(gender="GENDER_NEUTRAL")

                            cstate = str(col.state).upper()
                            hstate = normalize_state(context.home_state or "").upper()

                            target_cutoffs = list(cutoffs_qs)
                            selected_cutoff = None
                            if target_cutoffs:
                                if exam_type == "JEE_MAIN" and hstate:
                                    if hstate == cstate:
                                        for tc in target_cutoffs:
                                            if tc.quota in ("HS", "AI"):
                                                selected_cutoff = tc
                                                break
                                    else:
                                        for tc in target_cutoffs:
                                            if tc.quota in ("OS", "AI"):
                                                selected_cutoff = tc
                                                break
                                if not selected_cutoff:
                                    selected_cutoff = target_cutoffs[0]

                            if selected_cutoff:
                                closing_rank = selected_cutoff.closing_rank
                                user_rank = context.rank
                                margin = closing_rank - user_rank
                                ratio = margin / max(closing_rank, 1)
                                if ratio < -0.10:
                                    tier = "UNLIKELY"
                                elif margin < 0:
                                    tier = "DREAM"
                                elif ratio <= 0.05:
                                    tier = "DREAM"
                                elif ratio <= 0.20:
                                    tier = "TARGET"
                                else:
                                    tier = "SAFE"

                                selected_category = selected_cutoff.category or "GENERAL"
                                selected_quota = selected_cutoff.quota or ""
                                reference_label, cutoff_explanation, confidence_reason = _build_cutoff_explanation(
                                    category,
                                    selected_category,
                                    selected_quota,
                                )
                                confidence_level = (
                                    "HIGH" if selected_category.strip().upper() == category.strip().upper() else "MEDIUM"
                                )

                                verified_cards.append({
                                    "college_name": col.canonical_name,
                                    "program_name": selected_cutoff.program.program_name,
                                    "branch": selected_cutoff.program.branch_canonical,
                                    "user_rank": user_rank,
                                    "closing_rank": closing_rank,
                                    "margin": margin,
                                    "classification": tier,
                                    "round": selected_cutoff.round,
                                    "category": selected_category,
                                    "quota": selected_quota,
                                    "reference_cutoff_label": reference_label,
                                    "cutoff_explanation": cutoff_explanation,
                                    "confidence_level": confidence_level,
                                    "confidence_reason": confidence_reason,
                                })

        # 3b. Load master_college_tiers.json and compute scoring metrics
        import json
        from pathlib import Path
        import re

        json_path = Path(__file__).resolve().parent / "master_college_tiers.json"
        tiers_data = {}
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    tiers_data = json.load(f)
            except Exception:
                pass

        # Calculate metrics for each card, attach to cards and inject into prompt
        scoring_parts = []
        for vc in verified_cards:
            col_name = vc["college_name"]
            col_obj = College.objects.filter(canonical_name=col_name).first()
            col_category = col_obj.category if col_obj else "Other"
            rating = col_obj.rating if col_obj else None

            metrics = self._get_college_metrics(col_name, tiers_data, col_category, rating)
            vc["metrics"] = metrics

            scoring_parts.append(
                f"COLLEGE_RECO_METRICS for '{col_name}': "
                f"Tier: {metrics.get('tier')}, "
                f"Coding Score: {metrics.get('coding_score')}/10, "
                f"Placement Score: {metrics.get('placement_score')}/10, "
                f"ROI Score: {metrics.get('roi_score')}/10, "
                f"Reputation Score: {metrics.get('reputation_score')}/10, "
                f"Alumni Network: {metrics.get('alumni_score')}/10, "
                f"Campus Life: {metrics.get('campus_score')}/10."
            )

        # 4. Strict "No Data Found" check
        strict_no_data = False
        if query_system_type == "SQL" and colleges and not verified_cards:
            strict_no_data = True

        structured_parts: list[str] = []
        if context.student_goals:
            structured_parts.append(f"GOALS:{context.student_goals}")

        if strict_no_data:
            structured_parts.append("VERIFIED_CUTOFF_DATA: UNAVAILABLE")

        # Inject metrics into structured prompt parts
        for sp in scoring_parts:
            structured_parts.append(sp)

        # 5. Inject verified database facts into prompt structured parts
        mentioned_colleges = self._detect_mentioned_colleges(message)
        fact_check_logs = []
        for college in mentioned_colleges:
            programs = list(college.programs.all())
            program_tuples = [(p.program_name, p.branch_canonical) for p in programs]

            fact_check_logs.append(
                f"VERIFIED_DATABASE_TRUTH: College '{college.canonical_name}' offers exactly "
                f"the following programs: {[{'name': p[0], 'branch': p[1]} for p in program_tuples]}. "
                f"It offers NO other programs or branches."
            )

            # Detect queried branches in user question
            lower_msg = message.lower()
            queried_branches = []
            for b in ["CSE", "IT", "ECE", "EEE", "ME", "CE", "CHE", "AE", "AI", "DS"]:
                if b.lower() in lower_msg or b in message:
                    queried_branches.append(b)

            # Check for non-existent branches asked by user
            for qb in queried_branches:
                if qb == "IT":
                    has_it = any("INFORMATION TECHNOLOGY" in p[0].upper() or p[1] == "IT" for p in program_tuples)
                    if not has_it:
                        fact_check_logs.append(
                            f"FACT_CHECK_WARNING: Student asked about 'IT' branch at '{college.canonical_name}'. "
                            f"Our verified database shows that '{college.canonical_name}' does NOT offer an 'IT' branch! "
                            f"You MUST clearly state in the verdict that it does not offer IT, "
                            f"and suggest related available branches like Computer Science and Engineering."
                        )
                elif qb == "CSE":
                    has_cse = any("COMPUTER SCIENCE" in p[0].upper() or p[1] == "CSE" or p[1] == "COMPUTER_SCIENCE_AND_ENGINEERING" for p in program_tuples)
                    if not has_cse:
                        fact_check_logs.append(
                            f"FACT_CHECK_WARNING: Student asked about 'CSE' branch at '{college.canonical_name}'. "
                            f"Our verified database shows that '{college.canonical_name}' does NOT offer a 'CSE' branch!"
                        )

        for log in fact_check_logs:
            structured_parts.append(log)

        # 6. Inject verified prediction session matches into context
        if session_obj:
            # Map original verified matches for LLM representation
            verified_matches = []
            all_matches = session_obj.results or []
            for m in all_matches:
                verified_matches.append({
                    "institute": m.get("college_name"),
                    "branch": m.get("program_name"),
                    "closing_rank": m.get("closing_rank"),
                    "category": m.get("seat_category"),
                    "round": m.get("round"),
                    "confidence": m.get("tier"),
                })
            structured_parts.append(
                "VERIFIED_SESSION:" + json.dumps({
                    "session_id": str(session_obj.id),
                    "rank": session_obj.rank,
                    "category": session_obj.category,
                    "exam_type": session_obj.exam_type,
                    "rank_type": session_obj.rank_type,
                    "round": session_obj.round,
                    "total_eligible_matches": len(session_obj.results or []),
                    "verified_matches": verified_matches[:25]
                }, separators=(",", ":"))
            )

        if context.sidebar_colleges:
            structured_parts.append(
                "VIEWING:" + json.dumps(context.sidebar_colleges[:10], separators=(",", ":"))
            )

        college_profile = self._college_profile(context.focused_college)
        if college_profile:
            structured_parts.append(
                "COLLEGE:" + json.dumps(college_profile, separators=(",", ":"))
            )

        structured_for_llm = "|".join(structured_parts)

        # 7. Disable RAG pipeline for all chat queries — rely on clean structured database facts only
        rag_chunks = []
        rag_context = ""

        fallback = ""
        if preference_payload:
            fallback = format_preference_list(preference_payload)
        elif intent == "college_detail" and college_profile:
            fallback = self._format_college_detail_fallback(
                context.focused_college, college_profile, prediction
            )
        elif prediction:
            fallback = format_prediction_response(
                message, prediction, home_state=context.home_state
            )

        reply = self.gemini.generate(
            user_message=message,
            structured_data=structured_for_llm,
            rag_context=rag_context,
            history=[{"role": m.role, "content": m.content} for m in (history or [])],
            fallback_text=fallback,
        )

        return {
            "reply": reply,
            "intent": intent,
            "predictions": prediction.to_dict() if prediction else None,
            "preference_list": preference_payload,
            "verified_cards": verified_cards,
            "verified_card": verified_cards[0] if verified_cards else None,
            "context_used": {
                "has_predictions": prediction is not None and prediction.total_eligible > 0,
                "focused_college": context.focused_college or None,
                "rag_sources": [c["source"] for c in rag_chunks],
                "gemini_enabled": self.gemini.available,
                "gemini_error": self.gemini.last_error,
                "session_info": {
                    "session_id": str(session_obj.id) if session_obj else None,
                    "rank": session_obj.rank if session_obj else None,
                    "category": session_obj.category if session_obj else None,
                    "exam_type": session_obj.exam_type if session_obj else None,
                    "rank_type": session_obj.rank_type if session_obj else None,
                    "round": session_obj.round if session_obj else None,
                    "total_eligible": len(session_obj.results or []) if session_obj else 0,
                } if session_obj else None
            },
        }

    def _classify_query_system(self, message: str) -> str:
        """Classify user query into SQL, RAG, or HYBRID."""
        import re
        lower = message.lower()
        clean_msg = re.sub(r'[^\w\s]', ' ', lower)
        clean_words = set(clean_msg.split())
        
        # 1. Pure seat allocation rules queries (always pure RAG)
        is_rules = any(w in clean_words for w in ("float", "freeze", "slide", "rule", "rules")) or "seat allotment" in clean_msg
        if is_rules:
            return "RAG"
            
        # 2. Hybrid / Comparison / Strategy queries
        is_comparison = (
            any(w in clean_words for w in ("compare", "vs", "versus", "or", "better"))
            or "difference between" in clean_msg
            or "compare" in clean_msg
        )
        is_strategy = (
            any(w in clean_words for w in ("strategy", "plan"))
            or "choice list" in clean_msg
            or "choice filling" in clean_msg
            or "preference order" in clean_msg
            or "preference list" in clean_msg
        )
        if is_comparison or is_strategy:
            return "HYBRID"
            
        # 3. Pure SQL queries (cutoffs, branches, existence)
        is_sql = any(
            w in clean_words
            for w in (
                "cutoff", "cut-off", "cut", "off", "rank", "closing", "opening", "eligible",
                "chance", "exist", "offer", "branches", "branch"
            )
        ) or any(
            phrase in clean_msg
            for phrase in ("can i get", "get into", "admission", "admit", "predict", "seat", "have branch", "has branch", "branch list", "what branches")
        )
        if is_sql:
            return "SQL"
            
        # 4. Pure RAG queries (hostels, freeze/float, rules, campus life)
        is_rag = any(
            w in clean_words
            for w in (
                "hostel", "mess", "life", "campus", "culture", "placement", "package", "salary",
                "lpa", "job", "recruiter", "counselling", "counseling", "document", "verification",
                "allotment", "payment", "refund"
            )
        )
        if is_rag:
            return "RAG"
            
        return "SQL"

    def _extract_entities(self, message: str, context: ChatContext) -> dict:
        """Extract Institute, Branch, Round, Category, Quota from message and context."""
        # 1. Colleges
        colleges = self._detect_mentioned_colleges(message)
        
        # 2. Branch
        lower_msg = message.lower()
        branches = []
        branch_map = {
            "computer science": "CSE",
            "cse": "CSE",
            "information technology": "IT",
            "it": "IT",
            "electronics": "ECE",
            "ece": "ECE",
            "electrical": "EE",
            "ee": "EE",
            "eee": "EEE",
            "mechanical": "ME",
            "mech": "ME",
            "me ": "ME",
            "civil": "CE",
            "chemical": "CHE",
            "aerospace": "AE",
            "artificial intelligence": "AI",
            "ai": "AI",
            "data science": "DS",
            "ds": "DS",
        }
        for key, val in branch_map.items():
            if key in lower_msg or f" {key} " in f" {lower_msg} ":
                if val not in branches:
                    branches.append(val)
                    
        if not branches and context.branch_preferences:
            for bp in context.branch_preferences:
                bp_upper = bp.strip().upper()
                if bp_upper == "ALL":
                    continue
                if bp_upper not in branches:
                    branches.append(bp_upper)
                    
        # 3. Round
        round_val = context.round
        import re
        round_match = re.search(r'\bround\s*([1-6])\b', lower_msg)
        if round_match:
            round_val = round_match.group(1)
        elif "r1" in lower_msg:
            round_val = "1"
        elif "r2" in lower_msg:
            round_val = "2"
        elif "r3" in lower_msg:
            round_val = "3"
        elif "r4" in lower_msg:
            round_val = "4"
        elif "r5" in lower_msg:
            round_val = "5"
        elif "r6" in lower_msg:
            round_val = "6"
            
        # 4. Category
        category = context.category
        for cat, token in [
            ("OBC", "obc"),
            ("SC", " sc"),
            ("ST", " st"),
            ("EWS", "ews"),
            ("GENERAL", "general"),
            ("GENERAL", "open"),
        ]:
            if token in lower_msg:
                category = cat
                
        # 5. Quota
        quota = None
        if "home state" in lower_msg or " hs" in lower_msg:
            quota = "HS"
        elif "other state" in lower_msg or " os" in lower_msg:
            quota = "OS"
        elif "all india" in lower_msg or " ai" in lower_msg:
            quota = "AI"
            
        return {
            "colleges": colleges,
            "branches": branches,
            "round": round_val,
            "category": category,
            "quota": quota,
        }

    def _run_prediction(self, ctx: ChatContext) -> PredictionResponse:
        category = normalize_category(ctx.category or "GENERAL")
        return self.engine.predict(
            PredictionRequest(
                rank=ctx.rank,
                seat_category=category,
                exam_type=ctx.exam_type or "JEE_MAIN",
                rank_type=ctx.rank_type or "CRL",
                gender=ctx.gender,
                home_state=normalize_state(ctx.home_state),
                branch_preferences=ctx.branch_preferences or None,
                year=ctx.year,
                round=ctx.round or "LATEST",
                student_goals=ctx.student_goals,
                limit=40,
                max_results=500,
            )
        )

    def _build_preference_list(self, ctx: ChatContext) -> dict:
        from counselling.services import generate_preference_order

        category = normalize_category(ctx.category or "GENERAL")
        return generate_preference_order(
            PredictionRequest(
                rank=ctx.rank,
                seat_category=category,
                exam_type=ctx.exam_type or "JEE_MAIN",
                rank_type=ctx.rank_type or "CRL",
                gender=ctx.gender,
                home_state=normalize_state(ctx.home_state),
                branch_preferences=ctx.branch_preferences or None,
                year=ctx.year,
                round=ctx.round or "LATEST",
                student_goals=ctx.student_goals,
            ),
            max_choices=25,
        )

    def _college_profile(self, name: str) -> dict | None:
        if not name:
            return None
        from counselling.models import College

        college = (
            College.objects.filter(canonical_name__icontains=name.strip())
            .prefetch_related("programs")
            .first()
        )
        if not college:
            return {"name": name, "note": "Not in local DB — use general knowledge carefully"}

        programs = list(
            college.programs.values(
                "program_name",
                "branch_canonical",
                "fees_inr",
                "avg_package_inr",
                "placement_rate",
            )[:8]
        )
        return {
            "name": college.canonical_name,
            "category": college.category,
            "state": college.state,
            "rating": college.rating,
            "placement_score": college.placement_score,
            "academic_score": college.academic_score,
            "infrastructure_score": college.infrastructure_score,
            "ug_fee": college.ug_fee,
            "programs_sample": programs,
        }

    def _format_college_detail_fallback(
        self, name: str, profile: dict, prediction: PredictionResponse | None
    ) -> str:
        lines = [f"## About **{name}**\n"]
        if profile.get("state"):
            lines.append(f"- **Location:** {profile['state']}")
        if profile.get("category"):
            lines.append(f"- **Type:** {profile['category']}")
        if profile.get("rating"):
            lines.append(f"- **Community rating (approx):** {profile['rating']}/10")
        if profile.get("placement_score"):
            lines.append(f"- **Placement score (approx):** {profile['placement_score']}/10")
        if profile.get("programs_sample"):
            lines.append("\n**Programs in our database:**")
            for p in profile["programs_sample"][:3]:
                pkg = p.get("avg_package_inr")
                pkg_str = f"₹{pkg:,} LPA approx" if pkg else "package data N/A"
                lines.append(f"- {p.get('branch_canonical', p.get('program_name', ''))}: {pkg_str}")

        lines.append(
            "\nFor detailed placement % and packages, I can give typical ranges when Gemini is connected. "
            "Verify cutoffs on josaa.nic.in."
        )
        return "\n".join(lines)

    def _extract_college_from_message(
        self, message: str, sidebar: list[dict]
    ) -> str:
        lower = message.lower()
        for item in sidebar:
            name = item.get("college_name", "")
            if name and name.lower() in lower:
                return name
        return ""

    def _detect_intent(self, message: str) -> str:
        lower = message.lower()
        if any(
            w in lower
            for w in (
                "placement",
                "package",
                "salary",
                "lpa",
                "campus",
                "hostel",
                "college life",
                "coding culture",
                "tell me about",
                "should i pick",
                "compare",
            )
        ):
            return "college_detail"
        if any(w in lower for w in ("preference order", "choice filling", "choice list")):
            return "preference"
        if any(
            w in lower
            for w in ("freeze", "float", "slide", "quota", "josaa rule", "round")
        ):
            return "rules"
        if any(
            w in lower
            for w in ("suggest", "best", "college", "nit", "iit", "iiit", "eligible")
        ):
            return "predict"
        return "general"

    def _enrich_context_from_message(self, message: str, ctx: ChatContext) -> None:
        if not ctx.rank:
            parsed = parse_rank_from_text(message)
            if parsed:
                ctx.rank = parsed

        lower = message.lower()
        for cat, token in [
            ("OBC", "obc"),
            ("SC", " sc"),
            ("ST", " st"),
            ("EWS", "ews"),
            ("GENERAL", "general"),
            ("GENERAL", "open"),
        ]:
            if token in lower and not ctx.category:
                ctx.category = cat

        for branch in ("cse", "computer", "ece", "eee", "mech", "civil", "it", "ai", "ds"):
            if branch in lower and branch.upper() not in ctx.branch_preferences:
                ctx.branch_preferences.append(branch.upper())

        states = {
            "telangana": "Telangana",
            "andhra": "Andhra Pradesh",
            "andhra pradesh": "Andhra Pradesh",
            "karnataka": "Karnataka",
            "tamil nadu": "Tamil Nadu",
            "maharashtra": "Maharashtra",
            "delhi": "Delhi",
            "uttar pradesh": "Uttar Pradesh",
            "bihar": "Bihar",
            "rajasthan": "Rajasthan",
            "gujarat": "Gujarat",
            "kerala": "Kerala",
            "west bengal": "West Bengal",
        }
        for key, canonical in states.items():
            if key in lower:
                ctx.home_state = canonical
                break

        goal_phrases = (
            "prefer coding",
            "prioritize placement",
            "prioritise placement",
            "want core",
            "love civil",
            "avoid core",
            "startup",
            "hate coding",
            "location matters",
            "near home",
        )
        for phrase in goal_phrases:
            if phrase in lower:
                note = f"Student mentioned: {phrase}"
                if note not in ctx.student_goals:
                    ctx.student_goals = (ctx.student_goals + "; " + note).strip("; ")

    def _detect_mentioned_colleges(self, message: str) -> list[College]:
        from counselling.models import College
        import re
        
        # Normalize and clean message: lower, replace punctuation with spaces, compress whitespace
        lower_msg = message.lower()
        clean_msg = " ".join(re.sub(r'[^\w\s]', ' ', lower_msg).split())
        
        mentioned = []
        
        # Load only colleges that actually have cutoffs
        colleges = College.objects.filter(programs__cutoffs__isnull=False).distinct()
        for college in colleges:
            name = college.canonical_name
            name_lower = name.lower()
            clean_name = " ".join(re.sub(r'[^\w\s]', ' ', name_lower).split())
            
            # 1. Direct canonical name match (cleaned)
            if clean_name in clean_msg:
                mentioned.append(college)
                continue
                
            # 2. Advanced abbreviation and alias matches
            aliases = []
            if "tiruchirappalli" in name_lower or "trichy" in name_lower:
                if "iiit" in name_lower:
                    aliases = ["iiit trichy", "iiit tiruchirappalli", "trichy iiit", "tiruchirappalli iiit"]
                elif "nit" in name_lower:
                    aliases = ["nit trichy", "nit tiruchirappalli", "trichy nit", "tiruchirappalli nit"]
            elif "bombay" in name_lower:
                aliases = ["iit bombay", "iit b", "iitb", "bombay iit"]
            elif "delhi" in name_lower and "technology" in name_lower:
                if "indian" in name_lower:
                    aliases = ["iit delhi", "iitd", "iit d"]
            elif "nagpur" in name_lower and "iiit" in name_lower:
                aliases = ["iiit nagpur", "nagpur iiit"]
            elif "pune" in name_lower and "iiit" in name_lower:
                aliases = ["iiit pune", "pune iiit"]
            elif "gwalior" in name_lower:
                aliases = ["iiit gwalior", "gwalior iiit", "iiitm gwalior", "abv iiitm"]
            elif "allahabad" in name_lower:
                if "iiit" in name_lower:
                    aliases = ["iiit allahabad", "iiita", "allahabad iiit"]
            elif "madras" in name_lower:
                aliases = ["iit madras", "iitm", "iit m"]
            elif "kharagpur" in name_lower:
                aliases = ["iit kharagpur", "iitkgp", "iit kgp"]
            elif "roorkee" in name_lower:
                aliases = ["iit roorkee", "iitr", "iit r"]
            elif "guwahati" in name_lower:
                if "iit" in name_lower:
                    aliases = ["iit guwahati", "iitg", "iit g"]
                elif "iiit" in name_lower:
                    aliases = ["iiit guwahati", "guwahati iiit"]
            elif "surathkal" in name_lower:
                aliases = ["nit surathkal", "surathkal nit", "nits"]
            elif "warangal" in name_lower:
                aliases = ["nit warangal", "warangal nit", "nitw"]
            elif "calicut" in name_lower:
                aliases = ["nit calicut", "calicut nit", "nitc"]
            elif "jaipur" in name_lower:
                aliases = ["mnit jaipur", "nit jaipur", "jaipur nit"]
            elif "kurukshetra" in name_lower:
                aliases = ["nit kurukshetra", "kurukshetra nit"]
            elif "rourkela" in name_lower:
                aliases = ["nit rourkela", "rourkela nit", "nitr"]
            elif "silchar" in name_lower:
                aliases = ["nit silchar", "silchar nit"]
                
            # Generic rules for "IIT X", "NIT X", "IIIT X"
            if "indian institute of technology" in name_lower:
                city = name_lower.replace("indian institute of technology", "").strip()
                city_clean = city.split("(")[0].strip()
                aliases.extend([f"iit {city_clean}", f"iit{city_clean}"])
            elif "national institute of technology" in name_lower:
                city = name_lower.replace("national institute of technology", "").strip()
                city_clean = city.split("(")[0].strip()
                aliases.extend([f"nit {city_clean}", f"nit{city_clean}"])
            elif "indian institute of information technology" in name_lower:
                city = name_lower.replace("indian institute of information technology", "").strip()
                city_clean = city.split("(")[0].strip()
                aliases.extend([f"iiit {city_clean}", f"iiit{city_clean}"])
                
            # Clean punctuation from aliases when checking match
            matched_alias = False
            for alias in aliases:
                clean_alias = " ".join(re.sub(r'[^\w\s]', ' ', alias.lower()).split())
                if clean_alias and clean_alias in clean_msg:
                    matched_alias = True
                    break
                    
            if matched_alias:
                mentioned.append(college)
                
        return list(set(mentioned))

    def _get_college_metrics(
        self,
        canonical_name: str,
        tiers_data: dict,
        college_category: str,
        rating: float | None,
    ) -> dict:
        import re

        col_name_lower = canonical_name.lower()
        
        # Clean both for matching
        def clean_text(text: str) -> str:
            text = text.lower()
            text = text.replace("indian institute of technology", "iit")
            text = text.replace("national institute of technology", "nit")
            text = text.replace("indian institute of information technology", "iiit")
            text = text.replace("tiruchirappalli", "trichy")
            text = text.replace("karnataka", "surathkal")
            return " ".join(re.sub(r'[^\w\s]', ' ', text).split())

        cleaned_col = clean_text(col_name_lower)

        # 1. Exact or substring match of cleaned text
        for key, metrics in tiers_data.items():
            cleaned_key = clean_text(key)
            if cleaned_key == cleaned_col or cleaned_key in cleaned_col or cleaned_col in cleaned_key:
                return metrics

        # 2. Try city/distinct keyword match based on category
        category_lower = (college_category or "").lower()
        is_iit = "iit" in category_lower or "technology" in category_lower or "iit" in cleaned_col
        is_nit = "nit" in category_lower or "national" in category_lower or "nit" in cleaned_col
        is_iiit = "iiit" in category_lower or "information" in category_lower or "iiit" in cleaned_col

        # Identify keywords from canonical name
        words = set(re.findall(r'\b\w+\b', col_name_lower))
        for key, metrics in tiers_data.items():
            key_lower = key.lower()
            key_words = set(re.findall(r'\b\w+\b', key_lower))
            
            # Check if type matches
            key_is_iit = "iit" in key_lower
            key_is_nit = "nit" in key_lower
            key_is_iiit = "iiit" in key_lower

            type_match = (is_iit and key_is_iit) or (is_nit and key_is_nit) or (is_iiit and key_is_iiit)
            if type_match:
                # Find common distinct words (excluding iit, nit, iiit, institute, technology, of, and, etc.)
                ignored = {"iit", "nit", "iiit", "institute", "technology", "of", "and", "national", "information"}
                col_distinct = words - ignored
                key_distinct = key_words - ignored
                if col_distinct & key_distinct: # Overlap found!
                    return metrics

        # 3. Fallback to generic defaults if no match found
        default_score = rating if rating is not None else 8.0
        
        if is_iit:
            return {
                "tier": "Tier 1",
                "coding_score": default_score,
                "placement_score": default_score,
                "roi_score": default_score,
                "reputation_score": default_score,
                "alumni_score": default_score,
                "campus_score": default_score,
            }
        elif is_nit:
            return {
                "tier": "Tier 2",
                "coding_score": round(max(5.0, default_score - 0.2), 1),
                "placement_score": round(max(5.0, default_score - 0.2), 1),
                "roi_score": round(default_score, 1),
                "reputation_score": round(max(5.0, default_score - 0.2), 1),
                "alumni_score": round(max(5.0, default_score - 0.2), 1),
                "campus_score": round(max(5.0, default_score - 0.1), 1),
            }
        elif is_iiit:
            return {
                "tier": "Tier 2",
                "coding_score": round(min(10.0, default_score + 0.2), 1),
                "placement_score": round(default_score, 1),
                "roi_score": round(max(5.0, default_score - 0.5), 1),
                "reputation_score": round(max(5.0, default_score - 0.3), 1),
                "alumni_score": round(max(5.0, default_score - 0.5), 1),
                "campus_score": round(max(5.0, default_score - 0.8), 1),
            }
        else:
            if "iit" in cleaned_col:
                tier = "Tier 1"
            elif "nit" in cleaned_col or "iiit" in cleaned_col:
                tier = "Tier 2"
            else:
                tier = "Tier 3"
            return {
                "tier": tier,
                "coding_score": default_score,
                "placement_score": default_score,
                "roi_score": default_score,
                "reputation_score": default_score,
                "alumni_score": default_score,
                "campus_score": default_score,
            }

