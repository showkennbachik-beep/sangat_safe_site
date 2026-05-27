import pdfplumber
import pandas as pd

def convert_pdf_to_excel(pdf_path, output_path):
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # Filter out None values from the table rows
                cleaned_table = [[cell if cell is not None else "" for cell in row] for row in table]
                all_data.extend(cleaned_table)
                
    if all_data:
        # Use the first row as columns, handle empty headers
        columns = all_data[0]
        columns = [f"Col_{i}" if not c else c for i, c in enumerate(columns)]
        
        df = pd.DataFrame(all_data[1:], columns=columns)
        df.to_excel(output_path, index=False)
    else:
        pd.DataFrame([["No tables found in this PDF"]]).to_excel(output_path, index=False, header=False)
        
    return output_path
