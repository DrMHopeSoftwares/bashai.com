#!/usr/bin/env python3
"""
Simplified Flask app for Railway deployment debugging
"""

from flask import Flask, jsonify, send_from_directory, request
import os
import time

# Create Flask app with minimal config
app = Flask(__name__, static_folder='static', static_url_path='/')

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    """Landing page"""
    try:
        return send_from_directory(app.static_folder, 'landing.html')
    except Exception as e:
        return jsonify({'error': f'Landing page error: {str(e)}'})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'app': 'bhashai.com',
        'static_folder': app.static_folder,
        'port': os.environ.get('PORT', 'unknown')
    })

@app.route('/simple-admin.html')
def simple_admin():
    """Simple admin page"""
    try:
        return send_from_directory(app.static_folder, 'simple-admin.html')
    except Exception as e:
        return jsonify({'error': f'Admin page error: {str(e)}'})

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    try:
        return send_from_directory(app.static_folder, 'admin-dashboard.html')
    except Exception as e:
        return jsonify({'error': f'Dashboard error: {str(e)}'})

@app.route('/dashboard.html')
@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard"""
    try:
        return send_from_directory(app.static_folder, 'dashboard.html')
    except Exception as e:
        return jsonify({'error': f'Dashboard error: {str(e)}'})

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'Railway deployment working!',
        'timestamp': '2025-07-13 10:03:14',
        'static_files_exist': {
            'landing.html': os.path.exists(os.path.join(app.static_folder, 'landing.html')),
            'simple-admin.html': os.path.exists(os.path.join(app.static_folder, 'simple-admin.html')),
            'admin-dashboard.html': os.path.exists(os.path.join(app.static_folder, 'admin-dashboard.html'))
        }
    })

@app.route('/signup')
def signup_page():
    """Signup page"""
    try:
        return send_from_directory(app.static_folder, 'signup.html')
    except Exception as e:
        return jsonify({'error': f'Signup page error: {str(e)}'})

@app.route('/book-demo.html')
@app.route('/book-demo')
def demo_page():
    """Demo booking page"""
    try:
        return send_from_directory(app.static_folder, 'book-demo.html')
    except Exception as e:
        return jsonify({'error': f'Demo page error: {str(e)}'})

@app.route('/agent-setup.html')
@app.route('/agent-setup')
def agent_setup():
    """Agent setup page"""
    try:
        return send_from_directory(app.static_folder, 'agent-setup.html')
    except Exception as e:
        return jsonify({'error': f'Agent setup error: {str(e)}'})

@app.route('/contact-management.html')
@app.route('/contact-management')
def contact_management():
    """Contact management page"""
    try:
        return send_from_directory(app.static_folder, 'contact-management.html')
    except Exception as e:
        return jsonify({'error': f'Contact management error: {str(e)}'})

@app.route('/organization-detail.html')
@app.route('/organization-detail')
def organization_detail():
    """Organization detail page"""
    try:
        return send_from_directory(app.static_folder, 'organization-detail.html')
    except Exception as e:
        return jsonify({'error': f'Organization detail error: {str(e)}'})

@app.route('/channel-detail.html')
@app.route('/channel-detail')
def channel_detail():
    """Channel detail page"""
    try:
        return send_from_directory(app.static_folder, 'channel-detail.html')
    except Exception as e:
        return jsonify({'error': f'Channel detail error: {str(e)}'})

@app.route('/phone-numbers.html')
@app.route('/phone-numbers')
def phone_numbers():
    """Phone numbers management page"""
    try:
        return send_from_directory(app.static_folder, 'phone-numbers.html')
    except Exception as e:
        return jsonify({'error': f'Phone numbers error: {str(e)}'})

@app.route('/create-agent.html')
@app.route('/create-agent')
def create_agent():
    """Agent creation wizard page"""
    try:
        return send_from_directory(app.static_folder, 'create-agent.html')
    except Exception as e:
        return jsonify({'error': f'Create agent error: {str(e)}'})

@app.route('/api/public/signup', methods=['POST', 'OPTIONS'])
def public_signup():
    """Public signup endpoint - no auth required"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Create enterprise and user
        enterprise_id = 'ent_' + str(int(time.time()))
        
        return jsonify({
            'success': True,
            'message': 'Enterprise created successfully!',
            'enterprise': {
                'id': enterprise_id,
                'name': data.get('name'),
                'owner_name': data.get('owner_name'),
                'contact_email': data.get('contact_email'),
                'contact_phone': data.get('contact_phone'),
                'type': data.get('type'),
                'status': 'trial',
                'trial_expires_at': '2025-08-13T00:00:00Z',
                'created_at': '2025-07-13T11:15:00Z'
            },
            'user': {
                'email': data.get('contact_email'),
                'role': 'admin',
                'enterprise_id': enterprise_id
            },
            'redirect_url': '/dashboard.html'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/public/demo', methods=['POST', 'OPTIONS'])
def demo_booking():
    """Demo booking endpoint - no auth required"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Create demo booking record
        demo_id = 'demo_' + str(int(time.time()))
        
        return jsonify({
            'success': True,
            'message': 'Demo scheduled successfully!',
            'demo': {
                'id': demo_id,
                'firstName': data.get('firstName'),
                'lastName': data.get('lastName'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'organization': data.get('organization'),
                'role': data.get('role'),
                'useCase': data.get('useCase'),
                'patientVolume': data.get('patientVolume'),
                'timePreference': data.get('timePreference'),
                'comments': data.get('comments'),
                'status': 'scheduled',
                'created_at': '2025-07-13T11:30:00Z'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/enterprises', methods=['POST', 'OPTIONS'])
def create_enterprise():
    """Simple enterprise creation endpoint"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        return '', 200
    
    try:
        data = request.get_json()
        
        # Mock successful creation
        return jsonify({
            'success': True,
            'message': f"Enterprise '{data.get('name')}' created successfully!",
            'enterprise': {
                'id': 'ent_' + str(int(time.time())),
                'name': data.get('name'),
                'contact_email': data.get('contact_email'),
                'status': data.get('status', 'trial'),
                'created_at': '2025-07-13T11:04:22Z'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting simplified bhashai.com on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)