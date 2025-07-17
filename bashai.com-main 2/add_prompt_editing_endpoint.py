#!/usr/bin/env python3
"""
Add prompt editing endpoints to main.py for RelevanceAI agents
"""

prompt_editing_routes = '''

# RelevanceAI Agent Prompt Management Endpoints
@app.route('/api/relevance-ai/agents/<agent_id>/prompt', methods=['GET'])
@login_required
@require_enterprise_context
def get_relevance_ai_agent_prompt(agent_id):
    """Get the current system prompt for a RelevanceAI agent"""
    try:
        enterprise_id = g.enterprise_id
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Get current prompt from RelevanceAI
        from relevance_ai_integration_fixed import RelevanceAIProvider
        provider = RelevanceAIProvider()
        
        try:
            # Get agent details from RelevanceAI
            agent_details = provider.get_agent(agent_id)
            current_prompt = agent_details.get('system_prompt', '')
            
            return jsonify({
                'agent_id': agent_id,
                'agent_name': agent_details.get('name', 'Unknown'),
                'system_prompt': current_prompt,
                'prompt_length': len(current_prompt),
                'last_updated': agent_details.get('updated_at', 'Unknown')
            }), 200
            
        except Exception as e:
            return jsonify({'message': f'Failed to retrieve prompt: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Get RelevanceAI prompt error: {e}")
        return jsonify({'message': 'Failed to get agent prompt'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/prompt', methods=['PUT'])
@login_required
@require_enterprise_context
def update_relevance_ai_agent_prompt(agent_id):
    """Update the system prompt for a RelevanceAI agent"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        new_prompt = data.get('system_prompt', '').strip()
        
        if not new_prompt:
            return jsonify({'message': 'System prompt is required'}), 400
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Update prompt in RelevanceAI
        from relevance_ai_integration_fixed import RelevanceAIProvider
        provider = RelevanceAIProvider()
        
        try:
            # Update the agent prompt
            success = provider.update_agent_prompt(agent_id, new_prompt)
            
            if success:
                # Update last modified in our database
                update_data = {
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'provider_config': {
                        **voice_agent[0].get('provider_config', {}),
                        'last_prompt_update': datetime.now(timezone.utc).isoformat(),
                        'prompt_length': len(new_prompt)
                    }
                }
                
                supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data=update_data)
                
                return jsonify({
                    'message': 'Agent prompt updated successfully',
                    'agent_id': agent_id,
                    'prompt_length': len(new_prompt),
                    'updated_at': update_data['updated_at']
                }), 200
            else:
                return jsonify({'message': 'Failed to update prompt in RelevanceAI'}), 500
                
        except Exception as e:
            return jsonify({'message': f'Failed to update prompt: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Update RelevanceAI prompt error: {e}")
        return jsonify({'message': 'Failed to update agent prompt'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/test-prompt', methods=['POST'])
@login_required  
@require_enterprise_context
def test_relevance_ai_agent_prompt(agent_id):
    """Test a RelevanceAI agent with a sample message"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        test_message = data.get('message', 'Hello, I need to book an appointment with Dr. Murali')
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Test the agent
        import requests
        import os
        
        # Use our working API format
        api_key = os.getenv('RELEVANCE_AI_API_KEY')
        region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c') 
        project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
        
        headers = {
            "Authorization": f"{project_id}:{api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "agent_id": agent_id,
            "message": {
                "role": "user",
                "content": test_message
            }
        }
        
        response = requests.post(
            f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger",
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'status': 'test_initiated',
                'conversation_id': result.get('conversation_id'),
                'job_id': result.get('job_info', {}).get('job_id'),
                'test_message': test_message,
                'agent_id': agent_id
            }), 200
        else:
            return jsonify({
                'message': f'Test failed with status {response.status_code}',
                'error': response.text
            }), 500
            
    except Exception as e:
        print(f"Test RelevanceAI agent error: {e}")
        return jsonify({'message': 'Failed to test agent'}), 500
'''

# Also create a simple HTML interface for prompt editing
html_interface = '''
<!DOCTYPE html>
<html>
<head>
    <title>Anohra Prompt Editor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .prompt-editor { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
        textarea { width: 100%; height: 400px; font-family: monospace; }
        button { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .primary { background: #007bff; color: white; }
        .success { background: #28a745; color: white; }
        .danger { background: #dc3545; color: white; }
        .info { background: #17a2b8; color: white; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Anohra Prompt Editor</h1>
        <p>Edit Anohra's system prompt for Dr. Murali's Orthopaedic Clinic</p>
        
        <div class="prompt-editor">
            <h3>Current System Prompt</h3>
            <div id="status" class="status" style="display:none;"></div>
            
            <textarea id="promptTextarea" placeholder="Loading current prompt..."></textarea>
            
            <div style="margin-top: 10px;">
                <button class="primary" onclick="loadCurrentPrompt()">🔄 Reload Current Prompt</button>
                <button class="success" onclick="updatePrompt()">💾 Save Updated Prompt</button>
                <button class="info" onclick="testPrompt()">📞 Test Prompt</button>
                <button class="danger" onclick="resetPrompt()">↺ Reset to Default</button>
            </div>
            
            <div style="margin-top: 15px;">
                <p><strong>Prompt Length:</strong> <span id="promptLength">0</span> characters</p>
                <p><strong>Agent ID:</strong> 7a4cfa99-6a96-4a48-941f-d5865e0ba577</p>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4>📋 Quick Templates:</h4>
            <button onclick="addTemplate('hindi')">Add Hindi Fluency</button>
            <button onclick="addTemplate('emergency')">Add Emergency Handling</button>
            <button onclick="addTemplate('scheduling')">Add Appointment Rules</button>
            <button onclick="addTemplate('closing')">Add Professional Closing</button>
        </div>
    </div>

    <script>
        const ANOHRA_ID = '7a4cfa99-6a96-4a48-941f-d5865e0ba577';
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
            setTimeout(() => status.style.display = 'none', 5000);
        }
        
        function updatePromptLength() {
            const textarea = document.getElementById('promptTextarea');
            document.getElementById('promptLength').textContent = textarea.value.length;
        }
        
        function loadCurrentPrompt() {
            showStatus('Loading current prompt...', 'info');
            
            fetch(`/api/relevance-ai/agents/${ANOHRA_ID}/prompt`)
                .then(response => response.json())
                .then(data => {
                    if (data.system_prompt) {
                        document.getElementById('promptTextarea').value = data.system_prompt;
                        updatePromptLength();
                        showStatus('Prompt loaded successfully!', 'success');
                    } else {
                        showStatus('Failed to load prompt', 'danger');
                    }
                })
                .catch(error => {
                    showStatus('Error loading prompt: ' + error.message, 'danger');
                });
        }
        
        function updatePrompt() {
            const newPrompt = document.getElementById('promptTextarea').value;
            
            if (!newPrompt.trim()) {
                showStatus('Prompt cannot be empty', 'danger');
                return;
            }
            
            showStatus('Updating prompt...', 'info');
            
            fetch(`/api/relevance-ai/agents/${ANOHRA_ID}/prompt`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: newPrompt })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message.includes('successfully')) {
                        showStatus('Prompt updated successfully!', 'success');
                    } else {
                        showStatus('Failed to update prompt', 'danger');
                    }
                })
                .catch(error => {
                    showStatus('Error updating prompt: ' + error.message, 'danger');
                });
        }
        
        function testPrompt() {
            showStatus('Testing prompt with sample message...', 'info');
            
            fetch(`/api/relevance-ai/agents/${ANOHRA_ID}/test-prompt`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'Hello, I need to book an appointment with Dr. Murali for knee pain' })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'test_initiated') {
                        showStatus(`Test initiated! Conversation ID: ${data.conversation_id}`, 'success');
                    } else {
                        showStatus('Test failed: ' + data.message, 'danger');
                    }
                })
                .catch(error => {
                    showStatus('Error testing prompt: ' + error.message, 'danger');
                });
        }
        
        function addTemplate(type) {
            const textarea = document.getElementById('promptTextarea');
            const templates = {
                hindi: '\\n\\n• Always respond in Hindi when the caller speaks Hindi\\n• Use professional medical Hindi terminology\\n• Be warm and empathetic in Hindi conversations',
                emergency: '\\n\\n• For emergency cases, immediately escalate to Dr. Murali\\n• Ask for emergency contact details\\n• Provide calm, reassuring guidance while arranging immediate care',
                scheduling: '\\n\\n• Check Dr. Murali\\'s availability before confirming appointments\\n• Always confirm date, time, and patient details\\n• Send appointment confirmation via SMS/email',
                closing: '\\n\\n• End every call with: \\"Thank you for calling Dr. Murali\\'s clinic\\"\\n• Offer assistance for any follow-up questions\\n• Mention clinic hours and emergency contact if needed'
            };
            
            if (templates[type]) {
                textarea.value += templates[type];
                updatePromptLength();
                showStatus(`Added ${type} template`, 'success');
            }
        }
        
        // Initialize
        document.getElementById('promptTextarea').addEventListener('input', updatePromptLength);
        loadCurrentPrompt();
    </script>
</body>
</html>
'''

print("📝 RelevanceAI Prompt Editing Components Created!")
print("=" * 50)
print("✅ API Endpoints:")
print("   GET  /api/relevance-ai/agents/<agent_id>/prompt")
print("   PUT  /api/relevance-ai/agents/<agent_id>/prompt") 
print("   POST /api/relevance-ai/agents/<agent_id>/test-prompt")
print()
print("✅ HTML Interface ready for integration")
print()
print("🔧 To add to your BhashAI project:")
print("1. Add the routes to main.py")
print("2. Create the HTML file as static/anohra-prompt-editor.html")
print("3. Add prompt editing to your enhanced UI")

# Save the HTML interface
with open('/Users/murali/bhashai.com 15th Jul/bashai.com/static/anohra-prompt-editor.html', 'w') as f:
    f.write(html_interface)

print("✅ HTML interface saved to static/anohra-prompt-editor.html")