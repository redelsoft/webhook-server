#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example bearer token:
curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer my-secret-token-1" \
     -d '{"key": "value"}'

Example basic auth:
curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)" \
     -d '{"key": "value"}'

"""

from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import json
from base64 import b64decode
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__, static_folder="templates", static_url_path="")
CORS(app)  # Enable CORS for frontend communication


# Configuration
PORT = 5000  # Default port, can be changed via command-line argument
TOKEN_FILE = "token.txt"  # File containing the Bearer Tokens (one per line)
CREDENTIALS_FILE = "credentials.txt"  # File containing username:password pairs (one per line)

# Database setup
def init_db():
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                data TEXT
            )
        """)
        conn.commit()

init_db()

def load_tokens():
    """
    Load all Bearer Tokens from the token file.
    Returns a list of tokens.
    """
    try:
        with open(TOKEN_FILE, "r") as file:
            # Read all lines, strip whitespace, and ignore empty lines
            tokens = [line.strip() for line in file if line.strip()]
            return tokens
    except FileNotFoundError:
        print(f"Error: Token file '{TOKEN_FILE}' not found.")
        exit(1)


def load_credentials():
    """
    Load all username:password pairs from the credentials file.
    Returns a dictionary of {username: password}.
    """
    try:
        with open(CREDENTIALS_FILE, "r") as file:
            # Read all lines, strip whitespace, and ignore empty lines
            credentials = {}
            for line in file:
                if line.strip():
                    username, password = line.strip().split(":", 1)
                    credentials[username] = password
            return credentials
    except FileNotFoundError:
        print(f"Error: Credentials file '{CREDENTIALS_FILE}' not found.")
        exit(1)


def authenticate_bearer(_request):
    """
    Validate the Bearer Token in the request's Authorization header.
    Returns True if the token is valid, False otherwise.
    """
    auth_header = _request.headers.get("Authorization")
    if not auth_header:
        return False

    # Check if the header starts with "Bearer "
    if not auth_header.startswith("Bearer "):
        return False

    # Extract the token from the header
    token = auth_header.split(" ")[1]

    # Check if the token matches any of the valid tokens
    return token in load_tokens()


def authenticate_basic(_request):
    """
    Validate the username and password in the request's Authorization header (Basic Auth).
    Returns True if the credentials are valid, False otherwise.
    """
    auth_header = _request.headers.get("Authorization")
    if not auth_header:
        return False

    # Check if the header starts with "Basic "
    if not auth_header.startswith("Basic "):
        return False

    # Extract and decode the base64-encoded credentials
    encoded_credentials = auth_header.split(" ")[1]
    try:
        decoded_credentials = b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return False

    # Check if the username and password match any valid pair
    credentials = load_credentials()
    return credentials.get(username) == password


@app.route('/')
def index():
    return send_from_directory("templates", "index.html")


@app.route('/messages', methods=['GET'])
def get_messages():
    search_query = request.args.get("search", "").lower()
    with sqlite3.connect("messages.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, data FROM messages ORDER BY id DESC LIMIT 100")
        messages = [{"timestamp": row[0], "data": row[1]} for row in cursor.fetchall()]
    
    if search_query:
        messages = [msg for msg in messages if search_query in msg["data"].lower()]
    
    return jsonify(messages[::-1])  # Reverse to show oldest first


@app.route('/webhook', methods=['POST'])
def webhook():
    # Authenticate the request using either Bearer Token or Basic Auth
    if not (authenticate_bearer(request) or authenticate_basic(request)):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Check if data is valid JSON
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect("messages.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (timestamp, data) VALUES (?, ?)", (timestamp, json.dumps(data)))
            conn.commit()

        # Pretty-print the JSON data and headers
        formatted_data = json.dumps(data, indent=4)
        print("Received HTTP Headers:")
        for header, value in request.headers.items():
            print(f"{header}: {value}")
        print("\nReceived JSON payload:")
        print(formatted_data)

        # Return a success response
        return jsonify({"status": "success", "message": "Webhook received"}), 200

    except Exception as e:
        # Handle any errors
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Webhook Receiver")
    parser.add_argument('--port', type=int, default=PORT, help='Port to listen on (default: 5000)')
    parser.add_argument('--cert', help='Path to SSL certificate file (for HTTPS)')
    parser.add_argument('--key', help='Path to SSL private key file (for HTTPS)')
    args = parser.parse_args()

    # Configure SSL if certificate and key are provided
    ssl_context = None
    if args.cert and args.key:
        ssl_context = (args.cert, args.key)

    # Run the Flask app
    print(f"Starting webhook receiver on port {args.port}...")
    app.run(host='0.0.0.0', port=args.port, ssl_context=ssl_context)