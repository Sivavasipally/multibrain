#!/usr/bin/env python3
"""
Simple CORS test server
"""
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Simple CORS setup - allow all origins for localhost
CORS(app, origins="*", supports_credentials=False)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'CORS test server'}), 200

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Handle preflight
        return jsonify({'message': 'preflight ok'}), 200
    return jsonify({'message': 'login endpoint', 'origin': request.headers.get('Origin')}), 200

if __name__ == '__main__':
    print("Starting simple CORS test server...")
    app.run(debug=False, host='0.0.0.0', port=5001)