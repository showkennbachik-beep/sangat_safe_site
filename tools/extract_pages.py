from PyPDF2 import PdfReader, PdfWriter


def extract_pages(pdf_path, output_path, pages_str):
    """Extract specified pages from a PDF into a new file. Pages are 1-indexed.
    pages_str format: '1,3,5-7'
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    pages_to_extract = set()
    try:
        parts = pages_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    pages_to_extract.add(i)
            else:
                pages_to_extract.add(int(part))
    except Exception:
        pages_to_extract = set(range(1, len(reader.pages) + 1))

    # Extract pages in order
    for page_num in sorted(pages_to_extract):
        if 1 <= page_num <= len(reader.pages):
            writer.add_page(reader.pages[page_num - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
