import uuid
from django.db import models


class College(models.Model):
    class Category(models.TextChoices):
        IIT = "IIT", "IIT"
        NIT = "NIT", "NIT"
        IIIT = "IIIT", "IIIT"
        GFTI = "GFTI", "GFTI"
        DEEMED = "Deemed", "Deemed"
        OTHER = "Other", "Other"

    canonical_name = models.CharField(max_length=512, unique=True, db_index=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
    state = models.CharField(max_length=128, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    stream = models.CharField(max_length=64, blank=True, default="")
    rating = models.FloatField(null=True, blank=True)
    placement_score = models.FloatField(null=True, blank=True)
    academic_score = models.FloatField(null=True, blank=True)
    infrastructure_score = models.FloatField(null=True, blank=True)
    ug_fee = models.CharField(max_length=64, blank=True, default="")
    pg_fee = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["canonical_name"]

    def __str__(self) -> str:
        return self.canonical_name


class Program(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="programs")
    program_name = models.CharField(max_length=512)
    branch_canonical = models.CharField(max_length=128, blank=True, default="", db_index=True)
    degree = models.CharField(max_length=64, blank=True, default="")
    fees_inr = models.BigIntegerField(null=True, blank=True)
    avg_package_inr = models.BigIntegerField(null=True, blank=True)
    placement_rate = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("college", "program_name", "branch_canonical")
        indexes = [
            models.Index(fields=["branch_canonical"]),
        ]

    def __str__(self) -> str:
        return f"{self.college.canonical_name} — {self.program_name}"


class Cutoff(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="cutoffs")
    year = models.PositiveSmallIntegerField(db_index=True)
    round = models.PositiveSmallIntegerField(db_index=True)
    category = models.CharField(max_length=32, db_index=True)
    quota = models.CharField(max_length=32, db_index=True)
    gender = models.CharField(max_length=32, default="GENDER_NEUTRAL")
    opening_rank = models.PositiveIntegerField(null=True, blank=True)
    closing_rank = models.PositiveIntegerField(db_index=True)
    exam_type = models.CharField(max_length=32, default="JEE_MAIN", db_index=True)
    rank_type = models.CharField(max_length=64, default="JEE_MAIN_CRL", db_index=True)
    source = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        unique_together = (
            "program",
            "year",
            "round",
            "category",
            "quota",
            "gender",
        )
        indexes = [
            models.Index(fields=["exam_type", "rank_type", "year", "round", "closing_rank"]),
            models.Index(fields=["year", "category", "quota", "closing_rank"]),
            models.Index(fields=["year", "round", "category", "closing_rank"]),
        ]

    def __str__(self) -> str:
        return f"{self.program} ({self.year} R{self.round}) close={self.closing_rank}"


class StudentUser(models.Model):
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=15, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.mobile_number})"


class PredictionSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    rank = models.PositiveIntegerField()
    category = models.CharField(max_length=32)
    exam_type = models.CharField(max_length=32, default="JEE_MAIN")
    rank_type = models.CharField(max_length=32, default="CRL")
    gender = models.CharField(max_length=32, default="GENDER_NEUTRAL")
    home_state = models.CharField(max_length=128, blank=True, default="")
    branch_preferences = models.JSONField(default=list, blank=True)
    year = models.PositiveSmallIntegerField()
    round = models.CharField(max_length=32, default="LATEST")
    results = models.JSONField(default=list)
    trace = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Session {self.id} (Rank={self.rank}, Category={self.category})"

