import fitz # PyMuPDF

def edit_pdf(pdf_path, output_path, text, page_num, x_pct, y_pct):
    doc = fitz.open(pdf_path)
    
    try:
        # 1-indexed to 0-indexed
        page_index = int(page_num) - 1
        
        # If user puts page out of bounds, default to first page
        if page_index < 0 or page_index >= len(doc):
            page_index = 0
            
        page = doc[page_index]
        
        # Convert percentages to actual points
        x = page.rect.width * (float(x_pct) / 100.0)
        y = page.rect.height * (float(y_pct) / 100.0)
        
        # Insert text (red, size 16)
        page.insert_text(fitz.Point(x, y), text, fontsize=16, color=(1, 0, 0)) # Red text
        
        doc.save(output_path)
    finally:
        doc.close()
        
    return output_path
