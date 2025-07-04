from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import boto3
import uuid
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('Users')
appointments_table = dynamodb.Table('Appointments')

sns_client = boto3.client('sns', region_name='us-east-1')
TOPIC_ARN = 'arn:aws:sns:ap-south-1:123456789012:MedTrackTopic'  # Replace with real ARN

# SNS sender
def send_sns_notification(message, subject='MedTrack Notification'):
    try:
        response = sns_client.publish(
            TopicArn=TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        print("SNS Message ID:", response['MessageId'])
    except Exception as e:
        print("SNS Error:", str(e))


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

        try:
            response = users_table.get_item(Key={'username': username})
            if 'Item' in response:
                flash('Username already exists.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            else:
                users_table.put_item(Item={
                    'username': username,
                    'email': email,
                    'password': password
                })
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('login'))
        except ClientError as e:
            flash("Signup failed: " + e.response['Error']['Message'], 'error')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            response = users_table.get_item(Key={'username': username})
            user = response.get('Item')

            if user and user['password'] == password:
                session['username'] = username
                flash('Login successful.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials.', 'error')
        except ClientError:
            flash('Error fetching user data.', 'error')

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
        reason = request.form.get('reason', '')

        appointment_id = str(uuid.uuid4())

        try:
            appointments_table.put_item(Item={
                'appointment_id': appointment_id,
                'user': session['username'],
                'patient': patient_name,
                'doctor': doctor,
                'date': date,
                'time': time,
                'reason': reason
            })

            message = f"New appointment booked for {patient_name} with Dr. {doctor} on {date} at {time}."
            send_sns_notification(message, subject="Appointment Confirmation")

            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('book_appointment'))
        except ClientError as e:
            flash("Error booking appointment: " + e.response['Error']['Message'], 'error')

    return render_template('book_appointment.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill in all fields.', 'error')
        else:
            flash('Thank you for contacting us!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'username' not in session:
        flash('Please log in to access the doctor dashboard.', 'error')
        return redirect(url_for('login'))

    upcoming_appointments = 12
    patients_today = 5
    pending_requests = 3

    recent_appointments = [
        {'patient': 'John Doe', 'date': '2025-06-28', 'time': '10:30 AM', 'reason': 'General Checkup'},
        {'patient': 'Jane Smith', 'date': '2025-06-28', 'time': '11:15 AM', 'reason': 'Follow-up'},
        {'patient': 'Emily Johnson', 'date': '2025-06-29', 'time': '09:00 AM', 'reason': 'Consultation'}
    ]

    return render_template('doctor_dashboard.html',
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
    try:
        response = appointments_table.scan()
        all_appts = response.get('Items', [])
        user_appts = [a for a in all_appts if a['user'] == username]
        today = datetime.today().strftime('%Y-%m-%d')
        upcoming = [a for a in user_appts if a['date'] >= today]

        return render_template('patient_dashboard.html',
            username=username,
            total_appointments=len(user_appts),
            upcoming_appointments=len(upcoming),
            upcoming_appointments_list=upcoming
        )
    except ClientError:
        flash('Error fetching appointment data.', 'error')
        return redirect(url_for('home'))


@app.route('/patient_appointments')
def patient_appointments():
    if 'username' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    try:
        response = appointments_table.scan()
        all_appts = response.get('Items', [])
        user_appts = [a for a in all_appts if a['user'] == session['username']]
        return render_template('patient_appointments.html', appointments=user_appts)
    except ClientError:
        flash('Unable to load appointments.', 'error')
        return redirect(url_for('home'))


@app.route('/patient_details')
def patient_details():
    if 'username' not in session:
        flash('Please log in to view your details.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    try:
        response = users_table.get_item(Key={'username': username})
        user = response.get('Item')

        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('login'))

        return render_template('patient_details.html', username=username, email=user['email'])
    except ClientError:
        flash('Unable to load user details.', 'error')
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
