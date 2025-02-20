from typing import Any, Dict, List, Optional, Union, Callable
from flask import json, current_app
from flask_babel import gettext as _
from markupsafe import Markup
from wtforms.validators import ValidationError
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from sqlalchemy import inspect
import logging

logger = logging.getLogger(__name__)

class TreeViewWidget(BS3TextFieldWidget):
    """
    Advanced treeview widget for self-referencing hierarchical data in Flask-AppBuilder.

    Features:
    - Hierarchical display using jsTree with drag-and-drop support
    - Lazy loading for efficient handling of large datasets
    - Advanced search with customizable filters
    - Node state persistence
    - Accessibility compliance (WCAG 2.1)

    See Part 2 and 3 for additional features and implementations.
    """

    template = """
        <div class="treeview-container %(container_class)s" id="%(field_id)s_container">
            <div class="treeview-header">
                <div class="treeview-toolbar">
                    <div class="treeview-search">
                        <input type="text"
                                class="form-control search-input"
                                placeholder="%(search_placeholder)s"
                                aria-label="%(search_aria_label)s">
                        <i class="fa fa-search search-icon"></i>
                    </div>
                    <div class="treeview-actions">
                        <div class="btn-group">
                            <button type="button"
                                    class="btn btn-sm btn-outline-primary expand-all"
                                    aria-label="%(expand_all_aria_label)s">
                                <i class="fa fa-plus-square-o"></i> %(expand_all_text)s
                            </button>
                            <button type="button"
                                    class="btn btn-sm btn-outline-primary collapse-all"
                                    aria-label="%(collapse_all_aria_label)s">
                                <i class="fa fa-minus-square-o"></i> %(collapse_all_text)s
                            </button>
                        </div>
                        <!-- Toolbar Template Integration -->
                        %(toolbar_buttons)s
                    </div>
                </div>
            </div>
            <input %(hidden)s>
            <div id="%(field_id)s_tree"
                    class="treeview-content"
                    role="tree"
                    aria-label="%(tree_aria_label)s">
            </div>
            <div class="treeview-footer">
                <div class="treeview-status" aria-live="polite"></div>
                <div class="treeview-error" role="alert"></div>
            </div>
        </div>

        <!-- Modal Templates Integration -->
        %(modal_templates)s
    """

    # Template for CRUD toolbar buttons
    toolbar_template = """
        <div class="btn-group ms-2">
            {% if allow_create %}
            <button type="button" class="btn btn-primary btn-sm create-node"
                    aria-label="Create new node">
                <i class="fa fa-plus"></i> {{ create_button_text }}
            </button>
            {% endif %}
        </div>
    """

    # Templates for CRUD modals
    modal_templates = """
        <!-- Create Node Modal -->
        <div class="modal fade" id="createNodeModal-%(field_id)s" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Create New Node</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="createNodeForm-%(field_id)s">
                            <div class="mb-3">
                                <label class="form-label">Name</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Type</label>
                                <select class="form-control" name="type">
                                    {% for type in node_types %}
                                    <option value="{{ type.id }}">{{ type.text }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="createNodeBtn-%(field_id)s">Create</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Node Modal -->
        <div class="modal fade" id="editNodeModal-%(field_id)s" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit Node</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editNodeForm-%(field_id)s">
                            <input type="hidden" name="node_id">
                            <div class="mb-3">
                                <label class="form-label">Name</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Type</label>
                                <select class="form-control" name="type">
                                    {% for type in node_types %}
                                    <option value="{{ type.id }}">{{ type.text }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="editNodeBtn-%(field_id)s">Save</button>
                    </div>
                </div>
            </div>
        </div>
    """


    default_config = {
        'container_class': '',
        'search_placeholder': _('Search nodes...'),
        'search_aria_label': _('Search tree nodes'),
        'expand_all_text': _('Expand All'),
        'expand_all_aria_label': _('Expand all tree nodes'),
        'collapse_all_text': _('Collapse All'),
        'collapse_all_aria_label': _('Collapse all tree nodes'),
        'tree_aria_label': _('Hierarchical tree view')
    }

    def __init__(
        self,
        label: Optional[str] = None,
        validators: Optional[List[Any]] = None,
        order_field: str = 'id',
        label_field: str = 'name',
        parent_field: str = 'parent_id',
        icon_field: Optional[str] = None,
        max_depth: int = 10,
        allow_drag: bool = True,
        allow_multi_select: bool = False,
        persist_state: bool = True,
        lazy_load: bool = True,
        min_search_chars: int = 2,
        default_expanded: bool = False,
        show_checkbox: bool = False,
        custom_actions: List[Dict[str, Any]] = None,
        node_formatter: Optional[Callable[[Dict[str, Any], Any], Dict[str, Any]]] = None,
        load_url: Optional[str] = None,
        save_url: Optional[str] = None,
        allow_create: bool = True,
        allow_edit: bool = True,
        allow_delete: bool = True,
        create_url: Optional[str] = None,
        update_url: Optional[str] = None,
        delete_url: Optional[str] = None,
        create_button_text: str = "Add Node",
        node_types: Optional[List[Dict[str, str]]] = None,
        **kwargs
        ):
        """Initialize TreeViewWidget with CRUD capabilities

            Args:
                allow_create: Enable node creation
                allow_edit: Enable node editing
                allow_delete: Enable node deletion
                create_url: Endpoint for creating nodes
                update_url: Endpoint for updating nodes
                delete_url: Endpoint for deleting nodes
                create_button_text: Text for create button
                node_types: List of available node types e.g. [{'id': 'folder', 'text': 'Folder'}]
            """
        super().__init__(label, validators, **kwargs)
        self.order_field = order_field
        self.label_field = label_field
        self.parent_field = parent_field
        self.icon_field = icon_field
        self.max_depth = max_depth
        self.allow_drag = allow_drag
        self.allow_multi_select = allow_multi_select
        self.persist_state = persist_state
        self.lazy_load = lazy_load
        self.min_search_chars = min_search_chars
        self.default_expanded = default_expanded
        self.show_checkbox = show_checkbox
        self.custom_actions = custom_actions or []
        self.node_formatter = node_formatter
        self.load_url = load_url
        self.save_url = save_url

        # Initialize caching
        self._node_cache = {}
        self._tree_data = None

        # Performance settings
        self.batch_size = kwargs.get('batch_size', 100)
        self.cache_timeout = kwargs.get('cache_timeout', 300)
        self.allow_create = allow_create
        self.allow_edit = allow_edit
        self.allow_delete = allow_delete
        self.create_url = create_url
        self.update_url = update_url
        self.delete_url = delete_url
        self.create_button_text = create_button_text
        self.node_types = node_types or [{'id': 'default', 'text': 'Default'}]

        # Additional configuration
        self.config = {**self.default_config, **kwargs.get('config', {})}

    def pre_validate(self, form):
        """Validate field before form processing."""
        if form.flags.required and not self.data:
            raise ValidationError(_("This field is required"))

    def process_formdata(self, valuelist):
        """Process form data to database format."""
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except json.JSONDecodeError as e:
                self.data = None
                raise ValidationError(_("Invalid JSON for TreeView data")) from e
        else:
            self.data = None

    def _get_tree_data(self, field):
            """Get hierarchical tree data from database."""
            try:
                model = field.model
                query = model.query.order_by(getattr(model, self.order_field))

                if self.lazy_load:
                    # Only load first level for lazy loading
                    query = query.filter(getattr(model, self.parent_field) == None)

                nodes = []
                for item in query.all():
                    node = self._format_node(item)
                    if node:  # Only add successfully formatted nodes
                        nodes.append(node)

                return nodes
            except Exception as e:
                logger.error(f"Error getting tree data: {str(e)}")
                return []

        def _format_node(self, item, depth=0):
            """Format database item as tree node for jsTree."""
            if depth > self.max_depth:
                return None

            try:
                # Basic node structure
                node = {
                    "id": str(item.id),
                    "text": str(getattr(item, self.label_field)),
                    "icon": getattr(item, self.icon_field) if self.icon_field else "fa fa-folder",
                    "state": {
                        "opened": self.default_expanded,
                        "selected": False,
                        "disabled": getattr(item, 'disabled', False)
                    },
                    "li_attr": {
                        "role": "treeitem",
                        "data-depth": depth,
                        "data-id": str(item.id)
                    },
                    "a_attr": {
                        "href": "#",
                        "aria-label": str(getattr(item, self.label_field))
                    },
                    "data": {
                        "depth": depth,
                        "parent_id": getattr(item, self.parent_field),
                        "order": getattr(item, self.order_field),
                        "type": getattr(item, 'node_type', 'default')
                    }
                }

                # Apply custom node formatting if provided
                if self.node_formatter:
                    node = self.node_formatter(node, item)

                # Add children if not lazy loading
                if not self.lazy_load:
                    children = (
                        item.query.filter(getattr(item.__class__, self.parent_field) == item.id)
                        .order_by(getattr(item.__class__, self.order_field))
                        .all()
                    )

                    if children:
                        node["children"] = []
                        for child in children:
                            child_node = self._format_node(child, depth + 1)
                            if child_node:
                                node["children"].append(child_node)

                # Cache the node data
                self._node_cache[str(item.id)] = node

                return node
            except Exception as e:
                logger.error(f"Error formatting node {getattr(item, 'id', 'unknown')}: {str(e)}")
                return None

    def _get_custom_actions_js(self):
        """Generate JavaScript for custom node actions."""
        if not self.custom_actions:
            return "null"

        actions = {}
        for action in self.custom_actions:
            action_def = {
                "label": action["label"],
                "action": Markup(f"""function(data) {{
                    var inst = $.jstree.reference(data.reference);
                    var node = inst.get_node(data.reference);
                    {action["handler"]}
                }}""").unescape(),
            }

            if "icon" in action:
                action_def["icon"] = action["icon"]

            if "separator_before" in action:
                action_def["separator_before"] = action["separator_before"]

            if "separator_after" in action:
                action_def["separator_after"] = action["separator_after"]

            if "shortcut" in action:
                action_def["shortcut"] = action["shortcut"]
                action_def["shortcut_label"] = action.get("shortcut_label", action["shortcut"])

            actions[action["name"]] = action_def

        return Markup(json.dumps(actions)).unescape()

    def _update_node_order(self, node_id, parent_id, position):
        """Update node order in the database."""
        try:
            model = self.model
            node = model.query.get(node_id)
            if not node:
                raise ValueError(f"Node {node_id} not found")

            # Update parent
            setattr(node, self.parent_field, parent_id)

            # Get siblings in new order
            siblings_query = model.query.filter(
                getattr(model, self.parent_field) == parent_id
            ).order_by(getattr(model, self.order_field))

            siblings = siblings_query.all()
            siblings.insert(position, siblings.pop(siblings.index(node)))

            # Update order for all siblings
            for i, sibling in enumerate(siblings):
                setattr(sibling, self.order_field, i * 10)

            current_app.db.session.commit()
            return True
        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error updating node order: {str(e)}")
            return False

    def _load_children(self, node_id):
        """Load child nodes for lazy loading."""
        try:
            model = self.model
            children = (
                model.query
                .filter(getattr(model, self.parent_field) == node_id)
                .order_by(getattr(model, self.order_field))
                .all()
            )

            return [self._format_node(child) for child in children if child]
        except Exception as e:
            logger.error(f"Error loading children for node {node_id}: {str(e)}")
            return []

    def _validate_move(self, node_id, new_parent_id, position):
        """Validate node move operation."""
        try:
            model = self.model
            node = model.query.get(node_id)
            if not node:
                return False, "Node not found"

            # Check if new parent exists (if not moving to root)
            if new_parent_id is not None:
                new_parent = model.query.get(new_parent_id)
                if not new_parent:
                    return False, "Parent node not found"

                # Check for circular reference
                current = new_parent
                while current:
                    if current.id == node.id:
                        return False, "Cannot move node to its descendant"
                    current = getattr(current, self.parent_field)

            # Check maximum depth
            depth = 0
            current = new_parent_id
            while current:
                depth += 1
                if depth >= self.max_depth:
                    return False, f"Maximum depth of {self.max_depth} exceeded"
                current = getattr(model.query.get(current), self.parent_field)

            return True, ""
        except Exception as e:
            logger.error(f"Error validating move: {str(e)}")
            return False, "Internal error during validation"

    def _generate_styles(self):
            """Generate CSS styles for the tree view."""
            return """
            <style>
                .treeview-container {
                    margin-bottom: 1.5rem;
                    border: 1px solid #dee2e6;
                    border-radius: 0.25rem;
                    font-size: 0.9rem;
                }

                .treeview-header {
                    padding: 1rem;
                    border-bottom: 1px solid #dee2e6;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background-color: #f8f9fa;
                }

                .treeview-search {
                    position: relative;
                    max-width: 300px;
                    flex: 1;
                    margin-right: 1rem;
                }

                .search-input {
                    padding-right: 2rem;
                    border-radius: 0.25rem;
                }

                .search-icon {
                    position: absolute;
                    right: 0.75rem;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #6c757d;
                }

                .treeview-content {
                    padding: 1rem;
                    min-height: 200px;
                    max-height: 600px;
                    overflow-y: auto;
                    background-color: #fff;
                }

                .treeview-footer {
                    padding: 0.5rem 1rem;
                    border-top: 1px solid #dee2e6;
                    background-color: #f8f9fa;
                    font-size: 0.8rem;
                }

                .treeview-error {
                    color: #dc3545;
                    margin-top: 0.5rem;
                    display: none;
                    padding: 0.5rem;
                    border-radius: 0.25rem;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                }

                .treeview-status {
                    color: #6c757d;
                }

                /* jsTree Customizations */
                .jstree-default .jstree-anchor {
                    border-radius: 0.25rem;
                    transition: all 0.2s ease;
                }

                .jstree-default .jstree-clicked {
                    background-color: #007bff !important;
                    color: white !important;
                }

                .jstree-default .jstree-hovered {
                    background-color: #e9ecef;
                }

                .jstree-default .jstree-wholerow-clicked {
                    background-color: #007bff !important;
                }

                .jstree-default .jstree-wholerow-hovered {
                    background-color: #e9ecef;
                }

                /* Loading States */
                .jstree-loading::after {
                    content: "";
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 1rem;
                    height: 1rem;
                    margin: -0.5rem;
                    border-radius: 50%;
                    border: 2px solid #007bff;
                    border-top-color: transparent;
                    animation: treeview-spinner 0.6s linear infinite;
                }

                @keyframes treeview-spinner {
                    to { transform: rotate(360deg); }
                }

                /* Accessibility Enhancements */
                .jstree-default .jstree-anchor:focus {
                    outline: 2px solid #007bff;
                    outline-offset: 2px;
                }

                /* Custom Node States */
                .jstree-node-error .jstree-anchor {
                    color: #dc3545;
                }

                .jstree-node-warning .jstree-anchor {
                    color: #ffc107;
                }

                .jstree-node-success .jstree-anchor {
                    color: #28a745;
                }

                /* Drag and Drop Visual Feedback */
                .jstree-dnd-parent {
                    border: 2px dashed #007bff;
                    border-radius: 0.25rem;
                }

                .jstree-dnd-forbidden {
                    border: 2px dashed #dc3545;
                    border-radius: 0.25rem;
                }
            </style>
            """

    def __call__(self, field, **kwargs):
        """Render the widget with integrated CRUD templates."""
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'hidden')
        kwargs.setdefault('value', field.data or '')

        # Initialize tree data if not lazy loading
        if not self.lazy_load:
            self._tree_data = self._get_tree_data(field)

        # Render toolbar template
        toolbar_buttons = Markup(
            self.toolbar_template % {
                'allow_create': str(self.allow_create).lower(),
                'create_button_text': self.create_button_text,
            }
        )

        # Render modal templates
        modals = Markup(
            self.modal_templates % {
                'field_id': field.id,
                'node_types': self.node_types
            }
        )

        # Merge all template variables
        template_vars = {
            **self.config,
            'field_id': field.id,
            'hidden': self.html_params(name=field.name, **kwargs),
            'toolbar_buttons': toolbar_buttons,
            'modal_templates': modals
        }

        return Markup(
            self.template % template_vars +
            self._generate_styles() +
            self._generate_scripts(field)
        )

    def _generate_scripts(self, field):
        """Generate JavaScript code for tree functionality."""
        return f"""
        <script>
            (function() {{
                class TreeViewManager {{
                    constructor(config) {{
                        this.config = config;
                        this.tree = null;
                        this.searchTimeout = null;
                        this.pendingRequests = new Set();
                        this.init();
                    }}

                    init() {{
                        this.initElements();
                        this.initTree();
                        this.initEventHandlers();
                        this.initKeyboardNavigation();
                    }}

                    initElements() {{
                        this.container = document.getElementById(`${{this.config.fieldId}}_container`);
                        this.treeElement = document.getElementById(`${{this.config.fieldId}}_tree`);
                        this.input = document.getElementById(this.config.fieldId);
                        this.searchInput = this.container.querySelector('.search-input');
                        this.errorElement = this.container.querySelector('.treeview-error');
                        this.statusElement = this.container.querySelector('.treeview-status');
                    }}

                    initTree() {{
                        const treeConfig = {{
                            core: {{
                                data: this.config.lazyLoad ? this.loadNodes.bind(this) : this.config.treeData,
                                themes: {{ name: 'default', responsive: true, variant: 'large' }},
                                check_callback: this.handleTreeCallback.bind(this),
                                multiple: this.config.allowMultiSelect,
                                worker: false,
                                animation: 100
                            }},
                            plugins: [
                                'search', 'dnd', 'wholerow',
                                'state', 'types', 'contextmenu',
                                'changed', 'unique'
                            ],
                            state: {{
                                key: `tree_${{this.config.fieldId}}_state`,
                                filter: (key) => ['opened', 'selected'].includes(key)
                            }},
                            dnd: {{
                                is_draggable: this.config.allowDrag,
                                inside_pos: 'last',
                                copy: false,
                                check_while_dragging: true,
                                always_copy: false,
                                drag_selection: true,
                                touch: true,
                                large_drag_target: true,
                                large_drop_target: true
                            }},
                            contextmenu: {{
                                items: this.getContextMenuItems.bind(this),
                                show_at_node: false
                            }},
                            types: {{
                                default: {{ icon: 'fa fa-folder' }},
                                file: {{ icon: 'fa fa-file', max_children: 0 }},
                                folder: {{ icon: 'fa fa-folder' }}
                            }},
                            search: {{
                                show_only_matches: true,
                                show_only_matches_children: true,
                                close_opened_onclear: false,
                                search_leaves_only: false,
                                fuzzy: false,
                                case_sensitive: false
                            }}
                        }};

                        $(this.treeElement).jstree(treeConfig)
                            .on('loaded.jstree', () => this.handleTreeLoaded())
                            .on('changed.jstree', (e, data) => this.handleNodeSelection(data))
                            .on('move_node.jstree', (e, data) => this.handleNodeMove(data))
                            .on('error.jstree', (e, data) => this.handleError(data))
                            .on('search.jstree', (e, data) => this.handleSearch(data));

                        this.tree = $(this.treeElement).jstree(true);
                    }}

                    initEventHandlers() {{
                        // Search handler with debouncing
                        this.searchInput.addEventListener('input', (e) => {{
                            clearTimeout(this.searchTimeout);
                            const value = e.target.value;

                            if (value.length >= this.config.minSearchChars) {{
                                this.searchTimeout = setTimeout(() => {{
                                    this.tree.search(value);
                                }}, 300);
                            }} else if (value.length === 0) {{
                                this.tree.clear_search();
                            }}
                        }});

                        // Expand/Collapse buttons
                        this.container.querySelector('.expand-all').addEventListener('click', () => {{
                            this.tree.open_all();
                        }});

                        this.container.querySelector('.collapse-all').addEventListener('click', () => {{
                            this.tree.close_all();
                        }});
                    }}

                    initKeyboardNavigation() {{
                        this.treeElement.addEventListener('keydown', (e) => {{
                            const node = this.tree.get_selected(true)[0];
                            if (!node) return;

                            switch(e.key) {{
                                case 'ArrowUp':
                                    this.tree.select_node(this.tree.get_prev_dom(node));
                                    e.preventDefault();
                                    break;
                                case 'ArrowDown':
                                    this.tree.select_node(this.tree.get_next_dom(node));
                                    e.preventDefault();
                                    break;
                                case 'ArrowLeft':
                                    if (this.tree.is_open(node)) {{
                                        this.tree.close_node(node);
                                    }}
                                    e.preventDefault();
                                    break;
                                case 'ArrowRight':
                                    if (!this.tree.is_open(node)) {{
                                        this.tree.open_node(node);
                                    }}
                                    e.preventDefault();
                                    break;
                                case 'Home':
                                    this.tree.select_node(this.tree.get_first_dom());
                                    e.preventDefault();
                                    break;
                                case 'End':
                                    this.tree.select_node(this.tree.get_last_dom());
                                    e.preventDefault();
                                    break;
                                case ' ':
                                case 'Enter':
                                    this.tree.toggle_node(node);
                                    e.preventDefault();
                                    break;
                            }}
                        }});
                    }}

                    async loadNodes(node, callback) {{
                        if (node.id === '#') {{
                            callback(this.config.treeData);
                            return;
                        }}

                        try {{
                            const requestId = Math.random().toString(36);
                            this.pendingRequests.add(requestId);

                            const response = await fetch(`${{this.config.loadUrl}}?node=${{node.id}}`);
                            if (!response.ok) throw new Error('Failed to load nodes');

                            const data = await response.json();

                            if (this.pendingRequests.has(requestId)) {{
                                callback(data);
                                this.pendingRequests.delete(requestId);
                            }}
                        }} catch (error) {{
                            this.showError('Failed to load nodes: ' + error.message);
                            callback([]);
                        }}
                    }}

                    handleTreeCallback(operation, node, parent, position) {{
                        if (operation === 'move_node') {{
                            return this.validateMove(node, parent, position);
                        }}
                        return true;
                    }}

                    validateMove(node, parent, position) {{
                        if (!this.config.allowDrag) return false;

                        const parentNode = parent === '#' ? null : this.tree.get_node(parent);

                        // Check depth limit
                        let depth = 1;
                        let current = parentNode;
                        while (current && current.id !== '#') {{
                            depth++;
                            if (depth > this.config.maxDepth) return false;
                            current = this.tree.get_node(current.parent);
                        }}

                        // Check for circular reference
                        if (parentNode) {{
                            let ancestor = parentNode;
                            while (ancestor && ancestor.id !== '#') {{
                                if (ancestor.id === node.id) return false;
                                ancestor = this.tree.get_node(ancestor.parent);
                            }}
                        }}

                        return true;
                    }}

                    async handleNodeMove(data) {{
                        try {{
                            const response = await fetch(this.config.saveUrl, {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{
                                    node_id: data.node.id,
                                    parent_id: data.parent === '#' ? null : data.parent,
                                    position: data.position
                                }})
                            }});

                            if (!response.ok) throw new Error('Failed to save node position');

                            this.showStatus('Node moved successfully');
                        }} catch (error) {{
                            this.showError('Failed to save node position: ' + error.message);
                            this.tree.refresh();
                        }}
                    }}

                    handleNodeSelection(data) {{
                        const selected = this.tree.get_selected();
                        this.input.value = JSON.stringify(selected);

                        if (selected.length > 0) {{
                            const node = this.tree.get_node(selected[0]);
                            this.showStatus(`Selected: ${{node.text}}`);
                        }} else {{
                            this.showStatus('');
                        }}
                    }}

                    handleSearch(data) {{
                        const count = data.nodes.length;
                        this.showStatus(`Found ${{count}} matching node${{count === 1 ? '' : 's'}}`);
                    }}
                """
