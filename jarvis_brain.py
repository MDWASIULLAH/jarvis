import csv
import html
import json
import math
import os
import re
import urllib.request
import urllib.parse
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

np = None
pd = None
XGBClassifier = None
ML_LOADED = False


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "jarvis_data"
BRAIN_DIR = DATA_DIR / "brain"
DATASET_DIR = BRAIN_DIR / "datasets"
IMPORTS_DIR = DATASET_DIR / "imports"
INTENTS_FILE = DATASET_DIR / "intents.csv"
MODEL_FILE = BRAIN_DIR / "intent_model.json"
XGB_MODEL_FILE = BRAIN_DIR / "intent_xgboost.json"
KNOWLEDGE_FILE = BRAIN_DIR / "knowledge.json"


SEED_ROWS = [
    ("open youtube", "open"),
    ("opne youtub", "open"),
    ("open calculator", "open"),
    ("open notepad", "open"),
    ("scroll", "scroll"),
    ("scroll the shorts", "auto_scroll"),
    ("keep scrolling youtube shorts", "auto_scroll"),
    ("stop scrolling", "stop_scroll"),
    ("write python code for calculator", "code"),
    ("create html code for app", "code"),
    ("write email about meeting", "email_draft"),
    ("send email to alex subject update body hello", "email_send"),
    ("read link https://example.com", "read_link"),
    ("open wikipedia of python and read it", "wikipedia"),
    ("daily briefing", "news"),
    ("share news to whatsapp", "share"),
    ("terminal dir", "terminal"),
    ("run command echo hello", "terminal"),
]


def _load_ml() -> None:
    global np, pd, XGBClassifier, ML_LOADED

    if ML_LOADED:
        return
    ML_LOADED = True

    try:
        import numpy as numpy_module
        np = numpy_module
    except Exception:
        np = None

    try:
        import pandas as pandas_module
        pd = pandas_module
    except Exception:
        pd = None

    try:
        from xgboost import XGBClassifier as xgb_classifier
        XGBClassifier = xgb_classifier
    except Exception:
        XGBClassifier = None


def _ensure_dirs() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    if not INTENTS_FILE.exists():
        with INTENTS_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["text", "intent"])
            writer.writerows(SEED_ROWS)
    if not KNOWLEDGE_FILE.exists():
        KNOWLEDGE_FILE.write_text("[]", encoding="utf-8")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", (text or "").lower())


def _read_intent_rows() -> list[tuple[str, str]]:
    _ensure_dirs()
    if pd is not None:
        try:
            frame = pd.read_csv(INTENTS_FILE)
            return [
                (str(row["text"]), str(row["intent"]))
                for _, row in frame.iterrows()
                if str(row.get("text", "")).strip() and str(row.get("intent", "")).strip()
            ]
        except Exception:
            pass

    with INTENTS_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            (row.get("text", "").strip(), row.get("intent", "").strip())
            for row in reader
            if row.get("text", "").strip() and row.get("intent", "").strip()
        ]


def train_intent_model() -> dict:
    _load_ml()
    rows = _read_intent_rows()
    labels = sorted({label for _, label in rows})
    vocab = sorted({token for text, _ in rows for token in _tokenize(text)})
    vocab_index = {token: index for index, token in enumerate(vocab)}
    label_doc_counts = Counter(label for _, label in rows)
    token_counts = {label: Counter() for label in labels}
    total_tokens = Counter()

    for text, label in rows:
        tokens = _tokenize(text)
        token_counts[label].update(tokens)
        total_tokens[label] += len(tokens)

    priors = {
        label: math.log(label_doc_counts[label] / max(1, len(rows)))
        for label in labels
    }
    likelihoods = {}
    vocab_size = max(1, len(vocab))
    for label in labels:
        denom = total_tokens[label] + vocab_size
        likelihoods[label] = {
            token: math.log((token_counts[label][token] + 1) / denom)
            for token in vocab
        }

    backend_parts = ["naive_bayes"]
    xgboost_status = "not_installed"
    if np is not None:
        backend_parts.append("numpy")

    if XGBClassifier is not None and np is not None and len(labels) > 1 and len(rows) >= len(labels):
        try:
            label_index = {label: index for index, label in enumerate(labels)}
            features = np.zeros((len(rows), max(1, len(vocab))), dtype=float)
            targets = np.array([label_index[label] for _, label in rows], dtype=int)
            for row_index, (text, _) in enumerate(rows):
                for token in _tokenize(text):
                    if token in vocab_index:
                        features[row_index, vocab_index[token]] += 1.0

            classifier = XGBClassifier(
                n_estimators=36,
                max_depth=3,
                learning_rate=0.22,
                subsample=1.0,
                colsample_bytree=1.0,
                eval_metric="mlogloss",
                verbosity=0,
            )
            classifier.fit(features, targets)
            classifier.save_model(str(XGB_MODEL_FILE))
            backend_parts.append("xgboost")
            xgboost_status = "trained"
        except Exception as error:
            xgboost_status = f"failed: {error}"
    elif XGBClassifier is not None:
        xgboost_status = "needs_numpy_and_more_examples"

    model = {
        "backend": "+".join(backend_parts),
        "xgboost_status": xgboost_status,
        "labels": labels,
        "vocab": vocab,
        "priors": priors,
        "likelihoods": likelihoods,
        "rows": len(rows),
    }
    MODEL_FILE.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return {
        "rows": len(rows),
        "labels": labels,
        "vocab_size": len(vocab),
        "backend": "+".join(backend_parts),
        "xgboost_status": xgboost_status,
    }


def load_intent_model() -> dict:
    _ensure_dirs()
    if not MODEL_FILE.exists():
        train_intent_model()
    return json.loads(MODEL_FILE.read_text(encoding="utf-8"))


def predict_intent(text: str) -> dict:
    _load_ml()
    model = load_intent_model()
    tokens = _tokenize(text)
    xgboost_candidate = None
    if XGBClassifier is not None and np is not None and XGB_MODEL_FILE.exists() and model.get("vocab"):
        try:
            vocab_index = {token: index for index, token in enumerate(model.get("vocab", []))}
            features = np.zeros((1, len(vocab_index)), dtype=float)
            for token in tokens:
                if token in vocab_index:
                    features[0, vocab_index[token]] += 1.0
            classifier = XGBClassifier()
            classifier.load_model(str(XGB_MODEL_FILE))
            probabilities = classifier.predict_proba(features)[0]
            best_index = int(np.argmax(probabilities))
            labels = model.get("labels", [])
            if 0 <= best_index < len(labels):
                xgboost_candidate = {
                    "intent": labels[best_index],
                    "confidence": round(float(probabilities[best_index]), 3),
                    "engine": "xgboost",
                }
        except Exception:
            pass

    scores = {}
    for label in model.get("labels", []):
        score = model["priors"].get(label, -99.0)
        likelihoods = model["likelihoods"].get(label, {})
        floor = math.log(1 / (len(model.get("vocab", [])) + 1))
        for token in tokens:
            score += likelihoods.get(token, floor)
        scores[label] = score

    if not scores:
        return {"intent": "unknown", "confidence": 0.0}

    best = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else 3.0
    confidence = 1 / (1 + math.exp(-margin))
    naive_candidate = {"intent": best, "confidence": round(confidence, 3), "engine": "naive_bayes"}

    if xgboost_candidate and xgboost_candidate["confidence"] >= max(0.5, naive_candidate["confidence"] * 0.75):
        return xgboost_candidate
    if xgboost_candidate:
        naive_candidate["engine"] = "naive_bayes+xgboost_trained"
    return naive_candidate


def add_intent_example(text: str, intent: str) -> dict:
    _ensure_dirs()
    with INTENTS_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([text, intent])
    return train_intent_model()


def _load_knowledge() -> list[dict]:
    _ensure_dirs()
    try:
        data = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_knowledge(items: list[dict]) -> None:
    _ensure_dirs()
    KNOWLEDGE_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def _chunk_text(text: str, size: int = 120, overlap: int = 24) -> list[str]:
    words = re.findall(r"\S+", text or "")
    chunks = []
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def add_knowledge(title: str, text: str, source: str = "manual") -> dict:
    items = _load_knowledge()
    chunks = _chunk_text(text)
    base_id = len(items) + 1
    for index, chunk in enumerate(chunks):
        tokens = _tokenize(chunk)
        items.append(
            {
                "id": f"k{base_id + index}",
                "title": title or "Untitled",
                "source": source,
                "text": chunk,
                "tokens": tokens,
            }
        )
    _save_knowledge(items)
    return {"chunks_added": len(chunks), "total_chunks": len(items)}


class _ReadableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = []
        self.parts = []
        self._title = False
        self._capture = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._title = True
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self._capture = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self._capture = False

    def handle_data(self, data):
        text = re.sub(r"\s+", " ", html.unescape(data or "")).strip()
        if not text:
            return
        if self._title:
            self.title.append(text)
        if self._capture:
            self.parts.append(text)


def add_link(url: str) -> dict:
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = "https://" + url
    request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalBrain/1.0"})
    with urllib.request.urlopen(request, timeout=12) as response:
        raw = response.read(900_000).decode("utf-8", errors="ignore")
    parser = _ReadableHTMLParser()
    parser.feed(raw)
    title = " ".join(parser.title).strip() or url
    text = " ".join(parser.parts)
    return add_knowledge(title, text, url)


def _read_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".log", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".jsonl"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return json.dumps(data, ensure_ascii=False, indent=2)

    if suffix == ".csv":
        if pd is not None:
            frame = pd.read_csv(path)
            return frame.head(200).to_csv(index=False)
        rows = []
        with path.open("r", newline="", encoding="utf-8", errors="ignore") as file:
            reader = csv.reader(file)
            for index, row in enumerate(reader):
                if index >= 200:
                    break
                rows.append(", ".join(row))
        return "\n".join(rows)

    return ""


def _supported_text_name(name: str) -> bool:
    return bool(re.search(r"\.(csv|json|jsonl|txt|md|markdown|log|py|js|ts|tsx|jsx|html|css)$", name, flags=re.IGNORECASE))


def _fetch_url_text(url: str, max_bytes: int = 2_000_000) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "JarvisLocalBrain/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(max_bytes).decode("utf-8", errors="ignore")


def _github_raw_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host == "raw.githubusercontent.com" and len(path_parts) >= 4:
        return url

    if host not in {"github.com", "www.github.com"} or len(path_parts) < 2:
        return None

    owner, repo = path_parts[0], path_parts[1]
    if len(path_parts) >= 5 and path_parts[2] == "blob":
        branch = path_parts[3]
        file_path = "/".join(path_parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"

    return None


def _github_readme_candidates(url: str) -> list[str]:
    parsed = urllib.parse.urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() not in {"github.com", "www.github.com"} or len(path_parts) < 2:
        return []

    owner, repo = path_parts[0], path_parts[1]
    branch = "main"
    if len(path_parts) >= 4 and path_parts[2] in {"tree", "blob"}:
        branch = path_parts[3]

    branches = [branch]
    for fallback in ["main", "master"]:
        if fallback not in branches:
            branches.append(fallback)

    names = ["README.md", "README.markdown", "README.txt", "README.rst"]
    return [
        f"https://raw.githubusercontent.com/{owner}/{repo}/{candidate_branch}/{name}"
        for candidate_branch in branches
        for name in names
    ]


def _import_github_url(url: str) -> dict | None:
    raw_url = _github_raw_url(url)
    if raw_url:
        if not _supported_text_name(raw_url):
            return {
                "chunks_added": 0,
                "total_chunks": len(_load_knowledge()),
                "message": "That GitHub file is not a readable text/code file for safe RAG import.",
            }
        text = _fetch_url_text(raw_url)
        return add_knowledge(raw_url.rsplit("/", 1)[-1] or "GitHub file", text, raw_url)

    candidates = _github_readme_candidates(url)
    if not candidates:
        return None

    for candidate in candidates:
        try:
            text = _fetch_url_text(candidate)
        except Exception:
            continue
        if text.strip():
            result = add_knowledge("GitHub README", text, candidate)
            result["message"] = "GitHub README imported safely into RAG memory."
            return result

    return {
        "chunks_added": 0,
        "total_chunks": len(_load_knowledge()),
        "message": "I could not find a readable README for that GitHub repo. Give me a README/raw file link or a downloaded repo folder.",
    }


def _safe_dataset_paths(target: str) -> list[Path]:
    raw = (target or "").strip().strip('"')
    if not raw:
        return []

    path = Path(os.path.expandvars(os.path.expanduser(raw)))
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()

    allowed_roots = [Path.cwd().resolve(), DATA_DIR.resolve(), Path.home().resolve()]
    if not any(path == root or root in path.parents for root in allowed_roots):
        raise ValueError("Dataset path blocked by local safety rules.")

    if path.is_dir():
        supported = {".txt", ".md", ".markdown", ".log", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".jsonl", ".csv"}
        return [item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in supported][:80]
    if path.is_file():
        return [path]
    return []


def import_dataset(target: str) -> dict:
    target = (target or "").strip()
    if not target:
        return {"chunks_added": 0, "total_chunks": len(_load_knowledge()), "message": "Give me a dataset path, URL, or Kaggle slug."}

    if re.match(r"^https?://", target, flags=re.IGNORECASE):
        github_result = _import_github_url(target)
        if github_result is not None:
            return github_result
        parsed = urllib.parse.urlparse(target)
        if parsed.netloc.lower() in {"github.com", "www.github.com", "raw.githubusercontent.com"}:
            return {
                "chunks_added": 0,
                "total_chunks": len(_load_knowledge()),
                "message": "Give me a specific GitHub repo, README, raw file, or downloaded repo folder so I can import it safely.",
            }

        if re.search(r"\.(csv|json|jsonl|txt|md)$", target, flags=re.IGNORECASE):
            raw = _fetch_url_text(target)
            return add_knowledge(target.rsplit("/", 1)[-1] or target, raw, target)
        return add_link(target)

    if re.fullmatch(r"[\w.-]+/[\w.-]+", target):
        try:
            kagglehub = __import__("kagglehub")
            downloaded = Path(kagglehub.dataset_download(target))
            result = import_dataset(str(downloaded))
            result["message"] = f"Kaggle dataset imported: {target}."
            return result
        except Exception as error:
            return {
                "chunks_added": 0,
                "total_chunks": len(_load_knowledge()),
                "message": (
                    "Kaggle download is not available in this environment yet. "
                    f"Download the public dataset to {IMPORTS_DIR} and run: train from dataset {IMPORTS_DIR}. "
                    f"Details: {error}"
                ),
            }

    paths = _safe_dataset_paths(target)
    if not paths:
        return {"chunks_added": 0, "total_chunks": len(_load_knowledge()), "message": "I could not find readable dataset files there."}

    total_added = 0
    for path in paths:
        text = _read_text_file(path)
        if not text.strip():
            continue
        result = add_knowledge(path.name, text, str(path))
        total_added += result.get("chunks_added", 0)

    return {"chunks_added": total_added, "total_chunks": len(_load_knowledge()), "files": len(paths)}


def retrieve(query: str, limit: int = 4) -> list[dict]:
    items = _load_knowledge()
    if not items:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    doc_freq = Counter()
    for item in items:
        doc_freq.update(set(item.get("tokens", [])))

    total_docs = max(1, len(items))
    query_counts = Counter(query_tokens)
    scored = []
    for item in items:
        counts = Counter(item.get("tokens", []))
        score = 0.0
        for token, q_count in query_counts.items():
            if token not in counts:
                continue
            idf = math.log((1 + total_docs) / (1 + doc_freq[token])) + 1
            score += q_count * counts[token] * idf
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def answer_with_rag(query: str) -> dict:
    matches = retrieve(query)
    if not matches:
        return {
            "answer": "I do not have enough knowledge saved yet. Add a link or text to knowledge first.",
            "matches": [],
        }

    context = "\n\n".join(f"{item['title']}: {item['text']}" for item in matches)
    answer_words = context.split()[:140]
    answer = " ".join(answer_words)
    if len(context.split()) > 140:
        answer += "..."
    return {"answer": answer, "matches": matches}
