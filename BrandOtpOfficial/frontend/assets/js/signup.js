// ===== SIGNUP.JS - Handle Registration Form =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Signup page loaded');
    
    const form = document.getElementById('signupForm');
    const submitBtn = document.getElementById('submitBtn');
    const messageContainer = document.getElementById('messageContainer');
    
    if (!form || !submitBtn || !messageContainer) {
        console.error('❌ Required elements not found');
        return;
    }
    
    console.log('✅ All signup elements found');

    // ✅ Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('📝 Signup form submitted');
        
        // Clear previous messages
        clearMessage();
        
        // Get form data
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validate form
        const validation = validateSignupForm({ username, email, password, confirmPassword });
        if (!validation.isValid) {
            showMessage(validation.message, 'error');
            return;
        }
        
        // Set loading state
        setLoadingState(true);
        
        try {
            // Create FormData
            const formData = new FormData();
            formData.append('username', username);
            formData.append('email', email);
            formData.append('password', password);
            formData.append('confirmPassword', confirmPassword);
            
            console.log('📤 Sending signup request...');
            
            // Submit to API
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log('📥 Signup response:', result);
            
            if (response.ok && result.success) {
                // ✅ SUCCESS: Show message and redirect to LOGIN (not dashboard)
                showMessage('🎉 Account created successfully! Redirecting to login...', 'success');
                
                // Save user info for login page (optional)
                sessionStorage.setItem('registered_email', email);
                sessionStorage.setItem('registered_username', username);
                
                // ✅ Redirect to LOGIN page after 2 seconds
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
                
            } else {
                const errorMsg = result.detail || 'Registration failed. Please try again.';
                showMessage('❌ ' + errorMsg, 'error');
            }
            
        } catch (error) {
            console.error('❌ Signup error:', error);
            showMessage('❌ Network error. Please check your connection.', 'error');
        } finally {
            setLoadingState(false);
        }
    });

    // ===== HELPER FUNCTIONS =====
    function validateSignupForm(data) {
        if (!data.username || !data.email || !data.password || !data.confirmPassword) {
            return { isValid: false, message: 'Please fill in all required fields.' };
        }
        
        if (data.username.length < 3 || data.username.length > 20) {
            return { isValid: false, message: 'Username must be between 3 and 20 characters.' };
        }
        
        if (!/^[a-zA-Z0-9_]+$/.test(data.username)) {
            return { isValid: false, message: 'Username can only contain letters, numbers, and underscores.' };
        }
        
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
            return { isValid: false, message: 'Please enter a valid email address.' };
        }
        
        if (data.password.length < 6) {
            return { isValid: false, message: 'Password must be at least 6 characters long.' };
        }
        
        if (data.password !== data.confirmPassword) {
            return { isValid: false, message: 'Passwords do not match.' };
        }
        
        return { isValid: true };
    }

    function showMessage(message, type) {
        messageContainer.textContent = message;
        messageContainer.className = 'message ' + type + '-message';
        messageContainer.style.display = 'block';
        messageContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function clearMessage() {
        messageContainer.innerHTML = '';
        messageContainer.style.display = 'none';
    }

    function setLoadingState(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating Account...';
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Account';
        }
    }
});
