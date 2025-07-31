from flask import Flask, request, jsonify, session, send_file
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

# ✅ Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# ✅ Enable CORS for frontend (adjust origin if needed)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

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

def get_chatbot_response(message):
    """
    Simple chatbot responses - Updated with correct disease names
    """
    message = message.lower()
    
    if 'alternaria' in message:
        return "Alternaria is a fungal disease causing leaf spots and fruit rot. Use copper-based fungicides and maintain proper sanitation."
    elif 'anthracnose' in message:
        return "Anthracnose is a fungal disease causing dark spots on fruits. Apply copper-based fungicides and maintain proper sanitation."
    elif 'black mould' in message or 'black mold' in message:
        return "Black Mould Rot affects stored fruits. Improve storage conditions with proper ventilation and handle fruits carefully."
    elif 'stem rot' in message or 'stem and rot' in message:
        return "Stem and Rot disease affects the plant structure. Apply systemic fungicides and improve drainage conditions."
    elif 'healthy' in message:
        return "Great! Your mango appears healthy. Continue regular monitoring and follow good agricultural practices."
    elif 'treatment' in message:
        return "Treatment depends on the specific disease. Upload an image for accurate diagnosis and recommendations."
    elif 'hello' in message or 'hi' in message:
        return "Hello! I'm here to help you with mango disease diagnosis. Upload an image or ask me questions about mango diseases."
    elif 'diseases' in message:
        return f"I can detect these mango diseases: {', '.join(DISEASE_CLASSES)}. Upload an image for analysis!"
    else:
        return "I can help you identify mango diseases and provide treatment recommendations. Upload an image for analysis or ask specific questions about mango diseases."

# ✅ Root route
@app.route("/")
def home():
    return "API is running"

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

# ✅ Chat route
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

# ✅ Optional: placeholder image generator route
@app.route('/api/placeholder/<int:width>/<int:height>', methods=['GET'])
def placeholder(width, height):
    img = Image.new('RGB', (width, height), color='gray')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)