from django.test import TestCase

from counselling.models import College, Cutoff, Program
from recommendation_engine.engine import PredictionEngine, PredictionRequest


class PredictionEngineTests(TestCase):
    def setUp(self):
        college = College.objects.create(
            canonical_name="NIT Warangal",
            category=College.Category.NIT,
            state="Telangana",
            rating=8.5,
        )
        program = Program.objects.create(
            college=college,
            program_name="Computer Science and Engineering (4 Years, B.Tech)",
            branch_canonical="COMPUTER_SCIENCE_AND_ENGINEERING",
        )
        Cutoff.objects.create(
            program=program,
            year=2024,
            round=6,
            category="OBC",
            quota="ALL_INDIA",
            gender="GENDER_NEUTRAL",
            opening_rank=8000,
            closing_rank=22000,
            exam_type="JEE_MAIN",
            rank_type="JEE_MAIN_OBC",
        )
        Cutoff.objects.create(
            program=program,
            year=2024,
            round=5,
            category="OBC",
            quota="HOME_STATE",
            gender="GENDER_NEUTRAL",
            opening_rank=15000,
            closing_rank=20000,
            exam_type="JEE_MAIN",
            rank_type="JEE_MAIN_OBC",
        )

    def test_eligible_obc_rank_18k(self):
        engine = PredictionEngine()
        result = engine.predict(
            PredictionRequest(
                rank=18000,
                seat_category="OBC",
                year=2024,
                round="6",
                rank_type="CATEGORY",
            )
        )
        self.assertGreaterEqual(result.total_eligible, 1)
        self.assertTrue(any(p.closing_rank >= 18000 for p in result.target + result.safe))

    def test_prediction_session_creation(self):
        engine = PredictionEngine()
        result = engine.predict(
            PredictionRequest(
                rank=18000,
                seat_category="OBC",
                year=2024,
                round="6",
                rank_type="CATEGORY",
            )
        )
        self.assertIsNotNone(result.session_id)
        from counselling.models import PredictionSession
        session = PredictionSession.objects.get(id=result.session_id)
        self.assertEqual(session.rank, 18000)
        self.assertEqual(session.category, "OBC")
        self.assertGreaterEqual(len(session.results), 1)


class CounsellingOrchestratorTests(TestCase):
    def setUp(self):
        self.college = College.objects.create(
            canonical_name="NIT Warangal",
            category=College.Category.NIT,
            state="Telangana",
            rating=8.5,
        )
        self.program = Program.objects.create(
            college=self.college,
            program_name="Computer Science and Engineering (4 Years, B.Tech)",
            branch_canonical="COMPUTER_SCIENCE_AND_ENGINEERING",
        )
        Cutoff.objects.create(
            program=self.program,
            year=2025,
            round=5,
            category="OBC",
            quota="ALL_INDIA",
            gender="GENDER_NEUTRAL",
            opening_rank=8000,
            closing_rank=22000,
            exam_type="JEE_MAIN",
            rank_type="JEE_MAIN_OBC",
        )

    def test_intent_classification(self):
        from ai_engine.orchestrator import CounsellingOrchestrator
        orchestrator = CounsellingOrchestrator()
        
        self.assertEqual(orchestrator._classify_query_system("What is the cutoff for CSE at NIT Warangal?"), "SQL")
        self.assertEqual(orchestrator._classify_query_system("Can I get into NIT Warangal at rank 15000?"), "SQL")
        self.assertEqual(orchestrator._classify_query_system("Does NIT Warangal offer IT?"), "SQL")
        self.assertEqual(orchestrator._classify_query_system("How is the hostel life at NIT Warangal?"), "RAG")
        self.assertEqual(orchestrator._classify_query_system("Explain the difference between float and freeze"), "RAG")
        self.assertEqual(orchestrator._classify_query_system("NIT Trichy vs NIT Warangal"), "HYBRID")

    def test_entity_extraction(self):
        from ai_engine.orchestrator import CounsellingOrchestrator, ChatContext
        orchestrator = CounsellingOrchestrator()
        context = ChatContext(round="LATEST")
        
        entities = orchestrator._extract_entities("Can I get CSE at NIT Warangal in Round 4?", context)
        self.assertEqual(len(entities["colleges"]), 1)
        self.assertEqual(entities["colleges"][0].canonical_name, "NIT Warangal")
        self.assertIn("CSE", entities["branches"])
        self.assertEqual(entities["round"], "4")

    def test_verified_cards_generation(self):
        from ai_engine.orchestrator import CounsellingOrchestrator, ChatContext
        orchestrator = CounsellingOrchestrator()
        context = ChatContext(rank=18000, category="OBC", home_state="Telangana", round="5", year=2025, rank_type="CATEGORY")
        
        res = orchestrator.handle(
            message="Can I get CSE at NIT Warangal?",
            context=context,
        )
        self.assertIn("verified_cards", res)
        self.assertEqual(len(res["verified_cards"]), 1)
        card = res["verified_cards"][0]
        self.assertEqual(card["college_name"], "NIT Warangal")
        self.assertEqual(card["closing_rank"], 22000)
        self.assertEqual(card["margin"], 4000)
        self.assertEqual(card["classification"], "TARGET")

