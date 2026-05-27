from PyPDF2 import PdfReader, PdfWriter

def lock_pdf(pdf_path, output_path, password):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
