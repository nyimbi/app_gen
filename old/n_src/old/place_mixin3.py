#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Nyimbi Odero
"""


from __future__ import annotations
from typing import List, Tuple, Optional, Union, Dict, Any
from sqlalchemy import Column, String, Integer, BigInteger, Date, Text, Float, Boolean, Table, MetaData, and_, func
from sqlalchemy.orm import Session, declared_attr
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

class PlaceMixin(Model):
    """
    A comprehensive mixin for Flask-AppBuilder models that provides extensive geographical information and operations.

    This mixin offers a wide range of geographical functionalities including data storage, geocoding, distance calculations,
    mapping, and integration with various geographical services and APIs.

    Attributes:
        place_name (Column): Name of the place.
        place_description (Column): Description of the place.
        latitude (Column): Latitude coordinate.
        longitude (Column): Longitude coordinate.
        altitude (Column): Altitude of the place.
        geometry (Column): Geometry data of the place.
        map (Column): Map representation.
        info (Column): Additional information about the place.
        pin (Column): Boolean indicating if the place should be pinned on a map.
        pin_color (Column): Color of the pin if used.
        pin_icon (Column): Icon for the pin if used.
        centered (Column): Boolean indicating if the place should be centered on a map.
        nearest_feature (Column): Nearest geographical feature.
        crs (Column): Coordinate Reference System.
    """

    __abstract__ = True

    @declared_attr
    def place_name(cls):
        return Column(String(100))

    @declared_attr
    def place_description(cls):
        return Column(Text)

    @declared_attr
    def latitude(cls):
        return Column(Float)

    @declared_attr
    def longitude(cls):
        return Column(Float)

    @declared_attr
    def altitude(cls):
        return Column(Float)

    @declared_attr
    def geometry(cls):
        return Column(Geometry(geometry_type='POINT', srid=4326))

    @declared_attr
    def map(cls):
        return Column(Text, default="")

    @declared_attr
    def info(cls):
        return Column(Text, default="")

    @declared_attr
    def pin(cls):
        return Column(Boolean)

    @declared_attr
    def pin_color(cls):
        return Column(String(20))

    @declared_attr
    def pin_icon(cls):
        return Column(String(50))

    @declared_attr
    def centered(cls):
        return Column(Boolean)

    @declared_attr
    def nearest_feature(cls):
        return Column(String(100))

    @declared_attr
    def crs(cls):
        return Column(String(20), default="EPSG:4326")

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

        Args:
            latitude (float): Latitude in degrees.
            longitude (float): Longitude in degrees.
            altitude (float, optional): Altitude in meters.

        Returns:
            PlaceMixin: The instance itself for method chaining.

        Raises:
            ValueError: If latitude or longitude is invalid.
        """
        self.validate_latitude(latitude)
        self.validate_longitude(longitude)
        self.latitude = latitude
        self.longitude = longitude
        if altitude is not None:
            self.altitude = altitude
        self.geometry = f'POINT({longitude} {latitude})'
        return self

    @staticmethod
    def validate_latitude(latitude: float) -> None:
        """
        Validate the given latitude value.

        Args:
            latitude (float): Latitude value to validate.

        Raises:
            ValueError: If latitude is not between -90 and 90 degrees.
        """
        if not -90 <= latitude <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')

    @staticmethod
    def validate_longitude(longitude: float) -> None:
        """
        Validate the given longitude value.

        Args:
            longitude (float): Longitude value to validate.

        Raises:
            ValueError: If longitude is not between -180 and 180 degrees.
        """
        if not -180 <= longitude <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')

    def validate(self) -> None:
        """
        Validate the place's coordinates.

        Raises:
            ValueError: If coordinates are invalid.
        """
        self.validate_latitude(self.latitude)
        self.validate_longitude(self.longitude)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the place to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing the place's attributes.
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

        Args:
            data (Dict[str, Any]): Dictionary containing place attributes.

        Returns:
            PlaceMixin: The instance itself for method chaining.
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

        Returns:
            Dict[str, Any]: GeoJSON feature dictionary.
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
    def from_geojson(cls, geojson: Dict[str, Any]) -> PlaceMixin:
        """
        Create a PlaceMixin instance from a GeoJSON feature.

        Args:
            geojson (Dict[str, Any]): GeoJSON feature dictionary.

        Returns:
            PlaceMixin: A new instance of PlaceMixin.
        """
        instance = cls()
        coords = geojson['geometry']['coordinates']
        instance.set_coordinates(coords[1], coords[0])

        for key, value in geojson['properties'].items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        return instance

    @classmethod
    def to_geojson_collection(cls, instances: List[PlaceMixin]) -> Dict[str, Any]:
        """
        Convert a list of PlaceMixin instances to a GeoJSON FeatureCollection.

        Args:
            instances (List[PlaceMixin]): List of PlaceMixin instances.

        Returns:
            Dict[str, Any]: GeoJSON FeatureCollection dictionary.
        """
        return {
            "type": "FeatureCollection",
            "features": [instance.to_geojson() for instance in instances]
        }

    def to_kml(self) -> str:
        """
        Convert the place to a KML Placemark.

        Returns:
            str: KML Placemark string.
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
    def bulk_import_geojson(cls, geojson_data: Dict[str, Any]) -> List[PlaceMixin]:
        """
        Bulk import places from a GeoJSON FeatureCollection.

        Args:
            geojson_data (Dict[str, Any]): GeoJSON FeatureCollection dictionary.

        Returns:
            List[PlaceMixin]: List of created PlaceMixin instances.
        """
        return [cls.from_geojson(feature) for feature in geojson_data['features']]

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on the earth using the Haversine formula.

        Args:
            lat1 (float): Latitude of the first point.
            lon1 (float): Longitude of the first point.
            lat2 (float): Latitude of the second point.
            lon2 (float): Longitude of the second point.

        Returns:
            float: Distance in kilometers.
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

        Args:
            lat1 (float): Latitude of the first point.
            lon1 (float): Longitude of the first point.
            lat2 (float): Latitude of the second point.
            lon2 (float): Longitude of the second point.

        Returns:
            float: Distance in kilometers.
        """
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    @staticmethod
    def great_circle_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the earth's surface.

        Args:
            lat1 (float): Latitude of the first point.
            lon1 (float): Longitude of the first point.
            lat2 (float): Latitude of the second point.
            lon2 (float): Longitude of the second point.

        Returns:
            float: Distance in kilometers.
        """
        return great_circle((lat1, lon1), (lat2, lon2)).kilometers

    def distance_to(self, other: Union[PlaceMixin, Tuple[float, float]], method: str = 'haversine') -> float:
        """
        Calculate the distance to another place or coordinates using the specified method.

        Args:
            other (Union[PlaceMixin, Tuple[float, float]]): Another PlaceMixin instance or a tuple of (latitude, longitude).
            method (str): Distance calculation method ('haversine', 'geodesic', or 'great_circle').

        Returns:
            float: Distance in kilometers.

        Raises:
            ValueError: If an invalid method is specified.
        """
        if isinstance(other, tuple):
            other_lat, other_lon = other
        else:
            other_lat, other_lon = other.latitude, other.longitude

        distance_methods = {
            'haversine': self.haversine,
            'geodesic': self.geodesic_distance,
            'great_circle': self.great_circle_distance
        }

        if method not in distance_methods:
            raise ValueError(f"Invalid distance calculation method: {method}")

        return distance_methods[method](self.latitude, self.longitude, other_lat, other_lon)

    def find_places_in_polygon(self, polygon_coords: List[Tuple[float, float]], session: Session) -> List[PlaceMixin]:
        """
        Find all places within a given polygon.

        Args:
            polygon_coords (List[Tuple[float, float]]): List of (longitude, latitude) tuples defining the polygon.
            session (Session): SQLAlchemy session.

        Returns:
            List[PlaceMixin]: List of places within the polygon.
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

        Args:
            lat (float): Latitude of the center point.
            lon (float): Longitude of the center point.
            distance_km (float): Radius in kilometers.

        Returns:
            bool: True if the place is within the fence, False otherwise.
        """
        point = Point(lon, lat)
        place_point = to_shape(self.geometry)
        return place_point.distance(point) <= distance_km / 111.32  # Approximate degrees to km conversion

    @staticmethod
    def transform_coordinates(from_crs: str, to_crs: str, lon: float, lat: float) -> Tuple[float, float]:
        """
        Transform coordinates from one CRS to another.

        Args:
            from_crs (str): Source coordinate reference system (e.g., 'EPSG:4326').
            to_crs (str): Target coordinate reference system.
            lon (float): Longitude in the source CRS.
            lat (float): Latitude in the source CRS.

        Returns:
            Tuple[float, float]: (longitude, latitude) in the target CRS.
        """
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        return transformer.transform(lon, lat)

    def set_coordinates_in_crs(self, lon: float, lat: float, from_crs: str = 'EPSG:4326') -> PlaceMixin:
        """
        Set the place's coordinates, transforming them from the given CRS to WGS84 if necessary.

        Args:
            lon (float): Longitude in the source CRS.
            lat (float): Latitude in the source CRS.
            from_crs (str): Source coordinate reference system (default is WGS84).

        Returns:
            PlaceMixin: The instance itself for method chaining.
        """
        if from_crs != 'EPSG:4326':
            lon, lat = self.transform_coordinates(from_crs, 'EPSG:4326', lon, lat)

        return self.set_coordinates(lat, lon)

    def generate_leaflet_map(self, zoom: int = 13, marker: bool = True) -> str:
        """
        Generate HTML and JavaScript for a Leaflet map centered on this place.

        Args:
            zoom (int): The zoom level for the map.
            marker (bool): Whether to place a marker on the map at the location.

        Returns:
            str: HTML and JavaScript code for embedding the Leaflet map.
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

        Args:
            zoom (int): The zoom level for the map.
            marker (bool): Whether to place a marker on the map at the location.

        Returns:
            str: HTML and JavaScript code for embedding the OpenLayers map.
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

        Args:
            mapbox_access_token (str): Mapbox access token.
            zoom (int): The zoom level for the map.

        Returns:
            str: HTML and JavaScript code for embedding the Mapbox GL JS map.
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

        Args:
            mapbox_access_token (str): Mapbox access token.
            width (int): Width of the image in pixels.
            height (int): Height of the image in pixels.
            zoom (int): The zoom level for the map.

        Returns:
            str: URL of the static map image.
        """
        base_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static"
        marker = f"pin-s+ff0000({self.longitude},{self.latitude})"
        center = f"{self.longitude},{self.latitude}"

        static_map_url = f"{base_url}/{marker}/{center},{zoom}/{width}x{height}?access_token={mapbox_access_token}"

        return static_map_url

    def save_static_map(self, mapbox_access_token: str, file_path: str, width: int = 600, height: int = 400, zoom: int = 13) -> None:
        """
        Save a static map image to a file.

        Args:
            mapbox_access_token (str): Mapbox access token.
            file_path (str): Path to save the image file.
            width (int): Width of the image in pixels.
            height (int): Height of the image in pixels.
            zoom (int): The zoom level for the map.

        Raises:
            IOError: If unable to save the file.
        """
        static_map_url = self.generate_static_map(mapbox_access_token, width, height, zoom)
        response = requests.get(static_map_url)

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Static map saved to {file_path}")
        else:
            raise IOError(f"Failed to generate static map.")
    #####
    def calculate_route_online(self, destination: PlaceMixin) -> List[Tuple[float, float]]:
        """
        Calculate a route to a destination using an online routing service (OSRM).

        Args:
            destination (PlaceMixin): The destination place.

        Returns:
            List[Tuple[float, float]]: List of coordinates representing the route.
        """
        url = f"http://router.project-osrm.org/route/v1/driving/{self.longitude},{self.latitude};{destination.longitude},{destination.latitude}?overview=full&geometries=geojson"
        response = requests.get(url)
        data = response.json()
        return data['routes'][0]['geometry']['coordinates']

    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_route_batch(locations: Tuple[PlaceMixin, ...], osrm_base_url: str = "http://localhost:5000") -> Optional[Dict[str, Any]]:
        """
        Calculate a route passing through a batch of locations using OSRM.

        Args:
            locations (Tuple[PlaceMixin, ...]): Tuple of PlaceMixin instances to route through.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails.
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

        Args:
            destination (PlaceMixin): The destination instance.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails.
        """
        return self.calculate_route_batch((self, destination), osrm_base_url)

    def calculate_optimal_route(self, destinations: List[PlaceMixin], osrm_base_url: str = "http://localhost:5000") -> Optional[Dict[str, Any]]:
        """
        Calculate the optimal route through multiple destinations, including this location.

        Args:
            destinations (List[PlaceMixin]): The destination instances to include in the route.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing the route's coordinates, distance, and duration, or None if route calculation fails.
        """
        locations = tuple([self] + destinations)
        return self.calculate_route_batch(locations, osrm_base_url)

    def estimate_travel_time(self, destination: PlaceMixin, speed_kmh: float = 50) -> Optional[float]:
        """
        Estimate the travel time to a destination.

        Args:
            destination (PlaceMixin): The destination instance.
            speed_kmh (float): Average travel speed in kilometers per hour.

        Returns:
            Optional[float]: Estimated travel time in minutes, or None if route calculation fails.
        """
        route = self.calculate_route_to(destination)
        if route:
            return route["duration"] / 60  # Convert seconds to minutes
        return None

    @classmethod
    def precompute_routes(cls, locations: List[PlaceMixin], osrm_base_url: str = "http://localhost:5000") -> Dict[Tuple[PlaceMixin, PlaceMixin], Dict[str, Any]]:
        """
        Precompute and store routes between a set of locations.

        Args:
            locations (List[PlaceMixin]): The list of PlaceMixin instances to route between.
            osrm_base_url (str): The base URL of the OSRM server.

        Returns:
            Dict[Tuple[PlaceMixin, PlaceMixin], Dict[str, Any]]: A dictionary mapping location pairs to their precomputed routes.
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

        Args:
            places (List[PlaceMixin]): A list of PlaceMixin instances to display on the map.
            map_type (str): The type of map to generate ('leaflet' or 'openlayers').
            zoom (int): The zoom level for the map.

        Returns:
            str: HTML and JavaScript code for embedding the map with multiple pins.

        Raises:
            ValueError: If an unsupported map type is specified.
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

        Args:
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

    @classmethod
    def setup_geonames(cls, engine, download_dir: str = 'geonames_data') -> None:
        """
        Download and populate the Geonames database.

        Args:
            engine: SQLAlchemy engine.
            download_dir (str): Directory to store downloaded Geonames files.
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

        Args:
            engine: SQLAlchemy engine.
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

        Args:
            engine: SQLAlchemy engine.
            data_dir (str): Directory containing the Geonames data files.
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

        Args:
            session (Session): SQLAlchemy session.
            name (str): The name to geocode.
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
                return_multiple: bool = False, max_results: int = 5) -> Union[PlaceMixin, List[PlaceMixin]]:
        """
        Geocode a place name using the Geonames data.

        Args:
            session (Session): SQLAlchemy session.
            name (str): The place name to geocode.
            admin1 (str, optional): Admin1 code to refine the search.
            admin2 (str, optional): Admin2 code to refine the search.
            return_multiple (bool): Whether to return multiple matches.
            max_results (int): Maximum number of results to return.

        Returns:
            Union[PlaceMixin, List[PlaceMixin]]: The geocoded PlaceMixin instance(s).
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

    def reverse_geocode(self, session: Session, latitude: float, longitude: float, radius_km: float = 10) -> Optional[PlaceMixin]:
        """
        Perform reverse geocoding to find the nearest location to the given coordinates.

        Args:
            session (Session): SQLAlchemy session.
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            radius_km (float): Search radius in kilometers.

        Returns:
            Optional[PlaceMixin]: The nearest PlaceMixin instance or None if not found.
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

    @classmethod
    def find_closest_instances(cls, latitude: float, longitude: float, n: int = 1, method: str = 'haversine') -> List[PlaceMixin]:
        """
        Find the `n` closest instances to a given latitude and longitude using a specified distance calculation method.

        Args:
            latitude (float): The latitude to compare.
            longitude (float): The longitude to compare.
            n (int): The number of closest instances to return.
            method (str): The distance calculation method ('haversine', 'geodesic', 'great_circle').

        Returns:
            List[PlaceMixin]: The `n` closest PlaceMixin instances.

        Raises:
            ValueError: If an unsupported distance calculation method is specified.
        """
        instances = cls.query.all()
        distances = []

        distance_methods = {
            'haversine': cls.haversine,
            'geodesic': cls.geodesic_distance,
            'great_circle': cls.great_circle_distance
        }

        if method not in distance_methods:
            raise ValueError(f"Unsupported distance calculation method: {method}")

        distance_func = distance_methods[method]

        for instance in instances:
            distance = distance_func(latitude, longitude, instance.latitude, instance.longitude)
            distances.append((instance, distance))

        distances.sort(key=lambda x: x[1])
        return [d[0] for d in distances[:n]]

    def current_location(self) -> str:
        """
        Generate HTML and JavaScript to request the user's current location.

        Returns:
            str: HTML and JavaScript code for getting the user's current location.
        """
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

        Returns:
            str: String representation.
        """
        return f"<Place: {self.place_name} ({self.latitude}, {self.longitude})>"
