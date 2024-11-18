"""
nx_widgets.py: Extended Custom Widgets for Flask-AppBuilder

This file contains implementations of custom widgets designed to enhance
the functionality and user experience of Flask-AppBuilder applications.
Each widget is self-contained with embedded Jinja templates for easy integration.

Widgets Implemented:
1. RangeSliderWidget
2. TagInputWidget
3. JSONEditorWidget
4. MarkdownEditorWidget
5. GeoPointWidget
6. CurrencyInputWidget
7. PhoneNumberWidget
8. RatingWidget
9. DurationWidget
10. RelationshipGraphWidget
11. FileUploadFieldWidget
12. ColorPickerWidget
13. DateRangePickerWidget
14. RichTextEditorWidget
15. MultiSelectWidget
16. TimePickerWidget
17. CheckBoxWidget
18. SwitchWidget
19. StarRatingWidget
20. ToggleButtonWidget
21. SliderWidget
22. AutocompleteWidget
23. PasswordStrengthWidget

Author: Nyimbi Odero
Date: 2024-05-20
"""

from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_babel import lazy_gettext as _
import json
from markupsafe import Markup
from wtforms import Field
from wtforms.widgets import TextInput
from wtforms.validators import ValidationError
import re
from datetime import time, datetime

from wtforms.fields import (
    StringField, TextAreaField, IntegerField, FloatField, DecimalField, BooleanField,
    DateField, DateTimeField, TimeField, SelectField, SelectMultipleField, FileField,
    PasswordField
)

from wtforms import Field
from wtforms.widgets import TextInput
from wtforms.validators import ValidationError
import re
from datetime import time, datetime


class TimeField(Field):
    """
    A custom field for entering time.

    This field will accept input in various formats:
    - HH:MM
    - HH:MM:SS
    - HH:MM AM/PM
    - HH:MM:SS AM/PM

    It will store and return time as a Python time object.
    """

    widget = TextInput()

    def __init__(self, label=None, validators=None, format='%H:%M:%S', **kwargs):
        super(CustomTimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        elif self.data is not None:
            return self.data.strftime(self.format)
        else:
            return ''

    def process_formdata(self, valuelist):
        if valuelist:
            time_str = ' '.join(valuelist)
            try:
                self.data = self.parse_time(time_str)
            except ValueError as e:
                self.data = None
                raise ValidationError(str(e))
        else:
            self.data = None

    @staticmethod
    def parse_time(time_str):
        """Parse the time string into a time object."""
        time_str = time_str.lower().strip()

        # Try parsing with various formats
        formats = [
            '%H:%M',
            '%H:%M:%S',
            '%I:%M %p',
            '%I:%M:%S %p',
            '%H%M',
            '%H%M%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                pass

        # If no format matches, try a more flexible approach
        match = re.match(r'(\d{1,2}):?(\d{2})(:?(\d{2}))?\s*(am|pm)?', time_str)
        if match:
            hours, minutes, _, seconds, period = match.groups()
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds) if seconds else 0

            if period:
                if hours == 12:
                    hours = 0
                if period == 'pm':
                    hours += 12

            if 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59:
                return time(hours, minutes, seconds)

        raise ValueError('Invalid time format. Please use HH:MM, HH:MM:SS, or HH:MM AM/PM.')

    def pre_validate(self, form):
        if self.data is None:
            raise ValidationError('Not a valid time value')

    def isoformat(self):
        """Return the time in ISO 8601 format."""
        if self.data:
            return self.data.isoformat()
        return None

    def to_12_hour(self):
        """Return the time in 12-hour format."""
        if self.data:
            return self.data.strftime('%I:%M:%S %p')
        return None

    def to_24_hour(self):
        """Return the time in 24-hour format."""
        if self.data:
            return self.data.strftime('%H:%M:%S')
        return None

class TimePickerWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="input-group">'
        '<span class="input-group-addon"><i class="fa fa-clock-o"></i></span>'
        '<input %(text)s>'
        '</div>'
    )
    empty_template = (
        '<div class="input-group">'
        '<span class="input-group-addon"><i class="fa fa-clock-o"></i></span>'
        '<input %(text)s>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs["type"] = "time"
        kwargs.setdefault("data-role", "timepicker")
        kwargs.setdefault("data-template", "dropdown")
        kwargs.setdefault("data-show-seconds", "true")
        kwargs.setdefault("data-default-time", "false")
        kwargs.setdefault("data-show-meridian", "false")
        kwargs.setdefault("data-minute-step", 1)

        if field.flags.required:
            kwargs["required"] = True

        template = self.data_template if field.data else self.empty_template
        return Markup(
            template % {"text": self.html_params(name=field.name, **kwargs)}
        )

class RangeSliderWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="range-slider">'
        '<input %(text)s>'
        '<div id="%(field_id)s-slider"></div>'
        '</div>'
    )
    empty_template = (
        '<div class="range-slider">'
        '<input %(text)s>'
        '<div id="%(field_id)s-slider"></div>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")
        kwargs.setdefault("data-slider-min", field.min)
        kwargs.setdefault("data-slider-max", field.max)
        kwargs.setdefault("data-slider-step", field.step)
        kwargs.setdefault(
            "data-slider-value",
            f"[{field.data[0]},{field.data[1]}]" if field.data else "[0,100]",
        )
        kwargs.setdefault("data-slider-tooltip", "always")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "text": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            $('#{field_id}-slider').slider({{
                min: {min},
                max: {max},
                step: {step},
                value: {value},
                tooltip: 'always',
                tooltip_split: true
            }}).on('slideStop', function(ev) {{
                $('#{field_id}').val(ev.value[0] + ',' + ev.value[1]);
            }});
        </script>
        """.format(
            field_id=field.id,
            min=field.min,
            max=field.max,
            step=field.step,
            value=f"[{field.data[0]},{field.data[1]}]" if field.data else "[0,100]"
        ))

class TagInputWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(text)s>'
    )
    empty_template = (
        '<input %(text)s>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")
        kwargs.setdefault("data-role", "tagsinput")

        template = self.data_template if field.data else self.empty_template
        html = template % {"text": self.html_params(name=field.name, **kwargs)}

        return Markup(html + """
        <script>
            $('#{field_id}').tagsinput({{
                trimValue: true,
                confirmKeys: [13, 44],
                tagClass: 'label label-primary'
            }});
        </script>
        """.format(field_id=field.id))

class JSONEditorWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor" style="height: 400px;"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor" style="height: 400px;"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            var editor = ace.edit("{field_id}-editor");
            editor.setTheme("ace/theme/monokai");
            editor.session.setMode("ace/mode/json");
            editor.setValue({json_data});
            editor.on('change', function() {{
                $('#{field_id}').val(editor.getValue());
            }});
        </script>
        """.format(
            field_id=field.id,
            json_data=json.dumps(field.data or {})
        ))

class MarkdownEditorWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            var easyMDE = new EasyMDE({{
                element: document.getElementById('{field_id}-editor'),
                initialValue: {initial_value},
                spellChecker: false,
                renderingConfig: {{
                    singleLineBreaks: false,
                    codeSyntaxHighlighting: true,
                }}
            }});
            easyMDE.codemirror.on("change", function() {{
                $('#{field_id}').val(easyMDE.value());
            }});
        </script>
        """.format(
            field_id=field.id,
            initial_value=json.dumps(field.data or '')
        ))

class GeoPointWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-map" style="height: 400px;"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-map" style="height: 400px;"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            var map = L.map('{field_id}-map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
            var marker;
            map.on('click', function(e) {{
                if (marker) {{
                    map.removeLayer(marker);
                }}
                marker = L.marker(e.latlng).addTo(map);
                $('#{field_id}').val(e.latlng.lat + ',' + e.latlng.lng);
            }});
        </script>
        """.format(field_id=field.id))

class CurrencyInputWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="input-group">'
        '<span class="input-group-addon">%(currency)s</span>'
        '<input %(text)s>'
        '</div>'
    )
    empty_template = (
        '<div class="input-group">'
        '<span class="input-group-addon">%(currency)s</span>'
        '<input %(text)s>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")
        kwargs.setdefault("data-currency", field.currency)

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "text": self.html_params(name=field.name, **kwargs),
            "currency": field.currency
        }

        return Markup(html + """
        <script>
            $('#{field_id}').maskMoney({{
                prefix: '{currency}',
                thousands: ',',
                decimal: '.',
                allowZero: true,
                allowNegative: false
            }});
        </script>
        """.format(field_id=field.id, currency=field.currency))

class PhoneNumberWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(text)s>'
    )
    empty_template = (
        '<input %(text)s>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "tel")

        template = self.data_template if field.data else self.empty_template
        html = template % {"text": self.html_params(name=field.name, **kwargs)}

        return Markup(html + """
        <script>
            $('#{field_id}').intlTelInput({{
                utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
                separateDialCode: true,
                nationalMode: false,
                autoPlaceholder: 'aggressive'
            }});
        </script>
        """.format(field_id=field.id))

class RatingWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-stars"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-stars"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            $('#{field_id}-stars').raty({{
                score: {score},
                half: true,
                click: function(score, evt) {{
                    $('#{field_id}').val(score);
                }}
            }});
        </script>
        """.format(field_id=field.id, score=field.data or 0))

class DurationWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(text)s>'
    )
    empty_template = (
        '<input %(text)s>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")

        template = self.data_template if field.data else self.empty_template
        html = template % {"text": self.html_params(name=field.name, **kwargs)}

        return Markup(html + """
        <script>
            $('#{field_id}').durationPicker({{
                showSeconds: true,
                showDays: false
            }}).on('change', function() {{
                var totalSeconds = $(this).data('durationPicker').totalSeconds();
                $('#{field_id}').val(totalSeconds);
            }});
        </script>
        """.format(field_id=field.id))

class RelationshipGraphWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-graph" style="height: 600px;"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-graph" style="height: 600px;"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            var nodes = new vis.DataSet({nodes});
            var edges = new vis.DataSet({edges});
            var container = document.getElementById('{field_id}-graph');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            var options = {{}};
            var network = new vis.Network(container, data, options);
            network.on("afterDrawing", function (ctx) {{
                var graphData = {{
                    nodes: nodes.get(),
                    edges: edges.get()
                }};
                $('#{field_id}').val(JSON.stringify(graphData));
            }});
        </script>
        """.format(
            field_id=field.id,
            nodes=json.dumps(field.nodes),
            edges=json.dumps(field.edges)
        ))

class ColorPickerWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="input-group color-picker-widget">'
        '<input %(text)s>'
        '<span class="input-group-addon"><i></i></span>'
        '</div>'
    )
    empty_template = (
        '<div class="input-group color-picker-widget">'
        '<input %(text)s>'
        '<span class="input-group-addon"><i></i></span>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")

        template = self.data_template if field.data else self.empty_template
        html = template % {"text": self.html_params(name=field.name, **kwargs)}

        return Markup(html + """
        <script>
            $('#{field_id}').colorpicker({{
                format: 'hex'
            }});
        </script>
        """.format(field_id=field.id))

class DateRangePickerWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="input-group date-range-picker-widget">'
        '<input %(text)s>'
        '<span class="input-group-addon"><i class="fa fa-calendar"></i></span>'
        '</div>'
    )
    empty_template = (
        '<div class="input-group date-range-picker-widget">'
        '<input %(text)s>'
        '<span class="input-group-addon"><i class="fa fa-calendar"></i></span>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "text")

        template = self.data_template if field.data else self.empty_template
        html = template % {"text": self.html_params(name=field.name, **kwargs)}

        return Markup(html + """
        <script>
            $('#{field_id}').daterangepicker({{
                startDate: moment().subtract(29, 'days'),
                endDate: moment(),
                ranges: {{
                   'Today': [moment(), moment()],
                   'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                   'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                   'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                   'This Month': [moment().startOf('month'), moment().endOf('month')],
                   'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
                }}
            }}, function(start, end, label) {{
                console.log("A new date selection was made: " + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'));
            }});
        </script>
        """.format(field_id=field.id))

class RichTextEditorWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-editor"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            var quill = new Quill('#{field_id}-editor', {{
                theme: 'snow',
                modules: {{
                    toolbar: [
                        [{{ 'header': [1, 2, 3, false] }}],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{{ 'list': 'ordered' }}, {{ 'list': 'bullet' }}],
                        ['link', 'image', 'code-block'],
                        [{{ 'color': [] }}, {{ 'background': [] }}],
                        [{{ 'align': [] }}]
                    ]
                }}
            }});
            quill.on('text-change', function() {{
                $('#{field_id}').val(JSON.stringify(quill.getContents()));
            }});
            quill.setContents({json_data});
        </script>
        """.format(
            field_id=field.id,
            json_data=json.dumps(field.data) if field.data else 'null'
        ))

class MultiSelectWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<select id="%(field_id)s-select" multiple="multiple" style="width: 100%;">'
        '%(options)s'
        '</select>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<select id="%(field_id)s-select" multiple="multiple" style="width: 100%;">'
        '%(options)s'
        '</select>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")
        kwargs.setdefault("multiple", "multiple")

        options = ''.join([f'<option value="{option[0]}">{option[1]}</option>' for option in field.choices])

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id,
            "options": options
        }

        return Markup(html + """
        <script>
            $('#{field_id}-select').select2({{
                data: {options},
                placeholder: 'Select options',
                allowClear: true,
                closeOnSelect: false
            }}).on('change', function() {{
                $('#{field_id}').val(JSON.stringify($(this).val()));
            }});
            $('#{field_id}-select').val({initial_value}).trigger('change');
        </script>
        """.format(
            field_id=field.id,
            options=json.dumps([{"id": option[0], "text": option[1]} for option in field.choices]),
            initial_value=json.dumps(field.data) if field.data else '[]'
        ))

class FileUploadFieldWidget(BS3TextFieldWidget):
    data_template = (
        '<div class="file-upload-widget">'
        '<input %(file)s>'
        '<div id="%(field_id)s-preview"></div>'
        '</div>'
    )
    empty_template = (
        '<div class="file-upload-widget">'
        '<input %(file)s>'
        '<div id="%(field_id)s-preview"></div>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "file")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "file": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            $('#{field_id}').on('change', function(e) {{
                var file = e.target.files[0];
                var reader = new FileReader();
                reader.onload = function(e) {{
                    var preview = $('#{field_id}-preview');
                    preview.empty();
                    if (file.type.startsWith('image/')) {{
                        preview.html('<img src="' + e.target.result + '" style="max-width: 100%; max-height: 200px;">');
                    }} else {{
                        preview.text(file.name);
                    }}
                }};
                reader.readAsDataURL(file);
            }});
        </script>
        """.format(field_id=field.id))


class CheckBoxWidget(object):
    data_template = (
        '<div class="checkbox">'
        '<label>'
        '<input %(checkbox)s> %(label)s'
        '</label>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if field.checked:
            kwargs['checked'] = 'checked'
        return Markup(self.data_template % {
            'checkbox': self.html_params(name=field.name, **kwargs),
            'label': field.label.text
        })

class SwitchWidget(object):
    data_template = (
        '<div class="custom-control custom-switch">'
        '<input type="checkbox" class="custom-control-input" %(checkbox)s>'
        '<label class="custom-control-label" for="%(field_id)s">%(label)s</label>'
        '</div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if field.checked:
            kwargs['checked'] = 'checked'
        return Markup(self.data_template % {
            'checkbox': self.html_params(name=field.name, **kwargs),
            'field_id': field.id,
            'label': field.label.text
        })

class StarRatingWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-stars" class="star-rating"></div>'
    )
    empty_template = (
        '<input %(hidden)s>'
        '<div id="%(field_id)s-stars" class="star-rating"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "hidden")

        template = self.data_template if field.data else self.empty_template
        html = template % {
            "hidden": self.html_params(name=field.name, **kwargs),
            "field_id": field.id
        }

        return Markup(html + """
        <script>
            $('#{field_id}-stars').starRating({{
                initialRating: {initial_rating},
                starSize: 25,
                callback: function(currentRating, $el){{
                    $('#{field_id}').val(currentRating);
                }}
            }});
        </script>
        """.format(field_id=field.id, initial_rating=field.data or 0))

class ToggleButtonWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(checkbox)s>'
        '<label for="%(field_id)s" class="btn btn-primary">%(label)s</label>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'checkbox')
        if field.checked:
            kwargs['checked'] = 'checked'
        return Markup(self.data_template % {
            'checkbox': self.html_params(name=field.name, **kwargs),
            'field_id': field.id,
            'label': field.label.text
        })

class SliderWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(range)s>'
        '<output for="%(field_id)s" id="%(field_id)s-output"></output>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'range')
        kwargs.setdefault('min', field.min)
        kwargs.setdefault('max', field.max)
        kwargs.setdefault('step', field.step)
        kwargs.setdefault('value', field.data or field.min)

        html = self.data_template % {
            'range': self.html_params(name=field.name, **kwargs),
            'field_id': field.id
        }

        return Markup(html + """
        <script>
            var slider = document.getElementById('{field_id}');
            var output = document.getElementById('{field_id}-output');
            output.innerHTML = slider.value;
            slider.oninput = function() {{
                output.innerHTML = this.value;
            }}
        </script>
        """.format(field_id=field.id))

class AutocompleteWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(text)s>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'text')

        html = self.data_template % {
            'text': self.html_params(name=field.name, **kwargs)
        }

        return Markup(html + """
        <script>
            $('#{field_id}').autocomplete({{
                source: {source},
                minLength: 2
            }});
        </script>
        """.format(field_id=field.id, source=json.dumps(field.choices)))

class PasswordStrengthWidget(BS3TextFieldWidget):
    data_template = (
        '<input %(password)s>'
        '<div id="%(field_id)s-strength" class="password-strength"></div>'
    )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'password')

        html = self.data_template % {
            'password': self.html_params(name=field.name, **kwargs),
            'field_id': field.id
        }

        return Markup(html + """
        <script>
            $('#{field_id}').on('input', function() {{
                var password = $(this).val();
                var strength = 0;
                if (password.length > 7) strength++;
                if (password.match(/[a-z]+/)) strength++;
                if (password.match(/[A-Z]+/)) strength++;
                if (password.match(/[0-9]+/)) strength++;
                if (password.match(/[$@#&!]+/)) strength++;

                var strengthBar = $('#{field_id}-strength');
                strengthBar.removeClass('weak medium strong very-strong');
                if (strength < 2) {{
                    strengthBar.addClass('weak').text('Weak');
                }} else if (strength < 3) {{
                    strengthBar.addClass('medium').text('Medium');
                }} else if (strength < 5) {{
                    strengthBar.addClass('strong').text('Strong');
                }} else {{
                    strengthBar.addClass('very-strong').text('Very Strong');
                }}
            }});
        </script>
        """.format(field_id=field.id))

"""
Usage Examples:

from .nx_widgets import (
    RangeSliderWidget, TagInputWidget, JSONEditorWidget, MarkdownEditorWidget,
    GeoPointWidget, CurrencyInputWidget, PhoneNumberWidget, RatingWidget,
    DurationWidget, RelationshipGraphWidget, FileUploadFieldWidget,
    ColorPickerWidget, DateRangePickerWidget, RichTextEditorWidget,
    MultiSelectWidget, CheckBoxWidget
)

class MyForm(DynamicForm):
    price_range = StringField('Price Range', widget=RangeSliderWidget())
    tags = StringField('Tags', widget=TagInputWidget())
    config = StringField('Configuration', widget=JSONEditorWidget())
    description = TextAreaField('Description', widget=MarkdownEditorWidget())
    location = StringField('Location', widget=GeoPointWidget())
    price = DecimalField('Price', widget=CurrencyInputWidget())
    phone = StringField('Phone', widget=PhoneNumberWidget())
    rating = FloatField('Rating', widget=RatingWidget())
    duration = IntegerField('Duration', widget=DurationWidget())
    relationships = StringField('Relationships', widget=RelationshipGraphWidget())
    file = FileField('File', widget=FileUploadFieldWidget())
    color = StringField('Color', widget=ColorPickerWidget())
    date_range = StringField('Date Range', widget=DateRangePickerWidget())
    content = TextAreaField('Content', widget=RichTextEditorWidget())
    agree_terms = BooleanField('I agree to the terms', widget=CheckBoxWidget())
    notifications = BooleanField('Enable notifications', widget=SwitchWidget())
    rating = FloatField('Rate this', widget=StarRatingWidget())
    toggle_feature = BooleanField('Enable feature', widget=ToggleButtonWidget())
    volume = IntegerField('Volume', widget=SliderWidget())
    country = StringField('Country', widget=AutocompleteWidget())
    password = PasswordField('Password', widget=PasswordStrengthWidget())
    categories = SelectMultipleField('Categories', widget=MultiSelectWidget(), choices=[
        ('1', 'Category 1'),
        ('2', 'Category 2'),
        ('3', 'Category 3')
    ])

class MyModelView(ModelView):
    datamodel = SQLAInterface(MyModel)
    form = MyForm

appbuilder.add_view(MyModelView, "My Model", icon="fa-folder-open-o", category="My Category")

Note: Remember to include the necessary CSS and JavaScript files in your base template
for these widgets to function properly. You may need to adjust the CDN links or
host the files locally depending on your project's requirements.
"""
