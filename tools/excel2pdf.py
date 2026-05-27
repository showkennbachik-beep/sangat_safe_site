import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def excel_to_pdf(excel_path, output_path):
    df = pd.read_excel(excel_path)
    
    # Handle NaN values
    df = df.fillna("")
    
    data = [df.columns.values.astype(str).tolist()] + df.astype(str).values.tolist()
    
    # Use landscape if many columns
    pagesize = landscape(letter) if len(df.columns) > 5 else letter
    pdf = SimpleDocTemplate(output_path, pagesize=pagesize)
    
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    
    pdf.build([table])
    return output_path
