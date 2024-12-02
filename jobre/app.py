from flask import Flask, render_template, redirect, url_for, request, flash, session
import os
import uuid
import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.security import generate_password_hash

app = Flask(__name__, template_folder='templates')

# Secret key for session management
app.secret_key = 'your_secret_key'

# In-memory storage for user profile and applied jobs
user_profile = {}
user_resume = {}
applied_jobs = []  # List to store applied job information

# Job and internship listings data
jobs = [
    {
        'title': 'Data Scientist',
        'company': 'XYZ Corp',
        'location': 'New York, USA',
        'salary': '$80,000 - $100,000/year',
        'description': 'Looking for an experienced Data Scientist to analyze large datasets, build predictive models, and contribute to decision-making processes.'
    },
    {
        'title': 'Machine Learning Engineer',
        'company': 'Tech Innovators',
        'location': 'San Francisco, USA',
        'salary': '$95,000 - $120,000/year',
        'description': 'Join our team of engineers to develop machine learning algorithms and improve our product features using AI technologies.'
    },
    {
        'title': 'Business Analyst',
        'company': 'Business Solutions',
        'location': 'Remote',
        'salary': '$70,000 - $90,000/year',
        'description': 'We are looking for a Business Analyst to help us analyze business processes, provide insights, and support data-driven decision-making.'
    },
    {
        'title': 'Data Analyst',
        'company': 'Data Insights Inc.',
        'location': 'Chicago, USA',
        'salary': '$65,000 - $85,000/year',
        'description': 'Seeking a Data Analyst to interpret complex data and provide actionable insights that help drive business strategies.'
    },
    {
        'title': 'HR Specialist',
        'company': 'PeopleFirst',
        'location': 'Los Angeles, USA',
        'salary': '$50,000 - $70,000/year',
        'description': 'We are hiring an HR Specialist to manage recruitment, employee relations, and support HR operations.'
    },
    {
        'title': 'Data Science Intern',
        'company': 'Data Science Labs',
        'location': 'Remote',
        'salary': 'Stipend: $1,500/month',
        'description': 'Join our team for an exciting internship in data analysis, machine learning, and data visualization.'
    },
    {
        'title': 'Machine Learning Intern',
        'company': 'AI Solutions',
        'location': 'Bangalore, India',
        'salary': 'Stipend: ₹25,000/month',
        'description': 'Assist in building machine learning models, data processing, and AI solution development.'
    },
    {
        'title': 'Business Analyst Intern',
        'company': 'Strategy Consult',
        'location': 'London, UK',
        'salary': 'Stipend: £1,200/month',
        'description': 'Help us analyze business operations and support strategic decision-making processes during this internship.'
    },
    {
        'title': 'Data Analyst Intern',
        'company': 'Data Analytics Group',
        'location': 'Sydney, Australia',
        'salary': 'Stipend: $2,000/month',
        'description': 'Work with our team to collect, process, and analyze data to provide valuable insights for business growth.'
    },
    {
        'title': 'Marketing Intern',
        'company': 'Digital Marketing Pro',
        'location': 'New York, USA',
        'salary': 'Stipend: $1,000/month',
        'description': 'Assist in market research, strategy development, and digital campaign management.'
    }
]

# Ensure that the 'uploads' folder exists to store resumes
os.makedirs('uploads', exist_ok=True)

# DynamoDB and SNS setup
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1') 
sns = boto3.client(
    'sns',
    aws_access_key_id='AKIASVQKHY3KFMWJQXEI',
    aws_secret_access_key='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',
    region_name='ap-south-1'
)

# DynamoDB tables
users_table = dynamodb.Table('users')
applied_list_table = dynamodb.Table('Applied_List')

# SNS Topic ARN for notifications (replace with your actual SNS topic ARN)
sns_topic_arn = 'arn:aws:sns:ap-south-1:183631333076:careerconnect'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']

        # Hash the password before saving to DynamoDB
        hashed_password = generate_password_hash(password)

        try:
            users_table.put_item(
                Item={
                    'email': email,
                    'name': name,
                    'password': hashed_password  # Store the hashed password
                }
            )
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except NoCredentialsError:
            flash('AWS credentials not configured correctly.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        # Assuming you have checked the email/password in DynamoDB and it's valid
        session['email'] = email  # Store email in session
        flash('Login successful.', 'success')
        return redirect(url_for('profile'))
    return render_template('login.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # Save the profile data to session
        session['name'] = request.form['name']
        session['age'] = request.form['age']
        session['gender'] = request.form['gender']
        session['headline'] = request.form['headline']
        session['experience'] = request.form['experience']
        session['education'] = request.form['education']
        session['skills'] = request.form['skills']
        session['location'] = request.form['location']
        session['contact'] = request.form['contact']
        
        # Handle resume upload
        resume = request.files.get('resume')
        if resume:
            # Generate a unique filename
            filename = os.path.join('uploads', f"{uuid.uuid4()}_{resume.filename}")
            resume.save(filename)
            session['resume'] = filename

        flash('Profile saved successfully!', 'success')
        return redirect(url_for('dashboard'))  # After update, redirect to the dashboard

    # Retrieve the profile information from session
    return render_template('profile.html', 
                           name=session.get('name', ''), 
                           age=session.get('age', ''), 
                           gender=session.get('gender', ''), 
                           headline=session.get('headline', ''), 
                           experience=session.get('experience', ''), 
                           education=session.get('education', ''), 
                           skills=session.get('skills', ''), 
                           location=session.get('location', ''), 
                           contact=session.get('contact', ''), 
                           resume=session.get('resume', None))


@app.route('/job_list', methods=['GET', 'POST'])
def job_list():
    if request.method == 'POST':
        # Handle the job application
        job_title = request.form.get('job_title')  # Get the job title from the form

        if not job_title:
            flash('Invalid job application. Please try again.', 'danger')
            return redirect(url_for('job_list'))

        # Find the job by title
        job = next((job for job in jobs if job['title'] == job_title), None)

        if job:
            # Retrieve or initialize applied jobs in session
            applied_jobs = session.get('applied_jobs', [])
            if job_title in [applied_job['title'] for applied_job in applied_jobs]:
                flash(f'You have already applied for "{job_title}".', 'warning')
            else:
                applied_jobs.append(job)  # Add the job to the applied list
                session['applied_jobs'] = applied_jobs  # Save updated list in session

                # Add to DynamoDB applied_list table
                try:
                    applied_list_table.put_item(
                        Item={
                            'email': session.get('email'),  # Ensure email is in session
                            'job_title': job['title'],
                            'company': job['company'],
                            'location': job['location'],
                            'salary': job['salary'],
                            'description': job['description']
                        }
                    )
                    flash(f'Successfully applied for "{job_title}".', 'success')
                except NoCredentialsError:
                    flash('AWS credentials not configured correctly.', 'danger')

                # Send an SNS notification (email to all subscribers)
                sns.publish(
                    TopicArn=sns_topic_arn,
                    Message=f"New application for {job['title']} at {job['company']}.",
                    Subject="Job Application Alert"
                )
        else:
            flash('Job not found. Please select a valid job to apply for.', 'danger')
    
    return render_template('job_list.html', jobs=jobs)

@app.route("/dashboard")
def dashboard():
    # Retrieve profile information from session
    profile = {
        'name': session.get('name', ''),
        'age': session.get('age', ''),
        'gender': session.get('gender', ''),
        'headline': session.get('headline', ''),
        'experience': session.get('experience', ''),
        'education': session.get('education', ''),
        'skills': session.get('skills', ''),
        'location': session.get('location', ''),
        'contact': session.get('contact', ''),
        'resume': session.get('resume', None),
        'applied_jobs': session.get('applied_jobs', [])
    }
    return render_template('dashboard.html', profile=profile)

if __name__ == '__main__':
    app.run(debug=True)
