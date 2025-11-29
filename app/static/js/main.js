/**
 * Solio - Main JavaScript
 * General UI functionality
 */

// ============================================
// DOM Ready
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initUserMenu();
    initFlashMessages();
    initModals();
});

// ============================================
// Navigation
// ============================================
function initNavigation() {
    const navbar = document.querySelector('.navbar');
    const navbarToggle = document.getElementById('navbarToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    // Scroll effect for navbar
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Check initial state
    }

    if (navbarToggle && mobileMenu) {
        navbarToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');
            navbarToggle.classList.toggle('active');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !navbarToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
                navbarToggle.classList.remove('active');
            }
        });
    }
}

// ============================================
// User Menu
// ============================================
function initUserMenu() {
    const userMenuTrigger = document.getElementById('userMenuTrigger');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuTrigger && userDropdown) {
        userMenuTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenuTrigger.parentElement.classList.toggle('active');
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!userMenuTrigger.contains(e.target) && !userDropdown.contains(e.target)) {
                userMenuTrigger.parentElement.classList.remove('active');
            }
        });
    }
}

// ============================================
// Flash Messages
// ============================================
function initFlashMessages() {
    document.querySelectorAll('.flash-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const flash = btn.closest('.flash');
            flash.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => flash.remove(), 300);
        });
    });

    // Auto-dismiss after 5 seconds
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            if (flash.parentElement) {
                flash.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => flash.remove(), 300);
            }
        }, 5000);
    });
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================
// Modals
// ============================================
function initModals() {
    // Connect wallet button opens modal
    const connectWalletBtn = document.getElementById('connectWalletBtn');
    const walletModal = document.getElementById('walletModal');

    if (connectWalletBtn && walletModal) {
        connectWalletBtn.addEventListener('click', () => {
            walletModal.classList.add('active');
        });
    }

    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        const backdrop = modal.querySelector('.modal-backdrop');
        const closeBtn = modal.querySelector('.modal-close');

        if (backdrop) {
            backdrop.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
            });
        }
    });
}

// ============================================
// Toast Notifications
// ============================================
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Make globally available
window.showToast = showToast;

// ============================================
// Loading Overlay
// ============================================
function showLoading(text = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    if (overlay) {
        if (loadingText) loadingText.textContent = text;
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    if (overlay) {
        overlay.classList.remove('active');
        if (loadingText) loadingText.textContent = 'Loading...';
    }
}

window.showLoading = showLoading;
window.hideLoading = hideLoading;

// ============================================
// Transaction Progress Modal
// ============================================
const txProgressSteps = ['prepare', 'sign', 'send', 'confirm', 'verify'];
let currentTxStep = -1;

function showTxProgress() {
    const modal = document.getElementById('txProgressModal');
    if (modal) {
        // Reset all steps
        txProgressSteps.forEach(step => {
            const stepEl = modal.querySelector(`[data-step="${step}"]`);
            if (stepEl) {
                stepEl.classList.remove('active', 'completed', 'error');
            }
        });
        // Hide signature
        const sigEl = document.getElementById('txSignature');
        if (sigEl) sigEl.style.display = 'none';

        currentTxStep = -1;
        modal.classList.add('active');
    }
}

function hideTxProgress() {
    const modal = document.getElementById('txProgressModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function setTxStep(stepName, status = 'active') {
    const modal = document.getElementById('txProgressModal');
    if (!modal) return;

    const stepIndex = txProgressSteps.indexOf(stepName);

    // Mark previous steps as completed
    txProgressSteps.forEach((step, index) => {
        const stepEl = modal.querySelector(`[data-step="${step}"]`);
        if (!stepEl) return;

        stepEl.classList.remove('active', 'completed', 'error');

        if (index < stepIndex) {
            stepEl.classList.add('completed');
        } else if (index === stepIndex) {
            stepEl.classList.add(status);
        }
    });

    currentTxStep = stepIndex;
}

function setTxSignature(signature, isDevnet = false) {
    const sigEl = document.getElementById('txSignature');
    const linkEl = document.getElementById('txSignatureLink');
    if (sigEl && linkEl) {
        const baseUrl = isDevnet
            ? 'https://solscan.io/tx/' + signature + '?cluster=devnet'
            : 'https://solscan.io/tx/' + signature;
        linkEl.href = baseUrl;
        sigEl.style.display = 'flex';
    }
}

function setTxError(stepName) {
    setTxStep(stepName, 'error');
}

window.showTxProgress = showTxProgress;
window.hideTxProgress = hideTxProgress;
window.setTxStep = setTxStep;
window.setTxSignature = setTxSignature;
window.setTxError = setTxError;

// ============================================
// CSRF Token Helper
// ============================================
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

window.getCsrfToken = getCsrfToken;

// ============================================
// Fetch Helper with CSRF
// ============================================
async function fetchWithCsrf(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    return fetch(url, mergedOptions);
}

window.fetchWithCsrf = fetchWithCsrf;

// ============================================
// Format Helpers
// ============================================
function formatSOL(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return '0';

    if (num >= 1) {
        return num.toLocaleString('cs-CZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (num >= 0.01) {
        return num.toFixed(4);
    } else {
        return num.toFixed(9).replace(/0+$/, '').replace(/\.$/, '');
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('cs-CZ', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateWallet(address, chars = 4) {
    if (!address || address.length < chars * 2) return address;
    return `${address.slice(0, chars)}...${address.slice(-chars)}`;
}

window.formatSOL = formatSOL;
window.formatDate = formatDate;
window.truncateWallet = truncateWallet;
