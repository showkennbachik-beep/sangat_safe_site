import fitz  # PyMuPDF
import re
from collections import Counter


def summarize_pdf(pdf_path, output_path, num_sentences=10):
    # Extract all text from the PDF
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + " "
    doc.close()

    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("No extractable text found in the PDF.")
        return output_path

    # Calculate word frequencies (TF scoring)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', full_text.lower())
    # Filter out common stop words
    stop_words = {
        "the", "and", "for", "that", "this", "with", "from", "are", "was",
        "were", "been", "have", "has", "had", "not", "but", "can", "all",
        "will", "its", "his", "her", "they", "them", "than", "other",
        "which", "their", "there", "about", "would", "into", "could",
        "more", "also", "each", "may", "these", "some", "such", "only",
    }
    words = [w for w in words if w not in stop_words]
    word_freq = Counter(words)

    # Normalize frequencies
    max_freq = max(word_freq.values()) if word_freq else 1
    for word in word_freq:
        word_freq[word] /= max_freq

    # Score each sentence by sum of its word frequencies
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        score = 0
        sent_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
        for word in sent_words:
            if word in word_freq:
                score += word_freq[word]
        sentence_scores.append((i, score, sentence))

    # Pick top N sentences by score, then sort by original order
    top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    top_sentences = top_sentences[:num_sentences]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])

    # Write summary to output file
    summary = "\n\n".join(s[2] for s in top_sentences)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)

    return output_path
