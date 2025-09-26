// ===== DASHBOARD.JS - Fixed for Profile Loading =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Dashboard loaded');
    
    // Initialize dashboard
    initializeDashboard();
});

async function initializeDashboard() {
    console.log('🚀 Initializing dashboard...');
    
    try {
        // Load user profile
        await loadUserProfile();
        console.log('✅ Dashboard initialized successfully');
        
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        showRetryButton();
    }
}

async function loadUserProfile() {
    console.log('👤 Loading user profile...');
    
    try {
        // Try the endpoint that's being called (based on terminal logs)
        const response = await fetch('/api/auth/me', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
                // Note: We'll add Authorization header later when auth is fully implemented
            }
        });
        
        console.log('📥 Profile response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('👤 Profile data:', data);
            
            if (data.success) {
                // Update UI with user data
                updateUserProfile(data.user);
                hideRetryButton();
            } else {
                throw new Error('Profile response not successful');
            }
        } else {
            throw new Error(`Profile API returned ${response.status}`);
        }
        
    } catch (error) {
        console.error('❌ Profile loading error:', error);
        
        // Fallback: Show user info from localStorage if available
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                const userData = JSON.parse(storedUser);
                console.log('📱 Using stored user data:', userData);
                updateUserProfile(userData);
                hideRetryButton();
                return;
            } catch (parseError) {
                console.error('❌ Failed to parse stored user:', parseError);
            }
        }
        
        throw error;
    }
}

function updateUserProfile(user) {
    console.log('🔄 Updating user profile UI');
    
    // Update username displays
    const userNameElements = document.querySelectorAll('.user-name, #userName, [data-user-name]');
    userNameElements.forEach(element => {
        if (element) {
            element.textContent = user.username || 'User';
        }
    });
    
    // Update "Hello, User!" text specifically
    const helloElements = document.querySelectorAll('.hello-user, .user-greeting');
    helloElements.forEach(element => {
        if (element) {
            element.textContent = `Hello, ${user.username || 'User'}! 👋`;
        }
    });
    
    // Update balance displays
    const balanceElements = document.querySelectorAll('.user-balance, #userBalance, [data-user-balance]');
    balanceElements.forEach(element => {
        if (element) {
            element.textContent = `₹${parseFloat(user.balance || 0).toFixed(2)}`;
        }
    });
    
    // Update email displays
    const emailElements = document.querySelectorAll('.user-email, #userEmail, [data-user-email]');
    emailElements.forEach(element => {
        if (element) {
            element.textContent = user.email || '';
        }
    });
    
    console.log('✅ Profile UI updated successfully');
}

function showRetryButton() {
    // Find or create retry button
    let retryContainer = document.querySelector('.retry-container');
    if (!retryContainer) {
        retryContainer = document.createElement('div');
        retryContainer.className = 'retry-container';
        retryContainer.innerHTML = `
            <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin: 20px; text-align: center;">
                <p>Failed to load your profile. Please check your connection and try again.</p>
                <button onclick="location.reload()" style="
                    margin-top: 10px; 
                    padding: 8px 16px; 
                    background: #dc3545; 
                    color: white; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer;
                ">Retry</button>
            </div>
        `;
        document.body.appendChild(retryContainer);
    }
    retryContainer.style.display = 'block';
}

function hideRetryButton() {
    const retryContainer = document.querySelector('.retry-container');
    if (retryContainer) {
        retryContainer.style.display = 'none';
    }
}

// ✅ LOGOUT FUNCTION
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Make logout function globally available
window.logout = logout;

console.log('✅ Dashboard JavaScript loaded successfully');
