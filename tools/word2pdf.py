import os


def convert_word_to_pdf(word_path, output_path):
    """Convert a Word document (.docx) to PDF.

    Primary path: MS Word via COM (Windows + MS Office only).
    Fallback: pure-python text extraction so the tool degrades
    gracefully on Linux/macOS instead of crashing the whole app.

    NOTE: imports are done INSIDE the function on purpose. The
    Windows-only modules (docx2pdf, pythoncom) must not be imported
    at module load time, or the entire Flask app fails to start on
    non-Windows systems.
    """
    abs_word = os.path.abspath(word_path)
    abs_out = os.path.abspath(output_path)

    # --- Primary: Windows + MS Word ---
    try:
        import pythoncom
        from docx2pdf import convert

        pythoncom.CoInitialize()
        try:
            convert(abs_word, abs_out)
        finally:
            pythoncom.CoUninitialize()
        return output_path
    except Exception:
        pass  # fall through to cross-platform fallback

    # --- Fallback: extract text and lay it into a simple PDF ---
    try:
        from docx import Document
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        doc = Document(abs_word)
        c = canvas.Canvas(abs_out, pagesize=letter)
        width, height = letter
        y = height - 50
        c.setFont("Helvetica", 11)

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                y -= 14
                continue
            while len(text) > 95:
                c.drawString(40, y, text[:95])
                text = text[95:]
                y -= 16
                if y < 50:
                    c.showPage(); c.setFont("Helvetica", 11); y = height - 50
            c.drawString(40, y, text)
            y -= 16
            if y < 50:
                c.showPage(); c.setFont("Helvetica", 11); y = height - 50

        c.save()
        return output_path
    except Exception as e:
        raise RuntimeError(
            "Word-to-PDF needs Microsoft Word (Windows) for full conversion, "
            "and the text-only fallback also failed. Details: %s" % e
        )
