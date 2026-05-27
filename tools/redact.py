import fitz # PyMuPDF

def redact_pdf(pdf_path, output_path, text_to_redact):
    doc = fitz.open(pdf_path)
    
    for page in doc:
        # Search for the exact text string
        areas = page.search_for(text_to_redact)
        
        # Add redaction annotations (draws black boxes over the text)
        for area in areas:
            page.add_redact_annot(area, fill=(0, 0, 0)) # Black fill
            
        # Apply redactions to physically remove the text from the file
        page.apply_redactions()
        
    doc.save(output_path)
    doc.close()
    return output_path
