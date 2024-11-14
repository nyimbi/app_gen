import os
import math
import json
import requests
from functools import lru_cache
from collections import namedtuple
from sqlalchemy import Column, String, Text, Float, Boolean, Table, MetaData, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geopy.distance import geodesic, great_circle
from fuzzywuzzy import process


Route = namedtuple("Route", ["coordinates", "distance", "duration"])

class PlaceMixin:
    """
    A mixin for Flask-AppBuilder models that provides geographical information,
    including optimized routing capabilities.

    Features:
    - Latitude, longitude, altitude, and geometric data storage.
    - Integration with Leaflet and OpenLayers for map rendering.
    - Optional routing functionality via OSRM.
    - Methods to generate Leaflet and OpenLayers maps, including markers, routes, and more.
    - Display of multiple pins for a selection of table rows.
    - Plotting of the shortest route between selected locations.
    - Support for different distance calculation methods: Haversine, Geodesic, Great Circle, and Euclidean.
    - Return `n` nearest instances using different distance calculation methods.
    - Caching of routes to minimize API calls.
    - Batch OSRM requests for multiple routes.
    - Precompute and store frequent routes.
    - Export capabilities for GeoJSON and KML formats.
    - Validation for latitude and longitude.
    - Write out Jinja2 templates and examples for Flask views.
    - Estimate travel time between locations.

    Usage:
    - OSRM integration is optional. If used, an OSRM server must be set up, and the base URL provided to relevant methods.
    - Leaflet and OpenLayers are used for map rendering. The generated maps can be embedded in Flask templates using the provided methods.
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

    # Geonames related tables and download configurations
    geonames_url = "http://download.geonames.org/export/dump/"
    geonames_files = {
        "allCountries.zip": "allCountries.txt",
        "countryInfo.txt": "countryInfo.txt",
        "admin1CodesASCII.txt": "admin1Codes.txt",
        "admin2Codes.txt": "admin2Codes.txt",
        "featureCodes_en.txt": "featureCodes.txt",
        "timeZones.txt": "timeZones.txt",
    }
    geonames_dir = "geonames_data"


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

    def to_geojson(self):
        """
        Converts a single PlaceMixin instance to a GeoJSON feature.
        """
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
                "info": self.info,
                "pin_color": self.pin_color,
                "pin_icon": self.pin_icon,
                "centered": self.centered,
                "nearest_feature": self.nearest_feature,
            }
        }
        return geojson

    @classmethod
    def to_geojson_collection(cls, instances):
        """
        Converts a list of PlaceMixin instances to a GeoJSON FeatureCollection.

        Parameters:
            instances (list): A list of PlaceMixin instances.

        Returns:
            str: A GeoJSON FeatureCollection string.
        """
        features = [instance.to_geojson() for instance in instances]
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        return json.dumps(feature_collection)

    def to_kml(self):
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

    @staticmethod
    def geodesic(lat1, lon1, lat2, lon2):
        """
        Calculate the Geodesic distance (Vincenty method) between two points on the Earth's surface.
        Uses the WGS-84 ellipsoid model of the Earth.
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def great_circle(lat1, lon1, lat2, lon2):
        """
        Calculate the Great Circle distance between two points on the Earth's surface.
        This method is faster than Geodesic but less accurate.
        """
        return great_circle((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def euclidean(lat1, lon1, lat2, lon2):
        """
        Calculate the Euclidean distance between two points.
        Note: This method does not account for the curvature of the Earth and is less accurate for long distances.
        """
        dLat = lat2 - lat1
        dLon = lon2 - lon1
        return math.sqrt(dLat * dLat + dLon * dLon)

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
        route = self.calculate_route_to(destination, osrm_base_url=osrm_base_url)

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
            leaflet_map_script += ",".join([f"[{lon},{lat}]" for lon, lat in route.coordinates])
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
        route = self.calculate_route_to(destination, osrm_base_url=osrm_base_url)

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
            openlayers_map_script += ",".join([f"ol.proj.fromLonLat([{lon},{lat}])" for lon, lat in route.coordinates])
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

    """GEONAMES and Geocoding functions"""

     @classmethod
    def setup_geonames(cls, engine):
        """
        Download and populate the Geonames database.
        """
        if not os.path.exists(cls.geonames_dir):
            os.makedirs(cls.geonames_dir)

        # Download the files
        for file_name, _ in cls.geonames_files.items():
            cls.download_file_wget(cls.geonames_url + file_name, os.path.join(cls.geonames_dir, file_name))

        # Create tables if they don't exist
        cls.create_geonames_tables(engine)

        # Populate tables
        cls.populate_geonames_tables(engine)

    @staticmethod
    def download_file_wget(url, destination):
        """
        Download a file using wget with parallel connections and retries.
        """
        if not os.path.exists(destination):
            print(f"Downloading {url} with wget...")
            command = [
                'wget', '-c', '-t', '10', '-O', destination,
                '--retry-connrefused', '--waitretry=1', '--timeout=20', '-T', '15', '--tries=10',
                '--retry-connrefused', '-nv', '--show-progress', '--max-redirect=20', '-e',
                'robots=off', '--no-check-certificate', url, '--quiet', '--no-dns-cache',
                '--no-hsts', '--no-cookies', '--no-use-server-timestamps', '--timestamping'
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print(f"Failed to download {url}. Error: {result.stderr.decode('utf-8')}")
            else:
                print(f"Successfully downloaded {destination}")

            # Unzip if necessary
            if destination.endswith('.zip'):
                with zipfile.ZipFile(destination, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(destination))
                print(f"Extracted {destination}")

    @classmethod
    def create_geonames_tables(cls, engine):
        """
        Create the Geonames tables if they don't exist.
        """
        metadata = MetaData(bind=engine)
        metadata.reflect()

        if 'geoname' not in metadata.tables:
            Table('geoname', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('name', String(200)),
                  Column('asciiname', String(200)),
                  Column('alt_names', Text),
                  Column('latitude', Float),
                  Column('longitude', Float),
                  Column('fclass', String(1)),
                  Column('fcode', String(10)),
                  Column('countrycode', String(2)),
                  Column('cc2', String(100)),
                  Column('admin1', String(20)),
                  Column('admin2', String(80)),
                  Column('admin3', String(20)),
                  Column('admin4', String(20)),
                  Column('population', BigInteger),
                  Column('elevation', Integer),
                  Column('gtopo30', Integer),
                  Column('timezone', String(40)),
                  Column('moddate', String(10)),
                  extend_existing=True)
            metadata.create_all()

        if 'country' not in metadata.tables:
            Table('country', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('iso_alpha2', String(2), nullable=False),
                  Column('iso_alpha3', String(3), nullable=False),
                  Column('iso_numeric', Integer),
                  Column('fips_code', String(3)),
                  Column('name', String(200)),
                  Column('capital', String(200)),
                  Column('areainsqkm', Float),
                  Column('population', Integer),
                  Column('continent', String(2)),
                  Column('tld', String(10)),
                  Column('currencycode', String(3)),
                  Column('currencyname', String(20)),
                  Column('phone', String(20)),
                  Column('postalcode', String(100)),
                  Column('postalcoderegex', String(200)),
                  Column('languages', String(200)),
                  Column('neighbors', String(50)),
                  Column('equivfipscode', String(3)),
                  extend_existing=True)
            metadata.create_all()

        if 'admin1Codes' not in metadata.tables:
            Table('admin1Codes', metadata,
                  Column('code', String(10), primary_key=True),
                  Column('name', String(200)),
                  Column('asciiname', String(200)),
                  Column('geonameid', Integer),
                  extend_existing=True)
            metadata.create_all()

        if 'admin2Codes' not in metadata.tables:
            Table('admin2Codes', metadata,
                  Column('code', String(20), primary_key=True),
                  Column('name', String(200)),
                  Column('asciiname', String(200)),
                  Column('geonameid', Integer),
                  extend_existing=True)
            metadata.create_all()

        if 'featureCodes' not in metadata.tables:
            Table('featureCodes', metadata,
                  Column('code', String(10), primary_key=True),
                  Column('name', String(200)),
                  Column('description', Text),
                  extend_existing=True)
            metadata.create_all()

        if 'timeZones' not in metadata.tables:
            Table('timeZones', metadata,
                  Column('country_code', String(2), primary_key=True),
                  Column('timezone_id', String(200)),
                  Column('gmt_offset', Float),
                  Column('dst_offset', Float),
                  Column('raw_offset', Float),
                  extend_existing=True)
            metadata.create_all()

    @classmethod
    def populate_geonames_tables(cls, engine):
        """
        Populate the Geonames tables with data.
        """
        metadata = MetaData(bind=engine)
        metadata.reflect()
        geoname_table = metadata.tables['geoname']
        country_table = metadata.tables['country']
        admin1_table = metadata.tables['admin1Codes']
        admin2_table = metadata.tables['admin2Codes']
        feature_table = metadata.tables['featureCodes']
        timezone_table = metadata.tables['timeZones']

        # Populate geoname table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['allCountries.zip']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    conn.execute(geoname_table.insert().values(
                        id=int(row[0]),
                        name=row[1],
                        asciiname=row[2],
                        alt_names=row[3],
                        latitude=float(row[4]),
                        longitude=float(row[5]),
                        fclass=row[6],
                        fcode=row[7],
                        countrycode=row[8],
                        cc2=row[9],
                        admin1=row[10],
                        admin2=row[11],
                        admin3=row[12],
                        admin4=row[13],
                        population=int(row[14]) if row[14] else None,
                        elevation=int(row[15]) if row[15] else None,
                        gtopo30=int(row[16]) if row[16] else None,
                        timezone=row[17],
                        moddate=row[18]
                    ))

        # Populate country table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['countryInfo.txt']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    if not row[0].startswith('#'):
                        conn.execute(country_table.insert().values(
                            iso_alpha2=row[0],
                            iso_alpha3=row[1],
                            iso_numeric=int(row[2]) if row[2] else None,
                            fips_code=row[3],
                            name=row[4],
                            capital=row[5],
                            areainsqkm=float(row[6]) if row[6] else None,
                            population=int(row[7]) if row[7] else None,
                            continent=row[8],
                            tld=row[9],
                            currencycode=row[10],
                            currencyname=row[11],
                            phone=row[12],
                            postalcode=row[13],
                            postalcoderegex=row[14],
                            languages=row[15],
                            neighbors=row[16],
                            equivfipscode=row[17]
                        ))

        # Populate admin1 table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['admin1CodesASCII.txt']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    conn.execute(admin1_table.insert().values(
                        code=row[0],
                        name=row[1],
                        asciiname=row[2],
                        geonameid=int(row[3])
                    ))

        # Populate admin2 table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['admin2Codes.txt']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    conn.execute(admin2_table.insert().values(
                        code=row[0],
                        name=row[1],
                        asciiname=row[2],
                        geonameid=int(row[3])
                    ))

        # Populate feature codes table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['featureCodes_en.txt']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    conn.execute(feature_table.insert().values(
                        code=row[0],
                        name=row[1],
                        description=row[2]
                    ))

        # Populate time zones table
        with open(os.path.join(cls.geonames_dir, cls.geonames_files['timeZones.txt']), 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            with engine.connect() as conn:
                for row in reader:
                    conn.execute(timezone_table.insert().values(
                        country_code=row[0],
                        timezone_id=row[1],
                        gmt_offset=float(row[2]),
                        dst_offset=float(row[3]),
                        raw_offset=float(row[4])
                    ))

    def geocode_simple(self, session, name):
        """
        Geocode a name using the Geonames data and store the result as GeoJSON in the geocoded_data column.

        Parameters:
            session (Session): SQLAlchemy session.
            name (str): The name to geocode.
        """
        geoname_table = Table('geoname', MetaData(bind=session.bind), autoload_with=session.bind)
        result = session.query(geoname_table).filter(geoname_table.c.name.ilike(name)).first()

        if result:
            self.latitude = result.latitude
            self.longitude = result.longitude
            self.geocoded_data = json.dumps({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [self.longitude, self.latitude]
                },
                "properties": {
                    "name": result.name,
                    "asciiname": result.asciiname,
                    "countrycode": result.countrycode,
                    "admin1": result.admin1,
                    "admin2": result.admin2,
                    "admin3": result.admin3,
                    "admin4": result.admin4,
                    "population": result.population,
                    "elevation": result.elevation
                }
            })
        else:
            print(f"No geocoding result found for name: {name}")



    def geocode(self, session: Session, name: str, admin1: str = None, admin2: str = None,
                return_multiple: bool = False, max_results: int = 5, fuzzy: bool = False,
                latitude: float = None, longitude: float = None):
        """
        Geocode a place name using the Geonames data and store the result as GeoJSON in the geocoded_data column.

        Parameters:
            session (Session): SQLAlchemy session.
            name (str): The place name to geocode.
            admin1 (str, optional): Admin1 code to refine the search.
            admin2 (str, optional): Admin2 code to refine the search.
            return_multiple (bool, optional): Whether to return multiple matches.
            max_results (int, optional): Maximum number of results to return.
            fuzzy (bool, optional): Whether to use fuzzy matching for the place name.
            latitude (float, optional): Latitude to find the nearest place.
            longitude (float, optional): Longitude to find the nearest place.

        Returns:
            list: A list of GeoJSON Feature objects or a single Feature if return_multiple is False.
        """
        geoname_table = Table('geoname', MetaData(bind=session.bind), autoload_with=session.bind)
        admin1_table = Table('admin1Codes', MetaData(bind=session.bind), autoload_with=session.bind)
        admin2_table = Table('admin2Codes', MetaData(bind=session.bind), autoload_with=session.bind)
        country_table = Table('country', MetaData(bind=session.bind), autoload_with=session.bind)
        feature_table = Table('featureCodes', MetaData(bind=session.bind), autoload_with=session.bind)
        timezone_table = Table('timeZones', MetaData(bind=session.bind), autoload_with=session.bind)

        # Start building the query
        query = session.query(
            geoname_table.c.id.label('geonameid'),
            geoname_table.c.name.label('name'),
            geoname_table.c.asciiname,
            geoname_table.c.alt_names,
            geoname_table.c.latitude,
            geoname_table.c.longitude,
            geoname_table.c.population,
            geoname_table.c.elevation,
            geoname_table.c.fcode,
            geoname_table.c.admin1.label('admin1_code'),
            geoname_table.c.admin2.label('admin2_code'),
            geoname_table.c.timezone,
            country_table.c.name.label('country_name'),
            country_table.c.iso_alpha2,
            country_table.c.iso_alpha3,
            country_table.c.continent,
            country_table.c.id.label('country_geonameid'),
            admin1_table.c.name.label('admin1_name'),
            admin1_table.c.geonameid.label('admin1_geonameid'),
            admin2_table.c.name.label('admin2_name'),
            admin2_table.c.geonameid.label('admin2_geonameid'),
            feature_table.c.name.label('feature_name')
        ).join(
            country_table, geoname_table.c.countrycode == country_table.c.iso_alpha2
        ).join(
            admin1_table, geoname_table.c.admin1 == admin1_table.c.code, isouter=True
        ).join(
            admin2_table, geoname_table.c.admin2 == admin2_table.c.code, isouter=True
        ).join(
            feature_table, geoname_table.c.fcode == feature_table.c.code, isouter=True
        ).join(
            timezone_table, geoname_table.c.timezone == timezone_table.c.timezone_id, isouter=True
        )

        # Fuzzy matching
        if fuzzy:
            names = [row.name for row in query.all()]
            matched_name = process.extractOne(name, names)
            if matched_name:
                name = matched_name[0]

        # Basic name filtering
        filters = [geoname_table.c.name.ilike(f"%{name}%")]

        # Additional filtering by admin codes
        if admin1:
            filters.append(geoname_table.c.admin1 == admin1)
        if admin2:
            filters.append(geoname_table.c.admin2 == admin2)

        # Apply filters to query
        query = query.filter(and_(*filters))

        # If latitude and longitude are provided, calculate the distance
        if latitude is not None and longitude is not None:
            query = query.order_by(func.abs(geoname_table.c.latitude - latitude) + func.abs(geoname_table.c.longitude - longitude))

        # Limit results
        query = query.limit(max_results)

        results = query.all()

        # Handle no results found
        if not results:
            print(f"No geocoding result found for name: {name}")
            return []

        # Convert results to GeoJSON
        geojson_features = []
        for result in results:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [result.longitude, result.latitude]
                },
                "properties": {
                    "geonameid": result.geonameid,
                    "name": result.name,
                    "asciiname": result.asciiname,
                    "alt_names": result.alt_names,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "population": result.population,
                    "elevation": result.elevation,
                    "country_geonameid": result.country_geonameid,
                    "country_name": result.country_name,
                    "iso_alpha2": result.iso_alpha2,
                    "iso_alpha3": result.iso_alpha3,
                    "continent": result.continent,
                    "admin1_geonameid": result.admin1_geonameid,
                    "admin1_name": result.admin1_name,
                    "admin2_geonameid": result.admin2_geonameid,
                    "admin2_name": result.admin2_name,
                    "feature_name": result.feature_name,
                    "timezone": result.timezone,
                }
            }
            geojson_features.append(feature)

        # Store or return results
        if return_multiple:
            return geojson_features
        else:
            # Store the first result as the geocoded data
            self.latitude = results[0].latitude
            self.longitude = results[0].longitude
            self.geocoded_data = json.dumps(geojson_features[0])
            return geojson_features[0]



    def reverse_geocode(self, session: Session, latitude: float, longitude: float,
                        radius_km: float = 10, max_results: int = 1):
        """
        Perform reverse geocoding to find the nearest location(s) to the given coordinates.

        Parameters:
            session (Session): SQLAlchemy session.
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            radius_km (float, optional): Search radius in kilometers. Defaults to 10 km.
            max_results (int, optional): Maximum number of results to return. Defaults to 1.

        Returns:
            list: A list of GeoJSON Feature objects.
        """
        # Validate input coordinates
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Invalid latitude or longitude values.")

        metadata = MetaData(bind=session.bind)

        # Reflect tables
        geoname_table = Table('geoname', metadata, autoload_with=session.bind)
        country_table = Table('country', metadata, autoload_with=session.bind)
        admin1_table = Table('admin1Codes', metadata, autoload_with=session.bind)
        admin2_table = Table('admin2Codes', metadata, autoload_with=session.bind)
        feature_table = Table('featureCodes', metadata, autoload_with=session.bind)
        timezone_table = Table('timeZones', metadata, autoload_with=session.bind)

        # Haversine formula in SQL
        earth_radius_km = 6371.0
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)

        distance_expr = earth_radius_km * func.acos(
            func.sin(func.radians(latitude)) * func.sin(func.radians(geoname_table.c.latitude)) +
            func.cos(func.radians(latitude)) * func.cos(func.radians(geoname_table.c.latitude)) *
            func.cos(func.radians(geoname_table.c.longitude) - func.radians(longitude))
        )

        # Build query
        query = session.query(
            geoname_table.c.geonameid,
            geoname_table.c.name,
            geoname_table.c.asciiname,
            geoname_table.c.alternatenames,
            geoname_table.c.latitude,
            geoname_table.c.longitude,
            geoname_table.c.feature_class,
            geoname_table.c.feature_code,
            geoname_table.c.population,
            geoname_table.c.elevation,
            geoname_table.c.dem,
            geoname_table.c.timezone,
            geoname_table.c.modification_date,
            country_table.c.iso_alpha2.label('country_code'),
            country_table.c.name.label('country_name'),
            country_table.c.iso_alpha3,
            country_table.c.continent,
            admin1_table.c.name.label('admin1_name'),
            admin2_table.c.name.label('admin2_name'),
            feature_table.c.name.label('feature_name'),
            timezone_table.c.gmt_offset,
            timezone_table.c.dst_offset,
            timezone_table.c.raw_offset,
            distance_expr.label('distance')
        ).join(
            country_table, geoname_table.c.country_code == country_table.c.iso_alpha2, isouter=True
        ).join(
            admin1_table, func.concat(geoname_table.c.country_code, '.', geoname_table.c.admin1_code) == admin1_table.c.code, isouter=True
        ).join(
            admin2_table, func.concat(geoname_table.c.country_code, '.', geoname_table.c.admin1_code, '.', geoname_table.c.admin2_code) == admin2_table.c.code, isouter=True
        ).join(
            feature_table, func.concat(geoname_table.c.feature_class, '.', geoname_table.c.feature_code) == feature_table.c.code, isouter=True
        ).join(
            timezone_table, geoname_table.c.timezone == timezone_table.c.timezone_id, isouter=True
        ).filter(
            distance_expr <= radius_km
        ).order_by(
            distance_expr
        ).limit(
            max_results
        )

        results = query.all()

        if not results:
            return []

        geojson_features = []
        for result in results:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [result.longitude, result.latitude]
                },
                "properties": {
                    "geonameid": result.geonameid,
                    "name": result.name,
                    "asciiname": result.asciiname,
                    "alternatenames": result.alternatenames.split(',') if result.alternatenames else [],
                    "feature_class": result.feature_class,
                    "feature_code": result.feature_code,
                    "feature_name": result.feature_name,
                    "country_code": result.country_code,
                    "country_name": result.country_name,
                    "iso_alpha3": result.iso_alpha3,
                    "continent": result.continent,
                    "admin1_name": result.admin1_name,
                    "admin2_name": result.admin2_name,
                    "population": result.population,
                    "elevation": result.elevation,
                    "dem": result.dem,
                    "timezone": result.timezone,
                    "gmt_offset": result.gmt_offset,
                    "dst_offset": result.dst_offset,
                    "raw_offset": result.raw_offset,
                    "modification_date": str(result.modification_date),
                    "distance_km": round(result.distance, 3)
                }
            }
            geojson_features.append(feature)

        # Store the closest result
        closest_feature = geojson_features[0]
        self.latitude = closest_feature['geometry']['coordinates'][1]
        self.longitude = closest_feature['geometry']['coordinates'][0]
        self.geocoded_data = json.dumps(closest_feature)

        return geojson_features if max_results > 1 else closest_feature



    def find_places_in_polygon(self, polygon_coords, session):
        """
        Find all places within a given polygon.

        :param polygon_coords: List of (longitude, latitude) tuples defining the polygon
        :param session: SQLAlchemy session
        :return: List of places within the polygon
        """
        polygon = Polygon(polygon_coords)
        polygon_wkb = from_shape(polygon, srid=4326)

        query = session.query(self.__class__).filter(
            func.ST_Within(self.__class__.geometry, func.ST_GeomFromWKB(polygon_wkb))
        )

        return query.all()

    def is_within_fence(self, lat, lon, distance_km):
        """
        Check if the place is within a certain distance of a point.

        :param lat: Latitude of the center point
        :param lon: Longitude of the center point
        :param distance_km: Radius in kilometers
        :return: Boolean indicating if the place is within the fence
        """
        point = Point(lon, lat)
        place_point = to_shape(self.geometry)
        return place_point.distance(point) <= distance_km / 111.32


    @staticmethod
    def transform_coordinates(from_crs, to_crs, lon, lat):
        """
        Transform coordinates from one CRS to another.

        :param from_crs: Source coordinate reference system (e.g., 'EPSG:4326')
        :param to_crs: Target coordinate reference system
        :param lon: Longitude in the source CRS
        :param lat: Latitude in the source CRS
        :return: (longitude, latitude) in the target CRS
        """
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        return transformer.transform(lon, lat)

    def set_coordinates_in_crs(self, lon, lat, from_crs='EPSG:4326'):
        """
        Set the place's coordinates, transforming them from the given CRS to WGS84 if necessary.

        :param lon: Longitude in the source CRS
        :param lat: Latitude in the source CRS
        :param from_crs: Source coordinate reference system (default is WGS84)
        """
        if from_crs != 'EPSG:4326':
            lon, lat = self.transform_coordinates(from_crs, 'EPSG:4326', lon, lat)

        self.longitude = lon
        self.latitude = lat
        self.geometry = f'POINT({lon} {lat})'


    def generate_mapbox_map(self, mapbox_access_token, zoom=13):
        """
        Generate HTML and JavaScript for a Mapbox GL JS map centered on this place.

        :param mapbox_access_token: Mapbox access token
        :param zoom: The zoom level for the map
        :return: HTML and JavaScript code for embedding the Mapbox GL JS map
        """
        mapbox_map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script src='https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.js'></script>
        <link href='https://api.mapbox.com/mapbox-gl-js/v2.9.1/mapbox-gl.css' rel='stylesheet' />
        <script>
            mapboxgl.accessToken = '{mapbox_access_token}';
            var map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v11',
                center: [{self.longitude}, {self.latitude}],
                zoom: {zoom}
            }});

            new mapboxgl.Marker()
                .setLngLat([{self.longitude}, {self.latitude}])
                .addTo(map);
        </script>
        """
        return mapbox_map_script

def generate_static_map(self, mapbox_access_token, width=600, height=400, zoom=13):
        """
        Generate a static map image using Mapbox Static Images API.

        :param mapbox_access_token: Mapbox access token
        :param width: Width of the image in pixels
        :param height: Height of the image in pixels
        :param zoom: The zoom level for the map
        :return: URL of the static map image
        """
        base_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static"
        marker = f"pin-s+ff0000({self.longitude},{self.latitude})"
        center = f"{self.longitude},{self.latitude}"

        static_map_url = f"{base_url}/{marker}/{center},{zoom}/{width}x{height}?access_token={mapbox_access_token}"

        return static_map_url

    def save_static_map(self, mapbox_access_token, file_path, width=600, height=400, zoom=13):
        """
        Save a static map image to a file.

        :param mapbox_access_token: Mapbox access token
        :param file_path: Path to save the image file
        :param width: Width of the image in pixels
        :param height: Height of the image in pixels
        :param zoom: The zoom level for the map
        """
        static_map_url = self.generate_static_map(mapbox_access_token, width, height, zoom)
        response = requests.get(static_map_url)

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Static map saved to {file_path}")
        else:
            print(f"Failed to generate static map. Status code: {response.status_code}")



