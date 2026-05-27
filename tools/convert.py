from PyPDF2 import PdfReader

def convert_pdf_to_text(pdf_path, output_path):
    reader = PdfReader(pdf_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                f.write(f"--- Page {i+1} ---\n")
                f.write(text)
                f.write("\n\n")
                
    return output_path
