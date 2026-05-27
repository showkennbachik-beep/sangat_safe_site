import fitz  # PyMuPDF
from datetime import datetime


def sign_pdf(pdf_path, output_path, signature_text, page_num=1):
    doc = fitz.open(pdf_path)
    # Clamp to valid 1-based range so negative/zero/out-of-range values don't silently pick wrong pages
    page_num = max(1, min(int(page_num), len(doc)))
    page = doc[page_num - 1]

    page_width = page.rect.width
    page_height = page.rect.height

    # Signature box dimensions and position (bottom-right corner)
    box_width = 200
    box_height = 60
    margin = 30
    x0 = page_width - box_width - margin
    y0 = page_height - box_height - margin
    x1 = x0 + box_width
    y1 = y0 + box_height
    sig_rect = fitz.Rect(x0, y0, x1, y1)

    # Draw the signature box background (light blue/gray)
    shape = page.new_shape()
    shape.draw_rect(sig_rect)
    shape.finish(color=(0.4, 0.4, 0.6), fill=(0.92, 0.95, 1.0), width=0.8)

    # Insert the signature text (italic style via helv font)
    text_x = x0 + 10
    text_y = y0 + 22
    shape.insert_text(
        fitz.Point(text_x, text_y),
        signature_text,
        fontsize=12,
        fontname="helv",
        color=(0.1, 0.1, 0.3),
    )

    # Draw a separator line below the signature text
    line_y = y0 + 30
    shape.draw_line(fitz.Point(x0 + 8, line_y), fitz.Point(x1 - 8, line_y))
    shape.finish(color=(0.3, 0.3, 0.5), width=0.5)

    # Add 'Digitally Signed' label and current date
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    shape.insert_text(
        fitz.Point(text_x, line_y + 14),
        "Digitally Signed",
        fontsize=7,
        fontname="helv",
        color=(0.3, 0.3, 0.5),
    )
    shape.insert_text(
        fitz.Point(text_x, line_y + 24),
        date_str,
        fontsize=7,
        fontname="helv",
        color=(0.4, 0.4, 0.5),
    )

    shape.commit()

    doc.save(output_path)
    doc.close()

    return output_path
