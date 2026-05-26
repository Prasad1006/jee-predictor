from django.urls import path

from counselling import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("meta/", views.MetaView.as_view(), name="meta"),
    path("predict/", views.PredictView.as_view(), name="predict"),
    path("preferences/generate/", views.PreferenceGenerateView.as_view(), name="preferences"),
    path("colleges/<int:college_id>/", views.CollegeDetailView.as_view(), name="college-detail"),
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("students/register/", views.StudentRegisterView.as_view(), name="student-register"),
]
