from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import io

# ✅ Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# ✅ Enable CORS for frontend (adjust origin if needed)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

# ✅ Initialize Bcrypt
bcrypt = Bcrypt(app)

# ✅ Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'manglo_db',
    'user': 'root',
    'password': ''
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

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
