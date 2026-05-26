from rest_framework import serializers

from counselling.models import College, Program, StudentUser


class StudentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        fields = ("id", "name", "gender", "mobile_number", "created_at")
        extra_kwargs = {
            "mobile_number": {
                "validators": []
            }
        }



class PredictRequestSerializer(serializers.Serializer):
    rank = serializers.IntegerField(min_value=1)
    category = serializers.CharField(max_length=32)
    exam_type = serializers.ChoiceField(
        choices=["JEE_MAIN", "JEE_ADVANCED"],
        default="JEE_MAIN",
        required=False,
    )
    rank_type = serializers.ChoiceField(
        choices=["CRL", "CATEGORY"],
        default="CRL",
        required=False,
    )
    gender = serializers.CharField(max_length=32, default="GENDER_NEUTRAL", required=False)
    home_state = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    branch_preferences = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    year = serializers.IntegerField(required=False, allow_null=True, min_value=2016, max_value=2030)
    round = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="LATEST")
    quotas = serializers.ListField(child=serializers.CharField(), required=False)
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)
    max_results = serializers.IntegerField(default=500, min_value=50, max_value=1000)
    student_goals = serializers.CharField(required=False, allow_blank=True, default="")


class PreferenceRequestSerializer(PredictRequestSerializer):
    max_choices = serializers.IntegerField(default=50, min_value=10, max_value=150)


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = (
            "id",
            "program_name",
            "branch_canonical",
            "fees_inr",
            "avg_package_inr",
            "placement_rate",
        )


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "model"])
    content = serializers.CharField()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    history = ChatMessageSerializer(many=True, required=False, default=list)
    rank = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    category = serializers.CharField(max_length=32, required=False, allow_blank=True)
    gender = serializers.CharField(max_length=32, required=False, default="GENDER_NEUTRAL")
    home_state = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    branch_preferences = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    year = serializers.IntegerField(required=False, allow_null=True, min_value=2016, max_value=2030)
    exam_type = serializers.ChoiceField(
        choices=["JEE_MAIN", "JEE_ADVANCED"],
        default="JEE_MAIN",
        required=False,
    )
    rank_type = serializers.ChoiceField(
        choices=["CRL", "CATEGORY"],
        default="CRL",
        required=False,
    )
    round = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="LATEST")
    student_goals = serializers.CharField(required=False, allow_blank=True, default="")
    focused_college = serializers.CharField(max_length=512, required=False, allow_blank=True)
    sidebar_colleges = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True
    )
    session_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    selected_card = serializers.DictField(required=False, allow_null=True, default=None)


class CollegeSerializer(serializers.ModelSerializer):
    programs = ProgramSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = (
            "id",
            "canonical_name",
            "category",
            "state",
            "city",
            "stream",
            "rating",
            "placement_score",
            "academic_score",
            "infrastructure_score",
            "ug_fee",
            "pg_fee",
            "programs",
        )
