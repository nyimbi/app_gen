from __future__ import annotations
from typing import List, Tuple, Optional, Union, Dict, Any
from sqlalchemy import Column, String, Integer, BigInteger, Date, Text, Float, Boolean, Table, MetaData, and_, func
from sqlalchemy.orm import Session, declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import requests
import json
from functools import lru_cache
from geopy.distance import geodesic, great_circle
import math
import os
from flask_appbuilder import Model

Base = declarative_base()

class PlaceMixin(Base):
    # __abstract__ = True

    """
    An enhanced mixin for Flask-AppBuilder models that provides comprehensive geographical information and operations.

    This mixin offers a fluent interface for chaining operations, comprehensive type hints,
    and improved documentation for better maintainability and IDE support. It utilizes modern
    Python features like f-strings and type annotations.

    Features:
    - Geographical data storage (latitude, longitude, altitude)
    - Geocoding and reverse geocoding
    - Distance calculations using various methods
    - Polygon searches and geofencing
    - Coordinate system transformations
    - Map generation (Leaflet, OpenLayers, Mapbox)
    - Static map generation
    - Routing capabilities
    - Geonames integration

    Usage:
    class MyPlace(PlaceMixin):
        __tablename__ = 'my_places'
        id = Column(Integer, primary_key=True)
        name = Column(String(50), unique=True, nullable=False)

    place = MyPlace(name="Example Place")
    place.set_coordinates(40.7128, -74.0060).geocode().save()
    """

    # Core geographic attributes
    place_name: Column = Column(String(100))
    place_description: Column = Column(Text)
    latitude: Column = Column(Float)
    longitude: Column = Column(Float)
    altitude: Column = Column(Float)
    geometry: Column = Column(Geometry(geometry_type='POINT', srid=4326))
    map: Column = Column(Text, default="")
    info: Column = Column(Text, default="")
    pin: Column = Column(Boolean)
    pin_color: Column = Column(String(20))
    pin_icon: Column = Column(String(50))
    centered: Column = Column(Boolean)
    nearest_feature: Column = Column(String(100))
    crs: Column = Column(String(20), default="EPSG:4326")

    # Geonames related configurations
    geonames_url: str = "http://download.geonames.org/export/dump/"
    geonames_files: Dict[str, str] = {
        "allCountries.zip": "allCountries.txt",
        "countryInfo.txt": "countryInfo.txt",
        "admin1CodesASCII.txt": "admin1Codes.txt",
        "admin2Codes.txt": "admin2Codes.txt",
        "featureCodes_en.txt": "featureCodes.txt",
        "timeZones.txt": "timeZones.txt",
    }
    geonames_dir: str = "geonames_data"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def set_coordinates(self, latitude: float, longitude: float, altitude: Optional[float] = None) -> PlaceMixin:
        """
        Set the geographical coordinates for the place.

        :param latitude: Latitude in degrees
        :param longitude: Longitude in degrees
        :param altitude: Altitude in meters (optional)
        :return: Self for method chaining
        """
        self.latitude = latitude
        self.longitude = longitude
        if altitude is not None:
            self.altitude = altitude
        self.geometry = f'POINT({longitude} {latitude})'
        return self

    def validate_latitude(self, latitude: float) -> None:
        """
        Validate the given latitude value.

        :param latitude: Latitude value to validate
        :raises ValueError: If latitude is invalid
        """
        if not -90 <= latitude <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')

    def validate_longitude(self, longitude: float) -> None:
        """
        Validate the given longitude value.

        :param longitude: Longitude value to validate
        :raises ValueError: If longitude is invalid
        """
        if not -180 <= longitude <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')

    def validate(self) -> None:
        """
        Validate the place's coordinates.

        :raises ValueError: If coordinates are invalid
        """
        self.validate_latitude(self.latitude)
        self.validate_longitude(self.longitude)

    def geocode(self, address: str, provider: str = 'nominatim') -> PlaceMixin:
        """
        Geocode the given address and set the coordinates.

        :param address: Address to geocode
        :param provider: Geocoding service provider (default: 'nominatim')
        :return: Self for method chaining
        :raises ValueError: If geocoding fails
        """
        # Implementation of geocoding logic here
        # This is a placeholder and should be replaced with actual geocoding logic
        print(f"Geocoding {address} using {provider}")
        # Simulating a geocoding result
        self.set_coordinates(40.7128, -74.0060)
        return self

    def reverse_geocode(self) -> PlaceMixin:
        """
        Perform reverse geocoding to find the address for the current coordinates.

        :return: Self for method chaining
        :raises ValueError: If reverse geocoding fails
        """
        # Implementation of reverse geocoding logic here
        # This is a placeholder and should be replaced with actual reverse geocoding logic
        print(f"Reverse geocoding coordinates: {self.latitude}, {self.longitude}")
        self.place_name = "Example Place"
        self.place_description = "123 Example Street, Example City"
        return self

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on the earth using the Haversine formula.

        :param lat1: Latitude of the first point
        :param lon1: Longitude of the first point
        :param lat2: Latitude of the second point
        :param lon2: Longitude of the second point
        :return: Distance in kilometers
        """
        R = 6371  # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon / 2) * math.sin(dLon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    @staticmethod
    def geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the geodesic distance between two points on the earth's surface.

        :param lat1: Latitude of the first point
        :param lon1: Longitude of the first point
        :param lat2: Latitude of the second point
        :param lon2: Longitude of the second point
        :return: Distance in kilometers
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def great_circle_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the earth's surface.

        :param lat1: Latitude of the first point
        :param lon1: Longitude of the first point
        :param lat2: Latitude of the second point
        :param lon2: Longitude of the second point
        :return: Distance in kilometers
        """
        return great_circle((lat1, lon1), (lat2, lon2)).kilometers

    def distance_to(self, other: Union[PlaceMixin, Tuple[float, float]], method: str = 'haversine') -> float:
        """
        Calculate the distance to another place or coordinates using the specified method.

        :param other: Another PlaceMixin instance or a tuple of (latitude, longitude)
        :param method: Distance calculation method ('haversine', 'geodesic', or 'great_circle')
        :return: Distance in kilometers
        :raises ValueError: If an invalid method is specified
        """
        if isinstance(other, tuple):
            other_lat, other_lon = other
        else:
            other_lat, other_lon = other.latitude, other.longitude

        if method == 'haversine':
            return self.haversine(self.latitude, self.longitude, other_lat, other_lon)
        elif method == 'geodesic':
            return self.geodesic_distance(self.latitude, self.longitude, other_lat, other_lon)
        elif method == 'great_circle':
            return self.great_circle_distance(self.latitude, self.longitude, other_lat, other_lon)
        else:
            raise ValueError(f"Invalid distance calculation method: {method}")

    def find_places_in_polygon(self, polygon_coords: List[Tuple[float, float]], session: Session) -> List[PlaceMixin]:
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

    def is_within_fence(self, lat: float, lon: float, distance_km: float) -> bool:
        """
        Check if the place is within a certain distance of a point.

        :param lat: Latitude of the center point
        :param lon: Longitude of the center point
        :param distance_km: Radius in kilometers
        :return: Boolean indicating if the place is within the fence
        """
        point = Point(lon, lat)
        place_point = to_shape(self.geometry)
        return place_point.distance(point) <= distance_km / 111.32  # Approximate degrees to km conversion

    @staticmethod
    def transform_coordinates(from_crs: str, to_crs: str, lon: float, lat: float) -> Tuple[float, float]:
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

    def set_coordinates_in_crs(self, lon: float, lat: float, from_crs: str = 'EPSG:4326') -> PlaceMixin:
        """
        Set the place's coordinates, transforming them from the given CRS to WGS84 if necessary.

        :param lon: Longitude in the source CRS
        :param lat: Latitude in the source CRS
        :param from_crs: Source coordinate reference system (default is WGS84)
        :return: Self for method chaining
        """
        if from_crs != 'EPSG:4326':
            lon, lat = self.transform_coordinates(from_crs, 'EPSG:4326', lon, lat)

        return self.set_coordinates(lat, lon)

    def generate_leaflet_map(self, zoom: int = 13, marker: bool = True) -> str:
        """
        Generate HTML and JavaScript for a Leaflet map centered on this place.

        :param zoom: The zoom level for the map
        :param marker: Whether to place a marker on the map at the location
        :return: HTML and JavaScript code for embedding the Leaflet map
        """
        map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script>
            var map = L.map('map').setView([{self.latitude}, {self.longitude}], {zoom});
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
        """

        if marker:
            map_script += f"""
            var marker = L.marker([{self.latitude}, {self.longitude}]).addTo(map);
            marker.bindPopup("<b>{self.place_name}</b><br>{self.place_description}").openPopup();
            """

        map_script += "</script>"
        return map_script

    def generate_openlayers_map(self, zoom: int = 13, marker: bool = True) -> str:
        """
        Generate HTML and JavaScript for an OpenLayers map centered on this place.

        :param zoom: The zoom level for the map
        :param marker: Whether to place a marker on the map at the location
        :return: HTML and JavaScript code for embedding the OpenLayers map
        """
        map_script = f"""
        <div id="map" style="height: 500px;"></div>
        <script src="https://openlayers.org/en/v6.5.0/build/ol.js"></script>
        <link rel="stylesheet" href="https://openlayers.org/en/v6.5.0/css/ol.css" type="text/css">
        <script>
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
            map_script += f"""
            var marker = new ol.Feature({{
                geometry: new ol.geom.Point(ol.proj.fromLonLat([{self.longitude}, {self.latitude}]))
            }});
            var vectorSource = new ol.source.Vector({{
                features: [marker]
            }});
            var markerVectorLayer = new ol.layer.Vector({{
                source: vectorSource,
            }});
            map.addLayer(markerVectorLayer);
            """

        map_script += "</script>"
        return map_script

    def generate_mapbox_map(self, mapbox_access_token: str, zoom: int = 13) -> str:
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

    def generate_static_map(self, mapbox_access_token: str, width: int = 600, height: int = 400, zoom: int = 13) -> str:
        """
        Generate a static map image URL using Mapbox Static Images API.

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

    def save_static_map(self, mapbox_access_token: str, file_path: str, width: int = 600, height: int = 400, zoom: int = 13) -> None:
        """
        Save a static map image to a file.

        :param mapbox_access_token: Mapbox access token
        :param file_path: Path to save the image file
        :param width: Width of the image in pixels
        :param height: Height of the image in pixels
        :param zoom: The zoom level for the map
        :raises IOError: If unable to save the file
        """
        static_map_url = self.generate_static_map(mapbox_access_token, width, height, zoom)
        response = requests.get(static_map_url)

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Static map saved to {file_path}")
        else:
            raise IOError(f"Failed to generate static map. Status code: {response.status_code}")

    def calculate_route_online(self, destination):
        # Example using OSRM for route calculation
        response = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/{self.longitude},{self.latitude};{destination.longitude},{destination.latitude}?overview=false")
        data = response.json()
        route = data.get('routes', [])[0].get('geometry', {}).get('coordinates', [])
        return route

    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_route_batch(locations: Tuple[PlaceMixin, ...], osrm_base_url: str = "http://localhost:5000") -> Optional[Dict[str, Any]]:
        """
        Calculate a route passing through a batch of locations using OSRM.

        :param locations: Tuple of PlaceMixin instances to route through
        :param osrm_base_url: The base URL of the OSRM server
        :return: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails
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
            return {
                "coordinates": route_data["geometry"]["coordinates"],
                "distance": route_data["distance"],
                "duration": route_data["duration"],
            }
        else:
            print("No route found by OSRM.")
            return None

    def calculate_route_to(self, destination: PlaceMixin, osrm_base_url: str = "http://localhost:5000") -> Optional[Dict[str, Any]]:
        """
        Calculate a direct route from this location to the destination using OSRM.

        :param destination: The destination instance
        :param osrm_base_url: The base URL of the OSRM server
        :return: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails
        """
        return self.calculate_route_batch((self, destination), osrm_base_url)

    def calculate_optimal_route(self, destinations: List[PlaceMixin], osrm_base_url: str = "http://localhost:5000") -> Optional[Dict[str, Any]]:
        """
        Calculate the optimal route through multiple destinations, including this location.

        :param destinations: The destination instances to include in the route
        :param osrm_base_url: The base URL of the OSRM server
        :return: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails
        """
        locations = tuple([self] + destinations)
        return self.calculate_route_batch(locations, osrm_base_url)

    def estimate_travel_time(self, destination: PlaceMixin, speed_kmh: float = 50) -> Optional[float]:
        """
        Estimate the travel time to a destination.

        :param destination: The destination instance
        :param speed_kmh: Average travel speed in kilometers per hour
        :return: Estimated travel time in minutes, or None if route calculation fails
        """
        route = self.calculate_route_to(destination)
        if route:
            return route["duration"] / 60  # Convert seconds to minutes
        return None

    @classmethod
    def precompute_routes(cls, locations: List[PlaceMixin], osrm_base_url: str = "http://localhost:5000") -> Dict[Tuple[PlaceMixin, PlaceMixin], Dict[str, Any]]:
        """
        Precompute and store routes between a set of locations.

        :param locations: The list of PlaceMixin instances to route between
        :param osrm_base_url: The base URL of the OSRM server
        :return: A dictionary mapping location pairs to their precomputed routes
        """
        routes = {}
        for i, loc1 in enumerate(locations):
            for loc2 in locations[i+1:]:
                route = loc1.calculate_route_to(loc2, osrm_base_url)
                if route:
                    routes[(loc1, loc2)] = route
                    routes[(loc2, loc1)] = route  # Store reverse route as well
        return routes

    @classmethod
    def generate_multiple_pins_map(cls, places: List[PlaceMixin], map_type: str = "leaflet", zoom: int = 13) -> str:
        """
        Generate a map with multiple pins for the provided places.

        :param places: A list of PlaceMixin instances to display on the map
        :param map_type: The type of map to generate ('leaflet' or 'openlayers')
        :param zoom: The zoom level for the map
        :return: HTML and JavaScript code for embedding the map with multiple pins
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
                marker.bindPopup("<b>{place.place_name}</b><br>{place.place_description}");
                """

            map_script += "</script>"
            return map_script

        elif map_type == "openlayers":
            map_script = f"""
            <div id="map" style="height: 500px;"></div>
            <script src="https://openlayers.org/en/v6.5.0/build/ol.js"></script>
            <link rel="stylesheet" href="https://openlayers.org/en/v6.5.0/css/ol.css" type="text/css">
            <script>
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

                var vectorSource = new ol.source.Vector({{
                    features: [
                        {','.join([f"new ol.Feature({{geometry: new ol.geom.Point(ol.proj.fromLonLat([{place.longitude}, {place.latitude}]))}})" for place in places])}
                    ]
                }});

                var vectorLayer = new ol.layer.Vector({{
                    source: vectorSource,
                    style: new ol.style.Style({{
                        image: new ol.style.Circle({{
                            radius: 6,
                            fill: new ol.style.Fill({{color: 'red'}}),
                            stroke: new ol.style.Stroke({{color: 'white', width: 2}})
                        }})
                    }})
                }});

                map.addLayer(vectorLayer);
            </script>
            """
            return map_script
        else:
            raise ValueError(f"Unsupported map type: {map_type}")

    @staticmethod
    def write_templates(directory: str) -> None:
        """
        Write out Jinja2 templates and examples to a designated directory.

        :param directory: The path to the directory where the templates will be written
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
                <script src="https://openlayers.org/en/v6.5.0/build/ol.js"></script>
                <link rel="stylesheet" href="https://openlayers.org/en/v6.5.0/css/ol.css" type="text/css">
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
        }

        for filename, content in template_map.items():
            file_path = os.path.join(directory, filename)
            with open(file_path, 'w') as f:
                f.write(content.strip())
            print(f"Template written to {file_path}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the place to a dictionary representation.

        :return: Dictionary containing the place's attributes
        """
        return {
            'place_name': self.place_name,
            'place_description': self.place_description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'pin': self.pin,
            'pin_color': self.pin_color,
            'pin_icon': self.pin_icon,
            'centered': self.centered,
            'nearest_feature': self.nearest_feature,
            'crs': self.crs,
        }

    def from_dict(self, data: Dict[str, Any]) -> PlaceMixin:
        """
        Update the place's attributes from a dictionary.

        :param data: Dictionary containing place attributes
        :return: Self for method chaining
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if 'latitude' in data and 'longitude' in data:
            self.set_coordinates(data['latitude'], data['longitude'], data.get('altitude'))

        return self

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the place to a GeoJSON feature.

        :return: GeoJSON feature dictionary
        """
        return {
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

    @classmethod
    def from_geojson(cls, geojson: Dict[str, Any]) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a GeoJSON feature.

        :param geojson: GeoJSON feature dictionary
        :return: PlaceMixin instance
        """
        instance = cls()
        coords = geojson['geometry']['coordinates']
        instance.set_coordinates(coords[1], coords[0])

        for key, value in geojson['properties'].items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        return instance

    @classmethod
    def to_geojson_collection(cls, instances: List['PlaceMixin']) -> Dict[str, Any]:
        """
        Convert a list of PlaceMixin instances to a GeoJSON FeatureCollection.

        :param instances: List of PlaceMixin instances
        :return: GeoJSON FeatureCollection dictionary
        """
        return {
            "type": "FeatureCollection",
            "features": [instance.to_geojson() for instance in instances]
        }

    def to_kml(self) -> str:
        """
        Convert the place to a KML Placemark.

        :return: KML Placemark string
        """
        return f"""
        <Placemark>
            <name>{self.place_name}</name>
            <description>{self.place_description}</description>
            <Point>
                <coordinates>{self.longitude},{self.latitude},{self.altitude or 0}</coordinates>
            </Point>
        </Placemark>
        """.strip()

    @classmethod
    def bulk_import_geojson(cls, geojson_data: Dict[str, Any]) -> List['PlaceMixin']:
        """
        Bulk import places from a GeoJSON FeatureCollection.

        :param geojson_data: GeoJSON FeatureCollection dictionary
        :return: List of created PlaceMixin instances
        """
        instances = []
        for feature in geojson_data['features']:
            instance = cls.from_geojson(feature)
            instances.append(instance)
        return instances

    @classmethod
    def find_closest_instances(cls, latitude: float, longitude: float, n: int = 1, method: str = 'haversine') -> List['PlaceMixin']:
        """
        Find the `n` closest instances to a given latitude and longitude using a specified distance calculation method.

        :param latitude: The latitude to compare
        :param longitude: The longitude to compare
        :param n: The number of closest instances to return
        :param method: The distance calculation method ('haversine', 'geodesic', 'great_circle')
        :return: The `n` closest PlaceMixin instances
        """
        instances = cls.query.all()
        distances = []

        for instance in instances:
            if method == 'haversine':
                distance = cls.haversine(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'geodesic':
                distance = cls.geodesic_distance(latitude, longitude, instance.latitude, instance.longitude)
            elif method == 'great_circle':
                distance = cls.great_circle_distance(latitude, longitude, instance.latitude, instance.longitude)
            else:
                raise ValueError(f"Unsupported distance calculation method: {method}")
            distances.append((instance, distance))

        distances.sort(key=lambda x: x[1])
        return [d[0] for d in distances[:n]]

    @classmethod
    def setup_geonames(cls, engine, download_dir: str = 'geonames_data') -> None:
        """
        Download and populate the Geonames database.

        :param engine: SQLAlchemy engine
        :param download_dir: Directory to store downloaded Geonames files
        """
        import wget
        import zipfile

        os.makedirs(download_dir, exist_ok=True)

        for file_name, _ in cls.geonames_files.items():
            file_path = os.path.join(download_dir, file_name)
            if not os.path.exists(file_path):
                print(f"Downloading {file_name}...")
                wget.download(cls.geonames_url + file_name, out=file_path)
                print(f"\nDownloaded {file_name}")

            if file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(download_dir)

        cls.create_geonames_tables(engine)
        cls.load_geonames_tables(engine, download_dir)

    @classmethod
    def create_geonames_tables(cls, engine) -> None:
        """
        Create the Geonames tables if they don't exist.

        :param engine: SQLAlchemy engine
        """
        metadata = MetaData()

        Table('geoname', metadata,
              Column('geonameid', Integer, primary_key=True),
              Column('name', String(200)),
              Column('asciiname', String(200)),
              Column('alternatenames', Text),
              Column('latitude', Float),
              Column('longitude', Float),
              Column('feature_class', String(1)),
              Column('feature_code', String(10)),
              Column('country_code', String(2)),
              Column('cc2', String(200)),
              Column('admin1_code', String(20)),
              Column('admin2_code', String(80)),
              Column('admin3_code', String(20)),
              Column('admin4_code', String(20)),
              Column('population', BigInteger),
              Column('elevation', Integer),
              Column('dem', Integer),
              Column('timezone', String(40)),
              Column('modification_date', Date)
        )

        Table('country_info', metadata,
              Column('iso_alpha2', String(2), primary_key=True),
              Column('iso_alpha3', String(3)),
              Column('iso_numeric', Integer),
              Column('fips_code', String(3)),
              Column('name', String(200)),
              Column('capital', String(200)),
              Column('area_in_sq_km', Float),
              Column('population', Integer),
              Column('continent', String(2)),
              Column('tld', String(10)),
              Column('currency_code', String(3)),
              Column('currency_name', String(20)),
              Column('phone', String(20)),
              Column('postal_code_format', String(100)),
              Column('postal_code_regex', String(200)),
              Column('languages', String(200)),
              Column('geonameid', Integer),
              Column('neighbors', String(100)),
              Column('equivalent_fips_code', String(10)))

        Table('admin1_codes', metadata,
              Column('code', String(20), primary_key=True),
              Column('name', String(200)),
              Column('name_ascii', String(200)),
              Column('geonameid', Integer))

        Table('admin2_codes', metadata,
              Column('code', String(80), primary_key=True),
              Column('name', String(200)),
              Column('name_ascii', String(200)),
              Column('geonameid', Integer))

        Table('feature_codes', metadata,
              Column('code', String(10), primary_key=True),
              Column('name', String(200)),
              Column('description', Text))

        Table('time_zones', metadata,
              Column('country_code', String(2), primary_key=True),
              Column('time_zone_id', String(200), primary_key=True),
              Column('gmt_offset', Float),
              Column('dst_offset', Float),
              Column('raw_offset', Float))

        metadata.create_all(engine)

    @classmethod
    def load_geonames_tables(cls, engine, data_dir: str) -> None:
        """
        Populate the Geonames tables with data.

        :param engine: SQLAlchemy engine
        :param data_dir: Directory containing the Geonames data files
        """
        import csv

        with engine.connect() as connection:
            for table_name, file_name in cls.geonames_files.items():
                table = Table(table_name.replace('.txt', '').replace('.zip', ''), MetaData(), autoload_with=engine)
                file_path = os.path.join(data_dir, file_name)

                print(f"Populating {table_name}...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f, delimiter='\t')
                    columns = [c.key for c in table.columns]
                    for row in csv_reader:
                        if not row[0].startswith('#'):
                            data = dict(zip(columns, row))
                            connection.execute(table.insert().values(**data))

                print(f"Finished populating {table_name}")

    def geocode_simple(self, session: Session, name: str) -> None:
        """
        Geocode a name using the Geonames data and store the result.

        :param session: SQLAlchemy session
        :param name: The name to geocode
        """
        geoname_table = Table('geoname', MetaData(), autoload_with=session.bind)
        result = session.query(geoname_table).filter(geoname_table.c.name.ilike(name)).first()

        if result:
            self.latitude = result.latitude
            self.longitude = result.longitude
            self.place_name = result.name
            self.place_description = f"Country: {result.country_code}, Feature: {result.feature_class}.{result.feature_code}"
            self.set_coordinates(self.latitude, self.longitude)
        else:
            print(f"No geocoding result found for name: {name}")

    def geocode(self, session: Session, name: str, admin1: str = None, admin2: str = None,
                return_multiple: bool = False, max_results: int = 5) -> Union['PlaceMixin', List['PlaceMixin']]:
        """
        Geocode a place name using the Geonames data.

        :param session: SQLAlchemy session
        :param name: The place name to geocode
        :param admin1: Admin1 code to refine the search
        :param admin2: Admin2 code to refine the search
        :param return_multiple: Whether to return multiple matches
        :param max_results: Maximum number of results to return
        :return: The geocoded PlaceMixin instance(s)
        """
        geoname_table = Table('geoname', MetaData(), autoload_with=session.bind)
        query = session.query(geoname_table).filter(geoname_table.c.name.ilike(f"%{name}%"))

        if admin1:
            query = query.filter(geoname_table.c.admin1_code == admin1)
        if admin2:
            query = query.filter(geoname_table.c.admin2_code == admin2)

        query = query.order_by(geoname_table.c.population.desc()).limit(max_results)
        results = query.all()

        if not results:
            print(f"No geocoding result found for name: {name}")
            return [] if return_multiple else None

        geocoded_places = []
        for result in results:
            place = PlaceMixin()
            place.set_coordinates(result.latitude, result.longitude)
            place.place_name = result.name
            place.place_description = f"Country: {result.country_code}, Feature: {result.feature_class}.{result.feature_code}"
            geocoded_places.append(place)

        return geocoded_places if return_multiple else geocoded_places[0]

    def reverse_geocode_to_place(self, session: Session, latitude: float, longitude: float, radius_km: float = 10) -> Optional['PlaceMixin']:
        """
        Perform reverse geocoding to find the nearest location to the given coordinates.

        :param session: SQLAlchemy session
        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param radius_km: Search radius in kilometers
        :return: The nearest PlaceMixin instance or None if not found
        """
        geoname_table = Table('geoname', MetaData(), autoload_with=session.bind)

        # Approximate degree to km conversion
        radius_deg = radius_km / 111.32

        query = session.query(geoname_table).filter(
            and_(
                geoname_table.c.latitude.between(latitude - radius_deg, latitude + radius_deg),
                geoname_table.c.longitude.between(longitude - radius_deg, longitude + radius_deg)
            )
        ).order_by(
            func.pow(geoname_table.c.latitude - latitude, 2) +
            func.pow(geoname_table.c.longitude - longitude, 2)
        ).first()

        if query:
            self.set_coordinates(query.latitude, query.longitude)
            self.place_name = query.name
            self.place_description = f"Country: {query.country_code}, Feature: {query.feature_class}.{query.feature_code}"
            return self
        else:
            print(f"No reverse geocoding result found for coordinates: {latitude}, {longitude}")
            return None

    def reverse_geocode_to_feature(self, latitude: float, longitude: float,
                        radius_km: float = 10, max_results: int = 1):
        """
        Perform reverse geocoding to find the nearest location(s) to the given coordinates.

        Parameters:
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

        metadata = MetaData(bind=db.session.bind)

        # Reflect tables
        geoname_table = Table('geoname', metadata, autoload_with=db.session.bind)
        country_table = Table('country', metadata, autoload_with=db.session.bind)
        admin1_table = Table('admin1Codes', metadata, autoload_with=db.session.bind)
        admin2_table = Table('admin2Codes', metadata, autoload_with=db.session.bind)
        feature_table = Table('featureCodes', metadata, autoload_with=db.session.bind)
        timezone_table = Table('timeZones', metadata, autoload_with=db.session.bind)

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
        query = db.session.query(
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
            admin1_table,
            func.concat(geoname_table.c.country_code, '.', geoname_table.c.admin1_code) == admin1_table.c.code,
            isouter=True
        ).join(
            admin2_table, func.concat(geoname_table.c.country_code, '.', geoname_table.c.admin1_code, '.',
                                      geoname_table.c.admin2_code) == admin2_table.c.code, isouter=True
        ).join(
            feature_table,
            func.concat(geoname_table.c.feature_class, '.', geoname_table.c.feature_code) == feature_table.c.code,
            isouter=True
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

    def current_location(self):
        """Generate HTML and JavaScript to request the user's current location."""
        return """
        <button onclick="getLocation()">Get Current Location</button>
        <div id="location"></div>
        <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                document.getElementById("location").innerHTML = "Geolocation is not supported by this browser.";
            }
        }

        function showPosition(position) {
            var latitude = position.coords.latitude;
            var longitude = position.coords.longitude;
            document.getElementById("location").innerHTML = 
                "Latitude: " + latitude + 
                "<br>Longitude: " + longitude;
            // Optionally, set these to your model's latitude and longitude fields
            // For example:
            // document.getElementById('latitudeField').value = latitude;
            // document.getElementById('longitudeField').value = longitude;
        }

        function showError(error) {
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    document.getElementById("location").innerHTML = "User denied the request for Geolocation."
                    break;
                case error.POSITION_UNAVAILABLE:
                    document.getElementById("location").innerHTML = "Location information is unavailable."
                    break;
                case error.TIMEOUT:
                    document.getElementById("location").innerHTML = "The request to get user location timed out."
                    break;
                case error.UNKNOWN_ERROR:
                    document.getElementById("location").innerHTML = "An unknown error occurred."
                    break;
            }
        }
        </script>
        """

    def __repr__(self) -> str:
        """
        String representation of the place.

        :return: String representation
        """
        return f"<Place: {self.place_name} ({self.latitude}, {self.longitude})>"
