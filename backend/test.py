from flask import Flask, request, jsonify, session, send_file, Response
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
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
from dotenv import load_dotenv


load_dotenv()  # Loads the .env file
# ✅ Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# ✅ FIXED: Enable CORS with specific origin and credentials support
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:5173"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ✅ Initialize Bcrypt
bcrypt = Bcrypt(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# ✅ Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'manglo_db',
    'user': 'root',
    'password': ''
}

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Model configuration - Updated to match test code
IMG_SIZE = (224, 224)
DISEASE_CLASSES = ['Alternaria', 'Anthracnose', 'Black Mould Rot', 'Healthy', 'Stem and Rot']

# Load your trained model (replace with your model path)
model = None
try:
    model_path = '../Model/best_model_final.h5'
    if os.path.exists(model_path):
        model = tf.keras.models.load_model(model_path)
        print("✓ Model loaded successfully.")
        print(f"✓ Model input shape: {model.input_shape}")
        print(f"✓ Model output shape: {model.output_shape}")
    else:
        print(f"Error loading model: File not found at {model_path}")
        print("Please update the model_path variable with correct path")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None

# ✅ Updated Chatbot Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
CHAT_MODEL = os.getenv("CHAT_MODEL")

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
    """
    Preprocess image for model prediction - Updated to match test code methodology
    
    Args:
        image_file: File object or file path
        
    Returns:
        numpy.ndarray: Preprocessed image array
    """
    try:
        # Handle both file objects and file paths
        if hasattr(image_file, 'read'):
            # File object - convert to PIL Image
            image = Image.open(image_file)
        else:
            # File path - use keras load_img for consistency with test code
            image = load_img(image_file, target_size=IMG_SIZE)
            img_array = img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize to [0,1]
            return img_array
        
        # For file objects, process similarly to test code
        image = image.convert('RGB')
        image = image.resize(IMG_SIZE)
        
        # Convert to numpy array and preprocess like test code
        img_array = img_to_array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0  # Normalize to [0,1]
        
        return img_array
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def predict_disease(image_file):
    """
    Predict disease from image - Updated to match test code logic
    
    Args:
        image_file: File object or file path
        
    Returns:
        dict: Prediction results matching test code format
    """
    if model is None:
        return {"error": "Model not loaded"}
    
    try:
        # Preprocess image
        processed_image = preprocess_image(image_file)
        if processed_image is None:
            return {"error": "Failed to process image"}
        
        # Make prediction
        predictions = model.predict(processed_image, verbose=0)
        
        # Get prediction results - matching test code logic
        predicted_class_idx = np.argmax(predictions[0])
        predicted_class = DISEASE_CLASSES[predicted_class_idx]
        confidence = float(predictions[0][predicted_class_idx])
        
        # Create results dictionary matching test code format
        results = {
            "predicted_class": predicted_class,
            "disease": predicted_class,  # Keep both for backward compatibility
            "confidence": confidence,
            "all_probabilities": {
                DISEASE_CLASSES[i]: float(predictions[0][i]) 
                for i in range(len(DISEASE_CLASSES))
            },
            "all_predictions": {  # Keep both for backward compatibility
                DISEASE_CLASSES[i]: float(predictions[0][i]) 
                for i in range(len(DISEASE_CLASSES))
            }
        }
        
        return results
    except Exception as e:
        print(f"Error in prediction: {e}")
        return {"error": f"Prediction failed: {str(e)}"}

def get_treatment_recommendations(disease):
    """
    Get treatment recommendations based on disease - Updated with correct disease names
    """
    recommendations = {
        'Alternaria': "Apply copper-based or mancozeb fungicides. Remove infected leaves and fruits. Ensure proper air circulation and avoid overhead watering.",
        'Anthracnose': "Apply copper-based fungicides or propiconazole. Remove infected fruits and maintain proper sanitation. Prune for better air circulation.",
        'Black Mould Rot': "Improve storage conditions with proper ventilation. Apply post-harvest fungicides. Handle fruits carefully to avoid wounds.",
        'Healthy': "Continue regular maintenance and monitoring. Follow good agricultural practices for disease prevention.",
        'Stem and Rot': "Apply systemic fungicides like carbendazim. Remove infected plant parts. Improve drainage and avoid waterlogging."
    }
    return recommendations.get(disease, "Consult with agricultural expert for treatment advice.")

# ✅ NEW: Database-driven mango knowledge function
def search_mango_knowledge(user_message, limit=5):
    """
    Search mango knowledge base for relevant information
    """
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        
        # Extract keywords from user message
        keywords = re.findall(r'\b\w+\b', user_message.lower())
        keywords = [word for word in keywords if len(word) > 2]  # Filter short words
        
        # Create search query using FULLTEXT search
        search_terms = ' '.join(keywords)
        
        # Use FULLTEXT search for better relevance
        query = """
        SELECT topic, content, category, subcategory, keywords 
        FROM mango_knowledge_base 
        WHERE MATCH(topic, content, keywords) AGAINST(%s IN NATURAL LANGUAGE MODE)
        ORDER BY MATCH(topic, content, keywords) AGAINST(%s IN NATURAL LANGUAGE MODE) DESC
        LIMIT %s
        """
        
        cursor.execute(query, (search_terms, search_terms, limit))
        results = cursor.fetchall()
        
        # If no FULLTEXT results, try LIKE search
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
        
        # Format results
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
    """
    Generate comprehensive mango response using database knowledge
    """
    # Search knowledge base
    knowledge_items = search_mango_knowledge(user_message, limit=5)
    
    if not knowledge_items:
        return """**🥭 Mango Farming Assistant**

I'd be happy to help you with any mango-related questions! I can assist with:

**Disease Management:**
• Identification and treatment of diseases like Anthracnose, Alternaria, Black Mould Rot
• Organic and chemical treatment options
• Prevention strategies

**Cultivation Practices:**
• Site selection and planting techniques
• Fertilization and nutrition programs
• Irrigation and water management
• Pruning and orchard maintenance

**Pest Control:**
• Fruit fly management
• Scale insects and mealybug control
• Integrated pest management

**Varieties and Selection:**
• Commercial variety recommendations
• Climate adaptation considerations

**Harvest and Post-Harvest:**
• Proper harvesting techniques
• Storage and handling methods

Please ask me specific questions about mango farming, and I'll provide detailed guidance!"""
    
    # Generate response based on knowledge
    response = f"**🥭 {knowledge_items[0]['category']} Information**\n\n"
    
    for item in knowledge_items:
        if item['subcategory']:
            response += f"**{item['subcategory']} - {item['topic']}**\n\n"
        else:
            response += f"**{item['topic']}**\n\n"
        
        response += f"{item['content']}\n\n"
        
        if len(knowledge_items) > 1:
            response += "---\n\n"
    
    # Add related suggestions
    categories = list(set([item['category'] for item in knowledge_items]))
    if categories:
        response += "\n**💡 Related Topics:**\n"
        response += f"Ask me more about {', '.join(categories)} or any other mango farming topics!\n"
    
    return response

# ✅ Updated Chatbot Functions
def get_openrouter_response(messages):
    """
    Get response from OpenRouter API with enhanced mango context
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Mango Disease Management Assistant",
            "Content-Type": "application/json",
        }
        
        # Enhanced system message with broader mango expertise
        system_message = {
            "role": "system",
            "content": """You are a comprehensive mango farming and agriculture expert. You specialize in ALL aspects of mango cultivation including:

🌱 **Complete Mango Expertise:**
• Disease identification, treatment, and prevention (Anthracnose, Alternaria, Black Mould Rot, Stem Rot, Powdery Mildew, etc.)
• Pest management (Fruit flies, Scale insects, Mealybugs, Thrips, Mites, etc.)
• Soil management and nutrition programs
• Irrigation and water management
• Pruning and orchard management techniques
• Variety selection and propagation
• Harvest timing and post-harvest handling
• Organic farming practices
• Climate requirements and adaptation
• Processing and value addition
• Market preparation and export guidelines

🎯 **Response Guidelines:**
• Provide practical, actionable advice for farmers
• Include specific product names, dosages, and application methods when relevant
• Offer both chemical and organic treatment options
• Consider different scales of farming (small-scale to commercial)
• Always prioritize safety and sustainable practices
• Be specific about timing, weather conditions, and seasonal considerations

You should respond to ANY question related to mango farming, not just diseases. Always provide comprehensive, practical advice in a structured format."""
        }
        
        payload = {
            "model": CHAT_MODEL,
            "messages": [system_message] + messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        else:
            print(f"OpenRouter API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error with OpenRouter API: {e}")
        return None

def get_chatbot_response(user_message, conversation_history=[]):
    """
    Get chatbot response with OpenRouter API and database fallback
    
    Args:
        user_message (str): The user's message
        conversation_history (list): Previous conversation messages
    
    Returns:
        str: Bot response
    """
    try:
        # Prepare messages for API
        messages = conversation_history + [{"role": "user", "content": user_message}]
        
        # Try OpenRouter API first
        api_response = get_openrouter_response(messages)
        if api_response:
            return api_response
        
        # Fallback to database-driven responses if API fails
        print("OpenRouter API failed, using database knowledge")
        return get_mango_response_from_db(user_message)
        
    except Exception as e:
        print(f"Error in chatbot response: {e}")
        return get_mango_response_from_db(user_message)

def save_chat_message(user_id, message, response):
    """
    FIXED: Save chat message and response to database with proper error handling
    """
    connection = None
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Ensure we have a valid connection and table exists
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                print("chat_history table does not exist")
                return False
            
            # Insert with explicit commit
            cursor.execute(
                """INSERT INTO chat_history (user_id, message, response, created_at) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, message, response, datetime.now())
            )
            connection.commit()
            print(f"✓ Chat message saved for user {user_id}")
            return True
        else:
            print("✗ Database connection failed in save_chat_message")
            return False
            
    except Exception as e:
        print(f"✗ Error saving chat message: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

def get_user_conversation_history(user_id, limit=10):
    """
    FIXED: Get recent conversation history for context with better error handling
    """
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if table exists first
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                print("chat_history table does not exist")
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
            for row in reversed(rows):  # Reverse to get chronological order
                history.extend([
                    {"role": "user", "content": row[0]},
                    {"role": "assistant", "content": row[1]}
                ])
            
            connection.close()
            print(f"✓ Retrieved {len(rows)} chat history items for user {user_id}")
            return history[-20:]  # Keep last 20 messages for context
            
    except Exception as e:
        print(f"✗ Error fetching conversation history: {e}")
        return []

# ✅ Root route
@app.route("/")
def home():
    return "Mango Disease Management API is running"

# ✅ Placeholder route (optional)
@app.route("/api/users")
def get_users():
    return jsonify({"message": "User API placeholder"})

# ✅ Check session login status
@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True})
    else:
        return jsonify({'authenticated': False})

# ✅ Register route
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

            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "User already exists"}), 409

            # Insert new user
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

# ✅ Login route
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

# ✅ Logout route
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

# ✅ Prediction route
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
            
            # Predict disease using the saved file path (matching test code approach)
            prediction_result = predict_disease(filepath)
            
            if "error" in prediction_result:
                return jsonify(prediction_result), 500
            
            # Save prediction to database
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
                    "disease": prediction_result['predicted_class'],  # For backward compatibility
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

# ✅ History route
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
                    "predicted_class": pred[1],  # For consistency
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

# ✅ Enhanced Chat route with debugging
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        print(f"🔄 Processing chat for user {session['user_id']}: {message[:50]}...")
        
        # Get conversation history for context
        conversation_history = get_user_conversation_history(session['user_id'], limit=5)
        
        # Get response from OpenRouter API with fallback
        bot_response = get_chatbot_response(message, conversation_history)
        
        # Save chat history to database with debugging
        save_success = save_chat_message(session['user_id'], message, bot_response)
        if not save_success:
            print("⚠️ Warning: Failed to save chat message to database")
        
        return jsonify({
            "response": bot_response,
            "timestamp": datetime.now().isoformat(),
            "saved": save_success  # For debugging
        }), 200
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({"error": "An error occurred while processing your message"}), 500

# ✅ Get chat history route with debugging
@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            if not cursor.fetchone():
                return jsonify({"error": "Chat history table not found"}), 500
            
            cursor.execute(
                """SELECT message, response, created_at 
                   FROM chat_history 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT 50""",
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
            return jsonify({"history": history, "count": len(history)}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
            
    except Exception as e:
        print(f"❌ Error fetching chat history: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

# ✅ Model info route
@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Get information about the loaded model"""
    try:
        if model is None:
            return jsonify({
                "model_loaded": False,
                "error": "Model not loaded"
            }), 500
        
        return jsonify({
            "model_loaded": True,
            "input_shape": str(model.input_shape),
            "output_shape": str(model.output_shape),
            "classes": DISEASE_CLASSES,
            "num_classes": len(DISEASE_CLASSES),
            "image_size": IMG_SIZE
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Test prediction route (without authentication)
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
            # Save temporarily for prediction
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Predict disease
            prediction_result = predict_disease(filepath)
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except:
                pass
            
            if "error" in prediction_result:
                return jsonify(prediction_result), 500
            
            return jsonify({
                "predicted_class": prediction_result['predicted_class'],
                "confidence": prediction_result['confidence'],
                "all_probabilities": prediction_result['all_probabilities'],
                "recommendations": get_treatment_recommendations(prediction_result['predicted_class'])
            }), 200
        else:
            return jsonify({"error": "Invalid file type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ FIXED: Streaming chat route with proper CORS headers
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming chat endpoint with enhanced mango knowledge
    """
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400
        
        def generate_stream():
            try:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Mango Disease Management Assistant",
                    "Content-Type": "application/json",
                }
                
                # Enhanced system message for comprehensive mango expertise
                system_message = {
                    "role": "system",
                    "content": """You are a comprehensive mango farming and agriculture expert. You specialize in ALL aspects of mango cultivation including:

🌱 **Complete Mango Expertise:**
• Disease identification, treatment, and prevention (Anthracnose, Alternaria, Black Mould Rot, Stem Rot, Powdery Mildew, etc.)
• Pest management (Fruit flies, Scale insects, Mealybugs, Thrips, Mites, etc.)
• Soil management and nutrition programs
• Irrigation and water management
• Pruning and orchard management techniques
• Variety selection and propagation
• Harvest timing and post-harvest handling
• Organic farming practices
• Climate requirements and adaptation
• Processing and value addition
• Market preparation and export guidelines

Provide practical, actionable advice with specific product names, dosages, and application methods when relevant."""
                }
                
                payload = {
                    "model": CHAT_MODEL,
                    "messages": [system_message] + messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                }
                
                response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, stream=True, timeout=30)
                
                if not response.ok:
                    # Fallback to database response if API fails
                    last_message = messages[-1]['content'] if messages else ""
                    fallback_response = get_mango_response_from_db(last_message)
                    
                    # Format as streaming response
                    for char in fallback_response:
                        yield f'data: {{"content": "{char}"}}\n\n'
                        time.sleep(0.01)  # Small delay for streaming effect
                    yield 'data: [DONE]\n\n'
                    return
                
                # Process streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_part = line[6:]  # Remove 'data: ' prefix
                            if data_part == '[DONE]':
                                # Save complete conversation to database
                                if full_response and messages:
                                    user_message = messages[-1]['content']
                                    save_chat_message(session['user_id'], user_message, full_response)
                                yield 'data: [DONE]\n\n'
                                break
                            
                            try:
                                parsed = json.loads(data_part)
                                content = parsed.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    full_response += content
                                    # Escape quotes for JSON
                                    escaped_content = content.replace('"', '\\"').replace('\n', '\\n')
                                    yield f'data: {{"content": "{escaped_content}"}}\n\n'
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                print(f"Streaming error: {e}")
                # Fallback response
                last_message = messages[-1]['content'] if messages else ""
                fallback_response = get_mango_response_from_db(last_message)
                
                for char in fallback_response:
                    escaped_char = char.replace('"', '\\"').replace('\n', '\\n')
                    yield f'data: {{"content": "{escaped_char}"}}\n\n'
                    time.sleep(0.01)
                yield 'data: [DONE]\n\n'
        
        # FIXED: Proper CORS headers for streaming response
        response = Response(
            generate_stream(),
            content_type='text/plain; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': 'http://localhost:5173',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            }
        )
        return response
        
    except Exception as e:
        print(f"Stream chat error: {e}")
        return jsonify({"error": "Failed to process streaming request"}), 500

# ✅ Clear chat history route
@app.route('/api/chat/clear', methods=['POST'])
def clear_chat_history():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM chat_history WHERE user_id = %s", (session['user_id'],))
            affected_rows = cursor.rowcount
            connection.commit()
            connection.close()
            
            return jsonify({
                "message": "Chat history cleared successfully", 
                "deleted_count": affected_rows
            }), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
            
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return jsonify({"error": "Failed to clear chat history"}), 500

# ✅ Get disease information route
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

# ✅ NEW: Knowledge base search endpoint
@app.route('/api/knowledge/search', methods=['GET'])
def search_knowledge():
    """Search mango knowledge base"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        knowledge_items = search_mango_knowledge(query, limit)
        
        return jsonify({
            "query": query,
            "results": knowledge_items,
            "count": len(knowledge_items)
        }), 200
        
    except Exception as e:
        print(f"Knowledge search error: {e}")
        return jsonify({"error": "Search failed"}), 500

# ✅ NEW: Get all knowledge categories
@app.route('/api/knowledge/categories', methods=['GET'])
def get_knowledge_categories():
    """Get all available knowledge categories"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT category, subcategory, COUNT(*) as count 
                FROM mango_knowledge_base 
                GROUP BY category, subcategory 
                ORDER BY category, subcategory
            """)
            
            results = cursor.fetchall()
            categories = {}
            
            for row in results:
                category = row[0]
                subcategory = row[1]
                count = row[2]
                
                if category not in categories:
                    categories[category] = {"subcategories": {}, "total": 0}
                
                if subcategory:
                    categories[category]["subcategories"][subcategory] = count
                
                categories[category]["total"] += count
            
            connection.close()
            return jsonify({"categories": categories}), 200
        else:
            return jsonify({"error": "Database connection failed"}), 500
            
    except Exception as e:
        print(f"Categories error: {e}")
        return jsonify({"error": "Failed to fetch categories"}), 500

# ✅ Health check route with database status
@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint with comprehensive status"""
    try:
        # Check database connection
        connection = get_db_connection()
        db_status = "connected" if connection else "disconnected"
        
        # Check tables
        tables_status = {}
        if connection:
            cursor = connection.cursor()
            required_tables = ['users', 'predictions', 'chat_history', 'mango_knowledge_base']
            
            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                tables_status[table] = "exists" if cursor.fetchone() else "missing"
            
            connection.close()
        
        # Check model status
        model_status = "loaded" if model is not None else "not_loaded"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "tables": tables_status,
            "model": model_status,
            "supported_diseases": DISEASE_CLASSES,
            "api_endpoints": {
                "authentication": ["/api/register", "/api/login", "/api/logout"],
                "prediction": ["/api/predict", "/api/predict/test"],
                "chat": ["/api/chat", "/api/chat/stream", "/api/chat/history"],
                "knowledge": ["/api/knowledge/search", "/api/knowledge/categories"],
                "data": ["/api/history", "/api/diseases"],
                "system": ["/api/health", "/api/model/info"]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ✅ Optional: placeholder image generator route
@app.route('/api/placeholder/<int:width>/<int:height>', methods=['GET'])
def placeholder(width, height):
    img = Image.new('RGB', (width, height), color='gray')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ✅ FIXED: Add OPTIONS handler for CORS preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# ✅ Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

# ✅ Run the app
if __name__ == '__main__':
    print("🥭 Starting Enhanced Mango Disease Management API...")
    print(f"✓ Model Status: {'Loaded' if model else 'Not Loaded'}")
    print(f"✓ Supported Diseases: {', '.join(DISEASE_CLASSES)}")
    print(f"✓ Chat API: OpenRouter {'Available' if OPENROUTER_API_KEY else 'Not Configured'}")
    print("✓ Database-driven Knowledge Base: Enabled")
    print("✓ Enhanced Mango Expertise: All aspects of mango farming")
    print("✓ Server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)