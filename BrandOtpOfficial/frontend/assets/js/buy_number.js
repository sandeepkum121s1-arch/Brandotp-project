console.log('🚀 Buy Number Script Loading...');

let isLoading = false;

window.onload = async function() {
    console.log('🚀 Page loaded, starting data load...');
    await loadData();
}

async function loadData() {
    setGlobalLoading(true);
    
    try {
        // Load countries and services
        await loadCountries();
        await loadServices();
        console.log('✅ Data loading completed');
        
    } catch (error) {
        console.error('❌ Data loading failed:', error);
        showResult('Data loading failed: ' + error.message, 'error');
    } finally {
        setGlobalLoading(false);
    }
}

async function loadCountries() {
    console.log('🌍 Loading countries...');
    
    try {
        const response = await fetch('/api/smsman/countries');
        console.log('📡 Countries response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Countries raw data:', data);
        console.log('📊 Data type:', typeof data);
        
        // ✅ FIXED: Handle any data format
        let countries = [];
        
        if (Array.isArray(data)) {
            countries = data;
        } else if (data && typeof data === 'object') {
            // Convert object to array
            countries = Object.values(data);
        } else {
            throw new Error('Invalid data format received');
        }
        
        console.log('📋 Processed countries count:', countries.length);
        
        if (countries.length === 0) {
            throw new Error('No countries found');
        }
        
        // Populate dropdown
        const select = document.getElementById("country");
        select.innerHTML = '<option value="">Select Country</option>';
        
        countries.forEach((country, index) => {
            const option = document.createElement("option");
            
            // Handle different object structures
            const id = country.id || country.country_id || index + 1;
            const name = country.title || country.name || country.country || `Country ${id}`;
            const code = country.code || country.country_code || '';
            
            option.value = id;
            option.textContent = code ? `${name} (${code})` : name;
            select.appendChild(option);
        });
        
        console.log('✅ Countries loaded successfully');
        
    } catch (error) {
        console.error('❌ Countries failed:', error);
        loadFallbackCountries();
    }
}

async function loadServices() {
    console.log('🛠️ Loading services...');
    
    try {
        const response = await fetch('/api/smsman/services');
        console.log('📡 Services response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Services raw data:', data);
        console.log('📊 Data type:', typeof data);
        
        // ✅ FIXED: Handle any data format
        let services = [];
        
        if (Array.isArray(data)) {
            services = data;
        } else if (data && typeof data === 'object') {
            // Convert object to array
            services = Object.values(data);
        } else {
            throw new Error('Invalid data format received');
        }
        
        console.log('📋 Processed services count:', services.length);
        
        if (services.length === 0) {
            throw new Error('No services found');
        }
        
        // Populate dropdown
        const select = document.getElementById("service");
        select.innerHTML = '<option value="">Select Service</option>';
        
        services.forEach((service, index) => {
            const option = document.createElement("option");
            
            // Handle different object structures
            const id = service.id || service.service_id || index + 1;
            const name = service.name || service.title || service.service || `Service ${id}`;
            
            option.value = id;
            option.textContent = name;
            select.appendChild(option);
        });
        
        console.log('✅ Services loaded successfully');
        
    } catch (error) {
        console.error('❌ Services failed:', error);
        loadFallbackServices();
    }
}

// Fallback functions
function loadFallbackCountries() {
    console.log('🔄 Loading fallback countries...');
    const select = document.getElementById("country");
    select.innerHTML = '<option value="">Select Country</option>';
    
    const countries = [
        {id: 1, title: "Russia", code: "RU"},
        {id: 2, title: "Ukraine", code: "UA"}, 
        {id: 7, title: "Kazakhstan", code: "KZ"},
        {id: 16, title: "Philippines", code: "PH"},
        {id: 91, title: "India", code: "IN"},
        {id: 44, title: "United Kingdom", code: "GB"},
        {id: 1, title: "USA", code: "US"}
    ];
    
    countries.forEach(country => {
        const option = document.createElement("option");
        option.value = country.id;
        option.textContent = `${country.title} (${country.code})`;
        select.appendChild(option);
    });
    
    console.log('✅ Fallback countries loaded');
}

function loadFallbackServices() {
    console.log('🔄 Loading fallback services...');
    const select = document.getElementById("service");
    select.innerHTML = '<option value="">Select Service</option>';
    
    const services = [
        {id: 1, name: "Telegram"},
        {id: 2, name: "WhatsApp"},
        {id: 12, name: "Instagram"},
        {id: 130, name: "Discord"},
        {id: 22, name: "Facebook"}
    ];
    
    services.forEach(service => {
        const option = document.createElement("option");
        option.value = service.id;
        option.textContent = service.name;
        select.appendChild(option);
    });
    
    console.log('✅ Fallback services loaded');
}

async function buyNumber() {
    const countryId = document.getElementById("country").value;
    const applicationId = document.getElementById("service").value;
    
    if (!countryId || !applicationId) {
        showResult('⚠️ Please select both country and service', 'error');
        return;
    }
    
    try {
        setButtonLoading(true);
        console.log(`🛒 Buying number: Country=${countryId}, Service=${applicationId}`);
        
        const response = await fetch('/api/smsman/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                countryId: parseInt(countryId),
                applicationId: parseInt(applicationId)
            })
        });
        
        const data = await response.json();
        console.log('📊 Buy response:', data);
        
        if (data.number) {
            showResult(`✅ Success! Number: ${data.number}`, 'success');
        } else {
            showResult(`❌ ${data.message || 'Purchase failed'}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Buy failed:', error);
        showResult(`❌ Error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(false);
    }
}

function setGlobalLoading(loading) {
    const container = document.querySelector('.container');
    if (loading) {
        container.classList.add('loading');
    } else {
        container.classList.remove('loading');
    }
}

function setButtonLoading(loading) {
    const btn = document.getElementById('buy-btn');
    if (loading) {
        btn.disabled = true;
        btn.textContent = '⏳ Buying...';
    } else {
        btn.disabled = false;
        btn.textContent = '🛒 Buy Number';
    }
}

function showResult(message, type) {
    const resultBox = document.getElementById('result');
    resultBox.textContent = message;
    resultBox.className = `result-box ${type}`;
}

console.log('✅ Buy Number Script Loaded');
