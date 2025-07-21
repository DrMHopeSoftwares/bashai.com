#!/usr/bin/env python3
"""
Simple test server to verify Flask works
"""

from flask import Flask
import os

app = Flask(__name__)
app.secret_key = 'test-key'

@app.route('/')
def home():
    return '''
    <h1>🚀 Simple Server Running!</h1>
    <p>Flask is working correctly.</p>
    <p>Your main server fixes are ready to deploy.</p>
    '''

@app.route('/test')
def test():
    return {'status': 'working', 'message': 'Server is functional'}

if __name__ == '__main__':
    print('🚀 Starting simple test server on port 5005...')
    app.run(host='0.0.0.0', port=5005, debug=True)
