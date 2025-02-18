// core/index.js
const AppCore = {
  init() {
    this.initializeComponents();
    this.setupEventListeners();
    this.setupAjaxHandlers();
  },

  initializeComponents() {
    // Initialize common components
    this.initializeTooltips();
    this.initializePopovers();
    this.initializeDropdowns();
    this.initializeModals();
    this.initializeAlerts();
  },

  setupEventListeners() {
    document.addEventListener("DOMContentLoaded", () => {
      // Setup global event handlers
    });

    // Handle dynamic content loading
    document.addEventListener("content-loaded", () => {
      this.initializeComponents();
    });
  },

  setupAjaxHandlers() {
    // Setup global AJAX handlers
    axios.interceptors.request.use((config) => {
      // Add CSRF token
      const token = document.querySelector('meta[name="csrf-token"]');
      if (token) {
        config.headers["X-CSRF-TOKEN"] = token.content;
      }
      return config;
    });

    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        this.handleAjaxError(error);
        return Promise.reject(error);
      },
    );
  },

  handleAjaxError(error) {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          this.handleUnauthorized();
          break;
        case 403:
          this.handleForbidden();
          break;
        case 404:
          this.handleNotFound();
          break;
        case 422:
          this.handleValidationError(error.response.data);
          break;
        case 500:
          this.handleServerError();
          break;
        default:
          this.handleGenericError();
      }
    }
  },

  // Utility Methods
  showNotification(message, type = "info") {
    // Implementation for showing notifications
  },

  confirmDialog(options) {
    return new Promise((resolve) => {
      // Implementation for confirmation dialogs
    });
  },

  formatDate(date, format = "YYYY-MM-DD") {
    return dayjs(date).format(format);
  },

  formatNumber(number, options = {}) {
    return new Intl.NumberFormat(undefined, options).format(number);
  },

  formatCurrency(amount, currency = "USD") {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency,
    }).format(amount);
  },
};

export default AppCore;
