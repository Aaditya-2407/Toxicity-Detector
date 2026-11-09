# CyberGuard — Toxicity Detector

A Flask web application that scores user comments for toxicity in real time using a locally-hosted [Toxic-BERT](https://huggingface.co/unitary/toxic-bert) model (Jigsaw Toxic Comment Classification). Comments are scored across **6 categories** and combined into a single weighted composite score.

---

## Features

| Feature | Detail |
|---|---|
| **Real-time preview** | Score updates as you type (400 ms debounce, no page reload) |
| **6-category breakdown** | Per-label confidence bars on every comment card |
| **Polygon radar chart** | Hexagonal chart mapping all 6 toxicity dimensions per comment |
| **Threshold colour bands** | Green / Amber / Red system across the whole UI |
| **Feed filter** | Show all / safe / caution / toxic comments |
| **Leaderboard** | Ranked by average composite toxicity with medal icons |
| **Auth** | Register + login with hashed passwords (Flask-Login + Werkzeug) |
| **Local model** | Toxic-BERT runs entirely on-device — no external API calls |

---

## Scoring System

### The 6 Categories

Toxic-BERT was trained on the [Jigsaw Toxic Comment Classification Challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge) dataset. It outputs an independent probability for each label:

| Index | Label | Description |
|---|---|---|
| 0 | `toxic` | General hostility, rudeness |
| 1 | `severe_toxic` | Extreme abuse or dehumanisation |
| 2 | `obscene` | Explicit or profane language |
| 3 | `threat` | Direct or implied threats of harm |
| 4 | `insult` | Personal attacks on an individual |
| 5 | `identity_hate` | Attacks targeting identity (race, religion, gender, etc.) |

### Composite Score (Weighted Sum)

Rather than taking the raw maximum, CyberGuard computes a **weighted sum** so that high-severity categories (threat, severe toxicity) contribute more than low-severity ones (isolated obscenity):

```
composite = Σ (score_i × weight_i)
```

| Category | Weight | Rationale |
|---|---|---|
| `severe_toxic` | **0.30** | Highest severity — dehumanisation |
| `threat` | **0.25** | Implies direct harm |
| `toxic` | **0.20** | General baseline toxicity |
| `identity_hate` | **0.12** | Targeted discrimination |
| `insult` | **0.08** | Personal attacks |
| `obscene` | **0.05** | Explicit language in isolation |

Weights sum to **1.00**. The composite is always in `[0, 1]`.

### Threshold Bands

| Band | Range | Colour | Meaning |
|---|---|---|---|
| **Safe** | 0.00 – 0.40 | 🟢 Green | No flags raised; content is clean |
| **Caution** | 0.40 – 0.70 | 🟡 Amber | Borderline; worth reviewing |
| **Toxic** | 0.70 – 1.00 | 🔴 Red | Flagged content |

All comments are stored and displayed regardless of score — the bands are informational, not a hard block.

---

## Architecture

```
CEP-Project/
├── app/
│   ├── __init__.py          # App factory
│   ├── extensions.py        # db, migrate, login singletons
│   ├── models.py            # User + Comment (with 6 score columns)
│   ├── auth/
│   │   ├── routes.py        # /auth/login, /auth/register, /auth/logout
│   │   └── forms.py
│   ├── main/
│   │   ├── routes.py        # /, /leaderboard, /score-comment, /preview-score
│   │   └── forms.py
│   ├── toxic_bert/
│   │   ├── model.py         # score_comment() → { composite, scores }
│   │   └── model_files/     # local Toxic-BERT weights (not in git)
│   ├── static/css/
│   │   └── style.css
│   └── templates/
│       ├── _base.html
│       ├── index.html
│       ├── leaderboard.html
│       └── auth/
│           ├── login.html
│           └── register.html
├── migrations/              # Alembic migrations
├── config.py
├── run.py
├── download_model.py        # One-time model download helper
└── requirements.txt
```

---

## Setup

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/Aaditya-2407/Toxicity-Detector.git
cd Toxicity-Detector
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db    # or a PostgreSQL URI for production
```

### 3. Download the model weights

The model files (`model.safetensors`, `tokenizer.json`, etc.) are **not committed to git** (they are ~440 MB). Run the download helper once:

```bash
python download_model.py
```

This saves the model into `app/toxic_bert/model_files/`.

### 4. Apply database migrations

```bash
flask db upgrade
```

> **Note:** if you are upgrading from a previous version that only had the `toxicity_score` column, the migration `a1b2c3d4e5f6` adds the 6 per-category columns automatically. Existing rows will have `NULL` for sub-scores; the UI handles this gracefully.

### 5. Run the development server

```bash
flask run
# or
python run.py
```

Open [http://localhost:5000](http://localhost:5000).

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ✅ | Comment feed |
| `GET` | `/leaderboard` | ✅ | User rankings |
| `POST` | `/score-comment` | ✅ | Submit + score a comment |
| `POST` | `/preview-score` | ✅ | Score text without saving (live preview) |
| `GET/POST` | `/auth/login` | — | Login |
| `GET/POST` | `/auth/register` | — | Register |
| `GET` | `/auth/logout` | ✅ | Logout |

### `/score-comment` response

```json
{
  "success": true,
  "comment": {
    "id": 42,
    "body": "This is great!",
    "author": "alice",
    "score": 0.014,
    "timestamp": "just now",
    "scores": {
      "toxic": 0.021,
      "severe_toxic": 0.003,
      "obscene": 0.008,
      "threat": 0.002,
      "insult": 0.011,
      "identity_hate": 0.004
    }
  }
}
```

### `/preview-score` request / response

```json
// POST body
{ "text": "You're an idiot." }

// Response
{
  "composite": 0.512,
  "scores": {
    "toxic": 0.823,
    "severe_toxic": 0.102,
    "obscene": 0.311,
    "threat": 0.045,
    "insult": 0.741,
    "identity_hate": 0.019
  }
}
```

---

## Model Details

| Property | Value |
|---|---|
| Model | `unitary/toxic-bert` |
| Base | `bert-base-uncased` |
| Task | Multi-label sequence classification |
| Output | 6 independent sigmoid probabilities |
| Max tokens | 512 (longer input is truncated) |
| Framework | PyTorch + Hugging Face Transformers |

---

## Deployment Notes

- The app ships with **gunicorn** in `requirements.txt`. For production: `gunicorn -w 2 "run:app"`.
- Toxic-BERT is CPU-compatible; a GPU will make inference noticeably faster.
- Use PostgreSQL (via `psycopg2-binary`) in production — the `DATABASE_URL` in `.env` controls this.
- Flash messages on login/register errors are auto-dismissed via Bootstrap's `alert-dismissible`.

---

## Planned Enhancements

- [ ] Pentagon/polygon radar chart on the leaderboard for per-user average breakdown
- [ ] Admin panel to bulk-review flagged comments
- [ ] Export comments to CSV
- [ ] Dark mode toggle

---

## License

MIT
