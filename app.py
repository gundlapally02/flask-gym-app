from flask import Flask, render_template, request, jsonify, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

import os

app = Flask(__name__)

# Ensure correct database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "instance", "gym_recommendations.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session management
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True, index=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.Integer)
    age = db.Column(db.Float)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    hypertension = db.Column(db.Integer)
    diabetes = db.Column(db.Integer)
    bmi = db.Column(db.Float)
    level = db.Column(db.Integer)
    fitness_goal = db.Column(db.Integer)
    fitness_type = db.Column(db.Integer)
    exercises = db.Column(db.String(200))
    diet = db.Column(db.String(200))
    equipment = db.Column(db.String(200))
    reset_token = db.Column(db.String(100), unique=True)

# Load Data
file_path = "gym recommendation.xlsx"
if os.path.exists(file_path):
    data = pd.read_excel(file_path)
    data.drop(columns=['ID'], inplace=True, errors='ignore')
else:
    data = pd.DataFrame()

if not data.empty:
    label_enc = LabelEncoder()
    for col in ['Sex', 'Hypertension', 'Diabetes', 'Level', 'Fitness Goal', 'Fitness Type']:
        data[col] = label_enc.fit_transform(data[col])
    scaler = StandardScaler()
    data[['Age', 'Height', 'Weight', 'BMI']] = scaler.fit_transform(data[['Age', 'Height', 'Weight', 'BMI']])
else:
    scaler = None

@app.route('/')
def home():
    return redirect('/login')

@app.context_processor
def inject_customer_number():
    return {'customer_number': '+91 86886622 ,+91 970411443'}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/recommend')
        return "Invalid credentials. Try again!", 400
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get("username")
        user = User.query.filter_by(username=username).first()
        if user:
            reset_token = os.urandom(16).hex()
            user.reset_token = reset_token
            db.session.commit()
            
            # ✅ Instead of displaying the token, redirect to reset password page
            return redirect(f'/reset_password/{reset_token}')
        return "User not found!", 400
    return render_template("forgot_password.html")

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        return "Invalid or expired token!", 400  # ✅ Error handling for invalid tokens

    if request.method == 'POST':
        new_password = request.form.get("new_password")
        user.password = new_password
        user.reset_token = None  # ✅ Remove token after reset
        db.session.commit()
        return redirect('/login')

    return render_template("reset_password.html", token=token)


@app.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template("chatbot.html")

@app.route('/chat_response', methods=['POST'])
def chat_response():
    user_message = request.json.get("message", "").lower()
    responses = {
        "hello": "Hi! How can I assist you today?",
        "how are you": "I'm just a bot, but I'm here to help!",
        "recommendation": "I can recommend gym workouts based on your profile. Would you like that?",
        "bye": "Goodbye! Have a great day!",
    }
    
    response = responses.get(user_message, "I'm not sure how to answer that. Try asking about gym workouts!")
    return jsonify({"reply": response})


@app.route('/new_registration', methods=['GET', 'POST'])
def new_registration():
    if request.method == 'POST':
        name = request.form.get("name")
        phone = request.form.get("phone")
        username = request.form.get("username")
        password = request.form.get("password")

        existing_user = User.query.filter((User.username == username) | (User.phone == phone)).first()
        if existing_user:
            return redirect('/login')

        session['name'] = name
        session['phone'] = phone
        session['username'] = username
        session['password'] = password

        return redirect('/registration')
    return render_template('new_registration.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if 'username' not in session or 'phone' not in session:
        return redirect('/new_registration')  # Redirect back to enter details again

    if request.method == 'POST':
        username = session.get('username')
        phone = session.get('phone')

        existing_user = User.query.filter((User.username == username) | (User.phone == phone)).first()
        if existing_user:
            return redirect('/login')  # ✅ Redirect only if user exists

        # ✅ Get fitness details with default values to prevent NaN
        height = request.form.get("height", "160")  # Default: 160 cm
        weight = request.form.get("weight", "60")   # Default: 60 kg
        hypertension = request.form.get("hypertension", "0")  # Default: No
        diabetes = request.form.get("diabetes", "0")  # Default: No
        level = request.form.get("level", "0")  # Default: Beginner
        fitness_goal = request.form.get("fitness_goal", "0")  # Default: Weight Loss
        fitness_type = request.form.get("fitness_type", "0")  # Default: Cardio

        # ✅ Ensure valid numeric values
        try:
            height = float(height)
            weight = float(weight)
            bmi = weight / ((height / 100) ** 2)  # ✅ Calculate BMI safely
        except ValueError:
            return "Error: Invalid height or weight values.", 400

        new_user = User(
            name=session.get('name', "Unknown"),  # Default name if missing
            phone=phone,
            username=username,
            password=session.get('password', "default123"),  # Default password if missing
            sex=request.form.get("sex", "0"),  # Default: Female
            age=request.form.get("age", "25"),  # Default: 25 years old
            height=height,
            weight=weight,
            hypertension=int(hypertension),
            diabetes=int(diabetes),
            bmi=bmi,
            level=int(level),
            fitness_goal=int(fitness_goal),
            fitness_type=int(fitness_type)
        )

        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id  # ✅ Store user session after successful registration
        session.pop('name', None)  # ✅ Clear session

        return redirect('/recommend')

    return render_template('registration.html')


@app.route('/recommend', methods=['GET'])
def recommend():
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])
    if not user:
        return redirect('/login')

    # ✅ Prepare user input for similarity comparison
    user_input = {
        "Sex": user.sex,
        "Hypertension": user.hypertension,
        "Diabetes": user.diabetes,
        "Level": user.level,
        "Fitness Goal": user.fitness_goal,
        "Fitness Type": user.fitness_type,
        "Age": user.age,
        "Height": user.height,
        "Weight": user.weight,
        "BMI": user.bmi
    }

    if data.empty or scaler is None:
        return jsonify({"error": "Data not available for recommendations."}), 400

    # ✅ Convert user input into DataFrame
    user_df = pd.DataFrame([user_input])

    # ✅ Ensure required columns exist
    required_features = ['Sex', 'Hypertension', 'Diabetes', 'Level', 'Fitness Goal', 'Fitness Type', 'Age', 'Height', 'Weight', 'BMI']
    for col in required_features:
        if col not in user_df:
            user_df[col] = 0  # Fill missing values with 0

    # ✅ Apply scaling to numerical features
    num_features = ['Age', 'Height', 'Weight', 'BMI']
    user_df[num_features] = scaler.transform(user_df[num_features])

    # ✅ Compute similarity scores
    similarity_scores = cosine_similarity(
        data[required_features],
        user_df
    ).flatten()

    # ✅ Find top similar users
    similar_user_indices = similarity_scores.argsort()[-5:][::-1]
    similar_users = data.iloc[similar_user_indices]

    # ✅ Get the most common recommendation
    if not similar_users.empty:
        recommendation = similar_users[['Exercises', 'Diet', 'Equipment']].mode().iloc[0]
        return render_template("recommend.html",
                               exercises=recommendation['Exercises'],
                               diet=recommendation['Diet'],
                               equipment=recommendation['Equipment'])
    else:
        return render_template("recommend.html",
                               exercises="No recommendations available.",
                               diet="No recommendations available.",
                               equipment="No recommendations available.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)