"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
"""


from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from jinja2 import Template
from wtforms.validators import ValidationError
from flask_appbuilder.widgets import BS3TextFieldWidget
from markupsafe import Markup
import json
import re
from datetime import datetime, timedelta


@dataclass
class AutocompleteConfig:
    """Configuration settings for the autocomplete widget."""

    remote_url: Optional[str] = None
    remote_method: str = "GET"
    remote_params: Dict[str, Any] = None
    custom_headers: Dict[str, str] = None
    value_field: str = "value"
    label_field: str = "label"
    suggestion_template: Optional[str] = None
    placeholder: str = ""
    required: bool = False
    readonly: bool = False
    disabled: bool = False
    validate_pattern: Optional[str] = None
    max_length: Optional[int] = None
    min_length: int = 2
    delay: int = 300
    debounce_delay: int = 150
    timeout: int = 5000
    cache: bool = True
    cache_expiry: int = 300  # 5 minutes
    multiple: bool = False
    max_items: Optional[int] = None
    delimiter: str = ","
    highlight: bool = True
    highlight_class: str = "autocomplete-highlight"
    mobile_friendly: bool = True
    category_grouping: bool = False
    wrapper_class: str = ""
    input_class: str = ""

    def __post_init__(self):
        self.remote_params = self.remote_params or {}
        self.custom_headers = self.custom_headers or {}


@dataclass
class AutocompleteMessages:
    """Messages displayed by the autocomplete widget."""

    error: str = "An error occurred while fetching results."
    no_results: str = "No results found."
    loading: str = "Loading..."
    max_items: str = "Maximum of {max} items allowed."
    required: str = "This field is required."


class AutocompleteWidget(BS3TextFieldWidget):
    """
    Enhanced autocomplete widget for Flask-AppBuilder with advanced features.

    Features:
        - Local and remote data sources with caching
        - Category-based grouping
        - Custom templates with rich formatting
        - Multiple selection with validation
        - Result highlighting and fuzzy matching
        - Mobile optimization and responsive design
        - Rate limiting and error handling
        - Accessibility support (ARIA)
        - RTL language support
        - Type hints and comprehensive documentation

    Example:
        ```python
        class MyModel(Model):
            country = Column(String(100),
                           info={'widget': AutocompleteWidget(
                               remote_url='/api/countries',
                               category_grouping=True,
                               multiple=True,
                               max_items=5
                           )})
        ```
    """

    template = Template(
        """
        <div class="autocomplete-wrapper {{ wrapper_class }}"
             role="combobox"
             aria-expanded="false"
             aria-haspopup="listbox">
            <input {{ text|safe }}
                   role="textbox"
                   aria-autocomplete="list"
                   aria-controls="{{ field_id }}-list">
            <div class="autocomplete-selected-items"
                 aria-live="polite"></div>
            <div class="autocomplete-loading"
                 style="display:none"
                 role="status">
                <i class="fa fa-spinner fa-spin"
                   aria-hidden="true"></i>
                <span class="sr-only">{{ loading_message }}</span>
            </div>
            <div class="autocomplete-error"
                 style="display:none"
                 role="alert">{{ error_message }}</div>
            <div class="autocomplete-no-results"
                 style="display:none"
                 role="status">{{ no_results_message }}</div>
            <ul class="autocomplete-list"
                id="{{ field_id }}-list"
                role="listbox"
                style="display:none"></ul>
        </div>
    """
    )

    def __init__(self, **kwargs):
        """
        Initialize the autocomplete widget with configuration and messages.

        Args:
            **kwargs: Configuration options for AutocompleteConfig and messages
        """
        super().__init__(**kwargs)

        # Initialize configuration
        config_args = {
            k: v for k, v in kwargs.items() if k in AutocompleteConfig.__annotations__
        }
        self.config = AutocompleteConfig(**config_args)

        # Initialize messages
        message_args = {
            k.replace("_message", ""): v
            for k, v in kwargs.items()
            if k.endswith("_message")
        }
        self.messages = AutocompleteMessages(**message_args)

        # Initialize cache
        self._cache = {}
        self._cache_timestamps = {}

    def __call__(self, field: Any, **kwargs) -> Markup:
        """
        Render the autocomplete widget.

        Args:
            field: The form field
            **kwargs: Additional HTML attributes

        Returns:
            Markup: The rendered HTML and JavaScript
        """
        kwargs = self._prepare_kwargs(field, kwargs)
        html = self._render_html(field, kwargs)
        assets = self._generate_assets(field)
        return Markup(f"{html}{assets}")

    def _prepare_kwargs(self, field: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare kwargs for HTML rendering.

        Args:
            field: The form field
            kwargs: Dictionary of HTML attributes

        Returns:
            Dict[str, Any]: Prepared kwargs with all necessary attributes
        """
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", "text")
        kwargs.setdefault("autocomplete", "off")
        kwargs.setdefault("placeholder", self.config.placeholder)
        kwargs.setdefault("class", f"form-control {self.config.input_class}")
        kwargs.setdefault(
            "aria-label", field.label.text if hasattr(field, "label") else field.name
        )

        # Add required attributes
        if field.flags.required or self.config.required:
            kwargs["required"] = "required"
            kwargs["aria-required"] = "true"

        # Add state attributes
        if self.config.readonly:
            kwargs["readonly"] = "readonly"
        if self.config.disabled:
            kwargs["disabled"] = "disabled"
            kwargs["aria-disabled"] = "true"

        # Add validation attributes
        if self.config.validate_pattern:
            kwargs["pattern"] = self.config.validate_pattern
        if self.config.max_length:
            kwargs["maxlength"] = str(self.config.max_length)

        # Handle initial values
        if field.data:
            if self.config.multiple:
                if isinstance(field.data, (list, tuple)):
                    kwargs["value"] = self.config.delimiter.join(map(str, field.data))
                else:
                    kwargs["value"] = str(field.data)
            else:
                kwargs["value"] = str(field.data)

        return kwargs

    def _render_html(self, field: Any, kwargs: Dict[str, Any]) -> str:
        """
        Render the base HTML template.

        Args:
            field: The form field
            kwargs: Dictionary of HTML attributes

        Returns:
            str: Rendered HTML string
        """
        from flask_appbuilder.fieldwidgets import html_params

        return self.template.render(
            {
                "field_id": field.id,
                "text": html_params(name=field.name, **kwargs),
                "wrapper_class": self.config.wrapper_class,
                "error_message": self.messages.error,
                "no_results_message": self.messages.no_results,
                "loading_message": self.messages.loading,
            }
        )

    def _generate_assets(self, field: Any) -> str:
        """
        Generate CSS and JavaScript assets for the widget.

        Args:
            field: The form field

        Returns:
            str: Combined CSS and JavaScript assets
        """
        return f"{self._generate_styles()}{self._generate_scripts(field)}"

    def _generate_styles(self) -> str:
        """
        Generate widget CSS styles with accessibility and RTL support.

        Returns:
            str: CSS styles as a string
        """
        return """
        <style>
            .autocomplete-wrapper {
                position: relative;
                margin-bottom: 1rem;
            }

            .autocomplete-wrapper input {
                width: 100%;
                padding-right: 30px;
                transition: border-color 0.15s ease-in-out,
                            box-shadow 0.15s ease-in-out;
            }

            .autocomplete-wrapper input:focus {
                outline: none;
                border-color: #80bdff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }

            .autocomplete-wrapper .autocomplete-loading {
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                z-index: 2;
            }

            .autocomplete-wrapper .autocomplete-error,
            .autocomplete-wrapper .autocomplete-no-results {
                margin-top: 0.25rem;
                font-size: 0.875rem;
                padding: 0.5rem;
                border-radius: 0.25rem;
                animation: fadeIn 0.2s ease-in-out;
            }

            .autocomplete-wrapper .autocomplete-error {
                color: #dc3545;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
            }

            .autocomplete-wrapper .autocomplete-no-results {
                color: #856404;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
            }

            .autocomplete-selected-items {
                margin-top: 0.5rem;
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }

            .autocomplete-selected-items .badge {
                display: inline-flex;
                align-items: center;
                padding: 0.5em 0.75em;
                font-size: 0.875rem;
                font-weight: 500;
                line-height: 1;
                color: #fff;
                background-color: #6c757d;
                border-radius: 0.25rem;
                transition: all 0.2s ease-in-out;
            }

            .autocomplete-selected-items .badge:hover {
                background-color: #5a6268;
            }

            .autocomplete-selected-items .badge .remove-item {
                margin-left: 0.5em;
                cursor: pointer;
                opacity: 0.8;
                transition: opacity 0.2s;
            }

            .autocomplete-selected-items .badge .remove-item:hover {
                opacity: 1;
            }

            .autocomplete-selected-items .badge .remove-item:focus {
                outline: none;
                box-shadow: 0 0 0 0.2rem rgba(255,255,255,.25);
            }

            .autocomplete-list {
                position: absolute;
                top: 100%;
                left: 0;
                z-index: 1000;
                width: 100%;
                max-height: 300px;
                margin: 0.125rem 0 0;
                padding: 0.5rem 0;
                list-style: none;
                background-color: #fff;
                background-clip: padding-box;
                border: 1px solid rgba(0,0,0,.15);
                border-radius: 0.25rem;
                box-shadow: 0 0.5rem 1rem rgba(0,0,0,.175);
                overflow-y: auto;
                scrollbar-width: thin;
                scrollbar-color: #6c757d #f8f9fa;
            }

            .autocomplete-list::-webkit-scrollbar {
                width: 6px;
            }

            .autocomplete-list::-webkit-scrollbar-track {
                background: #f8f9fa;
            }

            .autocomplete-list::-webkit-scrollbar-thumb {
                background-color: #6c757d;
                border-radius: 3px;
            }

            .autocomplete-list .autocomplete-item {
                padding: 0.5rem 1rem;
                margin: 0;
                clear: both;
                font-weight: 400;
                color: #212529;
                text-align: inherit;
                white-space: nowrap;
                background-color: transparent;
                border: 0;
                cursor: pointer;
                transition: background-color 0.15s ease-in-out;
            }

            .autocomplete-list .autocomplete-item:hover,
            .autocomplete-list .autocomplete-item:focus {
                color: #16181b;
                text-decoration: none;
                background-color: #f8f9fa;
            }

            .autocomplete-list .autocomplete-item.active {
                color: #fff;
                background-color: #007bff;
            }

            .autocomplete-list .autocomplete-category {
                padding: 0.5rem 1rem;
                font-weight: 600;
                color: #6c757d;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }

            /* RTL Support */
            .autocomplete-wrapper.is-rtl input {
                padding-right: 0.75rem;
                padding-left: 30px;
            }

            .autocomplete-wrapper.is-rtl .autocomplete-loading {
                right: auto;
                left: 10px;
            }

            /* Mobile Optimizations */
            @media (max-width: 768px) {
                .autocomplete-list {
                    max-height: 50vh;
                    position: fixed;
                    top: auto;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    width: 100%;
                    margin: 0;
                    border-radius: 0.5rem 0.5rem 0 0;
                    box-shadow: 0 -2px 10px rgba(0,0,0,.1);
                }

                .autocomplete-wrapper input {
                    font-size: 16px; /* Prevent iOS zoom */
                }

                .autocomplete-selected-items .badge {
                    padding: 0.75em 1em;
                }
            }

            /* Prefers-reduced-motion */
            @media (prefers-reduced-motion: reduce) {
                .autocomplete-wrapper * {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                    scroll-behavior: auto !important;
                }
            }
        </style>
        """

    def _generate_scripts(self, field: Any) -> str:
        """
        Generate widget JavaScript functionality with accessibility support.

        Args:
            field: The form field

        Returns:
            str: JavaScript as a string
        """

        config = {
            "field_id": field.id,
            "min_length": self.config.min_length,
            "delay": self.config.delay,
            "debounce_delay": self.config.debounce_delay,
            "timeout": self.config.timeout,
            "cache": self.config.cache,
            "cache_expiry": self.config.cache_expiry,
            "multiple": self.config.multiple,
            "max_items": self.config.max_items,
            "delimiter": self.config.delimiter,
            "highlight": self.config.highlight,
            "mobile_friendly": self.config.mobile_friendly,
            "category_grouping": self.config.category_grouping,
            "messages": {
                "error": self.messages.error,
                "no_results": self.messages.no_results,
                "loading": self.messages.loading,
                "max_items": self.messages.max_items,
            },
        }

        return f"""
        <script>
            (function() {{
                'use strict';

                class AutocompleteManager {{
                    constructor(config) {{
                        this.config = config;
                        this.cache = {{}};
                        this.cacheTimestamps = {{}};
                        this.setupElements();
                        this.initializeAutocomplete();
                        this.bindEvents();
                    }}

                    setupElements() {{
                        this.$input = document.getElementById(this.config.field_id);
                        this.$wrapper = this.$input.closest('.autocomplete-wrapper');
                        this.$loading = this.$wrapper.querySelector('.autocomplete-loading');
                        this.$error = this.$wrapper.querySelector('.autocomplete-error');
                        this.$noResults = this.$wrapper.querySelector('.autocomplete-no-results');
                        this.$selected = this.$wrapper.querySelector('.autocomplete-selected-items');
                        this.$list = this.$wrapper.querySelector('.autocomplete-list');

                        // Initialize ARIA attributes
                        this.$input.setAttribute('aria-expanded', 'false');
                        this.$list.style.display = 'none';

                        // Initialize selected items if multiple mode
                        if (this.config.multiple && this.$input.value) {{
                            this.updateSelectedItems(this.getValues());
                        }}
                    }} 0 0;
                }}

                .autocomplete-wrapper input {{
                    font-size: 16px; /* Prevent iOS zoom */
                }}

                .autocomplete-selected-items .badge {{
                    padding: 0.75em 1em;
                }}
            }}

            /* Accessibility Focus Styles */
            .autocomplete-wrapper input:focus-visible,
            .autocomplete-list .autocomplete-item:focus-visible {{
                outline: 2px solid #007bff;
                outline-offset: 2px;
            }}

            /* Animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}

            .autocomplete-highlight {{
                font-weight: bold;
                background-color: #fff3cd;
                padding: 0.1em 0.2em;
                border-radius: 0.2em;
            }}

            /* High Contrast Mode Support */
            @media (forced-colors: active) {{
                .autocomplete-wrapper input:focus {{
                    outline: 2px solid CanvasText;
                }}

                .autocomplete-list .autocomplete-item:focus {{
                    outline: 2px solid CanvasText;
                    outline-offset: -2px;
                }}
            }}
        </style>
        """

    def _generate_scripts(self, field: Any) -> str:
        """
        Generate widget JavaScript functionality with accessibility support.

        Args:
            field: The form field

        Returns:
            str: JavaScript as a string
        """
        config = {
            "field_id": field.id,
            "min_length": self.config.min_length,
            "delay": self.config.delay,
            "debounce_delay": self.config.debounce_delay,
            "timeout": self.config.timeout,
            "cache": self.config.cache,
            "cache_expiry": self.config.cache_expiry,
            "multiple": self.config.multiple,
            "max_items": self.config.max_items,
            "delimiter": self.config.delimiter,
            "highlight": self.config.highlight,
            "mobile_friendly": self.config.mobile_friendly,
            "category_grouping": self.config.category_grouping,
            "messages": {
                "error": self.messages.error,
                "no_results": self.messages.no_results,
                "loading": self.messages.loading,
                "max_items": self.messages.max_items,
            },
        }

        return f"""
        <script>
            (function() {{
                'use strict';

                class AutocompleteManager {{
                    constructor(config) {{
                        this.config = config;
                        this.cache = {{}};
                        this.cacheTimestamps = {{}};
                        this.setupElements();
                        this.initializeAutocomplete();
                        this.bindEvents();
                    }}

                    setupElements() {{
                        this.$input = document.getElementById(this.config.field_id);
                        this.$wrapper = this.$input.closest('.autocomplete-wrapper');
                        this.$loading = this.$wrapper.querySelector('.autocomplete-loading');
                        this.$error = this.$wrapper.querySelector('.autocomplete-error');
                        this.$noResults = this.$wrapper.querySelector('.autocomplete-no-results');
                        this.$selected = this.$wrapper.querySelector('.autocomplete-selected-items');
                        this.$list = this.$wrapper.querySelector('.autocomplete-list');

                        // Initialize ARIA attributes
                        this.$input.setAttribute('aria-expanded', 'false');
                        this.$list.style.display = 'none';

                        // Initialize selected items if multiple mode
                        if (this.config.multiple && this.$input.value) {{
                            this.updateSelectedItems(this.getValues());
                        }}
                    }}

                    initializeAutocomplete() {{
                        let currentRequest = null;
                        let currentTerm = '';

                        const debounce = (fn, delay) => {{
                            let timeoutId;
                            return (...args) => {{
                                clearTimeout(timeoutId);
                                timeoutId = setTimeout(() => fn.apply(this, args), delay);
                            }};
                        }};

                        const fetchResults = async (term) => {{
                            // Check cache first
                            if (this.config.cache && this.cache[term]) {{
                                const timestamp = this.cacheTimestamps[term];
                                if (Date.now() - timestamp < this.config.cache_expiry * 1000) {{
                                    return this.cache[term];
                                }}
                            }}

                            // Abort previous request
                            if (currentRequest) {{
                                currentRequest.abort();
                            }}

                            this.showLoading();

                            try {{
                                const response = await fetch(`{
            self.config.remote_url
        }?q=${encodeURIComponent(term)}`, {{
                                    method: '{self.config.remote_method}',
                                    headers: {json.dumps(self.config.custom_headers)},
                                    signal: (currentRequest = new AbortController()).signal
                                }});

                                if (!response.ok) {{
                                    throw new Error(`HTTP error! status: ${{response.status}}`);
                                }}

                                const data = await response.json();

                                // Cache results
                                if (this.config.cache) {{
                                    this.cache[term] = data;
                                    this.cacheTimestamps[term] = Date.now();
                                }}

                                return data;
                            }} catch (error) {{
                                if (error.name === 'AbortError') return null;
                                throw error;
                            }} finally {{
                                this.hideLoading();
                            }}
                        }};

                        const processResults = debounce(async (term) => {{
                            if (term.length < this.config.min_length) {{
                                this.clearResults();
                                return;
                            }}

                            try {{
                                const data = await fetchResults(term);
                                if (!data) return;

                                const results = this.config.category_grouping
                                    ? this.processCategorizedData(data)
                                    : this.processData(data);

                                this.displayResults(results, term);
                            }} catch (error) {{
                                this.showError(this.config.messages.error);
                            }}
                        }}, this.config.debounce_delay);

                        // Input event handler
                        this.$input.addEventListener('input', (event) => {{
                            currentTerm = event.target.value.trim();
                            processResults(currentTerm);
                        }});
                    }}
                    bindEvents() {{
                        // Handle keyboard navigation
                        this.$input.addEventListener('keydown', (event) => {{
                            const items = Array.from(this.$list.querySelectorAll('.autocomplete-item'));
                            const activeItem = this.$list.querySelector('.autocomplete-item.active');
                            const activeIndex = activeItem ? items.indexOf(activeItem) : -1;

                            switch (event.key) {{
                                case 'ArrowDown':
                                    event.preventDefault();
                                    this.handleArrowNavigation(items, activeIndex, 1);
                                    break;
                                case 'ArrowUp':
                                    event.preventDefault();
                                    this.handleArrowNavigation(items, activeIndex, -1);
                                    break;
                                case 'Enter':
                                    if (activeItem) {{
                                        event.preventDefault();
                                        this.selectItem(activeItem);
                                    }}
                                    break;
                                case 'Escape':
                                    event.preventDefault();
                                    this.clearResults();
                                    break;
                            }}
                        }});

                        // Handle click events on results
                        this.$list.addEventListener('click', (event) => {{
                            const item = event.target.closest('.autocomplete-item');
                            if (item) {{
                                this.selectItem(item);
                            }}
                        }});

                        // Handle form events
                        const form = this.$input.closest('form');
                        if (form) {{
                        form.addEventListener('reset', () => {{
                                setTimeout(() => {{
                                    this.$input.value = '';
                                    this.updateSelectedItems([]);
                                    this.$error.style.display = 'none';
                                    this.$noResults.style.display = 'none';
                                }}, 0);
                            }});

                            form.addEventListener('submit', (event) => {{
                                if (this.config.required && !this.getValues().length) {{
                                    event.preventDefault();
                                    this.showError(this.config.messages.required);
                                }}
                            }});
                        }}

                        // Handle mobile optimizations
                        if (this.config.mobile_friendly) {{
                        this.$input.addEventListener('focus', () => {{
                                if (this.isMobile()) {{
                                    document.body.style.overflow = 'hidden';
                                }}
                            }});

                            this.$input.addEventListener('blur', () => {{
                                if (this.isMobile()) {{
                                    document.body.style.overflow = '';
                                }}
                            }});
                        }}
                    }}

                    handleArrowNavigation(items, activeIndex, direction) {{
                        if (!items.length) return;

                        let newIndex = activeIndex + direction;
                        if (newIndex < 0) newIndex = items.length - 1;
                        if (newIndex >= items.length) newIndex = 0;

                        items.forEach(item => item.classList.remove('active'));
                        items[newIndex].classList.add('active');
                        items[newIndex].scrollIntoView({{ block: 'nearest' }});
                    }}

                    processData(data) {{
                    return data.map(item => {{
                            if (typeof item === 'string' || typeof item === 'number') {{
                                return {{
                                    label: String(item),
                                    value: String(item)
                                }};
                            }}
                            return {{
                                label: String(item[this.config.label_field] || ''),
                                value: String(item[this.config.value_field] || ''),
                                data: item
                            }};
                    }});
                    }}

                    processCategorizedData(daire
                        const processed = [];
                        for (const category of data) {{
                            if (!category?.category || !Array.isArray(category.items)) continue;

                            processed.push({label: category.category,
                                isCategory: true
                            });

                            processed.push(...category.items.map(item => ({{
                                label: String(item[this.config.label_field] || ''),
                                value: String(item[this.config.value_field] || ''),
                                category: category.category,
                                data: item
                            }})));
                        }}
                        return processed;
                    }}

                    displayResults(results, term) {{
                        this.$list.innerHTML = '';
                        this.$wrapper.setAttribute('aria-expanded', 'true');

                        if (!results.length) {{
                            this.showNoResults();
                            return;
                        }}

                        results.forEach((result, index) => {{
                            const element = document.createElement('li');

                            if (result.isCategory) {{
                                element.className = 'autocomplete-category';
                                element.setAttribute('role', 'presentation');
                                element.textContent = result.label;
                            }} else {{
                                element.className = 'autocomplete-item';
                                element.setAttribute('role', 'option');
                                element.setAttribute('id', `${
            this.config.field_id
        }-option-${index}`);
                                element.dataset.value = result.value;

                                if (this.config.highlight) {{
                                    element.innerHTML = this.highlightText(result.label, term);
                                }} else {{
                                    element.textContent = result.label;
                                }}
                            }}

                            this.$list.appendChild(element);
                        }});

                        this.$list.style.display = 'block';
                    }}

                    selectItem(item) {{
                        const value = item.dataset.value;
                        const label = item.textContent;

                        if (this.config.multiple) {{
                            const values = this.getValues();
                            if (values.length >= this.config.max_items) {{
                                this.showError(this.config.messages.max_items.replace('{
            max
        }', this.config.max_items));
                                return;
                            }}
                            values.push(value);
                            this.setValues(values);
                            this.$input.value = '';
                        }} else {{
                            this.$input.value = label;
                            this.updateSelectedItems([value]);
                        }}

                        this.clearResults();
                        this.$input.focus();
                    }}

                    getValues() {{
                        if (!this.config.multiple) {{
                            return [this.$input.value].filter(Boolean);
                        }}
                        return this.$input.value
                            .split(this.config.delimiter)
                            .map(item => item.trim())
                            .filter(Boolean);
                    }}

                    setValues(values) {{
                        if (this.config.multiple) {{
                            this.updateSelectedItems(values);
                        }} else {{
                            this.$input.value = values[0] || '';
                        }}
                    }}

                    updateSelectedItems(items) {{
                        if (!this.config.multiple) return;

                        this.$selected.innerHTML = '';
                        items.forEach(item => {{
                            const badge = document.createElement('span');
                            badge.className = 'badge';
                            badge.innerHTML = `
                                ${{this.escapeHtml(item)}}
                                <button type="button"
                                        class="remove-item"
                                        aria-label="Remove ${item}"
                                        tabindex="0">
                                    <i class="fa fa-times" aria-hidden="true"></i>
                                </button>
                            `;

                            badge.querySelector('.remove-item').addEventListener('click', () => {{
                                this.removeItem(item);
                            }});

                            this.$selected.appendChild(badge);
                        }});
                    }}

                    removeItem(item) {{
                        const values = this.getValues();
                        const index = values.indexOf(item);
                        if (index > -1) {{
                            values.splice(index, 1);
                            this.setValues(values);
                        }}
                    }}

                    highlightText(text, term) {{
                        if (!term) return this.escapeHtml(text);

                        const escapedTerm = this.escapeRegExp(term);
                        const regex = new RegExp(`(${escapedTerm})`, 'gi');
                        return this.escapeHtml(text).replace(
                            regex,
                            `<span class="autocomplete-highlight">$1</span>`
                        );
                    }}

                    showLoading() {{
                        this.$loading.style.display = 'block';
                        this.$error.style.display = 'none';
                        this.$noResults.style.display = 'none';
                        this.$input.setAttribute('aria-busy', 'true');
                    }}

                    hideLoading() {{
                        this.$loading.style.display = 'none';
                        this.$input.setAttribute('aria-busy', 'false');
                    }}

                    showError(message) {{
                        this.$error.textContent = message;
                        this.$error.style.display = 'block';
                        this.$loading.style.display = 'none';
                        this.$noResults.style.display = 'none';
                        this.clearResults();
                    }}

                    showNoResults() {{
                        this.$noResults.style.display = 'block';
                        this.$loading.style.display = 'none';
                        this.$error.style.display = 'none';
                        this.clearResults();
                    }}

                    clearResults() {{
                        this.$list.innerHTML = '';
                        this.$list.style.display = 'none';
                        this.$wrapper.setAttribute('aria-expanded', 'false');
                    }}

                    // Utility methods
                    escapeHtml(str) {{
                        const div = document.createElement('div');
                        div.textContent = str;
                        return div.innerHTML;
                    }}

                    escapeRegExp(str) {{
                        return str.replace(/[.*+?^${{}}()|[\]\\]/g, '\\                        if (!term) return this.escapeHtml(text);');
                    }}

                    isMobile() {{
                        return window.innerWidth <= 768 ||
                                'ontouchstart' in window ||
                                navigator.maxTouchPoints > 0;
                    }}
                }}

                // Initialize the autocomplete manager with the configuration
                window.autocompleteManager = new AutocompleteManager({
            json.dumps(config)
        });
            }})();
        </script>
        """

    def process_formdata(self, valuelist: List[str]) -> None:
        """
        Process form data into appropriate format.

        Args:
            valuelist: List of form values

        Raises:
            ValidationError: If data format is invalid
        """
        if not valuelist:
            self.data = [] if self.config.multiple else None
            return

        try:
            if self.config.multiple:
                self.data = [
                    value.strip()
                    for value in valuelist[0].split(self.config.delimiter)
                    if value.strip()
                ]
            else:
                self.data = valuelist[0]
        except Exception as e:
            self.data = None
            raise ValidationError(f"Invalid data format: {str(e)}")

    def process_data(self, value: Any) -> None:
        """
        Process data from Python/database format.

        Args:
            value: Input value to process

        Raises:
            ValidationError: If data format is invalid
        """
        if value is None:
            self.data = [] if self.config.multiple else None
            return

        try:
            if self.config.multiple:
                if isinstance(value, str):
                    self.data = [
                        v.strip()
                        for v in value.split(self.config.delimiter)
                        if v.strip()
                    ]
                elif isinstance(value, (list, tuple)):
                    self.data = [str(v) for v in value if v]
                else:
                    self.data = [str(value)]
            else:
                self.data = str(value)
        except Exception as e:
            self.data = None
            raise ValidationError(f"Invalid data format: {str(e)}")

    def pre_validate(self, form: Any) -> None:
        """
        Validate field before form processing.

        Args:
            form: The form containing this field

        Raises:
            ValidationError: If validation fails
        """
        if not self.data and self.config.required:
            raise ValidationError(self.messages.required)

        if self.config.multiple:
            if not isinstance(self.data, (list, tuple)):
                raise ValidationError("Multiple selection data must be a list")

            if self.config.max_items and len(self.data) > self.config.max_items:
                raise ValidationError(
                    self.messages.max_items.format(max=self.config.max_items)
                )

        if self.config.validate_pattern and not isinstance(self.data, (list, tuple)):
            pattern = re.compile(self.config.validate_pattern)
            if not pattern.match(str(self.data)):
                raise ValidationError("Value does not match the required pattern")
                )

        if self.config.validate_pattern and not isinstance(self.data, (list, tuple)):
            pattern = re.compile(self.config.validate_pattern)
            if not pattern.match(str(self.data)):
                raise ValidationError("Value does not match the required pattern")
