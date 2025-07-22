"""from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Enable CORS for all routes
CORS(app, origins=["http://localhost:5173"])  # Vite default port

# Sample data
users = [
    {"id": 1, "name": "John Doe", "email": "john@example.com"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com"}
]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Flask backend is running!",
        "status": "success"
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        "users": users,
        "total": len(users)
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Name and email are required"}), 400
    
    new_user = {
        "id": max([u["id"] for u in users]) + 1 if users else 1,
        "name": data["name"],
        "email": data["email"]
    }
    
    users.append(new_user)
    return jsonify(new_user), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if data.get('name'):
        user['name'] = data['name']
    if data.get('email'):
        user['email'] = data['email']
    
    return jsonify(user)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    global users
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    users = [u for u in users if u["id"] != user_id]
    return jsonify({"message": "User deleted successfully"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host='0.0.0.0',
        port=5000
    )"""
# This code is a Flask application that serves as a backend for a web application.

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
CORS(app)
bcrypt = Bcrypt(app)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:5173"])  # Vite default port

@app.route("/")
def home():
    return "API is running"

@app.route("/api/users")
def get_users():
    return jsonify({"message": "User API placeholder"})


# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'manglo_db',
    'user': 'root',
    'password': ''
}

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load your trained model (replace with your model path)
try:
    model_path = '../Model/best_model_final.h5'
    if os.path.exists(model_path):
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully.")
    else:
        print(f"Error loading model: File not found at {model_path}")
    
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Disease classes (update according to your model)
DISEASE_CLASSES = [
    'Healthy',
    'Anthracnose',
    'Bacterial_Canker',
    'Cutting_Weevil',
    'Die_Back',
    'Gall_Midge',
    'Powdery_Mildew',
    'Sooty_Mould'
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def preprocess_image(image_file):
    """Preprocess image for model prediction"""
    try:
        # Open and convert image
        image = Image.open(image_file)
        image = image.convert('RGB')
        
        # Resize image (adjust size according to your model requirements)
        image = image.resize((224, 224))
        
        # Convert to numpy array and normalize
        img_array = np.array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def predict_disease(image_file):
    """Predict disease from image"""
    if model is None:
        return {"error": "Model not loaded"}
    
    try:
        # Preprocess image
        processed_image = preprocess_image(image_file)
        if processed_image is None:
            return {"error": "Failed to process image"}
        
        # Make prediction
        predictions = model.predict(processed_image)
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        
        predicted_disease = DISEASE_CLASSES[predicted_class_idx]
        
        return {
            "disease": predicted_disease,
            "confidence": confidence,
            "all_predictions": {
                DISEASE_CLASSES[i]: float(predictions[0][i]) 
                for i in range(len(DISEASE_CLASSES))
            }
        }
    except Exception as e:
        print(f"Error in prediction: {e}")
        return {"error": "Prediction failed"}

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "User already exists"}), 409
            
            # Insert new user
            cursor.execute(
                "INSERT INTO users (email, password, created_at) VALUES (%s, %s, %s)",
                (email, hashed_password, datetime.now())
            )
            connection.commit()
            
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": "Database connection failed"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, email, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user and bcrypt.check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['email'] = user[1]
                return jsonify({
                    "message": "Login successful",
                    "user": {"id": user[0], "email": user[1]}
                }), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        else:
            return jsonify({"error": "Database connection failed"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Reset file pointer for prediction
            file.seek(0)
            
            # Predict disease
            prediction_result = predict_disease(file)
            
            if "error" in prediction_result:
                return jsonify(prediction_result), 500
            
            # Save prediction to database
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    """INSERT INTO predictions (user_id, image_path, predicted_disease, 
                       confidence, created_at) VALUES (%s, %s, %s, %s, %s)""",
                    (session['user_id'], filepath, prediction_result['disease'], 
                     prediction_result['confidence'], datetime.now())
                )
                connection.commit()
                prediction_id = cursor.lastrowid
                connection.close()
                
                return jsonify({
                    "id": prediction_id,
                    "disease": prediction_result['disease'],
                    "confidence": prediction_result['confidence'],
                    "recommendations": get_treatment_recommendations(prediction_result['disease'])
                }), 200
            else:
                return jsonify({"error": "Database connection failed"}), 500
        else:
            return jsonify({"error": "Invalid file type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                """SELECT id, predicted_disease, confidence, created_at 
                   FROM predictions WHERE user_id = %s ORDER BY created_at DESC""",
                (session['user_id'],)
            )
            predictions = cursor.fetchall()
            
            history = []
            for pred in predictions:
                history.append({
                    "id": pred[0],
                    "disease": pred[1],
                    "confidence": pred[2],
                    "date": pred[3].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return jsonify({"history": history}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        message = data.get('message', '')
        
        # Simple chatbot responses (you can integrate with a more sophisticated NLP model)
        response = get_chatbot_response(message)
        
        return jsonify({"response": response}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_treatment_recommendations(disease):
    """Get treatment recommendations based on disease"""
    recommendations = {
        'Anthracnose': "Apply copper-based fungicides. Remove infected fruits and maintain proper sanitation.",
        'Bacterial_Canker': "Use copper-based bactericides. Prune infected branches and improve air circulation.",
        'Cutting_Weevil': "Apply appropriate insecticides. Remove fallen fruits and maintain clean orchard.",
        'Die_Back': "Prune infected branches. Apply fungicides and improve drainage.",
        'Gall_Midge': "Use systemic insecticides. Remove infected flowers and fruits.",
        'Powdery_Mildew': "Apply sulfur-based fungicides. Ensure good air circulation.",
        'Sooty_Mould': "Control honeydew-producing insects. Apply fungicides if necessary.",
        'Healthy': "Continue regular maintenance and monitoring."
    }
    return recommendations.get(disease, "Consult with agricultural expert for treatment advice.")

def get_chatbot_response(message):
    """Simple chatbot responses"""
    message = message.lower()
    
    if 'anthracnose' in message:
        return "Anthracnose is a fungal disease. Use copper-based fungicides and maintain proper sanitation."
    elif 'healthy' in message:
        return "Great! Your mango appears healthy. Continue regular monitoring and care."
    elif 'treatment' in message:
        return "Treatment depends on the specific disease. Upload an image for accurate diagnosis and recommendations."
    elif 'hello' in message or 'hi' in message:
        return "Hello! I'm here to help you with mango disease diagnosis. Upload an image or ask me questions about mango diseases."
    else:
        return "I can help you identify mango diseases and provide treatment recommendations. Upload an image for analysis or ask specific questions about mango diseases."

if __name__ == '__main__':
    app.run(debug=True)