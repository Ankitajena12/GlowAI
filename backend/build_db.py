from rag_engine import INDEX_FILE, build_local_index


def build():
    sections = build_local_index()
    print(f"Built local GlowAI SentenceTransformer index with {len(sections)} sections.")
    print(f"Saved to {INDEX_FILE}")


if __name__ == "__main__":
    build()
