import os
import math
import json
import requests
from sqlalchemy import Column, String, Text, Float, Boolean
from geoalchemy2 import Geometry
from functools import lru_cache
from collections import namedtuple
from geopy.distance import great_circle as gc_distance, geodesic # vincenty as vin_distance


class PlaceMixin:
    """
    A mixin for Flask-AppBuilder models that provides geographical information,
    including coordinates, mapping details, and optional routing capabilities using OSRM.

    Features:
    - Latitude, longitude, altitude, and geometric data storage.
    - Integration with Leaflet and OpenLayers for map rendering.
    - Optional routing functionality via OSRM.
    - Methods to generate Leaflet and OpenLayers maps, including markers, routes, and more.
    - Display of multiple pins for a selection of table rows.
    - Plotting of the shortest route between selected locations.
    - Export capabilities for GeoJSON and KML formats.
    - Validation for latitude and longitude.
    - Write out Jinja2 templates and examples for Flask views.
    - Estimate travel time between locations.

    Usage:
    - OSRM integration is optional. If used, an OSRM server must be set up, and the
      base URL provided to relevant methods.
    - Leaflet and OpenLayers are used for map rendering. The generated maps can be
      embedded in Flask templates using the provided methods.
    """

    # Core geographic attributes
    place_name = Column(String(40))
    place_description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    geometry = Column(Geometry(geometry_type='POINT', srid=4326))
    map = Column(Text, default="")
    info = Column(Text, default="")
    pin = Column(Boolean)  # Do we put a pin
    pin_color = Column(String(20))
    pin_icon = Column(String(50))
    centered = Column(Boolean)
    nearest_feature = Column(String(100))
    crs = Column(String(20), default="EPSG:4326")

    def __repr__(self):
        return self.place_name

    def validate_latitude(self, latitude):
        if latitude < -90 or latitude > 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')

    def validate_longitude(self, longitude):
        if longitude < -180 or longitude > 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')

    def validate(self):
        self.validate_latitude(self.latitude)
        self.validate_longitude(self.longitude)

    def save_to_geojson(self):
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "place_name": self.place_name,
                "place_description": self.place_description,
                "altitude": self.altitude,
                "info": self.info
            }
        }
        return json.dumps(geojson)

    def save_to_kml(self):
        kml = f"""
        <Placemark>
            <name>{self.place_name}</name>
            <description>{self.place_description}</description>
            <Point>
                <coordinates>{self.longitude},{self.latitude},{self.altitude}</coordinates>
            </Point>
        </Placemark>
        """
        return kml.strip()

    @classmethod
    def bulk_import_geojson(cls, geojson_data):
        features = json.loads(geojson_data)['features']
        instances = []
        for feature in features:
            geom = feature['geometry']
            props = feature['properties']
            instance = cls(
                latitude=geom['coordinates'][1],
                longitude=geom['coordinates'][0],
                place_name=props.get('place_name', ''),
                place_description=props.get('place_description', ''),
                altitude=props.get('altitude', 0),
                info=props.get('info', '')
            )
            instances.append(instance)
        return instances

    @classmethod
    def find_closest_instance(cls, latitude, longitude):
        instances = cls.query.all()
        closest_instance = None
        closest_distance = float('inf')
        for instance in instances:
            distance = cls.haversine(latitude, longitude, instance.latitude, instance.longitude)
            if distance < closest_distance:
                closest_distance = distance
                closest_instance = instance
        return closest_instance

    @classmethod
    def find_closest_instances(cls, latitude, longitude, n=1, method='haversine'):
        """
        Find the `n` closest instances to a given latitude and longitude using a specified distance calculation method.

        Parameters:
            latitude (float): The latitude to compare.
            longitude (float): The longitude to compare.
            n (int): The number of closest instances to return.
            method (str): The distance calculation method ('haversine', 'geodesic', 'great_circle', 'euclidean').

        Returns:
            list: The `n` closest PlaceMixin instances.
        """
        instances = cls.query.all()
        distances = []

        for instance in instances:
            distance = None
            if method == 'haversine':
                distance = cls.haversine(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'geodesic':
                distance = cls.geodesic(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'great_circle':
                distance = cls.great_circle(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'euclidean':
                distance = cls.euclidean(latitude, longitude, instance.latitude, instance.longitude)
            distances.append((instance, distance))

        # Sort by distance and return the top `n` instances
        distances.sort(key=lambda x: x[1])
        return [d[0] for d in distances[:n]]

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(
            math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        h_distance = R * c  # Distance in km
        return h_distance

    # @staticmethod
    # def vincenty(lat1, lon1, lat2, lon2):
    #     """
    #     Calculate the Vincenty distance between two points on the Earth's surface.
    #     Uses the WGS-84 ellipsoid model of the Earth.
    #     """
    #     return vin_distance((lat1, lon1), (lat2, lon2)).kilometers


    @staticmethod
    def geodesic(lat1, lon1, lat2, lon2):
        """
        Calculate the Geodesic distance (Geodesic method) between two points on the Earth's surface.
        Uses the WGS-84 ellipsoid model of the Earth.
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def great_circle(lat1, lon1, lat2, lon2):
        """
        Calculate the Great Circle distance between two points on the Earth's surface.
        This method is faster than Vincenty but less accurate.
        """
        return gc_distance((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def euclidean(lat1, lon1, lat2, lon2):
        """
        Calculate the Euclidean distance between two points.
        Note: This method does not account for the curvature of the Earth and is less accurate for long distances.
        """
        dLat = lat2 - lat1
        dLon = lon2 - lon1
        return math.sqrt(dLat * dLat + dLon * dLon)


    def generate_leaflet_map(self, zoom=13, marker=True, custom_marker_url=None):
        """
        Generate HTML and JavaScript for a Leaflet map centered on this place.

        Parameters:
            zoom (int): The zoom level for the map.
            marker (bool): Whether to place a marker on the map at the location.
            custom_marker_url (str): URL of a custom marker icon.

        Returns:
            str: HTML and JavaScript code for embedding the Leaflet map.
        """
        leaflet_map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script>
            var map = L.map('map').setView([{self.latitude}, {self.longitude}], {zoom});
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
        """

        if marker:
            if custom_marker_url:
                leaflet_map_script += f"""
                var customIcon = L.icon({{
                    iconUrl: '{custom_marker_url}',
                    iconSize: [38, 38],
                    iconAnchor: [22, 94],
                    popupAnchor: [-3, -76],
                }});
                var marker = L.marker([{self.latitude}, {self.longitude}], {{icon: customIcon}}).addTo(map);
                """
            else:
                leaflet_map_script += f"""
                var marker = L.marker([{self.latitude}, {self.longitude}]).addTo(map);
                """

            leaflet_map_script += f"""
            marker.bindPopup("<b>{self.place_name}</b><br>{self.place_description}").openPopup();
            """

        leaflet_map_script += "</script>"
        return leaflet_map_script

    def generate_leaflet_route_map(self, destination, osrm_base_url="http://localhost:5000", zoom=13):
        """
        Generate a Leaflet map showing the route from this place to the destination using OSRM.

        Parameters:
            destination (PlaceMixin): The destination instance.
            osrm_base_url (str): The base URL of the OSRM server.
            zoom (int): The zoom level for the map.

        Returns:
            str: HTML and JavaScript code for embedding the Leaflet map with the route.
        """
        route = self.calculate_route(destination, osrm_base_url=osrm_base_url)

        leaflet_map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script>
            var map = L.map('map').setView([{self.latitude}, {self.longitude}], {zoom});
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
        """

        leaflet_map_script += f"""
        var startMarker = L.marker([{self.latitude}, {self.longitude}]).addTo(map);
        startMarker.bindPopup("<b>Start: {self.place_name}</b><br>{self.place_description}").openPopup();
        var endMarker = L.marker([{destination.latitude}, {destination.longitude}]).addTo(map);
        endMarker.bindPopup("<b>Destination: {destination.place_name}</b><br>{destination.place_description}").openPopup();
        """

        if route:
            leaflet_map_script += """
            var routeCoordinates = ["""
            leaflet_map_script += ",".join([f"[{lon},{lat}]" for lon, lat in route])
            leaflet_map_script += """];
            var routePolyline = L.polyline(routeCoordinates, {color: 'blue'}).addTo(map);
            map.fitBounds(routePolyline.getBounds());
            """

        leaflet_map_script += "</script>"
        return leaflet_map_script

    def generate_openlayers_map(self, zoom=13, marker=True):
        """
        Generate HTML and JavaScript for an OpenLayers map centered on this place.

        Parameters:
            zoom (int): The zoom level for the map.
            marker (bool): Whether to place a marker on the map at the location.

        Returns:
            str: HTML and JavaScript code for embedding the OpenLayers map.
        """
        openlayers_map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script src="https://openlayers.org/en/v4.6.5/build/ol.js" type="text/javascript"></script>
        <script type="text/javascript">
            var map = new ol.Map({{
                target: 'map',
                layers: [
                    new ol.layer.Tile({{
                        source: new ol.source.OSM()
                    }})
                ],
                view: new ol.View({{
                    center: ol.proj.fromLonLat([{self.longitude}, {self.latitude}]),
                    zoom: {zoom}
                }})
            }});
        """

        if marker:
            openlayers_map_script += f"""
            var marker = new ol.Overlay({{
                position: ol.proj.fromLonLat([{self.longitude}, {self.latitude}]),
                positioning: 'center-center',
                element: document.createElement('div'),
                stopEvent: false
            }});
            marker.getElement().innerHTML = "<div style='background: red; width: 10px; height: 10px; border-radius: 50%;'></div>";
            map.addOverlay(marker);
            """

        openlayers_map_script += "</script>"
        return openlayers_map_script

    def generate_openlayers_route_map(self, destination, osrm_base_url="http://localhost:5000", zoom=13):
        """
        Generate an OpenLayers map showing the route from this place to the destination using OSRM.

        Parameters:
            destination (PlaceMixin): The destination instance.
            osrm_base_url (str): The base URL of the OSRM server.
            zoom (int): The zoom level for the map.

        Returns:
            str: HTML and JavaScript code for embedding the OpenLayers map with the route.
        """
        route = self.calculate_route(destination, osrm_base_url=osrm_base_url)

        openlayers_map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script src="https://openlayers.org/en/v4.6.5/build/ol.js" type="text/javascript"></script>
        <script type="text/javascript">
            var map = new ol.Map({{
                target: 'map',
                layers: [
                    new ol.layer.Tile({{
                        source: new ol.source.OSM()
                    }})
                ],
                view: new ol.View({{
                    center: ol.proj.fromLonLat([{self.longitude}, {self.latitude}]),
                    zoom: {zoom}
                }})
            }});
        """

        if route:
            openlayers_map_script += """
            var routeCoordinates = ["""
            openlayers_map_script += ",".join([f"ol.proj.fromLonLat([{lon},{lat}])" for lon, lat in route])
            openlayers_map_script += """];
            var routeFeature = new ol.Feature({{
                geometry: new ol.geom.LineString(routeCoordinates)
            }});
            var routeLayer = new ol.layer.Vector({{
                source: new ol.source.Vector({
                    features: [routeFeature]
                }),
                style: new ol.style.Style({{
                    stroke: new ol.style.Stroke({{
                        color: 'blue',
                        width: 3
                    }})
                }})
            }});
            map.addLayer(routeLayer);
            map.getView().fit(routeLayer.getSource().getExtent(), {{ duration: 1000 }});
            """

        openlayers_map_script += "</script>"
        return openlayers_map_script

    def calculate_route(self, destination, osrm_base_url="http://localhost:5000"):
        """
        Calculate a route from the current location to the destination using OSRM.

        Parameters:
            destination (PlaceMixin): The destination instance.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            list: A list of coordinates representing the route, or None if the route could not be calculated.
        """
        start_coords = f"{self.longitude},{self.latitude}"
        dest_coords = f"{destination.longitude},{destination.latitude}"

        osrm_route_url = f"{osrm_base_url}/route/v1/driving/{start_coords};{dest_coords}?overview=full&geometries=geojson"

        try:
            response = requests.get(osrm_route_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with OSRM server: {e}")
            return None

        data = response.json()
        if "routes" in data and data["routes"]:
            route_geometry = data["routes"][0]["geometry"]["coordinates"]
            return route_geometry
        else:
            print("No route found by OSRM.")
            return None

    @classmethod
    def generate_multiple_pins_map(cls, places, map_type="leaflet", zoom=13):
        """
        Generate a map with multiple pins for the provided places.

        Parameters:
            places (list): A list of PlaceMixin instances to display on the map.
            map_type (str): The type of map to generate ('leaflet' or 'openlayers').
            zoom (int): The zoom level for the map.

        Returns:
            str: HTML and JavaScript code for embedding the map with multiple pins.
        """
        if map_type == "leaflet":
            map_script = f"""
            <div id="map" style="height: 500px;"></div>
            <script>
                var map = L.map('map').setView([{places[0].latitude}, {places[0].longitude}], {zoom});
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
            """

            for place in places:
                map_script += f"""
                var marker = L.marker([{place.latitude}, {place.longitude}]).addTo(map);
                marker.bindPopup("<b>{place.place_name}</b><br>{place.place_description}").openPopup();
                """

            map_script += "</script>"
            return map_script

        elif map_type == "openlayers":
            map_script = f"""
            <div id="map" style="height: 500px;"></div>
            <script src="https://openlayers.org/en/v4.6.5/build/ol.js" type="text/javascript"></script>
            <script type="text/javascript">
                var map = new ol.Map({{
                    target: 'map',
                    layers: [
                        new ol.layer.Tile({{
                            source: new ol.source.OSM()
                        }})
                    ],
                    view: new ol.View({{
                        center: ol.proj.fromLonLat([{places[0].longitude}, {places[0].latitude}]),
                        zoom: {zoom}
                    }})
                }});
            """

            for place in places:
                map_script += f"""
                var marker = new ol.Overlay({{
                    position: ol.proj.fromLonLat([{place.longitude}, {place.latitude}]),
                    positioning: 'center-center',
                    element: document.createElement('div'),
                    stopEvent: false
                }});
                marker.getElement().innerHTML = "<div style='background: red; width: 10px; height: 10px; border-radius: 50%;'></div>";
                map.addOverlay(marker);
                """

            map_script += "</script>"
            return map_script
    @staticmethod
    @lru_cache(maxsize=128)  # Cache the results of OSRM queries to improve performance
    def calculate_route_batch(locations, osrm_base_url="http://localhost:5000"):
        """
        Calculate a route passing through a batch of locations using OSRM.

        Parameters:
            locations (list of PlaceMixin): The list of PlaceMixin instances to route through.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Route: A namedtuple containing the route's coordinates, distance, and duration.
        """
        coordinates = ";".join([f"{loc.longitude},{loc.latitude}" for loc in locations])
        osrm_route_url = f"{osrm_base_url}/route/v1/driving/{coordinates}?overview=full&geometries=geojson&steps=true"

        try:
            response = requests.get(osrm_route_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with OSRM server: {e}")
            return None

        data = response.json()
        if "routes" in data and data["routes"]:
            route_data = data["routes"][0]
            return Route(
                coordinates=route_data["geometry"]["coordinates"],
                distance=route_data["distance"],
                duration=route_data["duration"],
            )
        else:
            print("No route found by OSRM.")
            return None

    def calculate_route_to(self, destination, osrm_base_url="http://localhost:5000"):
        """
        Calculate a direct route from this location to the destination using OSRM.

        Parameters:
            destination (PlaceMixin): The destination instance.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Route: A namedtuple containing the route's coordinates, distance, and duration.
        """
        return self.calculate_route_batch([self, destination], osrm_base_url)

    def calculate_optimal_route(self, destinations, osrm_base_url="http://localhost:5000"):
        """
        Calculate the optimal route through multiple destinations, including this location.

        Parameters:
            destinations (list of PlaceMixin): The destination instances to include in the route.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Route: A namedtuple containing the route's coordinates, distance, and duration.
        """
        locations = [self] + destinations
        return self.calculate_route_batch(locations, osrm_base_url)

    def estimate_travel_time(self, destination, speed_kmh=50):
        """
        Estimate the travel time to a destination.

        Parameters:
            destination (PlaceMixin): The destination instance.
            speed_kmh (float): Average travel speed in kilometers per hour.

        Returns:
            float: Estimated travel time in minutes.
        """
        route = self.calculate_route_to(destination)
        if route:
            return route.duration / 60  # Convert seconds to minutes
        return None

    @staticmethod
    def precompute_routes(locations, osrm_base_url="http://localhost:5000"):
        """
        Precompute and store routes between a set of locations.

        Parameters:
            locations (list of PlaceMixin): The list of PlaceMixin instances to route between.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            dict: A dictionary mapping location pairs to their precomputed routes.
        """
        routes = {}
        for i, loc1 in enumerate(locations):
            for loc2 in locations[i+1:]:
                route = loc1.calculate_route_to(loc2, osrm_base_url)
                if route:
                    routes[(loc1, loc2)] = route
                    routes[(loc2, loc1)] = route  # Store reverse route as well
        return routes

    def find_closest_instances(cls, latitude, longitude, n=1, method='haversine'):
        """
        Find the `n` closest instances to a given latitude and longitude using a specified distance calculation method.

        Parameters:
            latitude (float): The latitude to compare.
            longitude (float): The longitude to compare.
            n (int): The number of closest instances to return.
            method (str): The distance calculation method ('haversine', 'geodesic', 'great_circle', 'euclidean').

        Returns:
            list: The `n` closest PlaceMixin instances.
        """
        instances = cls.query.all()
        distances = []

        for instance in instances:
            distance = None
            if method == 'haversine':
                distance = cls.haversine(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'geodesic':
                distance = cls.geodesic(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'great_circle':
                distance = cls.great_circle(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'euclidean':
                distance = cls.euclidean(latitude, longitude, instance.latitude, instance.longitude)
            distances.append((instance, distance))

        # Sort by distance and return the top `n` instances
        distances.sort(key=lambda x: x[1])
        return [d[0] for d in distances[:n]]

    @staticmethod
    def write_templates(directory):
        """
        Write out Jinja2 templates and examples to a designated directory.

        Parameters:
            directory (str): The path to the directory where the templates will be written.
        """
        os.makedirs(directory, exist_ok=True)

        template_map = {
            "map_template.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Leaflet Map</title>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            </head>
            <body>
                <!-- Map Container -->
                <div id="map" style="height: 500px;"></div>

                <!-- Leaflet Map Script from Flask -->
                {{ map_script|safe }}
            </body>
            </html>
            """,

            "openlayers_map_template.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>OpenLayers Map</title>
                <script src="https://openlayers.org/en/v4.6.5/build/ol.js" type="text/javascript"></script>
            </head>
            <body>
                <!-- Map Container -->
                <div id="map" style="height: 500px;"></div>

                <!-- OpenLayers Map Script from Flask -->
                {{ map_script|safe }}
            </body>
            </html>
            """,

            "route_template.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Route Map</title>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            </head>
            <body>
                <!-- Map Container -->
                <div id="map" style="height: 500px;"></div>

                <!-- Route Map Script from Flask -->
                {{ route_map_script|safe }}
            </body>
            </html>
            """,

            "current_location_template.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Current Location</title>
            </head>
            <body>
                <!-- Button and Location Display -->
                {{ current_location_script|safe }}
            </body>
            </html>
            """
        }

        for filename, content in template_map.items():
            file_path = os.path.join(directory, filename)
            with open(file_path, 'w') as f:
                f.write(content.strip())
                print(f"Template written to {file_path}")

