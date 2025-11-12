from flask import Flask, request, jsonify, session, send_file, Response
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os
import uuid
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
from dotenv import load_dotenv
import traceback
import requests

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  
tf.get_logger().setLevel('ERROR')  

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Session configuration for cross-origin requests
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:5173"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'manglo_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '')
}

# AI API Configuration - GEMINI ONLY
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"



# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Model configuration
IMG_SIZE = (224, 224)
DISEASE_CLASSES = ['Alternaria', 'Anthracnose', 'Black Mould Rot', 'Healthy', 'Stem and Rot']

# Load your trained model
model = None
try:
    model_path = '../Model/best_model_final.h5'
    if os.path.exists(model_path):
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully.")
    else:
        print(f"Warning: Model file not found at {model_path}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Load MobileNetV2 for mango detection
mango_detector = None
try:
    mango_detector = tf.keras.applications.MobileNetV2(
        weights='imagenet',
        include_top=True,
        input_shape=(224, 224, 3)
    )
    print("Mango detector (MobileNetV2) loaded successfully.")
except Exception as e:
    print(f"Error loading mango detector: {e}")
    mango_detector = None

# Mango Chatbot System Prompt
MANGO_CHATBOT_SYSTEM_PROMPT = """You are a specialized AI assistant focused exclusively on mango-related topics. Your expertise includes:

- Mango varieties and cultivars
- Mango cultivation and farming practices
- Mango diseases and pest management
- Mango nutrition and health benefits
- Mango harvesting and post-harvest handling
- Mango processing and uses
- Mango growing conditions and climate requirements
- Mango tree care and maintenance

IMPORTANT RULES:
1. ONLY answer questions related to mangoes
2. If a user asks about anything unrelated to mangoes, politely redirect them by saying: "I'm specialized in mango-related topics only. Please ask me anything about mangoes, such as varieties, cultivation, diseases, nutrition, or uses."
3. Provide accurate, helpful, and concise information
4. Be friendly and professional
5. If you don't know something about mangoes, admit it honestly

Focus areas:
- Mango diseases: Alternaria, Anthracnose, Black Mould Rot, Stem and Root Rot, Powdery Mildew, etc.
- Treatment recommendations and prevention strategies
- Best practices for mango farming
- Mango varieties suitable for different climates
- Nutritional benefits and culinary uses"""

def call_gemini_api(user_message):
    """Call Gemini API for chatbot responses"""
    
    if not GEMINI_API_KEY:
        return {
            "error": "API not configured",
            "message": "Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
        }
    
    try:
        print("Calling Gemini API...")
        
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{MANGO_CHATBOT_SYSTEM_PROMPT}\n\nUser question: {user_message}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            }
        }
        
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message_text = result['candidates'][0]['content']['parts'][0]['text']
            return {
                "success": True,
                "message": message_text
            }
        else:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            return {
                "error": f"API Error: {response.status_code}",
                "message": f"Gemini API returned an error. Please try again later."
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Timeout",
            "message": "The request timed out. Please try again."
        }
    except Exception as e:
        print(f"Gemini API error: {e}")
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "An error occurred while processing your request. Please try again."
        }

def generate_placeholder_image(width, height, text="Placeholder"):
    """Generate a placeholder image with given dimensions"""
    try:
        img = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", size=min(width, height) // 10)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font)
        draw.rectangle([0, 0, width-1, height-1], outline='#cccccc')
        
        return img
    except Exception as e:
        print(f"Error generating placeholder: {e}")
        img = Image.new('RGB', (width, height), color='#f0f0f0')
        return img

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def is_mango_image(image_input):
    """Detect if the uploaded image contains a mango using MobileNetV2"""
    if mango_detector is None:
        return True, "Validation skipped"
    
    try:
        if isinstance(image_input, str):
            image = Image.open(image_input)
        else:
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            
            image_bytes = image_input.read()
            
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            
            image = Image.open(io.BytesIO(image_bytes))
        
        image = image.convert('RGB')
        image = image.resize((224, 224))
        
        img_array = img_to_array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
        
        predictions = mango_detector.predict(img_array, verbose=0)
        decoded = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=5)[0]
        
        mango_related_classes = [
            'mango', 'fruit', 'orange', 'lemon', 'banana', 
            'fig', 'pineapple', 'jackfruit', 'pomegranate',
            'Granny_Smith', 'strawberry', 'custard_apple'
        ]
        
        for _, class_name, confidence in decoded:
            class_name_lower = class_name.lower()
            if any(mango_class in class_name_lower for mango_class in mango_related_classes):
                return True, f"Detected as fruit/mango-related ({class_name}: {confidence:.2%})"
        
        top_class = decoded[0][1]
        top_confidence = decoded[0][2]
        
        return False, f"Not a mango image. Detected as: {top_class} ({top_confidence:.2%})"
        
    except Exception as e:
        print(f"Error in mango detection: {e}")
        traceback.print_exc()
        return True, f"Validation error: {str(e)}"

def preprocess_image(image_input):
    """Preprocess image for model prediction"""
    try:
        if isinstance(image_input, str):
            image = load_img(image_input, target_size=IMG_SIZE)
        else:
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            
            image_bytes = image_input.read()
            
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('RGB')
            image = image.resize(IMG_SIZE)
        
        img_array = img_to_array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        
        return img_array
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        traceback.print_exc()
        return None

def predict_disease(image_input):
    """Predict disease from image"""
    if model is None:
        return {"error": "Model not loaded"}
    
    try:
        processed_image = preprocess_image(image_input)
        if processed_image is None:
            return {"error": "Failed to process image"}
        
        predictions = model.predict(processed_image, verbose=0)
        
        predicted_class_idx = np.argmax(predictions[0])
        predicted_class = DISEASE_CLASSES[predicted_class_idx]
        confidence = float(predictions[0][predicted_class_idx])
        
        results = {
            "predicted_class": predicted_class,
            "disease": predicted_class,
            "confidence": confidence,
            "all_probabilities": {
                DISEASE_CLASSES[i]: float(predictions[0][i]) 
                for i in range(len(DISEASE_CLASSES))
            }
        }
        
        return results
    except Exception as e:
        print(f"Error in prediction: {e}")
        traceback.print_exc()
        return {"error": f"Prediction failed: {str(e)}"}

def get_treatment_recommendations(disease):
    """Get treatment recommendations based on disease"""
    recommendations = {
        'Alternaria': "Apply copper-based or mancozeb fungicides. Remove infected leaves and fruits. Ensure proper air circulation and avoid overhead watering.",
        'Anthracnose': "Apply copper-based fungicides or propiconazole. Remove infected fruits and maintain proper sanitation. Prune for better air circulation.",
        'Black Mould Rot': "Improve storage conditions with proper ventilation. Apply post-harvest fungicides. Handle fruits carefully to avoid wounds.",
        'Healthy': "Continue regular maintenance and monitoring. Follow good agricultural practices for disease prevention.",
        'Stem and Rot': "Apply systemic fungicides like carbendazim. Remove infected plant parts. Improve drainage and avoid waterlogging."
    }
    return recommendations.get(disease, "Consult with agricultural expert for treatment advice.")

# Routes
@app.route("/")
def home():
    return jsonify({
        "message": "Mango Disease Management API is running",
        "version": "1.0",
        "endpoints": {
            "health": "/api/health",
            "register": "/api/register",
            "login": "/api/login",
            "predict": "/api/predict",
            "history": "/api/history",
            "diseases": "/api/diseases",
            "chatbot": "/api/chatbot"
        }
    })

@app.route('/api/placeholder/<int:width>/<int:height>')
def placeholder_image(width, height):
    """Generate and serve placeholder images"""
    try:
        width = min(max(width, 50), 2000)
        height = min(max(height, 50), 2000)
        
        img = generate_placeholder_image(width, height, f"{width}x{height}")
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"Error generating placeholder image: {e}")
        return jsonify({"error": "Failed to generate placeholder image"}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    try:
        if 'user_id' in session:
            return jsonify({
                'authenticated': True,
                'user_id': session.get('user_id'),
                'email': session.get('email')
            }), 200
        else:
            return jsonify({'authenticated': False}), 200
    except Exception as e:
        print(f"Auth check error: {e}")
        return jsonify({'authenticated': False}), 200

@app.route('/api/register', methods=['POST'])
def register():
    connection = None
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "User already exists"}), 409

            cursor.execute(
                "INSERT INTO users (email, password, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                (email, hashed_password, datetime.now(), datetime.now())
            )
            connection.commit()
            return jsonify({"message": "User registered successfully"}), 201
        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        print(f"Registration error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    connection = None
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
                
                print(f"User logged in: {user[1]} (ID: {user[0]})")
                
                return jsonify({
                    "message": "Login successful",
                    "success": True,
                    "user": {"id": user[0], "email": user[1]},
                    "redirect": "dashboard"
                }), 200
            else:
                return jsonify({
                    "error": "Invalid email or password", 
                    "success": False
                }), 401
        else:
            return jsonify({"error": "Database connection failed"}), 500

    except Exception as e:
        print(f"Login error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Login failed. Please try again."}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Mango-focused AI Chatbot endpoint - Using Gemini API Only"""
    try:
        print("=" * 50)
        print("CHATBOT REQUEST RECEIVED")
        print("=" * 50)
        
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data or 'message' not in data:
            print("ERROR: No message in request")
            return jsonify({
                "error": "No message provided",
                "message": "Please provide a message in the request body",
                "success": False
            }), 400
        
        user_message = data.get('message', '').strip()
        print(f"User message: {user_message}")
        
        if not user_message:
            print("ERROR: Empty message")
            return jsonify({
                "error": "Empty message",
                "message": "Please provide a non-empty message",
                "success": False
            }), 400
        
        print(f"Calling Gemini API...")
        print(f"Gemini API Key present: {bool(GEMINI_API_KEY)}")
        
        result = call_gemini_api(user_message)
        print(f"API Result: {result}")
        
        if "error" in result:
            print(f"ERROR from API: {result.get('error')}")
            return jsonify({
                "error": result.get("error"),
                "message": result.get("message"),
                "success": False
            }), 500
        
        print("SUCCESS - Sending response")
        return jsonify({
            "success": True,
            "message": result.get("message"),
            "user_message": user_message
        }), 200
        
    except Exception as e:
        print(f"CHATBOT EXCEPTION: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "success": False
        }), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        print(f"Session data: {dict(session)}")
        print(f"Request files: {request.files}")
        print(f"Request form: {request.form}")
        
        if 'user_id' not in session:
            print("Authentication failed - no user_id in session")
            return jsonify({"error": "Authentication required", "details": "Please log in first"}), 401
        
        if 'image' not in request.files:
            print("No image file in request")
            return jsonify({"error": "No image file provided", "details": "Please select an image file"}), 400
        
        file = request.files['image']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            return jsonify({"error": "No file selected", "details": "Filename is empty"}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400
        
        is_mango, validation_message = is_mango_image(file)
        
        if not is_mango:
            return jsonify({
                "error": "Invalid image type",
                "message": "Please upload a mango image only.",
                "details": validation_message,
                "is_mango": False
            }), 400
        
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.seek(0)
        file.save(filepath)
        
        prediction_result = predict_disease(filepath)
        
        if "error" in prediction_result:
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify(prediction_result), 500
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO predictions (user_id, image_path, predicted_disease, 
                   confidence, created_at) VALUES (%s, %s, %s, %s, %s)""",
                (session['user_id'], filepath, prediction_result['predicted_class'], 
                 prediction_result['confidence'], datetime.now())
            )
            connection.commit()
            prediction_id = cursor.lastrowid
            connection.close()
            
            return jsonify({
                "id": prediction_id,
                "predicted_class": prediction_result['predicted_class'],
                "disease": prediction_result['predicted_class'],
                "confidence": prediction_result['confidence'],
                "all_probabilities": prediction_result['all_probabilities'],
                "recommendations": get_treatment_recommendations(prediction_result['predicted_class']),
                "is_mango": True,
                "validation_message": validation_message
            }), 200
        else:
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({"error": "Database connection failed"}), 500
    
    except Exception as e:
        print(f"Prediction error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    connection = None
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                """SELECT id, predicted_disease, confidence, created_at 
                   FROM predictions WHERE user_id = %s ORDER BY created_at DESC LIMIT 20""",
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
        print(f"History error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/diseases', methods=['GET'])
def get_disease_info():
    """Get information about all supported diseases"""
    try:
        disease_info = {
            'Alternaria': {
                'name': 'Alternaria Leaf Spot',
                'symptoms': 'Brown spots with concentric rings on leaves, premature leaf drop',
                'treatment': get_treatment_recommendations('Alternaria'),
                'severity': 'Moderate',
                'prevention': 'Avoid overhead watering, maintain plant hygiene'
            },
            'Anthracnose': {
                'name': 'Anthracnose',
                'symptoms': 'Dark, sunken spots on fruits and leaves, pink spore masses',
                'treatment': get_treatment_recommendations('Anthracnose'),
                'severity': 'High',
                'prevention': 'Proper air circulation, remove infected debris'
            },
            'Black Mould Rot': {
                'name': 'Black Mould Rot',
                'symptoms': 'Black sooty growth on fruit surface during storage',
                'treatment': get_treatment_recommendations('Black Mould Rot'),
                'severity': 'Moderate',
                'prevention': 'Careful handling, proper storage conditions'
            },
            'Stem and Rot': {
                'name': 'Stem and Root Rot',
                'symptoms': 'Wilting, yellowing leaves, dark lesions on stem base',
                'treatment': get_treatment_recommendations('Stem and Rot'),
                'severity': 'High',
                'prevention': 'Improve drainage, avoid waterlogging'
            },
            'Healthy': {
                'name': 'Healthy Plant',
                'symptoms': 'No visible disease symptoms, healthy green foliage',
                'treatment': get_treatment_recommendations('Healthy'),
                'severity': 'None',
                'prevention': 'Continue regular maintenance and monitoring'
            }
        }
        
        return jsonify({
            "diseases": disease_info,
            "total_classes": len(DISEASE_CLASSES)
        }), 200
        
    except Exception as e:
        print(f"Disease info error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict/test', methods=['POST'])
def predict_test():
    """Test prediction without authentication (for development)"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        is_mango, validation_message = is_mango_image(file)
        
        if not is_mango:
            return jsonify({
                "error": "Invalid image type",
                "message": "Please upload a mango image only.",
                "details": validation_message,
                "is_mango": False
            }), 400
        
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.seek(0)
        file.save(filepath)
        
        prediction_result = predict_disease(filepath)
        
        try:
            os.remove(filepath)
        except:
            pass
        
        if "error" in prediction_result:
            return jsonify(prediction_result), 500
        
        return jsonify({
            "predicted_class": prediction_result['predicted_class'],
            "disease": prediction_result['predicted_class'],
            "confidence": prediction_result['confidence'],
            "all_probabilities": prediction_result['all_probabilities'],
            "recommendations": get_treatment_recommendations(prediction_result['predicted_class']),
            "is_mango": True,
            "validation_message": validation_message
        }), 200
    
    except Exception as e:
        print(f"Test prediction error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    try:
        connection = get_db_connection()
        db_status = "connected" if connection else "disconnected"
        if connection:
            connection.close()
        
        model_status = "loaded" if model is not None else "not_loaded"
        detector_status = "loaded" if mango_detector is not None else "not_loaded"
        chatbot_status = "gemini_configured" if GEMINI_API_KEY else "not_configured"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "model": model_status,
            "mango_detector": detector_status,
            "chatbot": chatbot_status,
            "supported_diseases": DISEASE_CLASSES
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

# Suppress Flask development server warning in logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == '__main__':
    print("🥭 Starting Mango Disease Management API...")
    print(f"✓ Model Status: {'Loaded' if model else 'Not Loaded'}")
    print(f"✓ Mango Detector: {'Loaded' if mango_detector else 'Not Loaded'}")
    print(f"✓ AI Chatbot: {'Gemini Configured' if GEMINI_API_KEY else 'Not Configured - Add GEMINI_API_KEY to .env'}")
    print(f"✓ Supported Diseases: {', '.join(DISEASE_CLASSES)}")
    print("✓ Server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)