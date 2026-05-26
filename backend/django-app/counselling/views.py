from django.conf import settings
from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from counselling.models import College, Cutoff, StudentUser
from counselling.serializers import (
    ChatRequestSerializer,
    CollegeSerializer,
    PredictRequestSerializer,
    PreferenceRequestSerializer,
    StudentUserSerializer,
)
from counselling.services import generate_preference_order
from recommendation_engine.engine import PredictionEngine, PredictionRequest
from recommendation_engine.normalization import normalize_category, normalize_rank_type, normalize_state

def normalize_request_data(data):
    """Normalize exam_type and rank_type if frontend sent them swapped or unified."""
    if hasattr(data, "copy"):
        normalized = data.copy()
    else:
        normalized = dict(data)

    raw_exam_type = normalized.get("exam_type")
    raw_rank_type = normalized.get("rank_type")
    raw_category = normalized.get("category", "GENERAL")

    if not raw_category:
        raw_category = "GENERAL"

    norm_cat = normalize_category(str(raw_category))

    # If rank_type is sent as JEE_MAIN or JEE_ADVANCED, it's actually the exam_type
    if raw_rank_type in ["JEE_MAIN", "JEE_ADVANCED"]:
        raw_exam_type = raw_rank_type
        # Determine CRL vs CATEGORY based on normalized category
        if norm_cat in ["GENERAL", "OPEN", "GEN"]:
            raw_rank_type = "CRL"
        else:
            raw_rank_type = "CATEGORY"

    if raw_exam_type:
        normalized["exam_type"] = raw_exam_type
    if raw_rank_type:
        normalized["rank_type"] = raw_rank_type

    return normalized



class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from ai_engine.gemini.client import resolve_api_key

        key = resolve_api_key()
        return Response(
            {
                "status": "ok",
                "colleges": College.objects.count(),
                "cutoffs": Cutoff.objects.count(),
                "gemini_configured": bool(key),
                "gemini_key_preview": f"{key[:8]}..." if len(key) > 8 else None,
            }
        )


class MetaView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agg = Cutoff.objects.aggregate(min_year=Min("year"), max_year=Max("year"))
        categories = list(
            Cutoff.objects.values_list("category", flat=True).distinct().order_by("category")
        )
        quotas = list(
            Cutoff.objects.values_list("quota", flat=True).distinct().order_by("quota")
        )
        genders = list(
            Cutoff.objects.values_list("gender", flat=True).distinct().order_by("gender")
        )
        branches = list(
            Cutoff.objects.values_list("program__branch_canonical", flat=True)
            .distinct()
            .order_by("program__branch_canonical")[:50]
        )
        preferred = list(getattr(settings, "CUTOFF_PREFERRED_YEARS", [2025, 2024]))
        default_year = int(getattr(settings, "DEFAULT_CUTOFF_YEAR", 2025))
        year_stats = list(
            Cutoff.objects.filter(year__in=preferred)
            .values("year")
            .annotate(count=Count("id"))
            .order_by("-year")
        )
        return Response(
            {
                "years": agg,
                "cutoff_years": preferred,
                "default_cutoff_year": default_year,
                "cutoff_year_stats": year_stats,
                "categories": categories,
                "quotas": quotas,
                "genders": genders,
                "sample_branches": [b for b in branches if b],
                "rank_types": [
                    {
                        "id": "JEE_MAIN",
                        "label": "JEE Main rank",
                        "institutes": "NIT · IIIT · GFTI",
                    },
                    {
                        "id": "JEE_ADVANCED",
                        "label": "JEE Advanced rank",
                        "institutes": "IIT only",
                    },
                ],
                "default_rank_type": "JEE_MAIN",
            }
        )


class PredictView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        normalized_data = normalize_request_data(request.data)
        serializer = PredictRequestSerializer(data=normalized_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        engine = PredictionEngine()
        result = engine.predict(
            PredictionRequest(
                rank=data["rank"],
                seat_category=normalize_category(data["category"]),
                exam_type=data.get("exam_type", "JEE_MAIN"),
                rank_type=data.get("rank_type", "CRL"),
                student_goals=data.get("student_goals", ""),
                gender=data.get("gender", "GENDER_NEUTRAL"),
                home_state=normalize_state(data.get("home_state", "")),
                branch_preferences=data.get("branch_preferences"),
                year=data.get("year"),
                round=data.get("round"),
                quotas=data.get("quotas"),
                limit=data.get("limit", 50),
                max_results=data.get("max_results", 500),
            )
        )
        return Response(result.to_dict())


class PreferenceGenerateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        normalized_data = normalize_request_data(request.data)
        serializer = PreferenceRequestSerializer(data=normalized_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payload = generate_preference_order(
            PredictionRequest(
                rank=data["rank"],
                seat_category=normalize_category(data["category"]),
                exam_type=data.get("exam_type", "JEE_MAIN"),
                rank_type=data.get("rank_type", "CRL"),
                student_goals=data.get("student_goals", ""),
                gender=data.get("gender", "GENDER_NEUTRAL"),
                home_state=normalize_state(data.get("home_state", "")),
                branch_preferences=data.get("branch_preferences"),
                year=data.get("year"),
                round=data.get("round"),
                quotas=data.get("quotas"),
            ),
            max_choices=data.get("max_choices", 50),
        )
        return Response(payload)


class CollegeDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, college_id: int):
        college = get_object_or_404(College.objects.prefetch_related("programs"), pk=college_id)
        return Response(CollegeSerializer(college).data)



class ChatView(APIView):
    """AI counselling assistant — DB facts + RAG + Gemini."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        normalized_data = normalize_request_data(request.data)
        serializer = ChatRequestSerializer(data=normalized_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from ai_engine.orchestrator import ChatContext, ChatMessage, CounsellingOrchestrator

        category = normalize_category(data["category"]) if data.get("category") else ""

        context = ChatContext(
            rank=data.get("rank"),
            category=category or None,
            gender=data.get("gender", "GENDER_NEUTRAL"),
            home_state=normalize_state(data.get("home_state", "")),
            branch_preferences=data.get("branch_preferences") or [],
            year=data.get("year"),
            exam_type=data.get("exam_type", "JEE_MAIN"),
            rank_type=data.get("rank_type", "CRL"),
            round=data.get("round", "LATEST"),
            student_goals=data.get("student_goals", ""),
            focused_college=data.get("focused_college", ""),
            sidebar_colleges=data.get("sidebar_colleges") or [],
            session_id=data.get("session_id"),
            selected_card=data.get("selected_card"),
        )
        history = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in data.get("history", [])
        ]

        result = CounsellingOrchestrator().handle(
            message=data["message"],
            context=context,
            history=history,
        )
        return Response(result)


class StudentRegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = StudentUserSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data["mobile_number"]
            student, created = StudentUser.objects.update_or_create(
                mobile_number=mobile,
                defaults={
                    "name": serializer.validated_data["name"],
                    "gender": serializer.validated_data["gender"],
                }
            )
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(StudentUserSerializer(student).data, status=status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

