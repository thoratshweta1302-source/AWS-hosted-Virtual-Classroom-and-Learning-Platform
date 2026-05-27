from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)

app.secret_key = "secretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

# AWS S3 Config
S3_BUCKET = 'aws-project-virtualclassroom'
S3_REGION = 'eu-north-1'

s3 = boto3.client('s3', region_name=S3_REGION)

# Database Config
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'mydb'


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


# HOME PAGE
@app.route('/')
def home():
    return render_template('home.html')


# REGISTER PAGE
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('email')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )

            conn.commit()

            flash('Registration Successful!', 'success')

            return redirect(url_for('login'))

        except pymysql.MySQLError as e:

            if e.args[0] == 1062:
                flash('Username already exists!', 'danger')
            else:
                flash(f"Error: {str(e)}", 'danger')

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')


# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):

            session['username'] = username

            flash('Login Successful!', 'success')

            return redirect(url_for('content'))

        else:
            flash('Invalid Username or Password!', 'danger')

    return render_template('login.html')


# CONTENT PAGE
@app.route('/content', methods=['GET', 'POST'])
def content():

    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    # Course Data
    courses = [
        {
            "title": "Python Programming",
            "description": "Learn Python from beginner to advanced level.",
            "image": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935",
            "badge": "Beginner",
            "link": "python"
        },
        {
            "title": "Web Development",
            "description": "Learn HTML, CSS, JavaScript and Flask.",
            "image": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6",
            "badge": "Intermediate",
            "link": "web-development"
        },
        {
            "title": "Database Management",
            "description": "Learn MySQL and database concepts.",
            "image": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d",
            "badge": "Advanced",
            "link": "database"
        }
    ]

    # File Upload
    if request.method == 'POST':

        file = request.files['file']

        if file:

            try:
                s3.upload_fileobj(file, S3_BUCKET, file.filename)

                flash(f"{file.filename} uploaded successfully!", 'success')

            except Exception as e:
                flash(f"Upload Error: {str(e)}", 'danger')

    return render_template('content.html', courses=courses)


# ENROLL ROUTE
@app.route('/enroll/<course_name>')
def enroll(course_name):

    flash(f"You enrolled in {course_name} course!", 'success')

    return redirect(url_for('content'))


# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    flash('Logged out successfully!', 'info')

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)