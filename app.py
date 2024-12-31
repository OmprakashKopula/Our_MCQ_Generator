from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
import spacy
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)

nlp = spacy.load('en_core_web_sm')

@app.route('/generate-mcqs', methods=['POST'])
def generate_mcqs():
    data = request.get_json()
    paragraph = data.get("paragraph", "")
    num_questions = int(data.get("numQuestions", 5))

    if not paragraph.strip():
        return jsonify({"error": "Paragraph cannot be empty", "mcqs": []}), 400

    doc = nlp(paragraph)
    sentences = [sent.text for sent in doc.sents]
    selected_sentences = random.sample(sentences, min(num_questions, len(sentences)))
    mcqs = []

    for sentence in selected_sentences:
        sentence = sentence.lower()
        sent_doc = nlp(sentence)
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]
        if len(nouns) < 2:
            continue
        subject = nouns[0]
        question_stem = sentence.replace(subject, "_____________")
        distractors = nouns[1:]
        while len(distractors) < 3:
            distractors.append("[Distractor]")
        random.shuffle(distractors)
        answer_choices = [subject] + distractors[:3]
        random.shuffle(answer_choices)
        mcqs.append({
            "question": question_stem,
            "choices": answer_choices,
            "answer": subject
        })

    return jsonify({"mcqs": mcqs})

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.get_json()
    mcqs = data.get("mcqs", [])

    # Create a PDF in memory
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 750, "MCQ Questions")
    y_position = 730

    for i, mcq in enumerate(mcqs, start=1):
        if y_position < 50:  # New page if space runs out
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y_position = 750
        pdf.drawString(50, y_position, f"Q{i}: {mcq['question']}")
        y_position -= 20
        for j, choice in enumerate(mcq["choices"], start=1):
            pdf.drawString(70, y_position, f"{chr(64 + j)}) {choice}")
            y_position -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="MCQs.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    app.run(debug=True)
