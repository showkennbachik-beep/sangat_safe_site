import fitz  # PyMuPDF


def compress_pdf(pdf_path, output_path):
    """Compress a PDF using PyMuPDF's full optimization pipeline.

    Removes duplicate objects, re-compresses all streams (including images
    and fonts), and cleans content streams — typically cuts file size 30-70%.
    """
    doc = fitz.open(pdf_path)
    doc.save(
        output_path,
        garbage=4,          # max garbage collection: remove/dedup unused objects
        deflate=True,        # zlib-compress all streams
        deflate_images=True, # also compress image streams
        deflate_fonts=True,  # also compress embedded font streams
        clean=True,          # sanitize content streams
    )
    doc.close()
    return output_path
