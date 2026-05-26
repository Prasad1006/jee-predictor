from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ingest counselling markdown into ChromaDB for RAG"

    def handle(self, *args, **options):
        try:
            from ai_engine.rag.ingest import ingest_chroma

            count = ingest_chroma()
            self.stdout.write(self.style.SUCCESS(f"Ingested {count} chunks into ChromaDB"))
        except ImportError:
            from ai_engine.rag.ingest import load_documents

            docs = load_documents()
            self.stdout.write(
                self.style.WARNING(
                    f"chromadb not installed — using keyword fallback ({len(docs)} chunks in memory). "
                    "Run: pip install chromadb"
                )
            )
