#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example bearer token:
curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer my-secret-token-1" \
     -d '{"key": "value"}'

curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)" \
     -d '{"key": "value"}'

"""

from flask import Flask, request, jsonify
import json
from base64 import b64decode

app = Flask(__name__)

# Configuration
PORT = 5000  # Default port, can be changed via command-line argument
TOKEN_FILE = "token.txt"  # File containing the Bearer Tokens (one per line)
CREDENTIALS_FILE = "credentials.txt"  # File containing username:password pairs (one per line)

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

@app.route('/webhook', methods=['POST'])
def webhook():
    # Authenticate the request using either Bearer Token or Basic Auth
    if not (authenticate_bearer(request) or authenticate_basic(request)):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Check if data is valid JSON
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400

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
    args = parser.parse_args()

    # Run the Flask app
    print(f"Starting webhook receiver on port {args.port}...")
    app.run(host='0.0.0.0', port=args.port)