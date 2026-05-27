from PyPDF2 import PdfReader, PdfWriter

def rotate_pdf(pdf_path, output_path, rotation=90):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(rotation)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
