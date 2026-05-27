from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io

def create_watermark(text):
    packet = io.BytesIO()
    can = canvas.Canvas(packet)
    can.setFont("Helvetica-Bold", 60)
    can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
    can.translate(250, 400)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.save()
    packet.seek(0)
    return packet

def watermark_pdf(pdf_path, output_path, watermark_text):
    watermark_pdf = PdfReader(create_watermark(watermark_text))
    watermark_page = watermark_pdf.pages[0]
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)
        
    with open(output_path, "wb") as f:
        writer.write(f)
        
    return output_path
