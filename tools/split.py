from PyPDF2 import PdfReader, PdfWriter
import os
import zipfile

def split_pdf(pdf_path, output_folder):
    reader = PdfReader(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    zip_path = os.path.join(output_folder, f"{base_name}_split.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            page_path = os.path.join(output_folder, f"{base_name}_page_{i+1}.pdf")
            with open(page_path, "wb") as f:
                writer.write(f)
            
            # Add to zip and delete the temporary page file
            zipf.write(page_path, arcname=f"{base_name}_page_{i+1}.pdf")
            os.remove(page_path)
            
    return zip_path
