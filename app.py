import re
import json
from flask import Flask, request, jsonify, render_template

nlp = None
SPACY_AVAILABLE = False

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        print("⚠️  spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        SPACY_AVAILABLE = False
except ImportError:
    print("⚠️  spaCy not installed. Pattern-based redaction only.")
    SPACY_AVAILABLE = False

FAKER_AVAILABLE = False
fake = None

try:
    from faker import Faker
    fake = Faker()
    FAKER_AVAILABLE = True
except ImportError:
    print("⚠️  Faker not installed. Using [REDACTED_*] placeholders.")
    FAKER_AVAILABLE = False

app = Flask(__name__)

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_PATTERN = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
URL_PATTERN = re.compile(r"\bhttps?://[^\s<>\"'\)]+")
AWS_ACCESS_KEY_PATTERN = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
JWT_PATTERN = re.compile(r"\b[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-. ]?)?(?:\(?\d{3}\)?[-. ]?)\d{3}[-. ]?\d{4}\b")
SECRET_KEYS = ["password", "secret", "api_key"]
SECRET_PATTERN = re.compile(r"\b(" + "|".join(SECRET_KEYS) + r")=(\S+)")

# Synthetic data cache
synthetic_cache = {}


def get_synthetic_replacement(entity_type: str, original: str) -> str:
    """Generate synthetic replacement for redacted data."""
    if not FAKER_AVAILABLE or fake is None:
        return f"[REDACTED_{entity_type}]"
    
    key = (entity_type, original)
    if key in synthetic_cache:
        return synthetic_cache[key]
    
    if entity_type == "EMAIL":
        replacement = fake.email()
    elif entity_type == "PHONE":
        replacement = fake.phone_number()
    elif entity_type == "PERSON":
        replacement = fake.name()
    elif entity_type == "ORGANIZATION":
        replacement = fake.company()
    elif entity_type == "GPE":
        replacement = fake.country()
    else:
        replacement = f"[REDACTED_{entity_type}]"
    
    synthetic_cache[key] = replacement
    return replacement


def calculate_pii_score(text: str, redaction_count: int) -> float:
    """Calculate privacy risk score (0-100). Higher = riskier."""
    if not text:
        return 0.0
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Base score: percentage of redacted items
    redaction_ratio = min((redaction_count / max(total_words / 10, 1)) * 100, 100)
    
    # Bonus: check for obvious risky patterns
    risky_keywords = ["password", "secret", "token", "key", "credential", "token"]
    risky_count = sum(1 for kw in risky_keywords if kw.lower() in text.lower())
    
    final_score = (redaction_ratio * 0.7) + (risky_count * 3)
    return min(final_score, 100.0)


def extract_entities_with_ner(text: str) -> dict:
    """Use spaCy NER to identify entities for smarter redaction."""
    if not SPACY_AVAILABLE or nlp is None:
        return {"entities": []}
    
    doc = nlp(text)
    entities = []
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT"]:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
    
    return {"entities": entities}


def redact_line(line: str, counters: dict) -> tuple:
    """Redact sensitive tokens in a single line and update counters."""

    def replace_email(match: re.Match) -> str:
        counters["emails"] += 1
        return get_synthetic_replacement("EMAIL", match.group(0))

    def replace_ip(match: re.Match) -> str:
        counters["ips"] += 1
        return "[REDACTED_IP]"

    def replace_secret(match: re.Match) -> str:
        counters["secrets"] += 1
        key = match.group(1)
        return f"{key}=[REDACTED_SECRET]"

    def replace_url(match: re.Match) -> str:
        counters["urls"] += 1
        return "[REDACTED_URL]"

    def replace_aws_key(match: re.Match) -> str:
        counters["aws_keys"] += 1
        return "[REDACTED_AWS_KEY]"

    def replace_jwt(match: re.Match) -> str:
        counters["jwts"] += 1
        return "[REDACTED_JWT]"

    def replace_phone(match: re.Match) -> str:
        counters["phones"] += 1
        return get_synthetic_replacement("PHONE", match.group(0))

    # Pass 1: emails
    redacted = EMAIL_PATTERN.sub(replace_email, line)
    # Pass 2: IPv4 addresses
    redacted = IP_PATTERN.sub(replace_ip, redacted)
    # Pass 3: URLs
    redacted = URL_PATTERN.sub(replace_url, redacted)
    # Pass 4: AWS Access Key IDs
    redacted = AWS_ACCESS_KEY_PATTERN.sub(replace_aws_key, redacted)
    # Pass 5: JWT tokens
    redacted = JWT_PATTERN.sub(replace_jwt, redacted)
    # Pass 6: Phone numbers
    redacted = PHONE_PATTERN.sub(replace_phone, redacted)
    # Pass 7: password/secret/api_key values
    redacted = SECRET_PATTERN.sub(replace_secret, redacted)
    return redacted


def stream_redact(lines):
    """
    Generator that redacts incoming text line-by-line.
    Beginner note: a generator lets us yield one redacted line at a time
    instead of building huge strings in memory, which is kinder to RAM.
    """
    counters = {"emails": 0, "ips": 0, "secrets": 0, "urls": 0, "aws_keys": 0, "jwts": 0, "phones": 0}
    for line in lines:
        yield redact_line(line, counters)
    return counters


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/redact", methods=["POST"])
def redact():
    try:
        raw_text = request.get_data(as_text=True) or ""
        lines = raw_text.splitlines(keepends=True)

        counters = {"emails": 0, "ips": 0, "secrets": 0, "urls": 0, "aws_keys": 0, "jwts": 0, "phones": 0}

        def redact_stream():
            """Yield redacted lines so we can process incrementally."""
            for line in lines:
                yield redact_line(line, counters)

        redacted_text = "".join(redact_stream())
        total_redacted = sum(counters.values())
        pii_score = calculate_pii_score(raw_text, total_redacted)
        
        return jsonify({
            "redacted": redacted_text,
            "counts": counters,
            "pii_score": round(pii_score, 1),
            "spacy_available": SPACY_AVAILABLE,
            "faker_available": FAKER_AVAILABLE
        })
    except Exception as e:
        print(f"Error in redact: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500






if __name__ == "__main__":
    import os
    # For production, use a WSGI server like gunicorn instead
    # Run with: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
