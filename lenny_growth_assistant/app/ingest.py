
from pathlib import Path
from sqlalchemy import delete

from app.db import Base, engine, SessionLocal
from app.models import TranscriptChunk
from app.retrieval import split_text

PROJECT_DIR = Path(__file__).resolve().parent.parent

# GitHub repository location
TRANSCRIPT_DIR = PROJECT_DIR / "data" / "source_transcripts"

# Fallback for transcripts stored directly in data/transcripts
FALLBACK_DIR = PROJECT_DIR / "data" / "transcripts"


def find_transcripts():
    paths = []

    for folder in [TRANSCRIPT_DIR, FALLBACK_DIR]:
        if folder.exists():
            paths.extend(folder.rglob("*.md"))
            paths.extend(folder.rglob("*.txt"))

    # Avoid duplicates and skip common non-transcript files
    ignored_names = {
        "readme.md",
        "license.md",
        "contributing.md",
    }

    unique_paths = {
        path.resolve()
        for path in paths
        if path.name.lower() not in ignored_names
        and ".git" not in path.parts
    }

    return sorted(unique_paths)


def main():
    paths = find_transcripts()

    if not paths:
        print("No transcript files found.")
        print(f"Check this folder: {TRANSCRIPT_DIR}")
        return

    print(f"Found {len(paths)} possible transcript files.")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        for path in paths:
            # Use a relative path to distinguish episodes
            source_name = str(path.relative_to(PROJECT_DIR))

            text = path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).strip()

            if not text:
                print(f"Skipping empty file: {source_name}")
                continue

            chunks = split_text(text)

            # Replace previously ingested chunks for this file
            db.execute(
                delete(TranscriptChunk).where(
                    TranscriptChunk.source_name == source_name
                )
            )

            for index, chunk in enumerate(chunks):
                db.add(
                    TranscriptChunk(
                        source_name=source_name,
                        chunk_index=index,
                        content=chunk
                    )
                )

            print(f"Processed {source_name}: {len(chunks)} chunks")

        db.commit()
        print("Transcript ingestion completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
