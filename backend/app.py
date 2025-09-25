from flask import Flask, request, jsonify, session, send_file, Response, current_app, g
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import os
import uuid
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import base64
import requests
import json
import time
import re
import random
import threading
from collections import deque
from dotenv import load_dotenv

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  
tf.get_logger().setLevel('ERROR')  

load_dotenv()  # Loads the .env file

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

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
    'host': 'localhost',
    'database': 'manglo_db',
    'user': 'root',
    'password': ''
}

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

# Chatbot Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
CHAT_MODEL = os.getenv("CHAT_MODEL")
MAX_RESPONSE_TOKENS = 2500

# Enhanced Rate Limiting System
class RateLimitHandler:
    def __init__(self, requests_per_minute=6, requests_per_hour=50):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = deque()
        self.hour_requests = deque()
        self.lock = threading.Lock()
        self.last_request_time = None
        
    def can_make_request(self):
        """Check if we can make a request based on our rate limits"""
        with self.lock:
            now = datetime.now()
            
            # Clean old requests from minute window
            while self.minute_requests and self.minute_requests[0] < now - timedelta(minutes=1):
                self.minute_requests.popleft()
            
            # Clean old requests from hour window
            while self.hour_requests and self.hour_requests[0] < now - timedelta(hours=1):
                self.hour_requests.popleft()
            
            # Check if we can make request
            return (len(self.minute_requests) < self.requests_per_minute and 
                    len(self.hour_requests) < self.requests_per_hour)
    
    def record_request(self):
        """Record that we made a request"""
        with self.lock:
            now = datetime.now()
            self.minute_requests.append(now)
            self.hour_requests.append(now)
            self.last_request_time = now
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            min_interval = 60 / self.requests_per_minute  # seconds between requests
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                time.sleep(wait_time)

    def get_status(self):
        """Get current rate limiting status"""
        with self.lock:
            now = datetime.now()
            
            # Clean old requests
            while self.minute_requests and self.minute_requests[0] < now - timedelta(minutes=1):
                self.minute_requests.popleft()
            while self.hour_requests and self.hour_requests[0] < now - timedelta(hours=1):
                self.hour_requests.popleft()
            
            return {
                'requests_this_minute': len(self.minute_requests),
                'requests_this_hour': len(self.hour_requests),
                'minute_limit': self.requests_per_minute,
                'hour_limit': self.requests_per_hour,
                'can_make_request': self.can_make_request(),
                'last_request': self.last_request_time.isoformat() if self.last_request_time else None
            }

# Initialize global rate limiter with conservative settings for free tier
rate_limiter = RateLimitHandler(requests_per_minute=6, requests_per_hour=50)

def exponential_backoff(attempt, base_delay=2.0, max_delay=60.0, jitter=True):
    """Calculate backoff delay with exponential growth and jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    if jitter:
        delay *= (0.5 + random.random() * 0.5)  # Add ±50% jitter
    return delay

def parse_retry_after(response):
    """Parse Retry-After header from response"""
    retry_after = response.headers.get('Retry-After')
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            return 30  # Default fallback
    return None

def generate_placeholder_image(width, height, text="Placeholder"):
    """Generate a placeholder image with given dimensions"""
    try:
        # Create image with light gray background
        img = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", size=min(width, height) // 10)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill='#666666', font=font)
        
        # Draw border
        draw.rectangle([0, 0, width-1, height-1], outline='#cccccc')
        
        return img
    except Exception as e:
        print(f"Error generating placeholder: {e}")
        # Return minimal placeholder
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

def preprocess_image(image_file):
    """Preprocess image for model prediction"""
    try:
        if hasattr(image_file, 'read'):
            image = Image.open(image_file)
        else:
            image = load_img(image_file, target_size=IMG_SIZE)
            img_array = img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0
            return img_array
        
        image = image.convert('RGB')
        image = image.resize(IMG_SIZE)
        
        img_array = img_to_array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        
        return img_array
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def predict_disease(image_file):
    """Predict disease from image"""
    if model is None:
        return {"error": "Model not loaded"}
    
    try:
        processed_image = preprocess_image(image_file)
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

def search_mango_knowledge(user_message, limit=5):
    """Search mango knowledge base for relevant information"""
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        keywords = re.findall(r'\b\w+\b', user_message.lower())
        keywords = [word for word in keywords if len(word) > 2]
        
        search_terms = ' '.join(keywords)
        
        query = """
        SELECT topic, content, category, subcategory, keywords 
        FROM mango_knowledge_base 
        WHERE MATCH(topic, content, keywords) AGAINST(%s IN NATURAL LANGUAGE MODE)
        ORDER BY MATCH(topic, content, keywords) AGAINST(%s IN NATURAL LANGUAGE MODE) DESC
        LIMIT %s
        """
        
        cursor.execute(query, (search_terms, search_terms, limit))
        results = cursor.fetchall()
        
        if not results:
            like_query = """
            SELECT topic, content, category, subcategory, keywords 
            FROM mango_knowledge_base 
            WHERE topic LIKE %s OR content LIKE %s OR keywords LIKE %s
            LIMIT %s
            """
            like_term = f"%{keywords[0] if keywords else user_message[:20]}%"
            cursor.execute(like_query, (like_term, like_term, like_term, limit))
            results = cursor.fetchall()
        
        connection.close()
        
        knowledge_items = []
        for row in results:
            knowledge_items.append({
                'topic': row[0],
                'content': row[1],
                'category': row[2],
                'subcategory': row[3],
                'keywords': row[4]
            })
        
        return knowledge_items
    
    except Exception as e:
        print(f"Error searching knowledge base: {e}")
        return []

def get_mango_response_from_db(user_message):
    """Generate comprehensive mango response using database knowledge"""
    knowledge_items = search_mango_knowledge(user_message, limit=5)
    
    if not knowledge_items:
        return """Mango Farming Comprehensive Guide

I'm here to provide detailed assistance with all aspects of mango cultivation:

Please ask me specific questions about any of these topics, and I'll provide detailed, practical guidance with step-by-step instructions!"""
    
    # Generate comprehensive response
    response = f"{knowledge_items[0]['category']} - Comprehensive Guide\n\n"
    
    for i, item in enumerate(knowledge_items[:3]):  # Show up to 3 detailed items
        if item['subcategory']:
            response += f"{i+1}. {item['subcategory']} - {item['topic']}\n\n"
        else:
            response += f"{i+1}. {item['topic']}\n\n"
        
        response += f"{item['content']}\n\n"
        
        if i < len(knowledge_items) - 1:
            response += "---\n\n"
    
    # Add actionable next steps
    response += "\nNext Steps & Related Information:\n"
    response += "• Ask for specific dosages and application methods\n"
    response += "• Request seasonal management calendars\n"
    response += "• Inquire about organic alternatives\n"
    response += "• Get information on integrated management approaches\n\n"
    
    # Add related topics
    categories = list(set([item['category'] for item in knowledge_items]))
    if len(categories) > 1:
        response += f"Related Topics Available:\n{', '.join(categories[1:])}\n\n"
    
    response += "Feel free to ask follow-up questions for more specific guidance!"
    
    return response

def get_openrouter_response(messages, max_retries=4):
    """Enhanced OpenRouter API call with better rate limiting"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Mango Disease Management Assistant",
            "Content-Type": "application/json",
        }
        
        system_message = {
            "role": "system",
            "content": """You are a comprehensive mango farming expert assistant. Provide detailed, practical advice on:
            • Disease identification and treatment protocols
            • Pest management strategies  
            • Cultivation best practices
            • Harvest and post-harvest handling
            
            Include specific product recommendations, dosages, and step-by-step procedures when applicable.
            Keep responses informative but concise (under 400 words when possible)."""
        }
        
        payload = {
            "model": CHAT_MODEL,
            "messages": [system_message] + messages[-6:],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": MAX_RESPONSE_TOKENS,
            "top_p": 0.9,
            "frequency_penalty": 0.1
        }
        
        for attempt in range(max_retries):
            try:
                # Check our internal rate limits
                if not rate_limiter.can_make_request():
                    print(f"Internal rate limit hit, waiting 5s...")
                    time.sleep(5)
                    continue
                
                # Wait between requests to be respectful
                rate_limiter.wait_if_needed()
                
                print(f"OpenRouter attempt {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    OPENROUTER_API_URL, 
                    headers=headers, 
                    json=payload, 
                    timeout=45
                )
                
                # Record successful request
                rate_limiter.record_request()
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content'].strip()
                        print(f"OpenRouter success (attempt {attempt + 1})")
                        return content
                    else:
                        print(f"OpenRouter returned empty response")
                        return None
                
                elif response.status_code == 429:
                    # Rate limited by OpenRouter
                    retry_after = parse_retry_after(response)
                    
                    if retry_after:
                        wait_time = retry_after + random.uniform(1, 3)
                        print(f"Rate limited by OpenRouter, waiting {wait_time:.1f}s (Retry-After: {retry_after})")
                    else:
                        wait_time = exponential_backoff(attempt, base_delay=3.0, max_delay=60.0)
                        print(f"Rate limited, exponential backoff: {wait_time:.1f}s")
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print("Max retries reached for rate limiting")
                        return None
                
                elif response.status_code in [500, 502, 503, 504]:
                    # Server errors - retry with backoff
                    wait_time = exponential_backoff(attempt, base_delay=2.0)
                    print(f"Server error {response.status_code}, retrying in {wait_time:.1f}s")
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"Max retries reached for server error {response.status_code}")
                        return None
                
                else:
                    print(f"OpenRouter API error: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"Error details: {error_data}")
                    except:
                        print(f"Response text: {response.text[:200]}...")
                    return None
                    
            except requests.exceptions.Timeout:
                wait_time = exponential_backoff(attempt, base_delay=3.0)
                print(f"Request timeout, retrying in {wait_time:.1f}s")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print("Max retries reached for timeout")
                    return None
                    
            except requests.exceptions.RequestException as e:
                wait_time = exponential_backoff(attempt, base_delay=2.0)
                print(f"Connection error: {e}, retrying in {wait_time:.1f}s")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print("Max retries reached for connection error")
                    return None
        
        return None
        
    except Exception as e:
        print(f"Unexpected error in OpenRouter request: {e}")
        return None

def get_chatbot_response(user_message, conversation_history=[]):
    """Get chatbot response with enhanced fallback"""
    try:
        messages = conversation_history[-6:] + [{"role": "user", "content": user_message}]
        
        api_response = get_openrouter_response(messages)
        if api_response:
            return api_response
        
        print("Falling back to database response")
        return get_mango_response_from_db(user_message)
        
    except Exception as e:
        print(f"Error in chatbot response: {e}")
        return get_mango_response_from_db(user_message)

def save_chat_message(user_id, message, response):
    """Save chat message and response to database"""
    connection = None
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                return False
            
            cursor.execute(
                """INSERT INTO chat_history (user_id, message, response, created_at) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, message, response, datetime.now())
            )
            connection.commit()
            return True
        return False
            
    except Exception as e:
        print(f"Error saving chat message: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

def get_user_conversation_history(user_id, limit=6):
    """Get recent conversation history for context"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                return []
            
            cursor.execute(
                """SELECT message, response FROM chat_history 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            
            history = []
            rows = cursor.fetchall()
            for row in reversed(rows):
                history.extend([
                    {"role": "user", "content": row[0]},
                    {"role": "assistant", "content": row[1]}
                ])
            
            connection.close()
            return history
            
    except Exception as e:
        print(f"Error fetching conversation history: {e}")
        return []

# Routes
@app.route("/")
def home():
    return "Mango Disease Management API is running"

@app.route('/api/placeholder/<int:width>/<int:height>')
def placeholder_image(width, height):
    """Generate and serve placeholder images"""
    try:
        # Limit dimensions to prevent abuse
        width = min(max(width, 50), 2000)
        height = min(max(height, 50), 2000)
        
        # Generate placeholder image
        img = generate_placeholder_image(width, height, f"{width}x{height}")
        
        # Convert to bytes
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        print(f"Error generating placeholder image: {e}")
        return jsonify({"error": "Failed to generate placeholder image"}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True})
    else:
        return jsonify({'authenticated': False})

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
        return jsonify({"error": "Login failed. Please try again."}), 500
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
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            prediction_result = predict_disease(filepath)
            
            if "error" in prediction_result:
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
                    "recommendations": get_treatment_recommendations(prediction_result['predicted_class'])
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
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        conversation_history = get_user_conversation_history(session['user_id'], limit=6)
        bot_response = get_chatbot_response(message, conversation_history)
        save_chat_message(session['user_id'], message, bot_response)
        
        return jsonify({
            "response": bot_response,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "An error occurred while processing your message"}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Enhanced streaming chat endpoint with better rate limiting"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400
        
        current_user_id = session['user_id']
        
        def generate_enhanced_stream():
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    # Check rate limits before attempting
                    if not rate_limiter.can_make_request():
                        print(f"Rate limit protection active, using fallback...")
                        # Use fallback response
                        last_message = messages[-1]['content'] if messages else ""
                        fallback_response = get_mango_response_from_db(last_message)
                        
                        for char in fallback_response:
                            escaped_char = char.replace('"', '\\"').replace('\n', '\\n')
                            yield f'data: {{"content": "{escaped_char}"}}\n\n'
                            time.sleep(0.01)
                        yield 'data: [DONE]\n\n'
                        return
                    
                    rate_limiter.wait_if_needed()
                    
                    headers = {
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "http://localhost:5000",
                        "X-Title": "Mango Disease Management Assistant", 
                        "Content-Type": "application/json",
                    }
                    
                    system_message = {
                        "role": "system",
                        "content": "You are a comprehensive mango farming expert. Provide detailed, practical advice covering disease management, pest control, cultivation, and post-harvest handling. Include specific product names, dosages, and step-by-step procedures. Aim for thorough, actionable responses."
                    }
                    
                    payload = {
                        "model": CHAT_MODEL,
                        "messages": [system_message] + messages[-6:],
                        "stream": True,
                        "temperature": 0.7,
                        "max_tokens": MAX_RESPONSE_TOKENS,
                    }
                    
                    print(f"Streaming attempt {attempt + 1}/{max_retries}")
                    
                    response = requests.post(
                        OPENROUTER_API_URL, 
                        headers=headers, 
                        json=payload, 
                        stream=True, 
                        timeout=60
                    )
                    
                    rate_limiter.record_request()
                    
                    if response.status_code == 200:
                        full_response = ""
                        
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    data_part = line[6:]
                                    if data_part == '[DONE]':
                                        # Save to database
                                        if full_response and messages:
                                            user_message = messages[-1]['content']
                                            try:
                                                save_chat_message(current_user_id, user_message, full_response)
                                            except Exception as save_error:
                                                print(f"Save error: {save_error}")
                                                
                                        yield 'data: [DONE]\n\n'
                                        return
                                    
                                    try:
                                        parsed = json.loads(data_part)
                                        content = parsed.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                        if content:
                                            full_response += content
                                            escaped_content = content.replace('"', '\\"').replace('\n', '\\n')
                                            yield f'data: {{"content": "{escaped_content}"}}\n\n'
                                    except json.JSONDecodeError:
                                        continue
                        return
                    
                    elif response.status_code == 429:
                        wait_time = 10 + (attempt * 5)  # Progressive delay
                        print(f"Streaming rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                        
                        if attempt < max_retries - 1:
                            time.sleep(wait_time)
                            continue
                        else:
                            # Use fallback on final attempt
                            break
                    
                    else:
                        print(f"Streaming error: {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(3 ** attempt)  # Progressive backoff
                            continue
                        else:
                            break
                            
                except Exception as e:
                    print(f"Streaming attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        break
            
            # Fallback response if all attempts failed
            print("Using fallback response for streaming")
            last_message = messages[-1]['content'] if messages else ""
            fallback_response = get_mango_response_from_db(last_message)
            
            for char in fallback_response:
                escaped_char = char.replace('"', '\\"').replace('\n', '\\n')
                yield f'data: {{"content": "{escaped_char}"}}\n\n'
                time.sleep(0.01)
            yield 'data: [DONE]\n\n'
        
        response = Response(
            generate_enhanced_stream(),
            content_type='text/plain; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': 'http://localhost:5173',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        return response
        
    except Exception as e:
        print(f"Enhanced stream chat error: {e}")
        return jsonify({"error": "Failed to process streaming request"}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                return jsonify({"error": "Chat history table not found"}), 500
            
            cursor.execute(
                """SELECT message, response, created_at 
                   FROM chat_history 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT 20""",
                (session['user_id'],)
            )
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "message": row[0],
                    "response": row[1],
                    "timestamp": row[2].isoformat() if row[2] else None
                })
            
            connection.close()
            return jsonify({"history": history}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
            
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

@app.route('/api/rate-limit/status', methods=['GET'])
def rate_limit_status():
    """Check current rate limit status"""
    try:
        status = rate_limiter.get_status()
        return jsonify(status), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                "recommendations": get_treatment_recommendations(prediction_result['predicted_class'])
            }), 200
        else:
            return jsonify({"error": "Invalid file type"}), 400
    
    except Exception as e:
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
        rate_status = rate_limiter.get_status()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "model": model_status,
            "supported_diseases": DISEASE_CLASSES,
            "rate_limiting": {
                "requests_this_minute": rate_status['requests_this_minute'],
                "requests_this_hour": rate_status['requests_this_hour'],
                "can_make_request": rate_status['can_make_request']
            },
            "api_config": {
                "openrouter_configured": bool(OPENROUTER_API_KEY),
                "chat_model": CHAT_MODEL,
                "max_tokens": MAX_RESPONSE_TOKENS
            }
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
    print("🥭 Starting Enhanced Mango Disease Management API...")
    print(f"✓ Model Status: {'Loaded' if model else 'Not Loaded'}")
    print(f"✓ Supported Diseases: {', '.join(DISEASE_CLASSES)}")
    print(f"✓ Chat API: OpenRouter {'Available' if OPENROUTER_API_KEY else 'Not Configured'}")
    print(f"✓ Rate Limiting: {rate_limiter.requests_per_minute}/min, {rate_limiter.requests_per_hour}/hour")
    print(f"✓ Max Response Tokens: {MAX_RESPONSE_TOKENS}")
    print("✓ Server starting on http://localhost:5000")
    print("✓ Enhanced endpoints:")
    print("  • /api/rate-limit/status - Check rate limiting status")
    print("  • /api/health - Comprehensive health check")
    print("  • /api/placeholder/<width>/<height> - Generate placeholder images")
    app.run(debug=True, host='0.0.0.0', port=5000)