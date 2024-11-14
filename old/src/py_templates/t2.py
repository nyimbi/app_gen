import sys
from pathlib import Path
from sqlalchemy import create_engine, MetaData, ForeignKey, Integer, PrimaryKeyConstraint,ForeignKeyConstraint,Column,Table,relationship
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from flask_appbuilder import AppBuilder, ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.views import MasterDetailView

# Define a list of tables to exclude from the introspection process
EXCLUDED_TABLES = ['alembic_version']

# Define a declarative base
Base = declarative_base()

def create_appbuilder_models(db_uri):
    # Create a database engine from the supplied URI
    engine = create_engine(db_uri)

    # Create a metadata object and reflect the schema and tables from the database
    metadata = MetaData()
    metadata.reflect(engine)

    # Create a Flask AppBuilder instance
    appbuilder = AppBuilder()

    # Loop over the tables in the metadata object and create models, views and related objects
    for table in metadata.tables.values():
        if table.name in EXCLUDED_TABLES:
            continue

        class_name = table.name.capitalize()
        primary_key = next(column.name for column in table.columns if column.primary_key)

        # Create a dictionary to hold the foreign key information
        foreign_keys = {}

        # Create a list of properties for the model
        properties = []

        # Loop over the columns in the table
        for column in table.columns:
            # Check if the column is a foreign key
            if isinstance(column.type, ForeignKey):
                foreign_key_table = str(column.type).split('.')[0].split("'")[1]
                foreign_key_column = str(column.type).split('.')[1].split("'")[0]

                # Add the foreign key information to the dictionary
                if foreign_key_table in foreign_keys:
                    foreign_keys[foreign_key_table].append((column.name, foreign_key_column))
                else:
                    foreign_keys[foreign_key_table] = [(column.name, foreign_key_column)]
            else:
                properties.append((column.name, column.type))

        # Create the class definition for the model
        model_class = type(class_name, (Base,), {
            '__tablename__': table.name,
            'id': Column(primary_key, Integer, primary_key=True),
        })

        # Add the properties to the model
        for property_name, property_type in properties:
            setattr(model_class, property_name, Column(property_type))

        # Add the foreign key relationships to the model
        for foreign_key, properties in foreign_keys.items():
            foreign_key_class_name = foreign_key.capitalize()
            foreign_key_primary_key = next(column.name for column in metadata.tables[foreign_key].columns if column.primary_key)
            foreign_key_properties = []

            for property_name, foreign_key_column in properties:
                foreign_key_properties.append(relationship(f"{foreign_key_class_name}.{foreign_key_column}", lazy='selectin'))

            # Create the foreign key model class
            foreign_key_model_class = type(f'{foreign_key_class_name}', (Base,), {
                '__tablename__': foreign_key,
                'id': Column(foreign_key_primary_key, Integer, primary_key=True),
            })

            # Add the foreign key properties to the foreign key model
            for property_name, property_type in foreign_key_properties:
                setattr(foreign_key_model_class, property_name, property_type)

            # Create the class definition for the model view
            view_class = type(f'{class_name}View', (ModelView,), {
                'datamodel': SQLAInterface(model_class),
                'related_views': [f'{foreign_key_class_name}View'],
                'base_permissions': ['can_add', 'can_edit', 'can_delete', 'can_list']
            })

            # Create the class definition for the master detail view
            master_detail_view_class = type(f'{class_name}MasterDetailView', (MasterDetailView,), {
                'related_views': [f'{foreign_key_class_name}MasterDetailView'],
                'allow_view_edit': True,
                'title': f'{class_name} Details',
                'master': view_class,
                'datamodel': SQLAInterface(model_class),
                'base_permissions': ['can_add', 'can_edit', 'can_delete', 'can_list']
            })

            # Create the class definition for the foreign key view
            foreign_key_view_class = type(f'{foreign_key_class_name}View', (ModelView,), {
                'datamodel': SQLAInterface(foreign_key_model_class),
                'related_views': [f'{class_name}View'],
                'base_permissions': ['can_add', 'can_edit', 'can_delete', 'can_list']
            })

            # Create the class definition for the foreign key master detail view
            foreign_key_master_detail_view_class = type(f'{foreign_key_class_name}MasterDetailView', (MasterDetailView,), {
                'related_views': [f'{class_name}MasterDetailView'],
                'allow_view_edit': True,
                'title': f'{foreign_key_class_name} Details',
                'master': foreign_key_view_class,
                'child': view_class,
                'datamodel': SQLAInterface(foreign_key_model_class),
                'base_permissions': ['can_add', 'can_edit', 'can_delete', 'can_list']
            })

            # Register the model and views with the app builder instance
            appbuilder.add_model(model_class)
            appbuilder.add_model(foreign_key_model_class)
            appbuilder.add_view(view_class, class_name)
            appbuilder.add_view(foreign_key_view_class, foreign_key_class_name)
            appbuilder.add_view(master_detail_view_class, f'{class_name} MasterDetail')
            appbuilder.add_view(foreign_key_master_detail_view_class, f'{foreign_key_class_name} MasterDetail')

    # Write the views code to a views.py file
    views_file = Path('../views.py')
    views_file.write_text(appbuilder.get_views_code())

    # Write the models code to a models.py file
    models_file = Path('../models.py')
    models_file.write_text(appbuilder.get_models_code())

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please provide a database connection string as the only argument')
        sys.exit(1)

    db_uri = sys.argv[1]
    create_appbuilder_models(db_uri)