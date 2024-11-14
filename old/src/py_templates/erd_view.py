from flask_appbuilder import BaseView, expose
from flask import render_template
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.engine import reflection
from src import appbuilder
# For the chart drawing module

class ERDView(BaseView):
    default_view = 'render'

    @expose('/')
    def render(self):
        # retrieve information about the tables in the database using SQLAlchemy's metadata object
        engine = create_engine(appbuilder.app.config['SQLALCHEMY_DATABASE_URI'])
        metadata = MetaData(bind=engine)
        metadata.reflect()

        nodes = []
        edges = []

        for table_name, table in metadata.tables.items():
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type':  column.type.compile(engine.dialect),
                    'pk': column.primary_key,
                    # add other characteristics as needed
                })
            nodes.append({
                'id': table,
                'label': table,
                'columns': columns,
            })

            for foreign_key in inspector.get_foreign_keys(table):
                edges.append({
                    'from': foreign_key['referred_table'],
                    'to': table,
                    'bifurcation': True,
                })

            for index in inspector.get_indexes(table):
                if index['unique'] and len(index['column_names']) == 1:
                    edges.append({
                        'from': index['column_names'][0],
                        'to': table,
                    })

        return render_template('erd_template.html', nodes=nodes, edges=edges)


    @expose('/save', methods=['POST']) # TODO Tidy this up
    def save(self):
        # Get the database engine and metadata
        engine = self.get_engine()
        metadata = MetaData(bind=engine)

        # Get the current state of the database
        inspector = inspect(engine)
        current_tables = sorted(inspector.get_table_names())
        current_columns = {
            table: sorted(col['name'] for col in inspector.get_columns(table))
            for table in current_tables
        }
        current_foreign_keys = {
            foreign_key['constrained_columns'][0]: {
                'table': foreign_key['referred_table'],
                'column': foreign_key['referred_columns'][0],
            }
            for foreign_key in inspector.get_foreign_keys()
        }

        # Get the changes submitted by the user
        changes = request.form.getlist('changes')
        accepted_changes = []

        for change in changes:
            action, table, column, data = change.split('|')
            if action == 'add_column':
                column_name, column_type, is_primary_key, is_unique = data.split(',')
                column_args = []
                if is_primary_key:
                    column_args.append(PrimaryKeyConstraint())
                if is_unique:
                    column_args.append(UniqueConstraint())
                column = Column(column_name, column_type, *column_args)
                table_object = Table(table, metadata, autoload=True)
                table_object.create_column(column)
                accepted_changes.append(change)
            elif action == 'delete_column':
                table_object = Table(table, metadata, autoload=True)
                table_object.c[column].drop()
                accepted_changes.append(change)
            elif action == 'add_relationship':
                _, foreign_key_table, foreign_key_column = data.split(',')
                foreign_key = ForeignKey(
                    f'{foreign_key_table}.{foreign_key_column}',
                    onupdate='CASCADE',
                    ondelete='CASCADE',
                )
                table_object = Table(table, metadata, autoload=True)
                table_object.append_column(foreign_key)
                accepted_changes.append(change)

        # Generate a list of changes to be confirmed by the user
        unconfirmed_changes = []
        for table in sorted(current_tables):
            if table not in request.form:
                continue
            for column in current_columns[table]:
                column_data = request.form[f'{table}.{column}']
                if column_data == 'delete':
                    change = f'delete_column|{table}|{column}|'
                    unconfirmed_changes.append(change)
                elif column_data.startswith('foreign_key:'):
                    foreign_key_table, foreign_key_column = column_data.split(':')[1:]
                    change = f'add_relationship|{table}|{column}|{foreign_key_table},{foreign_key_column}'
                    unconfirmed_changes.append(change)

        # Show the user the changes to be confirmed
        return self.render_template(
            'confirm_changes.html',
            unconfirmed_changes=unconfirmed_changes,
            accepted_changes=accepted_changes,
        )