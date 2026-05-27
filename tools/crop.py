from PyPDF2 import PdfReader, PdfWriter

def crop_pdf(pdf_path, output_path, margin=50):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        upper_right = page.mediabox.upper_right
        lower_left = page.mediabox.lower_left
        
        # Apply margin crop
        new_ur = (float(upper_right[0]) - margin, float(upper_right[1]) - margin)
        new_ll = (float(lower_left[0]) + margin, float(lower_left[1]) + margin)
        
        page.mediabox.upper_right = new_ur
        page.mediabox.lower_left = new_ll
        
        writer.add_page(page)
        
    with open(output_path, "wb") as f:
        writer.write(f)
        
    return output_path
