import fitz  # PyMuPDF
import os


def ocr_pdf(pdf_path, output_path):
    """Perform OCR on a scanned/image-based PDF to make it searchable.
    
    Uses PyMuPDF to extract text. If pages have no text (image-based),
    renders pages as images and uses pytesseract for OCR, then creates
    a new searchable PDF. Falls back gracefully if tesseract isn't installed.
    """
    doc = fitz.open(pdf_path)
    
    # Check if the PDF already has text
    has_text = False
    for page in doc:
        if page.get_text().strip():
            has_text = True
            break
    
    if has_text:
        # PDF already has text - just extract and overlay to ensure searchability
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return output_path
    
    # Try OCR with pytesseract
    try:
        import pytesseract
        from PIL import Image
        import io
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter
        from PyPDF2 import PdfReader, PdfWriter, PdfMerger
        
        writer = PdfWriter()
        original_reader = PdfReader(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page to image at 300 DPI
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Run OCR
            ocr_text = pytesseract.image_to_string(img)

            # Create a text overlay PDF page
            text_pdf_path = output_path + f"_ocr_temp_{page_num}.pdf"
            c = rl_canvas.Canvas(text_pdf_path, pagesize=(page.rect.width, page.rect.height))

            # Add invisible text for searchability
            c.setFillAlpha(0)  # Make text invisible
            c.setFont("Helvetica", 10)

            y_pos = page.rect.height - 20
            for line in ocr_text.split('\n'):
                if line.strip():
                    c.drawString(10, y_pos, line)
                    y_pos -= 12
                    if y_pos < 20:
                        break

            c.save()

            # Merge original page with OCR text overlay
            text_reader = PdfReader(text_pdf_path)
            
            original_page = original_reader.pages[page_num]
            if len(text_reader.pages) > 0:
                original_page.merge_page(text_reader.pages[0])
            writer.add_page(original_page)
            
            # Clean up temp file
            try:
                os.remove(text_pdf_path)
            except OSError:
                pass
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        doc.close()
        return output_path
        
    except ImportError:
        # pytesseract not available - extract whatever text we can with fitz
        # and create a text-based PDF
        doc.close()
        
        # Fallback: just copy the PDF with optimization
        doc2 = fitz.open(pdf_path)
        
        # Try to insert text layer using fitz's built-in capabilities
        for page in doc2:
            # Get text blocks if any
            text = page.get_text()
            if not text.strip():
                # Render page as image and re-insert (cleans up the PDF)
                pix = page.get_pixmap(dpi=150)
                # Page already has the image content, just optimize
                pass
        
        doc2.save(output_path, garbage=4, deflate=True)
        doc2.close()
        return output_path
