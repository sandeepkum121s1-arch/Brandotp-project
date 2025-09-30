// ===== BUY NUMBER SCRIPT - NETLIFY READY VERSION =====
console.log('🚀 Buy Number Script Loading...');

// ✅ NETLIFY PROXY - EMPTY BACKEND URL (Netlify will handle routing)
const BACKEND_URL = '';

// Global data storage
let countries = [];
let allServices = []; 
let filteredServices = [];
let currentPurchase = null;
let smsCheckInterval = null;

// DOM elements
const countrySelect = document.getElementById('countrySelect');
const serviceSelect = document.getElementById('serviceSelect');
const countrySearch = document.getElementById('countrySearch');
const serviceSearch = document.getElementById('serviceSearch');
const serviceCount = document.getElementById('serviceCount');
const buyBtn = document.getElementById('buyBtn');
const result = document.getElementById('result');
const loadingOverlay = document.getElementById('loadingOverlay');

// Number display elements
const numberSection = document.getElementById('numberSection');
const phoneNumber = document.getElementById('phoneNumber');
const requestId = document.getElementById('requestId');
const numberStatus = document.getElementById('numberStatus');

// SMS display elements
const smsSection = document.getElementById('smsSection');
const smsFrom = document.getElementById('smsFrom');
const smsMessage = document.getElementById('smsMessage');
const smsCode = document.getElementById('smsCode');

/* ✅ SIMPLE HEADERS - NO AUTH REQUIRED */
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Buy Number DOM loaded - Starting without auth check');
    loadCountries();
});

async function loadCountries() {
    loadingOverlay.style.display = 'flex';
    
    try {
        /* ✅ NETLIFY PROXY API CALL - YOUR TOML WILL HANDLE ROUTING */
        console.log('🌍 Fetching countries via Netlify proxy...');
        
        const response = await fetch('/api/smsman/countries', {
            method: 'GET',
            headers: getHeaders()
        });
        
        console.log('🌍 Countries response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🌍 Countries response data:', data);
        
        if (data.success && data.countries && data.countries.length > 0) {
            countries = data.countries;
            populateCountries();
            showSuccess(`✅ Loaded ${countries.length} countries successfully!`);
        } else {
            throw new Error(data.detail || 'No countries found in response');
        }
        
    } catch (error) {
        console.error('❌ Error loading countries:', error);
        showError('Failed to load countries from server. Using fallback countries for testing...');
        loadFallbackCountries();
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

// Load services when country changes
async function loadServicesForCountry(countryId) {
    serviceSelect.innerHTML = '<option value="">🔄 Loading services...</option>';
    serviceSearch.disabled = true;
    serviceSearch.placeholder = 'Loading services...';
    serviceCount.textContent = '';
    
    try {
        /* ✅ NETLIFY PROXY API CALL */
        console.log(`🛠️ Fetching services for country ${countryId} via Netlify proxy...`);
        
        const response = await fetch(`/api/smsman/services/${countryId}`, {
            method: 'GET',
            headers: getHeaders()
        });
        
        console.log(`🛠️ Services response status for country ${countryId}:`, response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`🛠️ Services for country ${countryId}:`, data);
        
        if (data.success && data.services && data.services.length > 0) {
            allServices = data.services;
            filteredServices = [...allServices];
            
            populateServices();
            updateServiceSearch();
            
            showInfo(`✅ Loaded ${allServices.length} services for selected country`);
            console.log(`✅ Loaded ${allServices.length} services for country ${countryId}`);
        } else {
            serviceSelect.innerHTML = '<option value="">❌ No services available for this country</option>';
            allServices = [];
            filteredServices = [];
            serviceSearch.disabled = true;
            serviceSearch.placeholder = 'No services available';
            serviceCount.textContent = '';
            showError('No services available for this country');
        }
        
    } catch (error) {
        console.error('❌ Error loading services:', error);
        serviceSelect.innerHTML = '<option value="">❌ Error loading services</option>';
        allServices = [];
        filteredServices = [];
        serviceSearch.disabled = true;
        serviceSearch.placeholder = 'Error loading services';
        serviceCount.textContent = '';
        showError('Error loading services from server');
    }
}

function populateCountries() {
    countrySelect.innerHTML = '<option value="">Select Country</option>';
    
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = `${country.title} (${country.code})`;
        countrySelect.appendChild(option);
    });
}

function populateServices() {
    serviceSelect.innerHTML = '<option value="">Select Service</option>';
    
    filteredServices.forEach(service => {
        const option = document.createElement('option');
        option.value = service.id;
        option.textContent = `${service.name} - ${service.display_price}`;
        serviceSelect.appendChild(option);
    });
    
    updateServiceCount();
}

function updateServiceSearch() {
    serviceSearch.disabled = false;
    serviceSearch.placeholder = 'Search services... (e.g., WhatsApp, Telegram, Instagram)';
    serviceSearch.value = '';
}

function updateServiceCount() {
    if (allServices.length > 0) {
        serviceCount.textContent = `Showing ${filteredServices.length} of ${allServices.length} services`;
    } else {
        serviceCount.textContent = '';
    }
}

// Country change handler
countrySelect.addEventListener('change', function(e) {
    const countryId = parseInt(e.target.value);
    
    if (countryId) {
        loadServicesForCountry(countryId);
    } else {
        serviceSelect.innerHTML = '<option value="">Select country first...</option>';
        allServices = [];
        filteredServices = [];
        serviceSearch.disabled = true;
        serviceSearch.placeholder = 'Select country first...';
        serviceSearch.value = '';
        serviceCount.textContent = '';
    }
});

// Service search functionality
serviceSearch.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase().trim();
    
    if (searchTerm.length < 1) {
        filteredServices = [...allServices];
    } else {
        filteredServices = allServices.filter(service => 
            service.name.toLowerCase().includes(searchTerm) ||
            service.display_price.toLowerCase().includes(searchTerm)
        );
    }
    
    populateServices();
    console.log(`🔍 Service search: "${searchTerm}" - Found ${filteredServices.length} services`);
});

// Country search functionality
countrySearch.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    
    if (searchTerm.length < 1) {
        populateCountries();
        return;
    }
    
    const filteredCountries = countries.filter(country => 
        country.title.toLowerCase().includes(searchTerm) ||
        country.code.toLowerCase().includes(searchTerm)
    );
    
    countrySelect.innerHTML = '<option value="">Select Country</option>';
    
    filteredCountries.forEach(country => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = `${country.title} (${country.code})`;
        countrySelect.appendChild(option);
    });
});

// Form submission - BUY NUMBER
document.getElementById('buyNumberForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const countryId = countrySelect.value;
    const serviceId = serviceSelect.value;
    
    if (!countryId || !serviceId) {
        showError('Please select both country and service.');
        return;
    }
    
    buyBtn.disabled = true;
    buyBtn.textContent = '🔄 Purchasing...';
    result.innerHTML = '';
    
    // Hide previous results
    numberSection.style.display = 'none';
    smsSection.style.display = 'none';
    
    try {
        /* ✅ NETLIFY PROXY API CALL - BUY NUMBER */
        console.log('🛒 Buying number:', {serviceId, countryId});
        
        const response = await fetch('/api/smsman/buy', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                application_id: parseInt(serviceId),
                country_id: parseInt(countryId)
            })
        });
        
        console.log('🛒 Buy response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🛒 Buy Number response:', data);
        
        if (data.success && data.number && data.request_id) {
            // Store purchase info
            currentPurchase = {
                number: data.number,
                request_id: data.request_id,
                service_id: serviceId,
                country_id: countryId
            };
            
            // Display the number
            displayPurchasedNumber(data);
            
            // Start checking for SMS automatically
            startSMSChecking();
            
        } else {
            showError(data.detail || data.error || 'Failed to purchase number. Please try again.');
        }
        
    } catch (error) {
        console.error('❌ Purchase error:', error);
        showError(`Purchase failed: ${error.message}`);
    } finally {
        buyBtn.disabled = false;
        buyBtn.textContent = '🛒 Buy Number';
    }
});

function displayPurchasedNumber(data) {
    phoneNumber.textContent = data.number;
    requestId.textContent = data.request_id;
    numberStatus.textContent = 'Waiting for SMS';
    numberStatus.className = 'status-badge status-waiting';
    
    numberSection.style.display = 'block';
    showSuccess('✅ Number purchased successfully! Waiting for SMS...');
}

function startSMSChecking() {
    // Check immediately, then every 10 seconds
    checkForSMS();
    
    smsCheckInterval = setInterval(checkForSMS, 10000);
    
    // Stop checking after 5 minutes
    setTimeout(() => {
        if (smsCheckInterval) {
            clearInterval(smsCheckInterval);
            smsCheckInterval = null;
            numberStatus.textContent = 'SMS Timeout';
            numberStatus.className = 'status-badge';
            numberStatus.style.background = '#f8d7da';
            numberStatus.style.color = '#721c24';
            showError('SMS timeout reached. Please try again or contact support.');
        }
    }, 300000);
}

async function checkForSMS() {
    if (!currentPurchase) return;
    
    try {
        /* ✅ NETLIFY PROXY API CALL - CHECK SMS */
        const response = await fetch('/api/smsman/get-sms', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                request_id: currentPurchase.request_id
            })
        });
        
        if (!response.ok) {
            console.warn('SMS check failed:', response.status);
            return;
        }
        
        const data = await response.json();
        console.log('📨 SMS Check response:', data);
        
        if (data.success && data.sms_code) {
            // SMS received!
            displaySMS({
                code: data.sms_code,
                message: data.sms_text || `Your verification code: ${data.sms_code}`,
                from: data.sender || 'Service'
            });
            
            // Stop checking
            if (smsCheckInterval) {
                clearInterval(smsCheckInterval);
                smsCheckInterval = null;
            }
            
            numberStatus.textContent = 'SMS Received';
            numberStatus.className = 'status-badge status-active';
            
        } else if (data.status === 'waiting') {
            console.log('Still waiting for SMS...');
        } else {
            console.log('SMS check result:', data);
        }
        
    } catch (error) {
        console.error('❌ SMS check error:', error);
        // Don't show error to user for SMS checks, just log it
    }
}

function displaySMS(smsData) {
    smsFrom.textContent = smsData.from;
    smsMessage.textContent = smsData.message;
    smsCode.textContent = smsData.code;
    
    smsSection.style.display = 'block';
    showSuccess('🎉 SMS received! Your verification code is ready.');
}

// Fallback countries in case API fails
function loadFallbackCountries() {
    console.log('🔄 Loading fallback countries for testing...');
    const fallbackCountries = [
        {id: 1, title: "Russia", code: "RU"},
        {id: 2, title: "Ukraine", code: "UA"}, 
        {id: 7, title: "Kazakhstan", code: "KZ"},
        {id: 16, title: "Philippines", code: "PH"},
        {id: 91, title: "India", code: "IN"},
        {id: 44, title: "United Kingdom", code: "GB"},
        {id: 840, title: "USA", code: "US"}
    ];
    
    countries = fallbackCountries;
    populateCountries();
    console.log('✅ Fallback countries loaded - This is for testing only');
    showInfo('Using fallback countries for testing. Please check your backend connection.');
}

function showError(message) {
    result.innerHTML = `<div class="error">❌ ${message}</div>`;
}

function showSuccess(message) {
    result.innerHTML = `<div class="success">✅ ${message}</div>`;
}

function showInfo(message) {
    result.innerHTML = `<div class="info">ℹ️ ${message}</div>`;
}

/* ✅ HANDLE PAGE ERRORS */
window.addEventListener('error', function(e) {
    console.error('Buy Number page error:', e.error);
});

console.log('✅ Buy Number script loaded successfully - Netlify Ready Version!');
