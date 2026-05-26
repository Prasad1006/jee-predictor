from django.contrib import admin

from .models import College, Cutoff, Program, StudentUser


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "category", "state", "rating")
    search_fields = ("canonical_name", "state")
    list_filter = ("category", "state")


class CutoffInline(admin.TabularInline):
    model = Cutoff
    extra = 0


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("college", "branch_canonical", "program_name")
    search_fields = ("college__canonical_name", "program_name", "branch_canonical")
    inlines = [CutoffInline]


@admin.register(Cutoff)
class CutoffAdmin(admin.ModelAdmin):
    list_display = ("program", "year", "round", "category", "quota", "closing_rank")
    list_filter = ("year", "category", "quota")


@admin.register(StudentUser)
class StudentUserAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile_number", "gender", "created_at")
    search_fields = ("name", "mobile_number")
    list_filter = ("gender", "created_at")

