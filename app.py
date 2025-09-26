import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'

# SIMPLE DATABASE CONFIG - Using SQLite for reliable deployment
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'Teacher' or 'Student'
    year_level = db.Column(db.Integer, nullable=True)  # Only for Students

    # Relationships
    prompts = db.relationship('Prompt', backref='teacher', lazy=True, cascade='all, delete-orphan')
    responses = db.relationship('Response', backref='student', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50), default='General')
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Responses cascade when prompt deleted
    responses = db.relationship('Response', backref='prompt', lazy=True, cascade='all, delete-orphan')

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # A single grade per response
    grade = db.relationship('Grade', backref='response', uselist=False, cascade='all, delete-orphan')

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)  # Expect 0-100
    feedback_text = db.Column(db.Text, nullable=True)
    response_id = db.Column(db.Integer, db.ForeignKey('response.id'), nullable=False, unique=True)

# Login loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role-based decorators
def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'Teacher':
            flash('You must be a teacher to access that page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'Student':
            flash('You must be a student to access that page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('teacher_dashboard')) if current_user.user_type == 'Teacher' else redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        password = request.form.get('password') or ''
        user_type = request.form.get('user_type')
        year_level_raw = request.form.get('year_level')
        year_level = int(year_level_raw) if year_level_raw and user_type == 'Student' else None

        if not name or not password or not user_type:
            flash('Name, password and user type are required.', 'error')
            return redirect(url_for('register'))

        if user_type == 'Student' and year_level is None:
            flash('Year level is required for students.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(name=name).first():
            flash('Username already exists. Choose another.', 'error')
            return redirect(url_for('register'))

        user = User(name=name, user_type=user_type, year_level=year_level)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(name=name).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    prompts = Prompt.query.filter_by(teacher_id=current_user.id).order_by(Prompt.timestamp.desc()).all()
    return render_template('teacher_dashboard.html', prompts=prompts)

@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    responses = Response.query.filter_by(student_id=current_user.id).order_by(Response.timestamp.desc()).all()
    return render_template('student_dashboard.html', responses=responses)

@app.route('/create_prompt', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_prompt():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        subject = (request.form.get('subject') or 'General').strip()

        if not title or not content:
            flash('Title and content are required for a prompt.', 'error')
            return redirect(url_for('create_prompt'))

        prompt = Prompt(title=title, content=content, subject=subject, teacher_id=current_user.id)
        db.session.add(prompt)
        db.session.commit()
        flash('Prompt created successfully.', 'success')
        return redirect(url_for('teacher_dashboard'))
    return render_template('create_prompt.html')

@app.route('/prompts')
@login_required
@student_required
def prompts():
    prompts = Prompt.query.order_by(Prompt.timestamp.desc()).all()
    return render_template('prompts.html', prompts=prompts, subject='General')

@app.route('/prompt/<int:prompt_id>', methods=['GET', 'POST'])
@login_required
@student_required
def view_prompt(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    if request.method == 'POST':
        content = (request.form.get('content') or '').strip()
        if not content:
            flash('Response cannot be empty.', 'error')
            return redirect(url_for('view_prompt', prompt_id=prompt_id))
        response = Response(content=content, prompt_id=prompt_id, student_id=current_user.id)
        db.session.add(response)
        db.session.commit()
        flash('Response submitted.', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('view_prompt.html', prompt=prompt)

@app.route('/grade/<int:prompt_id>')
@login_required
@teacher_required
def grade_responses(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.teacher_id != current_user.id:
        flash('You are not authorized to grade responses for that prompt.', 'error')
        return redirect(url_for('teacher_dashboard'))
    responses = Response.query.filter_by(prompt_id=prompt_id).order_by(Response.timestamp.asc()).all()
    return render_template('grade_responses.html', prompt=prompt, responses=responses)

@app.route('/grade_response/<int:response_id>', methods=['POST'])
@login_required
@teacher_required
def grade_response(response_id):
    response = Response.query.get_or_404(response_id)
    if response.prompt.teacher_id != current_user.id:
        flash('You are not authorized to grade this response.', 'error')
        return redirect(url_for('teacher_dashboard'))

    score_raw = request.form.get('score')
    feedback = request.form.get('feedback') or ''
    try:
        score = int(score_raw)
    except (TypeError, ValueError):
        flash('Score must be an integer between 0 and 100.', 'error')
        return redirect(url_for('grade_responses', prompt_id=response.prompt_id))

    if not (0 <= score <= 100):
        flash('Score must be between 0 and 100.', 'error')
        return redirect(url_for('grade_responses', prompt_id=response.prompt_id))

    existing_grade = Grade.query.filter_by(response_id=response_id).first()
    if existing_grade:
        existing_grade.score = score
        existing_grade.feedback_text = feedback
        flash('Grade updated.', 'success')
    else:
        grade = Grade(score=score, feedback_text=feedback, response_id=response_id)
        db.session.add(grade)

    db.session.commit()
    return redirect(url_for('grade_responses', prompt_id=response.prompt_id))

@app.route('/leaderboard')
@login_required
def leaderboard():
    from sqlalchemy import func
    students_with_grades = db.session.query(
        User.id, User.name, User.year_level, func.avg(Grade.score).label('avg_score')
    ).join(Response, Response.student_id == User.id).join(Grade, Grade.response_id == Response.id).filter(
        User.user_type == 'Student'
    ).group_by(User.id).having(func.count(Grade.id) > 0).order_by(func.avg(Grade.score).desc()).all()

    leaderboard_data = []
    for rank, (uid, name, year_level, avg_score) in enumerate(students_with_grades, start=1):
        leaderboard_data.append({
            'rank': rank,
            'name': name,
            'year_level': year_level,
            'avg_score': round(avg_score, 2)
        })
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)