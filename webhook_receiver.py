#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json

"""
Example CURL Commands (note the escape characters that are required on Windows)

Windows:
curl -X POST http://localhost:5000/webhook -H "Content-Type: application/json" -H "Authorization: Bearer my-secret-token" -d "{\"key\": \"value\"}"

Bash:
curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer my-secret-token" \
     -d '{"key": "value"}'
"""

app = Flask(__name__)

# Configuration
PORT = 5000  # Default port, can be changed via command-line argument
TOKEN_FILE = "token.txt"  # File containing the Bearer Token

def load_token():
    """
    Load the Bearer Token from the token file.
    """
    try:
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Token file '{TOKEN_FILE}' not found.")
        exit(1)

def authenticate(request):
    """
    Validate the Bearer Token in the request's Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False

    # Check if the header starts with "Bearer "
    if not auth_header.startswith("Bearer "):
        return False

    # Extract the token from the header
    token = auth_header.split(" ")[1]
    return token == load_token()

@app.route('/webhook', methods=['POST'])
def webhook():
    # Authenticate the request
    if not authenticate(request):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Check if data is valid JSON
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Pretty-print the JSON data
        formatted_data = json.dumps(data, indent=4)
        print("Received JSON payload:")
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
    args = parser.parse_args()

    # Run the Flask app
    print(f"Starting webhook receiver on port {args.port}...")
    app.run(host='0.0.0.0', port=args.port)