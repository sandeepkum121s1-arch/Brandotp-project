/**
 * BrandOtp Frontend JavaScript
 */

// API Base URL - Change this to match your backend URL
const API_BASE_URL = 'http://localhost:8000';

// Global error handler
function handleApiError(error, customMessage = '') {
    const message = error.message || customMessage || 'An error occurred';
    alert(message);
    console.error('API Error:', error);
}

// Loading spinner functions
const loadingSpinner = {
    show: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.dataset.originalContent = element.innerHTML;
            element.innerHTML = '<div class="spinner"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
            element.classList.add('loading');
        }
    },
    hide: function(elementId) {
        const element = document.getElementById(elementId);
        if (element && element.classList.contains('loading')) {
            element.innerHTML = element.dataset.originalContent || '';
            element.classList.remove('loading');
            delete element.dataset.originalContent;
        }
    }
};

// Toast notification functions
const toast = {
    show: function(message, type = 'success') {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close"><i class="fas fa-times"></i></button>
        `;

        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.add('toast-hiding');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });

        toastContainer.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.add('toast-hiding');
                setTimeout(() => {
                    if (toast.parentNode) toast.remove();
                }, 300);
            }
        }, 5000);
    },
    success: function(message) {
        this.show(message, 'success');
    },
    error: function(message) {
        this.show(message, 'error');
    }
};

// Authentication header function
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Authentication Page Functions
function initAuthPage() {
    const authTabs = document.querySelectorAll('.auth-tab');
    const authForms = document.querySelectorAll('.auth-form');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            authTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabId = tab.getAttribute('data-tab');
            authForms.forEach(form => form.classList.remove('active'));

            if (tabId === 'login') {
                document.getElementById('login-form').classList.add('active');
            } else if (tabId === 'signup') {
                document.getElementById('signup-form').classList.add('active');
            }
        });
    });

    if (signupForm) {
        signupForm.addEventListener('submit', signupUser);
    }

    if (loginForm) {
        loginForm.addEventListener('submit', loginUser);
    }
}

// Handle signup form submission
async function signupUser(event) {
    event.preventDefault();

    const username = document.getElementById('signup-username').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    const errorElement = document.getElementById('signup-error');
    const signupButton = document.querySelector('#signup-form button[type="submit"]');

    errorElement.textContent = '';

    if (password !== confirmPassword) {
        errorElement.textContent = 'Passwords do not match';
        toast.error('Passwords do not match');
        return;
    }

    if (password.length < 8) {
        errorElement.textContent = 'Password must be at least 8 characters long';
        toast.error('Password must be at least 8 characters long');
        return;
    }

    try {
        loadingSpinner.show('signup-form');
        signupButton.disabled = true;

        const userData = { username, email, password };
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        toast.success('Signup successful! Please login with your credentials.');
        document.querySelector('.auth-tab[data-tab="login"]').click();
        document.getElementById('signup-form').reset();
    } catch (error) {
        errorElement.textContent = error.message || 'Registration failed. Please try again.';
        toast.error(error.message || 'Registration failed');
    } finally {
        loadingSpinner.hide('signup-form');
        signupButton.disabled = false;
    }
}

// ✅ Handle login form submission (fixed for FastAPI OAuth2PasswordRequestForm)
async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorElement = document.getElementById('login-error');
    const loginButton = document.querySelector('#login-form button[type="submit"]');

    errorElement.textContent = '';

    try {
        loadingSpinner.show('login-form');
        loginButton.disabled = true;

        // FastAPI OAuth2 needs form-data (x-www-form-urlencoded)
        const formData = new URLSearchParams();
        formData.append("username", email);  
        formData.append("password", password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            toast.success('Login successful!');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            throw new Error('Login failed. Invalid response from server.');
        }
    } catch (error) {
        errorElement.textContent = error.message || 'Login failed. Please check your credentials.';
        toast.error(error.message || 'Login failed');
    } finally {
        loadingSpinner.hide('login-form');
        loginButton.disabled = false;
    }
}

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.auth-page')) {
        initAuthPage();
        return;
    }

    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const navItems = document.querySelectorAll('.sidebar-nav li');
    const sections = document.querySelectorAll('.section');
    const navbarTitle = document.querySelector('.navbar-left h1');

    const walletBalanceElement = document.getElementById('wallet-balance');
    const recentTransactionsList = document.getElementById('recent-transactions');

    initApp();
});

    
    /**
     * Load services from API 
     */
    async function loadServices() {
        const tableBody = document.getElementById('services-table');
        const paginationContainer = document.getElementById('services-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr><td colspan="6">Loading services...</td></tr>';
            
            // Fetch services from API
            const response = await fetch(`${API_BASE_URL}/admin/services`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load services');
            }
            
            const data = await response.json();
            
            // Check if we have services
            if (data.services && data.services.length > 0) {
                // Render services table
                tableBody.innerHTML = data.services.map(service => `
                    <tr>
                        <td>${service.service_id}</td>
                        <td>${service.name}</td>
                        <td>$${parseFloat(service.provider_price).toFixed(2)}</td>
                        <td>$${parseFloat(service.my_price).toFixed(2)}</td>
                        <td>
                            <span class="status-badge ${service.status.toLowerCase()}">
                                ${service.status}
                            </span>
                        </td>
                        <td>
                            <div class="actions">
                                <button class="action-btn edit-service" data-id="${service.service_id}">
                                    <i class="fas fa-edit"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
                
                // Add event listeners for edit buttons
                document.querySelectorAll('.edit-service').forEach(button => {
                    button.addEventListener('click', () => {
                        const serviceId = button.getAttribute('data-id');
                        openServiceEditModal(serviceId, data.services);
                    });
                });
                
                // Setup pagination if available
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, (page) => {
                        loadServices(page);
                    });
                }
            } else {
                // No services found
                tableBody.innerHTML = '<tr><td colspan="6">No services found</td></tr>';
                paginationContainer.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading services:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Error loading services: ${error.message}</td></tr>`;
            paginationContainer.innerHTML = '';
        }
    }
    
    /**
     * Open service edit modal
     * @param {string} serviceId - ID of the service to edit
     * @param {Array} services - Array of services data
     */
    function openServiceEditModal(serviceId, services) {
        const modal = document.getElementById('service-edit-modal');
        const service = services.find(s => s.service_id === serviceId);
        
        if (!service) {
            console.error('Service not found');
            return;
        }
        
        // Populate form fields
        document.getElementById('edit-service-id').value = service.service_id;
        document.getElementById('edit-service-name').value = service.name;
        document.getElementById('edit-provider-price').value = parseFloat(service.provider_price).toFixed(2);
        document.getElementById('edit-my-price').value = parseFloat(service.my_price).toFixed(2);
        document.getElementById('edit-service-status').value = service.status.toLowerCase();
        
        // Show modal
        modal.style.display = 'block';
    }
    
    /**
     * Update service details
     */
    async function updateService() {
        const serviceId = document.getElementById('edit-service-id').value;
        const myPrice = document.getElementById('edit-my-price').value;
        const status = document.getElementById('edit-service-status').value;
        const modal = document.getElementById('service-edit-modal');
        
        try {
            // Send update request to API
            const response = await fetch(`${API_BASE_URL}/admin/service/${serviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    my_price: parseFloat(myPrice),
                    status: status
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update service');
            }
            
            // Close modal
            modal.style.display = 'none';
            
            // Reload services
            loadServices();
            
            // Show success message
            alert('Service updated successfully');
        } catch (error) {
            console.error('Error updating service:', error);
            alert(`Error updating service: ${error.message}`);
        }
    }
    
    /**
     * Load orders from API
     * @param {string} status - Optional status filter
     * @param {string} dateFrom - Optional start date filter
     * @param {string} dateTo - Optional end date filter
     */
    async function loadOrders(status = '', dateFrom = '', dateTo = '') {
        const tableBody = document.getElementById('orders-table');
        const paginationContainer = document.getElementById('orders-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr><td colspan="6">Loading orders...</td></tr>';
            
            // Construct API URL with query parameters
            let url = `${API_BASE_URL}/admin/search/orders?`;
            const params = new URLSearchParams();
            
            if (status) params.append('status', status);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            
            url += params.toString();
            
            // Fetch orders from API
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load orders');
            }
            
            const data = await response.json();
            
            // Check if we have orders
            if (data.orders && data.orders.length > 0) {
                // Render orders table
                tableBody.innerHTML = data.orders.map(order => `
                    <tr>
                        <td>${order.order_id}</td>
                        <td>${order.user_id}</td>
                        <td>$${parseFloat(order.amount).toFixed(2)}</td>
                        <td>
                            <span class="status-badge ${order.status.toLowerCase()}">
                                ${order.status}
                            </span>
                        </td>
                        <td>${new Date(order.created_at).toLocaleString()}</td>
                        <td>
                            <div class="actions">
                                <button class="action-btn view-order" data-id="${order.order_id}">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
                
                // Setup pagination if available
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, (page) => {
                        loadOrders(status, dateFrom, dateTo, page);
                    });
                }
            } else {
                // No orders found
                tableBody.innerHTML = '<tr><td colspan="6">No orders found</td></tr>';
                paginationContainer.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading orders:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Error loading orders: ${error.message}</td></tr>`;
            paginationContainer.innerHTML = '';
        }
    }
    
    /**
     * Load OTP requests from API
     * @param {string} status - Optional status filter
     * @param {string} serviceId - Optional service ID filter
     * @param {string} userId - Optional user ID filter
     */
    async function loadOtpRequests(status = '', serviceId = '', userId = '') {
        const tableBody = document.getElementById('otp-requests-table');
        const paginationContainer = document.getElementById('otp-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr><td colspan="6">Loading OTP requests...</td></tr>';
            
            // Construct API URL with query parameters
            let url = `${API_BASE_URL}/admin/search/otp?`;
            const params = new URLSearchParams();
            
            if (status) params.append('status', status);
            if (serviceId) params.append('service_id', serviceId);
            if (userId) params.append('user_id', userId);
            
            url += params.toString();
            
            // Fetch OTP requests from API
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load OTP requests');
            }
            
            const data = await response.json();
            
            // Check if we have OTP requests
            if (data.requests && data.requests.length > 0) {
                // Render OTP requests table
                tableBody.innerHTML = data.requests.map(request => `
                    <tr>
                        <td>${request.request_id}</td>
                        <td>${request.number}</td>
                        <td>
                            <span class="status-badge ${request.status.toLowerCase()}">
                                ${request.status}
                            </span>
                        </td>
                        <td>${new Date(request.created_at).toLocaleString()}</td>
                        <td>${request.otp_code || 'N/A'}</td>
                        <td>
                            <div class="actions">
                                <button class="action-btn view-otp" data-id="${request.request_id}">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
                
                // Setup pagination if available
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, (page) => {
                        loadOtpRequests(status, serviceId, userId, page);
                    });
                }
            } else {
                // No OTP requests found
                tableBody.innerHTML = '<tr><td colspan="6">No OTP requests found</td></tr>';
                paginationContainer.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading OTP requests:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Error loading OTP requests: ${error.message}</td></tr>`;
            paginationContainer.innerHTML = '';
        }
    }
    
    /**
     * Load system reports from API
     */
    async function loadReports() {
        try {
            // Fetch reports from API
            const response = await fetch(`${API_BASE_URL}/admin/reports/summary`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load reports');
            }
            
            const data = await response.json();
            
            // Update report values
            document.getElementById('total-users').textContent = data.total_users || 0;
            document.getElementById('total-revenue').textContent = `$${parseFloat(data.total_revenue || 0).toFixed(2)}`;
            document.getElementById('total-transactions').textContent = data.total_transactions || 0;
            document.getElementById('active-services').textContent = data.active_services || 0;
        } catch (error) {
            console.error('Error loading reports:', error);
            alert(`Error loading reports: ${error.message}`);
        }
    }
    
    /**
     * Switch between history tabs
     */
    function switchHistoryTab(tabId) {
        // Update active tab button
        const tabButtons = document.querySelectorAll('.history-tabs .tab-btn');
        tabButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            }
        });
        
        // Show the selected tab pane
        const tabPanes = document.querySelectorAll('.tab-pane');
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
            if (pane.id === tabId) {
                pane.classList.add('active');
            }
        });
        
        // Load data for the selected tab
        if (tabId === 'wallet-transactions') {
            loadWalletHistory();
        } else if (tabId === 'payment-orders') {
            loadPaymentHistory();
        } else if (tabId === 'otp-requests') {
            loadOtpHistory();
        }
    }
    
    /**
     * Load wallet transaction history
     */
    async function loadWalletHistory() {
        const tableBody = document.getElementById('wallet-transactions-table');
        const paginationContainer = document.getElementById('wallet-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">Loading transactions...</td></tr>';
            
            // Fetch wallet transactions from API
            const response = await fetch(`${API_BASE_URL}/wallet/transactions`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch wallet transactions');
            }
            
            const data = await response.json();
            
            // Display transactions
            if (data.transactions && data.transactions.length > 0) {
                let html = '';
                
                data.transactions.forEach(transaction => {
                    const type = transaction.type === 'credit' ? 'credit' : 'debit';
                    const formattedDate = formatDate(transaction.timestamp);
                    
                    html += `
                    <tr>
                        <td>${transaction.type === 'credit' ? '+' : '-'}$${Math.abs(transaction.amount).toFixed(2)}</td>
                        <td><span class="transaction-type ${type}">${transaction.type}</span></td>
                        <td>${transaction.ref_id || 'N/A'}</td>
                        <td>${formattedDate}</td>
                    </tr>
                    `;
                });
                
                tableBody.innerHTML = html;
                
                // Setup pagination if needed
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, loadWalletHistory);
                }
            } else {
                tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">No transactions found</td></tr>';
            }
        } catch (error) {
            console.error('Error loading wallet transactions:', error);
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">Error loading transactions</td></tr>';
        }
    }
    
    /**
     * Load payment order history
     */
    async function loadPaymentHistory() {
        const tableBody = document.getElementById('payment-orders-table');
        const paginationContainer = document.getElementById('payments-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">Loading payment orders...</td></tr>';
            
            // Fetch payment orders from API
            const response = await fetch(`${API_BASE_URL}/payments/history`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch payment orders');
            }
            
            const data = await response.json();
            
            // Display payment orders
            if (data.orders && data.orders.length > 0) {
                let html = '';
                
                data.orders.forEach(order => {
                    const formattedDate = formatDate(order.created_at);
                    
                    html += `
                    <tr>
                        <td>${order.order_id}</td>
                        <td>$${order.amount.toFixed(2)}</td>
                        <td><span class="status-badge ${order.status.toLowerCase()}">${order.status}</span></td>
                        <td>${formattedDate}</td>
                    </tr>
                    `;
                });
                
                tableBody.innerHTML = html;
                
                // Setup pagination if needed
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, loadPaymentHistory);
                }
            } else {
                tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">No payment orders found</td></tr>';
            }
        } catch (error) {
            console.error('Error loading payment orders:', error);
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="4">Error loading payment orders</td></tr>';
        }
    }
    
    /**
     * Load OTP request history
     */
    async function loadOtpHistory() {
        const tableBody = document.getElementById('otp-requests-table');
        const paginationContainer = document.getElementById('otp-pagination');
        
        try {
            // Show loading state
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="5">Loading OTP requests...</td></tr>';
            
            // Fetch OTP requests from API
            const response = await fetch(`${API_BASE_URL}/otp/history`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch OTP requests');
            }
            
            const data = await response.json();
            
            // Display OTP requests
            if (data.requests && data.requests.length > 0) {
                let html = '';
                
                data.requests.forEach(request => {
                    const formattedDate = formatDate(request.created_at);
                    
                    html += `
                    <tr>
                        <td>${request.service_id}</td>
                        <td>${request.number}</td>
                        <td><span class="status-badge ${request.status.toLowerCase()}">${request.status}</span></td>
                        <td>${request.otp_code || 'N/A'}</td>
                        <td>${formattedDate}</td>
                    </tr>
                    `;
                });
                
                tableBody.innerHTML = html;
                
                // Setup pagination if needed
                if (data.pagination) {
                    renderPagination(paginationContainer, data.pagination, loadOtpHistory);
                }
            } else {
                tableBody.innerHTML = '<tr class="no-data-row"><td colspan="5">No OTP requests found</td></tr>';
            }
        } catch (error) {
            console.error('Error loading OTP requests:', error);
            tableBody.innerHTML = '<tr class="no-data-row"><td colspan="5">Error loading OTP requests</td></tr>';
        }
    }
    
    /**
     * Render pagination controls
     */
    function renderPagination(container, pagination, loadFunction) {
        const { current_page, total_pages } = pagination;
        
        let html = '';
        
        // Previous button
        html += `<button ${current_page === 1 ? 'disabled' : ''} data-page="${current_page - 1}">Previous</button>`;
        
        // Page numbers
        const startPage = Math.max(1, current_page - 2);
        const endPage = Math.min(total_pages, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button ${i === current_page ? 'class="active"' : ''} data-page="${i}">${i}</button>`;
        }
        
        // Next button
        html += `<button ${current_page === total_pages ? 'disabled' : ''} data-page="${current_page + 1}">Next</button>`;
        
        container.innerHTML = html;
        
        // Add event listeners to pagination buttons
        container.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', () => {
                if (!button.disabled) {
                    const page = parseInt(button.getAttribute('data-page'));
                    loadFunction(page);
                }
            });
        });
    }
    
    /**
     * Initialize the application
     */
    async function initApp() {
        // Check if user is logged in
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'auth.html';
            return;
        }
        
        try {
            // Verify token and get user info
            const userInfo = await checkUserAuth();
            
            // Check if admin page is being accessed by non-admin
            if (window.location.pathname.includes('admin.html') && userInfo.role !== 'admin') {
                toast.error('Access denied. Admin privileges required.');
                window.location.href = 'index.html';
                return;
            }
            
            // Setup event listeners
            setupEventListeners();
            
            // Load user profile
            loadUserProfile(userInfo);
            
            // Check which page we're on and initialize accordingly
            const currentPage = getCurrentPage();
            
            switch(currentPage) {
                case 'wallet':
                    loadWallet();
                    break;
                case 'buy_number':
                    loadServices();
                    loadRecentNumbers();
                    break;
                case 'history':
                    loadWalletHistory();
                    setupHistoryTabs();
                    break;
                case 'admin':
                    setupAdminPage();
                    break;
                default: // dashboard or index
                    fetchWalletBalance();
                    fetchRecentTransactions();
                    showSection('dashboard');
                    break;
            }
        } catch (error) {
            // Handle authentication errors
            console.error('Auth error:', error);
            handleApiError(error, 'Authentication failed. Please login again.');
            localStorage.removeItem('token');
            window.location.href = 'auth.html';
        }
    }
    
    /**
     * Get current page name from URL
     */
    function getCurrentPage() {
        const path = window.location.pathname.toLowerCase();
        
        if (path.includes('wallet.html')) return 'wallet';
        if (path.includes('buy_number.html')) return 'buy_number';
        if (path.includes('history.html')) return 'history';
        if (path.includes('admin.html')) return 'admin';
        if (path.includes('index.html') || path.endsWith('/')) return 'dashboard';
        
        return 'unknown';
    }
    
    /**
     * Check user authentication and get user info
     */
    async function checkUserAuth() {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error('Authentication failed');
            }
            
            return await response.json();
        } catch (error) {
            throw new Error('Authentication failed: ' + (error.message || 'Unknown error'));
        }
    }
    
    /**
     * Load user profile information
     * @param {Object} userInfo - User information object
     */
    function loadUserProfile(userInfo) {
        try {
            // Update user name in the navbar
            const userNameElement = document.getElementById('user-name');
            if (userNameElement) {
                userNameElement.textContent = userInfo.username || 'User';
            }
            
            // Update admin name if on admin page
            const adminNameElement = document.getElementById('admin-name');
            if (adminNameElement) {
                adminNameElement.textContent = userInfo.username || 'Admin';
            }
            
            // If we're on the profile page, populate the form
            const usernameInput = document.getElementById('username');
            const emailInput = document.getElementById('email');
            
            if (usernameInput && emailInput) {
                usernameInput.value = userInfo.username || '';
                emailInput.value = userInfo.email || '';
                
                // Add event listener to profile form if it exists
                const profileForm = document.getElementById('profile-form');
                if (profileForm && !profileForm.hasAttribute('data-initialized')) {
                    profileForm.addEventListener('submit', handleProfileUpdate);
                    profileForm.setAttribute('data-initialized', 'true');
                }
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            handleApiError(error, 'Failed to load user profile');
        }
    }
    
    /**
     * Setup event listeners for the application
     */
    function setupEventListeners() {
        // Sidebar toggle
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Navigation
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                // Update active navigation item
                navItems.forEach(navItem => navItem.classList.remove('active'));
                item.classList.add('active');
                
                // Show corresponding section
                const sectionId = item.getAttribute('data-section');
                sections.forEach(section => section.classList.remove('active'));
                document.getElementById(sectionId).classList.add('active');
                
                // Update navbar title
                navbarTitle.textContent = item.querySelector('a').textContent.trim();
            });
        });
        
        // Buy number form
        const buyNumberForm = document.getElementById('buy-number-form');
        if (buyNumberForm) {
            buyNumberForm.addEventListener('submit', buyNumber);
        }
        
        // Cancel number buttons (delegated event for dynamically added buttons)
        document.addEventListener('click', (e) => {
            if (e.target && e.target.classList.contains('cancel-number-btn')) {
                const requestId = e.target.getAttribute('data-request-id');
                if (requestId) {
                    cancelNumber(requestId);
                }
            }
        });
        
        // History page tab buttons
        const historyTabButtons = document.querySelectorAll('.history-tabs .tab-btn');
        if (historyTabButtons.length > 0) {
            historyTabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const tabId = button.getAttribute('data-tab');
                    switchHistoryTab(tabId);
                });
            });
        }
        
        // Initialize history tabs if we're on the history page
        if (window.location.pathname.includes('history.html')) {
            setupHistoryTabs();
        }
        
        // Admin page initialization is now handled in initApp() switch statement
        
        // Section links
        document.querySelectorAll('[data-section]').forEach(element => {
            if (element.tagName === 'LI') return; // Skip sidebar nav items (already handled)
            
            element.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = element.getAttribute('data-section');
                
                // Update active navigation item
                navItems.forEach(navItem => navItem.classList.remove('active'));
                document.querySelector(`.sidebar-nav li[data-section="${sectionId}"]`).classList.add('active');
                
                // Show corresponding section
                sections.forEach(section => section.classList.remove('active'));
                document.getElementById(sectionId).classList.add('active');
                
                // Update navbar title
                navbarTitle.textContent = document.querySelector(`.sidebar-nav li[data-section="${sectionId}"] a`).textContent.trim();
            });
        });
        
        // Add funds form (dashboard)
        const addFundsForm = document.getElementById('add-funds-form');
        if (addFundsForm) {
            addFundsForm.addEventListener('submit', handleAddFunds);
        }
        
        // Add money form (wallet page)
        const addMoneyForm = document.getElementById('add-money-form');
        if (addMoneyForm) {
            addMoneyForm.addEventListener('submit', addMoney);
        }
        
        // Profile form
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', handleProfileUpdate);
        }
    }
    
    /**
 * Load wallet data (balance and transactions)
 */
async function loadWallet() {
    try {
        // Fetch wallet balance
        await fetchWalletBalance();
        
        // Fetch transaction history
        await fetchTransactions();
    } catch (error) {
        console.error('Error loading wallet data:', error);
    }
}

/**
 * Fetch wallet balance from the API
 */
async function fetchWalletBalance() {
    try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('No authentication token found');
                return;
            }
            
            const response = await fetch(`${API_BASE_URL}/wallet/balance`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch wallet balance');
            }
            
            const data = await response.json();
            
            // Update the UI with the wallet balance
            if (walletBalanceElement) {
                walletBalanceElement.textContent = data.balance.toFixed(2);
            }
        } catch (error) {
            console.error('Error fetching wallet balance:', error);
            // Handle error (e.g., show error message to user)
        }
    }
    
    /**
 * Fetch transactions from the API
 * @param {number} page - Page number for pagination
 * @param {number} limit - Number of transactions per page
 */
async function fetchTransactions(page = 1, limit = 10) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No authentication token found');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/wallet/transactions?page=${page}&limit=${limit}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch transactions');
        }
        
        const data = await response.json();
        
        // Display transactions in the transaction history table
        const tableBody = document.getElementById('transaction-history');
        if (tableBody) {
            displayTransactions(data.transactions, data.pagination);
        }
    } catch (error) {
        console.error('Error fetching transactions:', error);
    }
}

/**
 * Display transactions in the transaction history table
 * @param {Array} transactions - List of transactions
 * @param {Object} pagination - Pagination information
 */
function displayTransactions(transactions, pagination) {
    const tableBody = document.getElementById('transaction-history');
    const noTransactionsMsg = document.getElementById('no-transactions');
    const paginationContainer = document.getElementById('transaction-pagination');
    
    if (!tableBody) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    
    if (!transactions || transactions.length === 0) {
        if (noTransactionsMsg) {
            noTransactionsMsg.style.display = 'block';
        }
        if (paginationContainer) {
            paginationContainer.innerHTML = '';
        }
        return;
    }
    
    if (noTransactionsMsg) {
        noTransactionsMsg.style.display = 'none';
    }
    
    // Add transaction rows
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        
        // Format date
        const date = new Date(transaction.created_at);
        const formattedDate = formatDate(date);
        
        // Determine transaction type class
        const typeClass = transaction.type === 'credit' ? 'credit' : 'debit';
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td><span class="transaction-type ${typeClass}">${transaction.type}</span></td>
            <td>$${parseFloat(transaction.amount).toFixed(2)}</td>
            <td>${transaction.reference_id || '-'}</td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Create pagination controls if pagination info is available
    if (pagination && paginationContainer) {
        paginationContainer.innerHTML = '';
        
        // Previous button
        if (pagination.current_page > 1) {
            const prevButton = document.createElement('button');
            prevButton.textContent = 'Previous';
            prevButton.addEventListener('click', () => {
                fetchTransactions(pagination.current_page - 1, pagination.per_page);
            });
            paginationContainer.appendChild(prevButton);
        }
        
        // Page numbers
        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageButton = document.createElement('button');
            pageButton.textContent = i;
            if (i === pagination.current_page) {
                pageButton.classList.add('active');
            }
            pageButton.addEventListener('click', () => {
                fetchTransactions(i, pagination.per_page);
            });
            paginationContainer.appendChild(pageButton);
        }
        
        // Next button
        if (pagination.current_page < pagination.total_pages) {
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Next';
            nextButton.addEventListener('click', () => {
                fetchTransactions(pagination.current_page + 1, pagination.per_page);
            });
            paginationContainer.appendChild(nextButton);
        }
    }
}

/**
 * Fetch recent transactions from the API
 */
async function fetchRecentTransactions() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No authentication token found');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/wallet/transactions?limit=5`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch recent transactions');
        }
        
        const data = await response.json();
        
        // Update the UI with recent transactions
        if (recentTransactionsList) {
            renderTransactions(data.transactions, recentTransactionsList);
        }
    } catch (error) {
        console.error('Error fetching recent transactions:', error);
        // Handle error (e.g., show error message to user)
    }
}
    
    /**
     * Render transactions in the specified container
     */
    function renderTransactions(transactions, container) {
        if (!transactions || transactions.length === 0) {
            container.innerHTML = '<li class="transaction-item">No transactions found</li>';
            return;
        }
        
        container.innerHTML = '';
        
        transactions.forEach(transaction => {
            const transactionType = transaction.type === 'credit' ? 'Credit' : 'Debit';
            const amountPrefix = transaction.type === 'credit' ? '+' : '-';
            
            const li = document.createElement('li');
            li.className = 'transaction-item';
            li.innerHTML = `
                <div class="transaction-info">
                    <span class="transaction-type ${transaction.type}">${transactionType}</span>
                    <span class="transaction-date">${formatDate(transaction.created_at)}</span>
                </div>
                <span class="transaction-amount">${amountPrefix}$${transaction.amount.toFixed(2)}</span>
            `;
            
            container.appendChild(li);
        });
    }
    
    /**
     * Handle adding funds to wallet
     */
    async function handleAddFunds(e) {
        e.preventDefault();
        
        const amountInput = document.getElementById('amount');
        const amount = parseFloat(amountInput.value);
        
        if (isNaN(amount) || amount <= 0) {
            alert('Please enter a valid amount');
            return;
        }
        
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('No authentication token found');
                return;
            }
            
            const response = await fetch(`${API_BASE_URL}/wallet/add-funds`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ amount })
            });
            
            if (!response.ok) {
                throw new Error('Failed to add funds to wallet');
            }
            
            const data = await response.json();
            
            // Update the UI
            alert('Funds added successfully!');
            amountInput.value = '';
            
            // Refresh wallet balance and transactions
            fetchWalletBalance();
            fetchRecentTransactions();
        } catch (error) {
            console.error('Error adding funds:', error);
            alert('Failed to add funds. Please try again.');
        }
    }
    
    /**
     * Add money to wallet
     */
    async function addMoney(event) {
        event.preventDefault();
        const amount = document.getElementById('amount').value;
        const errorElement = document.getElementById('add-money-error');
        
        // Reset error message
        if (errorElement) {
            errorElement.textContent = '';
        }
        
        if (!amount || isNaN(amount) || amount <= 0) {
            if (errorElement) {
                errorElement.textContent = 'Please enter a valid amount';
            }
            return;
        }
        
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = 'auth.html';
                return;
            }
            
            const response = await fetch(`${API_BASE_URL}/wallet/add`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ amount: parseFloat(amount) })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to add money');
            }
            
            const data = await response.json();
            
            // Show success message
            alert('Money added successfully!');
            
            // Refresh wallet data
            loadWallet();
            
            // Clear form
            document.getElementById('amount').value = '';
        } catch (error) {
            console.error('Error adding money:', error);
            if (errorElement) {
                errorElement.textContent = error.message || 'Failed to add money. Please try again.';
            }
        }
    }
    
    /**
     * Handle profile update
     */
    async function handleProfileUpdate(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const newPassword = document.getElementById('new-password').value;
        const updateButton = document.querySelector('#profile-form button[type="submit"]');
        
        const userData = {
            username,
            email
        };
        
        if (newPassword) {
            userData.password = newPassword;
        }
        
        try {
            // Show loading spinner and disable button
            loadingSpinner.show('profile-form');
            updateButton.disabled = true;
            
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                method: 'PUT',
                headers: {
                    ...getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to update profile');
            }
            
            toast.success('Profile updated successfully!');
        } catch (error) {
            console.error('Error updating profile:', error);
            handleApiError(error, 'Failed to update profile. Please try again.');
        } finally {
            // Hide loading spinner and enable button
            loadingSpinner.hide('profile-form');
            updateButton.disabled = false;
        }
    }
    
    /**
 * Format date for display
 * @param {Date|string} dateString - The date to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    if (isNaN(date)) {
        return 'Invalid date';
    }
    
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Check if date is today
    if (date.toDateString() === now.toDateString()) {
        return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    // Check if date is yesterday
    if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    // Otherwise, return full date
    return date.toLocaleString([], { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
    });
}

/**
 * Load available services for OTP
 */
async function loadServices() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'auth.html';
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/services`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch services');
        }
        
        const services = await response.json();
        
        // Populate the service dropdown
        const serviceSelect = document.getElementById('service-select');
        if (!serviceSelect) return;
        
        // Clear existing options except the first one
        while (serviceSelect.options.length > 1) {
            serviceSelect.remove(1);
        }
        
        // Add services to dropdown
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} - $${service.my_price.toFixed(2)}`;
            option.dataset.price = service.my_price;
            option.dataset.name = service.name;
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading services:', error);
        const errorElement = document.getElementById('buy-number-error');
        if (errorElement) {
            errorElement.textContent = error.message || 'Failed to load services. Please try again.';
        }
    }
}

/**
 * Buy a number for the selected service
 */
async function buyNumber(event) {
    event.preventDefault();
    
    const serviceSelect = document.getElementById('service-select');
    const errorElement = document.getElementById('buy-number-error');
    
    // Reset error message
    if (errorElement) {
        errorElement.textContent = '';
    }
    
    if (!serviceSelect || serviceSelect.value === '') {
        if (errorElement) {
            errorElement.textContent = 'Please select a service';
        }
        return;
    }
    
    const serviceId = serviceSelect.value;
    const serviceName = serviceSelect.options[serviceSelect.selectedIndex].dataset.name;
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'auth.html';
            return;
        }
        
        // Request a number
        const response = await fetch(`${API_BASE_URL}/otp/request`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ service_id: serviceId })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to buy number');
        }
        
        const data = await response.json();
        
        // Display the number details
        displayNumberDetails(data, serviceName);
        
        // Start polling for OTP status
        startOtpPolling(data.request_id);
        
        // Refresh wallet balance
        fetchWalletBalance();
        
    } catch (error) {
        console.error('Error buying number:', error);
        if (errorElement) {
            errorElement.textContent = error.message || 'Failed to buy number. Please try again.';
        }
    }
}

/**
 * Display number details in the UI
 */
function displayNumberDetails(data, serviceName) {
    const container = document.getElementById('active-number-container');
    if (!container) return;
    
    // Show the container
    container.style.display = 'block';
    
    // Update the details
    document.getElementById('request-id').textContent = data.request_id;
    document.getElementById('phone-number').textContent = data.number || '-';
    document.getElementById('service-name').textContent = serviceName || '-';
    
    // Set status badge
    const statusElement = document.getElementById('number-status');
    if (statusElement) {
        statusElement.textContent = data.status || 'pending';
        statusElement.className = 'status-badge ' + (data.status || 'pending');
    }
    
    // Reset OTP code
    document.getElementById('otp-code').textContent = 'Waiting for code...';
    
    // Enable/disable buttons
    const copyOtpBtn = document.getElementById('copy-otp-btn');
    if (copyOtpBtn) {
        copyOtpBtn.disabled = true;
    }
    
    // Setup copy number button
    const copyNumberBtn = document.getElementById('copy-number-btn');
    if (copyNumberBtn) {
        copyNumberBtn.onclick = () => {
            navigator.clipboard.writeText(data.number)
                .then(() => alert('Number copied to clipboard'))
                .catch(err => console.error('Could not copy number:', err));
        };
    }
    
    // Setup cancel button
    const cancelBtn = document.getElementById('cancel-number-btn');
    if (cancelBtn) {
        cancelBtn.onclick = () => cancelNumber(data.request_id);
    }
}

/**
 * Start polling for OTP status
 */
function startOtpPolling(requestId) {
    // Clear any existing polling interval
    if (window.otpPollingInterval) {
        clearInterval(window.otpPollingInterval);
    }
    
    // Set up polling interval (every 10 seconds)
    window.otpPollingInterval = setInterval(() => {
        checkOtpStatus(requestId);
    }, 10000); // 10 seconds
    
    // Initial check immediately
    checkOtpStatus(requestId);
}

/**
 * Check OTP status
 */
async function checkOtpStatus(requestId) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            clearInterval(window.otpPollingInterval);
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/otp/status/${requestId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to check OTP status');
        }
        
        const data = await response.json();
        
        // Update status badge
        const statusElement = document.getElementById('number-status');
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = 'status-badge ' + data.status;
        }
        
        // Update OTP code if available
        if (data.otp_code) {
            document.getElementById('otp-code').textContent = data.otp_code;
            
            // Enable copy OTP button
            const copyOtpBtn = document.getElementById('copy-otp-btn');
            if (copyOtpBtn) {
                copyOtpBtn.disabled = false;
                copyOtpBtn.onclick = () => {
                    navigator.clipboard.writeText(data.otp_code)
                        .then(() => alert('OTP copied to clipboard'))
                        .catch(err => console.error('Could not copy OTP:', err));
                };
            }
        }
        
        // Update time remaining if available
        if (data.expires_at) {
            const expiresAt = new Date(data.expires_at);
            const now = new Date();
            const timeRemaining = Math.max(0, Math.floor((expiresAt - now) / 1000));
            
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            
            document.getElementById('time-remaining').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // If status is completed or cancelled, stop polling
        if (data.status === 'completed' || data.status === 'cancelled') {
            clearInterval(window.otpPollingInterval);
            
            // Refresh recent numbers
            loadRecentNumbers();
        }
    } catch (error) {
        console.error('Error checking OTP status:', error);
    }
}

/**
 * Cancel a number request
 */
async function cancelNumber(requestId) {
    if (!confirm('Are you sure you want to cancel this number?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'auth.html';
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/otp/cancel/${requestId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to cancel number');
        }
        
        const data = await response.json();
        
        // Update status in UI
        const statusElement = document.getElementById('number-status');
        if (statusElement) {
            statusElement.textContent = 'cancelled';
            statusElement.className = 'status-badge cancelled';
        }
        
        // Stop polling
        if (window.otpPollingInterval) {
            clearInterval(window.otpPollingInterval);
        }
        
        // Refresh wallet balance (for refund)
        fetchWalletBalance();
        
        // Refresh recent numbers
        loadRecentNumbers();
        
        alert('Number cancelled successfully');
    } catch (error) {
        console.error('Error cancelling number:', error);
        alert(error.message || 'Failed to cancel number. Please try again.');
    }
}

/**
 * Load recent numbers
 */
async function loadRecentNumbers() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'auth.html';
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/otp/history`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch recent numbers');
        }
        
        const data = await response.json();
        
        // Display recent numbers
        displayRecentNumbers(data);
    } catch (error) {
        console.error('Error loading recent numbers:', error);
    }
}

/**
 * Display recent numbers in the table
 */
function displayRecentNumbers(numbers) {
    const tableBody = document.getElementById('recent-numbers');
    const noNumbersMsg = document.getElementById('no-numbers');
    
    if (!tableBody) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    
    if (!numbers || numbers.length === 0) {
        if (noNumbersMsg) {
            noNumbersMsg.style.display = 'block';
        }
        return;
    }
    
    if (noNumbersMsg) {
        noNumbersMsg.style.display = 'none';
    }
    
    // Add number rows
    numbers.forEach(number => {
        const row = document.createElement('tr');
        
        // Format date
        const date = new Date(number.created_at);
        const formattedDate = formatDate(date);
        
        row.innerHTML = `
            <td>${number.service_name || '-'}</td>
            <td>${number.number || '-'}</td>
            <td><span class="status-badge ${number.status}">${number.status}</span></td>
            <td>${number.otp_code || '-'}</td>
            <td>${formattedDate}</td>
            <td>
                ${number.status === 'pending' || number.status === 'active' ? 
                    `<button class="action-btn cancel" onclick="cancelNumber('${number.request_id}')"><i class="fas fa-times"></i></button>` : ''}
                ${number.number ? 
                    `<button class="action-btn" onclick="navigator.clipboard.writeText('${number.number}')"><i class="fas fa-copy"></i></button>` : ''}
                ${number.otp_code ? 
                    `<button class="action-btn" onclick="navigator.clipboard.writeText('${number.otp_code}')"><i class="fas fa-clipboard"></i></button>` : ''}
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}
document.addEventListener('DOMContentLoaded', () => {
    // Switch tabs between login and signup
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));

            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            document.getElementById(target + '-form').classList.add('active');
        });
    });
});

