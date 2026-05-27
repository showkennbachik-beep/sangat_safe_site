import fitz  # PyMuPDF


def optimize_pdf(pdf_path, output_path):
    """Optimize a PDF by garbage collecting unused objects, 
    deflating streams, and cleaning up the structure.
    """
    doc = fitz.open(pdf_path)

    # Save with aggressive optimization flags
    # garbage=4: maximum garbage collection (remove unused objects, merge duplicates)
    # deflate=True: compress all streams
    # clean=True: clean and sanitize content streams
    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True,
        linear=True  # Linearize for fast web viewing
    )
    doc.close()

    return output_path
