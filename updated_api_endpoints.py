# Updated API endpoints for the new structure
# Enterprise → Organizations → Channels → Voice Agents → Contacts

@app.route('/api/enterprises', methods=['GET'])
@require_auth
def get_enterprises():
    """Get enterprises for the current user"""
    try:
        user_id = g.user_id
        
        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id,role')
        if not user or len(user) == 0:
            return jsonify({'message': 'User not found'}), 404
        
        user_data = user[0]
        enterprise_id = user_data.get('enterprise_id')
        
        if not enterprise_id:
            return jsonify({'enterprises': []}), 200
        
        # Get user's enterprise
        enterprises = supabase_request('GET', f'enterprises?id=eq.{enterprise_id}')
        
        return jsonify({'enterprises': enterprises}), 200
        
    except Exception as e:
        print(f"Get enterprises error: {e}")
        return jsonify({'message': 'Failed to get enterprises'}), 500

@app.route('/api/enterprises/<enterprise_id>/organizations', methods=['GET'])
@require_auth
def get_organizations(enterprise_id):
    """Get organizations for an enterprise"""
    try:
        user_id = g.user_id
        
        # Verify user has access to this enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get organizations for the enterprise
        organizations = supabase_request('GET', f'organizations?enterprise_id=eq.{enterprise_id}&order=created_at.desc')
        
        return jsonify({'organizations': organizations}), 200
        
    except Exception as e:
        print(f"Get organizations error: {e}")
        return jsonify({'message': 'Failed to get organizations'}), 500

@app.route('/api/organizations', methods=['POST'])
@require_auth
def create_organization():
    """Create a new organization"""
    try:
        user_id = g.user_id
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'message': 'Organization name is required'}), 400
        
        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id,role')
        if not user or len(user) == 0:
            return jsonify({'message': 'User not found'}), 404
        
        user_data = user[0]
        enterprise_id = user_data.get('enterprise_id')
        
        if not enterprise_id:
            return jsonify({'message': 'User not associated with an enterprise'}), 400
        
        # Create organization
        org_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'type': data.get('type', 'general'),
            'status': 'active',
            'enterprise_id': enterprise_id
        }
        
        organization = supabase_request('POST', 'organizations', data=org_data)
        
        if organization and len(organization) > 0:
            org_id = organization[0]['id']
            
            # Create default channels for the organization
            channels_data = [
                {
                    'name': 'Inbound Calls',
                    'description': 'Handle incoming customer calls',
                    'status': 'active',
                    'organization_id': org_id
                },
                {
                    'name': 'Outbound Calls', 
                    'description': 'Make calls to customers',
                    'status': 'active',
                    'organization_id': org_id
                },
                {
                    'name': 'WhatsApp Messages',
                    'description': 'Send automated WhatsApp messages',
                    'status': 'active',
                    'organization_id': org_id
                }
            ]
            
            # Create channels
            for channel_data in channels_data:
                supabase_request('POST', 'channels', data=channel_data)
        
        return jsonify({'organization': organization[0] if organization else None}), 201
        
    except Exception as e:
        print(f"Create organization error: {e}")
        return jsonify({'message': 'Failed to create organization'}), 500

@app.route('/api/organizations/<org_id>/channels', methods=['GET'])
@require_auth
def get_channels(org_id):
    """Get channels for an organization"""
    try:
        user_id = g.user_id
        
        # Verify user has access to this organization
        org = supabase_request('GET', f'organizations?id=eq.{org_id}&select=enterprise_id')
        if not org or len(org) == 0:
            return jsonify({'message': 'Organization not found'}), 404
        
        enterprise_id = org[0]['enterprise_id']
        
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get channels for the organization
        channels = supabase_request('GET', f'channels?organization_id=eq.{org_id}&order=name.asc')
        
        return jsonify({'channels': channels}), 200
        
    except Exception as e:
        print(f"Get channels error: {e}")
        return jsonify({'message': 'Failed to get channels'}), 500

@app.route('/api/channels/<channel_id>/voice-agents', methods=['GET'])
@require_auth
def get_voice_agents_by_channel(channel_id):
    """Get voice agents for a channel"""
    try:
        user_id = g.user_id
        
        # Verify user has access to this channel
        channel = supabase_request('GET', f'channels?id=eq.{channel_id}&select=organization_id')
        if not channel or len(channel) == 0:
            return jsonify({'message': 'Channel not found'}), 404
        
        org_id = channel[0]['organization_id']
        
        # Get organization and verify enterprise access
        org = supabase_request('GET', f'organizations?id=eq.{org_id}&select=enterprise_id')
        if not org or len(org) == 0:
            return jsonify({'message': 'Organization not found'}), 404
        
        enterprise_id = org[0]['enterprise_id']
        
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get voice agents for the channel
        voice_agents = supabase_request('GET', f'voice_agents?channel_id=eq.{channel_id}&order=created_at.desc')
        
        return jsonify({'voice_agents': voice_agents}), 200
        
    except Exception as e:
        print(f"Get voice agents error: {e}")
        return jsonify({'message': 'Failed to get voice agents'}), 500

@app.route('/api/voice-agents', methods=['POST'])
@require_auth
def create_voice_agent():
    """Create a new voice agent"""
    try:
        user_id = g.user_id
        data = request.json
        
        # Validate required fields
        required_fields = ['title', 'description', 'url', 'channel_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        channel_id = data['channel_id']
        
        # Verify user has access to this channel
        channel = supabase_request('GET', f'channels?id=eq.{channel_id}&select=organization_id')
        if not channel or len(channel) == 0:
            return jsonify({'message': 'Channel not found'}), 404
        
        org_id = channel[0]['organization_id']
        
        # Get organization and verify enterprise access
        org = supabase_request('GET', f'organizations?id=eq.{org_id}&select=enterprise_id')
        if not org or len(org) == 0:
            return jsonify({'message': 'Organization not found'}), 404
        
        enterprise_id = org[0]['enterprise_id']
        
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Create voice agent
        agent_data = {
            'title': data['title'],
            'description': data['description'],
            'url': data['url'],
            'status': data.get('status', 'active'),
            'channel_id': channel_id,
            'organization_id': org_id,
            'enterprise_id': enterprise_id
        }
        
        voice_agent = supabase_request('POST', 'voice_agents', data=agent_data)
        
        return jsonify({'voice_agent': voice_agent[0] if voice_agent else None}), 201
        
    except Exception as e:
        print(f"Create voice agent error: {e}")
        return jsonify({'message': 'Failed to create voice agent'}), 500

@app.route('/api/voice-agents/<agent_id>/contacts', methods=['GET'])
@require_auth
def get_agent_contacts(agent_id):
    """Get contacts for a voice agent"""
    try:
        user_id = g.user_id
        
        # Verify user has access to this agent
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=enterprise_id')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        enterprise_id = agent[0]['enterprise_id']
        
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get contacts for the agent
        contacts = supabase_request('GET', f'contacts?voice_agent_id=eq.{agent_id}&order=created_at.desc')
        
        return jsonify({'contacts': contacts}), 200
        
    except Exception as e:
        print(f"Get agent contacts error: {e}")
        return jsonify({'message': 'Failed to get contacts'}), 500

@app.route('/api/voice-agents/<agent_id>/contacts', methods=['POST'])
@require_auth
def create_contact(agent_id):
    """Create a new contact for a voice agent"""
    try:
        user_id = g.user_id
        data = request.json
        
        # Validate required fields
        if not data.get('name') or not data.get('phone'):
            return jsonify({'message': 'Name and phone are required'}), 400
        
        # Verify user has access to this agent
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=enterprise_id,organization_id,channel_id')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        agent_data = agent[0]
        enterprise_id = agent_data['enterprise_id']
        organization_id = agent_data['organization_id']
        channel_id = agent_data['channel_id']
        
        user = supabase_request('GET', f'users?id=eq.{user_id}&enterprise_id=eq.{enterprise_id}')
        if not user or len(user) == 0:
            return jsonify({'message': 'Access denied'}), 403
        
        # Check for duplicate phone number for this agent
        existing_contact = supabase_request('GET', f'contacts?voice_agent_id=eq.{agent_id}&phone=eq.{data["phone"]}')
        if existing_contact and len(existing_contact) > 0:
            return jsonify({'message': 'A contact with this phone number already exists for this agent'}), 400
        
        # Create contact
        contact_data = {
            'name': data['name'],
            'phone': data['phone'],
            'status': data.get('status', 'active'),
            'voice_agent_id': agent_id,
            'channel_id': channel_id,
            'organization_id': organization_id,
            'enterprise_id': enterprise_id
        }
        
        contact = supabase_request('POST', 'contacts', data=contact_data)
        
        return jsonify({'contact': contact[0] if contact else None}), 201
        
    except Exception as e:
        print(f"Create contact error: {e}")
        return jsonify({'message': 'Failed to create contact'}), 500
