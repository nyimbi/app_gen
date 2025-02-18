"""
geo_location_mixin.py

This module provides a GeoLocationMixin class for implementing geolocation
capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The GeoLocationMixin adds support for storing geographic coordinates,
performing distance calculations, and executing geospatial queries.

Dependencies:
    - SQLAlchemy >= 1.4.0
    - Flask-AppBuilder >= 4.0.0
    - GeoAlchemy2 >= 0.10.0
    - Shapely >= 2.0.0
    - geopy >= 2.0.0
    - psycopg2-binary >= 2.9.0
    - PostgreSQL >= 12.0 with PostGIS extension

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from flask_appbuilder import Model
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from shapely.geometry import Point, mapping
from sqlalchemy import Column, Float, Index, func, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import UserDefinedType

logger = logging.getLogger(__name__)


class GeoLocationMixin:
    """
    A mixin class for adding geolocation capabilities to SQLAlchemy models.

    This mixin provides methods for storing and querying geographic coordinates,
    calculating distances, and performing geospatial operations.

    Attributes:
        latitude (Column): Latitude coordinate (-90 to 90)
        longitude (Column): Longitude coordinate (-180 to 180)
        location (Column): PostGIS geometry point for spatial indexing
        altitude (Column): Optional altitude in meters
        accuracy (Column): Optional accuracy radius in meters
        timestamp (Column): Optional timestamp of location fix

    Indexes:
        - Spatial index on location column
        - Composite index on lat/long columns
    """

    @declared_attr
    def latitude(cls):
        """Latitude in decimal degrees, range -90 to 90"""
        return Column(
            Float(precision=9),
            nullable=True,
            default=0.0,
            info={
                "label": "Latitude",
                "validators": [lambda x: -90 <= x <= 90 if x is not None else True],
            },
        )

    @declared_attr
    def longitude(cls):
        """Longitude in decimal degrees, range -180 to 180"""
        return Column(
            Float(precision=9),
            nullable=True,
            default=0.0,
            info={
                "label": "Longitude",
                "validators": [lambda x: -180 <= x <= 180 if x is not None else True],
            },
        )

    @declared_attr
    def location(cls):
        """PostGIS geometry point with spatial index"""
        return Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True))

    @declared_attr
    def altitude(cls):
        """Optional altitude in meters above sea level"""
        return Column(Float(precision=6), nullable=True, info={"label": "Altitude (m)"})

    @declared_attr
    def accuracy(cls):
        """Optional accuracy radius in meters"""
        return Column(Float(precision=6), nullable=True, info={"label": "Accuracy (m)"})

    @declared_attr
    def timestamp(cls):
        """Optional timestamp of location fix"""
        return Column(func.now(), nullable=True, info={"label": "Timestamp"})

    @classmethod
    def __declare_last__(cls):
        """Setup database triggers and event listeners"""
        from sqlalchemy import event

        # Create spatial index
        Index(
            f"idx_{cls.__tablename__}_location", cls.location, postgresql_using="gist"
        )

        # Create composite lat/long index
        Index(f"idx_{cls.__tablename__}_lat_long", cls.latitude, cls.longitude)

        @event.listens_for(cls, "before_insert")
        @event.listens_for(cls, "before_update")
        def receive_before_save(mapper, connection, instance):
            """Update PostGIS point when lat/long change"""
            try:
                if instance.latitude is not None and instance.longitude is not None:
                    if not (-90 <= instance.latitude <= 90):
                        raise ValueError(f"Invalid latitude: {instance.latitude}")
                    if not (-180 <= instance.longitude <= 180):
                        raise ValueError(f"Invalid longitude: {instance.longitude}")
                    point = Point(instance.longitude, instance.latitude)
                    instance.location = from_shape(point, srid=4326)
                    instance.timestamp = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error updating location: {str(e)}")
                raise

    def set_coordinates(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        accuracy: Optional[float] = None,
    ) -> None:
        """
        Set the geographic coordinates for this instance.

        Args:
            latitude: Decimal degrees latitude (-90 to 90)
            longitude: Decimal degrees longitude (-180 to 180)
            altitude: Optional altitude in meters
            accuracy: Optional accuracy radius in meters

        Raises:
            ValueError: If coordinates are invalid
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}")

        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.accuracy = accuracy
        self.timestamp = datetime.utcnow()

        point = Point(longitude, latitude)
        self.location = from_shape(point, srid=4326)

    @classmethod
    def get_by_coordinates(
        cls,
        session,
        latitude: float,
        longitude: float,
        distance_km: float = 1.0,
        limit: Optional[int] = None,
        order_by_distance: bool = True,
    ) -> List[Any]:
        """
        Find instances within a specified radius of given coordinates.

        Args:
            session: SQLAlchemy session
            latitude: Center point latitude
            longitude: Center point longitude
            distance_km: Search radius in kilometers (default 1km)
            limit: Optional limit on number of results
            order_by_distance: Order results by distance from center

        Returns:
            List of instances within the specified distance

        Raises:
            ValueError: If coordinates or distance are invalid
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}")
        if distance_km <= 0:
            raise ValueError(f"Invalid distance: {distance_km}")

        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        query = session.query(cls)

        # Calculate distance and filter
        distance_clause = (
            func.ST_Distance(
                func.ST_Transform(cls.location, 3857), func.ST_Transform(point, 3857)
            )
            <= distance_km * 1000
        )  # Convert km to meters

        query = query.filter(distance_clause)

        if order_by_distance:
            query = query.order_by(func.ST_Distance(cls.location, point))

        if limit:
            query = query.limit(limit)

        return query.all()

    def distance_to(
        self, other: Union[Tuple[float, float], Any], method: str = "geodesic"
    ) -> float:
        """
        Calculate the distance to another instance or coordinates.

        Args:
            other: Another instance of this class or tuple of (latitude, longitude)
            method: Distance calculation method ('geodesic', 'haversine', or 'postgis')

        Returns:
            Distance in kilometers

        Raises:
            ValueError: If coordinates are invalid or method unknown
        """
        if isinstance(other, tuple):
            other_lat, other_lon = other
            if not (-90 <= other_lat <= 90):
                raise ValueError(f"Invalid latitude: {other_lat}")
            if not (-180 <= other_lon <= 180):
                raise ValueError(f"Invalid longitude: {other_lon}")
        else:
            other_lat, other_lon = other.latitude, other.longitude

        if method == "geodesic":
            return geodesic(
                (self.latitude, self.longitude), (other_lat, other_lon)
            ).kilometers
        elif method == "haversine":
            return self.haversine_distance(
                self.latitude, self.longitude, other_lat, other_lon
            )
        elif method == "postgis":
            if not hasattr(self, "location") or not self.location:
                raise ValueError("PostGIS location not available")
            return (
                func.ST_Distance(
                    func.ST_Transform(self.location, 3857),
                    func.ST_Transform(
                        func.ST_SetSRID(func.ST_MakePoint(other_lon, other_lat), 4326),
                        3857,
                    ),
                )
                / 1000
            )  # Convert meters to km
        else:
            raise ValueError(f"Unknown distance calculation method: {method}")

    @classmethod
    def geocode_address(
        cls, address: str, timeout: int = 10, exactly_one: bool = True
    ) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to get latitude and longitude.

        Args:
            address: The address to geocode
            timeout: Timeout in seconds
            exactly_one: Return only the first result

        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails

        Raises:
            GeocoderTimedOut: If geocoding request times out
            GeocoderServiceError: If geocoding service fails
        """
        try:
            geolocator = Nominatim(user_agent="flask-appbuilder")
            location = geolocator.geocode(
                address, timeout=timeout, exactly_one=exactly_one
            )
            if location:
                return location.latitude, location.longitude
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for {address}: {str(e)}")
            raise

    @classmethod
    def reverse_geocode(
        cls, latitude: float, longitude: float, timeout: int = 10, language: str = "en"
    ) -> Optional[str]:
        """
        Reverse geocode coordinates to get an address.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            timeout: Timeout in seconds
            language: Preferred language for results

        Returns:
            Address string or None if reverse geocoding fails

        Raises:
            ValueError: If coordinates are invalid
            GeocoderTimedOut: If geocoding request times out
            GeocoderServiceError: If geocoding service fails
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}")

        try:
            geolocator = Nominatim(user_agent="flask-appbuilder")
            location = geolocator.reverse(
                f"{latitude}, {longitude}", timeout=timeout, language=language
            )
            if location:
                return location.address
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(
                f"Reverse geocoding error for ({latitude}, {longitude}): {str(e)}"
            )
            raise

    def to_geojson(self, include_props: bool = True) -> Dict[str, Any]:
        """
        Convert the instance to a GeoJSON feature.

        Args:
            include_props: Whether to include model properties

        Returns:
            GeoJSON feature representation of the instance
        """
        if not all([self.latitude, self.longitude]):
            raise ValueError("Instance missing coordinates")

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
            "properties": {
                "id": getattr(self, "id", None),
                "altitude": self.altitude,
                "accuracy": self.accuracy,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            },
        }

        if include_props:
            # Add all public attributes
            for key, value in self.__dict__.items():
                if not key.startswith("_") and key not in [
                    "latitude",
                    "longitude",
                    "location",
                    "altitude",
                    "accuracy",
                    "timestamp",
                ]:
                    feature["properties"][key] = value

        return feature

    @classmethod
    def from_geojson(cls, feature: Dict[str, Any]) -> "GeoLocationMixin":
        """
        Create an instance from a GeoJSON feature.

        Args:
            feature: GeoJSON feature dictionary

        Returns:
            New instance with coordinates set from the feature

        Raises:
            ValueError: If feature is invalid or missing required data
        """
        if not isinstance(feature, dict):
            raise ValueError("Invalid GeoJSON: must be a dictionary")

        if feature.get("type") != "Feature":
            raise ValueError("Invalid GeoJSON: must be a Feature")

        geometry = feature.get("geometry", {})
        if geometry.get("type") != "Point":
            raise ValueError("Invalid GeoJSON: geometry must be a Point")

        coords = geometry.get("coordinates", [])
        if len(coords) < 2:
            raise ValueError("Invalid GeoJSON: coordinates must have at least 2 values")

        instance = cls()
        instance.set_coordinates(
            latitude=coords[1],
            longitude=coords[0],
            altitude=coords[2] if len(coords) > 2 else None,
        )

        # Set properties
        properties = feature.get("properties", {})
        for key, value in properties.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        return instance

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points using the haversine formula.

        Args:
            lat1, lon1: Latitude and longitude of the first point
            lat2, lon2: Latitude and longitude of the second point

        Returns:
            Distance between points in kilometers

        Raises:
            ValueError: If coordinates are invalid
        """
        if not all(-90 <= lat <= 90 for lat in [lat1, lat2]):
            raise ValueError("Invalid latitude")
        if not all(-180 <= lon <= 180 for lon in [lon1, lon2]):
            raise ValueError("Invalid longitude")

        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    @classmethod
    def get_bounding_box(
        cls, center_lat: float, center_lon: float, distance_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate a bounding box given a center point and distance.

        Args:
            center_lat: Latitude of the center point
            center_lon: Longitude of the center point
            distance_km: Distance from center point in kilometers

        Returns:
            Tuple of (min_lat, min_lon, max_lat, max_lon)

        Raises:
            ValueError: If coordinates or distance are invalid
        """
        if not (-90 <= center_lat <= 90):
            raise ValueError(f"Invalid latitude: {center_lat}")
        if not (-180 <= center_lon <= 180):
            raise ValueError(f"Invalid longitude: {center_lon}")
        if distance_km <= 0:
            raise ValueError(f"Invalid distance: {distance_km}")

        # Approximate degrees latitude per km
        lat_change = distance_km / 111.32

        # Approximate degrees longitude per km at given latitude
        lon_change = distance_km / (111.32 * math.cos(math.radians(center_lat)))

        min_lat = max(center_lat - lat_change, -90)
        max_lat = min(center_lat + lat_change, 90)
        min_lon = center_lon - lon_change
        max_lon = center_lon + lon_change

        # Handle longitude wraparound
        if min_lon < -180:
            min_lon = min_lon + 360
        if max_lon > 180:
            max_lon = max_lon - 360

        return (min_lat, min_lon, max_lat, max_lon)

    @classmethod
    def get_by_bounding_box(
        cls, session, min_lat: float, min_lon: float, max_lat: float, max_lon: float
    ) -> List[Any]:
        """
        Find all instances within a bounding box.

        Args:
            session: SQLAlchemy session
            min_lat, min_lon: Minimum latitude and longitude
            max_lat, max_lon: Maximum latitude and longitude

        Returns:
            List of instances within the bounding box

        Raises:
            ValueError: If coordinates are invalid
        """
        if not all(-90 <= lat <= 90 for lat in [min_lat, max_lat]):
            raise ValueError("Invalid latitude range")
        if not all(-180 <= lon <= 180 for lon in [min_lon, max_lon]):
            raise ValueError("Invalid longitude range")

        bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        return session.query(cls).filter(func.ST_Within(cls.location, bbox)).all()


# Example usage remains the same as in original
