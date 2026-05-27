import fitz  # PyMuPDF


def flatten_pdf_forms(pdf_path, output_path):
    """Flatten PDF form fields by rendering each page to static image content.

    Rendering at 2× zoom bakes the current field values into the page as
    non-editable pixels, removing all interactive form elements.
    """
    src = fitz.open(pdf_path)
    out = fitz.open()

    for page in src:
        # Render at 2× zoom (≈144 DPI) — form field content is included
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, pixmap=pix)

    out.save(output_path, deflate=True, garbage=4)
    out.close()
    src.close()

    return output_path
