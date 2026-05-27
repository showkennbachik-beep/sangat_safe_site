import fitz  # PyMuPDF
import difflib


def compare_pdfs(pdf_path1, pdf_path2, output_path):
    # Extract text from the first PDF
    doc1 = fitz.open(pdf_path1)
    text1 = []
    for page in doc1:
        text1.extend(page.get_text().splitlines())
    doc1.close()

    # Extract text from the second PDF
    doc2 = fitz.open(pdf_path2)
    text2 = []
    for page in doc2:
        text2.extend(page.get_text().splitlines())
    doc2.close()

    # Generate side-by-side HTML diff report
    differ = difflib.HtmlDiff(wrapcolumn=80)
    html_content = differ.make_file(
        text1,
        text2,
        fromdesc="PDF 1",
        todesc="PDF 2",
        context=True,
        numlines=3,
    )

    # Save the HTML diff report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
