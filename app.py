from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import PyPDF2
import docx

app = Flask(__name__)
app.secret_key = 'my_secret_key_123_change_this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size

# Temporary database - Real project mein SQLite use karna
users = {}
JOB_SKILLS = ['python', 'java', 'javascript', 'html', 'css', 'sql', 'flask', 'django',
              'react', 'node', 'git', 'aws', 'docker', 'machine learning', 'data analysis',
              'c++', 'php', 'excel', 'powerbi', 'tableau']

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
    except:
        pass
    return text.lower()

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.lower()

def analyze_resume(text):
    found_skills = []
    for skill in JOB_SKILLS:
        if skill in text:
            found_skills.append(skill.title())

    missing_skills = [skill.title() for skill in JOB_SKILLS if skill not in text]

    interview_questions = []
    question_bank = {
        'Python': 'Python mein list comprehension kya hota hai? Example do.',
        'Java': 'Java mein OOP ke 4 pillars kaun se hain?',
        'Javascript': 'JavaScript mein var, let, const mein difference kya hai?',
        'Sql': 'SQL mein INNER JOIN aur LEFT JOIN mein kya farq hai?',
        'Flask': 'Flask mein blueprint ka use kya hai?',
        'Django': 'Django mein MVT architecture samjhao.',
        'React': 'React mein useState hook kaise kaam karta hai?',
        'Git': 'Git mein merge aur rebase mein kya difference hai?',
        'Aws': 'AWS EC2 aur S3 mein kya antar hai?',
        'Machine Learning': 'Supervised aur Unsupervised learning mein difference batao.'
    }

    for skill in found_skills[:6]:
        if skill in question_bank:
            interview_questions.append(question_bank[skill])
        else:
            interview_questions.append(f"{skill} project mein aapne kaise use kiya hai? Challenges kya aaye?")

    return found_skills, missing_skills[:8], interview_questions

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists!')
            return redirect(url_for('signup'))

        users[username] = generate_password_hash(password)
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        if file and file.filename.endswith(('.pdf', '.docx')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            else:
                text = extract_text_from_docx(filepath)

            if not text.strip():
                flash('Resume se text read nahi ho paya. Koi aur file try karo.')
                os.remove(filepath)
                return redirect(request.url)

            skills, missing, questions = analyze_resume(text)
            os.remove(filepath)

            return render_template('dashboard.html',
                                 username=session['username'],
                                 skills=skills,
                                 missing=missing,
                                 questions=questions)
        else:
            flash('Only PDF or DOCX files allowed!')

    # YAHAN CHANGE KIYA - Default values bhejo
    return render_template('dashboard.html',
                         username=session['username'],
                         skills=[],
                         missing=[],
                         questions=[])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)