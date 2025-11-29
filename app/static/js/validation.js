/**
 * Real-time Form Validation
 * Provides instant feedback as users fill out forms
 */

// Validation rules
const validators = {
    required: (value) => {
        return value.trim().length > 0 ? null : 'This field is required';
    },

    email: (value) => {
        if (!value.trim()) return null; // Let required handle empty
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value) ? null : 'Please enter a valid email address';
    },

    minLength: (min) => (value) => {
        if (!value.trim()) return null;
        return value.trim().length >= min ? null : `Must be at least ${min} characters`;
    },

    maxLength: (max) => (value) => {
        return value.length <= max ? null : `Must be no more than ${max} characters`;
    },

    url: (value) => {
        if (!value.trim()) return null;
        try {
            new URL(value);
            return null;
        } catch {
            return 'Please enter a valid URL';
        }
    },

    solAmount: (value) => {
        if (!value) return null;
        const num = parseFloat(value);
        if (isNaN(num)) return 'Please enter a valid number';
        if (num < 0.001) return 'Minimum amount is 0.001 SOL';
        if (num > 1000000) return 'Maximum amount is 1,000,000 SOL';
        return null;
    },

    futureDate: (value) => {
        if (!value) return null;
        const date = new Date(value);
        const now = new Date();
        return date > now ? null : 'Date must be in the future';
    },

    match: (fieldId, fieldName) => (value, form) => {
        const matchField = form.querySelector(`#${fieldId}`);
        if (!matchField) return null;
        return value === matchField.value ? null : `Must match ${fieldName}`;
    },

    password: (value) => {
        if (!value) return null;
        if (value.length < 8) return 'Password must be at least 8 characters';
        return null;
    },

    username: (value) => {
        if (!value.trim()) return null;
        if (value.length < 3) return 'Username must be at least 3 characters';
        if (value.length > 30) return 'Username must be no more than 30 characters';
        if (!/^[a-zA-Z0-9_]+$/.test(value)) return 'Username can only contain letters, numbers, and underscores';
        return null;
    },

    walletAddress: (value) => {
        if (!value.trim()) return null;
        // Solana addresses are base58 encoded and typically 32-44 characters
        if (value.length < 32 || value.length > 44) return 'Invalid Solana wallet address';
        if (!/^[1-9A-HJ-NP-Za-km-z]+$/.test(value)) return 'Invalid Solana wallet address format';
        return null;
    }
};

// Create validation instance for a form
class FormValidator {
    constructor(formSelector, rules) {
        this.form = document.querySelector(formSelector);
        this.rules = rules;
        this.errors = {};

        if (!this.form) return;

        this.init();
    }

    init() {
        // Add validation on blur and input
        Object.keys(this.rules).forEach(fieldId => {
            const field = this.form.querySelector(`#${fieldId}`);
            if (!field) return;

            // Validate on blur
            field.addEventListener('blur', () => this.validateField(fieldId));

            // Validate on input (with debounce)
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => this.validateField(fieldId), 300);
            });
        });

        // Validate all fields on submit
        this.form.addEventListener('submit', (e) => {
            let hasErrors = false;
            Object.keys(this.rules).forEach(fieldId => {
                const error = this.validateField(fieldId);
                if (error) hasErrors = true;
            });

            if (hasErrors) {
                e.preventDefault();
                // Scroll to first error
                const firstError = this.form.querySelector('.validation-error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    validateField(fieldId) {
        const field = this.form.querySelector(`#${fieldId}`);
        if (!field) return null;

        const fieldRules = this.rules[fieldId];
        let error = null;

        // Run through each validator
        for (const rule of fieldRules) {
            if (typeof rule === 'function') {
                error = rule(field.value, this.form);
            }
            if (error) break;
        }

        this.setFieldError(field, error);
        this.errors[fieldId] = error;

        return error;
    }

    setFieldError(field, error) {
        const wrapper = field.closest('.form-group');
        if (!wrapper) return;

        // Remove existing error
        const existingError = wrapper.querySelector('.validation-error');
        if (existingError) existingError.remove();

        // Remove error class
        field.classList.remove('input-error');
        wrapper.classList.remove('has-error');

        if (error) {
            // Add error class
            field.classList.add('input-error');
            wrapper.classList.add('has-error');

            // Add error message
            const errorEl = document.createElement('span');
            errorEl.className = 'validation-error';
            errorEl.textContent = error;
            wrapper.appendChild(errorEl);
        }
    }

    isValid() {
        return Object.values(this.errors).every(e => e === null);
    }
}

// Initialize validation on common forms
document.addEventListener('DOMContentLoaded', () => {
    // Registration form
    if (document.querySelector('#registerForm')) {
        new FormValidator('#registerForm', {
            'username': [validators.required, validators.username],
            'email': [validators.required, validators.email],
            'password': [validators.required, validators.password],
            'confirm_password': [validators.required, validators.match('password', 'password')]
        });
    }

    // Login form
    if (document.querySelector('#loginForm')) {
        new FormValidator('#loginForm', {
            'email': [validators.required, validators.email],
            'password': [validators.required]
        });
    }

    // Project create form
    if (document.querySelector('.project-form')) {
        new FormValidator('.project-form', {
            'title': [validators.required, validators.minLength(3), validators.maxLength(100)],
            'goal_sol': [validators.required, validators.solAmount],
            'end_date': [validators.required, validators.futureDate],
            'video_url': [validators.url],
            'project_website': [validators.url],
            'project_twitter': [validators.url],
            'project_telegram': [validators.url],
            'project_github': [validators.url],
            'project_discord': [validators.url],
            'project_linkedin': [validators.url],
            'project_youtube': [validators.url]
        });
    }

    // Profile edit form
    if (document.querySelector('#profileEditForm')) {
        new FormValidator('#profileEditForm', {
            'username': [validators.required, validators.username],
            'wallet_address': [validators.walletAddress],
            'twitter_url': [validators.url],
            'telegram_url': [validators.url],
            'discord_url': [validators.url],
            'website_url': [validators.url],
            'github_url': [validators.url],
            'linkedin_url': [validators.url],
            'youtube_url': [validators.url]
        });
    }

    // Password reset form
    if (document.querySelector('#resetPasswordForm')) {
        new FormValidator('#resetPasswordForm', {
            'password': [validators.required, validators.password],
            'confirm_password': [validators.required, validators.match('password', 'password')]
        });
    }

    // Forgot password form
    if (document.querySelector('#forgotPasswordForm')) {
        new FormValidator('#forgotPasswordForm', {
            'email': [validators.required, validators.email]
        });
    }
});

// Export for manual use
window.FormValidator = FormValidator;
window.validators = validators;
