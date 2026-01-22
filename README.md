# 🔒 CODE GHOST - Intelligent Data Redactor

A production-ready Flask web application for automatically detecting and redacting sensitive information (PII) from text data. Perfect for sanitizing logs, API responses, configuration files, and any text containing personally identifiable information.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **Intelligent Pattern Detection**: Automatically identifies and redacts:
  - Email addresses
  - IPv4 addresses
  - URLs
  - AWS Access Keys
  - JWT tokens
  - Phone numbers
  - Secrets (passwords, API keys, tokens)

- **Privacy Risk Scoring**: Real-time PII risk assessment (0-100 scale)
- **Synthetic Data Replacement**: Optional fake data generation using Faker
- **NER Support**: Enhanced entity detection with spaCy (optional)
- **Modern UI**: Clean, responsive interface with dark/light themes
- **Export Options**: Copy to clipboard or download as text file
- **Production Ready**: Proper error handling, environment config, and WSGI support

## 📋 Requirements

- Python 3.8+
- pip

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ghost-code

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Optional: Install spaCy Model (Recommended)

For enhanced entity recognition:

```bash
python -m spacy download en_core_web_sm
```

> **Note**: The app works without spaCy, using pattern-based redaction only.

### 3. Configure Environment (Optional)

```bash
# Copy example environment file
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux

# Edit .env to customize settings
```

### 4. Run Development Server

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## 🏭 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With timeout for long requests
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

### Environment Variables

| Variable      | Default     | Description                             |
| ------------- | ----------- | --------------------------------------- |
| `FLASK_HOST`  | `127.0.0.1` | Server bind address                     |
| `FLASK_PORT`  | `5000`      | Server port                             |
| `FLASK_DEBUG` | `false`     | Debug mode (never `true` in production) |

### Using with Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t ghost-code .
docker run -p 5000:5000 ghost-code
```

## 📁 Project Structure

```
ghost-code/
├── app.py                 # Flask application & redaction logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── style.css         # Stylesheet (dark/light themes)
    └── script.js         # Frontend logic
```

## 🔧 Configuration

### Customizing Redaction Patterns

Edit `app.py` to modify or add patterns:

```python
# Add custom patterns
CUSTOM_PATTERN = re.compile(r"your-regex-here")

def redact_line(line: str, counters: dict) -> tuple:
    # Add custom redaction logic
    redacted = CUSTOM_PATTERN.sub(replace_custom, line)
    return redacted
```

### Adjusting Risk Calculation

Modify the `calculate_pii_score()` function in `app.py`:

```python
def calculate_pii_score(text: str, redaction_count: int) -> float:
    # Customize scoring logic
    # Current: 70% redaction density + 30% risky keywords
    pass
```

## 🎨 UI Customization

### Themes

Toggle between dark/light modes using the theme button. Theme preference persists via localStorage.

### Color Scheme

Edit CSS variables in `static/style.css`:

```css
:root {
  --neon-cyan: #00e5ff; /* Primary accent */
  --accent-purple: #a855f7; /* Secondary accent */
  /* ... more variables */
}
```

## 🧪 Testing

### Test with Sample Data

Paste this into the input console:

```
User: john.doe@company.com
Password: SuperSecret123!
API_KEY=sk_live_abcd1234efgh5678
AWS Access Key: AKIAIOSFODNN7EXAMPLE
Phone: +1 (555) 123-4567
Server: 192.168.1.100
JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U
```

Expected result: All sensitive data redacted/replaced.

## 📦 Dependencies

- **Flask 2.3.3**: Web framework
- **spaCy 3.7.2**: NLP & entity recognition (optional)
- **Faker 20.0.0**: Synthetic data generation (optional)

## 🛡️ Security Notes

- **Never log original text**: The app processes data in-memory only
- **HTTPS in production**: Always use SSL/TLS in production
- **Rate limiting**: Consider adding rate limiting for public deployments
- **Input validation**: Current limits: 10,000 chars / 2,000 words
- **Audit trail**: Add logging for compliance requirements if needed

## 🐛 Troubleshooting

### spaCy model not found

```bash
python -m spacy download en_core_web_sm
```

### Port already in use

```bash
# Change port in .env
FLASK_PORT=8000
```

### Faker not generating replacements

- Ensure Faker is installed: `pip install faker`
- Check console for warnings on startup

## 📝 License

MIT License - feel free to use in personal and commercial projects.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💡 Roadmap

- [ ] Support for credit card and SSN detection
- [ ] Batch file processing
- [ ] API endpoint for programmatic access
- [ ] Custom pattern management UI
- [ ] Multi-language support
- [ ] Advanced reporting dashboard

## 👥 Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Check existing issues for solutions

---

**Built with ❤️ for privacy and security**
