import fitz  # PyMuPDF
from deep_translator import GoogleTranslator


def translate_pdf(pdf_path, output_path, target_lang="es"):
    # Extract text from the source PDF
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    # Chunk the text into segments of 4500 characters to avoid API limits
    chunk_size = 4500
    chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]

    # Translate each chunk
    translator = GoogleTranslator(source="auto", target=target_lang)
    translated_chunks = []
    for chunk in chunks:
        if chunk.strip():
            translated = translator.translate(chunk)
            translated_chunks.append(translated)
        else:
            translated_chunks.append("")

    translated_text = "".join(translated_chunks)

    # Create a new PDF with the translated text
    new_doc = fitz.open()
    # Split translated text into pages (roughly 3000 chars per page)
    page_size = 3000
    text_pages = [translated_text[i:i + page_size] for i in range(0, len(translated_text), page_size)]

    for text_block in text_pages:
        page = new_doc.new_page(width=595, height=842)  # A4 size
        # Insert translated text with wrapping
        text_rect = fitz.Rect(50, 50, 545, 792)
        page.insert_textbox(
            text_rect,
            text_block,
            fontsize=11,
            fontname="helv",
            align=fitz.TEXT_ALIGN_LEFT,
        )

    new_doc.save(output_path)
    new_doc.close()

    return output_path
