from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps
import os
import zipfile

# Handle Pillow version differences (>=9.1 moved resamplers to Image.Resampling)
_RS = getattr(Image, 'Resampling', None)
LANCZOS = getattr(_RS, 'LANCZOS', None) or Image.LANCZOS


def _get_font(size):
    for path in [
        r'C:\Windows\Fonts\Arial.ttf',
        r'C:\Windows\Fonts\arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _get_impact_font(size):
    for path in [
        r'C:\Windows\Fonts\impact.ttf',
        r'C:\Windows\Fonts\Impact.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Impact.ttf',
        r'C:\Windows\Fonts\Arial.ttf',
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return _get_font(size)


def _to_rgb(img):
    """Flatten transparency to white and ensure RGB mode."""
    if img.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode == 'P':
        return _to_rgb(img.convert('RGBA'))
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img


def _save(img, path, quality=90):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        _to_rgb(img).save(path, 'JPEG', quality=quality)
    elif ext == '.png':
        img.save(path, 'PNG')
    elif ext == '.webp':
        img.save(path, 'WEBP', quality=quality)
    elif ext == '.bmp':
        _to_rgb(img).save(path, 'BMP')
    elif ext == '.tiff':
        img.save(path, 'TIFF')
    else:
        img.save(path)


# ── Tool 1: Resize ────────────────────────────────────────────────────────────
def resize_image(input_path, output_path, width, height, maintain_aspect=False):
    img = Image.open(input_path)
    w, h = int(width), int(height)
    if maintain_aspect:
        img.thumbnail((w, h), LANCZOS)
    else:
        img = img.resize((w, h), LANCZOS)
    _save(img, output_path)


# ── Tool 2: Compress ──────────────────────────────────────────────────────────
def compress_image(input_path, output_path, quality=60):
    img = Image.open(input_path)
    _to_rgb(img).save(output_path, 'JPEG', quality=int(quality), optimize=True)


# ── Tool 3: Remove Background ────────────────────────────────────────────────
def remove_background(input_path, output_path):
    try:
        from rembg import remove
        with open(input_path, 'rb') as f:
            data = f.read()
        with open(output_path, 'wb') as f:
            f.write(remove(data))
    except ImportError:
        # Fallback: make near-white pixels transparent
        img = Image.open(input_path).convert('RGBA')
        pixels = list(img.getdata())
        new_pixels = [
            (r, g, b, 0) if r > 230 and g > 230 and b > 230 else (r, g, b, a)
            for r, g, b, a in pixels
        ]
        img.putdata(new_pixels)
        img.save(output_path, 'PNG')


# ── Tool 4: JPG → PNG ─────────────────────────────────────────────────────────
def jpg_to_png(input_path, output_path):
    Image.open(input_path).save(output_path, 'PNG')


# ── Tool 5: PNG → JPG ─────────────────────────────────────────────────────────
def png_to_jpg(input_path, output_path, quality=90):
    _to_rgb(Image.open(input_path)).save(output_path, 'JPEG', quality=int(quality))


# ── Tool 6: Crop ──────────────────────────────────────────────────────────────
def crop_image(input_path, output_path, left, top, right, bottom):
    img = Image.open(input_path)
    _save(img.crop((int(left), int(top), int(right), int(bottom))), output_path)


# ── Tool 7: Rotate ────────────────────────────────────────────────────────────
def rotate_image(input_path, output_path, angle, expand=True):
    img = Image.open(input_path)
    # PIL rotates counter-clockwise; negate so positive angle = clockwise (matches UI labels)
    _save(img.rotate(-float(angle), expand=expand), output_path)


# ── Tool 8: Flip ──────────────────────────────────────────────────────────────
def flip_image(input_path, output_path, direction='horizontal'):
    img = Image.open(input_path)
    fn = ImageOps.mirror if direction == 'horizontal' else ImageOps.flip
    _save(fn(img), output_path)


# ── Tool 9: Watermark ────────────────────────────────────────────────────────
def add_watermark_to_image(input_path, output_path, text, opacity=60, font_size=40):
    img = Image.open(input_path).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_font(int(font_size))
    alpha = int(255 * int(opacity) / 100)

    try:
        bb = draw.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    except AttributeError:
        tw, th = draw.textsize(text, font=font)

    for y in range(-img.height, img.height * 2, th + 80):
        for x in range(-img.width, img.width * 2, tw + 60):
            draw.text((x, y), text, fill=(200, 200, 200, alpha), font=font)

    result = Image.alpha_composite(img, overlay)
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        result = result.convert('RGB')
    result.save(output_path)


# ── Tool 10: Blur ─────────────────────────────────────────────────────────────
def blur_image(input_path, output_path, radius=3):
    img = Image.open(input_path)
    _save(img.filter(ImageFilter.GaussianBlur(radius=float(radius))), output_path)


# ── Tool 11: Brightness ───────────────────────────────────────────────────────
def adjust_brightness(input_path, output_path, factor=1.5):
    img = Image.open(input_path)
    _save(ImageEnhance.Brightness(img).enhance(float(factor)), output_path)


# ── Tool 12: Contrast ─────────────────────────────────────────────────────────
def adjust_contrast(input_path, output_path, factor=1.5):
    img = Image.open(input_path)
    _save(ImageEnhance.Contrast(img).enhance(float(factor)), output_path)


# ── Tool 13: Sharpen ──────────────────────────────────────────────────────────
def sharpen_image(input_path, output_path, factor=2.0):
    img = Image.open(input_path)
    _save(ImageEnhance.Sharpness(img).enhance(float(factor)), output_path)


# ── Tool 14: Grayscale ────────────────────────────────────────────────────────
def convert_to_grayscale(input_path, output_path):
    _save(ImageOps.grayscale(Image.open(input_path)), output_path)


# ── Tool 15: Images → PDF ─────────────────────────────────────────────────────
def image_to_pdf_tool(input_paths, output_path):
    images = [_to_rgb(Image.open(p)) for p in input_paths]
    if images:
        images[0].save(
            output_path, format='PDF', save_all=True, append_images=images[1:]
        )


# ── Tool 16: PDF → Images ─────────────────────────────────────────────────────
def pdf_to_images_tool(input_path, output_folder):
    import fitz  # PyMuPDF
    doc = fitz.open(input_path)
    zip_path = os.path.join(output_folder, 'pdf_pages.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for i, page in enumerate(doc):
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            zf.writestr(f'page_{i + 1:03d}.png', pix.tobytes('png'))
    doc.close()
    return zip_path


# ── Tool 17: Meme Generator ───────────────────────────────────────────────────
def generate_meme(input_path, output_path, top_text='', bottom_text=''):
    img = Image.open(input_path).convert('RGBA')
    w, h = img.size
    font_size = max(24, w // 12)
    font = _get_impact_font(font_size)
    draw = ImageDraw.Draw(img)

    def _measure(text):
        try:
            bb = draw.textbbox((0, 0), text, font=font)
            return bb[2] - bb[0], bb[3] - bb[1]
        except AttributeError:
            return draw.textsize(text, font=font)

    def _draw(text, cy):
        text = text.upper()
        tw, th = _measure(text)
        cx = (w - tw) // 2
        outline = max(2, font_size // 14)
        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                if dx or dy:
                    draw.text((cx + dx, cy + dy), text, font=font, fill='black')
        draw.text((cx, cy), text, font=font, fill='white')

    if top_text:
        _draw(top_text, 8)
    if bottom_text:
        _, th = _measure(bottom_text.upper())
        _draw(bottom_text, h - th - font_size // 2 - 8)

    _to_rgb(img).save(output_path)


# ── Tool 18: AI Enhancer (upscale + sharpen) ──────────────────────────────────
def enhance_image(input_path, output_path, scale=2):
    img = Image.open(input_path)
    s = max(1, min(int(scale), 4))
    up = img.resize((img.width * s, img.height * s), LANCZOS)
    _save(ImageEnhance.Sharpness(up).enhance(1.5), output_path)


# ── Tool 19: Color Picker (dominant colors as HTML report) ────────────────────
def get_image_colors(input_path, output_path, num_colors=10):
    img = Image.open(input_path).convert('RGB')
    small = img.resize((150, 150), LANCZOS)
    quantized = small.quantize(colors=int(num_colors))
    pal = quantized.getpalette()

    colors = []
    for i in range(int(num_colors)):
        r, g, b = pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]
        colors.append({'hex': f'#{r:02x}{g:02x}{b:02x}', 'rgb': f'{r},{g},{b}'})

    swatches = ''.join(
        f'<div class="sw"><div class="cb" style="background:{c["hex"]}"></div>'
        f'<div class="info"><b>{c["hex"].upper()}</b><br>'
        f'<span>rgb({c["rgb"]})</span></div></div>'
        for c in colors
    )

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Dominant Colors</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     background:#f8fafc;padding:40px 20px;color:#0f172a}}
h1{{font-size:2rem;font-weight:800;margin-bottom:8px}}
p{{color:#64748b;margin-bottom:32px;font-size:1.05rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:16px}}
.sw{{border-radius:14px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.1);background:#fff}}
.cb{{height:90px}}
.info{{padding:10px;font-size:.78rem}}
.info b{{display:block;margin-bottom:3px;font-size:.85rem}}
.info span{{color:#64748b}}
</style></head>
<body>
<h1>🎨 Dominant Colors</h1>
<p>Top {num_colors} colors extracted from your image</p>
<div class="grid">{swatches}</div>
</body></html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ── Tool 20: Format Converter ─────────────────────────────────────────────────
def convert_image_format(input_path, output_path, target_format):
    img = Image.open(input_path)
    fmt = target_format.upper()
    if fmt in ('JPG', 'JPEG'):
        _to_rgb(img).save(output_path, 'JPEG', quality=90)
    elif fmt == 'PNG':
        img.save(output_path, 'PNG')
    elif fmt == 'WEBP':
        img.save(output_path, 'WEBP', quality=90)
    elif fmt == 'BMP':
        _to_rgb(img).save(output_path, 'BMP')
    elif fmt == 'TIFF':
        img.save(output_path, 'TIFF')
    elif fmt == 'GIF':
        quantized = img.quantize(256) if img.mode not in ('P', 'L') else img
        quantized.save(output_path, 'GIF')
    else:
        img.save(output_path)
