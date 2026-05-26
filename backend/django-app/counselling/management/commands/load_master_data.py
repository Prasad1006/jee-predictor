"""Import cleaned CSVs into PostgreSQL/SQLite."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from counselling.models import College, Cutoff, Program
from recommendation_engine.college_metadata import infer_college_category, infer_college_state
from recommendation_engine.normalization import get_correct_branch_canonical

ROOT = Path(__file__).resolve().parents[5]
PIPELINE = ROOT / "data-pipeline"
MAPPINGS = PIPELINE / "mappings"


def parse_fee(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace(",", "").strip()


def safe_float(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text in ("", "--", "-", "NA", "N/A"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Load master cutoffs and college metadata from data-pipeline outputs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cutoffs-only",
            action="store_true",
            help="Skip college metadata; only reload cutoffs",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="bulk_create batch size for cutoffs",
        )

    def handle(self, *args, **options):
        batch_size: int = options["batch_size"]
        cutoffs_path = PIPELINE / "merged-data" / "master_cutoffs_merged.csv"
        if not cutoffs_path.exists():
            self.stderr.write(self.style.ERROR(f"Missing {cutoffs_path}. Run data pipeline first."))
            return

        college_meta = self._load_college_metadata()

        if not options["cutoffs_only"]:
            self.stdout.write("Loading college metadata...")
            self._import_college_metadata(college_meta)
            self._import_fees_placement()

        self.stdout.write("Loading cutoffs (this may take a few minutes)...")
        self._import_cutoffs(cutoffs_path, college_meta, batch_size)
        
        self.stdout.write("Running college metadata backfills and cleanups...")
        # 1. Backfill categories & states
        updated_count = 0
        for college in College.objects.iterator(chunk_size=500):
            cat = infer_college_category(college.canonical_name)
            state = college.state.strip() or infer_college_state(college.canonical_name)
            fields = {}
            if college.category != cat:
                fields["category"] = cat
            if state and college.state != state:
                fields["state"] = state
            if fields:
                College.objects.filter(pk=college.pk).update(**fields)
                updated_count += 1
        self.stdout.write(f"  Updated metadata for {updated_count} colleges.")

        # 2. Update category to GFTI for colleges with cutoffs currently marked 'Other' or 'GFTI' (ensure database clean consistency)
        gfti_count = College.objects.filter(programs__cutoffs__isnull=False, category='Other').update(category='GFTI')
        self.stdout.write(f"  Marked {gfti_count} colleges as GFTI.")

        # 3. Clean up database: delete colleges without any cutoffs
        deleted_count, _ = College.objects.filter(programs__cutoffs__isnull=True).delete()
        self.stdout.write(f"  Deleted {deleted_count} unused colleges without cutoffs.")

        self._print_stats()

    def _load_college_metadata(self) -> dict[str, dict]:
        meta: dict[str, dict] = {}
        mapped_path = MAPPINGS / "colleges_auto_mapped.json"
        if mapped_path.exists():
            with open(mapped_path, encoding="utf-8") as file:
                raw = json.load(file)
            for _name, entry in raw.items():
                canonical = entry.get("canonical_name")
                if canonical:
                    meta[canonical] = entry
        return meta

    def _import_college_metadata(self, college_meta: dict[str, dict]) -> None:
        path = PIPELINE / "normalized-data" / "college_data_normalized.csv"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Skipping college metadata: {path} not found"))
            return

        df = pd.read_csv(path, low_memory=False)
        created = 0
        for _, row in df.iterrows():
            canonical = str(row.get("institute_canonical") or row.get("college_name", "")).strip()
            if not canonical:
                continue
            extra = college_meta.get(canonical, {})
            category = extra.get("category") or infer_college_category(canonical)
            if category not in dict(College.Category.choices):
                category = College.Category.OTHER
            state = (
                str(row.get("state") or extra.get("state") or "").strip()
                or infer_college_state(canonical)
            )[:128]

            _, was_created = College.objects.update_or_create(
                canonical_name=canonical,
                defaults={
                    "category": category,
                    "state": state,
                    "stream": str(row.get("stream") or "")[:64],
                    "rating": safe_float(row.get("rating")),
                    "placement_score": safe_float(row.get("placement")),
                    "academic_score": safe_float(row.get("academic")),
                    "infrastructure_score": safe_float(row.get("infrastructure")),
                    "ug_fee": parse_fee(row.get("ug_fee")),
                    "pg_fee": parse_fee(row.get("pg_fee")),
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f"  colleges: {College.objects.count()} total ({created} new)")

    def _import_fees_placement(self) -> None:
        path = PIPELINE / "standardized-data" / "std_fees_placement.csv"
        if not path.exists():
            return
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            name = str(row.get("college", "")).strip()
            if not name:
                continue
            college, _ = College.objects.get_or_create(
                canonical_name=name,
                defaults={"category": infer_college_category(name)},
            )
            branch = str(row.get("branch", "")).upper()
            program_name = f"{row.get('program', 'B.Tech')} {branch}".strip()
            clean_branch = get_correct_branch_canonical(program_name)
            Program.objects.update_or_create(
                college=college,
                program_name=program_name,
                branch_canonical=clean_branch,
                defaults={
                    "fees_inr": int(row["fees_inr"]) if pd.notna(row.get("fees_inr")) else None,
                    "avg_package_inr": int(row["avg_package_inr"])
                    if pd.notna(row.get("avg_package_inr"))
                    else None,
                    "placement_rate": float(row["placement"]) if pd.notna(row.get("placement")) else None,
                },
            )

    def _import_cutoffs(self, path: Path, college_meta: dict, batch_size: int) -> None:
        df = pd.read_csv(path, low_memory=False)
        df = df.dropna(subset=["institute_canonical", "closing_rank", "year"])

        # Ensure colleges exist for all canonical names in cutoffs
        unique_colleges = df["institute_canonical"].astype(str).unique()
        college_ids: dict[str, int] = {}
        to_create = []
        for name in unique_colleges:
            name = name.strip()
            if not name:
                continue
            if College.objects.filter(canonical_name=name).exists():
                college_ids[name] = College.objects.get(canonical_name=name).pk
            else:
                extra = college_meta.get(name, {})
                cat = extra.get("category") or infer_college_category(name)
                if cat not in dict(College.Category.choices):
                    cat = College.Category.OTHER
                state = str(extra.get("state") or infer_college_state(name) or "")[:128]
                to_create.append(
                    College(
                        canonical_name=name,
                        category=cat,
                        state=state,
                    )
                )
        if to_create:
            College.objects.bulk_create(to_create, ignore_conflicts=True)
        for name in unique_colleges:
            name = name.strip()
            if name and name not in college_ids:
                college_ids[name] = College.objects.get(canonical_name=name).pk

        self.stdout.write(f"  {len(college_ids)} colleges ready")

        # Programs: unique per college + program_name + branch
        program_keys = df[["institute_canonical", "program_name", "branch_canonical"]].drop_duplicates()
        program_ids: dict[tuple[str, str, str], int] = {}
        programs_to_create = []
        for _, row in program_keys.iterrows():
            cname = str(row["institute_canonical"]).strip()
            pname = str(row["program_name"]) if pd.notna(row["program_name"]) else "Unknown"
            branch = get_correct_branch_canonical(pname)
            key = (cname, pname, str(row["branch_canonical"]) if pd.notna(row["branch_canonical"]) else "")
            college_id = college_ids.get(cname)
            if not college_id:
                continue
            existing = Program.objects.filter(
                college_id=college_id, program_name=pname, branch_canonical=branch
            ).first()
            if existing:
                program_ids[key] = existing.pk
            else:
                programs_to_create.append(
                    Program(college_id=college_id, program_name=pname, branch_canonical=branch)
                )
        if programs_to_create:
            Program.objects.bulk_create(programs_to_create, ignore_conflicts=True)
        for _, row in program_keys.iterrows():
            cname = str(row["institute_canonical"]).strip()
            pname = str(row["program_name"]) if pd.notna(row["program_name"]) else "Unknown"
            branch = str(row["branch_canonical"]) if pd.notna(row["branch_canonical"]) else ""
            key = (cname, pname, branch)
            if key not in program_ids:
                prog = Program.objects.get(
                    college_id=college_ids[cname], program_name=pname, branch_canonical=branch
                )
                program_ids[key] = prog.pk

        self.stdout.write(f"  {len(program_ids)} programs ready")

        Cutoff.objects.all().delete()
        buffer: list[Cutoff] = []
        total = 0

        cols = [
            "institute_canonical",
            "program_name",
            "branch_canonical",
            "year",
            "round",
            "category",
            "quota",
            "gender",
            "opening_rank",
            "closing_rank",
            "source",
            "exam_type",
            "rank_type",
        ]
        for chunk_start in range(0, len(df), 100_000):
            chunk = df.iloc[chunk_start : chunk_start + 100_000]
            for row in chunk[cols].itertuples(index=False, name=None):
                cname = str(row[0]).strip()
                pname = str(row[1]) if pd.notna(row[1]) else "Unknown"
                branch = str(row[2]) if pd.notna(row[2]) else ""
                pid = program_ids.get((cname, pname, branch))
                if not pid:
                    continue
                closing = int(float(row[9]))
                opening = int(float(row[8])) if pd.notna(row[8]) else None
                buffer.append(
                    Cutoff(
                        program_id=pid,
                        year=int(row[3]),
                        round=int(row[4]) if pd.notna(row[4]) else 1,
                        category=str(row[5])[:32],
                        quota=str(row[6])[:32],
                        gender=str(row[7] or "GENDER_NEUTRAL")[:32],
                        opening_rank=opening,
                        closing_rank=closing,
                        exam_type=str(row[11])[:32] if pd.notna(row[11]) else "JEE_MAIN",
                        rank_type=str(row[12])[:64] if pd.notna(row[12]) else "JEE_MAIN_CRL",
                        source=str(row[10] or "")[:64],
                    )
                )
                if len(buffer) >= batch_size:
                    Cutoff.objects.bulk_create(buffer, ignore_conflicts=True)
                    total += len(buffer)
                    buffer.clear()
                    self.stdout.write(f"  inserted {total} cutoffs...", ending="\r")

        if buffer:
            Cutoff.objects.bulk_create(buffer, ignore_conflicts=True)
            total += len(buffer)

        self.stdout.write(self.style.SUCCESS(f"\n  cutoffs loaded: {total}"))

    def _print_stats(self) -> None:
        self.stdout.write(self.style.SUCCESS("--- Database stats ---"))
        self.stdout.write(f"Colleges: {College.objects.count()}")
        self.stdout.write(f"Programs: {Program.objects.count()}")
        self.stdout.write(f"Cutoffs:  {Cutoff.objects.count()}")
