// ===== WALLET.JS - BACKEND CONNECTED =====
console.log('💰 Wallet JS loaded');

// ✅ BACKEND URL CONSTANT
const BACKEND_URL = 'https://brandotp-project1.onrender.com';

let currentUser = null;
let isRefreshing = false;

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

/* ✅ GET AUTH HEADERS */
function getAuthHeaders() {
    const accessToken = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    };
}

// Initialize wallet on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('💰 Wallet page DOM loaded');
    if (!checkAuth()) return;
    initializeWallet();
});

// ✅ INITIALIZE WALLET
async function initializeWallet() {
    try {
        console.log('🚀 Initializing wallet...');
        
        // Load real wallet data from API
        await loadWalletData();
        
        // Start auto-refresh every 30 seconds
        setInterval(loadWalletData, 30000);
        
    } catch (error) {
        console.error('❌ Wallet initialization error:', error);
        showError('Failed to initialize wallet');
    }
}

// ✅ LOAD REAL WALLET DATA FROM API
async function loadWalletData() {
    if (isRefreshing) return;
    isRefreshing = true;
    
    try {
        console.log('🔄 Loading wallet data...');
        
        // Show loading
        showLoading(true);
        
        /* ✅ API CALL TO BACKEND - GET WALLET BALANCE */
        const balanceResponse = await fetch(`${BACKEND_URL}/api/wallet/balance`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        
        const balanceData = await balanceResponse.json();
        console.log('💰 Balance response:', balanceData);
        
        if (balanceData.success && balanceData.balance !== undefined) {
            updateWalletBalance(balanceData.balance);
            console.log('✅ Balance loaded:', balanceData.balance);
        }
        
        /* ✅ API CALL TO BACKEND - GET TRANSACTION HISTORY */
        const transactionsResponse = await fetch(`${BACKEND_URL}/api/wallet/transactions`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        
        const transactionsData = await transactionsResponse.json();
        console.log('📊 Transactions response:', transactionsData);
        
        if (transactionsData.success && transactionsData.transactions) {
            loadTransactionHistory(transactionsData.transactions);
            console.log('✅ Transactions loaded:', transactionsData.transactions.length);
        } else {
            // Show empty state
            loadTransactionHistory([]);
        }
        
        // Show content
        showLoading(false);
        
    } catch (error) {
        console.error('❌ Wallet loading error:', error);
        showError('Failed to load wallet data. Please check your connection.');
    } finally {
        isRefreshing = false;
    }
}

// ✅ UPDATE BALANCE DISPLAY
function updateWalletBalance(balance) {
    const balanceEl = document.getElementById('walletBalance');
    if (balanceEl) {
        const formattedBalance = parseFloat(balance || 0).toFixed(2);
        balanceEl.textContent = `₹${formattedBalance}`;
        
        // Add animation
        balanceEl.style.transform = 'scale(1.05)';
        setTimeout(() => {
            balanceEl.style.transform = 'scale(1)';
            balanceEl.style.transition = 'transform 0.3s ease';
        }, 300);
    }
}

// ✅ LOAD REAL TRANSACTION HISTORY
function loadTransactionHistory(transactions) {
    const historyList = document.getElementById('historyList');
    const noHistory = document.getElementById('noHistory');
    
    if (!transactions || transactions.length === 0) {
        historyList.innerHTML = '';
        historyList.style.display = 'none';
        noHistory.style.display = 'block';
        return;
    }
    
    // Clear and populate with real data
    historyList.innerHTML = '';
    
    // Sort transactions by date (newest first)
    const sortedTransactions = transactions.sort((a, b) => 
        new Date(b.created_at || b.timestamp) - new Date(a.created_at || a.timestamp)
    );
    
    sortedTransactions.forEach(transaction => {
        const historyItem = createTransactionItem(transaction);
        historyList.appendChild(historyItem);
    });
    
    historyList.style.display = 'block';
    noHistory.style.display = 'none';
}

// ✅ CREATE TRANSACTION ITEM
function createTransactionItem(transaction) {
    const item = document.createElement('div');
    item.className = 'history-item';
    
    // Determine transaction type and formatting
    const isCredit = transaction.type === 'credit' || transaction.transaction_type === 'credit' || transaction.amount > 0;
    const amountColor = isCredit ? '#28a745' : '#dc2626';
    const amountPrefix = isCredit ? '+' : '-';
    const amount = Math.abs(parseFloat(transaction.amount || 0)).toFixed(2);
    
    // Get transaction description
    let description = 'Transaction';
    if (transaction.reason) {
        description = transaction.reason;
    } else if (transaction.description) {
        description = transaction.description;
    } else if (transaction.transaction_type === 'add_money') {
        description = 'Money Added to Wallet';
    } else if (transaction.transaction_type === 'purchase') {
        description = 'Number Purchase';
    }
    
    item.innerHTML = `
        <div class="history-info">
            <div class="history-desc">${description}</div>
            <div class="history-date">${formatDateTime(transaction.created_at || transaction.timestamp)}</div>
        </div>
        <div class="history-amount" style="color: ${amountColor}">
            ${amountPrefix}₹${amount}
        </div>
    `;
    
    return item;
}

// ✅ FORMAT DATE TIME
function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (minutes < 1) {
            return 'Just now';
        } else if (minutes < 60) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (hours < 24) {
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (days === 1) {
            return 'Yesterday';
        } else if (days < 7) {
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString('en-IN') + ' at ' + date.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    } catch (error) {
        return 'Unknown date';
    }
}

// ✅ SHOW/HIDE LOADING
function showLoading(show) {
    const loading = document.getElementById('loading');
    const content = document.getElementById('walletContent');
    
    if (show) {
        loading.style.display = 'block';
        content.style.display = 'none';
    } else {
        loading.style.display = 'none';
        content.style.display = 'block';
    }
}

// ✅ SHOW ERROR
function showError(message) {
    const loading = document.getElementById('loading');
    loading.innerHTML = `
        <div style="color: #dc2626; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 20px;">❌</div>
            <div>${message}</div>
            <button onclick="window.location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #4361ee; color: white; border: none; border-radius: 5px; cursor: pointer;">
                🔄 Retry
            </button>
        </div>
    `;
    loading.style.display = 'block';
    document.getElementById('walletContent').style.display = 'none';
}

// ✅ MANUAL REFRESH
function refreshWallet() {
    console.log('🔄 Manual refresh triggered');
    loadWalletData();
}

// ✅ GO TO ADD MONEY
function goToAddMoney() {
    window.location.href = '/add-money';
}

/* ✅ HANDLE PAGE ERRORS */
window.addEventListener('error', function(e) {
    console.error('Wallet page error:', e.error);
});

console.log('✅ Real Wallet JavaScript loaded successfully - Backend connected!');
