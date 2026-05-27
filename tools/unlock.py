from PyPDF2 import PdfReader, PdfWriter

def unlock_pdf(pdf_path, output_path, password):
    reader = PdfReader(pdf_path)

    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == 0:
            raise ValueError("Incorrect password. Please check and try again.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
