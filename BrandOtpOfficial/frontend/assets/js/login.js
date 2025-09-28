// ===== LOGIN.JS - Handle Login Form and Dashboard Redirect =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔐 Login page loaded');
    
    // Get form elements
    const form = document.getElementById('loginForm');
    const submitBtn = document.getElementById('submitBtn');
    const messageContainer = document.getElementById('messageContainer');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    
    // Check if required elements exist
    if (!form || !submitBtn || !messageContainer) {
        console.error('❌ Required elements not found');
        return;
    }
    
    console.log('✅ All login elements found');

    // ✅ Check if user just registered - show welcome message
    checkRegistrationStatus();

    // ✅ Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent default form submission
        console.log('🔐 Login form submitted');
        
        // Clear previous messages
        clearMessage();
        
        // Get form data
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        // Validate form data
        const validation = validateLoginForm({ email, password });
        if (!validation.isValid) {
            showMessage(validation.message, 'error');
            return;
        }
        
        // Set loading state
        setLoadingState(true);
        
        try {
            // Create FormData for API
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            
            console.log('📤 Sending login request to API...');
            
            // Send POST request to login API
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                body: formData
            });
            
            console.log('📥 Login response status:', response.status);
            
            const result = await response.json();
            console.log('📋 Login response data:', result);
            
            if (response.ok && result.success) {
                // ✅ SUCCESS: Save token and redirect to DASHBOARD
                showMessage('🎉 Login successful! Redirecting to dashboard...', 'success');
                
                // ✅ Save access token and user info to localStorage
                localStorage.setItem('access_token', result.access_token);
                localStorage.setItem('user', JSON.stringify(result.user));
                
                console.log('✅ Token saved:', result.access_token ? 'Yes' : 'No');
                console.log('✅ User info saved:', result.user ? 'Yes' : 'No');
                
                // Clear registration session data
                sessionStorage.removeItem('registered_email');
                sessionStorage.removeItem('registered_username');
                
                console.log('🚀 Redirecting to dashboard...');
                
                // ✅ Redirect to DASHBOARD after 1.5 seconds
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
                
            } else {
                // Show error message
                const errorMsg = result.detail || 'Login failed. Please check your credentials.';
                showMessage('❌ ' + errorMsg, 'error');
            }
            
        } catch (error) {
            console.error('❌ Login error:', error);
            showMessage('❌ Network error. Please check your connection.', 'error');
        } finally {
            // Reset loading state
            setLoadingState(false);
        }
    });

    // ===== HELPER FUNCTIONS =====

    function checkRegistrationStatus() {
        const registeredEmail = sessionStorage.getItem('registered_email');
        const registeredUsername = sessionStorage.getItem('registered_username');
        
        if (registeredEmail && registeredUsername) {
            console.log('👋 User just registered, showing welcome message');
            
            // Pre-fill email field
            emailInput.value = registeredEmail;
            
            // Show personalized welcome message
            document.getElementById('welcomeText').textContent = 
                `Welcome ${registeredUsername}! Please login with your new account.`;
            welcomeMessage.style.display = 'block';
            
            // Focus on password field since email is pre-filled
            passwordInput.focus();
        }
    }

    function validateLoginForm(data) {
        // Check required fields
        if (!data.email || !data.password) {
            return { isValid: false, message: 'Please fill in all required fields.' };
        }
        
        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(data.email)) {
            return { isValid: false, message: 'Please enter a valid email address.' };
        }
        
        // Validate password length
        if (data.password.length < 6) {
            return { isValid: false, message: 'Password must be at least 6 characters long.' };
        }
        
        return { isValid: true };
    }

    function showMessage(message, type) {
        messageContainer.textContent = message;
        messageContainer.className = 'message ' + type + '-message';
        messageContainer.style.display = 'block';
        
        // Scroll message into view
        messageContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function clearMessage() {
        messageContainer.innerHTML = '';
        messageContainer.style.display = 'none';
        // Don't hide welcome message when clearing error messages
    }

    function setLoadingState(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Login';
        }
    }
});
