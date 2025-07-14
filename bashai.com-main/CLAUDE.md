# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BhashAI SaaS Platform - A multi-tenant SaaS platform for managing organizations and AI voice agents with native Hindi/Hinglish support. Built with Flask backend and Supabase database.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Supabase credentials (Clerk removed)

# Test database connection
python test_connection.py

# Test local authentication (Clerk removed)
python -c "from auth import auth_manager; print('Auth system ready')"
```

### Running the Application
```bash
# Development server
python main.py  # Runs on port 8000

# Production server
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Testing
```bash
# No formal test suite - use individual test scripts:
python test_connection.py      # Test Supabase connection
python -c "from auth_routes import auth_bp; print('Local auth ready')"  # Test local auth
python test_contact_tables.py   # Test database tables
python test_google_oauth.py     # Test OAuth flow
```

## Architecture and Structure

### Monolithic Flask Application
- Single `main.py` file containing all routes and business logic
- Direct Supabase API calls via requests library (no ORM)
- Local SQLite authentication system (Clerk removed)
- Static frontend files served by Flask (no build process)

### Database Hierarchy
```
Enterprise (Trial Owner)
├── Organizations (e.g., "TechCorp", "RetailPlus")
│   ├── Channels (Inbound Calls, Outbound Calls, WhatsApp)
│   │   ├── Voice Agents (AI assistants)
│   │   │   └── Contacts (Agent-specific contacts)
```

### Key API Endpoints
- Auth: `/auth/*` - Login, signup, user management
- Enterprises: `/api/enterprises/*` - Organization CRUD
- Voice Agents: `/api/voice-agents/*` - AI agent management
- Contacts: `/api/contacts/*` - Contact management
- Organizations: `/api/organizations/*` - Multi-org support
- Channels: `/api/channels/*` - Communication channels

### Middleware Components
- `auth.py` - Local authentication system
- `trial_middleware.py` - Trial account limitations

### Environment Variables Required
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-secret-key
# CLERK_SECRET_KEY removed - using local auth
```

### Current Implementation Status
- Phase 1: Core Functionality ✅
- Phase 2: Supabase Integration ✅
- Phase 3: Advanced AI Integration (In Progress)
- Using local SQLite authentication for all users

### Database Schema
Apply schema using Supabase SQL Editor:
- `supabase_schema.sql` - Main database schema
- `updated_schema.sql` - Updated enterprise structure
- `create_contact_tables.sql` - Contact management tables

### Development Notes
- Always test with admin@bhashai.com (superadmin account)
- Row Level Security (RLS) is enabled - ensure proper auth
- Frontend uses vanilla JavaScript - no framework or bundling
- API returns JSON responses with proper error handling
- Trial middleware limits features for trial accounts