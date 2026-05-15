import json
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "skincare_docs"
INDEX_FILE = BASE_DIR / "local_kb.json"

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


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def tokenize(text: str) -> list[str]:
    return [
        token for token in normalize_text(text).split()
        if len(token) > 2 and token not in STOPWORDS
    ]


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


def build_local_index() -> list[dict]:
    sections = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        sections.extend(parse_sections(path))

    INDEX_FILE.write_text(
        json.dumps(sections, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return sections


class GlowAIEngine:
    def __init__(self):
        self.sections = []
        self._ready = False

    def load(self):
        try:
            if INDEX_FILE.exists():
                self.sections = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            else:
                self.sections = build_local_index()

            self._ready = bool(self.sections)
            print(f"GlowAI ready with {len(self.sections)} knowledge sections.")
            return self._ready
        except Exception as exc:
            print(f"Error loading engine: {exc}")
            self.sections = []
            self._ready = False
            return False

    def _score_section(self, question: str, question_tokens: list[str], section: dict) -> float:
        if not question_tokens:
            return 0.0

        score = 0.0
        title_key = section.get("title_key", "")
        body = section.get("body", "")
        body_lower = body.lower()
        token_set = set(section.get("tokens", []))

        for token in question_tokens:
            if token in title_key:
                score += 5
            if token in token_set:
                score += 2
            if token in body_lower:
                score += 1

        normalized_question = normalize_text(question)
        if title_key and title_key in normalized_question:
            score += 8

        question_has_routine = any(term in normalized_question for term in ("routine", "morning", "night", "evening"))
        if question_has_routine and "routine" in body_lower:
            score += 4

        question_has_mix = any(term in normalized_question for term in ("mix", "combine", "layer", "compatible"))
        if question_has_mix and ("compatible with" in body_lower or "avoid mixing" in body_lower or "do not mix" in body_lower):
            score += 4

        question_has_start = any(term in normalized_question for term in ("start", "begin", "introduce"))
        if question_has_start and ("how to start" in body_lower or "frequency" in body_lower):
            score += 4

        return score

    def _line_score(self, block: str, question_tokens: list[str], question: str) -> float:
        block_lower = block.lower()
        score = 0.0

        for token in question_tokens:
            if token in block_lower:
                score += 2

        for prefix in (
            "benefits:", "best for:", "use time:", "compatible with:",
            "avoid mixing with:", "do not use with:", "how to start:",
            "frequency:", "routine for", "morning routine:", "evening routine:",
            "anti-aging morning routine:", "anti-aging evening routine:",
            "spot treatments:", "what not to do:"
        ):
            if block_lower.startswith(prefix):
                score += 3

        if any(term in question.lower() for term in ("routine", "steps")) and re.match(r"^\d+\.", block.strip()):
            score += 4

        return score

    def _extract_blocks(self, section: dict, question_tokens: list[str], question: str) -> list[str]:
        lines = [line.strip() for line in section["body"].splitlines() if line.strip()]
        blocks = []
        i = 0

        while i < len(lines):
            line = lines[i]
            block_lines = [line]

            if line.endswith(":"):
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if re.match(r"^(\d+\.|-)", next_line):
                        block_lines.append(next_line)
                        j += 1
                    else:
                        break
                i = j
            else:
                i += 1

            block = "\n".join(block_lines)
            score = self._line_score(block, question_tokens, question)
            blocks.append((score, block))

        ranked = [block for score, block in sorted(blocks, key=lambda item: item[0], reverse=True) if score > 0]
        if ranked:
            return ranked[:4]
        return lines[:3]

    def _build_answer(self, question: str, matches: list[dict]) -> str:
        top_match = matches[0]
        question_tokens = tokenize(question)
        lead = f"Here is the best guidance I found for {top_match['title'].lower()}:"

        points = []
        seen = set()

        for match in matches[:2]:
            for block in self._extract_blocks(match, question_tokens, question):
                clean_block = block.strip()
                if clean_block and clean_block not in seen:
                    seen.add(clean_block)
                    points.append(clean_block)
                if len(points) >= 4:
                    break
            if len(points) >= 4:
                break

        formatted_points = []
        for point in points:
            if "\n" in point:
                first, *rest = point.splitlines()
                formatted_points.append(f"- {first}")
                for subpoint in rest[:4]:
                    formatted_points.append(f"  {subpoint}")
            else:
                formatted_points.append(f"- {point}")

        closing = ""
        if any(flag in normalize_text(question).split() for flag in MEDICAL_FLAGS):
            closing = "\n\nPlease consider a dermatologist for severe, persistent, painful, or pregnancy-related skin concerns."

        return lead + "\n" + "\n".join(formatted_points[:8]) + closing

    def ask(self, question: str) -> dict:
        if not self._ready:
            return {
                "answer": "GlowAI could not load its local knowledge base.",
                "sources": [],
                "time_taken": 0,
            }

        start = time.time()
        question_tokens = tokenize(question)
        scored = []

        for section in self.sections:
            score = self._score_section(question, question_tokens, section)
            if score > 0:
                scored.append((score, section))

        scored.sort(key=lambda item: item[0], reverse=True)

        if not scored:
            elapsed = round(time.time() - start, 1)
            return {
                "answer": (
                    "I do not have a precise match for that in the current GlowAI knowledge base yet. "
                    "Try asking about a skin type, routine step, ingredient, dark spots, acne, pores, "
                    "sunscreen, or retinol."
                ),
                "sources": [],
                "time_taken": elapsed,
            }

        matches = [section for _, section in scored[:3]]
        elapsed = round(time.time() - start, 1)

        return {
            "answer": self._build_answer(question, matches),
            "sources": list(dict.fromkeys(section["source"] for section in matches)),
            "time_taken": elapsed,
        }


engine = GlowAIEngine()
