# app.py  — SANGAT Tools
import os
import sqlite3
import logging
import time
import threading
import webbrowser
from datetime import timedelta
from threading import Timer

from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else reads os.environ

from flask import (Flask, render_template, request, send_file, session,
                   redirect, url_for, flash, jsonify, Response)
from flask_compress import Compress
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import our tools
from tools import (
    merge_pdfs, split_pdf, compress_pdf, convert_pdf_to_text, images_to_pdf,
    lock_pdf, rotate_pdf, convert_pdf_to_word, convert_word_to_pdf, unlock_pdf,
    watermark_pdf, pdf_to_jpg, organize_pdf, add_page_numbers, crop_pdf,
    repair_pdf, redact_pdf, excel_to_pdf, convert_pdf_to_excel, edit_pdf,
    pdf_to_pptx,
    remove_pages, extract_pages, scan_to_pdf, optimize_pdf, ocr_pdf,
    ppt_to_pdf, html_to_pdf, convert_to_pdfa, flatten_pdf_forms,
    sign_pdf, compare_pdfs, summarize_pdf, translate_pdf
)

# Import image tools
from image_tools import (
    resize_image, compress_image, remove_background,
    jpg_to_png, png_to_jpg, crop_image, rotate_image, flip_image,
    add_watermark_to_image, blur_image, adjust_brightness, adjust_contrast,
    sharpen_image, convert_to_grayscale, image_to_pdf_tool, pdf_to_images_tool,
    generate_meme, enhance_image, get_image_colors, convert_image_format
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'static', 'uploads'))
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(BASE_DIR, 'outputs'))
DB_PATH       = os.environ.get('DB_PATH',       os.path.join(BASE_DIR, 'users.db'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'static'),
            template_folder=os.path.join(BASE_DIR, 'templates'))

IS_PRODUCTION = os.environ.get('FLASK_ENV', 'development') == 'production'

app.config.update(
    SECRET_KEY                = os.environ.get('SECRET_KEY', 'dev-only-insecure-key-change-in-production'),
    SESSION_COOKIE_SECURE     = IS_PRODUCTION,
    SESSION_COOKIE_HTTPONLY   = True,
    SESSION_COOKIE_SAMESITE   = 'Lax',
    PERMANENT_SESSION_LIFETIME= timedelta(days=30),
    MAX_CONTENT_LENGTH        = int(os.environ.get('MAX_UPLOAD_MB', 100)) * 1024 * 1024,
    SITE_URL                  = os.environ.get('SITE_URL', 'https://sangatsafesite.com'),
    GA_MEASUREMENT_ID         = os.environ.get('GA_MEASUREMENT_ID', ''),
)

# Enable gzip compression on all responses
Compress(app)

# ── Database ──────────────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
init_db()

# ── Security headers ──────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy',
        'camera=(), microphone=(), geolocation=(), payment=()')
    if IS_PRODUCTION:
        response.headers.setdefault('Strict-Transport-Security',
            'max-age=31536000; includeSubDomains; preload')
    return response

# ── Static file caching ───────────────────────────────────────────────────────
@app.after_request
def cache_static(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response

# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error('500 error: %s', e)
    return render_template('500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    flash('File is too large. Maximum upload size is '
          f'{app.config["MAX_CONTENT_LENGTH"] // (1024*1024)} MB.')
    return redirect(request.referrer or url_for('home'))

# ── SEO utility routes ────────────────────────────────────────────────────────
@app.route('/robots.txt')
def robots_txt():
    site = app.config['SITE_URL']
    content = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /static/uploads/\n'
        'Disallow: /login\n'
        'Disallow: /signup\n'
        'Disallow: /logout\n'
        'Disallow: /checkout\n'
        f'\nSitemap: {site}/sitemap.xml\n'
    )
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    site = app.config['SITE_URL']
    pages = [
        ('/',           '1.0', 'daily'),
        ('/features',   '0.9', 'weekly'),
        ('/pricing',    '0.8', 'weekly'),
        ('/about',      '0.7', 'monthly'),
        ('/faq',        '0.7', 'monthly'),
        ('/blog',       '0.6', 'weekly'),
        ('/our-story',  '0.5', 'monthly'),
        ('/press',      '0.5', 'monthly'),
        ('/contact',    '0.5', 'monthly'),
        ('/security',   '0.5', 'monthly'),
        ('/privacy',    '0.4', 'yearly'),
        ('/terms',      '0.4', 'yearly'),
        ('/cookies',    '0.4', 'yearly'),
        ('/api-docs',   '0.6', 'monthly'),
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pri, freq in pages:
        lines.append(
            f'  <url><loc>{site}{path}</loc>'
            f'<changefreq>{freq}</changefreq>'
            f'<priority>{pri}</priority></url>'
        )
    lines.append('</urlset>')
    return Response('\n'.join(lines), mimetype='application/xml')

# ── Periodic temp-file cleanup ────────────────────────────────────────────────
def _cleanup_old_files(max_age_seconds=3600):
    cutoff = time.time() - max_age_seconds
    for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER):
        for name in os.listdir(folder):
            if name == '.gitkeep':
                continue
            path = os.path.join(folder, name)
            try:
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass

def _start_cleanup_scheduler():
    def run():
        while True:
            time.sleep(1800)  # run every 30 minutes
            try:
                _cleanup_old_files()
            except Exception as ex:
                logger.warning('Cleanup error: %s', ex)
    t = threading.Thread(target=run, daemon=True)
    t.start()

_start_cleanup_scheduler()

# ── Page context injector (makes config vars available in all templates) ──────
@app.context_processor
def inject_globals():
    return {
        'site_url': app.config['SITE_URL'],
        'ga_id':    app.config['GA_MEASUREMENT_ID'],
    }

# ── Health-check endpoint (required by Cloud Run / App Engine) ────────────────
@app.route('/healthz')
def health_check():
    return jsonify({'status': 'ok'}), 200

# ====================================================================
# PAGES
# ====================================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/process-payment', methods=['POST'])
def process_payment():
    # ------------------------------------------------------------------
    # PLACEHOLDER ONLY — this route does NOT process any real payment.
    # It must be replaced with a real payment processor (e.g. Stripe,
    # PayPal) before collecting any real money or card details.
    # Until then, it tells the user the truth instead of faking success.
    # ------------------------------------------------------------------
    flash("Online payments are not active yet. No charge was made. "
          "Please contact support to complete your upgrade manually.")
    return redirect(url_for('home'))

@app.route('/api-docs')
def api_docs():
    return render_template('api.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/security')
def security():
    return render_template('security.html')

# --- NEW CONTENT PAGES ---
@app.route('/our-story')
def our_story():
    return render_template('our_story.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/press')
def press():
    return render_template('press.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

# --- AUTH ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            flash('Account created! You can now log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with sqlite3.connect(DB_PATH) as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            
        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# ====================================================================
# EXISTING TOOL ROUTES
# ====================================================================

@app.route('/merge', methods=['POST'])
def route_merge():
    try:
        files = request.files.getlist('pdfs')
        paths = []
        for file in files:
            path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(path)
            paths.append(path)
        output_path = os.path.join(OUTPUT_FOLDER, "merged.pdf")
        merge_pdfs(paths, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/split', methods=['POST'])
def route_split():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = split_pdf(path, OUTPUT_FOLDER)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/compress', methods=['POST'])
def route_compress():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "compressed_" + secure_filename(file.filename))
        compress_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/convert', methods=['POST'])
def route_convert():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        text_filename = os.path.splitext(file.filename)[0] + ".txt"
        output_path = os.path.join(OUTPUT_FOLDER, text_filename)
        convert_pdf_to_text(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/img2pdf', methods=['POST'])
def route_img2pdf():
    try:
        files = request.files.getlist('images')
        paths = []
        for file in files:
            path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(path)
            paths.append(path)
        output_path = os.path.join(OUTPUT_FOLDER, "images_converted.pdf")
        images_to_pdf(paths, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/lock', methods=['POST'])
def route_lock():
    try:
        file = request.files['pdf']
        password = request.form['password']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "locked_" + secure_filename(file.filename))
        lock_pdf(path, output_path, password)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/rotate', methods=['POST'])
def route_rotate():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        angle = int(request.form.get('angle', 90))
        output_path = os.path.join(OUTPUT_FOLDER, "rotated_" + secure_filename(file.filename))
        rotate_pdf(path, output_path, angle)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf2word', methods=['POST'])
def route_pdf2word():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        convert_pdf_to_word(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/word2pdf', methods=['POST'])
def route_word2pdf():
    try:
        file = request.files['word']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        convert_word_to_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/unlock', methods=['POST'])
def route_unlock():
    try:
        file = request.files['pdf']
        password = request.form['password']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "unlocked_" + secure_filename(file.filename))
        unlock_pdf(path, output_path, password)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/watermark', methods=['POST'])
def route_watermark():
    try:
        file = request.files['pdf']
        text = request.form['watermark_text']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "watermarked_" + secure_filename(file.filename))
        watermark_pdf(path, output_path, text)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf2jpg', methods=['POST'])
def route_pdf2jpg():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = pdf_to_jpg(path, OUTPUT_FOLDER)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/organize', methods=['POST'])
def route_organize():
    try:
        file = request.files['pdf']
        pages = request.form['pages']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "organized_" + secure_filename(file.filename))
        organize_pdf(path, output_path, pages)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pagenumbers', methods=['POST'])
def route_pagenumbers():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "numbered_" + secure_filename(file.filename))
        add_page_numbers(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/crop', methods=['POST'])
def route_crop():
    try:
        file = request.files['pdf']
        margin = int(request.form.get('margin', 50))
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "cropped_" + secure_filename(file.filename))
        crop_pdf(path, output_path, margin)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/repair', methods=['POST'])
def route_repair():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "repaired_" + secure_filename(file.filename))
        repair_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/redact', methods=['POST'])
def route_redact():
    try:
        file = request.files['pdf']
        text = request.form['redact_text']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "redacted_" + secure_filename(file.filename))
        redact_pdf(path, output_path, text)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/excel2pdf', methods=['POST'])
def route_excel2pdf():
    try:
        file = request.files['excel']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        excel_to_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf2excel', methods=['POST'])
def route_pdf2excel():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".xlsx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        convert_pdf_to_excel(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/edit', methods=['POST'])
def route_edit():
    try:
        file = request.files['pdf']
        text = request.form['text']
        page_num = int(request.form.get('page', 1))
        x_pct = int(request.form.get('x', 50))
        y_pct = int(request.form.get('y', 50))
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "edited_" + secure_filename(file.filename))
        edit_pdf(path, output_path, text, page_num, x_pct, y_pct)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf2ppt', methods=['POST'])
def route_pdf2ppt():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".pptx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        pdf_to_pptx(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

# ====================================================================
# NEW TOOL ROUTES
# ====================================================================

@app.route('/remove-pages', methods=['POST'])
def route_remove_pages():
    try:
        file = request.files['pdf']
        pages = request.form['pages']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "removed_" + secure_filename(file.filename))
        remove_pages(path, output_path, pages)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/extract-pages', methods=['POST'])
def route_extract_pages():
    try:
        file = request.files['pdf']
        pages = request.form['pages']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "extracted_" + secure_filename(file.filename))
        extract_pages(path, output_path, pages)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/scan2pdf', methods=['POST'])
def route_scan2pdf():
    try:
        files = request.files.getlist('images')
        paths = []
        for file in files:
            path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(path)
            paths.append(path)
        output_path = os.path.join(OUTPUT_FOLDER, "scanned.pdf")
        scan_to_pdf(paths, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/optimize', methods=['POST'])
def route_optimize():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "optimized_" + secure_filename(file.filename))
        optimize_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/ocr', methods=['POST'])
def route_ocr():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "ocr_" + secure_filename(file.filename))
        ocr_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/ppt2pdf', methods=['POST'])
def route_ppt2pdf():
    try:
        file = request.files['ppt']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        ppt_to_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/html2pdf', methods=['POST'])
def route_html2pdf():
    try:
        file = request.files['html']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + ".pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        html_to_pdf(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf2pdfa', methods=['POST'])
def route_pdf2pdfa():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "pdfa_" + secure_filename(file.filename))
        convert_to_pdfa(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/pdf-forms', methods=['POST'])
def route_pdf_forms():
    try:
        file = request.files['pdf']
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "flattened_" + secure_filename(file.filename))
        flatten_pdf_forms(path, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/sign', methods=['POST'])
def route_sign():
    try:
        file = request.files['pdf']
        signature_text = request.form['signature_text']
        page_num = int(request.form.get('page', 1))
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "signed_" + secure_filename(file.filename))
        sign_pdf(path, output_path, signature_text, page_num)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/compare', methods=['POST'])
def route_compare():
    try:
        file1 = request.files['pdf1']
        file2 = request.files['pdf2']
        path1 = os.path.join(UPLOAD_FOLDER, secure_filename(file1.filename))
        path2 = os.path.join(UPLOAD_FOLDER, secure_filename(file2.filename))
        file1.save(path1)
        file2.save(path2)
        output_path = os.path.join(OUTPUT_FOLDER, "comparison.html")
        compare_pdfs(path1, path2, output_path)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/summarize', methods=['POST'])
def route_summarize():
    try:
        file = request.files['pdf']
        num_sentences = int(request.form.get('sentences', 10))
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_filename = os.path.splitext(file.filename)[0] + "_summary.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        summarize_pdf(path, output_path, num_sentences)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

@app.route('/translate', methods=['POST'])
def route_translate():
    try:
        file = request.files['pdf']
        target_lang = request.form.get('target_lang', 'es')
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(path)
        output_path = os.path.join(OUTPUT_FOLDER, "translated_" + secure_filename(file.filename))
        translate_pdf(path, output_path, target_lang)
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        logger.error('Tool error in %s: %s', request.path, e, exc_info=True)
        return _pdf_error(str(e))

# ====================================================================
# IMAGE TOOL ROUTES
# ====================================================================

def _img_save(file):
    fname = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, fname)
    file.save(path)
    return path, fname

def _img_error(msg, code=400):
    return _tool_error(msg, code)

def _pdf_error(msg, code=400):
    return _tool_error(msg, code)

def _tool_error(msg, code=400):
    return f"""<!DOCTYPE html>
<html><head><title>Tool Error — SANGAT Tools</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:#f8fafc;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#fff;border-radius:16px;padding:40px;max-width:520px;width:100%;box-shadow:0 4px 24px rgba(0,0,0,.08);text-align:center}}
.icon{{font-size:3rem;margin-bottom:16px}}
h2{{color:#0f172a;font-size:1.4rem;font-weight:700;margin-bottom:12px}}
p{{color:#64748b;font-size:.95rem;line-height:1.6;margin-bottom:24px}}
.btn{{display:inline-block;background:#4f46e5;color:#fff;font-weight:600;padding:12px 28px;border-radius:10px;text-decoration:none;font-size:.95rem}}
.btn:hover{{background:#4338ca}}
</style></head>
<body><div class="card">
    <div class="icon">⚠️</div>
    <h2>Something went wrong</h2>
    <p>{msg}</p>
    <a href="/" class="btn">← Back to tools</a>
</div></body></html>""", code

@app.route('/img/resize', methods=['POST'])
def route_img_resize():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        w = request.form.get('width', 800)
        h = request.form.get('height', 600)
        aspect = request.form.get('maintain_aspect') == 'on'
        out = os.path.join(OUTPUT_FOLDER, 'resized_' + fname)
        resize_image(path, out, w, h, aspect)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/compress', methods=['POST'])
def route_img_compress():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        quality = int(request.form.get('quality', 60))
        base = os.path.splitext(fname)[0]
        out = os.path.join(OUTPUT_FOLDER, f'compressed_{base}.jpg')
        compress_image(path, out, quality)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/remove-bg', methods=['POST'])
def route_img_rembg():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        base = os.path.splitext(fname)[0]
        out = os.path.join(OUTPUT_FOLDER, f'{base}_nobg.png')
        remove_background(path, out)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/jpg2png', methods=['POST'])
def route_img_jpg2png():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        out = os.path.join(OUTPUT_FOLDER, os.path.splitext(fname)[0] + '.png')
        jpg_to_png(path, out)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/png2jpg', methods=['POST'])
def route_img_png2jpg():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        quality = int(request.form.get('quality', 90))
        out = os.path.join(OUTPUT_FOLDER, os.path.splitext(fname)[0] + '.jpg')
        png_to_jpg(path, out, quality)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/crop', methods=['POST'])
def route_img_crop():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        left   = request.form.get('left',   0)
        top    = request.form.get('top',    0)
        right  = request.form.get('right',  100)
        bottom = request.form.get('bottom', 100)
        out = os.path.join(OUTPUT_FOLDER, 'cropped_' + fname)
        crop_image(path, out, left, top, right, bottom)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/rotate', methods=['POST'])
def route_img_rotate():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        angle = request.form.get('angle', 90)
        out = os.path.join(OUTPUT_FOLDER, 'rotated_' + fname)
        rotate_image(path, out, angle)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/flip', methods=['POST'])
def route_img_flip():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        direction = request.form.get('direction', 'horizontal')
        out = os.path.join(OUTPUT_FOLDER, 'flipped_' + fname)
        flip_image(path, out, direction)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/watermark', methods=['POST'])
def route_img_watermark():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        text      = request.form.get('text', 'WATERMARK')
        opacity   = request.form.get('opacity', 60)
        font_size = request.form.get('font_size', 40)
        out = os.path.join(OUTPUT_FOLDER, 'watermarked_' + fname)
        add_watermark_to_image(path, out, text, opacity, font_size)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/blur', methods=['POST'])
def route_img_blur():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        radius = request.form.get('radius', 3)
        out = os.path.join(OUTPUT_FOLDER, 'blurred_' + fname)
        blur_image(path, out, radius)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/brightness', methods=['POST'])
def route_img_brightness():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        factor = request.form.get('factor', 1.5)
        out = os.path.join(OUTPUT_FOLDER, 'bright_' + fname)
        adjust_brightness(path, out, factor)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/contrast', methods=['POST'])
def route_img_contrast():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        factor = request.form.get('factor', 1.5)
        out = os.path.join(OUTPUT_FOLDER, 'contrast_' + fname)
        adjust_contrast(path, out, factor)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/sharpen', methods=['POST'])
def route_img_sharpen():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        factor = request.form.get('factor', 2.0)
        out = os.path.join(OUTPUT_FOLDER, 'sharpened_' + fname)
        sharpen_image(path, out, factor)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/grayscale', methods=['POST'])
def route_img_grayscale():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        out = os.path.join(OUTPUT_FOLDER, 'gray_' + fname)
        convert_to_grayscale(path, out)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/to-pdf', methods=['POST'])
def route_img_to_pdf():
    try:
        files = request.files.getlist('images')
        paths = []
        for file in files:
            p, _ = _img_save(file)
            paths.append(p)
        out = os.path.join(OUTPUT_FOLDER, 'images_to.pdf')
        image_to_pdf_tool(paths, out)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/from-pdf', methods=['POST'])
def route_img_from_pdf():
    try:
        f = request.files['pdf']
        path, _ = _img_save(f)
        zip_path = pdf_to_images_tool(path, OUTPUT_FOLDER)
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/meme', methods=['POST'])
def route_img_meme():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        top    = request.form.get('top_text', '')
        bottom = request.form.get('bottom_text', '')
        base   = os.path.splitext(fname)[0]
        out    = os.path.join(OUTPUT_FOLDER, f'meme_{base}.jpg')
        generate_meme(path, out, top, bottom)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/enhance', methods=['POST'])
def route_img_enhance():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        scale = request.form.get('scale', 2)
        out = os.path.join(OUTPUT_FOLDER, 'enhanced_' + fname)
        enhance_image(path, out, scale)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/colors', methods=['POST'])
def route_img_colors():
    try:
        f = request.files['image']
        path, _ = _img_save(f)
        num = int(request.form.get('num_colors', 10))
        out = os.path.join(OUTPUT_FOLDER, 'colors_report.html')
        get_image_colors(path, out, num)
        return send_file(out, as_attachment=True, download_name='color_palette.html')
    except Exception as e:
        return _img_error(str(e))

@app.route('/img/convert-format', methods=['POST'])
def route_img_convert_format():
    try:
        f = request.files['image']
        path, fname = _img_save(f)
        target_fmt = request.form.get('format', 'PNG').upper()
        ext_map = {'JPG': '.jpg', 'JPEG': '.jpg', 'PNG': '.png',
                   'WEBP': '.webp', 'BMP': '.bmp', 'TIFF': '.tif', 'GIF': '.gif'}
        ext = ext_map.get(target_fmt, '.png')
        base = os.path.splitext(fname)[0]
        out  = os.path.join(OUTPUT_FOLDER, f'{base}_converted{ext}')
        convert_image_format(path, out, target_fmt)
        return send_file(out, as_attachment=True)
    except Exception as e:
        return _img_error(str(e))

# ====================================================================

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    if debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1.25, lambda: webbrowser.open_new(f'http://127.0.0.1:{port}/')).start()

    app.run(host='0.0.0.0', port=port, debug=debug)