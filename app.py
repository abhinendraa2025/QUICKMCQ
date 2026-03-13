from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import spacy
import random
import PyPDF2
from collections import Counter
from PyPDF2 import PdfReader

app = Flask(__name__)
Bootstrap(app)

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def generate_mcqs(text, num_questions=5):
    if not text:
        return []
    
    # Process the text once using spaCy
    doc = nlp(text)
    
    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]
    
    # Ensure that the number of questions does not exceed the number of sentences
    num_questions = min(num_questions, len(sentences))
    
    # Randomly select sentences to form questions
    selected_sentences = random.sample(sentences, num_questions)
    
    # Initialize list to store generated MCQs
    mcqs = []
    
    # Generate MCQs for each selected sentence
    for sentence in selected_sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)
        
        # Extract nouns from the sentence (these will be the likely subjects for our questions)
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]
        
        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 2:
            continue  # Skip this sentence if we don't have enough nouns
        
        # Count the occurrence of each noun and choose the most common noun as the subject
        noun_counts = Counter(nouns)
        subject = noun_counts.most_common(1)[0][0]
        
        # Generate the question stem by replacing the subject with "______"
        question_stem = sentence.replace(subject, "______")
        
        # Answer choices: Start with the correct answer (subject)
        answer_choices = [subject]
        
        # Add some random nouns from the sentence as distractors (excluding the subject)
        distractors = list(set(nouns) - {subject})  # Avoid using the subject as a distractor
        
        # If there aren't enough distractors, just use whatever nouns are available
        while len(distractors) < 3:
            distractors.append(nouns[0])  # Reuse the first noun if there aren't enough
        
        # Randomly select 3 distractors and shuffle them with the correct answer
        random.shuffle(distractors)
        answer_choices.extend(distractors[:3])
        
        # Shuffle the answer choices to randomize their order
        random.shuffle(answer_choices)
        
        # Determine the correct answer choice (A, B, C, D)
        correct_answer = chr(64 + answer_choices.index(subject) + 1)  # Convert index to letter (A, B, C, D)
        
        # Append the generated MCQ to the list
        mcqs.append((question_stem, answer_choices, correct_answer))
    
    return mcqs

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = ""

        # Check if files were uploaded
        if 'files[]' in request.files:
            files = request.files.getlist('files[]')
            for file in files:
                if file.filename.endswith('.pdf'):
                    # Process PDF file
                    text += process_pdf(file)
                elif file.filename.endswith('.txt'):
                    # Process text file
                    text += file.read().decode('utf-8')
        else:
            # Process manual input
            text = request.form['text']

        # Get the selected number of questions from the dropdown menu
        num_questions = int(request.form['num_questions'])

        mcqs = generate_mcqs(text, num_questions=num_questions)  # Pass the selected number of questions

        # Ensure each MCQ is formatted correctly as (question_stem, answer_choices, correct_answer)
        mcqs_with_index = [(i + 1, mcq) for i, mcq in enumerate(mcqs)]
        return render_template('mcqs.html', mcqs=mcqs_with_index)

    return render_template('index.html')

def process_pdf(file):
    # Initialize an empty string to store the extracted text
    text = ""

    # Create a PyPDF2 PdfReader object
    pdf_reader = PdfReader(file)

    # Loop through each page of the PDF and extract text efficiently
    for page in pdf_reader.pages:
        # Extract text from the current page
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text

if __name__ == '__main__':
    app.run(debug=True)