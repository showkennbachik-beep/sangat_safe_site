# SANGAT P.D.F — Document Toolkit

A Flask web application offering 33+ PDF tools: merge, split, compress, convert
(Word/Excel/PPT/JPG/HTML ↔ PDF), OCR, sign, redact, watermark, translate,
summarize, and more.

---

## Quick start

```bash
# 1. Clone
git clone <your-repo-url>
cd pdf-tools

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your secret key
cp .env.example .env            # then edit .env and paste a real key
#   generate one with: python -c "import secrets; print(secrets.token_hex(32))"

# 5. Run
python app.py
# Opens http://127.0.0.1:5000
```

> **Note:** The app reads `SECRET_KEY` from the environment. If you don't use a
> `.env` loader, export it manually:
> `export SECRET_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")`

---

## Platform notes (read before deploying)

| Tool | Works on | Notes |
|------|----------|-------|
| Most tools | Windows / macOS / Linux | Pure Python (PyMuPDF, PyPDF2, reportlab) |
| **OCR** | All | Requires the **Tesseract** binary installed separately (see `requirements.txt`) |
| **Word → PDF** | **Windows only** | Uses MS Word via COM (`docx2pdf`) |
| **PPT → PDF** | **Windows only** (full fidelity) | Falls back to text-only PDF on Linux/macOS |

If you deploy to a **Linux server**, the two Office-COM tools will not work at
full fidelity. Consider replacing them with LibreOffice headless conversion.

---

## Project structure

```
pdf-tools/
├── app.py              # Flask routes
├── tools/              # one module per PDF operation
├── templates/          # Jinja2 HTML (extends base.html)
├── static/             # css, js, uploads (gitignored)
├── outputs/            # generated files (gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Security

- `users.db` and `.env` are **gitignored** — never commit them.
- The checkout `/process-payment` route is currently a **placeholder** and does
  not process real payments. Do not collect real payment data until a real
  payment processor (e.g. Stripe) is integrated.
