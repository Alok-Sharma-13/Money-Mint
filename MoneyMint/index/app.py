import sqlite3
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'ade0245d83c58d65ae5dcef50652a9f6'

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            first_name TEXT,
            surname TEXT,
            age INTEGER,
            dob TEXT,
            gmail TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Generate random alphanumeric user ID
def generate_user_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        surname = request.form['surname']
        age = request.form['age']
        dob = request.form['dob']
        gmail = request.form['gmail']
        password = request.form['password']
        user_id = generate_user_id()

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (user_id, first_name, surname, age, dob, gmail, password) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (user_id, first_name, surname, age, dob, gmail, password))
            conn.commit()
            conn.close()
            # Redirect to login page after successful registration
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'This Gmail ID is already registered.'
   
    return render_template('register.html')


# Login route
from flask import Flask, render_template, request, session
import sqlite3

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']

        # Connect to the SQLite database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE gmail = ? AND password = ?', (gmail, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Storing user details in the session
            session['user_id'] = user[1]  # Assuming user_id is the second column
            session['first_name'] = user[2]  # Assuming first_name is the third column
            session['surname'] = user[3]      # Assuming surname is the fourth column
            
            # Render the index.html template instead of redirecting
            return render_template('index.html', first_name=session['first_name'], surname=session['surname'])
        else:
            return 'Invalid login credentials'
   
    return render_template('login.html')


# Profile route
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return redirect('index.html')  # Replace with your desired URL


@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()  # Clear the session data
    flash('You have been logged out.', 'info')  # Flash a message to the user
    return redirect('http://127.0.0.1:5000/login')  # Redirect to the homepage or login page




if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True,port=5000)