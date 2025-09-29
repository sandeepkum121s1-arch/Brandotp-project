// ===== ADD MONEY SCRIPT - BACKEND CONNECTED =====
console.log('💳 Add Money page loading...');

// ✅ BACKEND URL CONSTANT
const BACKEND_URL = 'https://brandotp-project1.onrender.com';

/* ---------- Elements ---------- */
const form   = document.getElementById("addMoneyForm");
const amount = document.getElementById("amount");
const mobile = document.getElementById("mobile_number");
const msgBox = document.getElementById("message");
const btn    = document.getElementById("addMoneyBtn");

/* ✅ AUTHENTICATION CHECK */
function checkAuth() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        console.log('❌ No authentication found, redirecting to login');
        window.location.href = '/login';
        return false;
    }
    return true;
}

/* ✅ QUICK-FILL AMOUNT BUTTONS */
function setAmount(v){
    amount.value = v;
    amount.focus();
}

/* ✅ SHOW / HIDE MESSAGES */
function showMessage(text, type){
    msgBox.textContent = text;
    msgBox.className = `message ${type}`;
    msgBox.style.display = "block";
    
    // Auto-hide error messages after 5 seconds
    if (type === 'error') {
        setTimeout(() => {
            msgBox.style.display = 'none';
        }, 5000);
    }
}

function clearMessage(){ 
    msgBox.style.display = "none"; 
    msgBox.className = 'message';
    msgBox.textContent = '';
}

/* ✅ FORM SUBMISSION HANDLER */
form.addEventListener("submit", async e => {
    e.preventDefault();
    clearMessage();
    
    // Disable button and show loading
    btn.disabled = true;
    btn.textContent = '⏳ Processing...';

    try {
        /* ✅ CLIENT-SIDE VALIDATION */
        const amt = parseFloat(amount.value);
        if (isNaN(amt) || amt < 50 || amt > 5000) {
            throw new Error("Enter amount ₹50–₹5,000");
        }
        if (!/^\d{10}$/.test(mobile.value)) {
            throw new Error("Enter valid 10-digit mobile number");
        }

        /* ✅ GET ACCESS TOKEN */
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            throw new Error("Please login to continue");
        }

        /* ✅ API CALL TO BACKEND - ADD MONEY ENDPOINT */
        const response = await fetch(`${BACKEND_URL}/api/wallet/add-money`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                amount: amt,
                mobile_number: mobile.value,
                payment_method: 'pay0'
            })
        });

        const data = await response.json();
        console.log('💳 Add Money response:', data);

        if (response.ok && data.success) {
            showMessage('Payment request created successfully! Redirecting...', 'success');
            
            // Redirect to payment gateway or success page
            if (data.payment_url) {
                setTimeout(() => {
                    window.location.href = data.payment_url;
                }, 1500);
            } else {
                setTimeout(() => {
                    window.location.href = '/wallet';
                }, 2000);
            }
            
        } else {
            const errorMsg = data.detail || data.message || 'Failed to process payment request';
            throw new Error(errorMsg);
        }

    } catch (err) {
        console.error('❌ Add Money error:', err);
        showMessage(err.message || "Payment error", "error");
        
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.textContent = '💳 Proceed to Pay0';
    }
});

/* ✅ CHECK AUTHENTICATION ON PAGE LOAD */
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Add Money DOM loaded');
    checkAuth();
});

/* ✅ HANDLE PAGE ERRORS */
window.addEventListener('error', function(e) {
    console.error('Add Money page error:', e.error);
});

console.log('✅ Add Money script loaded successfully - Backend connected!');
