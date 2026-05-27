import fitz # PyMuPDF

def repair_pdf(pdf_path, output_path):
    # PyMuPDF naturally repairs broken xref tables when saving
    doc = fitz.open(pdf_path)
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    return output_path
