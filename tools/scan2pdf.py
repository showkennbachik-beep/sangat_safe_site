from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF
import os


def scan_to_pdf(image_paths, output_path):
    """Convert scanned images (photos of documents) to a clean PDF.
    Enhances images: grayscale, contrast boost, sharpening.
    """
    doc = fitz.open()

    for img_path in image_paths:
        # Open and enhance the image
        img = Image.open(img_path)

        # Convert to grayscale for a cleaner scan look
        img = img.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Sharpen
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)

        # Increase brightness slightly
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)

        # Save enhanced image to a temporary path
        temp_path = img_path + "_enhanced.png"
        img.save(temp_path, "PNG")

        # Insert into PDF - fit to A4 page
        page = doc.new_page(width=595, height=842)  # A4 dimensions in points
        rect = page.rect
        page.insert_image(rect, filename=temp_path)

        # Clean up temp file
        try:
            os.remove(temp_path)
        except OSError:
            pass

    doc.save(output_path, deflate=True)
    doc.close()

    return output_path
