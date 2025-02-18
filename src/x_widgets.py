from typing import Any, Dict, Optional
from wtforms.widgets import html_params, HTMLString
from flask_appbuilder.widgets import FormWidget

class BaseCustomWidget(FormWidget):
    """Base class for custom widgets with common functionality"""
    template = """
        <div class="form-group">
            <label class="control-label">%(label)s</label>
            <div class="controls">%(field)s</div>
            <div class="help-block">%(help)s</div>
        </div>
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.css_class = kwargs.get('css_class', '')
        self.placeholder = kwargs.get('placeholder', '')
        self.readonly = kwargs.get('readonly', False)

    def __call__(self, field: Any, **kwargs) -> HTMLString:
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('class', f'form-control {self.css_class}')
        kwargs.setdefault('placeholder', self.placeholder)
        if self.readonly:
            kwargs['readonly'] = 'readonly'
        return HTMLString(self.template % {
            'label': field.label.text,
            'field': self.render_field(field, **kwargs),
            'help': field.description or ''
        })

class MoneyWidget(BaseCustomWidget):
    """Widget for handling money/currency input with formatting"""
    def render_field(self, field: Any, **kwargs) -> str:
        kwargs['type'] = 'number'
        kwargs['step'] = '0.01'
        kwargs['data-type'] = 'currency'
        html = f"""
            <div class="input-group">
                <span class="input-group-addon">$</span>
                <input {html_params(**kwargs)} value="{field.data or ''}">
            </div>
            <script>
                $(document).ready(function() {{
                    $('#{field.id}').on('input', function() {{
                        var value = $(this).val();
                        if (value) {{
                            $(this).val(parseFloat(value).toFixed(2));
                        }}
                    }});
                }});
            </script>
        """
        return html

class PhoneWidget(BaseCustomWidget):
    """Widget for phone number input with formatting"""
    def render_field(self, field: Any, **kwargs) -> str:
        kwargs['type'] = 'tel'
        kwargs['pattern'] = '[0-9]{3}-[0-9]{3}-[0-9]{4}'
        html = f"""
            <input {html_params(**kwargs)} value="{field.data or ''}">
            <script>
                $(document).ready(function() {{
                    $('#{field.id}').mask('000-000-0000');
                }});
            </script>
        """
        return html

class AddressWidget(BaseCustomWidget):
    """Widget for address input with multiple fields"""
    def render_field(self, field: Any, **kwargs) -> str:
        value = field.data or {}
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value)
            except:
                value = {}

        html = f"""
            <div class="address-widget" id="{field.id}_container">
                <input type="text" class="form-control" id="{field.id}_street"
                       placeholder="Street Address" value="{value.get('street', '')}">
                <div class="row">
                    <div class="col-md-6">
                        <input type="text" class="form-control" id="{field.id}_city"
                               placeholder="City" value="{value.get('city', '')}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" id="{field.id}_state"
                               placeholder="State" value="{value.get('state', '')}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" id="{field.id}_zip"
                               placeholder="ZIP" value="{value.get('zip', '')}">
                    </div>
                </div>
                <input type="hidden" name="{field.name}" id="{field.id}" value="{field.data or ''}">
            </div>
            <script>
                $(document).ready(function() {{
                    function updateAddress() {{
                        var data = {{
                            street: $('#{field.id}_street').val(),
                            city: $('#{field.id}_city').val(),
                            state: $('#{field.id}_state').val(),
                            zip: $('#{field.id}_zip').val()
                        }};
                        $('#{field.id}').val(JSON.stringify(data));
                    }}

                    $('#{field.id}_container input').on('change', updateAddress);
                }});
            </script>
        """
        return html

class JSONEditorWidget(BaseCustomWidget):
    """Widget for JSON editing with syntax highlighting"""
    def render_field(self, field: Any, **kwargs) -> str:
        value = field.data
        if value and isinstance(value, dict):
            import json
            value = json.dumps(value, indent=2)

        html = f"""
            <div id="{field.id}_editor" style="height: 300px;"></div>
            <input type="hidden" name="{field.name}" id="{field.id}" value="{value or ''}">
            <script>
                $(document).ready(function() {{
                    var editor = ace.edit("{field.id}_editor");
                    editor.setTheme("ace/theme/monokai");
                    editor.session.setMode("ace/mode/json");
                    editor.setValue({json.dumps(value or '')});

                    editor.on('change', function() {{
                        try {{
                            var value = editor.getValue();
                            JSON.parse(value); // Validate JSON
                            $('#{field.id}').val(value);
                            editor.getSession().setAnnotations([]);
                        }} catch (e) {{
                            editor.getSession().setAnnotations([{{
                                row: 0,
                                column: 0,
                                text: "Invalid JSON: " + e.message,
                                type: "error"
                            }}]);
                        }}
                    }});
                }});
            </script>
        """
        return html

class ColorPickerWidget(BaseCustomWidget):
    """Widget for color picking with preview"""
    def render_field(self, field: Any, **kwargs) -> str:
        kwargs['type'] = 'text'
        kwargs['data-coloris'] = ''
        html = f"""
            <div class="input-group color-picker">
                <input {html_params(**kwargs)} value="{field.data or '#000000'}">
                <span class="input-group-addon"><i></i></span>
            </div>
            <script>
                $(document).ready(function() {{
                    Coloris({{
                        el: '#{field.id}',
                        theme: 'default',
                        themeMode: 'light',
                        formatToggle: true,
                        clearButton: true,
                        swatches: [
                            '#264653',
                            '#2a9d8f',
                            '#e9c46a',
                            '#f4a261',
                            '#e76f51'
                        ]
                    }});
                }});
            </script>
        """
        return html

class CKEditorWidget(BaseCustomWidget):
    """Widget for rich text editing using CKEditor"""
    def render_field(self, field: Any, **kwargs) -> str:
        kwargs['type'] = 'textarea'
        html = f"""
            <textarea {html_params(**kwargs)}>{field.data or ''}</textarea>
            <script>
                $(document).ready(function() {{
                    ClassicEditor
                        .create(document.querySelector('#{field.id}'), {{
                            toolbar: [
                                'heading',
                                '|',
                                'bold',
                                'italic',
                                'link',
                                'bulletedList',
                                'numberedList',
                                '|',
                                'indent',
                                'outdent',
                                '|',
                                'imageUpload',
                                'blockQuote',
                                'insertTable',
                                'mediaEmbed',
                                'undo',
                                'redo'
                            ]
                        }})
                        .catch(error => {{
                            console.error(error);
                        }});
                }});
            </script>
        """
        return html

# Required JavaScript and CSS dependencies for the widgets
WIDGET_DEPENDENCIES = {
    'css': [
        'https://cdn.jsdelivr.net/npm/coloris@latest/dist/coloris.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.min.css',
    ],
    'js': [
        'https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js',
        'https://cdn.jsdelivr.net/npm/coloris@latest/dist/coloris.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.js',
        'https://cdn.ckeditor.com/ckeditor5/27.1.0/classic/ckeditor.js',
    ]
}

# Helper function to include widget dependencies in templates
def include_widget_dependencies() -> Dict[str, str]:
    """Generate HTML for including widget dependencies"""
    css_links = '\n'.join([
        f'<link rel="stylesheet" href="{css}">'
        for css in WIDGET_DEPENDENCIES['css']
    ])
    js_links = '\n'.join([
        f'<script src="{js}"></script>'
        for js in WIDGET_DEPENDENCIES['js']
    ])
    return {
        'css': css_links,
        'js': js_links
    }
