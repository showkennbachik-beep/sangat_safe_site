import fitz  # PyMuPDF
import os


def html_to_pdf(html_path, output_path):
    """Convert an HTML file to PDF.
    Tries xhtml2pdf first, falls back to PyMuPDF text rendering.
    """
    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    # Try xhtml2pdf first (best HTML rendering)
    try:
        from xhtml2pdf import pisa

        with open(output_path, "wb") as out_file:
            pisa_status = pisa.CreatePDF(html_content, dest=out_file)

        if not pisa_status.err:
            return output_path
    except ImportError:
        pass

    # Fallback: Use PyMuPDF Story API if available (fitz >= 1.21)
    try:
        story = fitz.Story(html=html_content)
        writer = fitz.DocumentWriter(output_path)
        
        # A4 page dimensions
        mediabox = fitz.paper_rect("a4")
        where = mediabox + (36, 36, -36, -36)  # margins

        while True:
            device = writer.begin_page(mediabox)
            more, _ = story.place(where)
            story.draw(device)
            writer.end_page()
            if not more:
                break

        writer.close()
        return output_path
    except (AttributeError, Exception):
        pass

    # Final fallback: strip HTML tags and render as plain text PDF
    import re
    
    # Simple HTML tag stripper
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Create PDF with the text
    doc = fitz.open()
    
    # Split text into chunks that fit on pages
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test = current_line + " " + word if current_line else word
        if len(test) > 80:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    
    lines_per_page = 50
    for i in range(0, len(lines), lines_per_page):
        page = doc.new_page(width=595, height=842)
        page_lines = lines[i:i + lines_per_page]
        text_block = "\n".join(page_lines)
        
        rect = fitz.Rect(40, 40, 555, 802)
        page.insert_textbox(rect, text_block, fontsize=10, fontname="helv")
    
    doc.save(output_path)
    doc.close()
    
    return output_path
