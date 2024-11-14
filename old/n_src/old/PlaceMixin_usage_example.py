## PlaceMixin Usage Example
# views.py

from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import request, jsonify
from .models import MyPlace
from . import appbuilder, db

class MyPlaceView(ModelView):
    datamodel = SQLAInterface(MyPlace)
    list_columns = ['name', 'place_name', 'latitude', 'longitude', 'country.name']
    show_columns = ['name', 'place_name', 'latitude', 'longitude', 'country.name', 'admin1_code', 'admin2_code', 'feature_code', 'timezone']
    edit_columns = ['name', 'place_name', 'latitude', 'longitude']
    add_columns = ['name', 'place_name', 'latitude', 'longitude']
    search_columns = ['name', 'place_name', 'country.name', 'admin1_code', 'admin2_code']

    @expose('/map/<int:pk>')
    def show_map(self, pk):
        place = self.datamodel.get(pk)
        if place:
            map_html = place.generate_leaflet_map()
            return self.render_template('place_map.html', map_html=map_html, place=place)
        else:
            flash("Place not found", "danger")
            return redirect(url_for(f"{self.__class__.__name__}.list"))

class PlaceUtilsView(BaseView):
    default_view = 'geocode'

    @expose('/geocode', methods=['GET', 'POST'])
    def geocode(self):
        if request.method == 'POST':
            address = request.form.get('address')
            place = MyPlace()
            result = place.geocode(db.session, address)
            if result:
                return self.render_template('geocode_result.html', place=result)
            else:
                flash("Geocoding failed", "danger")
        return self.render_template('geocode_form.html')

    @expose('/reverse_geocode', methods=['GET', 'POST'])
    def reverse_geocode(self):
        if request.method == 'POST':
            lat = float(request.form.get('latitude'))
            lon = float(request.form.get('longitude'))
            place = MyPlace()
            result = place.reverse_geocode(db.session, lat, lon)
            if result:
                return self.render_template('geocode_result.html', place=result)
            else:
                flash("Reverse geocoding failed", "danger")
        return self.render_template('reverse_geocode_form.html')

    @expose('/distance', methods=['GET', 'POST'])
    def calculate_distance(self):
        if request.method == 'POST':
            place1_id = int(request.form.get('place1'))
            place2_id = int(request.form.get('place2'))
            place1 = db.session.query(MyPlace).get(place1_id)
            place2 = db.session.query(MyPlace).get(place2_id)
            if place1 and place2:
                distance = place1.distance_to(place2)
                return self.render_template('distance_result.html', place1=place1, place2=place2, distance=distance)
            else:
                flash("One or both places not found", "danger")
        places = db.session.query(MyPlace).all()
        return self.render_template('distance_form.html', places=places)

    @expose('/nearby/<int:pk>')
    def nearby_places(self, pk):
        place = db.session.query(MyPlace).get(pk)
        if place:
            nearby = place.get_nearby_places(db.session, radius_km=50, limit=10)
            return self.render_template('nearby_places.html', place=place, nearby=nearby)
        else:
            flash("Place not found", "danger")
            return redirect(url_for(f"{self.__class__.__name__}.list"))

# Add views to AppBuilder
appbuilder.add_view(MyPlaceView, "Places", icon="fa-globe", category="Locations")
appbuilder.add_view(PlaceUtilsView, "Geocoding", icon="fa-search", category="Utilities")
appbuilder.add_link("Calculate Distance", href="/placeutilsview/distance", icon="fa-calculator", category="Utilities")

# forms.py
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import StringField, FloatField
from wtforms.validators import DataRequired

class GeocodeForm(DynamicForm):
    address = StringField("Address", validators=[DataRequired()], widget=BS3TextFieldWidget())

class ReverseGeocodeForm(DynamicForm):
    latitude = FloatField("Latitude", validators=[DataRequired()], widget=BS3TextFieldWidget())
    longitude = FloatField("Longitude", validators=[DataRequired()], widget=BS3TextFieldWidget())

# templates/place_map.html
{% extends "appbuilder/base.html" %}

{% block content %}
<h1>{{ place.place_name }} Map</h1>
{{ map_html | safe }}
{% endblock %}

# templates/geocode_form.html
{% extends "appbuilder/base.html" %}
{% import "appbuilder/general/lib.html" as lib %}

{% block content %}
<h1>Geocode Address</h1>
<form method="post">
    {{ lib.render_field(form.address) }}
    <input type="submit" value="Geocode" class="btn btn-primary">
</form>
{% endblock %}

# templates/reverse_geocode_form.html
{% extends "appbuilder/base.html" %}
{% import "appbuilder/general/lib.html" as lib %}

{% block content %}
<h1>Reverse Geocode Coordinates</h1>
<form method="post">
    {{ lib.render_field(form.latitude) }}
    {{ lib.render_field(form.longitude) }}
    <input type="submit" value="Reverse Geocode" class="btn btn-primary">
</form>
{% endblock %}

# templates/geocode_result.html
{% extends "appbuilder/base.html" %}

{% block content %}
<h1>Geocoding Result</h1>
<p><strong>Name:</strong> {{ place.place_name }}</p>
<p><strong>Latitude:</strong> {{ place.latitude }}</p>
<p><strong>Longitude:</strong> {{ place.longitude }}</p>
<p><strong>Country:</strong> {{ place.country.name if place.country else 'N/A' }}</p>
<p><strong>Admin1:</strong> {{ place.admin1_code or 'N/A' }}</p>
<p><strong>Admin2:</strong> {{ place.admin2_code or 'N/A' }}</p>
{{ place.generate_leaflet_map() | safe }}
{% endblock %}

# templates/distance_form.html
{% extends "appbuilder/base.html" %}

{% block content %}
<h1>Calculate Distance</h1>
<form method="post">
    <div class="form-group">
        <label for="place1">From:</label>
        <select name="place1" class="form-control">
            {% for place in places %}
            <option value="{{ place.id }}">{{ place.place_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="form-group">
        <label for="place2">To:</label>
        <select name="place2" class="form-control">
            {% for place in places %}
            <option value="{{ place.id }}">{{ place.place_name }}</option>
            {% endfor %}
        </select>
    </div>
    <input type="submit" value="Calculate Distance" class="btn btn-primary">
</form>
{% endblock %}

# templates/distance_result.html
{% extends "appbuilder/base.html" %}

{% block content %}
<h1>Distance Result</h1>
<p>Distance between {{ place1.place_name }} and {{ place2.place_name }} is {{ distance|round(2) }} km.</p>
{{ place1.generate_leaflet_route_map(place2) | safe }}
{% endblock %}

# templates/nearby_places.html
{% extends "appbuilder/base.html" %}

{% block content %}
<h1>Nearby Places to {{ place.place_name }}</h1>
<ul>
{% for nearby_place in nearby %}
    <li>{{ nearby_place.place_name }} ({{ place.distance_to(nearby_place)|round(2) }} km)</li>
{% endfor %}
</ul>
{{ PlaceMixin.generate_multiple_pins_map([place] + nearby) | safe }}
{% endblock %}

# Example usage in a script or interactive session:
with app.app_context():
    # Create a new place
    new_york = MyPlace(name="New York City")
    new_york.geocode(db.session, "New York City, USA")
    db.session.add(new_york)
    db.session.commit()

    # Find nearby places
    nearby = new_york.get_nearby_places(db.session, radius_km=100, limit=5)
    for place in nearby:
        print(f"Nearby: {place.place_name}, Distance: {new_york.distance_to(place):.2f} km")

    # Get timezone
    timezone = new_york.get_timezone(db.session)
    print(f"Timezone: {timezone}")

    # Get local time
    local_time = new_york.get_local_time()
    print(f"Local time: {local_time}")

    # Get sun position
    sun_position = new_york.get_sun_position()
    print(f"Sun position: Altitude: {sun_position['altitude']:.2f}°, Azimuth: {sun_position['azimuth']:.2f}°")

    # Convert to geohash
    geohash = new_york.to_geohash()
    print(f"Geohash: {geohash}")

    # Format coordinates
    formatted_coords = new_york.format_coordinates('dms')
    print(f"Formatted coordinates: {formatted_coords}")

    # Calculate area of the country
    country_area = new_york.calculate_area(db.session, 'country')
    print(f"Country area: {country_area:.2f} km²")

    # Get population
    population = new_york.get_population(db.session)
    print(f"Population: {population}")

    # Convert to GeoJSON
    geojson = new_york.to_geojson()
    print(f"GeoJSON: {json.dumps(geojson, indent=2)}")

    # Save to KML
    new_york.save_to_kml("new_york.kml")
    print("Saved to KML file: new_york.kml")

    # Create a Folium map
    folium_map = new_york.to_folium_map()
    folium_map.save("new_york_map.html")
    print("Saved Folium map to: new_york_map.html")

# This comprehensive example demonstrates how to integrate the PlaceMixin into a Flask-AppBuilder application,
# including views, forms, and templates. It also shows how to use various methods of the PlaceMixin in a script
# or interactive session.
