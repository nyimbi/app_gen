"""
geo_location_mixin.py

This module provides a GeoLocationMixin class for implementing geolocation
capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The GeoLocationMixin adds support for storing geographic coordinates,
performing distance calculations, and executing geospatial queries.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - GeoAlchemy2
    - Shapely
    - geopy

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Float, func
from sqlalchemy.ext.declarative import declared_attr
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import math

class GeoLocationMixin:
    """
    A mixin class for adding geolocation capabilities to SQLAlchemy models.

    This mixin provides methods for storing and querying geographic coordinates,
    calculating distances, and performing geospatial operations.

    Attributes:
        latitude (Column): Latitude coordinate.
        longitude (Column): Longitude coordinate.
        location (Column): Geometry point for efficient spatial indexing.
    """

    @declared_attr
    def latitude(cls):
        return Column(Float)

    @declared_attr
    def longitude(cls):
        return Column(Float)

    @declared_attr
    def location(cls):
        return Column(Geometry(geometry_type='POINT', srid=4326))

    @classmethod
    def __declare_last__(cls):
        from sqlalchemy import event

        @event.listens_for(cls, 'before_insert')
        @event.listens_for(cls, 'before_update')
        def receive_before_save(mapper, connection, instance):
            if instance.latitude is not None and instance.longitude is not None:
                point = Point(instance.longitude, instance.latitude)
                instance.location = from_shape(point, srid=4326)

    def set_coordinates(self, latitude, longitude):
        """
        Set the latitude and longitude coordinates for the instance.

        Args:
            latitude (float): Latitude coordinate.
            longitude (float): Longitude coordinate.
        """
        self.latitude = latitude
        self.longitude = longitude
        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)

    @classmethod
    def get_by_coordinates(cls, session, latitude, longitude, distance_km=1):
        """
        Find instances within a specified distance of given coordinates.

        Args:
            session: SQLAlchemy session.
            latitude (float): Latitude of the center point.
            longitude (float): Longitude of the center point.
            distance_km (float): Radius in kilometers to search within.

        Returns:
            list: Instances within the specified distance.
        """
        point = func.ST_GeomFromText(f'POINT({longitude} {latitude})', 4326)
        return session.query(cls).filter(
            func.ST_DWithin(
                cls.location,
                point,
                distance_km / 111.32  # Approximate degrees to km conversion
            )
        ).all()

    def distance_to(self, other):
        """
        Calculate the distance to another instance or coordinates.

        Args:
            other: Another instance of this class or a tuple of (latitude, longitude).

        Returns:
            float: Distance in kilometers.
        """
        if isinstance(other, tuple):
            other_lat, other_lon = other
        else:
            other_lat, other_lon = other.latitude, other.longitude
        
        return geodesic(
            (self.latitude, self.longitude),
            (other_lat, other_lon)
        ).kilometers

    @classmethod
    def geocode_address(cls, address):
        """
        Geocode an address to get latitude and longitude.

        Args:
            address (str): The address to geocode.

        Returns:
            tuple: (latitude, longitude) or None if geocoding fails.
        """
        geolocator = Nominatim(user_agent="myapp")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None

    @classmethod
    def reverse_geocode(cls, latitude, longitude):
        """
        Reverse geocode coordinates to get an address.

        Args:
            latitude (float): Latitude coordinate.
            longitude (float): Longitude coordinate.

        Returns:
            str: Address string or None if reverse geocoding fails.
        """
        geolocator = Nominatim(user_agent="myapp")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        if location:
            return location.address
        return None

    def to_geojson(self):
        """
        Convert the instance to a GeoJSON feature.

        Returns:
            dict: GeoJSON feature representation of the instance.
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": self.id,
                # Add other relevant properties here
            }
        }

    @classmethod
    def from_geojson(cls, feature):
        """
        Create an instance from a GeoJSON feature.

        Args:
            feature (dict): GeoJSON feature.

        Returns:
            GeoLocationMixin: New instance with coordinates set from the feature.
        """
        coords = feature['geometry']['coordinates']
        instance = cls()
        instance.set_coordinates(latitude=coords[1], longitude=coords[0])
        # Set other properties as needed
        return instance

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on the Earth.

        Args:
            lat1, lon1: Latitude and longitude of the first point.
            lat2, lon2: Latitude and longitude of the second point.

        Returns:
            float: Distance between the points in kilometers.
        """
        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        return distance

    @classmethod
    def get_bounding_box(cls, center_lat, center_lon, distance_km):
        """
        Calculate a bounding box given a center point and distance.

        Args:
            center_lat (float): Latitude of the center point.
            center_lon (float): Longitude of the center point.
            distance_km (float): Distance from the center point in kilometers.

        Returns:
            tuple: (min_lat, min_lon, max_lat, max_lon)
        """
        # Approximate degrees latitude per km
        lat_change = distance_km / 111.32
        # Approximate degrees longitude per km at given latitude
        lon_change = distance_km / (111.32 * math.cos(math.radians(center_lat)))

        min_lat = center_lat - lat_change
        max_lat = center_lat + lat_change
        min_lon = center_lon - lon_change
        max_lon = center_lon + lon_change

        return (min_lat, min_lon, max_lat, max_lon)

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.geo_location_mixin import GeoLocationMixin

class Place(GeoLocationMixin, Model):
    __tablename__ = 'nx_places'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

# In your application code:

# Create a new place
new_york = Place(name="New York City")
new_york.set_coordinates(40.7128, -74.0060)
db.session.add(new_york)
db.session.commit()

# Find places within 100km of a point
nearby_places = Place.get_by_coordinates(db.session, 40.7128, -74.0060, distance_km=100)

# Calculate distance between two places
london = Place(name="London")
london.set_coordinates(51.5074, -0.1278)
distance = new_york.distance_to(london)
print(f"Distance between New York and London: {distance:.2f} km")

# Geocode an address
coords = Place.geocode_address("Eiffel Tower, Paris, France")
if coords:
    eiffel_tower = Place(name="Eiffel Tower")
    eiffel_tower.set_coordinates(*coords)
    db.session.add(eiffel_tower)
    db.session.commit()

# Reverse geocode
address = Place.reverse_geocode(48.8584, 2.2945)
print(f"Address of the Eiffel Tower: {address}")

# Convert to GeoJSON
geojson_feature = new_york.to_geojson()

# Create from GeoJSON
geojson_data = {
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [-0.1276, 51.5074]
    },
    "properties": {
        "name": "Big Ben"
    }
}
big_ben = Place.from_geojson(geojson_data)
big_ben.name = geojson_data['properties']['name']
db.session.add(big_ben)
db.session.commit()

# Get bounding box
bbox = Place.get_bounding_box(40.7128, -74.0060, 10)
print(f"Bounding box for 10km around New York: {bbox}")
"""
