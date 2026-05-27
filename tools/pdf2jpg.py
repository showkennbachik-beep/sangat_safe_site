import fitz  # PyMuPDF
import os
import zipfile

def pdf_to_jpg(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    zip_path = os.path.join(output_dir, "images.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better quality
            img_filename = f"page_{page_num + 1}.jpg"
            img_path = os.path.join(output_dir, img_filename)
            pix.save(img_path)
            zipf.write(img_path, img_filename)
            os.remove(img_path)
            
    doc.close()
    return zip_path
