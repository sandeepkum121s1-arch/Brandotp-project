// ===== WALLET.JS - Real API Integration =====
console.log('💰 Wallet JS loaded');

let currentUser = null;
let isRefreshing = false;

// Initialize wallet on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('💰 Wallet page DOM loaded');
    initializeWallet();
});

// ✅ INITIALIZE WALLET
async function initializeWallet() {
    try {
        // Check authentication
        if (!await checkAuthentication()) {
            return;
        }
        
        // Load real wallet data from API
        await loadWalletData();
        
        // Start auto-refresh every 30 seconds
        setInterval(loadWalletData, 30000);
        
    } catch (error) {
        console.error('❌ Wallet initialization error:', error);
        showError('Failed to initialize wallet');
    }
}

// ✅ AUTHENTICATION CHECK
async function checkAuthentication() {
    try {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            console.log('❌ No access token found, redirecting to login');
            window.location.href = '/login';
            return false;
        }
        
        // Verify token with backend
        const response = await fetch('/api/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                currentUser = data.user;
                console.log('✅ Authentication verified:', currentUser.email);
                return true;
            }
        }
        
        // Token invalid, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return false;
        
    } catch (error) {
        console.error('❌ Authentication error:', error);
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return false;
    }
}

// ✅ LOAD REAL WALLET DATA FROM API
async function loadWalletData() {
    if (isRefreshing) return;
    isRefreshing = true;
    
    try {
        const accessToken = localStorage.getItem('access_token');
        
        // Show loading
        showLoading(true);
        
        // Fetch balance and transactions from real API
        const [balanceResponse, transactionsResponse] = await Promise.all([
            fetch('/api/wallet/balance', {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            }),
            fetch('/api/wallet/transactions', {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            })
        ]);
        
        // Process balance
        if (balanceResponse.ok) {
            const balanceData = await balanceResponse.json();
            if (balanceData.success) {
                updateWalletBalance(balanceData.balance);
                console.log('✅ Balance loaded:', balanceData.balance);
            }
        }
        
        // Process transactions
        if (transactionsResponse.ok) {
            const transactionsData = await transactionsResponse.json();
            if (transactionsData.success) {
                loadTransactionHistory(transactionsData.transactions);
                console.log('✅ Transactions loaded:', transactionsData.transactions.length);
            }
        }
        
        // Show content
        showLoading(false);
        
    } catch (error) {
        console.error('❌ Wallet loading error:', error);
        showError('Failed to load wallet data');
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
    
    transactions.forEach(transaction => {
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
    
    const isCredit = transaction.type === 'credit';
    const amountColor = isCredit ? '#28a745' : '#dc2626';
    const amountPrefix = isCredit ? '+' : '-';
    const amount = parseFloat(transaction.amount || 0).toFixed(2);
    
    item.innerHTML = `
        <div class="history-info">
            <div class="history-desc">${transaction.reason || transaction.description || 'Transaction'}</div>
            <div class="history-date">${formatDateTime(transaction.created_at)}</div>
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

console.log('✅ Real Wallet JavaScript loaded successfully');
