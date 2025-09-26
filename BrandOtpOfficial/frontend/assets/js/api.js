const API_BASE_URL = 'http://127.0.0.1:8000';

async function apiRequest(endpoint, method = 'GET', data = null, token = null) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = { 'Content-Type': 'application/json' };
    
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const options = { method, headers };
    if (data && method !== 'GET') options.body = JSON.stringify(data);
    
    const response = await fetch(url, options);
    const result = await response.json();
    
    if (!response.ok) {
        throw new Error(result.detail || 'API request failed');
    }
    
    return result;
}

// ✅ MAIN API FUNCTIONS
const api = {
    // Authentication
    auth: {
        login: async (email, password) => {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);
            
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Login failed');
            return data;
        },
        
        getProfile: async () => {
            const token = localStorage.getItem('token');
            return apiRequest('/auth/me', 'GET', null, token);
        },
        
        logout: () => {
            localStorage.removeItem('token');
            localStorage.removeItem('username');
        }
    },
    
    // Wallet Operations
    wallet: {
        getBalance: async () => {
            const token = localStorage.getItem('token');
            return apiRequest('/wallet/balance', 'GET', null, token);
        },
        
        addMoney: async (amount) => {
            const token = localStorage.getItem('token');
            const formData = new FormData();
            formData.append('amount', amount);
            formData.append('payment_method', 'manual');
            
            const response = await fetch(`${API_BASE_URL}/wallet/add-money`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to add money');
            return data;
        },
        
        getTransactions: async () => {
            const token = localStorage.getItem('token');
            return apiRequest('/wallet/transactions', 'GET', null, token);
        }
    },
    
    // ✅ SMSMan Services (70% Markup)
    smsman: {
        getServices: async () => {
            const data = await apiRequest('/smsman/services');
            console.log('✅ Services loaded:', data.services);
            return data.services || [];
        },
        
        getMeta: async () => {
            return apiRequest('/smsman/meta');
        },
        
        getPrice: async (applicationId, countryId) => {
            return apiRequest(`/smsman/price/${applicationId}/${countryId}`);
        },
        
        buyNumber: async (applicationId, countryId) => {
            const token = localStorage.getItem('token');
            return apiRequest('/smsman/buy', 'POST', {
                application_id: applicationId,
                country_id: countryId
            }, token);
        },
        
        getSMS: async (requestId) => {
            const token = localStorage.getItem('token');
            return apiRequest(`/smsman/sms/${requestId}`, 'GET', null, token);
        },
        
        cancel: async (requestId) => {
            const token = localStorage.getItem('token');
            return apiRequest(`/smsman/cancel/${requestId}`, 'POST', null, token);
        }
    },
    
    // ✅ Pricing Helpers
    pricing: {
        formatPrice: (price) => `₹${Number(price).toFixed(2)}`,
        
        canAfford: (userBalance, servicePrice) => 
            Number(userBalance) >= Number(servicePrice),
            
        getShortage: (userBalance, servicePrice) => {
            const shortage = Number(servicePrice) - Number(userBalance);
            return shortage > 0 ? shortage : 0;
        }
    },
    
    // ✅ Complete Purchase Flow
    purchase: {
        buyService: async (serviceId, countryId = 91) => {
            try {
                console.log(`🛒 Buying service: ${serviceId}`);
                
                // Check balance
                const balance = await api.wallet.getBalance();
                console.log(`💰 Balance: ₹${balance.balance}`);
                
                // Get price
                const priceInfo = await api.smsman.getPrice(serviceId, countryId);
                console.log(`💰 Price: ${api.pricing.formatPrice(priceInfo.user_price)}`);
                
                // Check affordability
                if (!api.pricing.canAfford(balance.balance, priceInfo.user_price)) {
                    const shortage = api.pricing.getShortage(balance.balance, priceInfo.user_price);
                    throw new Error(`Insufficient balance! Need ${api.pricing.formatPrice(shortage)} more`);
                }
                
                // Buy
                const result = await api.smsman.buyNumber(serviceId, countryId);
                console.log('✅ Purchase successful:', result);
                
                return { success: true, ...result, pricing: priceInfo };
                
            } catch (error) {
                console.error('❌ Purchase failed:', error);
                throw error;
            }
        }
    }
};

// ✅ UI HELPERS
async function loadServicesWithPrices() {
    try {
        const services = await api.smsman.getServices();
        const balance = await api.wallet.getBalance();
        
        console.log('✅ Services:', services);
        console.log('✅ Balance:', balance.balance);
        
        // Display services with prices
        services.forEach(service => {
            console.log(`${service.name}: ${service.display_price}`);
        });
        
        return services;
    } catch (error) {
        console.error('❌ Failed to load services:', error);
        return [];
    }
}

async function handleBuyClick(serviceId) {
    try {
        const result = await api.purchase.buyService(serviceId);
        alert(`✅ Success!\nNumber: ${result.number}\nCharged: ${result.transaction.charged_amount}\nNew Balance: ₹${result.transaction.new_balance}`);
        
        // Refresh page or update UI
        location.reload();
    } catch (error) {
        alert(`❌ Purchase failed: ${error.message}`);
    }
}

// Auto-load on page ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('dashboard') || window.location.pathname.includes('services')) {
        loadServicesWithPrices();
    }
});

// Make api available globally
window.api = api;
window.loadServicesWithPrices = loadServicesWithPrices;
window.handleBuyClick = handleBuyClick;
