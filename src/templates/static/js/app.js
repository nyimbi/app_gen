// app.js

// Core Utilities and Helpers
const Utils = {
  // Date formatting
  formatDate(date, format = "YYYY-MM-DD") {
    return dayjs(date).format(format);
  },

  // Number formatting
  formatNumber(number, options = {}) {
    return new Intl.NumberFormat(undefined, options).format(number);
  },

  // Currency formatting
  formatCurrency(amount, currency = "USD") {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency,
    }).format(amount);
  },

  // Debounce function
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
  },

  // Deep clone object
  deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  },

  // Generate unique ID
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  },

  // Validation helpers
  validators: {
    required(value) {
      return value && value.toString().trim() !== ""
        ? null
        : "This field is required";
    },
    email(value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
        ? null
        : "Invalid email format";
    },
    minLength(length) {
      return (value) =>
        value.length >= length ? null : `Minimum length is ${length}`;
    },
    maxLength(length) {
      return (value) =>
        value.length <= length ? null : `Maximum length is ${length}`;
    },
    numeric(value) {
      return !isNaN(value) ? null : "Must be a number";
    },
    url(value) {
      try {
        new URL(value);
        return null;
      } catch {
        return "Invalid URL format";
      }
    },
  },
};

// Event Bus for component communication
const EventBus = {
  listeners: {},

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  },

  off(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(
      (listener) => listener !== callback,
    );
  },

  emit(event, data) {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach((callback) => callback(data));
  },
};

// Base View Class
class BaseView {
  constructor(options = {}) {
    this.options = {
      ...this.getDefaultOptions(),
      ...options,
    };

    this.initialize();
  }

  getDefaultOptions() {
    return {
      container: null,
      baseUrl: "",
      csrf_token: "",
      permissions: {},
      translations: {},
      formatters: {},
      validators: {},
    };
  }

  initialize() {
    if (!this.options.container) {
      console.error("No container specified for view");
      return;
    }

    this.setupElements();
    this.setupEventListeners();
    this.initializeComponents();
  }

  setupElements() {
    this.container =
      typeof this.options.container === "string"
        ? document.querySelector(this.options.container)
        : this.options.container;

    if (!this.container) {
      console.error("Container element not found");
      return;
    }
  }

  setupEventListeners() {
    // Virtual method to be implemented by child classes
  }

  initializeComponents() {
    // Virtual method to be implemented by child classes
  }

  destroy() {
    // Cleanup method to be called when view is destroyed
    this.removeEventListeners();
    this.destroyComponents();
  }

  removeEventListeners() {
    // Virtual method to be implemented by child classes
  }

  destroyComponents() {
    // Virtual method to be implemented by child classes
  }

  // AJAX Helpers
  async fetchData(url, params = {}) {
    try {
      const response = await axios.get(url, {
        params,
        headers: this._getHeaders(),
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async postData(url, data) {
    try {
      const response = await axios.post(url, data, {
        headers: this._getHeaders(),
      });
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  _getHeaders() {
    return {
      "X-CSRF-TOKEN": this.options.csrf_token,
      Accept: "application/json",
      "Content-Type": "application/json",
    };
  }

  // Error Handling
  handleError(error) {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          this.handleUnauthorized();
          break;
        case 403:
          this.handleForbidden();
          break;
        case 422:
          this.handleValidationError(error.response.data.errors);
          break;
        default:
          this.handleGenericError();
      }
    } else {
      this.handleNetworkError();
    }
  }

  handleUnauthorized() {
    window.location.href = "/login";
  }

  handleForbidden() {
    this.showNotification(
      "You do not have permission to perform this action",
      "error",
    );
  }

  handleValidationError(errors) {
    Object.entries(errors).forEach(([field, messages]) => {
      this.showFieldError(field, messages[0]);
    });
  }

  handleGenericError() {
    this.showNotification("An error occurred. Please try again.", "error");
  }

  handleNetworkError() {
    this.showNotification(
      "Network error. Please check your connection.",
      "error",
    );
  }

  // UI Helpers
  showNotification(message, type = "info") {
    if (window.Toastify) {
      Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        className: `toast-${type}`,
      }).showToast();
    } else {
      alert(message);
    }
  }

  showFieldError(fieldName, message) {
    const field = this.container.querySelector(`[name="${fieldName}"]`);
    if (!field) return;

    const errorDiv = document.createElement("div");
    errorDiv.className = "field-error";
    errorDiv.textContent = message;

    const existingError = field.parentElement.querySelector(".field-error");
    if (existingError) {
      existingError.remove();
    }

    field.classList.add("is-invalid");
    field.parentElement.appendChild(errorDiv);
  }

  clearFieldErrors() {
    this.container
      .querySelectorAll(".field-error")
      .forEach((el) => el.remove());
    this.container.querySelectorAll(".is-invalid").forEach((el) => {
      el.classList.remove("is-invalid");
    });
  }

  loading(show = true) {
    if (show) {
      this.container.classList.add("loading");
    } else {
      this.container.classList.remove("loading");
    }
  }
}

// ListView Implementation
class ListView extends BaseView {
  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      pageSize: 20,
      sortable: true,
      filterable: true,
      selectable: true,
      exportable: true,
      bulkActions: true,
      columns: [],
      filters: [],
      actions: [],
      rowActions: [],
      bulkActions: [],
    };
  }

  initialize() {
    super.initialize();
    this.currentPage = 1;
    this.totalPages = 1;
    this.sortField = "";
    this.sortDirection = "asc";
    this.selectedItems = new Set();
    this.activeFilters = new Map();

    this.loadData();
  }

  setupElements() {
    super.setupElements();

    // Cache frequently used elements
    this.tableBody = this.container.querySelector(".table-body");
    this.pagination = this.container.querySelector(".pagination");
    this.searchInput = this.container.querySelector(".search-input");
    this.filterForm = this.container.querySelector(".filter-form");
    this.bulkActionsContainer = this.container.querySelector(".bulk-actions");
  }

  setupEventListeners() {
    // Search
    if (this.searchInput) {
      this.searchInput.addEventListener(
        "input",
        Utils.debounce(() => this.handleSearch(), 300),
      );
    }

    // Sorting
    if (this.options.sortable) {
      this.container.querySelectorAll(".sortable").forEach((header) => {
        header.addEventListener("click", (e) => this.handleSort(e));
      });
    }

    // Filters
    if (this.filterForm) {
      this.filterForm.addEventListener("submit", (e) => this.handleFilter(e));
      this.filterForm.addEventListener("reset", () => this.resetFilters());
    }

    // Selection
    if (this.options.selectable) {
      this.container
        .querySelector(".select-all")
        ?.addEventListener("click", (e) => this.handleSelectAll(e));
    }

    // Row actions
    this.container.addEventListener("click", (e) => {
      const actionButton = e.target.closest("[data-action]");
      if (actionButton) {
        const action = actionButton.dataset.action;
        const itemId = actionButton.closest("tr").dataset.id;
        this.handleRowAction(action, itemId);
      }
    });

    // Bulk actions
    if (this.options.bulkActions) {
      this.container.querySelectorAll(".bulk-action").forEach((button) => {
        button.addEventListener("click", (e) => {
          const action = e.target.dataset.action;
          this.handleBulkAction(action);
        });
      });
    }

    // Pagination
    this.pagination?.addEventListener("click", (e) => {
      const pageLink = e.target.closest("[data-page]");
      if (pageLink) {
        e.preventDefault();
        this.goToPage(parseInt(pageLink.dataset.page));
      }
    });
  }

  async loadData() {
    this.loading(true);
    try {
      const params = this.getRequestParams();
      const data = await this.fetchData(this.options.baseUrl, params);
      this.renderData(data);
      this.updatePagination(data.pagination);
      this.updateBulkActions();
    } catch (error) {
      this.showNotification("Error loading data", "error");
    } finally {
      this.loading(false);
    }
  }

  getRequestParams() {
    const params = {
      page: this.currentPage,
      per_page: this.options.pageSize,
    };

    // Add search
    if (this.searchInput?.value) {
      params.search = this.searchInput.value;
    }

    // Add sorting
    if (this.sortField) {
      params.sort_field = this.sortField;
      params.sort_direction = this.sortDirection;
    }

    // Add filters
    this.activeFilters.forEach((value, key) => {
      params[`filter[${key}]`] = value;
    });

    return params;
  }

  renderData(data) {
    if (!this.tableBody) return;

    this.tableBody.innerHTML = "";

    if (!data.items.length) {
      this.renderEmptyState();
      return;
    }

    data.items.forEach((item) => {
      const row = this.renderRow(item);
      this.tableBody.appendChild(row);
    });
  }

  renderRow(item) {
    const row = document.createElement("tr");
    row.dataset.id = item.id;

    if (this.options.selectable) {
      row.innerHTML = `
                <td>
                    <input type="checkbox" class="row-checkbox"
                           value="${item.id}"
                           ${this.selectedItems.has(item.id) ? "checked" : ""}>
                </td>
            `;
    }

    this.options.columns.forEach((column) => {
      const value = this.formatColumnValue(item, column);
      row.innerHTML += `<td class="column-${column.name}">${value}</td>`;
    });

    if (this.options.rowActions.length) {
      row.innerHTML += this.renderRowActions();
    }

    return row;
  }

  renderRowActions() {
    return `
            <td class="actions-cell">
                <div class="btn-group">
                    ${this.options.rowActions
                      .map(
                        (action) => `
                        <button type="button"
                                class="btn btn-sm btn-${action.style || "default"}"
                                data-action="${action.name}"
                                ${action.enabled?.call(this) === false ? "disabled" : ""}>
                            <i class="fa fa-${action.icon}"></i>
                            ${action.label}
                        </button>
                    `,
                      )
                      .join("")}
                </div>
            </td>
        `;
  }

  renderEmptyState() {
    this.tableBody.innerHTML = `
            <tr>
                <td colspan="${this.getColumnCount()}" class="text-center">
                    <div class="empty-state">
                        <i class="fa fa-folder-open"></i>
                        <p>${this.options.translations.noRecords || "No records found"}</p>
                    </div>
                </td>
            </tr>
        `;
  }

  formatColumnValue(item, column) {
    let value = item[column.name];

    // Apply formatter if defined
    if (column.formatter) {
      value = column.formatter.call(this, value, item);
    }
    // Apply default formatting based on type
    else if (column.type) {
      switch (column.type) {
        case "date":
          value = Utils.formatDate(value);
          break;
        case "datetime":
          value = Utils.formatDate(value, "YYYY-MM-DD HH:mm");
          break;
        case "number":
          value = Utils.formatNumber(value);
          break;
        case "currency":
          value = Utils.formatCurrency(value);
          break;
        case "boolean":
          value = this.formatBoolean(value);
          break;
      }
    }

    return value ?? "";
  }

  formatBoolean(value) {
    return `
            <span class="badge badge-${value ? "success" : "danger"}">
                ${value ? "Yes" : "No"}
            </span>
        `;
  }

  updatePagination(pagination) {
    if (!this.pagination) return;

    this.totalPages = pagination.total_pages;
    this.currentPage = pagination.current_page;

    this.pagination.innerHTML = this.renderPagination(pagination);
  }

  renderPagination(pagination) {
    if (pagination.total_pages <= 1) return "";

    let pages = [];
    const current = pagination.current_page;
    const total = pagination.total_pages;

    // Always show first page
    pages.push(1);

    // Calculate range around current page
    let start = Math.max(2, current - 2);
    let end = Math.min(total - 1, current + 2);

    // Add ellipsis if needed
    if (start > 2) pages.push("...");

    // Add pages around current
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    // Add ellipsis if needed
    if (end < total - 1) pages.push("...");

    // Always show last page
    if (total > 1) pages.push(total);

    return `
            <ul class="pagination">
                <li class="page-item ${current === 1 ? "disabled" : ""}">
                    <a class="page-link" href="#" data-page="${current - 1}">
                        <i class="fa fa-chevron-left"></i>
                    </a>
                </li>
                ${pages
                  .map(
                    (page) => `
                    <li class="page-item ${page === current ? "active" : ""} ${page === "..." ? "disabled" : ""}">
                        <a class="page-link" href="#" ${page !== "..." ? `data-page="${page}"` : ""}>
                            ${page}
                        </a>
                    </li>
                `,
                  )
                  .join("")}
                <li class="page-item ${current === total ? "disabled" : ""}">
                    <a class="page-link" href="#" data-page="${current + 1}">
                        <i class="fa fa-chevron-right"></i>
                    </a>
                </li>
            </ul>
        `;
  }

  updateBulkActions() {
    if (!this.bulkActionsContainer) return;

    const hasSelection = this.selectedItems.size > 0;
    this.bulkActionsContainer.classList.toggle("hidden", !hasSelection);

    if (hasSelection) {
      this.container.querySelectorAll(".bulk-action").forEach((button) => {
        const action = this.options.bulkActions.find(
          (a) => a.name === button.dataset.action,
        );
        if (action?.enabled) {
          button.disabled = !action.enabled.call(this, this.selectedItems);
        }
      });
    }
  }

  // Event Handlers
  handleSearch() {
    this.currentPage = 1;
    this.loadData();
  }

  handleSort(e) {
    const header = e.target.closest(".sortable");
    const field = header.dataset.field;

    if (this.sortField === field) {
      this.sortDirection = this.sortDirection === "asc" ? "desc" : "asc";
    } else {
      this.sortField = field;
      this.sortDirection = "asc";
    }

    this.updateSortIndicators();
    this.loadData();
  }

  updateSortIndicators() {
    this.container.querySelectorAll(".sortable").forEach((header) => {
      header.classList.remove("sorted-asc", "sorted-desc");
      if (header.dataset.field === this.sortField) {
        header.classList.add(`sorted-${this.sortDirection}`);
      }
    });
  }

  handleFilter(e) {
    e.preventDefault();
    this.activeFilters.clear();

    const formData = new FormData(e.target);
    for (const [key, value] of formData.entries()) {
      if (value) {
        this.activeFilters.set(key, value);
      }
    }

    this.currentPage = 1;
    this.loadData();
    this.updateActiveFilters();
  }

  resetFilters() {
    this.activeFilters.clear();
    this.filterForm.reset();
    this.currentPage = 1;
    this.loadData();
    this.updateActiveFilters();
  }

  updateActiveFilters() {
    const container = this.container.querySelector(".active-filters");
    if (!container) return;

    container.innerHTML = "";

    this.activeFilters.forEach((value, key) => {
      const filter = this.options.filters.find((f) => f.name === key);
      if (filter) {
        container.innerHTML += `
                    <div class="filter-tag">
                        <span class="filter-label">${filter.label}:</span>
                        <span class="filter-value">${this.formatFilterValue(value, filter)}</span>
                        <button type="button" class="remove-filter" data-filter="${key}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                `;
      }
    });
  }

  formatFilterValue(value, filter) {
    if (filter.formatter) {
      return filter.formatter.call(this, value);
    }
    return value;
  }

  handleSelectAll(e) {
    const checked = e.target.checked;
    this.container.querySelectorAll(".row-checkbox").forEach((checkbox) => {
      checkbox.checked = checked;
      const itemId = checkbox.value;
      if (checked) {
        this.selectedItems.add(itemId);
      } else {
        this.selectedItems.delete(itemId);
      }
    });
    this.updateBulkActions();
  }

  async handleRowAction(action, itemId) {
    const actionDef = this.options.rowActions.find((a) => a.name === action);
    if (!actionDef) return;

    if (actionDef.confirm) {
      const confirmed = await this.confirm(actionDef.confirm);
      if (!confirmed) return;
    }

    try {
      this.loading(true);
      await actionDef.handler.call(this, itemId);
      if (actionDef.refresh !== false) {
        this.loadData();
      }
    } catch (error) {
      this.showNotification(error.message, "error");
    } finally {
      this.loading(false);
    }
  }

  async handleBulkAction(action) {
    const actionDef = this.options.bulkActions.find((a) => a.name === action);
    if (!actionDef) return;

    if (actionDef.confirm) {
      const confirmed = await this.confirm(actionDef.confirm);
      if (!confirmed) return;
    }

    try {
      this.loading(true);
      await actionDef.handler.call(this, Array.from(this.selectedItems));
      this.selectedItems.clear();
      if (actionDef.refresh !== false) {
        this.loadData();
      }
    } catch (error) {
      this.showNotification(error.message, "error");
    } finally {
      this.loading(false);
    }
  }

  goToPage(page) {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.loadData();
  }

  // Utility Methods
  getColumnCount() {
    return (
      this.options.columns.length +
      (this.options.selectable ? 1 : 0) +
      (this.options.rowActions.length ? 1 : 0)
    );
  }

  confirm(message) {
    return new Promise((resolve) => {
      if (window.confirm(message)) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  }
}
// FormView Implementation
class FormView extends BaseView {
  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      mode: "create", // 'create' or 'edit'
      redirectAfterSave: true,
      redirectUrl: null,
      validateOnChange: true,
      validateOnBlur: true,
      autoSave: false,
      autoSaveDelay: 1000,
      confirmUnsavedChanges: true,
      fieldsets: [],
      relationships: {},
      fileUploads: {},
      customValidators: {},
      dependentFields: {},
      computedFields: {},
      formatters: {},
      events: {},
    };
  }

  initialize() {
    super.initialize();

    this.form = this.container.querySelector("form");
    if (!this.form) {
      console.error("No form element found");
      return;
    }

    this.originalData = this.getFormData();
    this.hasChanges = false;
    this.autoSaveTimeout = null;

    this.initializeFieldsets();
    this.initializeRelationships();
    this.initializeFileUploads();
    this.initializeDependentFields();
    this.initializeComputedFields();
    this.setupValidation();
  }

  setupEventListeners() {
    // Form submission
    this.form.addEventListener("submit", (e) => this.handleSubmit(e));

    // Form changes
    if (this.options.validateOnChange || this.options.autoSave) {
      this.form.addEventListener("change", (e) => this.handleChange(e));
    }

    if (this.options.validateOnBlur) {
      this.form.addEventListener("blur", (e) => this.handleBlur(e), true);
    }

    // File uploads
    Object.keys(this.options.fileUploads).forEach((fieldName) => {
      const field = this.form.querySelector(`[name="${fieldName}"]`);
      if (field) {
        field.addEventListener("change", (e) => this.handleFileSelect(e));
      }
    });

    // Dependent fields
    Object.keys(this.options.dependentFields).forEach((fieldName) => {
      const field = this.form.querySelector(`[name="${fieldName}"]`);
      if (field) {
        field.addEventListener("change", (e) => this.handleDependentField(e));
      }
    });

    // Custom events
    Object.entries(this.options.events).forEach(([event, handler]) => {
      this.form.addEventListener(event, (e) => handler.call(this, e));
    });

    // Unsaved changes warning
    if (this.options.confirmUnsavedChanges) {
      window.addEventListener("beforeunload", (e) =>
        this.handleBeforeUnload(e),
      );
    }
  }

  // Form Data Handling
  getFormData() {
    const formData = new FormData(this.form);
    const data = {};

    for (const [key, value] of formData.entries()) {
      if (key.includes("[")) {
        // Handle array and object notation
        this.setNestedValue(data, key, value);
      } else {
        data[key] = this.formatFieldValue(key, value);
      }
    }

    return data;
  }

  setNestedValue(obj, path, value) {
    const keys = path.replace(/\[/g, ".").replace(/\]/g, "").split(".");
    const lastKey = keys.pop();
    const lastObj = keys.reduce((obj, key) => {
      if (!obj[key]) obj[key] = {};
      return obj[key];
    }, obj);
    lastObj[lastKey] = this.formatFieldValue(path, value);
  }

  formatFieldValue(fieldName, value) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return value;

    const formatter = this.options.formatters[fieldName];
    if (formatter) {
      return formatter.call(this, value, field);
    }

    // Default formatting based on field type
    switch (field.type) {
      case "number":
        return value === "" ? null : Number(value);
      case "checkbox":
        return field.checked;
      case "select-multiple":
        return Array.from(field.selectedOptions).map((opt) => opt.value);
      default:
        return value;
    }
  }

  setFormData(data) {
    Object.entries(data).forEach(([key, value]) => {
      const field = this.form.querySelector(`[name="${key}"]`);
      if (field) {
        this.setFieldValue(field, value);
      }
    });
  }

  setFieldValue(field, value) {
    switch (field.type) {
      case "checkbox":
        field.checked = Boolean(value);
        break;
      case "select-multiple":
        Array.from(field.options).forEach((option) => {
          option.selected = value.includes(option.value);
        });
        break;
      case "file":
        // Handle file field separately
        break;
      default:
        field.value = value ?? "";
    }

    // Trigger change event for dependent fields
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // Validation
  setupValidation() {
    this.validators = {};

    // Setup field validators
    this.form.querySelectorAll("[data-validate]").forEach((field) => {
      const rules = field.dataset.validate.split("|");
      this.validators[field.name] = rules.map((rule) => {
        const [name, params] = rule.split(":");
        return this.createValidator(name, params);
      });
    });

    // Add custom validators
    Object.entries(this.options.customValidators).forEach(
      ([fieldName, validator]) => {
        if (!this.validators[fieldName]) {
          this.validators[fieldName] = [];
        }
        this.validators[fieldName].push(validator);
      },
    );
  }

  createValidator(name, params) {
    const baseValidators = {
      required: (value) => value !== "" || "This field is required",
      email: (value) =>
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || "Invalid email",
      min: (value, min) => Number(value) >= min || `Minimum value is ${min}`,
      max: (value, max) => Number(value) <= max || `Maximum value is ${max}`,
      minLength: (value, min) =>
        value.length >= min || `Minimum length is ${min}`,
      maxLength: (value, max) =>
        value.length <= max || `Maximum length is ${max}`,
      pattern: (value, pattern) =>
        new RegExp(pattern).test(value) || "Invalid format",
      match: (value, field) =>
        value === this.form[field].value || "Fields do not match",
    };

    return (value) => baseValidators[name](value, params);
  }

  validateField(field) {
    const validators = this.validators[field.name];
    if (!validators) return true;

    const value = field.type === "checkbox" ? field.checked : field.value;

    for (const validator of validators) {
      const result = validator(value, field);
      if (result !== true) {
        this.showFieldError(field, result);
        return false;
      }
    }

    this.clearFieldError(field);
    return true;
  }

  validateForm() {
    let isValid = true;
    const fields = Array.from(this.form.elements);

    fields.forEach((field) => {
      if (field.name && !this.validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }

  showFieldError(field, message) {
    const container = field.closest(".form-group");
    if (!container) return;

    const errorElement =
      container.querySelector(".field-error") || document.createElement("div");
    errorElement.className = "field-error";
    errorElement.textContent = message;

    field.classList.add("is-invalid");
    if (!container.querySelector(".field-error")) {
      container.appendChild(errorElement);
    }
  }

  clearFieldError(field) {
    const container = field.closest(".form-group");
    if (!container) return;

    const errorElement = container.querySelector(".field-error");
    if (errorElement) {
      errorElement.remove();
    }
    field.classList.remove("is-invalid");
  }

  // Fieldsets
  initializeFieldsets() {
    this.fieldsets = this.container.querySelectorAll(".fieldset");

    this.fieldsets.forEach((fieldset) => {
      const header = fieldset.querySelector(".fieldset-header");
      const content = fieldset.querySelector(".fieldset-content");

      if (header && content) {
        header.addEventListener("click", () => {
          const isCollapsed = content.classList.contains("collapsed");
          content.classList.toggle("collapsed");
          header.querySelector(".fieldset-toggle-icon").textContent =
            isCollapsed ? "▼" : "▶";

          // Save state
          if (fieldset.id) {
            localStorage.setItem(
              `fieldset_${fieldset.id}`,
              isCollapsed ? "expanded" : "collapsed",
            );
          }
        });

        // Restore state
        if (fieldset.id) {
          const state = localStorage.getItem(`fieldset_${fieldset.id}`);
          if (state === "collapsed") {
            content.classList.add("collapsed");
            header.querySelector(".fieldset-toggle-icon").textContent = "▶";
          }
        }
      }
    });
  }

  // Relationships
  initializeRelationships() {
    Object.entries(this.options.relationships).forEach(
      ([fieldName, config]) => {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        if (!field) return;

        if (config.type === "select2") {
          this.initializeSelect2(field, config);
        } else if (config.type === "autocomplete") {
          this.initializeAutocomplete(field, config);
        }
      },
    );
  }

  initializeSelect2(field, config) {
    if (!window.Select2) {
      console.warn("Select2 is not loaded");
      return;
    }

    $(field).select2({
      ajax: {
        url: config.url,
        dataType: "json",
        delay: 250,
        data: (params) => ({
          search: params.term,
          page: params.page || 1,
        }),
        processResults: (data, params) => ({
          results: data.items,
          pagination: {
            more: data.has_more,
          },
        }),
        cache: true,
      },
      minimumInputLength: config.minLength || 2,
      placeholder: config.placeholder,
      allowClear: config.allowClear !== false,
      templateResult: config.templateResult,
      templateSelection: config.templateSelection,
    });
  }

  initializeAutocomplete(field, config) {
    // Implement autocomplete functionality
  }

  // File Uploads
  initializeFileUploads() {
    Object.entries(this.options.fileUploads).forEach(([fieldName, config]) => {
      const field = this.form.querySelector(`[name="${fieldName}"]`);
      if (!field) return;

      // Create preview container
      const previewContainer = document.createElement("div");
      previewContainer.className = "file-preview";
      field.parentNode.insertBefore(previewContainer, field.nextSibling);

      // Setup drag and drop
      field.parentNode.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation();
        field.parentNode.classList.add("dragover");
      });

      field.parentNode.addEventListener("dragleave", (e) => {
        e.preventDefault();
        e.stopPropagation();
        field.parentNode.classList.remove("dragover");
      });

      field.parentNode.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        field.parentNode.classList.remove("dragover");

        const files = e.dataTransfer.files;
        if (files.length) {
          field.files = files;
          field.dispatchEvent(new Event("change"));
        }
      });
    });
  }

  handleFileSelect(e) {
    const field = e.target;
    const config = this.options.fileUploads[field.name];
    if (!config) return;

    const previewContainer = field.parentNode.querySelector(".file-preview");
    if (!previewContainer) return;

    const files = Array.from(field.files);

    // Validate files
    const invalidFiles = files.filter((file) => {
      const ext = file.name.split(".").pop().toLowerCase();
      return !config.allowedTypes.includes(ext) || file.size > config.maxSize;
    });

    if (invalidFiles.length) {
      this.showFieldError(field, "Invalid file type or size");
      field.value = "";
      return;
    }

    // Show preview
    previewContainer.innerHTML = files
      .map((file) => {
        const isImage = file.type.startsWith("image/");
        if (isImage) {
          return `
                    <div class="file-preview-item">
                        <img src="${URL.createObjectURL(file)}" alt="${file.name}">
                        <span class="file-name">${file.name}</span>
                        <button type="button" class="remove-file">×</button>
                    </div>
                `;
        } else {
          return `
                    <div class="file-preview-item">
                        <i class="fa fa-file"></i>
                        <span class="file-name">${file.name}</span>
                        <button type="button" class="remove-file">×</button>
                    </div>
                `;
        }
      })
      .join("");

    // Handle remove buttons
    previewContainer
      .querySelectorAll(".remove-file")
      .forEach((button, index) => {
        button.addEventListener("click", () => {
          const newFiles = new DataTransfer();
          files.forEach((file, i) => {
            if (i !== index) newFiles.items.add(file);
          });
          field.files = newFiles.files;
          button.parentNode.remove();
        });
      });
  }

  // Dependent Fields
  initializeDependentFields() {
    Object.entries(this.options.dependentFields).forEach(
      ([fieldName, config]) => {
        const dependentField = this.form.querySelector(`[name="${fieldName}"]`);
        const sourceField = this.form.querySelector(
          `[name="${config.dependsOn}"]`,
        );

        if (dependentField && sourceField) {
          this.updateDependentField(dependentField, sourceField, config);
          sourceField.addEventListener("change", () => {
            this.updateDependentField(dependentField, sourceField, config);
          });
        }
      },
    );
  }

  updateDependentField(dependentField, sourceField, config) {
    const sourceValue =
      sourceField.type === "checkbox" ? sourceField.checked : sourceField.value;

    const show = config.condition(sourceValue, sourceField);
    const container = dependentField.closest(".form-group");

    if (container) {
      container.style.display = show ? "" : "none";

      if (show && config.required) {
        dependentField.setAttribute("required", "");
      } else {
        dependentField.removeAttribute("required");
      }
    }
  }

  // Computed Fields
  initializeComputedFields() {
    Object.entries(this.options.computedFields).forEach(
      ([fieldName, config]) => {
        const computedField = this.form.querySelector(`[name="${fieldName}"]`);
        if (!computedField) return;

        const sourceFields = config.dependsOn
          .map((name) => this.form.querySelector(`[name="${name}"]`))
          .filter(Boolean);

        const updateValue = () => {
          const values = sourceFields.map((field) =>
            field.type === "checkbox" ? field.checked : field.value,
          );
          computedField.value = config.compute.apply(this, values);
        };

        sourceFields.forEach((field) => {
          field.addEventListener("change", updateValue);
          field.addEventListener("input", updateValue);
        });

        updateValue();
      },
    );
  }

  // Event Handlers
  async handleSubmit(e) {
    e.preventDefault();

    if (!this.validateForm()) {
      this.showNotification(
        "Please correct the errors before submitting",
        "error",
      );
      return;
    }

    try {
      this.loading(true);
      const data = this.getFormData();

      const response = await this.saveForm(data);

      this.showNotification(
        this.options.mode === "create"
          ? "Record created successfully"
          : "Record updated successfully",
        "success",
      );

      if (this.options.redirectAfterSave) {
        window.location.href =
          this.options.redirectUrl || this.getRedirectUrl(response.data);
      }
    } catch (error) {
      this.handleError(error);
    } finally {
      this.loading(false);
    }
  }

  async saveForm(data) {
    const url =
      this.options.mode === "create"
        ? this.options.baseUrl
        : `${this.options.baseUrl}/${data.id}`;

    const method = this.options.mode === "create" ? "POST" : "PUT";

    return await this.postData(url, data, method);
  }

  handleChange(e) {
    const field = e.target;
    if (!field.name) return;

    if (this.options.validateOnChange) {
      this.validateField(field);
    }

    if (this.options.autoSave) {
      clearTimeout(this.autoSaveTimeout);
      this.autoSaveTimeout = setTimeout(() => {
        this.handleSubmit(new Event("submit"));
      }, this.options.autoSaveDelay);
    }

    this.hasChanges = true;
  }

  handleBlur(e) {
    const field = e.target;
    if (field.name && this.options.validateOnBlur) {
      this.validateField(field);
    }
  }

  handleBeforeUnload(e) {
    if (this.hasChanges) {
      e.preventDefault();
      e.returnValue = "";
    }
  }

  // Utility Methods
  getRedirectUrl(data) {
    return `${this.options.baseUrl}/${data.id}`;
  }
}

// ShowView Implementation
class ShowView extends BaseView {
  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      fieldsets: [],
      actions: [],
      relationshipTabs: [],
      formatters: {},
      expandedFieldsets: ["basic"],
      historyEnabled: false,
      commentsEnabled: false,
      attachmentsEnabled: false,
      workflowEnabled: false,
    };
  }

  initialize() {
    super.initialize();
    this.itemId = this.container.dataset.itemId;

    this.initializeFieldsets();
    this.initializeRelationshipTabs();

    if (this.options.historyEnabled) {
      this.initializeHistory();
    }

    if (this.options.commentsEnabled) {
      this.initializeComments();
    }

    if (this.options.attachmentsEnabled) {
      this.initializeAttachments();
    }

    if (this.options.workflowEnabled) {
      this.initializeWorkflow();
    }

    this.loadData();
  }

  setupElements() {
    super.setupElements();

    this.fieldsets = this.container.querySelectorAll(".fieldset");
    this.relationshipTabs = this.container.querySelector(".relationship-tabs");
    this.tabContent = this.container.querySelector(".tab-content");
  }

  setupEventListeners() {
    // Fieldset toggling
    this.fieldsets.forEach((fieldset) => {
      const header = fieldset.querySelector(".fieldset-header");
      if (header) {
        header.addEventListener("click", () => this.toggleFieldset(fieldset));
      }
    });

    // Relationship tab switching
    if (this.relationshipTabs) {
      this.relationshipTabs.addEventListener("click", (e) => {
        const tabLink = e.target.closest('[data-toggle="tab"]');
        if (tabLink) {
          e.preventDefault();
          this.switchTab(tabLink);
        }
      });
    }

    // Actions
    this.container.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", (e) => this.handleAction(e));
    });

    // Field value copying
    this.container.querySelectorAll(".copy-value").forEach((button) => {
      button.addEventListener("click", (e) => this.copyFieldValue(e));
    });
  }

  async loadData() {
    try {
      this.loading(true);
      const data = await this.fetchData(
        `${this.options.baseUrl}/${this.itemId}`,
      );
      this.renderData(data);
    } catch (error) {
      this.handleError(error);
    } finally {
      this.loading(false);
    }
  }

  renderData(data) {
    // Render field values
    Object.entries(data).forEach(([field, value]) => {
      const element = this.container.querySelector(`[data-field="${field}"]`);
      if (element) {
        element.innerHTML = this.formatFieldValue(field, value);
      }
    });

    // Update metadata
    this.updateMetadata(data);

    // Load initial relationship tab if any
    if (this.relationshipTabs) {
      const activeTab = this.relationshipTabs.querySelector(".active");
      if (activeTab) {
        this.loadRelationshipTab(activeTab.dataset.target);
      }
    }
  }

  formatFieldValue(field, value) {
    // Use custom formatter if defined
    const formatter = this.options.formatters[field];
    if (formatter) {
      return formatter.call(this, value);
    }

    // Default formatting based on field type
    const fieldConfig = this.options.fields[field];
    if (!fieldConfig) return value;

    switch (fieldConfig.type) {
      case "date":
        return value ? Utils.formatDate(value) : "";

      case "datetime":
        return value ? Utils.formatDate(value, "YYYY-MM-DD HH:mm:ss") : "";

      case "currency":
        return value ? Utils.formatCurrency(value) : "";

      case "number":
        return value ? Utils.formatNumber(value) : "";

      case "boolean":
        return this.formatBoolean(value);

      case "json":
        return this.formatJson(value);

      case "image":
        return this.formatImage(value);

      case "file":
        return this.formatFile(value);

      case "enum":
        return this.formatEnum(value, fieldConfig.options);

      case "relationship":
        return this.formatRelationship(value, fieldConfig);

      default:
        return value || "";
    }
  }

  formatBoolean(value) {
    return `
            <span class="badge badge-${value ? "success" : "danger"}">
                ${value ? "Yes" : "No"}
            </span>
        `;
  }

  formatJson(value) {
    if (!value) return "";
    try {
      const formatted = JSON.stringify(
        typeof value === "string" ? JSON.parse(value) : value,
        null,
        2,
      );
      return `
                <pre class="json-viewer">
                    <code>${this.escapeHtml(formatted)}</code>
                </pre>
            `;
    } catch (e) {
      return value;
    }
  }

  formatImage(value) {
    if (!value) return "";
    return `
            <div class="image-preview">
                <img src="${value}" alt=""
                     class="img-thumbnail"
                     data-action="zoom"
                     loading="lazy">
            </div>
        `;
  }

  formatFile(value) {
    if (!value) return "";
    const fileName = value.split("/").pop();
    return `
            <div class="file-preview">
                <i class="fa fa-file"></i>
                <a href="${value}" target="_blank">${fileName}</a>
                <span class="file-size">${this.getFileSize(value)}</span>
            </div>
        `;
  }

  formatEnum(value, options) {
    const option = options.find((opt) => opt.value === value);
    if (!option) return value;

    return `
            <span class="badge badge-${option.color || "secondary"}">
                ${option.label}
            </span>
        `;
  }

  formatRelationship(value, config) {
    if (!value) return "";

    if (Array.isArray(value)) {
      return value
        .map((item) => this.formatRelationshipItem(item, config))
        .join(", ");
    }

    return this.formatRelationshipItem(value, config);
  }

  formatRelationshipItem(item, config) {
    const displayField = config.displayField || "name";
    const url = `${config.baseUrl}/${item.id}`;
    return `
            <a href="${url}" class="relationship-link">
                ${item[displayField]}
            </a>
        `;
  }

  updateMetadata(data) {
    // Update created/updated info
    const createdAt = this.container.querySelector(".created-at");
    if (createdAt && data.created_at) {
      createdAt.textContent = Utils.formatDate(
        data.created_at,
        "YYYY-MM-DD HH:mm:ss",
      );
    }

    const updatedAt = this.container.querySelector(".updated-at");
    if (updatedAt && data.updated_at) {
      updatedAt.textContent = Utils.formatDate(
        data.updated_at,
        "YYYY-MM-DD HH:mm:ss",
      );
    }

    // Update workflow state if enabled
    if (this.options.workflowEnabled && data.state) {
      const stateElement = this.container.querySelector(".workflow-state");
      if (stateElement) {
        stateElement.innerHTML = this.formatWorkflowState(data.state);
      }
    }
  }

  formatWorkflowState(state) {
    const stateConfig = this.options.workflowStates[state];
    if (!stateConfig) return state;

    return `
            <span class="badge badge-${stateConfig.color || "secondary"}">
                <i class="fa fa-${stateConfig.icon}"></i>
                ${stateConfig.label}
            </span>
        `;
  }

  // Fieldset handling
  toggleFieldset(fieldset) {
    const content = fieldset.querySelector(".fieldset-content");
    const icon = fieldset.querySelector(".fieldset-toggle-icon");
    const isCollapsed = content.classList.toggle("collapsed");

    icon.textContent = isCollapsed ? "►" : "▼";

    // Save state if fieldset has ID
    if (fieldset.id) {
      localStorage.setItem(
        `fieldset_${fieldset.id}`,
        isCollapsed ? "collapsed" : "expanded",
      );
    }
  }

  // Relationship tabs handling
  async switchTab(tabLink) {
    // Update active state
    this.relationshipTabs
      .querySelectorAll(".active")
      .forEach((el) => el.classList.remove("active"));
    tabLink.classList.add("active");

    // Load tab content if not already loaded
    const tabId = tabLink.getAttribute("href").substring(1);
    const tabPanel = this.tabContent.querySelector(`#${tabId}`);

    if (!tabPanel.dataset.loaded) {
      await this.loadRelationshipTab(tabId);
      tabPanel.dataset.loaded = "true";
    }
  }

  async loadRelationshipTab(tabId) {
    const tabConfig = this.options.relationshipTabs.find(
      (tab) => tab.id === tabId,
    );
    if (!tabConfig) return;

    const tabPanel = this.tabContent.querySelector(`#${tabId}`);
    if (!tabPanel) return;

    try {
      this.loading(true);
      const data = await this.fetchData(
        `${this.options.baseUrl}/${this.itemId}/relationships/${tabConfig.relationship}`,
      );
      tabPanel.innerHTML = this.renderRelationshipTab(data, tabConfig);
    } catch (error) {
      tabPanel.innerHTML = `
                <div class="alert alert-danger">
                    Error loading data: ${error.message}
                </div>
            `;
    } finally {
      this.loading(false);
    }
  }

  renderRelationshipTab(data, config) {
    if (!data.length) {
      return `
                <div class="empty-state">
                    <i class="fa fa-folder-open"></i>
                    <p>No ${config.label} found</p>
                </div>
            `;
    }

    return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            ${config.columns
                              .map(
                                (col) => `
                                <th>${col.label}</th>
                            `,
                              )
                              .join("")}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data
                          .map(
                            (item) => `
                            <tr>
                                ${config.columns
                                  .map(
                                    (col) => `
                                    <td>${this.formatFieldValue(col.name, item[col.name])}</td>
                                `,
                                  )
                                  .join("")}
                                <td>
                                    <div class="btn-group">
                                        <a href="${config.baseUrl}/${item.id}"
                                           class="btn btn-sm btn-default">
                                            <i class="fa fa-eye"></i>
                                        </a>
                                        ${
                                          this.options.permissions.edit
                                            ? `
                                            <a href="${config.baseUrl}/${item.id}/edit"
                                               class="btn btn-sm btn-primary">
                                                <i class="fa fa-edit"></i>
                                            </a>
                                        `
                                            : ""
                                        }
                                    </div>
                                </td>
                            </tr>
                        `,
                          )
                          .join("")}
                    </tbody>
                </table>
            </div>
        `;
  }

  // Action handling
  async handleAction(e) {
    const button = e.target.closest("[data-action]");
    const action = button.dataset.action;
    const actionConfig = this.options.actions.find((a) => a.name === action);

    if (!actionConfig) return;

    if (actionConfig.confirm) {
      const confirmed = await this.confirm(actionConfig.confirm);
      if (!confirmed) return;
    }

    try {
      this.loading(true);
      await actionConfig.handler.call(this, this.itemId);

      if (actionConfig.refresh) {
        await this.loadData();
      }

      if (actionConfig.redirect) {
        window.location.href =
          typeof actionConfig.redirect === "function"
            ? actionConfig.redirect(this.itemId)
            : actionConfig.redirect;
      }
    } catch (error) {
      this.handleError(error);
    } finally {
      this.loading(false);
    }
  }

  // History handling
  async initializeHistory() {
    const historyTab = this.container.querySelector("#history-tab");
    if (!historyTab) return;

    try {
      const history = await this.fetchData(
        `${this.options.baseUrl}/${this.itemId}/history`,
      );
      this.renderHistory(history);
    } catch (error) {
      console.error("Error loading history:", error);
    }
  }

  renderHistory(history) {
    const container = this.container.querySelector("#history");
    if (!container) return;

    if (!history.length) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fa fa-history"></i>
                    <p>No history available</p>
                </div>
            `;
      return;
    }

    container.innerHTML = `
            <div class="timeline">
                ${history
                  .map(
                    (entry) => `
                    <div class="timeline-item">
                        <div class="timeline-marker">
                            <i class="fa fa-${this.getHistoryIcon(entry.action)}"></i>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-header">
                                <span class="user">
                                    ${
                                      entry.user
                                        ? `
                                        <img src="${entry.user.avatar}"
                                             class="user-avatar" alt="">
                                        ${entry.user.name}
                                    `
                                        : "System"
                                    }
                                </span>
                                <span class="date">
                                    ${Utils.formatDate(entry.created_at, "YYYY-MM-DD HH:mm")}
                                </span>
                            </div>
                            <div class="timeline-body">
                                ${this.formatHistoryEntry(entry)}
                            </div>
                        </div>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        `;
  }

  getHistoryIcon(action) {
    const icons = {
      create: "plus",
      update: "edit",
      delete: "trash",
      restore: "history",
      comment: "comment",
      state_change: "random",
    };
    return icons[action] || "circle";
  }

  formatHistoryEntry(entry) {
    switch (entry.action) {
      case "update":
        return this.formatChanges(entry.changes);
      case "state_change":
        return this.formatStateChange(entry);
      default:
        return entry.description;
    }
  }

  formatChanges(changes) {
    return `
            <table class="changes-table">
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Old Value</th>
                        <th>New Value</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(changes)
                      .map(
                        ([field, change]) => `
                        <tr>
                            <td>${this.options.fields[field]?.label || field}</td>
                            <td>${this.formatFieldValue(field, change.old)}</td>
                            <td>${this.formatFieldValue(field, change.new)}</td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        `;
  }

  formatStateChange(entry) {
    return `
            Changed state from
            <strong>${this.formatWorkflowState(entry.old_state)}</strong>
            to
            <strong>${this.formatWorkflowState(entry.new_state)}</strong>
            ${entry.comment ? `<div class="state-comment">${entry.comment}</div>` : ""}
        `;
  }

  // Utility methods
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  async getFileSize(url) {
    try {
      const response = await fetch(url, { method: "HEAD" });
      const size = response.headers.get("content-length");
      return this.formatBytes(size);
    } catch {
      return "";
    }
  }

  formatBytes(bytes) {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  }

  confirm(message) {
    return new Promise((resolve) => {
      if (window.confirm(message)) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  }
}
class KanbanView extends BaseView {
  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      columns: [],
      groupBy: null,
      stateField: "state",
      cardTemplate: null,
      draggable: true,
      quickAdd: true,
      cardActions: [],
      columnActions: [],
      filters: [],
      summaries: [],
      autoRefresh: false,
      refreshInterval: 30000, // 30 seconds
      defaultColumnWidth: 300,
      cardLimit: 0, // 0 means no limit
      loadMoreIncrement: 20,
      animations: true,
    };
  }

  initialize() {
    super.initialize();
    this.columns = new Map(); // Column elements map
    this.cards = new Map(); // Card elements map
    this.sortables = new Map(); // Sortable instances for each column
    this.loadedCounts = new Map(); // Track loaded cards per column
    this.hasMore = new Map(); // Track if more cards can be loaded

    this.initializeColumns();
    this.initializeDragAndDrop();

    if (this.options.autoRefresh) {
      this.startAutoRefresh();
    }
  }

  setupElements() {
    super.setupElements();
    this.board = this.container.querySelector(".kanban-board");
    this.columnContainer = this.container.querySelector(".kanban-columns");
    this.searchInput = this.container.querySelector(".search-input");
    this.filterForm = this.container.querySelector(".filter-form");
  }

  setupEventListeners() {
    // Search
    if (this.searchInput) {
      this.searchInput.addEventListener(
        "input",
        Utils.debounce(() => this.handleSearch(), 300),
      );
    }

    // Filters
    if (this.filterForm) {
      this.filterForm.addEventListener("submit", (e) => this.handleFilter(e));
    }

    // Column width resizing
    this.container
      .querySelectorAll(".column-resize-handle")
      .forEach((handle) => {
        handle.addEventListener("mousedown", (e) => this.startColumnResize(e));
      });

    // Quick add buttons
    if (this.options.quickAdd) {
      this.container.querySelectorAll(".quick-add-button").forEach((button) => {
        button.addEventListener("click", (e) => this.showQuickAddForm(e));
      });
    }

    // Card actions
    this.board.addEventListener("click", (e) => {
      const actionButton = e.target.closest("[data-action]");
      if (actionButton) {
        const action = actionButton.dataset.action;
        const cardId = actionButton.closest(".kanban-card").dataset.id;
        this.handleCardAction(action, cardId);
      }
    });

    // Column actions
    this.board.addEventListener("click", (e) => {
      const actionButton = e.target.closest("[data-column-action]");
      if (actionButton) {
        const action = actionButton.dataset.columnAction;
        const columnId = actionButton.closest(".kanban-column").dataset.id;
        this.handleColumnAction(action, columnId);
      }
    });

    // Load more buttons
    this.board.addEventListener("click", (e) => {
      const loadMoreButton = e.target.closest(".load-more-button");
      if (loadMoreButton) {
        const columnId = loadMoreButton.closest(".kanban-column").dataset.id;
        this.loadMoreCards(columnId);
      }
    });
  }

  async initializeColumns() {
    try {
      // Get column definitions
      let columns = this.options.columns;

      // If groupBy is specified, fetch dynamic columns
      if (this.options.groupBy) {
        columns = await this.fetchColumns();
      }

      // Create columns
      columns.forEach((column) => this.createColumn(column));

      // Load initial cards
      await Promise.all(columns.map((column) => this.loadCards(column.id)));
    } catch (error) {
      this.handleError(error);
    }
  }

  async fetchColumns() {
    const response = await this.fetchData(`${this.options.baseUrl}/columns`, {
      group_by: this.options.groupBy,
    });
    return response.columns;
  }

  createColumn(column) {
    const columnElement = document.createElement("div");
    columnElement.className = "kanban-column";
    columnElement.dataset.id = column.id;

    columnElement.innerHTML = `
            <div class="column-header" style="background-color: ${column.color || "#f0f0f0"}">
                <div class="column-title">
                    <span class="column-name">${column.name}</span>
                    <span class="column-count badge">0</span>
                </div>
                <div class="column-actions">
                    ${
                      this.options.quickAdd
                        ? `
                        <button type="button" class="btn btn-xs btn-success quick-add-button"
                                title="Add new card">
                            <i class="fa fa-plus"></i>
                        </button>
                    `
                        : ""
                    }
                    ${this.options.columnActions
                      .map(
                        (action) => `
                        <button type="button"
                                class="btn btn-xs btn-${action.style || "default"}"
                                data-column-action="${action.name}"
                                title="${action.label}">
                            <i class="fa fa-${action.icon}"></i>
                        </button>
                    `,
                      )
                      .join("")}
                </div>
            </div>
            <div class="column-content">
                <div class="cards-container"></div>
                <div class="column-footer">
                    <button type="button" class="btn btn-link btn-block load-more-button"
                            style="display: none;">
                        Load more...
                    </button>
                </div>
            </div>
            ${
              this.options.resizable
                ? `
                <div class="column-resize-handle"></div>
            `
                : ""
            }
        `;

    this.columnContainer.appendChild(columnElement);
    this.columns.set(column.id, columnElement);

    if (this.options.summaries) {
      this.addColumnSummary(column, columnElement);
    }
  }

  addColumnSummary(column, columnElement) {
    const summaryElement = document.createElement("div");
    summaryElement.className = "column-summary";

    summaryElement.innerHTML = this.options.summaries
      .map(
        (summary) => `
            <div class="summary-item">
                <span class="summary-label">${summary.label}:</span>
                <span class="summary-value" data-summary="${summary.name}">-</span>
            </div>
        `,
      )
      .join("");

    columnElement.querySelector(".column-footer").prepend(summaryElement);
  }

  async loadCards(columnId, offset = 0) {
    const column = this.columns.get(columnId);
    if (!column) return;

    try {
      const response = await this.fetchData(`${this.options.baseUrl}/cards`, {
        column_id: columnId,
        offset: offset,
        limit: this.options.loadMoreIncrement,
      });

      if (offset === 0) {
        // Clear existing cards if this is the initial load
        column.querySelector(".cards-container").innerHTML = "";
        this.loadedCounts.set(columnId, 0);
      }

      response.cards.forEach((card) => this.addCard(card, columnId));

      // Update counts and load more button
      this.loadedCounts.set(
        columnId,
        (this.loadedCounts.get(columnId) || 0) + response.cards.length,
      );
      this.hasMore.set(columnId, response.has_more);
      this.updateLoadMoreButton(columnId);
      this.updateColumnCount(columnId);

      // Update column summaries
      if (response.summaries) {
        this.updateColumnSummaries(columnId, response.summaries);
      }
    } catch (error) {
      this.handleError(error);
    }
  }

  addCard(cardData, columnId) {
    const card = document.createElement("div");
    card.className = "kanban-card";
    card.dataset.id = cardData.id;

    if (this.options.cardTemplate) {
      card.innerHTML = this.options.cardTemplate(cardData);
    } else {
      card.innerHTML = this.defaultCardTemplate(cardData);
    }

    const container = this.columns
      .get(columnId)
      .querySelector(".cards-container");

    if (this.options.animations) {
      card.style.opacity = "0";
      container.appendChild(card);
      requestAnimationFrame(() => {
        card.style.opacity = "1";
      });
    } else {
      container.appendChild(card);
    }

    this.cards.set(cardData.id, card);
  }

  defaultCardTemplate(cardData) {
    return `
            <div class="card-header">
                ${
                  cardData.priority
                    ? `
                    <span class="priority priority-${cardData.priority.toLowerCase()}">
                        <i class="fa fa-flag"></i>
                    </span>
                `
                    : ""
                }
                <div class="card-title">${cardData.title}</div>
                <div class="card-actions">
                    ${this.options.cardActions
                      .map(
                        (action) => `
                        <button type="button"
                                class="btn btn-xs btn-link"
                                data-action="${action.name}"
                                title="${action.label}">
                            <i class="fa fa-${action.icon}"></i>
                        </button>
                    `,
                      )
                      .join("")}
                </div>
            </div>
            ${
              cardData.description
                ? `
                <div class="card-description">
                    ${cardData.description}
                </div>
            `
                : ""
            }
            <div class="card-meta">
                ${
                  cardData.due_date
                    ? `
                    <span class="due-date ${this.isDueDate(cardData.due_date) ? "overdue" : ""}">
                        <i class="fa fa-calendar"></i>
                        ${Utils.formatDate(cardData.due_date)}
                    </span>
                `
                    : ""
                }
                ${
                  cardData.assigned_to
                    ? `
                    <span class="assigned-to">
                        <i class="fa fa-user"></i>
                        ${cardData.assigned_to.name}
                    </span>
                `
                    : ""
                }
            </div>
            ${
              cardData.tags?.length
                ? `
                <div class="card-tags">
                    ${cardData.tags
                      .map(
                        (tag) => `
                        <span class="tag" style="background-color: ${tag.color}">
                            ${tag.name}
                        </span>
                    `,
                      )
                      .join("")}
                </div>
            `
                : ""
            }
            <div class="card-footer">
                ${
                  cardData.comments_count
                    ? `
                    <span class="comments-count">
                        <i class="fa fa-comments"></i>
                        ${cardData.comments_count}
                    </span>
                `
                    : ""
                }
                ${
                  cardData.attachments_count
                    ? `
                    <span class="attachments-count">
                        <i class="fa fa-paperclip"></i>
                        ${cardData.attachments_count}
                    </span>
                `
                    : ""
                }
                ${
                  cardData.checklist_progress
                    ? `
                    <div class="checklist-progress"
                         title="${cardData.checklist_progress.completed}/${cardData.checklist_progress.total}">
                        <div class="progress">
                            <div class="progress-bar" style="width: ${cardData.checklist_progress.percentage}%">
                            </div>
                        </div>
                    </div>
                `
                    : ""
                }
            </div>
        `;
  }

  initializeDragAndDrop() {
    if (!this.options.draggable || !window.Sortable) return;

    this.columns.forEach((column, columnId) => {
      const container = column.querySelector(".cards-container");

      const sortable = new Sortable(container, {
        group: "cards",
        animation: 150,
        ghostClass: "card-ghost",
        dragClass: "card-drag",
        handle: ".card-header",
        onEnd: (evt) => this.handleCardMove(evt),
      });

      this.sortables.set(columnId, sortable);
    });
  }

  async handleCardMove(evt) {
    const cardId = evt.item.dataset.id;
    const newColumnId = evt.to.closest(".kanban-column").dataset.id;
    const newIndex = evt.newIndex;

    try {
      await this.updateCardPosition(cardId, newColumnId, newIndex);
      this.updateColumnCounts();
    } catch (error) {
      // Revert the move
      evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
      this.handleError(error);
    }
  }

  async updateCardPosition(cardId, columnId, position) {
    return await this.postData(
      `${this.options.baseUrl}/cards/${cardId}/position`,
      {
        column_id: columnId,
        position: position,
      },
    );
  }

  updateColumnCounts() {
    this.columns.forEach((column, columnId) => {
      this.updateColumnCount(columnId);
    });
  }

  updateColumnCount(columnId) {
    const column = this.columns.get(columnId);
    if (!column) return;

    const count = column.querySelector(".cards-container").children.length;
    column.querySelector(".column-count").textContent = count;
  }

  updateLoadMoreButton(columnId) {
    const column = this.columns.get(columnId);
    if (!column) return;

    const button = column.querySelector(".load-more-button");
    button.style.display = this.hasMore.get(columnId) ? "" : "none";
  }

  async loadMoreCards(columnId) {
    const offset = this.loadedCounts.get(columnId) || 0;
    await this.loadCards(columnId, offset);
  }

  updateColumnSummaries(columnId, summaries) {
    const column = this.columns.get(columnId);
    if (!column) return;

    Object.entries(summaries).forEach(([key, value]) => {
      const element = column.querySelector(`[data-summary="${key}"]`);
      if (element) {
        element.textContent = value;
      }
    });
  }

  startColumnResize(e) {
    const handle = e.target;
    const column = handle.closest(".kanban-column");
    const startX = e.clientX;
    const startWidth = column.offsetWidth;

    const resize = (e) => {
      const diff = e.clientX - startX;
      const newWidth = Math.max(
        this.options.defaultColumnWidth,
        startWidth + diff,
      );
      column.style.width = `${newWidth}px`;
    };

    const stopResize = () => {
      document.removeEventListener("mousemove", resize);
      document.removeEventListener("mouseup", stopResize);
    };

    document.addEventListener("mousemove", resize);
    document.addEventListener("mouseup", stopResize);
  }

  async showQuickAddForm(e) {
    const column = e.target.closest(".kanban-column");
    const columnId = column.dataset.id;

    const form = document.createElement("form");
    form.className = "quick-add-form";
    form.innerHTML = `
            <input type="text" class="form-control"
                   placeholder="Enter card title..."
                   required>
            <div class="form-actions">
                <button type="submit" class="btn btn-xs btn-success">
                    <i class="fa fa-check"></i>
                </button>
                <button type="button" class="btn btn-xs btn-default cancel-quick-add">
                    <i class="fa fa-times"></i>
                </button>
            </div>
        `;

    const container = column.querySelector(".cards-container");
    container.insertBefore(form, container.firstChild);

    const input = form.querySelector("input");
    input.focus();

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = input.value.trim();
      if (!title) return;

      try {
        const response = await this.postData(`${this.options.baseUrl}/cards`, {
          title: title,
          column_id: columnId,
        });

        form.remove();
        this.addCard(response.card, columnId);
        this.updateColumnCount(columnId);
      } catch (error) {
        this.handleError(error);
      }
    });

    form.querySelector(".cancel-quick-add").addEventListener("click", () => {
      form.remove();
    });
  }

  async handleCardAction(action, cardId) {
    const actionConfig = this.options.cardActions.find(
      (a) => a.name === action,
    );
    if (!actionConfig) return;

    if (actionConfig.confirm) {
      const confirmed = await this.confirm(actionConfig.confirm);
      if (!confirmed) return;
    }

    try {
      this.loading(true);
      await actionConfig.handler.call(this, cardId);

      if (actionConfig.refresh !== false) {
        const card = this.cards.get(cardId);
        const columnId = card.closest(".kanban-column").dataset.id;
        await this.loadCards(columnId);
      }
    } catch (error) {
      this.handleError(error);
    } finally {
      this.loading(false);
    }
  }

  async handleColumnAction(action, columnId) {
    const actionConfig = this.options.columnActions.find(
      (a) => a.name === action,
    );
    if (!actionConfig) return;

    if (actionConfig.confirm) {
      const confirmed = await this.confirm(actionConfig.confirm);
      if (!confirmed) return;
    }

    try {
      this.loading(true);
      await actionConfig.handler.call(this, columnId);

      if (actionConfig.refresh !== false) {
        await this.loadCards(columnId);
      }
    } catch (error) {
      this.handleError(error);
    } finally {
      this.loading(false);
    }
  }

  handleSearch() {
    const searchTerm = this.searchInput.value.toLowerCase();

    this.cards.forEach((card) => {
      const title = card.querySelector(".card-title").textContent.toLowerCase();
      const description =
        card.querySelector(".card-description")?.textContent.toLowerCase() ||
        "";

      if (title.includes(searchTerm) || description.includes(searchTerm)) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });

    this.updateColumnCounts();
  }

  async handleFilter(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const filters = {};

    for (const [key, value] of formData.entries()) {
      if (value) {
        filters[key] = value;
      }
    }

    try {
      this.loading(true);
      await Promise.all(
        Array.from(this.columns.keys()).map((columnId) =>
          this.loadCards(columnId),
        ),
      );
    } finally {
      this.loading(false);
    }
  }

  startAutoRefresh() {
    this.refreshInterval = setInterval(() => {
      if (document.hidden) return;

      Promise.all(
        Array.from(this.columns.keys()).map((columnId) =>
          this.loadCards(columnId),
        ),
      ).catch((error) => {
        console.error("Auto-refresh error:", error);
      });
    }, this.options.refreshInterval);
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  isDueDate(date) {
    return new Date(date) < new Date();
  }

  destroy() {
    this.stopAutoRefresh();
    this.sortables.forEach((sortable) => sortable.destroy());
    super.destroy();
  }
}
/ CalendarView Implementation
class CalendarView extends BaseView {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            defaultView: 'month', // month, week, day, agenda
            firstDay: 1, // Monday
            businessHours: {
                start: '09:00',
                end: '17:00',
                days: [1, 2, 3, 4, 5] // Monday to Friday
            },
            eventSources: [],
            eventColors: {},
            eventTemplate: null,
            dateFormat: 'YYYY-MM-DD',
            timeFormat: 'HH:mm',
            showWeekends: true,
            showWeekNumbers: false,
            quickAdd: true,
            dragAndDrop: true,
            resizable: true,
            allDaySlot: true,
            slotDuration: '00:30:00',
            slotMinTime: '00:00:00',
            slotMaxTime: '24:00:00',
            eventOverlap: true,
            eventLimit: true, // "more" link when too many events
            views: {
                month: { eventLimit: 4 },
                week: { eventLimit: false },
                day: { eventLimit: false }
            }
        };
    }

    initialize() {
        super.initialize();
        this.calendar = null;
        this.currentEvents = new Map();
        this.quickAddPopover = null;

        this.initializeCalendar();

        if (this.options.eventSources.length) {
            this.loadEvents();
        }
    }

    setupElements() {
        super.setupElements();
        this.calendarElement = this.container.querySelector('.calendar-main');
        this.sidebarElement = this.container.querySelector('.calendar-sidebar');
        this.miniCalendar = this.container.querySelector('.mini-calendar');
    }

    setupEventListeners() {
        // View selector
        this.container.querySelectorAll('.view-selector .btn').forEach(button => {
            button.addEventListener('click', () => {
                this.switchView(button.dataset.view);
            });
        });

        // Date navigation
        this.container.querySelector('.prev-period').addEventListener('click', () => {
            this.calendar.prev();
        });

        this.container.querySelector('.next-period').addEventListener('click', () => {
            this.calendar.next();
        });

        this.container.querySelector('.current-period').addEventListener('click', () => {
            this.calendar.today();
        });

        // Category filters
        if (this.sidebarElement) {
            this.sidebarElement.querySelectorAll('.category-filter input').forEach(checkbox => {
                checkbox.addEventListener('change', () => this.filterEvents());
            });
        }

        // Mini calendar
        if (this.miniCalendar) {
            this.initializeMiniCalendar();
        }
    }

    initializeCalendar() {
        if (!window.FullCalendar) {
            console.error('FullCalendar is not loaded');
            return;
        }

        this.calendar = new FullCalendar.Calendar(this.calendarElement, {
            initialView: this.options.defaultView,
            headerToolbar: false, // We're using our own header
            firstDay: this.options.firstDay,
            businessHours: this.options.businessHours,
            weekends: this.options.showWeekends,
            weekNumbers: this.options.showWeekNumbers,
            dayMaxEvents: this.options.eventLimit,
            slotDuration: this.options.slotDuration,
            slotMinTime: this.options.slotMinTime,
            slotMaxTime: this.options.slotMaxTime,
            allDaySlot: this.options.allDaySlot,
            editable: this.options.dragAndDrop,
            eventResizableFromStart: this.options.resizable,
            eventOverlap: this.options.eventOverlap,
            views: this.options.views,

            // Event rendering
            eventContent: (info) => this.renderEvent(info),
            eventDidMount: (info) => this.handleEventMount(info),
            eventWillUnmount: (info) => this.handleEventUnmount(info),

            // Event handlers
            dateClick: (info) => this.handleDateClick(info),
            eventClick: (info) => this.handleEventClick(info),
            eventDrop: (info) => this.handleEventDrop(info),
            eventResize: (info) => this.handleEventResize(info),

            // View rendering
            datesSet: (info) => this.handleViewChange(info),
            dayCellDidMount: (info) => this.handleDayCellMount(info),

            // Data fetching
            loading: (isLoading) => this.loading(isLoading),

            // Custom rendering
            dayHeaderContent: (info) => this.renderDayHeader(info),
            dayHeaderDidMount: (info) => this.handleDayHeaderMount(info),
            moreLinkContent: (info) => this.renderMoreLink(info),
            moreLinkClick: (info) => this.handleMoreLinkClick(info)
        });

        this.calendar.render();
    }

    initializeMiniCalendar() {
        new FullCalendar.Calendar(this.miniCalendar, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: '',
                center: 'title',
                right: ''
            },
            dayMaxEvents: 0, // Hide events
            aspectRatio: 1,
            height: 'auto',
            dateClick: (info) => {
                this.calendar.gotoDate(info.date);
            },
            datesSet: (info) => {
                this.highlightCurrentRange(info);
            }
        }).render();
    }

    async loadEvents() {
        try {
            const events = await Promise.all(
                this.options.eventSources.map(source => this.fetchEvents(source))
            );

            this.calendar.removeAllEvents();
            events.flat().forEach(event => {
                this.calendar.addEvent(this.processEvent(event));
            });
        } catch (error) {
            this.handleError(error);
        }
    }

    async fetchEvents(source) {
        const start = this.calendar.view.activeStart;
        const end = this.calendar.view.activeEnd;

        try {
            const response = await this.fetchData(source.url, {
                start: start.toISOString(),
                end: end.toISOString(),
                ...source.extraParams
            });

            return response.events.map(event => ({
                ...event,
                source: source.id
            }));
        } catch (error) {
            console.error(`Error fetching events from source ${source.id}:`, error);
            return [];
        }
    }

    processEvent(event) {
        // Add default styling based on category
        if (event.category && this.options.eventColors[event.category]) {
            event.backgroundColor = this.options.eventColors[event.category];
        }

        // Handle recurring events
        if (event.recurring) {
            event.classNames = [...(event.classNames || []), 'recurring-event'];
        }

        // Handle all-day events
        if (event.allDay) {
            event.classNames = [...(event.classNames || []), 'all-day-event'];
        }

        return event;
    }

    renderEvent(info) {
        if (this.options.eventTemplate) {
            return this.options.eventTemplate(info);
        }

        const event = info.event;
        return {
            html: `
                <div class="fc-event-main-content">
                    ${event.allDay ? `
                        <div class="fc-event-title">
                            ${event.title}
                            ${event.recurring ? '<i class="fa fa-repeat"></i>' : ''}
                        </div>
                    ` : `
                        <div class="fc-event-time">
                            ${info.timeText}
                            ${event.recurring ? '<i class="fa fa-repeat"></i>' : ''}
                        </div>
                        <div class="fc-event-title">
                            ${event.title}
                        </div>
                    `}
                    ${event.location ? `
                        <div class="fc-event-location">
                            <i class="fa fa-map-marker"></i> ${event.location}
                        </div>
                    ` : ''}
                </div>
            `
        };
    }

    handleEventMount(info) {
        const event = info.event;
        const element = info.el;

        // Store reference
        this.currentEvents.set(event.id, {
            event,
            element
        });

        // Add custom classes
        if (event.url) {
            element.classList.add('clickable');
        }

        if (this.isOverdue(event)) {
            element.classList.add('overdue');
        }

        // Add tooltip
        if (event.extendedProps.description) {
            element.setAttribute('title', event.extendedProps.description);
            // Initialize tooltip if using Bootstrap
            if (window.bootstrap?.Tooltip) {
                new bootstrap.Tooltip(element);
            }
        }
    }

    handleEventUnmount(info) {
        this.currentEvents.delete(info.event.id);

        // Cleanup tooltip if using Bootstrap
        if (window.bootstrap?.Tooltip) {
            const tooltip = bootstrap.Tooltip.getInstance(info.el);
            if (tooltip) {
                tooltip.dispose();
            }
        }
    }

    async handleDateClick(info) {
        if (!this.options.quickAdd) return;

        // Remove any existing quick add form
        this.removeQuickAddForm();

        const form = document.createElement('div');
        form.className = 'quick-add-popover';
        form.innerHTML = `
            <form class="quick-add-form">
                <div class="form-group">
                    <input type="text" class="form-control" name="title"
                           placeholder="Event title" required>
                </div>
                <div class="form-group">
                    <div class="input-group">
                        <input type="text" class="form-control" name="start"
                               value="${info.dateStr}" required>
                        <span class="input-group-addon">
                            <i class="fa fa-clock-o"></i>
                        </span>
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary btn-sm">
                        Add Event
                    </button>
                    <button type="button" class="btn btn-default btn-sm" data-dismiss="popover">
                        Cancel
                    </button>
                </div>
            </form>
        `;

        // Position the form
        const rect = info.dayEl.getBoundingClientRect();
        form.style.position = 'absolute';
        form.style.top = `${rect.top + window.scrollY}px`;
        form.style.left = `${rect.left + window.scrollX}px`;

        document.body.appendChild(form);
        this.quickAddPopover = form;

        // Initialize datetime picker if available
        if (window.flatpickr) {
            flatpickr(form.querySelector('[name="start"]'), {
                enableTime: !info.allDay,
                defaultHour: info.date.getHours(),
                defaultMinute: info.date.getMinutes(),
                dateFormat: info.allDay ? 'Y-m-d' : 'Y-m-d H:i'
            });
        }

        // Handle form submission
        form.querySelector('form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(e.target);
            try {
                const response = await this.postData(
                    `${this.options.baseUrl}/events`,
                    {
                        title: formData.get('title'),
                        start: formData.get('start'),
                        allDay: info.allDay
                    }
                );

                this.calendar.addEvent(this.processEvent(response.event));
                this.removeQuickAddForm();
            } catch (error) {
                this.handleError(error);
            }
        });

        // Handle cancel
        form.querySelector('[data-dismiss="popover"]').addEventListener('click', () => {
            this.removeQuickAddForm();
        });

        // Handle click outside
        document.addEventListener('click', (e) => {
            if (!form.contains(e.target) && this.quickAddPopover) {
                this.removeQuickAddForm();
            }
        });

        // Focus title input
        form.querySelector('[name="title"]').focus();
    }

    removeQuickAddForm() {
        if (this.quickAddPopover) {
            this.quickAddPopover.remove();
            this.quickAddPopover = null;
        }
    }

    async handleEventClick(info) {
        if (info.event.url) {
            info.jsEvent.preventDefault();
            window.open(info.event.url, '_blank');
            return;
        }

        // Show event details modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${info.event.title}</h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        ${this.renderEventDetails(info.event)}
                    </div>
                    <div class="modal-footer">
                        ${this.options.permissions.edit ? `
                            <button type="button" class="btn btn-primary edit-event">
                                <i class="fa fa-edit"></i> Edit
                            </button>
                        ` : ''}
                        ${this.options.permissions.delete ? `
                            <button type="button" class="btn btn-danger delete-event">
                                <i class="fa fa-trash"></i> Delete
                            </button>
                        ` : ''}
                        <button type="button" class="btn btn-default" data-dismiss="modal">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Initialize Bootstrap modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Handle edit
        modal.querySelector('.edit-event')?.addEventListener('click', () => {
            modalInstance.hide();
            this.showEventForm(info.event);
        });

        // Handle delete
        modal.querySelector('.delete-event')?.addEventListener('click', async () => {
            if (await this.confirm('Are you sure you want to delete this event?')) {
                try {
                    await this.deleteEvent(info.event);
                    modalInstance.hide();
                } catch (error) {
                    this.handleError(error);
                }
            }
        });

        // Cleanup on hide
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    renderEventDetails(event) {
        return `
            <div class="event-details">
                <div class="event-time">
                    <i class="fa fa-clock-o"></i>
                    ${this.formatEventTime(event)}
                </div>

                ${event.extendedProps.location ? `
                    <div class="event-location">
                        <i class="fa fa-map-marker"></i>
                        ${event.extendedProps.location}
                    </div>
                ` : ''}

                ${event.extendedProps.description ? `
                    <div class="event-description">
                        ${event.extendedProps.description}
                    </div>
                ` : ''}

                ${event.extendedProps.attendees?.length ? `
                    <div class="event-attendees">
                        <h6>Attendees:</h6>
                        <ul class="attendee-list">
                            ${event.extendedProps.attendees.map(attendee => `
                                <li class="attendee">
                                    ${attendee.avatar ? `
                                        <img src="${attendee.avatar}"
                                             class="attendee-avatar"
                                             alt="${attendee.name}">
                                    ` : ''}
                                    <span class="attendee-name">${attendee.name}</span>
                                    <span class="attendee-status status-${attendee.status}">
                                        ${attendee.status}
                                    </span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${event.extendedProps.attachments?.length ? `
                    <div class="event-attachments">
                        <h6>Attachments:</h6>
                        <ul class="attachment-list">
                            ${event.extendedProps.attachments.map(attachment => `
                                <li class="attachment">
                                    <a href="${attachment.url}" target="_blank">
                                        <i class="fa fa-paperclip"></i>
                                        ${attachment.name}
                                    </a>
                                    <span class="attachment-size">
                                        ${this.formatBytes(attachment.size)}
                                    </span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    formatEventTime(event) {
        if (event.allDay) {
            return 'All day';
        }

        const start = event.start;
        const end = event.end;

        if (!end) {
            return Utils.formatDate(start, this.options.timeFormat);
        }

        if (start.toDateString() === end.toDateString()) {
            return `${Utils.formatDate(start, this.options.timeFormat)} - ${Utils.formatDate(end, this.options.timeFormat)}`;
        }

        return `${Utils.formatDate(start, this.options.dateFormat)} ${Utils.formatDate(start, this.options.timeFormat)} - ${Utils.formatDate(end, this.options.dateFormat)} ${Utils.formatDate(end, this.options.timeFormat)}`;
    }

    async handleEventDrop(info) {
        try {
            await this.updateEvent(info.event, {
                start: info.event.start.toISOString(),
                end: info.event.end?.toISOString(),
                allDay: info.event.allDay
            });
        } catch (error) {
            info.revert();
            this.handleError(error);
        }
    }

    async handleEventResize(info) {
        try {
            await this.updateEvent(info.event, {
                end: info.event.end.toISOString()
            });
        } catch (error) {
            info.revert();
            this.handleError(error);
        }
    }

    async updateEvent(event, data) {
        const response = await this.postData(
            `${this.options.baseUrl}/events/${event.id}`,
            data,
            'PUT'
        );

        // Update event with response data
        Object.assign(event, this.processEvent(response.event));
    }

    async deleteEvent(event) {
        await this.postData(
            `${this.options.baseUrl}/events/${event.id}`,
            null,
            'DELETE'
        );
        event.remove();
    }

    handleViewChange(info) {
        // Update period label
        this.updatePeriodLabel(info.view);

        // Update active view button
        this.container.querySelectorAll('.view-selector .btn').forEach(button => {
            button.classList.toggle('active', button.dataset.view === info.view.type);
        });

        // Reload events if needed
        if (this.shouldReloadEvents(info)) {
            this.loadEvents();
        }

        // Update mini calendar
        this.updateMiniCalendar(info);
    }

    updatePeriodLabel(view) {
        const label = this.container.querySelector('.current-period-label');
        if (!label) return;

        let title = view.title;

        // Customize format if needed
        switch (view.type) {
            case 'timeGridWeek':
                title = `Week ${view.currentStart.getWeek()}, ${view.currentStart.getFullYear()}`;
                break;
            case 'timeGridDay':
                title = Utils.formatDate(view.currentStart, 'dddd, MMMM D, YYYY');
                break;
        }

        label.textContent = title;
    }

    shouldReloadEvents(info) {
        // Implement your logic to determine if events should be reloaded
        // For example, when switching between month/week/day views
        return true;
    }

    updateMiniCalendar(info) {
        if (!this.miniCalendar) return;

        const miniCalendar = this.miniCalendar.getApi();
        miniCalendar.gotoDate(info.view.currentStart);
        this.highlightCurrentRange(info);
    }

    highlightCurrentRange(info) {
        if (!this.miniCalendar) return;

        this.miniCalendar.querySelectorAll('.fc-highlight').forEach(el => {
            el.classList.remove('fc-highlight');
        });

        const start = info.view.currentStart;
        const end = info.view.currentEnd;

        this.miniCalendar.querySelectorAll('.fc-daygrid-day').forEach(dayEl => {
            const date = new Date(dayEl.dataset.date);
            if (date >= start && date < end) {
                dayEl.classList.add('fc-highlight');
            }
        });
    }

    switchView(viewName) {
        this.calendar.changeView(viewName);
    }

    filterEvents() {
        const selectedCategories = new Set();

        this.sidebarElement.querySelectorAll('.category-filter input:checked').forEach(checkbox => {
            selectedCategories.add(checkbox.value);
        });

        this.currentEvents.forEach(({event, element}) => {
            const visible = selectedCategories.size === 0 ||
                          selectedCategories.has(event.extendedProps.category);
            element.style.display = visible ? '' : 'none';
        });
    }

    isOverdue(event) {
        return !event.allDay &&
               event.end &&
               new Date(event.end) < new Date() &&
               !event.extendedProps.completed;
    }

    formatBytes(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
    }

    destroy() {
        if (this.calendar) {
            this.calendar.destroy();
        }
        if (this.miniCalendar) {
            this.miniCalendar.destroy();
        }
        super.destroy();
    }
}
class PivotView extends BaseView {
    getDefaultOptions() {
        return {
            ...super.getDefaultOptions(),
            fields: [],                // Available fields for analysis
            measures: [],             // Numerical fields that can be aggregated
            dimensions: [],           // Fields that can be used for grouping
            filters: [],              // Fields that can be used for filtering
            aggregators: {            // Available aggregation functions
                sum: (values) => values.reduce((a, b) => a + b, 0),
                avg: (values) => values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0,
                count: (values) => values.length,
                min: (values) => Math.min(...values),
                max: (values) => Math.max(...values),
                median: (values) => {
                    values.sort((a, b) => a - b);
                    const mid = Math.floor(values.length / 2);
                    return values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2;
                }
            },
            defaultAggregator: 'sum',
            dateRanges: {            // Predefined date ranges
                today: () => ({
                    start: new Date().setHours(0, 0, 0, 0),
                    end: new Date().setHours(23, 59, 59, 999)
                }),
                thisWeek: () => {
                    const start = new Date();
                    start.setDate(start.getDate() - start.getDay());
                    start.setHours(0, 0, 0, 0);
                    const end = new Date(start);
                    end.setDate(end.getDate() + 6);
                    end.setHours(23, 59, 59, 999);
                    return { start, end };
                },
                thisMonth: () => {
                    const start = new Date();
                    start.setDate(1);
                    start.setHours(0, 0, 0, 0);
                    const end = new Date(start.getFullYear(), start.getMonth() + 1, 0, 23, 59, 59, 999);
                    return { start, end };
                },
                thisYear: () => {
                    const start = new Date(new Date().getFullYear(), 0, 1, 0, 0, 0, 0);
                    const end = new Date(new Date().getFullYear(), 11, 31, 23, 59, 59, 999);
                    return { start, end };
                }
            },
            formatters: {           // Value formatters
                number: (value) => new Intl.NumberFormat().format(value),
                currency: (value) => new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD'
                }).format(value),
                percentage: (value) => new Intl.NumberFormat('en-US', {
                    style: 'percent',
                    minimumFractionDigits: 2
                }).format(value / 100),
                date: (value) => new Date(value).toLocaleDateString(),
                datetime: (value) => new Date(value).toLocaleString()
            },
            showTotals: true,      // Show row and column totals
            showSubtotals: true,   // Show subtotals for nested dimensions
            allowDrilldown: true,  // Allow drilling down into data
            maxDrilldownLevels: 5, // Maximum levels for drilldown
            autoRefresh: false,    // Automatically refresh data
            refreshInterval: 300000, // 5 minutes
            exportFormats: ['csv', 'excel', 'pdf'],
            chartOptions: {
                types: ['bar', 'line', 'pie', 'scatter'],
                defaultType: 'bar',
                colors: [
                    '#4e79a7', '#f28e2c', '#e15759', '#76b7b2',
                    '#59a14f', '#edc949', '#af7aa1', '#ff9da7'
                ]
            }
        };
    }

    initialize() {
        super.initialize();

        this.pivotData = null;      // Processed pivot data
        this.rawData = null;        // Raw data from server
        this.currentConfig = null;  // Current pivot configuration
        this.chart = null;          // Chart instance
        this.drilldownStack = [];   // Stack for drilldown history

        this.initializeFields();
        this.loadData();

        if (this.options.autoRefresh) {
            this.startAutoRefresh();
        }
    }

    setupElements() {
        super.setupElements();

        // Main sections
        this.configPanel = this.container.querySelector('.config-panel');
        this.resultsPanel = this.container.querySelector('.results-panel');

        // Configuration elements
        this.rowsDropZone = this.configPanel.querySelector('.row-fields');
        this.colsDropZone = this.configPanel.querySelector('.column-fields');
        this.valuesDropZone = this.configPanel.querySelector('.value-fields');
        this.filtersDropZone = this.configPanel.querySelector('.filter-fields');

        // Results elements
        this.pivotTable = this.resultsPanel.querySelector('.pivot-table');
        this.chartContainer = this.resultsPanel.querySelector('.chart-container');
    }

    setupEventListeners() {
        // Field drag and drop
        this.initializeDragAndDrop();

        // View controls
        this.container.querySelector('.view-controls').addEventListener('click', e => {
            const viewButton = e.target.closest('[data-view]');
            if (viewButton) {
                this.switchView(viewButton.dataset.view);
            }
        });

        // Apply button
        this.container.querySelector('#apply-analysis').addEventListener('click', () => {
            this.applyAnalysis();
        });

        // Save/Load views
        this.container.querySelector('#save-view').addEventListener('click', () => {
            this.showSaveViewDialog();
        });

        this.container.querySelector('#load-view').addEventListener('click', () => {
            this.showLoadViewDialog();
        });

        // Export buttons
        this.container.querySelectorAll('[data-export-type]').forEach(button => {
            button.addEventListener('click', (e) => {
                this.exportData(e.target.dataset.exportType);
            });
        });

        // Drilldown handling
        if (this.options.allowDrilldown) {
            this.pivotTable.addEventListener('click', e => {
                const drilldownCell = e.target.closest('[data-drilldown]');
                if (drilldownCell) {
                    this.handleDrilldown(drilldownCell);
                }
            });
        }
    }

    initializeDragAndDrop() {
        const dropZones = [
            this.rowsDropZone,
            this.colsDropZone,
            this.valuesDropZone,
            this.filtersDropZone
        ];

        // Make fields draggable
        this.container.querySelectorAll('.field-item').forEach(field => {
            field.draggable = true;

            field.addEventListener('dragstart', e => {
                e.dataTransfer.setData('text/plain', field.dataset.field);
                field.classList.add('dragging');
            });

            field.addEventListener('dragend', () => {
                field.classList.remove('dragging');
            });
        });

        // Setup drop zones
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', e => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', e => {
                e.preventDefault();
                zone.classList.remove('drag-over');

                const fieldName = e.dataTransfer.getData('text/plain');
                this.addFieldToZone(fieldName, zone);
            });
        });
    }

    addFieldToZone(fieldName, zone) {
        const fieldConfig = this.options.fields.find(f => f.name === fieldName);
        if (!fieldConfig) return;

        const fieldElement = document.createElement('div');
        fieldElement.className = 'dropped-field';
        fieldElement.dataset.field = fieldName;

        fieldElement.innerHTML = `
            <span class="field-name">${fieldConfig.label}</span>
            <div class="field-actions">
                ${zone === this.valuesDropZone ? `
                    <select class="aggregator-select">
                        ${Object.keys(this.options.aggregators).map(agg => `
                            <option value="${agg}"
                                    ${agg === this.options.defaultAggregator ? 'selected' : ''}>
                                ${this.formatAggregatorName(agg)}
                            </option>
                        `).join('')}
                    </select>
                ` : ''}
                <button type="button" class="btn btn-xs btn-link remove-field"
                        title="Remove field">
                    <i class="fa fa-times"></i>
                </button>
            </div>
        `;

        // Add remove handler
        fieldElement.querySelector('.remove-field').addEventListener('click', () => {
            fieldElement.remove();
        });

        // Add aggregator change handler for value fields
        const aggregatorSelect = fieldElement.querySelector('.aggregator-select');
        if (aggregatorSelect) {
            aggregatorSelect.addEventListener('change', () => {
                this.updateFieldAggregator(fieldName, aggregatorSelect.value);
            });
        }

        zone.appendChild(fieldElement);
    }
    // Data Processing Methods
     async loadData() {
         try {
             this.loading(true);
             const response = await this.fetchData(this.options.baseUrl);
             this.rawData = response.data;
             this.processData();
         } catch (error) {
             this.handleError(error);
         } finally {
             this.loading(false);
         }
     }

     processData() {
         const config = this.getCurrentConfig();
         this.currentConfig = config;

         if (!this.rawData || !config.values.length) {
             this.pivotData = null;
             this.renderEmptyState();
             return;
         }

         try {
             // Apply filters first
             let filteredData = this.applyFilters(this.rawData, config.filters);

             // Group data by dimensions
             const groupedData = this.groupData(filteredData, config);

             // Calculate aggregates
             this.pivotData = this.calculateAggregates(groupedData, config);

             // Add totals if enabled
             if (this.options.showTotals) {
                 this.addTotals(this.pivotData, config);
             }

             // Render results
             this.renderResults();
         } catch (error) {
             console.error('Error processing data:', error);
             this.showNotification('Error processing data', 'error');
         }
     }

     getCurrentConfig() {
         const config = {
             rows: [],
             columns: [],
             values: [],
             filters: []
         };

         // Get row fields
         this.rowsDropZone.querySelectorAll('.dropped-field').forEach(field => {
             config.rows.push({
                 name: field.dataset.field,
                 ...this.options.fields.find(f => f.name === field.dataset.field)
             });
         });

         // Get column fields
         this.colsDropZone.querySelectorAll('.dropped-field').forEach(field => {
             config.columns.push({
                 name: field.dataset.field,
                 ...this.options.fields.find(f => f.name === field.dataset.field)
             });
         });

         // Get value fields
         this.valuesDropZone.querySelectorAll('.dropped-field').forEach(field => {
             const aggregator = field.querySelector('.aggregator-select')?.value ||
                              this.options.defaultAggregator;
             config.values.push({
                 name: field.dataset.field,
                 aggregator: aggregator,
                 ...this.options.fields.find(f => f.name === field.dataset.field)
             });
         });

         // Get filters
         this.filtersDropZone.querySelectorAll('.dropped-field').forEach(field => {
             config.filters.push({
                 name: field.dataset.field,
                 ...this.options.fields.find(f => f.name === field.dataset.field)
             });
         });

         return config;
     }

     applyFilters(data, filters) {
         if (!filters.length) return data;

         return data.filter(row => {
             return filters.every(filter => {
                 const filterElement = this.filtersDropZone.querySelector(
                     `[data-field="${filter.name}"]`
                 );
                 const filterValue = filterElement?.querySelector('input, select')?.value;

                 if (!filterValue) return true;

                 const rowValue = row[filter.name];

                 switch (filter.type) {
                     case 'date':
                         return this.applyDateFilter(rowValue, filterValue, filter);
                     case 'number':
                         return this.applyNumberFilter(rowValue, filterValue, filter);
                     case 'select':
                         return filterValue === 'all' || rowValue === filterValue;
                     default:
                         return rowValue?.toString().toLowerCase()
                             .includes(filterValue.toLowerCase());
                 }
             });
         });
     }

     groupData(data, config) {
         const dimensions = [...config.rows, ...config.columns];
         if (!dimensions.length) return { values: data };

         return data.reduce((acc, row) => {
             let current = acc;

             // Create path through dimension hierarchy
             const path = dimensions.map(dim => ({
                 dimension: dim.name,
                 value: this.formatDimensionValue(row[dim.name], dim)
             }));

             // Navigate/create tree structure
             path.forEach((level, index) => {
                 const key = `${level.dimension}:${level.value}`;

                 if (index === path.length - 1) {
                     current[key] = current[key] || { values: [] };
                     current[key].values.push(row);
                 } else {
                     current[key] = current[key] || {};
                     current = current[key];
                 }
             });

             return acc;
         }, {});
     }

     calculateAggregates(groupedData, config) {
         const result = {
             dimensions: {},
             values: {}
         };

         const processNode = (node, path = []) => {
             if (node.values) {
                 // Leaf node - calculate aggregates
                 config.values.forEach(value => {
                     const values = node.values.map(row => row[value.name])
                                             .filter(v => v != null);

                     const aggregator = this.options.aggregators[value.aggregator];
                     const aggregateValue = values.length ? aggregator(values) : null;

                     // Store result
                     const resultPath = path.join('|');
                     if (!result.values[resultPath]) {
                         result.values[resultPath] = {};
                     }
                     result.values[resultPath][value.name] = aggregateValue;
                 });
             } else {
                 // Interior node - recurse
                 Object.entries(node).forEach(([key, childNode]) => {
                     const [dimension, value] = key.split(':');

                     // Track unique dimension values
                     if (!result.dimensions[dimension]) {
                         result.dimensions[dimension] = new Set();
                     }
                     result.dimensions[dimension].add(value);

                     processNode(childNode, [...path, key]);
                 });
             }
         };

         processNode(groupedData);

         // Convert Sets to Arrays
         Object.keys(result.dimensions).forEach(dim => {
             result.dimensions[dim] = Array.from(result.dimensions[dim]);
         });

         return result;
     }

     addTotals(pivotData, config) {
         const addDimensionTotals = (dimension) => {
             const values = {};

             // Get all paths that include this dimension
             const relevantPaths = Object.keys(pivotData.values).filter(path =>
                 path.includes(`${dimension}:`)
             );

             // Group paths by their value for this dimension
             const pathsByValue = relevantPaths.reduce((acc, path) => {
                 const dimValue = path.split('|')
                     .find(p => p.startsWith(`${dimension}:`))
                     ?.split(':')[1];

                 if (dimValue) {
                     if (!acc[dimValue]) acc[dimValue] = [];
                     acc[dimValue].push(path);
                 }
                 return acc;
             }, {});

             // Calculate totals for each value
             Object.entries(pathsByValue).forEach(([dimValue, paths]) => {
                 const totalKey = `${dimension}:${dimValue}|total`;
                 values[totalKey] = {};

                 config.values.forEach(value => {
                     const aggregator = this.options.aggregators[value.aggregator];
                     const vals = paths.map(p => pivotData.values[p][value.name])
                                     .filter(v => v != null);

                     values[totalKey][value.name] = vals.length ?
                         aggregator(vals) : null;
                 });
             });

             // Add grand total
             const grandTotalKey = `${dimension}:total`;
             values[grandTotalKey] = {};

             config.values.forEach(value => {
                 const aggregator = this.options.aggregators[value.aggregator];
                 const vals = Object.values(pivotData.values)
                     .map(v => v[value.name])
                     .filter(v => v != null);

                 values[grandTotalKey][value.name] = vals.length ?
                     aggregator(vals) : null;
             });

             Object.assign(pivotData.values, values);
         };

         // Add totals for each dimension
         [...config.rows, ...config.columns].forEach(dim => {
             addDimensionTotals(dim.name);
         });
     }

     formatDimensionValue(value, dimension) {
         if (value == null) return 'Null';

         switch (dimension.type) {
             case 'date':
                 return this.options.formatters.date(value);
             case 'datetime':
                 return this.options.formatters.datetime(value);
             case 'number':
                 return this.options.formatters.number(value);
             default:
                 return value.toString();
         }
     }

     formatValue(value, valueConfig) {
         if (value == null) return '';

         const formatter = this.options.formatters[valueConfig.format] ||
                         this.options.formatters.number;
         return formatter(value);
     }

     formatAggregatorName(name) {
         return name.charAt(0).toUpperCase() + name.slice(1);
     }

     // Continue with rendering methods...
     // Rendering Methods
     renderResults() {
         if (!this.pivotData) {
             this.renderEmptyState();
             return;
         }

         const view = this.container.querySelector('.view-controls .active')
                                  ?.dataset.view || 'table';

         if (view === 'table') {
             this.renderPivotTable();
         } else {
             this.renderPivotChart();
         }
     }

     renderEmptyState() {
         const content = this.currentConfig.values.length === 0 ?
             `
                 <div class="empty-state">
                     <i class="fa fa-table"></i>
                     <p>Drag and drop value fields to start analysis</p>
                 </div>
             ` :
             `
                 <div class="empty-state">
                     <i class="fa fa-database"></i>
                     <p>No data available for the current configuration</p>
                 </div>
             `;

         this.pivotTable.innerHTML = content;
         if (this.chart) {
             this.chart.destroy();
             this.chart = null;
         }
     }

     renderPivotTable() {
         const config = this.currentConfig;
         const data = this.pivotData;

         // Generate column headers
         const columnDimensions = config.columns;
         const columnValues = this.generateColumnHeaders(data, columnDimensions);

         // Generate row headers
         const rowDimensions = config.rows;
         const rowValues = this.generateRowHeaders(data, rowDimensions);

         // Build table HTML
         let html = '<table class="pivot-table">';

         // Header rows
         html += this.renderTableHeaders(columnDimensions, columnValues, rowDimensions);

         // Data rows
         html += this.renderTableRows(rowValues, columnValues, config);

         html += '</table>';

         this.pivotTable.innerHTML = html;
     }

     generateColumnHeaders(data, columnDimensions) {
         if (!columnDimensions.length) return [['']];

         const headers = [];
         const processLevel = (dimension, level = 0, prefix = '') => {
             const values = data.dimensions[dimension.name];

             if (level === columnDimensions.length - 1) {
                 return values.map(value => `${prefix}${dimension.name}:${value}`);
             }

             return values.flatMap(value => {
                 const newPrefix = `${prefix}${dimension.name}:${value}|`;
                 return processLevel(columnDimensions[level + 1], level + 1, newPrefix);
             });
         };

         return processLevel(columnDimensions[0]);
     }

     generateRowHeaders(data, rowDimensions) {
         if (!rowDimensions.length) return [['']];

         const headers = [];
         const processLevel = (dimension, level = 0, prefix = '') => {
             const values = data.dimensions[dimension.name];

             if (level === rowDimensions.length - 1) {
                 return values.map(value => `${prefix}${dimension.name}:${value}`);
             }

             return values.flatMap(value => {
                 const newPrefix = `${prefix}${dimension.name}:${value}|`;
                 return processLevel(rowDimensions[level + 1], level + 1, newPrefix);
             });
         };

         return processLevel(rowDimensions[0]);
     }

     renderTableHeaders(columnDimensions, columnValues, rowDimensions) {
         let html = '<thead>';

         // Calculate header height
         const headerHeight = columnDimensions.length;
         const rowHeaderWidth = rowDimensions.length;

         // Generate header rows
         for (let i = 0; i < headerHeight; i++) {
             html += '<tr>';

             // Empty cells for row headers
             if (i === headerHeight - 1) {
                 html += rowDimensions.map(dim =>
                     `<th class="row-header">${dim.label}</th>`
                 ).join('');
             } else {
                 html += `<th colspan="${rowHeaderWidth}"></th>`;
             }

             // Column headers
             let currentPrefix = '';
             let colspan = 1;
             const levelSize = this.currentConfig.values.length;

             columnValues.forEach((fullPath, colIndex) => {
                 const parts = fullPath.split('|');
                 const currentPart = parts[i];

                 if (currentPart === currentPrefix) {
                     colspan += levelSize;
                 } else {
                     if (currentPrefix) {
                         html += `<th colspan="${colspan}">${this.formatHeaderValue(currentPrefix)}</th>`;
                     }
                     currentPrefix = currentPart;
                     colspan = levelSize;
                 }

                 // Handle last column
                 if (colIndex === columnValues.length - 1) {
                     html += `<th colspan="${colspan}">${this.formatHeaderValue(currentPrefix)}</th>`;
                 }
             });

             html += '</tr>';
         }

         // Value headers
         if (this.currentConfig.values.length > 1) {
             html += '<tr>';

             // Empty cells for row headers
             html += `<th colspan="${rowHeaderWidth}"></th>`;

             // Value labels
             columnValues.forEach(() => {
                 this.currentConfig.values.forEach(value => {
                     html += `<th class="value-header">${value.label}</th>`;
                 });
             });

             html += '</tr>';
         }

         html += '</thead>';
         return html;
     }

     renderTableRows(rowValues, columnValues, config) {
         let html = '<tbody>';

         rowValues.forEach((rowPath, rowIndex) => {
             html += '<tr>';

             // Row headers
             const rowParts = rowPath.split('|');
             rowParts.forEach((part, i) => {
                 const [dimension, value] = part.split(':');
                 const isFirstInGroup = i === 0 ||
                     rowParts[i - 1] !== rowValues[rowIndex - 1]?.split('|')[i];

                 if (isFirstInGroup) {
                     // Calculate rowspan
                     let rowspan = 1;
                     let nextRow = rowIndex + 1;
                     while (nextRow < rowValues.length &&
                            rowValues[nextRow].split('|')[i] === part) {
                         rowspan++;
                         nextRow++;
                     }

                     html += `
                         <th class="row-header" rowspan="${rowspan}"
                             ${this.options.allowDrilldown ?
                               `data-drilldown="${dimension}:${value}"` : ''}>
                             ${this.formatHeaderValue(part)}
                         </th>
                     `;
                 }
             });

             // Data cells
             columnValues.forEach(colPath => {
                 const path = rowPath + (colPath ? '|' + colPath : '');
                 const values = this.pivotData.values[path] || {};

                 config.values.forEach(value => {
                     const cellValue = values[value.name];
                     html += `
                         <td class="value-cell"
                             data-value="${cellValue ?? ''}"
                             title="${value.label}: ${this.formatValue(cellValue, value)}">
                             ${this.formatValue(cellValue, value)}
                         </td>
                     `;
                 });
             });

             html += '</tr>';
         });

         // Render totals if enabled
         if (this.options.showTotals) {
             html += this.renderTotalRows(rowValues, columnValues, config);
         }

         html += '</tbody>';
         return html;
     }

     renderTotalRows(rowValues, columnValues, config) {
         let html = '';

         // Column totals
         if (config.columns.length) {
             html += '<tr class="total-row">';

             // Total label
             html += `<th colspan="${config.rows.length}">Total</th>`;

             // Total values
             columnValues.forEach(colPath => {
                 const totalPath = colPath ? `${colPath}|total` : 'total';
                 const values = this.pivotData.values[totalPath] || {};

                 config.values.forEach(value => {
                     const cellValue = values[value.name];
                     html += `
                         <td class="total-cell"
                             data-value="${cellValue ?? ''}"
                             title="Total ${value.label}: ${this.formatValue(cellValue, value)}">
                             ${this.formatValue(cellValue, value)}
                         </td>
                     `;
                 });
             });

             html += '</tr>';
         }

         return html;
     }

     formatHeaderValue(header) {
         if (!header) return '';

         const [dimension, value] = header.split(':');
         const dimensionConfig = this.options.fields.find(f => f.name === dimension);

         if (!dimensionConfig) return value;

         return dimensionConfig.formatter ?
                dimensionConfig.formatter(value) :
                value;
     }

     renderPivotChart() {
         if (!window.Chart) {
             console.error('Chart.js is not loaded');
             return;
         }

         const chartType = this.container.querySelector('.chart-type-select')?.value ||
                          this.options.chartOptions.defaultType;

         const config = this.getChartConfig(chartType);

         if (this.chart) {
             this.chart.destroy();
         }

         const ctx = this.chartContainer.querySelector('canvas').getContext('2d');
         this.chart = new Chart(ctx, config);
     }

     getChartConfig(chartType) {
         const data = this.prepareChartData(chartType);
         const options = this.getChartOptions(chartType);

         return {
             type: chartType,
             data: data,
             options: options
         };
     }

     prepareChartData(chartType) {
         const config = this.currentConfig;
         const data = this.pivotData;

         // Prepare labels and datasets based on chart type
         switch (chartType) {
             case 'bar':
             case 'line':
                 return this.prepareBarLineData();
             case 'pie':
                 return this.preparePieData();
             case 'scatter':
                 return this.prepareScatterData();
             default:
                 return this.prepareBarLineData();
         }
     }

     prepareBarLineData() {
         const config = this.currentConfig;
         const data = this.pivotData;

         // Get unique labels (e.g., from row or column dimensions)
         const labels = Object.keys(data.dimensions[config.rows[0]?.name ||
                                                  config.columns[0]?.name || ''] || {});

         // Prepare datasets
         const datasets = config.values.map(value => {
             return {
                 label: value.label,
                 data: labels.map(label => {
                     const path = `${config.rows[0]?.name ||
                                   config.columns[0]?.name}:${label}`;
                     return data.values[path]?.[value.name] || 0;
                 }),
                 backgroundColor: this.options.chartOptions.colors[0],
                 borderColor: this.options.chartOptions.colors[0],
                 fill: false
             };
         });

         return { labels, datasets };
     }

     preparePieData() {
         const config = this.currentConfig;
         const data = this.pivotData;

         // Use only the first value field for pie charts
         const valueField = config.values[0];
         if (!valueField) return { labels: [], datasets: [] };

         const dimensionField = config.rows[0] || config.columns[0];
         if (!dimensionField) return { labels: [], datasets: [] };

         const labels = Object.keys(data.dimensions[dimensionField.name] || {});
         const values = labels.map(label => {
             const path = `${dimensionField.name}:${label}`;
             return data.values[path]?.[valueField.name] || 0;
         });

         return {
             labels,
             datasets: [{
                 data: values,
                 backgroundColor: this.options.chartOptions.colors,
                 hoverOffset: 4
             }]
         };
     }

     prepareScatterData() {
         // Requires at least two value fields
         if (this.currentConfig.values.length < 2) {
             return { datasets: [] };
         }

         const value1 = this.currentConfig.values[0];
         const value2 = this.currentConfig.values[1];

         const datasets = [{
             label: `${value1.label} vs ${value2.label}`,
             data: Object.entries(this.pivotData.values).map(([path, values]) => ({
                 x: values[value1.name] || 0,
                 y: values[value2.name] || 0
             })),
             backgroundColor: this.options.chartOptions.colors[0]
         }];

         return { datasets };
     }

     getChartOptions(chartType) {
         const baseOptions = {
             responsive: true,
             maintainAspectRatio: false,
             plugins: {
                 legend: {
                     position: 'top',
                 },
                 title: {
                     display: true,
                     text: this.getChartTitle()
                 },
                 tooltip: {
                     callbacks: {
                         label: (context) => {
                             const value = context.raw;
                             const valueConfig = this.currentConfig.values[context.datasetIndex];
                             return `${context.dataset.label}: ${this.formatValue(value, valueConfig)}`;
                         }
                     }
                 }
             }
         };

         // Add chart-specific options
         switch (chartType) {
             case 'bar':
                 return {
                     ...baseOptions,
                     scales: {
                         y: {
                             beginAtZero: true
                         }
                     }
                 };
             case 'line':
                 return {
                     ...baseOptions,
                     elements: {
                         line: {
                             tension: 0.4
                         }
                     }
                 };
             case 'pie':
                 return {
                     ...baseOptions,
                     plugins: {
                         ...baseOptions.plugins,
                         legend: {
                             position: 'right'
                         }
                     }
                 };
             case 'scatter':
                 return {
                     ...baseOptions,
                     scales: {
                         x: {
                             type: 'linear',
                             position: 'bottom'
                         },
                         y: {
                             type: 'linear',
                             position: 'left'
                         }
                     }
                 };
             default:
                 return baseOptions;
         }
     }

     getChartTitle() {
         const config = this.currentConfig;
         const parts = [];

         if (config.values.length) {
             parts.push(config.values.map(v => v.label).join(' vs '));
         }

         if (config.rows.length) {
             parts.push(`by ${config.rows.map(r => r.label).join(', ')}`);
         }

         if (config.columns.length) {
             parts.push(`and ${config.columns.map(c => c.label).join(', ')}`);
         }

         return parts.join(' ');
     }

     // Continue with export functionality...
