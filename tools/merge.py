from PyPDF2 import PdfMerger

def merge_pdfs(pdf_paths, output_path):
    merger = PdfMerger()
    for path in pdf_paths:
        merger.append(path)
    merger.write(output_path)
    merger.close()
    return output_path
