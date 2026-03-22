"""
CLI script to ingest documents into the vector store.
Usage: python scripts/ingest.py --docs-dir data/sample_docs
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from src.pipeline import RAGPipeline

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into RAG knowledge base")
    parser.add_argument("--docs-dir", type=str, default="data/sample_docs", help="Directory with documents")
    parser.add_argument("--reset", action="store_true", help="Wipe existing collection before ingesting")
    args = parser.parse_args()

    console.print(f"\n[bold blue]RAG Ingestion Pipeline[/bold blue]")
    console.print(f"Directory: {args.docs_dir}")

    pipeline = RAGPipeline()

    if args.reset:
        console.print("[yellow]Resetting collection...[/yellow]")
        pipeline.vector_store.delete_collection()
        from src.ingestion.vector_store import VectorStore
        pipeline.vector_store = VectorStore()

    console.print("[cyan]Loading documents...[/cyan]")
    count = pipeline.ingest_directory(args.docs_dir)

    table = Table(title="Ingestion Complete")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Chunks added", str(count))
    table.add_row("Total in store", str(pipeline.vector_store.count()))
    table.add_row("Collection", pipeline.vector_store.collection_name)

    console.print(table)


if __name__ == "__main__":
    main()