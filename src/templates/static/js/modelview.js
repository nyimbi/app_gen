// views/ModelView.js
import AppCore from ".";

class ModelView {
  constructor(options = {}) {
    this.options = {
      ...this.getDefaultOptions(),
      ...options,
    };

    this.initialize();
  }

  getDefaultOptions() {
    return {
      baseUrl: "",
      csrf_token: "",
      permissions: {},
      translations: {},
      formatters: {},
      validators: {},
    };
  }

  initialize() {
    this.setupElements();
    this.setupEventListeners();
    this.initializeComponents();
  }

  setupElements() {
    // Cache commonly used elements
    this.container = document.querySelector(this.options.containerSelector);
    if (!this.container) {
      console.error("Container element not found");
      return;
    }
  }

  setupEventListeners() {
    // Setup common event listeners
    document.addEventListener(
      "content-loaded",
      this.onContentLoaded.bind(this),
    );
  }

  initializeComponents() {
    // Initialize common components
  }

  // CRUD Operations
  async fetchData(params = {}) {
    try {
      const response = await axios.get(this.options.baseUrl, { params });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async saveData(data, method = "POST") {
    try {
      const response = await axios({
        method,
        url: this.options.baseUrl,
        data,
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async deleteData(id) {
    try {
      const confirmed = await AppCore.confirmDialog({
        title: this.options.translations.confirmDelete,
        message: this.options.translations.deleteMessage,
        confirmText: this.options.translations.delete,
        cancelText: this.options.translations.cancel,
        type: "danger",
      });

      if (confirmed) {
        const response = await axios.delete(`${this.options.baseUrl}/${id}`);
        return response.data;
      }
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  // Form Handling
  getFormData(form) {
    const formData = new FormData(form);
    return Object.fromEntries(formData.entries());
  }

  validateForm(form) {
    let isValid = true;
    const errors = {};

    // Get all form fields
    const fields = form.querySelectorAll("input, select, textarea");

    fields.forEach((field) => {
      const validators = this.options.validators[field.name];
      if (validators) {
        const fieldErrors = this.validateField(field, validators);
        if (fieldErrors.length) {
          errors[field.name] = fieldErrors;
          isValid = false;
        }
      }
    });

    return { isValid, errors };
  }

  validateField(field, validators) {
    const errors = [];
    validators.forEach((validator) => {
      const error = validator(field.value, field);
      if (error) errors.push(error);
    });
    return errors;
  }

  showFieldError(field, error) {
    const errorElement = document.createElement("div");
    errorElement.className = "field-error";
    errorElement.textContent = error;

    const existingError = field.parentElement.querySelector(".field-error");
    if (existingError) {
      existingError.remove();
    }

    field.classList.add("is-invalid");
    field.parentElement.appendChild(errorElement);
  }

  clearFieldErrors() {
    this.container
      .querySelectorAll(".field-error")
      .forEach((error) => error.remove());
    this.container.querySelectorAll(".is-invalid").forEach((field) => {
      field.classList.remove("is-invalid");
    });
  }

  // Error Handling
  handleError(error) {
    if (error.response) {
      if (error.response.status === 422) {
        this.handleValidationErrors(error.response.data.errors);
      } else {
        AppCore.showNotification(
          error.response.data.message || this.options.translations.genericError,
          "error",
        );
      }
    } else {
      AppCore.showNotification(this.options.translations.networkError, "error");
    }
  }

  handleValidationErrors(errors) {
    Object.entries(errors).forEach(([field, messages]) => {
      const fieldElement = this.container.querySelector(`[name="${field}"]`);
      if (fieldElement) {
        this.showFieldError(fieldElement, messages[0]);
      }
    });
  }

  // Utility Methods
  formatValue(value, type) {
    const formatter = this.options.formatters[type];
    return formatter ? formatter(value) : value;
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Event Handlers
  onContentLoaded() {
    this.initializeComponents();
  }
}

export default ModelView;
