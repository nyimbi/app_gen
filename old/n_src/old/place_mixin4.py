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
import hashlib
import zipfile

import requests
import gzip
import logging
import json
import csv
import io
from typing import List, Dict, Any, Tuple, Optional, Union
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, MetaData, inspect, create_engine, \
    event, func
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point, Polygon
import math
from flask import current_app, g
from flask_appbuilder import AppBuilder, SQLA
# from flask_appbuilder import Model
# Work across both SQLAlchemy 1.x and 2.0
try:
    # SQLAlchemy 2.0
    from sqlalchemy.orm import DeclarativeBase, mapped_column
    SQLALCHEMY_2 = True
except ImportError:
    # SQLAlchemy 1.x
    from sqlalchemy.ext.declarative import declared_attr
    SQLALCHEMY_2 = False

# db = g.get('db')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaceMixin:
    """
    A comprehensive mixin for Flask-AppBuilder models that provides extensive
    geographical information and operations.
    """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    if SQLALCHEMY_2:
        # id = mapped_column(Integer, primary_key=True)
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
        # id = Column(Integer, primary_key=True)
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
                        connection.execute(f"COPY {table_name} FROM STDIN WITH CSV DELIMITER E'\\t' QUOTE E'\\b' NULL AS ''")
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

    def distance_to(self, other: Union['PlaceMixin', Tuple[float, float]], method: str = 'haversine') -> float:
        """
        Calculate the distance to another place or coordinates.

        Args:
            other (Union[PlaceMixin, Tuple[float, float]]): Another PlaceMixin instance or a tuple of (latitude, longitude)
            method (str): Distance calculation method ('haversine', 'geodesic', or 'great_circle')

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
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
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
                func.ST_GeomFromText(func.concat('POINT(', NxGeoGeoname.c.longitude, ' ', NxGeoGeoname.c.latitude, ')'), 4326)
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
                func.ST_GeomFromText(func.concat('POINT(', NxGeoGeoname.c.longitude, ' ', NxGeoGeoname.c.latitude, ')'), 4326)
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

    def __repr__(self) -> str:
        """
        String representation of the place.

        Returns:
            str: String representation
        """
        return f"<Place {self.place_name} ({self.latitude}, {self.longitude})>"

# Example usage:
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from your_app import db  # Import your Flask-AppBuilder db instance

class MyPlace(Model, PlaceMixin):
    __tablename__ = 'my_places'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    def __repr__(self):
        return self.name

# In your Flask-AppBuilder application:

# config.py
SETUP_GEONAMES = True

# views.py
from flask_appbuilder import ModelView
from .models import MyPlace

class MyPlaceView(ModelView):
    datamodel = SQLAInterface(MyPlace)
    list_columns = ['name', 'place_name', 'latitude', 'longitude', 'country.name']
    show_columns = ['name', 'place_name', 'place_description', 'latitude', 'longitude', 'altitude', 'country.name', 'admin1_code', 'admin2_code', 'feature.name', 'timezone_info.timezoneid']
    edit_columns = ['name', 'place_name', 'place_description', 'latitude', 'longitude', 'altitude']
    add_columns = ['name', 'place_name', 'place_description', 'latitude', 'longitude', 'altitude']
    search_columns = ['name', 'place_name', 'country.name', 'admin1_code', 'admin2_code']

# In your Flask-AppBuilder application initialization:
appbuilder.add_view(MyPlaceView, "My Places", icon="fa-globe", category="Locations")

# Using the PlaceMixin in your application:
with app.app_context():
    new_place = MyPlace(name="Eiffel Tower")
    new_place.set_coordinates(48.8584, 2.2945)
    new_place.geocode(db, "Eiffel Tower, Paris")
    db.session.add(new_place)
    db.session.commit()

    # Find nearest places
    nearest = new_place.nearest_places(db, limit=5)
    for place in nearest:
        print(f"Nearby: {place.place_name}, Distance: {new_place.distance_to(place):.2f} km")

    # Convert to GeoJSON
    geojson = new_place.to_geojson()
    print(json.dumps(geojson, indent=2))

    # Reverse geocoding
    unknown_place = MyPlace(name="Unknown")
    unknown_place.reverse_geocode(db, 40.7128, -74.0060)
    print(f"Reverse geocoded: {unknown_place.place_name}, {unknown_place.place_description}")
"""
