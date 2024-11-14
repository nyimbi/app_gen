def get_view_icon(model_name: str, view_type: str, icon_set: str = 'fontawesome', custom_icons: dict = None, theme: str = None) -> str:
    """
    Determine the appropriate icon for a view based on the model name, view type, and other factors.

    Parameters:
    - model_name: The name of the model (e.g., 'User', 'Product').
    - view_type: The type of view (e.g., 'ModelView', 'AddView', 'EditView').
    - icon_set: The icon set to use ('fontawesome', 'material', 'custom_svg').
    - custom_icons: A dictionary of user-defined custom icons.
    - theme: Optional theme-based icons for dark or light modes.

    Returns:
    - str: The appropriate icon class (e.g., 'fa-user' for FontAwesome).
    """
    # Default icons for different view types in the FontAwesome set
    default_icons = {
        'ModelView': 'fa-table',
        'AddView': 'fa-plus-circle',
        'EditView': 'fa-edit',
        'DetailView': 'fa-info-circle',
        'DeleteView': 'fa-trash',
        'ListView': 'fa-list',
        'MasterDetailView': 'fa-link',
        'MultipleView': 'fa-cubes',
        'ChartView': 'fa-chart-bar',
        'ModelRestApi': 'fa-api',
        'DashboardView': 'fa-tachometer-alt',
        'ReportView': 'fa-file-alt',
        'ExportView': 'fa-download',
        'ImportView': 'fa-upload',
    }

    # Model-specific icons (customize this based on your models)
    model_icons = {
        'User': 'fa-user',
        'Group': 'fa-users',
        'Role': 'fa-user-tag',
        'Permission': 'fa-key',
        'Document': 'fa-file',
        'Category': 'fa-folder',
        'Product': 'fa-box',
        'Order': 'fa-shopping-cart',
        'Customer': 'fa-address-book',
        'Employee': 'fa-id-badge',
        'Department': 'fa-building',
        'Project': 'fa-project-diagram',
        'Task': 'fa-tasks',
        'Event': 'fa-calendar-alt',
        'Location': 'fa-map-marker-alt',
        'Setting': 'fa-cog',
        'Log': 'fa-history',
        'Notification': 'fa-bell',
        'Message': 'fa-envelope',
        'Comment': 'fa-comment',
        'Review': 'fa-star',
        'Payment': 'fa-credit-card',
        'Invoice': 'fa-file-invoice-dollar',
        'Subscription': 'fa-recycle',
        'Report': 'fa-chart-line',
        'Alert': 'fa-exclamation-circle',
        'Feedback': 'fa-comment-dots',
        'Budget': 'fa-piggy-bank',
        'Survey': 'fa-poll',
        'Address': 'fa-map-pin',
        'Sale': 'fa-tags',
        'Vendor': 'fa-store',
        'Inventory': 'fa-warehouse',
        'Discount': 'fa-percent',
        'Shipping': 'fa-truck',
        'Support': 'fa-headset',
        'Asset': 'fa-boxes',
        'Expense': 'fa-wallet',
        'Calendar': 'fa-calendar',
        'Goal': 'fa-bullseye',
        'Team': 'fa-people-arrows',
        'Analytics': 'fa-chart-pie',
        'Profile': 'fa-id-card',

        # User and Access Control
        'User': 'fa-user',
        'Group': 'fa-users',
        'Role': 'fa-user-tag',
        'Permission': 'fa-key',
        'Profile': 'fa-id-card',
        'Admin': 'fa-user-shield',
        'Audit': 'fa-user-secret',
        'AccessLog': 'fa-door-open',

        # Document and Content Management
        'Document': 'fa-file',
        'File': 'fa-file-alt',
        'Folder': 'fa-folder',
        'Media': 'fa-photo-video',
        'Image': 'fa-image',
        'Video': 'fa-video',
        'Audio': 'fa-music',
        'Content': 'fa-file-alt',
        'Post': 'fa-newspaper',
        'Blog': 'fa-blog',
        'Article': 'fa-book-open',
        'Publication': 'fa-book',
        'Wiki': 'fa-book-reader',

        # E-Commerce and Sales
        'Product': 'fa-box',
        'Order': 'fa-shopping-cart',
        'Customer': 'fa-address-book',
        'Vendor': 'fa-store',
        'Category': 'fa-folder-open',
        'Cart': 'fa-shopping-basket',
        'Checkout': 'fa-credit-card',
        'Invoice': 'fa-file-invoice-dollar',
        'Payment': 'fa-credit-card',
        'Subscription': 'fa-recycle',
        'Discount': 'fa-percent',
        'Shipping': 'fa-truck',
        'Sale': 'fa-tags',
        'Inventory': 'fa-warehouse',
        'Return': 'fa-undo-alt',
        'Refund': 'fa-money-bill-wave',

        # Finance and Accounting
        'Budget': 'fa-piggy-bank',
        'Expense': 'fa-wallet',
        'Revenue': 'fa-chart-line',
        'Income': 'fa-dollar-sign',
        'ExpenseReport': 'fa-file-invoice',
        'Tax': 'fa-receipt',
        'Transaction': 'fa-exchange-alt',
        'Bank': 'fa-university',
        'Investment': 'fa-coins',
        'Loan': 'fa-hand-holding-usd',
        'FinancialStatement': 'fa-file-invoice',

        # Human Resources
        'Employee': 'fa-id-badge',
        'Department': 'fa-building',
        'Attendance': 'fa-calendar-check',
        'Payroll': 'fa-money-check-alt',
        'Leave': 'fa-calendar-minus',
        'Hiring': 'fa-user-plus',
        'Termination': 'fa-user-slash',
        'Job': 'fa-briefcase',
        'Candidate': 'fa-user-tie',
        'Skill': 'fa-tools',
        'Performance': 'fa-chart-line',
        'Training': 'fa-chalkboard-teacher',
        'Benefits': 'fa-hand-holding-heart',
        'Insurance': 'fa-shield-alt',
        'Vacation': 'fa-umbrella-beach',
        'Overtime': 'fa-clock',
        'Schedule': 'fa-calendar-alt',

        # Project Management
        'Project': 'fa-project-diagram',
        'Task': 'fa-tasks',
        'Milestone': 'fa-flag-checkered',
        'Team': 'fa-people-arrows',
        'Goal': 'fa-bullseye',
        'Timeline': 'fa-stream',
        'Sprint': 'fa-running',
        'Bug': 'fa-bug',
        'Issue': 'fa-exclamation-triangle',
        'Status': 'fa-info-circle',
        'Risk': 'fa-shield-virus',
        'Resource': 'fa-clipboard-list',
        'Priority': 'fa-exclamation',

        # Marketing and Customer Relations
        'Campaign': 'fa-bullhorn',
        'Lead': 'fa-users',
        'Opportunity': 'fa-handshake',
        'Client': 'fa-user-tie',
        'Contact': 'fa-address-book',
        'Event': 'fa-calendar-alt',
        'Survey': 'fa-poll',
        'Feedback': 'fa-comment-dots',
        'Review': 'fa-star',
        'Newsletter': 'fa-envelope-open-text',
        'Ad': 'fa-ad',

        # Communication
        'Notification': 'fa-bell',
        'Message': 'fa-envelope',
        'Chat': 'fa-comments',
        'Email': 'fa-at',
        'Announcement': 'fa-bullhorn',
        'Forum': 'fa-comments',
        'Discussion': 'fa-comment-alt',
        'Thread': 'fa-paperclip',

        # IT and Operations
        'Asset': 'fa-boxes',
        'Incident': 'fa-fire',
        'Log': 'fa-history',
        'Ticket': 'fa-ticket-alt',
        'Support': 'fa-headset',
        'HelpDesk': 'fa-life-ring',
        'Request': 'fa-hand-paper',
        'Change': 'fa-sync',
        'Patch': 'fa-tools',
        'Security': 'fa-shield-alt',
        'Alert': 'fa-exclamation-circle',
        'Monitor': 'fa-desktop',
        'Backup': 'fa-hdd',
        'Server': 'fa-server',
        'Database': 'fa-database',

        # Legal and Compliance
        'Contract': 'fa-file-signature',
        'Agreement': 'fa-file-contract',
        'Policy': 'fa-balance-scale',
        'Audit': 'fa-user-secret',
        'Compliance': 'fa-shield-alt',
        'Regulation': 'fa-gavel',
        'License': 'fa-id-card',
        'Investigation': 'fa-search',
        'Incident': 'fa-exclamation-triangle',
        'Litigation': 'fa-balance-scale-left',

        # Education and Learning
        'Student': 'fa-user-graduate',
        'Teacher': 'fa-chalkboard-teacher',
        'Course': 'fa-book-open',
        'Lesson': 'fa-book-reader',
        'Exam': 'fa-file-alt',
        'Assignment': 'fa-tasks',
        'Grade': 'fa-award',
        'Class': 'fa-school',
        'Attendance': 'fa-calendar-check',
        'Library': 'fa-book',
        'Lecture': 'fa-podcast',
        'Discussion': 'fa-comment-alt',

        # Analytics and Reporting
        'Report': 'fa-chart-line',
        'Chart': 'fa-chart-bar',
        'Dashboard': 'fa-tachometer-alt',
        'Data': 'fa-database',
        'Metric': 'fa-ruler',
        'Goal': 'fa-bullseye',
        'KeyPerformanceIndicator': 'fa-bullseye',
        'Performance': 'fa-chart-line',
        'Trend': 'fa-chart-area',
        'Forecast': 'fa-chart-line',

        # Calendar and Time Management
        'Calendar': 'fa-calendar',
        'Event': 'fa-calendar-alt',
        'Appointment': 'fa-calendar-check',
        'Meeting': 'fa-handshake',
        'Reminder': 'fa-clock',
        'TimeLog': 'fa-stopwatch',
        'Timesheet': 'fa-clock',
        'Schedule': 'fa-calendar-alt',

        # Miscellaneous
        'Feedback': 'fa-comment-dots',
        'Survey': 'fa-poll',
        'Poll': 'fa-poll-h',
        'Map': 'fa-map',
        'Location': 'fa-map-marker-alt',
        'Weather': 'fa-cloud-sun',
        'News': 'fa-newspaper',
        'Gallery': 'fa-images',
        'Video': 'fa-video',
        'Podcast': 'fa-podcast',
    }

    # User-defined custom icons, if provided (with substring matching)
    if custom_icons:
        for key in custom_icons:
            if key.lower() in model_name.lower():  # Substring matching (case-insensitive)
                return custom_icons[key]

    # Check if the model_name contains a key in model_icons (substring matching)
    for key in model_icons:
        if key.lower() in model_name.lower():  # Substring matching (case-insensitive)
            return model_icons[key]

    # Icon selection based on the icon set
    if icon_set == 'fontawesome':
        # Check if a default icon exists for the view type
        return default_icons.get(view_type, 'fa-table')  # Fallback to a generic icon

    elif icon_set == 'material':
        material_icons = {
            'ModelView': 'table_chart',
            'AddView': 'add_circle',
            'EditView': 'edit',
            'DetailView': 'info',
            'DeleteView': 'delete',
            'ListView': 'list',
            'MasterDetailView': 'link',
            'MultipleView': 'category',
            'ChartView': 'bar_chart',
            'ModelRestApi': 'api',
            'DashboardView': 'dashboard',
            'ReportView': 'description',
            'ExportView': 'cloud_download',
            'ImportView': 'cloud_upload',
        }
        return material_icons.get(view_type, 'table_chart')  # Fallback to a generic Material icon

    elif icon_set == 'custom_svg':
        # Handle custom SVG icons if provided
        svg_icons = {
            'User': 'custom-user-icon.svg',
            'Product': 'custom-product-icon.svg',
            'Order': 'custom-order-icon.svg',
            # Add more SVG mappings here...
        }
        return svg_icons.get(model_name, 'custom-default-icon.svg')

    # Fallback to a default icon for the icon set
    return 'fa-table'  # Fallback to FontAwesome table icon if everything else fails


def generate_list_with_lazy_loading_template():
    """
    Generate the HTML template for list view with lazy loading.

    Returns:
        str: HTML content for the list_with_lazy_loading.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>{{ title }}</h1>

            {# Search form #}
            <div class="well well-sm">
                <form class="form-inline" id="searchForm" method="get">
                    <div class="form-group">
                        <input type="text" class="form-control" name="search" placeholder="Search..." value="{{ request.args.get('search', '') }}">
                    </div>
                    <button type="submit" class="btn btn-primary">Search</button>
                </form>
            </div>

            {# Data table #}
            <table class="table table-hover table-bordered">
                <thead>
                    <tr>
                        {% for col in list_columns %}
                        <th>{{ col }}</th>
                        {% endfor %}
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="dataTable">
                    {# Data rows will be inserted here dynamically #}
                </tbody>
            </table>

            {# Load more button #}
            <button id="loadMore" class="btn btn-default btn-block" style="display: none;">Load More</button>

            {# Loading indicator #}
            <div id="loading" class="text-center" style="display: none;">
                <i class="fa fa-spinner fa-spin fa-3x"></i>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block scripts %}
{{ super() }}
<script>
    var page = 1;
    var hasMore = true;
    var isLoading = false;
    var lastId = 0;

    function loadData() {
        if (isLoading || !hasMore) return;

        isLoading = true;
        $('#loading').show();
        $('#loadMore').hide();

        $.ajax({
            url: '{{ url_for(modelview_name + ".api_get_list") }}',
            data: {
                page: page,
                last_id: lastId,
                search: $('input[name="search"]').val()
            },
            success: function(response) {
                var rows = '';
                $.each(response.data, function(index, item) {
                    rows += '<tr>';
                    {% for col in list_columns %}
                    rows += '<td>' + (item.{{ col }} || '') + '</td>';
                    {% endfor %}
                    rows += '<td>';
                    rows += '<a href="{{ url_for(modelview_name + ".show", pk="') }}' + item.id + '" class="btn btn-sm btn-primary">View</a> ';
                    rows += '<a href="{{ url_for(modelview_name + ".edit", pk="') }}' + item.id + '" class="btn btn-sm btn-success">Edit</a> ';
                    rows += '<a href="{{ url_for(modelview_name + ".delete", pk="') }}' + item.id + '" class="btn btn-sm btn-danger">Delete</a>';
                    rows += '</td>';
                    rows += '</tr>';
                    lastId = item.id;
                });
                $('#dataTable').append(rows);

                hasMore = response.has_more;
                if (hasMore) {
                    $('#loadMore').show();
                }
                page++;
            },
            error: function() {
                alert('An error occurred while loading data.');
            },
            complete: function() {
                isLoading = false;
                $('#loading').hide();
            }
        });
    }

    $(document).ready(function() {
        loadData();

        $('#loadMore').click(loadData);

        $('#searchForm').submit(function(e) {
            e.preventDefault();
            $('#dataTable').empty();
            page = 1;
            lastId = 0;
            hasMore = true;
            loadData();
        });
    });
</script>
{% endblock %}
"""
    return template

def generate_interactive_filter_template():
    """
    Generate the HTML content for the interactive_filters.html template.

    Returns:
        str: HTML content for the interactive_filters.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>{{ title }}</h1>

            {# Interactive Filter Form #}
            <form id="filterForm" class="form-horizontal">
                {% for filter_col in filter_columns %}
                <div class="form-group">
                    <label class="col-sm-2 control-label">{{ filter_col|capitalize }}</label>
                    <div class="col-sm-10">
                        {% if filter_col in filter_rel_fields %}
                            <select name="{{ filter_col }}" class="form-control select2" multiple="multiple">
                                <option value="">Select {{ filter_col|capitalize }}</option>
                                {% for value, label in filter_rel_fields[filter_col] %}
                                    <option value="{{ value }}">{{ label }}</option>
                                {% endfor %}
                            </select>
                        {% else %}
                            <input type="text" name="{{ filter_col }}" class="form-control" placeholder="Filter by {{ filter_col|capitalize }}">
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
                <div class="form-group">
                    <div class="col-sm-offset-2 col-sm-10">
                        <button type="submit" class="btn btn-primary">Apply Filters</button>
                        <button type="button" id="resetFilters" class="btn btn-default">Reset Filters</button>
                    </div>
                </div>
            </form>

            {# Results Table #}
            <table class="table table-hover table-bordered">
                <thead>
                    <tr>
                        {% for col in list_columns %}
                        <th>{{ col|capitalize }}</th>
                        {% endfor %}
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="resultsTable">
                    {# Results will be dynamically inserted here #}
                </tbody>
            </table>

            {# Pagination #}
            <nav aria-label="Page navigation">
                <ul class="pagination" id="pagination">
                    {# Pagination links will be dynamically inserted here #}
                </ul>
            </nav>

            {# Loading Indicator #}
            <div id="loading" class="text-center" style="display: none;">
                <i class="fa fa-spinner fa-spin fa-3x"></i>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css" rel="stylesheet" />
<script>
$(document).ready(function() {
    $('.select2').select2();

    var currentPage = 1;

    function loadResults(page) {
        $('#loading').show();
        var formData = $('#filterForm').serialize() + '&page=' + page;

        $.ajax({
            url: '{{ url_for(modelview_name + ".api_filter_results") }}',
            data: formData,
            success: function(response) {
                var rows = '';
                $.each(response.data, function(index, item) {
                    rows += '<tr>';
                    {% for col in list_columns %}
                    rows += '<td>' + (item.{{ col }} || '') + '</td>';
                    {% endfor %}
                    rows += '<td>';
                    rows += '<a href="{{ url_for(modelview_name + ".show", pk="') }}' + item.id + '" class="btn btn-sm btn-primary">View</a> ';
                    rows += '<a href="{{ url_for(modelview_name + ".edit", pk="') }}' + item.id + '" class="btn btn-sm btn-success">Edit</a> ';
                    rows += '<a href="{{ url_for(modelview_name + ".delete", pk="') }}' + item.id + '" class="btn btn-sm btn-danger">Delete</a>';
                    rows += '</td>';
                    rows += '</tr>';
                });
                $('#resultsTable').html(rows);

                // Update pagination
                var pagination = '';
                for (var i = 1; i <= response.total_pages; i++) {
                    pagination += '<li class="page-item ' + (i === response.page ? 'active' : '') + '">';
                    pagination += '<a class="page-link" href="#" data-page="' + i + '">' + i + '</a>';
                    pagination += '</li>';
                }
                $('#pagination').html(pagination);

                currentPage = response.page;
            },
            error: function() {
                alert('An error occurred while filtering data.');
            },
            complete: function() {
                $('#loading').hide();
            }
        });
    }

    $('#filterForm').submit(function(e) {
        e.preventDefault();
        loadResults(1);
    });

    $('#resetFilters').click(function() {
        $('#filterForm')[0].reset();
        $('.select2').val(null).trigger('change');
        loadResults(1);
    });

    $(document).on('click', '.pagination .page-link', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        loadResults(page);
    });

    // Initial load
    loadResults(1);
});
</script>
{% endblock %}
"""
    return template


def generate_search_results_template():
    """
    Generate the HTML content for the search_results.html template.

    Returns:
        str: HTML content for the search_results.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>Search Results</h1>

            {# Search form #}
            <div class="well well-sm">
                <form class="form-inline" id="searchForm" method="get">
                    <div class="form-group">
                        <input type="text" class="form-control" name="q" placeholder="Search..." value="{{ search_query }}">
                    </div>
                    <button type="submit" class="btn btn-primary">Search</button>
                </form>
            </div>

            {% if search_query %}
                <h3>Results for "{{ search_query }}"</h3>
            {% endif %}

            {% if not items %}
                <p>No results found.</p>
            {% else %}
                {# Results table #}
                <table class="table table-hover table-bordered">
                    <thead>
                        <tr>
                            {% for col in list_columns %}
                            <th>{{ col|capitalize }}</th>
                            {% endfor %}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            {% for col in list_columns %}
                            <td>
                                {% if item[col + '_highlighted'] %}
                                    {{ item[col + '_highlighted']|safe }}
                                {% else %}
                                    {{ item[col] }}
                                {% endif %}
                            </td>
                            {% endfor %}
                            <td>
                                <a href="{{ url_for(modelview_name + '.show', pk=item['id']) }}" class="btn btn-sm btn-primary">View</a>
                                <a href="{{ url_for(modelview_name + '.edit', pk=item['id']) }}" class="btn btn-sm btn-success">Edit</a>
                                <a href="{{ url_for(modelview_name + '.delete', pk=item['id']) }}" class="btn btn-sm btn-danger">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                {# Pagination #}
                {% if pagination %}
                <nav aria-label="Page navigation">
                    <ul class="pagination">
                        {% for page in pagination.iter_pages() %}
                            {% if page %}
                                {% if page != pagination.page %}
                                    <li class="page-item">
                                        <a class="page-link" href="{{ url_for(modelview_name + '.search', q=search_query, page=page) }}">{{ page }}</a>
                                    </li>
                                {% else %}
                                    <li class="page-item active">
                                        <span class="page-link">{{ page }} <span class="sr-only">(current)</span></span>
                                    </li>
                                {% endif %}
                            {% else %}
                                <li class="page-item disabled">
                                    <span class="page-link">...</span>
                                </li>
                            {% endif %}
                        {% endfor %}
                    </ul>
                </nav>
                {% endif %}
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script>
    $(document).ready(function() {
        // You can add any JavaScript functionality here if needed
    });
</script>
{% endblock %}
"""
    return template

def generate_filter_results_template():
    """
    Generate the HTML content for the filter_results.html template.

    Returns:
        str: HTML content for the filter_results.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>{{ title }}</h1>

            {# Filter Summary #}
            <div class="well well-sm">
                <h4>Applied Filters:</h4>
                {% if filter_params %}
                    <ul>
                    {% for key, value in filter_params.items() %}
                        <li><strong>{{ key|capitalize }}:</strong> {{ value }}</li>
                    {% endfor %}
                    </ul>
                    <a href="{{ url_for(modelview_name + '.list') }}" class="btn btn-default btn-sm">Clear All Filters</a>
                {% else %}
                    <p>No filters applied.</p>
                {% endif %}
            </div>

            {# Results Table #}
            {% if items %}
                <table class="table table-hover table-bordered">
                    <thead>
                        <tr>
                            {% for col in list_columns %}
                            <th>{{ col|capitalize }}</th>
                            {% endfor %}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            {% for col in list_columns %}
                            <td>{{ item[col] }}</td>
                            {% endfor %}
                            <td>
                                <a href="{{ url_for(modelview_name + '.show', pk=item['id']) }}" class="btn btn-sm btn-primary">View</a>
                                <a href="{{ url_for(modelview_name + '.edit', pk=item['id']) }}" class="btn btn-sm btn-success">Edit</a>
                                <a href="{{ url_for(modelview_name + '.delete', pk=item['id']) }}" class="btn btn-sm btn-danger">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                {# Pagination #}
                {% if pagination %}
                <nav aria-label="Page navigation">
                    <ul class="pagination">
                        {% for page in pagination.iter_pages() %}
                            {% if page %}
                                {% if page != pagination.page %}
                                    <li class="page-item">
                                        <a class="page-link" href="{{ url_for(modelview_name + '.filter', page=page, **filter_params) }}">{{ page }}</a>
                                    </li>
                                {% else %}
                                    <li class="page-item active">
                                        <span class="page-link">{{ page }} <span class="sr-only">(current)</span></span>
                                    </li>
                                {% endif %}
                            {% else %}
                                <li class="page-item disabled">
                                    <span class="page-link">...</span>
                                </li>
                            {% endif %}
                        {% endfor %}
                    </ul>
                </nav>
                {% endif %}
            {% else %}
                <p>No results found matching the applied filters.</p>
            {% endif %}

            {# Back to Filter Form #}
            <a href="{{ url_for(modelview_name + '.list') }}" class="btn btn-default">Back to Filters</a>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script>
    $(document).ready(function() {
        // You can add any JavaScript functionality here if needed
    });
</script>
{% endblock %}
"""
    return template

def generate_personalize_template():
    """
    Generate the HTML content for the personalize.html template.

    Returns:
        str: HTML content for the personalize.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>Personalize View Settings</h1>

            <form id="personalizeForm" method="post" action="{{ url_for(modelview_name + '.personalize') }}">
                {{ form.csrf_token }}

                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Select Columns to Display</h3>
                    </div>
                    <div class="panel-body">
                        <div class="row">
                            {% for column in columns %}
                            <div class="col-md-4">
                                <div class="checkbox">
                                    <label>
                                        <input type="checkbox" name="columns" value="{{ column }}"
                                               {% if column in current_columns %}checked{% endif %}>
                                        {{ column|capitalize }}
                                    </label>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Column Order</h3>
                    </div>
                    <div class="panel-body">
                        <ul id="columnOrder" class="list-group">
                            {% for column in current_columns %}
                            <li class="list-group-item" data-column="{{ column }}">
                                <i class="fa fa-bars handle"></i> {{ column|capitalize }}
                            </li>
                            {% endfor %}
                        </ul>
                        <input type="hidden" name="column_order" id="columnOrderInput">
                    </div>
                </div>

                <div class="form-group">
                    <label for="page_size">Items per page:</label>
                    <input type="number" class="form-control" id="page_size" name="page_size"
                           value="{{ current_page_size }}" min="1" max="100">
                </div>

                <button type="submit" class="btn btn-primary">Save Settings</button>
                <a href="{{ url_for(modelview_name + '.list') }}" class="btn btn-default">Cancel</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.14.0/Sortable.min.js"></script>
<script>
    $(document).ready(function() {
        var el = document.getElementById('columnOrder');
        var sortable = Sortable.create(el, {
            handle: '.handle',
            animation: 150,
            onEnd: function() {
                updateColumnOrder();
            }
        });

        function updateColumnOrder() {
            var order = sortable.toArray();
            $('#columnOrderInput').val(JSON.stringify(order));
        }

        updateColumnOrder();

        $('#personalizeForm').submit(function() {
            updateColumnOrder();
        });

        $('input[name="columns"]').change(function() {
            var column = $(this).val();
            if ($(this).is(':checked')) {
                $('#columnOrder').append(
                    '<li class="list-group-item" data-column="' + column + '">' +
                    '<i class="fa fa-bars handle"></i> ' + column.charAt(0).toUpperCase() + column.slice(1) +
                    '</li>'
                );
            } else {
                $('#columnOrder li[data-column="' + column + '"]').remove();
            }
            updateColumnOrder();
        });
    });
</script>
{% endblock %}
"""
    return template



def generate_print_items_template():
    """
    Generate the HTML content for the print_items.html template.

    Returns:
        str: HTML content for the print_items.html template
    """
    template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Print {{ model }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .print-header, .print-footer {
            text-align: center;
            margin-bottom: 20px;
            font-size: 12px;
            color: #666;
        }
        @media print {
            .no-print {
                display: none;
            }
            body {
                font-size: 12pt;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="print-header">
            Printed on {{ now.strftime('%Y-%m-%d %H:%M:%S') }}
        </div>

        <h1>{{ model }} - Print View</h1>

        <table>
            <thead>
                <tr>
                    {% for col in list_columns %}
                    <th>{{ col|capitalize }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    {% for col in list_columns %}
                    <td>{{ item[col] }}</td>
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="print-footer">
            Page 1 of 1
        </div>

        <div class="no-print">
            <button onclick="window.print()">Print</button>
            <button onclick="window.close()">Close</button>
        </div>
    </div>

    <script>
        window.onload = function() {
            if (!window.location.search.includes('no_print')) {
                window.print();
            }
        }
    </script>
</body>
</html>
"""
    return template


def generate_bulk_edit_template():
    """
    Generate the HTML content for the bulk_edit.html template.

    Returns:
        str: HTML content for the bulk_edit.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>Bulk Edit {{ model_name }}</h1>

            <form id="bulk-edit-form" method="post" action="{{ url_for(modelview_name + '.bulk_edit_form', ids=ids) }}">
                {{ form.csrf_token }}

                <div class="alert alert-info">
                    You are editing {{ items|length }} item(s). Fields left blank will not be updated.
                </div>

                {% for field in form %}
                    {% if field.name != 'csrf_token' %}
                        <div class="form-group">
                            {{ field.label }}
                            {{ field(class="form-control") }}
                            {% if field.errors %}
                                <div class="alert alert-danger">
                                    {% for error in field.errors %}
                                        {{ error }}
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    {% endif %}
                {% endfor %}

                <button type="submit" class="btn btn-primary">Update Items</button>
                <a href="{{ url_for(modelview_name + '.list') }}" class="btn btn-default">Cancel</a>
            </form>

            <h2 class="mt-4">Items being edited:</h2>
            <table class="table table-bordered table-hover">
                <thead>
                    <tr>
                        {% for col in list_columns %}
                            <th>{{ col|capitalize }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                        <tr>
                            {% for col in list_columns %}
                                <td>{{ item[col] }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script>
    $(document).ready(function() {
        // You can add custom JavaScript for the bulk edit form here
        // For example, you might want to add confirmation before submission
        $('#bulk-edit-form').submit(function(e) {
            if (!confirm('Are you sure you want to update these items?')) {
                e.preventDefault();
            }
        });
    });
</script>
{% endblock %}
"""
    return template


def generate_multiple_view():
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container-fluid">
    <h2>{{ list_title }}</h2>

    {# Layout Controls #}
    <div class="layout-controls mb-3">
        <div class="btn-group" role="group" aria-label="Layout Options">
            {% for layout_key, layout_name in layout_options.items() %}
                <a href="{{ url_for('.change_layout', layout=layout_key) }}"
                    class="btn btn-outline-primary {% if layout == layout_key %}active{% endif %}">
                    {{ layout_name }}
                </a>
            {% endfor %}
        </div>
    </div>

    {# Search Bar #}
    <div class="search-bar mb-3">
        <input type="text" id="global-search" class="form-control" placeholder="Search across all views...">
    </div>

    {# Multiple View Content #}
    <div class="multiple-view-content">
        {% if layout == 'tabs' %}
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                {% for view in views %}
                    <li class="nav-item" role="presentation">
                        <button class="nav-link {% if loop.first %}active{% endif %}" id="tab-{{ view.__class__.__name__ }}"
                                data-bs-toggle="tab" data-bs-target="#content-{{ view.__class__.__name__ }}" type="button"
                                role="tab" aria-controls="content-{{ view.__class__.__name__ }}" aria-selected="{% if loop.first %}true{% else %}false{% endif %}">
                            {{ view.list_title }}
                        </button>
                    </li>
                {% endfor %}
            </ul>
            <div class="tab-content" id="myTabContent">
                {% for view in views %}
                    <div class="tab-pane fade {% if loop.first %}show active{% endif %}" id="content-{{ view.__class__.__name__ }}"
                            role="tabpanel" aria-labelledby="tab-{{ view.__class__.__name__ }}">
                        <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                            {# Content will be loaded dynamically #}
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif layout == 'accordion' %}
            <div class="accordion" id="viewAccordion">
                {% for view in views %}
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading-{{ view.__class__.__name__ }}">
                            <button class="accordion-button {% if not loop.first %}collapsed{% endif %}" type="button"
                                    data-bs-toggle="collapse" data-bs-target="#collapse-{{ view.__class__.__name__ }}"
                                    aria-expanded="{% if loop.first %}true{% else %}false{% endif %}" aria-controls="collapse-{{ view.__class__.__name__ }}">
                                {{ view.list_title }}
                            </button>
                        </h2>
                        <div id="collapse-{{ view.__class__.__name__ }}" class="accordion-collapse collapse {% if loop.first %}show{% endif %}"
                                aria-labelledby="heading-{{ view.__class__.__name__ }}" data-bs-parent="#viewAccordion">
                            <div class="accordion-body">
                                <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                                    {# Content will be loaded dynamically #}
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif layout == 'grid' %}
            <div class="row">
                {% for view in views %}
                    <div class="col-md-6 mb-4">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">{{ view.list_title }}</h5>
                            </div>
                            <div class="card-body">
                                <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                                    {# Content will be loaded dynamically #}
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif layout == 'list' %}
            <div class="list-group">
                {% for view in views %}
                    <div class="list-group-item">
                        <h5 class="mb-1">{{ view.list_title }}</h5>
                        <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                            {# Content will be loaded dynamically #}
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif layout == 'cards' %}
            <div class="row">
                {% for view in views %}
                    <div class="col-md-4 mb-4">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">{{ view.list_title }}</h5>
                            </div>
                            <div class="card-body">
                                <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                                    {# Content will be loaded dynamically #}
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>

        {% elif layout == 'sidebar' %}
            <div class="row">
                <div class="col-md-3">
                    <div class="list-group" id="list-tab" role="tablist">
                        {% for view in views %}
                            <a class="list-group-item list-group-item-action {% if loop.first %}active{% endif %}"
                                id="list-{{ view.__class__.__name__ }}-list" data-bs-toggle="list"
                                href="#list-{{ view.__class__.__name__ }}" role="tab"
                                aria-controls="{{ view.__class__.__name__ }}">{{ view.list_title }}</a>
                        {% endfor %}
                    </div>
                </div>
                <div class="col-md-9">
                    <div class="tab-content" id="nav-tabContent">
                        {% for view in views %}
                            <div class="tab-pane fade {% if loop.first %}show active{% endif %}"
                                    id="list-{{ view.__class__.__name__ }}" role="tabpanel"
                                    aria-labelledby="list-{{ view.__class__.__name__ }}-list">
                                <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                                    {# Content will be loaded dynamically #}
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

        {% elif layout == 'split' %}
            <div class="row">
                <div class="col-md-6">
                    <h3>{{ views[0].list_title }}</h3>
                    <div class="view-content" data-view="{{ views[0].__class__.__name__ }}">
                        {# Content will be loaded dynamically #}
                    </div>
                </div>
                <div class="col-md-6">
                    <h3>{{ views[1].list_title }}</h3>
                    <div class="view-content" data-view="{{ views[1].__class__.__name__ }}">
                        {# Content will be loaded dynamically #}
                    </div>
                </div>
            </div>

        {% elif layout == 'wizard' %}
            <div class="wizard">
                <ul class="nav nav-tabs" role="tablist">
                    {% for view in views %}
                        <li class="nav-item" role="presentation">
                            <button class="nav-link {% if loop.first %}active{% endif %}"
                                    id="step{{ loop.index }}-tab" data-bs-toggle="tab"
                                    data-bs-target="#step{{ loop.index }}" type="button" role="tab"
                                    aria-controls="step{{ loop.index }}" aria-selected="{% if loop.first %}true{% else %}false{% endif %}">
                                Step {{ loop.index }}
                            </button>
                        </li>
                    {% endfor %}
                </ul>
                <div class="tab-content">
                    {% for view in views %}
                        <div class="tab-pane fade {% if loop.first %}show active{% endif %}"
                                id="step{{ loop.index }}" role="tabpanel" aria-labelledby="step{{ loop.index }}-tab">
                            <h3>{{ view.list_title }}</h3>
                            <div class="view-content" data-view="{{ view.__class__.__name__ }}">
                                {# Content will be loaded dynamically #}
                            </div>
                        </div>
                    {% endfor %}
                </div>
            </div>
        {% endif %}
    </div>
</div>

{# Relationships Visualization #}
<div id="relationships-graph" class="mt-4"></div>

{% endblock %}

{% block scripts %}
{{ super() }}
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
<script>
    // Function to load view content
    function loadViewContent(viewName) {
        fetch(`/api/data/${viewName}`)
            .then(response => response.json())
            .then(data => {
                const viewContent = document.querySelector(`.view-content[data-view="${viewName}"]`);
                if (data.data && data.data.length > 0) {
                    viewContent.innerHTML = `
                        <table class="table">
                            <thead>
                                <tr>${Object.keys(data.data[0]).map(key => `<th>${key}</th>`).join('')}</tr>
                            </thead>
                            <tbody>
                                ${data.data.map(item => `
                                    <tr>${Object.values(item).map(value => `<td>${value}</td>`).join('')}</tr>
                                `).join('')}
                            </tbody>
                        </table>
                        <nav aria-label="Page navigation">
                            <ul class="pagination">
                                ${Array.from({length: data.pages}, (_, i) => i + 1).map(page => `
                                    <li class="page-item ${page === data.page ? 'active' : ''}">
                                        <a class="page-link" href="#" onclick="loadViewContent('${viewName}', ${page})">${page}</a>
                                    </li>
                                `).join('')}
                            </ul>
                        </nav>
                    `;
                } else {
                    viewContent.innerHTML = '<p>No data available</p>';
                }
            });
    }

    // Update the global search functionality:
    document.getElementById('global-search').addEventListener('input', function(e) {
        const searchTerm = e.target.value;
        if (searchTerm.length > 2) {
            fetch(`/api/search?q=${searchTerm}`)
                .then(response => response.json())
                .then(data => {
                    Object.entries(data).forEach(([viewName, results]) => {
                        const viewContent = document.querySelector(`.view-content[data-view="${viewName}"]`);
                        if (results && results.length > 0) {
                            viewContent.innerHTML = `
                                <table class="table">
                                    <thead>
                                        <tr>${Object.keys(results[0]).map(key => `<th>${key}</th>`).join('')}</tr>
                                    </thead>
                                    <tbody>
                                        ${results.map(item => `
                                            <tr>${Object.values(item).map(value => `<td>${value}</td>`).join('')}</tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                        } else {
                            viewContent.innerHTML = '<p>No results found</p>';
                        }
                    });
                });
        }
    });

    // Load content for all views
    document.querySelectorAll('.view-content').forEach(viewContent => {
        const viewName = viewContent.dataset.view;
        loadViewContent(viewName);
    });


    // Relationships visualization
    const relationships = {{ relationships|safe }};
    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();

    relationships.forEach(rel => {
        if (!nodes.get(rel.from)) {
            nodes.add({id: rel.from, label: rel.from});
        }
        if (!nodes.get(rel.to)) {
            nodes.add({id: rel.to, label: rel.to});
        }
        edges.add({from: rel.from, to: rel.to, label: `${rel.from_col} -> ${rel.to_col}`});
    });

    const container = document.getElementById('relationships-graph');
    const data = {
        nodes: nodes,
        edges: edges
    };
    const options = {};
    const network = new vis.Network(container, data, options);
</script>
{% endblock %}

"""
    return template


def generate_wizard_template():
    """
    Generate the HTML content for the wizard.html template.

    Returns:
        str: HTML content for the wizard.html template
    """
    template = """
{% extends "appbuilder/base.html" %}
{% import 'appbuilder/general/lib.html' as lib %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>{{ modelview_name }} Wizard</h1>

            {# Progress bar #}
            <div class="progress mb-4">
                <div class="progress-bar" role="progressbar" style="width: {{ progress }}%;"
                     aria-valuenow="{{ progress }}" aria-valuemin="0" aria-valuemax="100">
                    {{ progress|round|int }}%
                </div>
            </div>

            {# Step indicator #}
            <ul class="nav nav-pills nav-justified mb-4">
                {% for i in range(1, total_steps + 1) %}
                <li class="nav-item">
                    <a class="nav-link {% if i == current_step %}active{% elif i < current_step %}complete{% endif %}"
                       {% if i < current_step %}href="{{ url_for(modelview_name + '.step' + i|string) }}"{% endif %}>
                        Step {{ i }}
                    </a>
                </li>
                {% endfor %}
                <li class="nav-item">
                    <a class="nav-link {% if current_step == 'submit' %}active{% endif %}"
                       {% if progress == 100 %}href="{{ url_for(modelview_name + '.submit') }}"{% endif %}>
                        Submit
                    </a>
                </li>
            </ul>

            <h2>{{ step_description }}</h2>

            <form method="post" enctype="multipart/form-data">
                {{ form.hidden_tag() }}

                {% for field in form %}
                    {% if field.type != 'CSRFTokenField' %}
                        <div class="form-group">
                            {{ field.label }}
                            {{ field(class="form-control") }}
                            {% if field.errors %}
                                <div class="alert alert-danger">
                                    {% for error in field.errors %}
                                        {{ error }}
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    {% endif %}
                {% endfor %}

                <div class="form-group mt-4">
                    {% if previous_step %}
                        <a href="{{ url_for(modelview_name + '.step' + previous_step|string) }}"
                           class="btn btn-secondary">Previous</a>
                    {% endif %}

                    {% if next_step == 'submit' %}
                        <button type="submit" class="btn btn-primary">Submit</button>
                    {% else %}
                        <button type="submit" class="btn btn-primary">Next</button>
                    {% endif %}
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script>
    $(document).ready(function() {
        // You can add custom JavaScript for the wizard here
        // For example, you might want to add client-side validation
        $('form').submit(function(e) {
            var isValid = true;
            $('.form-control').each(function() {
                if ($(this).prop('required') && !$(this).val()) {
                    isValid = false;
                    $(this).addClass('is-invalid');
                } else {
                    $(this).removeClass('is-invalid');
                }
            });
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
</script>
{% endblock %}
"""
    return template



def write_templates(templates_dir='templates'):
    """
    Write generated templates to files.

    Args:
        templates_dir (str): Directory where templates should be written
    """
    import os

    # Ensure the templates directory exists
    os.makedirs(templates_dir, exist_ok=True)

    # Generate and write the interactive filters template
    interactive_filters_content = generate_interactive_filter_template()
    with open(os.path.join(templates_dir, 'interactive_filters.html'), 'w') as f:
        f.write(interactive_filters_content)

    list_with_lazy_loading_content = generate_list_with_lazy_loading_template()
    with open(os.path.join(templates_dir, 'list_with_lazy_loading.html'), 'w') as f:
        f.write(list_with_lazy_loading_content)

    search_results_content = generate_search_results_template()
    with open(os.path.join(templates_dir, 'search_results.html'), 'w') as f:
        f.write(search_results_content)

 # Generate and write the filter results template
    filter_results_content = generate_filter_results_template()
    with open(os.path.join(templates_dir, 'filter_results.html'), 'w') as f:
        f.write(filter_results_content)
        print(f"Templates have been written to the {templates_dir} directory.")

    # Generate and write the personalize template
    personalize_content = generate_personalize_template()
    with open(os.path.join(templates_dir, 'personalize.html'), 'w') as f:
        f.write(personalize_content)

     # Generate and write the print items template
    print_items_content = generate_print_items_template()
    with open(os.path.join(templates_dir, 'print_items.html'), 'w') as f:
        f.write(print_items_content)

    # Generate and write the bulk edit template
    bulk_edit_content = generate_bulk_edit_template()
    with open(os.path.join(templates_dir, 'bulk_edit.html'), 'w') as f:
        f.write(bulk_edit_content)

    multi_view_template = generate_multiple_view()
    with open(os.path.join(templates_dir, 'multiple_view.html'), 'w') as f:
        f.write(multi_view_template)

    wizard_content = generate_wizard_template()
    with open(os.path.join(templates_dir, 'wizard.html'), 'w') as f:
        f.write(wizard_content)

    print(f"Templates have been written to the {templates_dir} directory.")


# Usage in your main script
