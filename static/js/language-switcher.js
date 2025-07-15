// Enhanced Language Switcher Component for BhashAI Platform
// Supports 20+ languages with smooth transitions and accessibility

class LanguageSwitcher {
    constructor(options = {}) {
        this.options = {
            selector: '.language-switcher',
            showFlags: true,
            showNativeNames: true,
            animationDuration: 300,
            position: 'top-right',
            ...options
        };
        
        this.currentLanguage = localStorage.getItem('bhashaiLanguage') || 'en';
        this.isOpen = false;
        this.init();
    }

    init() {
        this.createSwitcher();
        this.bindEvents();
        this.updateContent();
    }

    createSwitcher() {
        const switcher = document.createElement('div');
        switcher.className = 'language-switcher-container';
        switcher.innerHTML = this.generateSwitcherHTML();
        
        // Add styles
        this.addStyles();
        
        // Find target container or create one
        let container = document.querySelector(this.options.selector);
        if (!container) {
            container = document.createElement('div');
            container.className = 'language-switcher';
            document.body.appendChild(container);
        }
        
        container.appendChild(switcher);
        this.container = container;
        this.switcher = switcher;
    }

    generateSwitcherHTML() {
        const currentLang = SUPPORTED_LANGUAGES[this.currentLanguage];
        
        return `
            <div class="language-switcher-trigger" role="button" tabindex="0" aria-label="Select Language">
                <span class="current-language">
                    ${this.options.showFlags ? currentLang.flag : ''}
                    <span class="language-name">${this.options.showNativeNames ? currentLang.nativeName : currentLang.name}</span>
                    <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 12 12">
                        <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="2" fill="none"/>
                    </svg>
                </span>
            </div>
            <div class="language-switcher-dropdown" role="menu">
                <div class="language-search">
                    <input type="text" placeholder="Search languages..." class="language-search-input" />
                </div>
                <div class="language-options">
                    ${this.generateLanguageOptions()}
                </div>
            </div>
        `;
    }

    generateLanguageOptions() {
        return Object.entries(SUPPORTED_LANGUAGES)
            .map(([code, lang]) => {
                const isActive = code === this.currentLanguage;
                return `
                    <div class="language-option ${isActive ? 'active' : ''}" 
                         data-lang="${code}" 
                         role="menuitem" 
                         tabindex="0">
                        ${this.options.showFlags ? `<span class="flag">${lang.flag}</span>` : ''}
                        <span class="native-name">${lang.nativeName}</span>
                        <span class="english-name">${lang.name}</span>
                        ${isActive ? '<span class="checkmark">✓</span>' : ''}
                    </div>
                `;
            })
            .join('');
    }

    addStyles() {
        if (document.getElementById('language-switcher-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'language-switcher-styles';
        styles.textContent = `
            .language-switcher-container {
                position: relative;
                display: inline-block;
                font-family: 'Inter', sans-serif;
                z-index: 10002;
            }

            .language-switcher-trigger {
                display: flex;
                align-items: center;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                color: white;
                min-width: 120px;
            }

            .language-switcher-trigger:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
                transform: translateY(-1px);
            }

            .language-switcher-trigger:focus {
                outline: 2px solid #4f46e5;
                outline-offset: 2px;
            }

            .current-language {
                display: flex;
                align-items: center;
                gap: 8px;
                width: 100%;
                justify-content: space-between;
            }

            .language-name {
                font-size: 14px;
                font-weight: 500;
            }

            .dropdown-arrow {
                transition: transform 0.3s ease;
                opacity: 0.7;
            }

            .language-switcher-container.open .dropdown-arrow {
                transform: rotate(180deg);
            }

            .language-switcher-dropdown {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                opacity: 0;
                visibility: hidden;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                max-height: 400px;
                overflow: hidden;
                margin-top: 4px;
                min-width: 280px;
                z-index: 10003;
            }

            .language-switcher-container.open .language-switcher-dropdown {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }

            .language-search {
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
            }

            .language-search-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s ease;
            }

            .language-search-input:focus {
                border-color: #4f46e5;
            }

            .language-options {
                max-height: 300px;
                overflow-y: auto;
                padding: 8px 0;
            }

            .language-option {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 16px;
                cursor: pointer;
                transition: all 0.2s ease;
                border-left: 3px solid transparent;
            }

            .language-option:hover {
                background: #f8fafc;
                border-left-color: #4f46e5;
            }

            .language-option.active {
                background: #f0f9ff;
                border-left-color: #0ea5e9;
                color: #0ea5e9;
            }

            .language-option:focus {
                outline: none;
                background: #f8fafc;
                border-left-color: #4f46e5;
            }

            .language-option .flag {
                font-size: 18px;
                width: 24px;
                text-align: center;
            }

            .language-option .native-name {
                font-weight: 500;
                font-size: 14px;
                min-width: 100px;
            }

            .language-option .english-name {
                font-size: 12px;
                color: #64748b;
                margin-left: auto;
            }

            .language-option .checkmark {
                color: #10b981;
                font-weight: bold;
                margin-left: auto;
            }

            .language-option.hidden {
                display: none;
            }

            /* RTL Support */
            [dir="rtl"] .language-switcher-dropdown {
                left: auto;
                right: 0;
            }

            [dir="rtl"] .current-language {
                flex-direction: row-reverse;
            }

            [dir="rtl"] .language-option {
                flex-direction: row-reverse;
                border-left: none;
                border-right: 3px solid transparent;
            }

            [dir="rtl"] .language-option:hover,
            [dir="rtl"] .language-option.active,
            [dir="rtl"] .language-option:focus {
                border-left: none;
                border-right-color: #4f46e5;
            }

            /* Mobile Responsive */
            @media (max-width: 768px) {
                .language-switcher-dropdown {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    right: auto;
                    transform: translate(-50%, -50%);
                    width: 90vw;
                    max-width: 400px;
                    max-height: 70vh;
                }

                .language-switcher-container.open .language-switcher-dropdown {
                    transform: translate(-50%, -50%);
                }
            }

            /* Animation for language change */
            .language-change-animation {
                animation: languageChange 0.5s ease;
            }

            @keyframes languageChange {
                0% { opacity: 1; }
                50% { opacity: 0.5; transform: scale(0.98); }
                100% { opacity: 1; transform: scale(1); }
            }

            /* Loading state */
            .language-switcher-loading {
                pointer-events: none;
                opacity: 0.7;
            }

            .language-switcher-loading::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 16px;
                height: 16px;
                border: 2px solid #4f46e5;
                border-top: 2px solid transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                transform: translate(-50%, -50%);
            }

            @keyframes spin {
                to { transform: translate(-50%, -50%) rotate(360deg); }
            }
        `;
        
        document.head.appendChild(styles);
    }

    bindEvents() {
        const trigger = this.switcher.querySelector('.language-switcher-trigger');
        const dropdown = this.switcher.querySelector('.language-switcher-dropdown');
        const searchInput = this.switcher.querySelector('.language-search-input');
        const options = this.switcher.querySelectorAll('.language-option');

        // Toggle dropdown
        trigger.addEventListener('click', () => this.toggleDropdown());
        trigger.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleDropdown();
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.switcher.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Search functionality
        searchInput.addEventListener('input', (e) => this.filterLanguages(e.target.value));

        // Language selection
        options.forEach(option => {
            option.addEventListener('click', () => {
                const langCode = option.dataset.lang;
                this.changeLanguage(langCode);
            });

            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const langCode = option.dataset.lang;
                    this.changeLanguage(langCode);
                }
            });
        });

        // Keyboard navigation
        dropdown.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
    }

    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        this.switcher.classList.add('open');
        this.isOpen = true;
        
        // Focus search input
        setTimeout(() => {
            const searchInput = this.switcher.querySelector('.language-search-input');
            searchInput.focus();
        }, 100);
    }

    closeDropdown() {
        this.switcher.classList.remove('open');
        this.isOpen = false;
        
        // Clear search
        const searchInput = this.switcher.querySelector('.language-search-input');
        searchInput.value = '';
        this.filterLanguages('');
    }

    filterLanguages(query) {
        const options = this.switcher.querySelectorAll('.language-option');
        const searchTerm = query.toLowerCase();

        options.forEach(option => {
            const nativeName = option.querySelector('.native-name').textContent.toLowerCase();
            const englishName = option.querySelector('.english-name').textContent.toLowerCase();
            
            if (nativeName.includes(searchTerm) || englishName.includes(searchTerm)) {
                option.classList.remove('hidden');
            } else {
                option.classList.add('hidden');
            }
        });
    }

    handleKeyboardNavigation(e) {
        const visibleOptions = Array.from(this.switcher.querySelectorAll('.language-option:not(.hidden)'));
        const currentFocus = document.activeElement;
        const currentIndex = visibleOptions.indexOf(currentFocus);

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % visibleOptions.length;
                visibleOptions[nextIndex].focus();
                break;
            case 'ArrowUp':
                e.preventDefault();
                const prevIndex = currentIndex <= 0 ? visibleOptions.length - 1 : currentIndex - 1;
                visibleOptions[prevIndex].focus();
                break;
            case 'Escape':
                this.closeDropdown();
                this.switcher.querySelector('.language-switcher-trigger').focus();
                break;
        }
    }

    async changeLanguage(langCode) {
        if (langCode === this.currentLanguage) {
            this.closeDropdown();
            return;
        }

        // Show loading state
        this.switcher.classList.add('language-switcher-loading');

        try {
            // Change language using the language manager
            if (window.languageManager) {
                const success = window.languageManager.changeLanguage(langCode);
                if (success) {
                    this.currentLanguage = langCode;
                    this.updateContent();
                    
                    // Add animation to page
                    document.body.classList.add('language-change-animation');
                    setTimeout(() => {
                        document.body.classList.remove('language-change-animation');
                    }, 500);
                    
                    // Show success notification
                    this.showNotification(`Language changed to ${SUPPORTED_LANGUAGES[langCode].nativeName}`);
                }
            }
        } catch (error) {
            console.error('Error changing language:', error);
            this.showNotification('Error changing language', 'error');
        } finally {
            // Remove loading state
            this.switcher.classList.remove('language-switcher-loading');
            this.closeDropdown();
        }
    }

    updateContent() {
        // Update the trigger display
        const currentLang = SUPPORTED_LANGUAGES[this.currentLanguage];
        const trigger = this.switcher.querySelector('.current-language');
        
        trigger.innerHTML = `
            ${this.options.showFlags ? currentLang.flag : ''}
            <span class="language-name">${this.options.showNativeNames ? currentLang.nativeName : currentLang.name}</span>
            <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 12 12">
                <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
        `;

        // Update active state in dropdown
        const options = this.switcher.querySelectorAll('.language-option');
        options.forEach(option => {
            const isActive = option.dataset.lang === this.currentLanguage;
            option.classList.toggle('active', isActive);
            
            const checkmark = option.querySelector('.checkmark');
            if (checkmark) checkmark.remove();
            
            if (isActive) {
                option.insertAdjacentHTML('beforeend', '<span class="checkmark">✓</span>');
            }
        });
    }

    showNotification(message, type = 'success') {
        // Remove existing notification
        const existing = document.querySelector('.language-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `language-notification ${type}`;
        notification.textContent = message;
        
        const bgColor = type === 'error' ? '#ef4444' : '#10b981';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10004;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
        `;

        // Add slide in animation
        const slideInKeyframes = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        
        if (!document.getElementById('notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = slideInKeyframes;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    // Public API methods
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getSupportedLanguages() {
        return SUPPORTED_LANGUAGES;
    }

    destroy() {
        if (this.container) {
            this.container.remove();
        }
        
        const styles = document.getElementById('language-switcher-styles');
        if (styles) styles.remove();
    }
}

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.languageSwitcher = new LanguageSwitcher();
    });
} else {
    window.languageSwitcher = new LanguageSwitcher();
}

// Export for manual initialization
window.LanguageSwitcher = LanguageSwitcher;
