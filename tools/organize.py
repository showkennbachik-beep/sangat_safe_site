from PyPDF2 import PdfReader, PdfWriter

def organize_pdf(pdf_path, output_path, pages_to_keep_str):
    # pages_to_keep_str like "1,3,5-7" — pages are output in the ORDER specified
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    # Parse the page list preserving user-specified order (supports reordering)
    page_nums = []
    try:
        for part in pages_to_keep_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                page_nums.extend(range(start, end + 1))
            else:
                page_nums.append(int(part))
    except Exception:
        page_nums = list(range(1, total_pages + 1))

    for page_num in page_nums:
        if 1 <= page_num <= total_pages:
            writer.add_page(reader.pages[page_num - 1])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
