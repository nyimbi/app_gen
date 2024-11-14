"""
place_mixin.py: Comprehensive PlaceMixin for Flask-AppBuilder

This module provides a robust PlaceMixin class for use with Flask-AppBuilder models.
It incorporates geographical information, GeoNames data integration, and various
geospatial operations. The mixin is designed to be SQLAlchemy version-agnostic and
uses dynamic table generation techniques.

Features:
1. Geographical data storage and operations
2. GeoNames data integration with selective download and verification
3. Geocoding and reverse geocoding capabilities
4. Distance calculations using various methods
5. Spatial queries and operations
6. Map generation for various mapping libraries
7. Data import/export in multiple formats
8. Comprehensive documentation for all methods and properties

Dependencies:
- Flask-AppBuilder
- SQLAlchemy
- GeoAlchemy2
- Shapely
- Requests
- Matplotlib (optional, for map generation)

Usage:
from flask_appbuilder import Model
from place_mixin import PlaceMixin

class MyPlace(Model, PlaceMixin):
    __tablename__ = 'my_places'
    # Additional fields specific to MyPlace

Note: Ensure that the SETUP_GEONAMES configuration is set in your Flask-AppBuilder
config if you want to use GeoNames data.
"""
import os
import gzip
import json
import hashlib
import zipfile
import math
import requests
import folium
from datetime import datetime
from flask import current_app
from sqlalchemy import func
from typing import List, Tuple, Dict, Any, Optional, Union
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon
from pyproj import Transformer
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, MetaData, inspect
from sqlalchemy.orm import relationship, declared_attr

# Work across both SQLAlchemy 1.x and 2.0
try:
    # SQLAlchemy 2.0
    from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
    SQLALCHEMY_2 = True
except ImportError:
    # SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import declared_attr
    SQLALCHEMY_2 = False



class PlaceMixin:
    """
       A comprehensive mixin for Flask-AppBuilder models that provides extensive
       geographical information and operations.
       """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    if SQLALCHEMY_2:
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        place_name = mapped_column(String(100))
        place_description = mapped_column(String(500))
        latitude = mapped_column(Float)
        longitude = mapped_column(Float)
        altitude = mapped_column(Float)
        geometry = mapped_column(Geometry(geometry_type='POINT', srid=4326))
        country_code = mapped_column(String(2), ForeignKey('nx_geo_country_info.iso_alpha2'))
        admin1_code = mapped_column(String(20))
        admin2_code = mapped_column(String(80))
        feature_code = mapped_column(String(10), ForeignKey('nx_geo_feature_codes.code'))
        timezone = mapped_column(String(200), ForeignKey('nx_geo_timezones.timezoneid'))
    else:
        id = Column(Integer, primary_key=True)
        place_name = Column(String(100))
        place_description = Column(String(500))
        latitude = Column(Float)
        longitude = Column(Float)
        altitude = Column(Float)
        geometry = Column(Geometry(geometry_type='POINT', srid=4326))
        country_code = Column(String(2), ForeignKey('nx_geo_country_info.iso_alpha2'))
        admin1_code = Column(String(20))
        admin2_code = Column(String(80))
        feature_code = Column(String(10), ForeignKey('nx_geo_feature_codes.code'))
        timezone = Column(String(200), ForeignKey('nx_geo_timezones.timezoneid'))

    # Relationships
    country = relationship('NxGeoCountryInfo', foreign_keys=[country_code])
    feature = relationship('NxGeoFeatureCodes', foreign_keys=[feature_code])
    timezone_info = relationship('NxGeoTimezones', foreign_keys=[timezone])

    class GeoNamesSetup:
        """
        Handles the setup and management of GeoNames data.
        """

        GEONAMES_URL = "https://download.geonames.org/export/dump/"
        GEONAMES_FILES = {
            "allCountries.zip": "allCountries.txt",
            "admin1CodesASCII.txt": None,
            "admin2Codes.txt": None,
            "countryInfo.txt": None,
            "alternateNames.zip": "alternateNames.txt",
            "hierarchy.zip": "hierarchy.txt",
            "featureCodes_en.txt": None,
            "timeZones.txt": None,
            "continentCodes.txt": None,
            "postalCodes.zip": "allCountries.txt",
            "iso-languagecodes.txt": None,
        }
        DOWNLOAD_DIR = "geonames_data"
        GEONAMES_MD5_URL = "https://download.geonames.org/export/dump/MD5.txt"

        @classmethod
        def setup(cls, db):
            """
            Main setup method to coordinate the entire GeoNames setup process.

            Args:
                db: SQLAlchemy database instance
            """
            if not cls.is_setup_complete():
                if not cls.tables_exist(db.engine):
                    cls.create_tables(db.engine)

                cls.download_all_files()
                cls.load_all_data(db)
                cls.mark_setup_complete()
            else:
                logger.info("GeoNames setup is already complete.")

        @classmethod
        def is_setup_complete(cls):
            """
            Check if GeoNames setup has been completed.

            Returns:
                bool: True if setup is complete, False otherwise
            """
            return os.path.exists(os.path.join(cls.DOWNLOAD_DIR, '.setup_complete'))

        @classmethod
        def mark_setup_complete(cls):
            """Mark the GeoNames setup as complete."""
            with open(os.path.join(cls.DOWNLOAD_DIR, '.setup_complete'), 'w') as f:
                f.write('Setup completed successfully')

        @classmethod
        def tables_exist(cls, engine):
            """
            Check if GeoNames tables already exist in the database.

            Args:
                engine: SQLAlchemy engine instance

            Returns:
                bool: True if all required tables exist, False otherwise
            """
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            required_tables = [
                'nx_geo_geoname', 'nx_geo_country_info', 'nx_geo_admin1_codes',
                'nx_geo_admin2_codes', 'nx_geo_alternate_names', 'nx_geo_feature_codes',
                'nx_geo_timezones', 'nx_geo_continents', 'nx_geo_postal_codes',
                'nx_geo_language_codes'
            ]
            return all(table in existing_tables for table in required_tables)

        @classmethod
        def create_tables(cls, engine):
            """
            Create GeoNames tables if they don't exist.

            Args:
                engine: SQLAlchemy engine instance
            """
            metadata = MetaData()

            # Define tables here (similar to the previous implementation)
            # Example:
            Table('nx_geo_geoname', metadata,
                  Column('geonameid', Integer, primary_key=True),
                  Column('name', String),
                  Column('asciiname', String),
                  Column('alternatenames', String),
                  Column('latitude', Float),
                  Column('longitude', Float),
                  Column('feature_class', String),
                  Column('feature_code', String),
                  Column('country_code', String),
                  Column('cc2', String),
                  Column('admin1_code', String),
                  Column('admin2_code', String),
                  Column('admin3_code', String),
                  Column('admin4_code', String),
                  Column('population', Integer),
                  Column('elevation', Integer),
                  Column('dem', Integer),
                  Column('timezone', String),
                  Column('modification_date', String))

            # ... Define other tables ...

            metadata.create_all(engine)
            logger.info("Created GeoNames tables.")

        @classmethod
        def download_all_files(cls):
            """Download all required GeoNames files."""
            os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
            for filename in cls.GEONAMES_FILES:
                cls.download_file(filename)

        @classmethod
        def download_file(cls, filename):
            """
            Download a single file, with resume capability.

            Args:
                filename (str): Name of the file to download
            """
            url = cls.GEONAMES_URL + filename
            local_file = os.path.join(cls.DOWNLOAD_DIR, filename)
            temp_file = local_file + '.tmp'

            if os.path.exists(local_file) and cls.verify_file(local_file, filename):
                logger.info(f"{filename} already downloaded and verified.")
                return

            if os.path.exists(temp_file):
                logger.info(f"Resuming download of {filename}")
                mode = 'ab'
                existing_size = os.path.getsize(temp_file)
                headers = {'Range': f'bytes={existing_size}-'}
            else:
                logger.info(f"Starting download of {filename}")
                mode = 'wb'
                existing_size = 0
                headers = {}

            response = requests.get(url, headers=headers, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open(temp_file, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        existing_size += len(chunk)
                        print(f"\rDownloading {filename}: {existing_size}/{total_size} bytes", end='', flush=True)

            print()  # New line after progress

            if cls.verify_file(temp_file, filename):
                os.rename(temp_file, local_file)
                logger.info(f"Successfully downloaded {filename}")
            else:
                logger.error(f"Download of {filename} failed verification. Retrying...")
                os.remove(temp_file)
                cls.download_file(filename)

        @classmethod
        def verify_file(cls, file_path, filename):
            """
            Verify the integrity of the downloaded file using MD5 checksums.

            Args:
                file_path (str): Path to the downloaded file
                filename (str): Name of the file

            Returns:
                bool: True if file is verified, False otherwise
            """
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            expected_md5 = cls.get_expected_md5(filename)
            if not expected_md5:
                logger.error(f"Could not retrieve expected MD5 for {filename}")
                return False

            actual_md5 = cls.calculate_md5(file_path)

            if actual_md5 == expected_md5:
                logger.info(f"File {filename} verified successfully.")
                return True
            else:
                logger.error(f"MD5 mismatch for {filename}. Expected: {expected_md5}, Actual: {actual_md5}")
                return False

        @classmethod
        def get_expected_md5(cls, filename):
            """
            Retrieve the expected MD5 checksum for a file from GeoNames MD5.txt.

            Args:
                filename (str): Name of the file

            Returns:
                str: Expected MD5 checksum or None if not found
            """
            try:
                response = requests.get(cls.GEONAMES_MD5_URL)
                response.raise_for_status()
                md5_content = response.text.splitlines()

                for line in md5_content:
                    if filename in line:
                        return line.split()[0]

                logger.warning(f"MD5 not found for {filename}")
                return None

            except requests.RequestException as e:
                logger.error(f"Error fetching MD5 information: {e}")
                return None

        @staticmethod
        def calculate_md5(file_path):
            """
            Calculate the MD5 checksum of a file.

            Args:
                file_path (str): Path to the file

            Returns:
                str: Calculated MD5 checksum
            """
            md5_hash = hashlib.md5()

            if file_path.endswith('.gz'):
                with gzip.open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
            else:
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)

            return md5_hash.hexdigest()

        @classmethod
        def load_all_data(cls, db):
            """
            Load all downloaded data into the database.

            Args:
                db: SQLAlchemy database instance
            """
            for filename, txt_filename in cls.GEONAMES_FILES.items():
                if txt_filename:
                    cls.load_data(db, filename, txt_filename)
                else:
                    cls.load_data(db, filename, filename)

        @classmethod
        def load_data(cls, db, zip_filename, txt_filename):
            """
            Load data from a file into the corresponding database table.

            Args:
                db: SQLAlchemy database instance
                zip_filename (str): Name of the zip file
                txt_filename (str): Name of the text file inside the zip

            Returns:
                bool: True if data was loaded successfully, False otherwise

            This method handles both zipped and unzipped files. It determines the
            appropriate table name based on the filename, deletes existing data
            from the table, and then bulk loads the new data.
            """
            file_path = os.path.join(cls.DOWNLOAD_DIR, zip_filename)

            try:
                # Handle zipped files
                if zip_filename.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        with zip_ref.open(txt_filename) as f:
                            content = f.read().decode('utf-8')
                else:
                    # Handle unzipped files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                # Determine the table name
                table_name = 'nx_geo_' + txt_filename.split('.')[0]
                if table_name == 'nx_geo_allCountries' and zip_filename == 'postalCodes.zip':
                    table_name = 'nx_geo_postal_codes'
                elif table_name == 'nx_geo_allCountries':
                    table_name = 'nx_geo_geoname'

                logger.info(f"Loading data into {table_name} table...")

                with db.engine.begin() as connection:
                    # Delete existing data
                    connection.execute(f"DELETE FROM {table_name}")

                    # Bulk load new data
                    if db.engine.dialect.name == 'postgresql':
                        # For PostgreSQL, use COPY command
                        connection.execute(
                            f"COPY {table_name} FROM STDIN WITH CSV DELIMITER E'\\t' QUOTE E'\\b' NULL AS ''")
                        connection.execute(content)
                    else:
                        # For other databases, use a more generic approach
                        temp_file = os.path.join(cls.DOWNLOAD_DIR, f'temp_{txt_filename}')
                        with open(temp_file, 'w', encoding='utf-8') as f:
                            f.write(content)

                        table = db.Model.metadata.tables[table_name]
                        with open(temp_file, 'r', encoding='utf-8') as f:
                            columns = [c.key for c in table.columns]
                            connection.execute(
                                table.insert(),
                                [dict(zip(columns, line.strip().split('\t'))) for line in f]
                            )

                        os.remove(temp_file)

                logger.info(f"Finished loading data into {table_name} table.")
                return True

            except Exception as e:
                logger.error(f"Error loading data into {table_name}: {str(e)}")
                return False

            #############

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Initialize subclass and set up GeoNames data if configured.
        """
        super().__init_subclass__(**kwargs)
        try:
            if current_app.config.get('SETUP_GEONAMES', False):
                from flask_appbuilder import db
                cls.GeoNamesSetup.setup(db)
        except RuntimeError:
            # This will occur if there's no application context
            pass

    def set_coordinates(self, latitude: float, longitude: float, altitude: Optional[float] = None) -> 'PlaceMixin':
        """
        Set the geographical coordinates for the place.

        Args:
            latitude (float): Latitude in degrees
            longitude (float): Longitude in degrees
            altitude (float, optional): Altitude in meters

        Returns:
            PlaceMixin: Self for method chaining
        """
        self.latitude = latitude
        self.longitude = longitude
        if altitude is not None:
            self.altitude = altitude
        self.geometry = f'POINT({longitude} {latitude})'
        return self



    def haversine_distance(self, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on the earth using the Haversine formula.

        Args:
            lat2 (float): Latitude of the second point
            lon2 (float): Longitude of the second point

        Returns:
            float: Distance in kilometers
        """
        R = 6371  # Radius of the Earth in km
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def geodesic_distance(self, lat2: float, lon2: float) -> float:
        """
        Calculate the geodesic distance between two points on the earth's surface.

        Args:
            lat2 (float): Latitude of the second point
            lon2 (float): Longitude of the second point

        Returns:
            float: Distance in kilometers
        """
        from geopy import distance
        return distance.geodesic((self.latitude, self.longitude), (lat2, lon2)).km

    def great_circle_distance(self, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on the earth's surface.

        Args:
            lat2 (float): Latitude of the second point
            lon2 (float): Longitude of the second point

        Returns:
            float: Distance in kilometers
        """
        from geopy import distance
        return distance.great_circle((self.latitude, self.longitude), (lat2, lon2)).km

    def nearest_places(self, db, limit: int = 5) -> List['PlaceMixin']:
        """
        Find the nearest places to this location.

        Args:
            db: SQLAlchemy database instance
            limit (int): Maximum number of places to return

        Returns:
            List[PlaceMixin]: List of nearest places
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        query = db.session.query(NxGeoGeoname).order_by(
            func.ST_Distance(
                func.ST_GeomFromText(f'POINT({self.longitude} {self.latitude})', 4326),
                func.ST_GeomFromText(func.concat('POINT(', NxGeoGeoname.c.longitude, ' ', NxGeoGeoname.c.latitude, ')'),
                                     4326)
            )
        ).limit(limit)
        return query.all()

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the place to a GeoJSON feature.

        Returns:
            Dict[str, Any]: GeoJSON feature dictionary
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "name": self.place_name,
                "description": self.place_description,
                "altitude": self.altitude
            }
        }

    @classmethod
    def from_geojson(cls, geojson: Dict[str, Any]) -> 'PlaceMixin':
        """
        Create a new place from a GeoJSON feature.

        Args:
            geojson (Dict[str, Any]): GeoJSON feature dictionary

        Returns:
            PlaceMixin: New PlaceMixin instance
        """
        place = cls()
        place.longitude, place.latitude = geojson['geometry']['coordinates']
        place.place_name = geojson['properties'].get('name')
        place.place_description = geojson['properties'].get('description')
        place.altitude = geojson['properties'].get('altitude')
        return place

    def geocode(self, db, address: str) -> Optional['PlaceMixin']:
        """
        Geocode an address using the GeoNames database.

        Args:
            db: SQLAlchemy database instance
            address (str): Address to geocode

        Returns:
            Optional[PlaceMixin]: Geocoded place or None if not found
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        query = db.session.query(NxGeoGeoname).filter(
            NxGeoGeoname.c.name.ilike(f"%{address}%")
        ).order_by(NxGeoGeoname.c.population.desc()).first()

        if query:
            self.set_coordinates(query.latitude, query.longitude)
            self.place_name = query.name
            self.place_description = f"Country: {query.country_code}, Feature: {query.feature_class}.{query.feature_code}"
            return self
        return None

    def reverse_geocode(self, db, latitude: float, longitude: float) -> Optional['PlaceMixin']:
        """
        Perform reverse geocoding to find the nearest location to the given coordinates.

        Args:
            db: SQLAlchemy database instance
            latitude (float): Latitude of the location
            longitude (float): Longitude of the location

        Returns:
            Optional[PlaceMixin]: Nearest place or None if not found
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        query = db.session.query(NxGeoGeoname).order_by(
            func.ST_Distance(
                func.ST_GeomFromText(f'POINT({longitude} {latitude})', 4326),
                func.ST_GeomFromText(func.concat('POINT(', NxGeoGeoname.c.longitude, ' ', NxGeoGeoname.c.latitude, ')'),
                                     4326)
            )
        ).first()

        if query:
            self.set_coordinates(query.latitude, query.longitude)
            self.place_name = query.name
            self.place_description = f"Country: {query.country_code}, Feature: {query.feature_class}.{query.feature_code}"
            return self
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the place to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing the place's attributes
        """
        return {
            'id': self.id,
            'place_name': self.place_name,
            'place_description': self.place_description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'country_code': self.country_code,
            'admin1_code': self.admin1_code,
            'admin2_code': self.admin2_code,
            'feature_code': self.feature_code,
            'timezone': self.timezone
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaceMixin':
        """
        Create a new place from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing place attributes

        Returns:
            PlaceMixin: New PlaceMixin instance
        """
        place = cls()
        for key, value in data.items():
            setattr(place, key, value)
        return place

    def to_wkt(self) -> str:
        """
        Convert the place's geometry to Well-Known Text (WKT) format.

        Returns:
            str: WKT representation of the place's geometry
        """
        return f"POINT({self.longitude} {self.latitude})"

    @classmethod
    def from_wkt(cls, wkt: str) -> 'PlaceMixin':
        """
        Create a new place from a Well-Known Text (WKT) geometry.

        Args:
            wkt (str): WKT representation of a point

        Returns:
            PlaceMixin: New PlaceMixin instance

        Raises:
            ValueError: If the WKT string is not a valid point
        """
        import re
        match = re.match(r"POINT\((\S+)\s+(\S+)\)", wkt)
        if match:
            place = cls()
            place.longitude, place.latitude = map(float, match.groups())
            return place
        else:
            raise ValueError("Invalid WKT point string")



    def distance_to(self, other: Union['PlaceMixin', Tuple[float, float]], method: str = 'haversine') -> float:
        """
        Calculate the distance to another place or coordinates.

        Args:
            other: Another PlaceMixin instance or a tuple of (latitude, longitude)
            method: Distance calculation method ('haversine', 'geodesic', or 'great_circle')

        Returns:
            float: Distance in kilometers

        Raises:
            ValueError: If an invalid method is specified
        """
        if isinstance(other, tuple):
            other_lat, other_lon = other
        else:
            other_lat, other_lon = other.latitude, other.longitude

        if method == 'haversine':
            return self.haversine_distance(other_lat, other_lon)
        elif method == 'geodesic':
            return self.geodesic_distance(other_lat, other_lon)
        elif method == 'great_circle':
            return self.great_circle_distance(other_lat, other_lon)
        else:
            raise ValueError(f"Invalid distance calculation method: {method}")

    def set_coordinates_in_crs(self, x: float, y: float, from_crs: str, to_crs: str = 'EPSG:4326') -> 'PlaceMixin':
        """
        Set coordinates transformed from one CRS to another.

        Args:
            x: X-coordinate (longitude or easting) in the source CRS
            y: Y-coordinate (latitude or northing) in the source CRS
            from_crs: Source Coordinate Reference System
            to_crs: Target Coordinate Reference System (default: WGS84)

        Returns:
            PlaceMixin: Self for method chaining
        """
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return self.set_coordinates(lat, lon)

    def generate_static_map(self, zoom: int = 12, width: int = 400, height: int = 300) -> str:
        """
        Generate a static map image URL using OpenStreetMap.

        Args:
            zoom: Zoom level (0-19)
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            str: URL of the static map image
        """
        base_url = "https://static-maps.openstreetmap.fr/"
        params = {
            'center': f"{self.latitude},{self.longitude}",
            'zoom': zoom,
            'size': f"{width}x{height}",
            'maptype': 'mapnik',
            'markers': f"{self.latitude},{self.longitude},red-dot"
        }
        return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def calculate_route_online(self, destination: 'PlaceMixin') -> Dict[str, Any]:
        """
        Calculate a route to a destination using the OSRM online service.

        Args:
            destination: Destination PlaceMixin instance

        Returns:
            dict: Route information including distance, duration, and geometry
        """
        url = f"http://router.project-osrm.org/route/v1/driving/{self.longitude},{self.latitude};{destination.longitude},{destination.latitude}?overview=full&geometries=geojson"
        response = requests.get(url)
        data = response.json()
        if data['code'] != 'Ok':
            raise ValueError("Unable to calculate route")
        route = data['routes'][0]
        return {
            'distance': route['distance'],
            'duration': route['duration'],
            'geometry': route['geometry']
        }

    def estimate_travel_time(self, destination: 'PlaceMixin', speed_km_h: float = 60) -> float:
        """
        Estimate travel time to a destination based on a given speed.

        Args:
            destination: Destination PlaceMixin instance
            speed_km_h: Average travel speed in km/h

        Returns:
            float: Estimated travel time in hours
        """
        distance = self.distance_to(destination)
        return distance / speed_km_h

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the place to a dictionary representation.

        Returns:
            dict: Dictionary containing place attributes
        """
        return {
            'id': self.id,
            'place_name': self.place_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'country_code': self.country_code,
            'admin1_code': self.admin1_code,
            'admin2_code': self.admin2_code,
            'feature_code': self.feature_code,
            'timezone': self.timezone
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a dictionary.

        Args:
            data: Dictionary containing place attributes

        Returns:
            PlaceMixin: New instance created from the dictionary
        """
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance

    @classmethod
    def from_geojson(cls, geojson: Dict[str, Any]) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a GeoJSON Feature.

        Args:
            geojson: GeoJSON Feature dictionary

        Returns:
            PlaceMixin: New instance created from the GeoJSON
        """
        if geojson['type'] != 'Feature' or geojson['geometry']['type'] != 'Point':
            raise ValueError("Invalid GeoJSON: must be a Feature with Point geometry")

        instance = cls()
        instance.longitude, instance.latitude = geojson['geometry']['coordinates']
        instance.place_name = geojson['properties'].get('name', '')
        instance.place_description = geojson['properties'].get('description', '')
        return instance

    @classmethod
    def bulk_import_geojson(cls, geojson_collection: Dict[str, Any]) -> List['PlaceMixin']:
        """
        Bulk import places from a GeoJSON FeatureCollection.

        Args:
            geojson_collection: GeoJSON FeatureCollection dictionary

        Returns:
            list: List of created PlaceMixin instances
        """
        if geojson_collection['type'] != 'FeatureCollection':
            raise ValueError("Invalid GeoJSON: must be a FeatureCollection")

        return [cls.from_geojson(feature) for feature in geojson_collection['features']]

    def geocode_simple(self, db, name: str) -> Optional['PlaceMixin']:
        """
        Simple geocoding using the GeoNames database.

        Args:
            db: SQLAlchemy database instance
            name: Place name to geocode

        Returns:
            PlaceMixin: Self if geocoding successful, None otherwise
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        result = db.session.query(NxGeoGeoname).filter(
            NxGeoGeoname.c.name.ilike(f"%{name}%")
        ).order_by(NxGeoGeoname.c.population.desc()).first()

        if result:
            self.set_coordinates(result.latitude, result.longitude)
            self.place_name = result.name
            self.country_code = result.country_code
            return self
        return None

    def reverse_geocode_to_place(self, db, latitude: float, longitude: float) -> Optional['PlaceMixin']:
        """
        Reverse geocode coordinates to the nearest place.

        Args:
            db: SQLAlchemy database instance
            latitude: Latitude to reverse geocode
            longitude: Longitude to reverse geocode

        Returns:
            PlaceMixin: Self if reverse geocoding successful, None otherwise
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        result = db.session.query(NxGeoGeoname).order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
            )
        ).first()

        if result:
            self.set_coordinates(result.latitude, result.longitude)
            self.place_name = result.name
            self.country_code = result.country_code
            return self
        return None

    def reverse_geocode_to_feature(self, db, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to the nearest feature with detailed information.

        Args:
            db: SQLAlchemy database instance
            latitude: Latitude to reverse geocode
            longitude: Longitude to reverse geocode

        Returns:
            dict: Detailed information about the nearest feature
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        NxGeoCountryInfo = db.Model.metadata.tables['nx_geo_country_info']
        NxGeoAdmin1Codes = db.Model.metadata.tables['nx_geo_admin1_codes']
        NxGeoAdmin2Codes = db.Model.metadata.tables['nx_geo_admin2_codes']

        result = db.session.query(NxGeoGeoname, NxGeoCountryInfo, NxGeoAdmin1Codes, NxGeoAdmin2Codes).join(
            NxGeoCountryInfo, NxGeoGeoname.c.country_code == NxGeoCountryInfo.c.iso_alpha2
        ).outerjoin(
            NxGeoAdmin1Codes, (NxGeoGeoname.c.country_code == func.substr(NxGeoAdmin1Codes.c.code, 1, 2)) &
                              (NxGeoGeoname.c.admin1_code == func.substr(NxGeoAdmin1Codes.c.code, 4, 3))
        ).outerjoin(
            NxGeoAdmin2Codes, (NxGeoGeoname.c.country_code == func.substr(NxGeoAdmin2Codes.c.code, 1, 2)) &
                              (NxGeoGeoname.c.admin1_code == func.substr(NxGeoAdmin2Codes.c.code, 4, 3)) &
                              (NxGeoGeoname.c.admin2_code == func.substr(NxGeoAdmin2Codes.c.code, 8, 3))
        ).order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
            )
        ).first()

        if result:
            geoname, country_info, admin1, admin2 = result
            return {
                'geonameid': geoname.geonameid,
                'name': geoname.name,
                'latitude': geoname.latitude,
                'longitude': geoname.longitude,
                'feature_class': geoname.feature_class,
                'feature_code': geoname.feature_code,
                'country_code': geoname.country_code,
                'country_name': country_info.name,
                'admin1_code': geoname.admin1_code,
                'admin1_name': admin1.name if admin1 else None,
                'admin2_code': geoname.admin2_code,
                'admin2_name': admin2.name if admin2 else None,
                'population': geoname.population,
                'timezone': geoname.timezone
            }
        return None

    @staticmethod
    def validate_latitude(latitude: float) -> None:
        """
        Validate the given latitude value.

        Args:
            latitude: Latitude value to validate

        Raises:
            ValueError: If latitude is invalid
        """
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")

    @staticmethod
    def validate_longitude(longitude: float) -> None:
        """
        Validate the given longitude value.

        Args:
            longitude: Longitude value to validate

        Raises:
            ValueError: If longitude is invalid
        """
        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")

    def save_to_geojson(self, filename: str) -> None:
        """
        Save the place to a GeoJSON file.

        Args:
            filename: Name of the file to save
        """
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": self.to_dict()
        }
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)

    def save_to_kml(self, filename: str) -> None:
        """
        Save the place to a KML file.

        Args:
            filename: Name of the file to save
        """
        kml = ET.Element('kml')
        document = ET.SubElement(kml, 'Document')
        placemark = ET.SubElement(document, 'Placemark')
        ET.SubElement(placemark, 'name').text = self.place_name
        point = ET.SubElement(placemark, 'Point')
        ET.SubElement(point, 'coordinates').text = f"{self.longitude},{self.latitude},{self.altitude or 0}"

        tree = ET.ElementTree(kml)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

    # def find_places_in_polygon(self, db, polygon: List[Tuple[float, float]]) -> List['PlaceMixin']:
    #     """
    #     Find all places within a given polygon.
    #
    #     Args:
    #         db: SQLAlchemy database instance
    #         polygon: List of (longitude, latitude) tuples defining the polygon
    #
    #     Returns:
    #         list: List of PlaceMixin instances within the polygon
    #     """
    #     NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
    #     polygon_wkt = f"POLYGON(({','.join([f'{lon} {lat}' for lon, lat in polygon])}))"
    #     query = db.session.query(NxGeoGeoname).filter(
    #         func.ST_Contains(
    #             func.ST_GeomFromText(polygon_wkt, 4326),
    #             func.ST_SetSRID(func.ST_MakePoint(NxGeoGeofunc.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
    #         )
    #     )
    #     return [self.from_dict(row._asdict()) for row in query.all()]
    @classmethod
    def find_places_in_polygon(cls, db, polygon: List[Tuple[float, float]]) -> List['PlaceMixin']:
        """
        Find all places within a given polygon.

        Args:
            db: SQLAlchemy database instance
            polygon: List of (longitude, latitude) tuples defining the polygon

        Returns:
            List[PlaceMixin]: List of PlaceMixin instances within the polygon
        """
        # Create a Shapely polygon from the input coordinates
        poly = Polygon(polygon)

        # Convert the Shapely polygon to a PostGIS geometry
        polygon_wkb = from_shape(poly, srid=4326)

        # Get the table for the current class
        table = cls.__table__

        # Construct the query
        query = db.session.query(cls).filter(
            func.ST_Contains(
                func.ST_GeomFromWKB(polygon_wkb, 4326),
                func.ST_SetSRID(func.ST_MakePoint(table.c.longitude, table.c.latitude), 4326)
            )
        )

        # Execute the query and return the results
        return query.all()

    def is_within_fence(self, center_lat: float, center_lon: float, radius_km: float) -> bool:
        """
        Check if the place is within a circular fence.

        Args:
            center_lat: Latitude of the fence center
            center_lon: Longitude of the fence center
            radius_km: Radius of the fence in kilometers

        Returns:
            bool: True if the place is within the fence, False otherwise
        """
        distance = self.distance_to((center_lat, center_lon))
        return distance <= radius_km

    @staticmethod
    def transform_coordinates(x: float, y: float, from_crs: str, to_crs: str) -> Tuple[float, float]:
        """
        Transform coordinates from one CRS to another.

        Args:
            x: X-coordinate (longitude or easting) in the source CRS
            y: Y-coordinate (latitude or northing) in the source CRS
            from_crs: Source Coordinate Reference System
            to_crs: Target Coordinate Reference System

        Returns:
            tuple: (x, y) coordinates in the target CRS
        """
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        return transformer.transform(x, y)

    def generate_leaflet_map(self, zoom: int = 12) -> str:
        """
        Generate HTML for a Leaflet map centered on this place.

        Args:
            zoom: Initial zoom level for the map

        Returns:
            str: HTML string containing the Leaflet map
        """
        map_html = f"""
        <div id="map" style="height: 400px;"></div>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script>
            var map = L.map('map').setView([{self.latitude}, {self.longitude}], {zoom});
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            L.marker([{self.latitude}, {self.longitude}]).addTo(map)
                .bindPopup("{self.place_name}").openPopup();
        </script>
        """
        return map_html

    def generate_openlayers_map(self, zoom: int = 12) -> str:
        """
        Generate HTML for an OpenLayers map centered on this place.

        Args:
            zoom: Initial zoom level for the map

        Returns:
            str: HTML string containing the OpenLayers map
        """
        map_html = f"""
        <div id="map" style="height: 400px;"></div>
        <script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/build/ol.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/css/ol.css" />
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
            var marker = new ol.Feature({{
                geometry: new ol.geom.Point(ol.proj.fromLonLat([{self.longitude}, {self.latitude}]))
            }});
            var vectorSource = new ol.source.Vector({{
                features: [marker]
            }});
            var vectorLayer = new ol.layer.Vector({{
                source: vectorSource
            }});
            map.addLayer(vectorLayer);
        </script>
        """
        return map_html

    def generate_leaflet_route_map(self, destination: 'PlaceMixin', zoom: int = 12) -> str:
        """
        Generate HTML for a Leaflet map with a route to a destination.

        Args:
            destination: Destination PlaceMixin instance
            zoom: Initial zoom level for the map

        Returns:
            str: HTML string containing the Leaflet map with route
        """
        route = self.calculate_route_online(destination)
        route_coords = json.dumps(route['geometry']['coordinates'])

        map_html = f"""
        <div id="map" style="height: 400px;"></div>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script>
            var map = L.map('map').setView([{self.latitude}, {self.longitude}], {zoom});
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            L.marker([{self.latitude}, {self.longitude}]).addTo(map)
                .bindPopup("Start: {self.place_name}").openPopup();
            L.marker([{destination.latitude}, {destination.longitude}]).addTo(map)
                .bindPopup("End: {destination.place_name}");
            var routeCoords = {route_coords};
            var routeLine = L.polyline(routeCoords.map(coord => [coord[1], coord[0]]), {{color: 'blue'}}).addTo(map);
            map.fitBounds(routeLine.getBounds());
        </script>
        """
        return map_html

    def generate_openlayers_route_map(self, destination: 'PlaceMixin', zoom: int = 12) -> str:
        """
        Generate HTML for an OpenLayers map with a route to a destination.

        Args:
            destination: Destination PlaceMixin instance
            zoom: Initial zoom level for the map

        Returns:
            str: HTML string containing the OpenLayers map with route
        """
        route = self.calculate_route_online(destination)
        route_coords = json.dumps(route['geometry']['coordinates'])

        map_html = f"""
        <div id="map" style="height: 400px;"></div>
        <script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/build/ol.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/css/ol.css" />
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
            var startMarker = new ol.Feature({{
                geometry: new ol.geom.Point(ol.proj.fromLonLat([{self.longitude}, {self.latitude}]))
            }});
            var endMarker = new ol.Feature({{
                geometry: new ol.geom.Point(ol.proj.fromLonLat([{destination.longitude}, {destination.latitude}]))
            }});
            var routeCoords = {route_coords};
            var routeLine = new ol.Feature({{
                geometry: new ol.geom.LineString(routeCoords).transform('EPSG:4326', 'EPSG:3857')
            }});
            var vectorSource = new ol.source.Vector({{
                features: [startMarker, endMarker, routeLine]
            }});
            var vectorLayer = new ol.layer.Vector({{
                source: vectorSource
            }});
            map.addLayer(vectorLayer);
            var extent = vectorSource.getExtent();
            map.getView().fit(extent, {{padding: [50, 50, 50, 50]}});
        </script>
        """
        return map_html

    @classmethod
    def generate_multiple_pins_map(cls, places: List['PlaceMixin'], zoom: int = 12) -> str:
        """
        Generate HTML for a Leaflet map with multiple pins.

        Args:
            places: List of PlaceMixin instances to display on the map
            zoom: Initial zoom level for the map

        Returns:
            str: HTML string containing the Leaflet map with multiple pins
        """
        center_lat = sum(place.latitude for place in places) / len(places)
        center_lon = sum(place.longitude for place in places) / len(places)

        markers_js = "\n".join([
            f"L.marker([{place.latitude}, {place.longitude}]).addTo(map).bindPopup('{place.place_name}');"
            for place in places
        ])

        map_html = f"""
        <div id="map" style="height: 400px;"></div>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script>
            var map = L.map('map').setView([{center_lat}, {center_lon}], {zoom});
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            {markers_js}
        </script>
        """
        return map_html

    @staticmethod
    def write_templates(directory: str) -> None:
        """
        Write HTML templates for maps to a specified directory.

        Args:
            directory: Directory to write the templates to
        """
        os.makedirs(directory, exist_ok=True)

        leaflet_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Leaflet Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        </head>
        <body>
            <div id="map" style="height: 400px;"></div>
            <script>
                // Leaflet map initialization code goes here
                {{ map_code }}
            </script>
        </body>
        </html>
        """

        openlayers_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenLayers Map</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/css/ol.css" />
            <script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.5.0/build/ol.js"></script>
        </head>
        <body>
            <div id="map" style="height: 400px;"></div>
            <script>
                // OpenLayers map initialization code goes here
                {{ map_code }}
            </script>
        </body>
        </html>
        """

        with open(os.path.join(directory, 'leaflet_template.html'), 'w') as f:
            f.write(leaflet_template)

        with open(os.path.join(directory, 'openlayers_template.html'), 'w') as f:
            f.write(openlayers_template)

    @staticmethod
    def download_file_wget(url: str, output_path: str) -> None:
        """
        Download a file using wget.

        Args:
            url: URL of the file to download
            output_path: Path to save the downloaded file

        Note: This method requires wget to be installed on the system.
        """
        import subprocess

        try:
            subprocess.run(['wget', '-O', output_path, url], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to download file: {e}")

    @classmethod
    def create_geonames_tables(cls, engine) -> None:
        """
        Create GeoNames tables in the database.

        Args:
            engine: SQLAlchemy engine instance
        """
        metadata = MetaData()

        Table('nx_geo_geoname', metadata,
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
              Column('modification_date', Date))

        # Add other GeoNames tables (country_info, admin1_codes, etc.) here

        metadata.create_all(engine)

    @classmethod
    def populate_geonames_tables(cls, engine, data_dir: str) -> None:
        """
        Populate GeoNames tables with data from downloaded files.

        Args:
            engine: SQLAlchemy engine instance
            data_dir: Directory containing the GeoNames data files
        """
        import csv

        with engine.connect() as connection:
            for table_name, file_name in cls.GeoNamesSetup.GEONAMES_FILES.items():
                file_path = os.path.join(data_dir, file_name or table_name)
                table = Table(f'nx_geo_{table_name.split(".")[0]}', MetaData(), autoload_with=engine)

                with open(file_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f, delimiter='\t')
                    columns = [c.key for c in table.columns]
                    connection.execute(table.delete())
                    connection.execute(table.insert(), [dict(zip(columns, row)) for row in csv_reader])

    def geocode(self, db, address: str) -> Optional['PlaceMixin']:
        """
        Geocode an address using the GeoNames database.

        Args:
            db: SQLAlchemy database instance
            address: Address to geocode

        Returns:
            Optional[PlaceMixin]: Geocoded place or None if not found
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        words = address.split()
        query = db.session.query(NxGeoGeoname)

        for word in words:
            query = query.filter(NxGeoGeoname.c.name.ilike(f"%{word}%"))

        result = query.order_by(NxGeoGeoname.c.population.desc()).first()

        if result:
            self.set_coordinates(result.latitude, result.longitude)
            self.place_name = result.name
            self.country_code = result.country_code
            self.admin1_code = result.admin1_code
            self.admin2_code = result.admin2_code
            return self
        return None

    def reverse_geocode(self, db, latitude: float, longitude: float) -> Optional['PlaceMixin']:
        """
        Perform reverse geocoding to find the nearest place to given coordinates.

        Args:
            db: SQLAlchemy database instance
            latitude: Latitude to reverse geocode
            longitude: Longitude to reverse geocode

        Returns:
            Optional[PlaceMixin]: Nearest place or None if not found
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        result = db.session.query(NxGeoGeoname).order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
            )
        ).first()

        if result:
            self.set_coordinates(result.latitude, result.longitude)
            self.place_name = result.name
            self.country_code = result.country_code
            self.admin1_code = result.admin1_code
            self.admin2_code = result.admin2_code
            return self
        return None

    @classmethod
    def find_closest_instances(cls, db, latitude: float, longitude: float, limit: int = 5) -> List['PlaceMixin']:
        """
        Find the closest instances to given coordinates.

        Args:
            db: SQLAlchemy database instance
            latitude: Latitude of the reference point
            longitude: Longitude of the reference point
            limit: Maximum number of instances to return

        Returns:
            List[PlaceMixin]: List of closest instances
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        results = db.session.query(NxGeoGeoname).order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
            )
        ).limit(limit).all()

        return [cls.from_dict(result._asdict()) for result in results]

    def get_elevation(self, api_key: str) -> Optional[float]:
        """
        Get the elevation of the place using the Open-Elevation API.

        Args:
            api_key: API key for the Open-Elevation service

        Returns:
            Optional[float]: Elevation in meters or None if not available
        """
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={self.latitude},{self.longitude}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['results'][0]['elevation']
        return None

    def get_timezone(self, db) -> Optional[str]:
        """
        Get the timezone of the place using the GeoNames database.

        Args:
            db: SQLAlchemy database instance

        Returns:
            Optional[str]: Timezone string or None if not found
        """
        NxGeoTimezones = db.Model.metadata.tables['nx_geo_timezones']
        result = db.session.query(NxGeoTimezones).filter(
            NxGeoTimezones.c.countrycode == self.country_code
        ).order_by(
            func.abs(NxGeoTimezones.c.gmtoffset - self.longitude / 15)
        ).first()

        return result.timezoneid if result else None

    def get_country_info(self, db) -> Optional[Dict[str, Any]]:
        """
        Get detailed country information for the place.

        Args:
            db: SQLAlchemy database instance

        Returns:
            Optional[Dict[str, Any]]: Dictionary with country information or None if not found
        """
        NxGeoCountryInfo = db.Model.metadata.tables['nx_geo_country_info']
        result = db.session.query(NxGeoCountryInfo).filter(
            NxGeoCountryInfo.c.iso_alpha2 == self.country_code
        ).first()

        return result._asdict() if result else None

    def get_administrative_divisions(self, db) -> Dict[str, str]:
        """
        Get administrative division names for the place.

        Args:
            db: SQLAlchemy database instance

        Returns:
            Dict[str, str]: Dictionary with admin1 and admin2 names
        """
        NxGeoAdmin1Codes = db.Model.metadata.tables['nx_geo_admin1_codes']
        NxGeoAdmin2Codes = db.Model.metadata.tables['nx_geo_admin2_codes']

        admin1 = db.session.query(NxGeoAdmin1Codes).filter(
            NxGeoAdmin1Codes.c.code == f"{self.country_code}.{self.admin1_code}"
        ).first()

        admin2 = db.session.query(NxGeoAdmin2Codes).filter(
            NxGeoAdmin2Codes.c.code == f"{self.country_code}.{self.admin1_code}.{self.admin2_code}"
        ).first()

        return {
            "admin1_name": admin1.name if admin1 else None,
            "admin2_name": admin2.name if admin2 else None
        }

    def get_nearby_places(self, db, radius_km: float, limit: int = 10) -> List['PlaceMixin']:
        """
        Get nearby places within a specified radius.

        Args:
            db: SQLAlchemy database instance
            radius_km: Search radius in kilometers
            limit: Maximum number of places to return

        Returns:
            List[PlaceMixin]: List of nearby places
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        results = db.session.query(NxGeoGeoname).filter(
            func.ST_DWithin(
                func.ST_SetSRID(func.ST_MakePoint(self.longitude, self.latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326),
                radius_km / 111.32  # Convert km to degrees (approximate)
            )
        ).order_by(
            func.ST_Distance(
                func.ST_SetSRID(func.ST_MakePoint(self.longitude, self.latitude), 4326),
                func.ST_SetSRID(func.ST_MakePoint(NxGeoGeoname.c.longitude, NxGeoGeoname.c.latitude), 4326)
            )
        ).limit(limit).all()

        return [self.from_dict(result._asdict()) for result in results]

    def get_bounding_box(self, distance_km: float) -> Tuple[float, float, float, float]:
        """
        Calculate a bounding box around the place.

        Args:
            distance_km: Distance in kilometers to extend the bounding box

        Returns:
            Tuple[float, float, float, float]: (min_lat, min_lon, max_lat, max_lon)
        """
        lat_change = distance_km / 111.32  # 1 degree of latitude is approximately 111.32 km
        lon_change = distance_km / (111.32 * math.cos(math.radians(self.latitude)))

        min_lat = self.latitude - lat_change
        max_lat = self.latitude + lat_change
        min_lon = self.longitude - lon_change
        max_lon = self.longitude + lon_change

        return (min_lat, min_lon, max_lat, max_lon)

    def to_folium_map(self, zoom: int = 12) -> folium.Map:
        """
        Create a Folium map centered on the place.

        Args:
            zoom: Initial zoom level for the map

        Returns:
            folium.Map: Folium map object
        """
        m = folium.Map(location=[self.latitude, self.longitude], zoom_start=zoom)
        folium.Marker(
            [self.latitude, self.longitude],
            popup=self.place_name,
            tooltip=self.place_name
        ).add_to(m)
        return m

    @classmethod
    def cluster_places(cls, places: List['PlaceMixin'], max_distance_km: float) -> List[List['PlaceMixin']]:
        """
        Cluster places based on their proximity.

        Args:
            places: List of PlaceMixin instances to cluster
            max_distance_km: Maximum distance between places in a cluster

        Returns:
            List[List[PlaceMixin]]: List of clusters, where each cluster is a list of PlaceMixin instances
        """
        clusters = []
        for place in places:
            added_to_cluster = False
            for cluster in clusters:
                if all(place.distance_to(p) <= max_distance_km for p in cluster):
                    cluster.append(place)
                    added_to_cluster = True
                    break
            if not added_to_cluster:
                clusters.append([place])
        return clusters

    def to_wkt(self) -> str:
        """
        Convert the place to Well-Known Text (WKT) format.

        Returns:
            str: WKT representation of the place
        """
        return f"POINT({self.longitude} {self.latitude})"

    @classmethod
    def from_wkt(cls, wkt: str) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a Well-Known Text (WKT) string.

        Args:
            wkt: WKT string representing a point

        Returns:
            PlaceMixin: New PlaceMixin instance

        Raises:
            ValueError: If the WKT string is not a valid point
        """
        import re
        match = re.match(r"POINT\s*\((-?\d+\.?\d*)\s+(-?\d+\.?\d*)\)", wkt)
        if match:
            lon, lat = map(float, match.groups())
            place = cls()
            place.set_coordinates(lat, lon)
            return place
        else:
            raise ValueError("Invalid WKT point string")

    def to_feature_collection(self) -> Dict[str, Any]:
        """
        Convert the place to a GeoJSON FeatureCollection.

        Returns:
            Dict[str, Any]: GeoJSON FeatureCollection
        """
        return {
            "type": "FeatureCollection",
            "features": [self.to_geojson()]
        }

    @staticmethod
    def plot_places(places: List['PlaceMixin'], filename: str) -> None:
        """
        Plot multiple places on a map and save it as an image.

        Args:
            places: List of PlaceMixin instances to plot
            filename: Name of the file to save the plot
        """
        lats = [place.latitude for place in places]
        lons = [place.longitude for place in places]
        names = [place.place_name for place in places]

        plt.figure(figsize=(12, 8))
        plt.scatter(lons, lats)
        for i, name in enumerate(names):
            plt.annotate(name, (lons[i], lats[i]))
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Place Locations')
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def get_alternate_names(self, db) -> List[str]:
        """
        Get alternate names for the place from the GeoNames database.

        Args:
            db: SQLAlchemy database instance

        Returns:
            List[str]: List of alternate names
        """
        NxGeoAlternateNames = db.Model.metadata.tables['nx_geo_alternate_names']
        results = db.session.query(NxGeoAlternateNames.c.alternate_name).filter(
            NxGeoAlternateNames.c.geonameid == self.id
        ).all()
        return [result.alternate_name for result in results]

    @classmethod
    def find_by_feature_code(cls, db, feature_code: str, limit: int = 10) -> List['PlaceMixin']:
        """
        Find places by feature code.

        Args:
            db: SQLAlchemy database instance
            feature_code: GeoNames feature code to search for
            limit: Maximum number of places to return

        Returns:
            List[PlaceMixin]: List of places with the specified feature code
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        results = db.session.query(NxGeoGeoname).filter(
            NxGeoGeoname.c.feature_code == feature_code
        ).order_by(NxGeoGeoname.c.population.desc()).limit(limit).all()
        return [cls.from_dict(result._asdict()) for result in results]

    def to_address_string(self) -> str:
        """
        Generate a formatted address string for the place.

        Returns:
            str: Formatted address string
        """
        components = [
            self.place_name,
            self.admin2_code,
            self.admin1_code,
            self.country_code
        ]
        return ", ".join(filter(None, components))

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the Haversine distance between two points.

        Args:
            lat1: Latitude of the first point
            lon1: Longitude of the first point
            lat2: Latitude of the second point
            lon2: Longitude of the second point

        Returns:
            float: Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def bearing_to(self, other: 'PlaceMixin') -> float:
        """
        Calculate the initial bearing from this place to another.

        Args:
            other: Another PlaceMixin instance

        Returns:
            float: Initial bearing in degrees
        """
        lat1, lon1 = map(math.radians, [self.latitude, self.longitude])
        lat2, lon2 = map(math.radians, [other.latitude, other.longitude])

        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        initial_bearing = math.atan2(y, x)

        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing

    def midpoint_to(self, other: 'PlaceMixin') -> 'PlaceMixin':
        """
        Calculate the midpoint between this place and another.

        Args:
            other: Another PlaceMixin instance

        Returns:
            PlaceMixin: New PlaceMixin instance representing the midpoint
        """
        lat1, lon1 = map(math.radians, [self.latitude, self.longitude])
        lat2, lon2 = map(math.radians, [other.latitude, other.longitude])

        bx = math.cos(lat2) * math.cos(lon2 - lon1)
        by = math.cos(lat2) * math.sin(lon2 - lon1)

        lat3 = math.atan2(math.sin(lat1) + math.sin(lat2),
                          math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2))
        lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)

        lat3, lon3 = map(math.degrees, [lat3, lon3])

        midpoint = PlaceMixin()
        midpoint.set_coordinates(lat3, lon3)
        midpoint.place_name = f"Midpoint between {self.place_name} and {other.place_name}"
        return midpoint

    def destination_point(self, bearing: float, distance: float) -> 'PlaceMixin':
        """
        Calculate the destination point given a bearing and distance from this place.

        Args:
            bearing: Bearing in degrees
            distance: Distance in kilometers

        Returns:
            PlaceMixin: New PlaceMixin instance representing the destination point
        """
        R = 6371  # Earth's radius in kilometers

        bearing = math.radians(bearing)
        lat1, lon1 = map(math.radians, [self.latitude, self.longitude])

        lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) +
                         math.cos(lat1) * math.sin(distance / R) * math.cos(bearing))
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(lat1),
                                 math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))

        lat2, lon2 = map(math.degrees, [lat2, lon2])

        destination = PlaceMixin()
        destination.set_coordinates(lat2, lon2)
        destination.place_name = f"Destination from {self.place_name}"
        return destination

    def is_within_country(self, db, country_code: str) -> bool:
        """
        Check if the place is within a specific country.

        Args:
            db: SQLAlchemy database instance
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            bool: True if the place is within the specified country, False otherwise
        """
        NxGeoCountryInfo = db.Model.metadata.tables['nx_geo_country_info']
        country = db.session.query(NxGeoCountryInfo).filter(
            NxGeoCountryInfo.c.iso_alpha2 == country_code
        ).first()

        if not country:
            raise ValueError(f"Invalid country code: {country_code}")

        return self.country_code == country_code

    def get_continent(self, db) -> Optional[str]:
        """
        Get the continent of the place.

        Args:
            db: SQLAlchemy database instance

        Returns:
            Optional[str]: Continent name or None if not found
        """
        NxGeoCountryInfo = db.Model.metadata.tables['nx_geo_country_info']
        NxGeoContinents = db.Model.metadata.tables['nx_geo_continents']

        result = db.session.query(NxGeoContinents.c.name).join(
            NxGeoCountryInfo,
            NxGeoCountryInfo.c.continent == NxGeoContinents.c.code
        ).filter(
            NxGeoCountryInfo.c.iso_alpha2 == self.country_code
        ).first()

        return result.name if result else None

    def get_local_time(self) -> datetime:
        """
        Get the current local time at the place.

        Returns:
            datetime: Current local time at the place
        """
        from datetime import datetime
        import pytz

        if not self.timezone:
            raise ValueError("Timezone information is not available for this place")

        local_tz = pytz.timezone(self.timezone)
        return datetime.now(local_tz)

    def format_coordinates(self, format: str = 'dms') -> str:
        """
        Format the coordinates of the place in various formats.

        Args:
            format: Coordinate format ('dms' for degrees, minutes, seconds; 'dm' for degrees, decimal minutes; 'd' for decimal degrees)

        Returns:
            str: Formatted coordinates
        """

        def dms_format(coord, pos, neg):
            deg = abs(coord)
            d = int(deg)
            m = int((deg - d) * 60)
            s = round(((deg - d) * 60 - m) * 60, 2)
            return f"{d}°{m}'{s}\"{pos if coord >= 0 else neg}"

        def dm_format(coord, pos, neg):
            deg = abs(coord)
            d = int(deg)
            m = round((deg - d) * 60, 4)
            return f"{d}°{m}'{pos if coord >= 0 else neg}"

        if format == 'dms':
            lat = dms_format(self.latitude, 'N', 'S')
            lon = dms_format(self.longitude, 'E', 'W')
        elif format == 'dm':
            lat = dm_format(self.latitude, 'N', 'S')
            lon = dm_format(self.longitude, 'E', 'W')
        elif format == 'd':
            lat = f"{self.latitude:.6f}°{'N' if self.latitude >= 0 else 'S'}"
            lon = f"{self.longitude:.6f}°{'E' if self.longitude >= 0 else 'W'}"
        else:
            raise ValueError("Invalid format. Use 'dms', 'dm', or 'd'")

        return f"{lat} {lon}"

    def get_sun_position(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate the sun's position at the place for a given date and time.

        Args:
            date: Date and time for the calculation (default: current UTC time)

        Returns:
            Dict[str, Any]: Dictionary containing sun position information
        """
        from pysolar import solar

        if date is None:
            date = datetime.utcnow()

        altitude = solar.get_altitude(self.latitude, self.longitude, date)
        azimuth = solar.get_azimuth(self.latitude, self.longitude, date)
        radiation = solar.radiation.get_radiation_direct(date, altitude)

        return {
            "altitude": altitude,
            "azimuth": azimuth,
            "radiation": radiation,
            "is_day": altitude > 0
        }

    def calculate_area(self, db, admin_level: str = 'country') -> Optional[float]:
        """
        Calculate the area of the administrative region containing the place.

        Args:
            db: SQLAlchemy database instance
            admin_level: Administrative level ('country', 'admin1', or 'admin2')

        Returns:
            Optional[float]: Area in square kilometers or None if not available
        """
        if admin_level == 'country':
            NxGeoCountryInfo = db.Model.metadata.tables['nx_geo_country_info']
            result = db.session.query(NxGeoCountryInfo.c.area).filter(
                NxGeoCountryInfo.c.iso_alpha2 == self.country_code
            ).first()
            return result.area if result else None
        elif admin_level in ['admin1', 'admin2']:
            # Note: This assumes you have area information in your admin tables.
            # You may need to adjust this based on your actual database schema.
            table_name = f'nx_geo_{admin_level}_codes'
            AdminTable = db.Model.metadata.tables[table_name]
            result = db.session.query(AdminTable.c.area).filter(
                AdminTable.c.code == getattr(self, f'{admin_level}_code')
            ).first()
            return result.area if result else None
        else:
            raise ValueError("Invalid admin_level. Use 'country', 'admin1', or 'admin2'")

    def get_population(self, db) -> Optional[int]:
        """
        Get the population of the place.

        Args:
            db: SQLAlchemy database instance

        Returns:
            Optional[int]: Population or None if not available
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        result = db.session.query(NxGeoGeoname.c.population).filter(
            NxGeoGeoname.c.geonameid == self.id
        ).first()
        return result.population if result else None

    @classmethod
    def find_places_by_name(cls, db, name: str, limit: int = 10) -> List['PlaceMixin']:
        """
        Find places by name.

        Args:
            db: SQLAlchemy database instance
            name: Name to search for
            limit: Maximum number of results to return

        Returns:
            List[PlaceMixin]: List of places matching the name
        """
        NxGeoGeoname = db.Model.metadata.tables['nx_geo_geoname']
        results = db.session.query(NxGeoGeoname).filter(
            NxGeoGeoname.c.name.ilike(f"%{name}%")
        ).order_by(NxGeoGeoname.c.population.desc()).limit(limit).all()
        return [cls.from_dict(result._asdict()) for result in results]

    def to_geohash(self, precision: int = 12) -> str:
        """
        Convert the place's coordinates to a geohash.

        Args:
            precision: Geohash precision (1-12)

        Returns:
            str: Geohash string
        """
        import geohash2

        return geohash2.encode(self.latitude, self.longitude, precision=precision)

    @classmethod
    def from_geohash(cls, geohash: str) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a geohash.

        Args:
            geohash: Geohash string

        Returns:
            PlaceMixin: New PlaceMixin instance
        """
        import geohash2

        lat, lon = geohash2.decode(geohash)
        place = cls()
        place.set_coordinates(lat, lon)
        place.place_name = f"Location {geohash}"
        return place

    def to_what3words(self, api_key: str) -> str:
        """
        Convert the place's coordinates to What3Words address.

        Args:
            api_key: What3Words API key

        Returns:
            str: What3Words address
        """
        url = f"https://api.what3words.com/v3/convert-to-3wa?coordinates={self.latitude},{self.longitude}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['words']
        else:
            raise RuntimeError(f"Failed to convert coordinates to What3Words: {response.text}")

    @classmethod
    def from_what3words(cls, words: str, api_key: str) -> 'PlaceMixin':
        """
        Create a PlaceMixin instance from a What3Words address.

        Args:
            words: What3Words address
            api_key: What3Words API key

        Returns:
            PlaceMixin: New PlaceMixin instance
        """
        url = f"https://api.what3words.com/v3/convert-to-coordinates?words={words}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            place = cls()
            place.set_coordinates(data['coordinates']['lat'], data['coordinates']['lng'])
            place.place_name = f"Location {words}"
            return place
        else:
            raise RuntimeError(f"Failed to convert What3Words to coordinates: {response.text}")

 def __repr__(self) -> str:
        """
        String representation of the place.

        Returns:
            str: String representation
        """
        return f"<Place {self.place_name} ({self.latitude}, {self.longitude})>"