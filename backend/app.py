from flask import Flask, request, jsonify, session, send_file, Response, current_app, g
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from datetime import datetime
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
from dotenv import load_dotenv

# ✅ FIXED: Set TensorFlow environment variables BEFORE importing TensorFlow
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress all TensorFlow warnings
tf.get_logger().setLevel('ERROR')  # Only show errors

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
    else:
        print(f"Warning: Model file not found at {model_path}")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None

# ✅ Updated Chatbot Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
CHAT_MODEL = os.getenv("CHAT_MODEL")

# ✅ FIXED: Increase response length for comprehensive answers
MAX_RESPONSE_TOKENS = 2500  # Allow longer, more detailed responses

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
        return """🥭 **Mango Farming Comprehensive Guide**

I'm here to provide detailed assistance with all aspects of mango cultivation. Here's what I can help you with:

**🌿 Disease Management:**
• Identification of diseases like Anthracnose, Alternaria, Black Mould Rot, Stem Rot
• Detailed treatment protocols with specific fungicides and dosages
• Organic and chemical control methods
• Prevention strategies and integrated disease management

**🌱 Cultivation Practices:**
• Site selection and soil preparation requirements
• Planting techniques and spacing recommendations
• Fertilization programs and nutrient management
• Irrigation scheduling and water management
• Pruning techniques for optimal growth and production

**🐛 Pest Control:**
• Comprehensive pest identification (fruit flies, scale insects, mealybugs)
• Integrated pest management strategies
• Biological control methods
• Chemical control with proper timing and dosages

**🥭 Varieties and Selection:**
• Commercial variety recommendations for different climates
• Grafting and propagation techniques
• Climate adaptation considerations

**📦 Harvest and Post-Harvest:**
• Proper harvesting techniques and timing
• Storage methods and shelf-life extension
• Packaging and transportation guidelines
• Value addition and processing options

**💡 Best Practices:**
• Organic farming approaches
• Sustainable orchard management
• Market preparation and quality standards
• Export requirements and procedures

Please ask me specific questions about any of these topics, and I'll provide detailed, practical guidance with step-by-step instructions!"""
    
    # Generate comprehensive response
    response = f"🥭 **{knowledge_items[0]['category']} - Comprehensive Guide**\n\n"
    
    for i, item in enumerate(knowledge_items[:3]):  # Show up to 3 detailed items
        if item['subcategory']:
            response += f"**{i+1}. {item['subcategory']} - {item['topic']}**\n\n"
        else:
            response += f"**{i+1}. {item['topic']}**\n\n"
        
        response += f"{item['content']}\n\n"
        
        if i < len(knowledge_items) - 1:
            response += "---\n\n"
    
    # Add actionable next steps
    response += "\n**💡 Next Steps & Related Information:**\n"
    response += "• Ask for specific dosages and application methods\n"
    response += "• Request seasonal management calendars\n"
    response += "• Inquire about organic alternatives\n"
    response += "• Get information on integrated management approaches\n\n"
    
    # Add related topics
    categories = list(set([item['category'] for item in knowledge_items]))
    if len(categories) > 1:
        response += f"**🔍 Related Topics Available:**\n{', '.join(categories[1:])}\n\n"
    
    response += "Feel free to ask follow-up questions for more specific guidance!"
    
    return response

def get_openrouter_response(messages):
    """Get response from OpenRouter API with token limit"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Mango Disease Management Assistant",
            "Content-Type": "application/json",
        }
        
        system_message = {
            "role": "system",
            "content": """You are a mango farming expert. Provide concise, practical advice on:
• Disease identification and treatment
• Pest management 
• Cultivation practices
• Harvest and storage

Keep responses under 300 words. Be specific and actionable."""
        }
        
        payload = {
            "model": CHAT_MODEL,
            "messages": [system_message] + messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": MAX_RESPONSE_TOKENS,
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        else:
            print(f"OpenRouter API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error with OpenRouter API: {e}")
        return None

def get_chatbot_response(user_message, conversation_history=[]):
    """Get chatbot response with fallback"""
    try:
        messages = conversation_history[-6:] + [{"role": "user", "content": user_message}]
        
        api_response = get_openrouter_response(messages)
        if api_response:
            return api_response
        
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

# ✅ NEW: Add placeholder image route
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

# ✅ Routes
@app.route("/")
def home():
    return "Mango Disease Management API is running"

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
                
                print(f"✓ User logged in: {user[1]} (ID: {user[0]})")
                
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
    """Streaming chat endpoint with context fix"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "Messages are required"}), 400
        
        current_user_id = session['user_id']
        
        def generate_stream():
            try:
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
                
                response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, stream=True, timeout=30)
                
                if not response.ok:
                    last_message = messages[-1]['content'] if messages else ""
                    fallback_response = get_mango_response_from_db(last_message)
                    
                    for char in fallback_response:
                        yield f'data: {{"content": "{char}"}}\n\n'
                        time.sleep(0.01)
                    yield 'data: [DONE]\n\n'
                    return
                
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_part = line[6:]
                            if data_part == '[DONE]':
                                if full_response and messages:
                                    user_message = messages[-1]['content']
                                    try:
                                        connection = get_db_connection()
                                        if connection:
                                            cursor = connection.cursor()
                                            cursor.execute(
                                                """INSERT INTO chat_history (user_id, message, response, created_at) 
                                                   VALUES (%s, %s, %s, %s)""",
                                                (current_user_id, user_message, full_response, datetime.now())
                                            )
                                            connection.commit()
                                            connection.close()
                                    except Exception as save_error:
                                        print(f"Save error: {save_error}")
                                        
                                yield 'data: [DONE]\n\n'
                                break
                            
                            try:
                                parsed = json.loads(data_part)
                                content = parsed.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    full_response += content
                                    escaped_content = content.replace('"', '\\"').replace('\n', '\\n')
                                    yield f'data: {{"content": "{escaped_content}"}}\n\n'
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                print(f"Streaming error: {e}")
                last_message = messages[-1]['content'] if messages else ""
                fallback_response = get_mango_response_from_db(last_message)
                
                for char in fallback_response:
                    escaped_char = char.replace('"', '\\"').replace('\n', '\\n')
                    yield f'data: {{"content": "{escaped_char}"}}\n\n'
                    time.sleep(0.01)
                yield 'data: [DONE]\n\n'
        
        response = Response(
            generate_stream(),
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
        print(f"Stream chat error: {e}")
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
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "model": model_status,
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
    print("🥭 Starting Enhanced Mango Disease Management API...")
    print(f"✓ Model Status: {'Loaded' if model else 'Not Loaded'}")
    print(f"✓ Supported Diseases: {', '.join(DISEASE_CLASSES)}")
    print(f"✓ Chat API: OpenRouter {'Available' if OPENROUTER_API_KEY else 'Not Configured'}")
    print(f"✓ Max Response Tokens: {MAX_RESPONSE_TOKENS}")
    print("✓ Server starting on http://localhost:5000")
    print("✓ Placeholder images available at /api/placeholder/<width>/<height>")
    app.run(debug=True, host='0.0.0.0', port=5000)