// Simple dashboard JavaScript - No Clerk dependencies

window.addEventListener('load', () => {
    console.log('Dashboard loaded - simple authentication mode');
    
    // Get user info from URL params or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const userEmail = urlParams.get('email') || localStorage.getItem('userEmail') || 'user@example.com';
    const userName = urlParams.get('name') || localStorage.getItem('enterpriseName') || 'My Enterprise';
    
    // Store in localStorage for future visits
    localStorage.setItem('userEmail', userEmail);
    localStorage.setItem('enterpriseName', userName);
    
    // Create a simple user object
    const user = {
        emailAddresses: [{ emailAddress: userEmail }],
        firstName: userName.split(' ')[0] || 'User',
        lastName: userName.split(' ')[1] || ''
    };
    
    // Show dashboard with user info
    showDashboard(user);
});

// Show dashboard function (simplified)
function showDashboard(user) {
    console.log('Showing dashboard for user:', user.emailAddresses[0]?.emailAddress);
    
    // Hide authentication required message
    const authRequired = document.getElementById('authRequired');
    if (authRequired) {
        authRequired.style.display = 'none';
    }
    
    // Show dashboard content
    const dashboardContent = document.getElementById('dashboardContent');
    if (dashboardContent) {
        dashboardContent.style.display = 'block';
    }
    
    // Update user info in header
    const userEmailSpan = document.getElementById('userEmail');
    if (userEmailSpan) {
        userEmailSpan.textContent = user.emailAddresses[0]?.emailAddress;
    }
    
    const userNameSpan = document.getElementById('userName');
    if (userNameSpan) {
        userNameSpan.textContent = `${user.firstName} ${user.lastName}`.trim();
    }
    
    // Load dashboard data
    loadOrganizations();
    loadVoiceAgents();
    loadContacts();
}

// Show unauthenticated state
function showUnauthenticated() {
    console.log('Showing unauthenticated state');
    
    const authRequired = document.getElementById('authRequired');
    if (authRequired) {
        authRequired.style.display = 'flex';
    }
    
    const dashboardContent = document.getElementById('dashboardContent');
    if (dashboardContent) {
        dashboardContent.style.display = 'none';
    }
}

// Simplified API request function
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Load organizations (simplified)
async function loadOrganizations() {
    try {
        console.log('Loading organizations...');
        // For now, show sample data
        const organizations = [
            { id: 1, name: 'Main Hospital', type: 'hospital', status: 'active' },
            { id: 2, name: 'Emergency Department', type: 'department', status: 'active' }
        ];
        
        displayOrganizations(organizations);
    } catch (error) {
        console.error('Error loading organizations:', error);
        displayOrganizations([]);
    }
}

// Load voice agents (simplified)  
async function loadVoiceAgents() {
    try {
        console.log('Loading voice agents...');
        // For now, show sample data
        const voiceAgents = [
            { id: 1, name: 'Appointment Booking Agent', language: 'Hindi', status: 'active' },
            { id: 2, name: 'Prescription Reminder Agent', language: 'Hinglish', status: 'active' }
        ];
        
        displayVoiceAgents(voiceAgents);
    } catch (error) {
        console.error('Error loading voice agents:', error);
        displayVoiceAgents([]);
    }
}

// Load contacts (simplified)
async function loadContacts() {
    try {
        console.log('Loading contacts...');
        // For now, show sample data  
        const contacts = [
            { id: 1, name: 'Rajesh Kumar', phone: '+91 98765 43210', status: 'active' },
            { id: 2, name: 'Priya Sharma', phone: '+91 87654 32109', status: 'active' }
        ];
        
        displayContacts(contacts);
    } catch (error) {
        console.error('Error loading contacts:', error);
        displayContacts([]);
    }
}

// Display functions (keep existing ones from dashboard)
function displayOrganizations(organizations) {
    console.log('Displaying organizations:', organizations);
    // The existing display logic should work
}

function displayVoiceAgents(voiceAgents) {
    console.log('Displaying voice agents:', voiceAgents);
    // The existing display logic should work
}

function displayContacts(contacts) {
    console.log('Displaying contacts:', contacts);
    // The existing display logic should work
}

// Sign out function (redirect to landing)
async function signOut() {
    localStorage.clear();
    window.location.href = '/';
}

// Redirect to sign in
function redirectToSignIn() {
    window.location.href = '/signup';
}