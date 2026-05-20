# 🌿 GlowAI — AI-Powered Skincare Assistant

<div align="center">

![GlowAI](https://img.shields.io/badge/GlowAI-Skincare%20Intelligence-c8775a?style=for-the-badge&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-FF6B35?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-Sentence%20Transformers-1C3C3C?style=for-the-badge)
![Reddit](https://img.shields.io/badge/Reddit-Live%20Reviews-FF4500?style=for-the-badge&logo=reddit&logoColor=white)

**A free, intelligent skincare AI that combines a curated knowledge base, semantic search, live Reddit reviews, and Groq LLaMA3 to give warm, personalized skincare advice.**

[Features](#-features) • [Demo](#-demo) • [Tech Stack](#-tech-stack) • [Getting Started](#-getting-started) • [How It Works](#-how-it-works) • [Project Structure](#-project-structure)

</div>

---

## ✨ Features

- 🤖 **AI Chat** — Ask anything about skincare, routines, ingredients, and concerns
- 🧠 **Semantic RAG** — Answers grounded in a curated skincare knowledge base using sentence-transformers
- 💬 **Live Reddit Reviews** — Pulls real community opinions from r/SkincareAddiction and r/IndianSkincareAddicts
- ⚡ **Groq LLaMA3** — Fast, warm, opinionated answers in under 3 seconds
- 🎙 **Voice Input** — Speak your question using your microphone (Chrome/Edge)
- 📷 **Skin Photo Upload** — Upload a photo for visual skin analysis
- 🆘 **Emergency Help** — GPS-based dermatologist finder with hospital contacts
- 🇮🇳 **India-focused** — Tailored for Indian skin tones, budget brands, and Indian climate
- 💰 **Completely Free** — Groq free tier, no credit card required

---

## 🎬 Demo

```
User: "I have oily skin with lots of pimples, what should I use?"

GlowAI: "Okay so for oily + acne-prone skin, salicylic acid is your best friend.
Get the Minimalist 2% BHA — people on r/IndianSkincareAddicts swear by it and
it's only ₹349. Use it 3 nights a week after cleansing. Pair it with a
niacinamide serum and always wear SPF in the morning. Trust me, give it
3 weeks and you'll see a real difference!"

📚 Sources: Concerns · Skin Types · r/IndianSkincareAddicts · r/SkincareAddiction
```

---

## 🛠 Tech Stack

| Layer            | Technology                               | Purpose                        |
| ---------------- | ---------------------------------------- | ------------------------------ |
| **Frontend**     | HTML, CSS, JavaScript                    | Luxury warm UI with animations |
| **Backend**      | Python, Flask                            | API server and routing         |
| **LLM**          | Groq API (LLaMA 3.1 8B)                  | Answer generation              |
| **Embeddings**   | sentence-transformers `all-MiniLM-L6-v2` | Semantic search                |
| **Vector Store** | Custom JSON index                        | Knowledge retrieval            |
| **Live Data**    | Reddit JSON API                          | Real user reviews              |
| **Voice**        | Web Speech API                           | Microphone input               |
| **Vision**       | Base64 image passing                     | Skin photo analysis            |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or newer
- Chrome or Edge browser (for voice input)
- Free Groq API key

### Step 1 — Clone the repo

```bash
git clone https://github.com/Ankitajena12/glowai.git
cd glowai
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Get your free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with Google — no credit card needed
3. Click **API Keys** → **Create API Key**
4. Copy it — looks like `gsk_xxxxxxxxxxxxxxxx`

### Step 4 — Add your key to `.env`

Create `backend/.env`:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

### Step 5 — Build the knowledge database

```bash
python backend/build_db.py
```

### Step 6 — Launch!

```bash
python backend/app.py
```

Open **http://localhost:5000** 🌿

---

## 🧠 How It Works

Every question goes through a 3-step pipeline:

```
User Question
      ↓
① SEMANTIC SEARCH
  sentence-transformers embeds the question
  → searches local_kb.json for top 4 matching chunks
      ↓
② LIVE REDDIT FETCH
  Reddit JSON API searches r/SkincareAddiction
  + r/IndianSkincareAddicts for real community reviews
      ↓
③ GROQ GENERATION
  Knowledge base chunks + Reddit posts sent to LLaMA3
  → warm, specific, India-aware answer generated
      ↓
  Answer displayed with clickable source pills
```

### Why this approach?

- **Semantic search** finds relevant knowledge even when exact words don't match
- **Reddit integration** adds real-world validation — not just textbook advice
- **Groq** generates fluent, opinionated answers fast and for free
- **No hallucination** — model only answers from retrieved context

---

## 📁 Project Structure

```
glowai/
│
├── backend/
│   ├── templates/
│   │   └── index.html          # Frontend — luxury warm UI
│   ├── app.py                  # Flask server & API routes
│   ├── rag_engine.py           # RAG pipeline + Groq + Reddit
│   ├── build_db.py             # Builds local_kb.json index
│   └── .env                    # API keys (gitignored)
│
├── skincare_docs/              # Knowledge base
│   ├── skin_types.txt          # Oily, dry, combination, sensitive
│   ├── ingredients.txt         # Retinol, niacinamide, Vitamin C etc.
│   ├── concerns.txt            # Acne, dark spots, aging, rosacea
│   ├── india_guide.txt         # Indian skin, brands, climate, budget
│   └── routines_lifestyle.txt  # AM/PM routines, diet, lifestyle
│
├── local_kb.json               # Auto-generated vector index (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🌐 API Endpoints

| Method | Route         | Description           |
| ------ | ------------- | --------------------- |
| `GET`  | `/`           | Serves the frontend   |
| `POST` | `/ask`        | Main AI chat endpoint |
| `GET`  | `/api/health` | Engine status check   |

### `/ask` Request

```json
{
  "question": "What routine suits oily skin?",
  "image": "data:image/jpeg;base64,..."
}
```

### `/ask` Response

```json
{
  "answer": "For oily skin, start with a BHA...",
  "sources": ["Skin Types", "r/SkincareAddiction"],
  "time": 1.4,
  "reddit_posts": [
    {
      "title": "Best products for oily skin?",
      "url": "https://reddit.com/...",
      "subreddit": "SkincareAddiction",
      "score": 847
    }
  ]
}
```

---

## 📖 Knowledge Base

| File                     | Topics Covered                                                |
| ------------------------ | ------------------------------------------------------------- |
| `skin_types.txt`         | Oily, dry, combination, sensitive, normal + how to identify   |
| `ingredients.txt`        | 15+ ingredients with benefits, usage, combinations            |
| `concerns.txt`           | Acne, hyperpigmentation, aging, rosacea, eczema, dark circles |
| `india_guide.txt`        | South Asian skin, Indian brands, climate, home remedies       |
| `routines_lifestyle.txt` | AM/PM routines, exfoliation, diet, sleep, lifestyle           |

Add any `.txt` file to `skincare_docs/` and run `build_db.py` again to expand the knowledge base.

---

## 🆘 Emergency Dermatologist Finder

- **GPS finder** — detects location and opens Google Maps with nearby dermatologists
- **Bhubaneswar hospitals** — AIIMS, KIMS, SUM Hospital, Hi-Tech Medical College
- **National helplines** — 104 (Health Helpline), 108 (Ambulance), IADVL
- **Teleconsult** — Practo, 1mg, Apollo 24/7

---

## 🎙 Voice & 📷 Image Features

**Voice Input:**

- Click 🎙 mic button → speak your question
- Transcribed text fills input automatically
- Chrome and Edge only (Web Speech API)
- Indian English (`en-IN`) language model

**Image Upload:**

- Click 📷 to upload a skin photo
- Preview thumbnail shown before sending
- Analyzed by Groq for skin concerns
- Works with or without a text question

---

## ⚙️ Configuration

In `backend/rag_engine.py`:

```python
GROQ_MODEL_NAME  = "llama-3.1-8b-instant"  # Groq model
TOP_K            = 4                         # KB chunks per query
REDDIT_MAX_POSTS = 3                         # Reddit posts to fetch
REDDIT_MAX_CHARS = 300                       # Characters per post
```

---

## 💻 System Requirements

| Spec     | Requirement              |
| -------- | ------------------------ |
| RAM      | 2 GB minimum             |
| Storage  | 500 MB                   |
| GPU      | Not required             |
| Internet | Required (Groq + Reddit) |
| Browser  | Chrome or Edge           |

---

## ⚠️ Disclaimer

GlowAI is an AI-powered assistant and is **not a substitute for professional medical advice**. Always consult a qualified dermatologist for diagnosis and treatment of skin conditions.

---

## 👩‍💻 Author

**P .Ankita Jena**
B.Tech — Artificial Intelligence & Machine Learning|
Sri Sri University, Cuttack, Odisha

[![GitHub](https://img.shields.io/badge/GitHub-Ankitajena12-181717?style=flat&logo=github)](https://github.com/Ankitajena12)

**Aditya Das**
B.Tech — Computer Sciene Enginerring|
SOA University, Bhubaneswar, Odisha
[![GitHub](https://img.shields.io/badge/GitHub-SaVvyCE-181717?style=flat&logo=github)](https://github.com/SaVvyCE)

---

<div align="center">
  Made with 🌿 and Python · GlowAI 2025
</div>
