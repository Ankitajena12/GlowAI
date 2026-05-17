import json
import math
import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "skincare_docs"
INDEX_FILE = BASE_DIR / "local_kb.json"

if load_dotenv:
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL_NAME = os.getenv("GLOWAI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
TOP_K = int(os.getenv("GLOWAI_TOP_K", "4"))

# Reddit subreddits to search
REDDIT_SUBS = "SkincareAddiction+IndianSkincareAddicts+AsianBeauty+tretinoin"
REDDIT_HEADERS = {"User-Agent": "GlowAI/1.0 (skincare assistant)"}
REDDIT_MAX_POSTS = 3      # number of Reddit posts to fetch
REDDIT_MAX_CHARS = 300    # max characters per post to send to Groq


def fetch_reddit(question: str) -> list[dict]:
    """
    Fetch top Reddit posts for a skincare question.
    Uses Reddit's public JSON API — no auth needed.
    Returns list of {title, text, url, subreddit, score}
    """
    try:
        query = urllib.parse.quote(question)
        url = (
            f"https://www.reddit.com/r/{REDDIT_SUBS}/search.json"
            f"?q={query}&sort=relevance&limit={REDDIT_MAX_POSTS}"
            f"&restrict_sr=1&type=link"
        )
        req = urllib.request.Request(url, headers=REDDIT_HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title     = post.get("title", "").strip()
            selftext  = post.get("selftext", "").strip()
            permalink = post.get("permalink", "")
            subreddit = post.get("subreddit", "")
            score     = post.get("score", 0)

            # Skip deleted/removed/empty posts
            if not title or selftext in ("", "[removed]", "[deleted]"):
                text = title  # use title only
            else:
                text = selftext[:REDDIT_MAX_CHARS]

            if title:
                posts.append({
                    "title":     title,
                    "text":      text,
                    "url":       f"https://reddit.com{permalink}",
                    "subreddit": subreddit,
                    "score":     score,
                })

        return posts

    except Exception as exc:
        print(f"Reddit fetch failed (non-critical): {exc}")
        return []

STOPWORDS = {
    "a", "about", "all", "am", "an", "and", "are", "as", "at", "be", "best",
    "but", "by", "can", "do", "for", "from", "get", "how", "i", "if", "in",
    "into", "is", "it", "me", "my", "of", "on", "or", "should", "so", "that",
    "the", "their", "them", "this", "to", "use", "what", "when", "which",
    "with", "you", "your"
}

MEDICAL_FLAGS = {
    "cyst", "cystic", "eczema", "infection", "melasma", "nodules", "nodule",
    "painful", "persistent", "pregnancy", "pregnant", "psoriasis", "rash",
    "rosacea", "severe", "swelling"
}


def load_environment() -> None:
    if load_dotenv:
        load_dotenv(BACKEND_DIR / ".env")
        load_dotenv(BASE_DIR / ".env")


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def tokenize(text: str) -> list[str]:
    return [
        token for token in normalize_text(text).split()
        if len(token) > 2 and token not in STOPWORDS
    ]


def section_text(section: dict) -> str:
    return f"{section.get('title', '')}\n{section.get('body', '')}".strip()


def display_source(source: str) -> str:
    return Path(source).stem.replace("_", " ").title()


def parse_sections(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    sections = []
    current_title = path.stem.replace("_", " ").title()
    current_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("==") and line.endswith("=="):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(
                        {
                            "title": current_title,
                            "source": path.name,
                            "body": body,
                        }
                    )
            current_title = line.strip("= ").strip()
            current_lines = []
            continue

        if line:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(
                {
                    "title": current_title,
                    "source": path.name,
                    "body": body,
                }
            )

    for section in sections:
        section["title_key"] = normalize_text(section["title"])
        section["tokens"] = tokenize(section["title"] + " " + section["body"])

    return sections


def get_sentence_transformer():
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception as exc:
        print(f"Online model load failed, trying local cache only: {exc}")
        return SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)


def add_embeddings(sections: list[dict], embedder=None) -> list[dict]:
    if not sections:
        return sections

    model = embedder or get_sentence_transformer()
    embeddings = model.encode(
        [section_text(section) for section in sections],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    for section, embedding in zip(sections, embeddings):
        section["embedding"] = [float(value) for value in embedding]

    return sections


def build_local_index(embedder=None) -> list[dict]:
    sections = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        sections.extend(parse_sections(path))

    add_embeddings(sections, embedder=embedder)
    INDEX_FILE.write_text(
        json.dumps(sections, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return sections


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class GlowAIEngine:
    def __init__(self):
        self.sections = []
        self.embedder = None
        self.groq_client = None
        self._ready = False
        self._groq_ready = False
        self.embedding_model = EMBEDDING_MODEL_NAME
        self.groq_model = GROQ_MODEL_NAME

    def load(self):
        try:
            load_environment()
            self.embedder = get_sentence_transformer()

            if INDEX_FILE.exists():
                self.sections = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
                if self.sections and not self.sections[0].get("embedding"):
                    add_embeddings(self.sections, embedder=self.embedder)
                    INDEX_FILE.write_text(
                        json.dumps(self.sections, indent=2, ensure_ascii=True),
                        encoding="utf-8",
                    )
            else:
                self.sections = build_local_index(embedder=self.embedder)

            groq_api_key = os.getenv("GROQ_API_KEY")
            if groq_api_key:
                from groq import Groq

                self.groq_client = Groq(api_key=groq_api_key)
                self._groq_ready = True
            else:
                self.groq_client = None
                self._groq_ready = False
                print("GROQ_API_KEY is not set. Retrieval will work, but Groq answers are disabled.")

            self._ready = bool(self.sections)
            print(
                "GlowAI ready with "
                f"{len(self.sections)} embedded sections using {self.embedding_model}."
            )
            return self._ready
        except Exception as exc:
            print(f"Error loading engine: {exc}")
            self.sections = []
            self.embedder = None
            self.groq_client = None
            self._ready = False
            self._groq_ready = False
            return False

    def _retrieve(self, question: str) -> list[dict]:
        question_embedding = self.embedder.encode(
            question,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        question_vector = [float(value) for value in question_embedding]

        scored = []
        question_tokens = set(tokenize(question))
        for section in self.sections:
            score = cosine_similarity(question_vector, section.get("embedding", []))
            token_overlap = question_tokens.intersection(section.get("tokens", []))
            if token_overlap:
                score += min(len(token_overlap), 4) * 0.03
            scored.append((score, section))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {**section, "score": round(score, 4)}
            for score, section in scored[:TOP_K]
            if score > 0.15
        ]

    def _fallback_answer(self, question: str, matches: list[dict], reason: str = "") -> str:
        if not matches:
            return (
                "I could not find a strong match in the current GlowAI knowledge base. "
                "Try asking about skin type, acne, dark spots, sunscreen, retinol, pores, "
                "or a morning/evening routine."
            )

        lead = "I found relevant skincare guidance from the GlowAI knowledge base."
        if reason:
            lead += f" {reason}"

        points = []
        for match in matches[:2]:
            body_lines = [line.strip() for line in match["body"].splitlines() if line.strip()]
            for line in body_lines[:3]:
                points.append(f"- {line}")

        closing = ""
        if any(flag in normalize_text(question).split() for flag in MEDICAL_FLAGS):
            closing = "\n\nPlease consider a dermatologist for severe, persistent, painful, or pregnancy-related skin concerns."

        return lead + "\n" + "\n".join(points[:6]) + closing

    def _answer_with_groq(self, question: str, matches: list[dict], reddit_posts: list[dict] = None) -> str:
        # Knowledge base context
        context_blocks = []
        for index, match in enumerate(matches, start=1):
            context_blocks.append(
                f"[{index}] Title: {match['title']}\n"
                f"Source: {match['source']}\n"
                f"Content:\n{match['body']}"
            )

        # Reddit context
        reddit_block = ""
        if reddit_posts:
            reddit_lines = []
            for post in reddit_posts:
                reddit_lines.append(
                    f"• r/{post['subreddit']} ({post['score']} upvotes): "
                    f"\"{post['title']}\" — {post['text']}"
                )
            reddit_block = (
                "\n\nReal user reviews and discussions from Reddit:\n"
                + "\n".join(reddit_lines)
            )

        medical_note = ""
        if any(flag in normalize_text(question).split() for flag in MEDICAL_FLAGS):
            medical_note = (
                " At the end, gently recommend seeing a dermatologist since this sounds "
                "like it needs professional attention."
            )

        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are GlowAI — a knowledgeable, warm, and opinionated skincare best friend. "
                        "You speak like a real person who genuinely cares, not like a medical textbook. "
                        "You give specific, confident advice — actual product names, exact percentages, "
                        "clear steps — not vague generalities. "
                        "You are deeply familiar with Indian and South Asian skin — you know Indian brands "
                        "like Minimalist, Plum, Dot & Key, Dr. Sheth's, the intense UV in India, common "
                        "concerns like PIH and melasma on darker skin tones, and budget constraints. "
                        "Your tone is warm, direct and encouraging — like texting a friend who happens "
                        "to be a skincare expert. Use casual language, occasional emphasis, and don't "
                        "be afraid to say things like 'honestly', 'trust me', 'this is the one thing I swear by'. "
                        "Give real opinions — if something is overhyped say so, if it's a game changer say that too. "
                        "When Reddit data is provided, mention what real users are saying — "
                        "quote or paraphrase interesting community opinions naturally in your answer, "
                        "like 'people on r/SkincareAddiction swear by this' or 'the Indian skincare community loves X'. "
                        "Always answer using the provided knowledge base first, then enrich with Reddit insights. "
                        "If context is not enough, say so honestly instead of making things up."
                        + medical_note
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Knowledge base context:\n\n"
                        + "\n\n---\n\n".join(context_blocks)
                        + reddit_block
                        + f"\n\nMy question: {question}"
                    ),
                },
            ],
            temperature=0.7,
            max_tokens=700,
        )
        return response.choices[0].message.content.strip()

    def ask(self, question: str) -> dict:
        if not self._ready or not self.embedder:
            return {
                "answer": "GlowAI could not load its SentenceTransformer knowledge base.",
                "sources": [],
                "time_taken": 0,
            }

        start = time.time()

        # Retrieve from knowledge base + fetch Reddit in parallel
        matches = self._retrieve(question)
        reddit_posts = fetch_reddit(question)

        sources = list(dict.fromkeys(display_source(section["source"]) for section in matches))

        # Add Reddit sources
        if reddit_posts:
            for post in reddit_posts:
                reddit_src = f"r/{post['subreddit']}"
                if reddit_src not in sources:
                    sources.append(reddit_src)

        if not matches:
            elapsed = round(time.time() - start, 1)
            return {
                "answer": self._fallback_answer(question, matches),
                "sources": [],
                "time_taken": elapsed,
            }

        if not self._groq_ready or not self.groq_client:
            answer = self._fallback_answer(question, matches)
        else:
            try:
                answer = self._answer_with_groq(question, matches, reddit_posts=reddit_posts)
            except Exception as exc:
                print(f"Groq request failed: {exc}")
                answer = self._fallback_answer(question, matches)

        elapsed = round(time.time() - start, 1)
        return {
            "answer":       answer,
            "sources":      sources,
            "time_taken":   elapsed,
            "reddit_posts": [
                {"title": p["title"], "url": p["url"], "subreddit": p["subreddit"], "score": p["score"]}
                for p in reddit_posts
            ],
        }


engine = GlowAIEngine()