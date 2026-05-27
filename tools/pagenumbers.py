import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

def add_page_numbers(pdf_path, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)
    
    for i, page in enumerate(reader.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
        # Draw text at the bottom center
        width = float(page.mediabox.width)
        can.setFont("Helvetica", 10)
        can.drawCentredString(width / 2.0, 20, f"{i + 1} / {total_pages}")
        can.save()
        packet.seek(0)
        
        number_pdf = PdfReader(packet)
        page.merge_page(number_pdf.pages[0])
        writer.add_page(page)
        
    with open(output_path, "wb") as f:
        writer.write(f)
        
    return output_path
