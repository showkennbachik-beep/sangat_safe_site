from PIL import Image

def images_to_pdf(image_paths, output_path):
    images = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
    
    if images:
        images[0].save(output_path, "PDF", save_all=True, append_images=images[1:])
    return output_path
