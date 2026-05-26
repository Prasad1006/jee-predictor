"""Backfill college category and state from institute names."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from counselling.models import College
from recommendation_engine.college_metadata import infer_college_category, infer_college_state


class Command(BaseCommand):
    help = "Infer and update college category (IIT/NIT/IIIT) and state from canonical names"

    def handle(self, *args, **options):
        updated = 0
        for college in College.objects.iterator(chunk_size=500):
            cat = infer_college_category(college.canonical_name)
            state = college.state.strip() or infer_college_state(college.canonical_name)
            fields = {}
            if college.category != cat and cat != "Other":
                fields["category"] = cat
            elif college.category == "Other" and cat != "Other":
                fields["category"] = cat
            if state and college.state != state:
                fields["state"] = state
            if fields:
                College.objects.filter(pk=college.pk).update(**fields)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} colleges"))
