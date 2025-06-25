from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {}
appointments = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if username in users:
            flash('Username already exists.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            users[username] = {'email': email, 'password': password}
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            flash('Login successful.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'error')

    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'username' not in session:
        flash('Please log in to book an appointment.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        patient_name = request.form['patient_name']
        doctor = request.form['doctor']
        date = request.form['date']
        time = request.form['time']

        appointments.append({
            'user': session['username'],
            'patient': patient_name,
            'doctor': doctor,
            'date': date,
            'time': time,
            'reason': request.form.get('reason', '')
        })

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('book_appointment'))

    return render_template('book_appointment.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('contact'))

        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'username' not in session:
        flash('Please log in to access the doctor dashboard.', 'error')
        return redirect(url_for('login'))

    # Sample doctor data or get from database
    upcoming_appointments = 12
    patients_today = 5
    pending_requests = 3

    recent_appointments = [
        {'patient': 'John Doe', 'date': '2025-06-28', 'time': '10:30 AM', 'reason': 'General Checkup'},
        {'patient': 'Jane Smith', 'date': '2025-06-28', 'time': '11:15 AM', 'reason': 'Follow-up'},
        {'patient': 'Emily Johnson', 'date': '2025-06-29', 'time': '09:00 AM', 'reason': 'Consultation'}
    ]

    return render_template(
        'doctor_dashboard.html',
        upcoming_appointments=upcoming_appointments,
        patients_today=patients_today,
        pending_requests=pending_requests,
        recent_appointments=recent_appointments
    )


@app.route('/patient_dashboard')
def patient_dashboard():
    if 'username' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    user_appts = [a for a in appointments if a['user'] == username]
    today = datetime.today().strftime('%Y-%m-%d')
    upcoming = [a for a in user_appts if a['date'] >= today]

    return render_template(
        'patient_dashboard.html',
        username=username,
        total_appointments=len(user_appts),
        upcoming_appointments=len(upcoming),
        upcoming_appointments_list=upcoming
    )

@app.route('/patient_appointments')
def patient_appointments():
    if 'username' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    user_appts = [a for a in appointments if a['user'] == session['username']]
    return render_template('patient_appointments.html', appointments=user_appts)

@app.route('/patient_details')
def patient_details():
    if 'username' not in session:
        flash('Please log in to view your details.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    user = users.get(username)

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    return render_template('patient_details.html', username=username, email=user['email'])



@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
