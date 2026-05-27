from PyPDF2 import PdfReader, PdfWriter


def _parse_pages(pages_str):
    """Parse a page string like '2,4,6-8' into a set of page numbers."""
    pages = set()
    try:
        parts = pages_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    pages.add(i)
            else:
                pages.add(int(part))
    except Exception:
        pass
    return pages


def remove_pages(pdf_path, output_path, pages_to_remove_str):
    """Remove specified pages from a PDF. Pages are 1-indexed."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    pages_to_remove = _parse_pages(pages_to_remove_str)
    total_pages = len(reader.pages)

    for i in range(total_pages):
        if (i + 1) not in pages_to_remove:
            writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
