#!/usr/bin/env python3
"""
Simple Flask app to test Railway deployment
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'bhashai.com is running on Railway!',
        'port': os.environ.get('PORT', 'unknown'),
        'env': 'production'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)