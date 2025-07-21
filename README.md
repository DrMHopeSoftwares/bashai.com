# DrM Hope SaaS Platform

A comprehensive SaaS platform for managing organizations and AI voice agents with native Hindi/Hinglish support. Built with Flask backend and Supabase database, designed for scalability and enterprise use.

## 🚀 Features

- **Enterprise Management**: Complete CRUD operations for organizations
- **User Management**: Role-based access control (super_admin, admin, user)
- **AI Voice Agents**: Integration ready for Clinivoice Hindi-native AI
- **Real-time Dashboard**: Live statistics and activity monitoring
- **Secure Authentication**: Supabase Auth with JWT tokens
- **Row Level Security**: Database-level security policies
- **Multi-tenant Architecture**: Organization-based data isolation
- **Responsive Design**: Mobile-friendly interface

## 🏗️ Architecture

```
Frontend (Vanilla JS) → Flask API → Supabase (PostgreSQL + Auth)
```

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python Flask with RESTful API
- **Database**: Supabase (PostgreSQL with real-time features)
- **Authentication**: Supabase Auth with JWT
- **Deployment**: Manus Platform ready

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- Modern web browser

## ⚡ Quick Start

### Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Set up Supabase**:
   - Create a Supabase project
   - Run `supabase_schema.sql` in SQL Editor
   - Create admin user in Auth

4. **Start the application**:
   ```bash
   python main.py
   ```

5. **Access the platform**:
   - Open http://localhost:5000
   - Login with: admin@drmhope.com / DrMHope@2024

## 📁 Project Structure

```
clinivooice/
├── main.py                 # Flask application with Supabase integration
├── static/
│   └── landing.html       # Modern landing page with enterprise signup
├── supabase_schema.sql    # Database schema and RLS policies
├── requirements.txt       # Python dependencies
├── test_connection.py     # Connection testing utility
├── .env.example          # Environment variables template
├── SETUP_GUIDE.md        # Detailed setup instructions
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-secret-key
```

### Database Schema

The platform uses the following main tables:
- `enterprises` - Organization data
- `users` - User accounts and roles
- `voice_agents` - AI voice agent configurations
- `call_logs` - Call history and analytics
- `activity_logs` - System activity tracking

## 🔐 Security Features

- **Row Level Security (RLS)**: Database-level access control
- **JWT Authentication**: Secure token-based auth
- **Role-based Permissions**: Super admin, admin, and user roles
- **Data Isolation**: Multi-tenant architecture
- **Indian Data Residency**: Compliant with local regulations

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Enterprises
- `GET /api/enterprises` - List enterprises
- `POST /api/enterprises` - Create enterprise
- `PUT /api/enterprises/<id>` - Update enterprise
- `DELETE /api/enterprises/<id>` - Delete enterprise

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

### Dashboard
- `GET /api/stats` - Get dashboard statistics

## 🧪 Testing

### Demo Credentials
- **Email**: admin@drmhope.com
- **Password**: DrMHope@2024

### Test Scenarios
1. Login with demo credentials
2. Create new organization
3. Add users to organization
4. Verify dashboard statistics update
5. Test role-based access control

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Manus Platform
The application is configured for deployment on Manus platform with proper static file serving.

## 🔄 Phase Roadmap

### ✅ Phase 1: Core Functionality (Complete)
- Flask backend with basic CRUD operations
- Frontend dashboard
- Manus platform deployment

### ✅ Phase 2: Supabase Integration (Complete)
- Full Supabase database integration
- Proper authentication with JWT
- Row Level Security implementation
- Flask application stability improvements

### 🔄 Phase 3: Clinivoice Integration (Next)
- Hindi-native AI voice agent integration
- Voice agent management UI
- Call logging and analytics
- Interactive demo widget

### 📋 Phase 4: Advanced Features (Planned)
- Real-time updates with WebSockets
- Advanced analytics and reporting
- Mobile app support
- API rate limiting and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For setup issues or questions:
1. Check the `SETUP_GUIDE.md` for detailed instructions
2. Verify Supabase configuration and credentials
3. Check browser console for frontend errors
4. Review Flask logs for backend issues

## 📄 License

Copyright © 2024 DrM Hope Softwares. All rights reserved.

## 🙏 Acknowledgments

- **Supabase** - Backend-as-a-Service platform
- **Flask** - Python web framework
- **Clinivoice** - AI voice technology partner
- **Manus Platform** - Deployment infrastructure

---

**Made with ❤️ by DrM Hope Softwares | Powered by Clinivoice AI**
# bashai.com
