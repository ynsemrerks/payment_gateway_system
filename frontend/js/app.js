const API_URL = 'http://localhost:8000/api/v1';

// State
const state = {
    user: null,
    apiKey: null,
    email: null
};

// Utils
const $ = (selector) => document.querySelector(selector);
const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
const formatDate = (dateString) => new Date(dateString).toLocaleString();

// Auth Logic
function checkAuth() {
    const userId = localStorage.getItem('pg_user_id');
    const apiKey = localStorage.getItem('pg_api_key');
    const email = localStorage.getItem('pg_email');

    if (!userId || !apiKey) {
        if (!window.location.href.includes('login.html')) {
            window.location.href = 'login.html';
        }
        return false;
    }

    state.user = { id: userId };
    state.apiKey = apiKey;
    state.email = email;

    // Update Navbar if exists
    const userDisplay = document.querySelector('.dropdown-toggle');
    if (userDisplay) {
        userDisplay.innerHTML = `<i class="fas fa-user-circle fa-lg me-1"></i> ${email || 'User'}`;
    }

    // Show API Key in a small element if it exists or create one
    // (Optional: can be added to the dropdown or somewhere else)

    return true;
}

async function login(username, password) {
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();

        localStorage.setItem('pg_user_id', data.user_id);
        localStorage.setItem('pg_api_key', data.api_key);
        localStorage.setItem('pg_email', data.email);
        window.location.href = 'index.html';
    } catch (error) {
        alert(error.message);
    }
}

function logout() {
    localStorage.removeItem('pg_user_id');
    localStorage.removeItem('pg_api_key');
    localStorage.removeItem('pg_email');
    window.location.href = 'login.html';
}

// API Calls
async function fetchWithAuth(endpoint, options = {}) {
    // Generate UUID for Idempotency-Key
    const uuid = crypto.randomUUID();

    const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': state.apiKey,
        'Idempotency-Key': uuid,
        ...options.headers
    };

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401 || response.status === 403) {
            alert('Session expired or invalid credentials. Please login again.');
            logout();
            return null;
        }

        if (!response.ok) {
            const error = await response.json();
            // Check if detail is an object (common in this app) or string
            let errorMessage = 'API Error';
            if (error.detail) {
                if (typeof error.detail === 'object' && error.detail.message) {
                    errorMessage = error.detail.message;
                } else {
                    errorMessage = error.detail;
                }
            }
            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        alert(`Error: ${error.message}`);
        return null;
    }
}

// Data Fetching
async function fetchBalance() {
    const data = await fetchWithAuth(`/users/${state.user.id}/balance`);
    if (data) {
        $('#balance-amount').textContent = formatCurrency(data.balance);
    }
}

async function fetchTransactions(type = null) {
    const typeParam = type ? `&type=${type}` : '';
    const data = await fetchWithAuth(`/users/${state.user.id}/transactions?limit=10${typeParam}`);
    if (data && data.items) {
        const list = $('#transaction-list');
        list.innerHTML = data.items.map(tx => `
            <a href="transaction-detail.html?type=${tx.type}&id=${tx.id}" class="text-decoration-none">
                <div class="transaction-item p-3 d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold ${tx.type === 'deposit' ? 'text-success' : 'text-danger'}">
                            ${tx.type === 'deposit' ? '↓ Deposit' : '↑ Withdrawal'}
                        </div>
                        <small class="text-white">${formatDate(tx.created_at)}</small>
                        <div class="small text-white">Ref: ${tx.bank_reference || 'Pending...'}</div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-white">${formatCurrency(tx.amount)}</div>
                        <span class="badge ${getStatusBadgeClass(tx.status)}">${tx.status}</span>
                    </div>
                </div>
            </a>
        `).join('');

        // Smart Polling Logic
        const hasPending = data.items.some(tx => tx.status === 'pending' || tx.status === 'processing');
        if (hasPending) {
            // Poll faster if pending
            setTimeout(() => {
                fetchBalance();
                fetchTransactions();
            }, 2000);
        }
    }
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'success': return 'badge-success';
        case 'pending': case 'processing': return 'badge-pending';
        case 'failed': return 'badge-failed';
        default: return 'bg-secondary';
    }
}

async function fetchTransactionDetail(type, id) {
    const endpoint = type === 'deposit' ? `/deposits/${id}` : `/withdrawals/${id}`;
    const tx = await fetchWithAuth(endpoint);

    if (tx) {
        // Update UI
        $('#detail-type-title').textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Details`;
        $('#detail-id-display').textContent = `ID: #${tx.id}`;

        const badge = $('#detail-status-badge');
        badge.textContent = tx.status;
        badge.className = `badge fs-6 px-3 py-2 ${getStatusBadgeClass(tx.status)}`;

        $('#detail-amount').textContent = formatCurrency(tx.amount);
        $('#detail-date').textContent = formatDate(tx.created_at);
        $('#detail-bank-ref').textContent = tx.bank_reference || 'Pending...';
        $('#detail-service-type').textContent = tx.type;

        if (tx.error_message) {
            $('#error-message-container').style.display = 'block';
            $('#detail-error-message').textContent = tx.error_message;
        }

        // Auto Refresh if pending
        if (tx.status === 'pending' || tx.status === 'processing') {
            setTimeout(() => fetchTransactionDetail(type, id), 3000);
        }
    }
}

// Actions
async function handleTransaction(type, amount) {
    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
        return;
    }

    const endpoint = type === 'deposit' ? '/deposits' : '/withdrawals';

    // Show loading
    const btn = $(`#btn-confirm-${type}`);
    const originalText = btn.textContent;
    btn.textContent = 'Processing...';
    btn.disabled = true;

    const result = await fetchWithAuth(endpoint, {
        method: 'POST',
        body: JSON.stringify({ amount: parseFloat(amount) })
    });

    // Reset button
    btn.textContent = originalText;
    btn.disabled = false;

    if (result) {
        // Close modal (using Bootstrap 5 vanilla JS)
        const modalEl = document.getElementById(`${type}Modal`);
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();

        // Reset form
        $(`#${type}-amount`).value = '0.00';

        alert(`${type.charAt(0).toUpperCase() + type.slice(1)} initiated successfully!`);

        // Refresh data
        fetchBalance();
        fetchTransactions();
    }
}

// Currency Input Logic
function setupCurrencyInput(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('focus', () => {
        if (input.value === '0.00') {
            // Select only the '0' part so typing replaces it
            input.setSelectionRange(0, 1);
        }
    });

    input.addEventListener('blur', () => {
        if (!input.value) {
            input.value = '0.00';
            return;
        }
        // Ensure 2 decimals
        const val = parseFloat(input.value.replace(/[^0-9.]/g, ''));
        if (!isNaN(val)) {
            input.value = val.toFixed(2);
        } else {
            input.value = '0.00';
        }
    });

    input.addEventListener('input', (e) => {
        // Allow ONLY digits and ONE dot
        let val = input.value.replace(/[^0-9.]/g, '');
        const parts = val.split('.');
        if (parts.length > 2) {
            val = parts[0] + '.' + parts.slice(1).join('');
        }
        if (input.value !== val) {
            input.value = val;
        }
    });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('login.html')) {
        // Login Page Logic
        $('#login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = $('#username').value;
            const password = $('#password').value;
            const btn = e.target.querySelector('button');

            const originalText = btn.textContent;
            btn.textContent = 'Logging in...';
            btn.disabled = true;

            await login(username, password);

            btn.textContent = originalText;
            btn.disabled = false;
        });
    } else if (window.location.pathname.endsWith('transaction-detail.html')) {
        if (checkAuth()) {
            const params = new URLSearchParams(window.location.search);
            const type = params.get('type');
            const id = params.get('id');

            if (!type || !id) {
                window.location.href = 'index.html';
                return;
            }

            fetchTransactionDetail(type, id);
        }
    } else {
        // Dashboard Logic
        if (checkAuth()) {
            const path = window.location.pathname;

            if (path.endsWith('deposits.html')) {
                fetchBalance();
                fetchTransactions('deposit');
                setInterval(() => {
                    const list = $('#transaction-list');
                    if (!list.innerHTML.includes('pending') && !list.innerHTML.includes('processing')) {
                        fetchBalance();
                        fetchTransactions('deposit');
                    }
                }, 30000);
            } else if (path.endsWith('withdrawals.html')) {
                fetchBalance();
                fetchTransactions('withdrawal');
                setInterval(() => {
                    const list = $('#transaction-list');
                    if (!list.innerHTML.includes('pending') && !list.innerHTML.includes('processing')) {
                        fetchBalance();
                        fetchTransactions('withdrawal');
                    }
                }, 30000);
            } else {
                fetchBalance();
                fetchTransactions();
                setInterval(() => {
                    const list = $('#transaction-list');
                    if (!list.innerHTML.includes('pending') && !list.innerHTML.includes('processing')) {
                        fetchBalance();
                        fetchTransactions();
                    }
                }, 30000);
            }

            // Reset inputs on Modal Show
            const depositModal = document.getElementById('depositModal');
            depositModal.addEventListener('shown.bs.modal', () => {
                const input = $('#deposit-amount');
                input.value = '0.00';
                input.focus();
                // Select integer part for easy typing
                input.setSelectionRange(0, 1);
            });

            const withdrawalModal = document.getElementById('withdrawalModal');
            withdrawalModal.addEventListener('shown.bs.modal', () => {
                const input = $('#withdrawal-amount');
                input.value = '0.00';
                input.focus();
                input.setSelectionRange(0, 1);
            });

            // Event Listeners for Modals
            $('#btn-confirm-deposit').addEventListener('click', () => {
                handleTransaction('deposit', $('#deposit-amount').value);
            });

            $('#btn-confirm-withdrawal').addEventListener('click', () => {
                handleTransaction('withdrawal', $('#withdrawal-amount').value);
            });

            $('#logout-btn').addEventListener('click', (e) => {
                e.preventDefault();
                logout();
            });
        }
    }
});
