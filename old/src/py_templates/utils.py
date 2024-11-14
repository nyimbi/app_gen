import sqlite3, re, string
from pathlib import Path
from typing import List, Dict

import sqlalchemy.types as types
import sqlparse
from pydbml import PyDBML
from sqlalchemy_utils import ChoiceType, ColorType, EmailType, IPAddressType, JSONType, PhoneNumberType, URLType
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword


# For writing a list of code to a file
def write_file(filename, list_of_strings):
    with open(filename, "w") as f:
        s = "\n".join(list_of_strings)
        f.write(s)
        # f.writelines(list_of_strings)



# This implements a lower case string
class LowerCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.lower()


class UpperCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.upper()


class TitleCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.title()


def snake_to_pascal(string):
    # split the string by underscores
    words = string.split('_')

    # capitalize the first letter of each word and join them
    return ''.join(word.capitalize() for word in words)

def snake_to_words(string):
    # split the string by underscores
    words = string.split('_')

    # capitalize the first letter of each word and join them
    return ' '.join(word.capitalize() for word in words)

def snake_to_camel(string):
    # split the string by underscores
    words = string.split('_')
    # capitalize the first letter of each word except the first one
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def snake_to_label(snake_str):
    components = snake_str.split('_')
    return ' '.join(word.capitalize() for word in components)


def camel_to_pascal(string):
    # capitalize the first letter of the string
    pascal = string.capitalize()

    # replace each instance of an uppercase letter with an underscore followed by the lowercase version of the same letter
    return pascal.replace('_', '')


def camel_to_snake(name):
    # create an empty string to hold the snake case name
    snake_case_name = ''
    # iterate over each character in the name
    for i, char in enumerate(name):
        # if the character is uppercase and not the first character
        if char.isupper() and i > 0:
            # add an underscore before the uppercase character
            snake_case_name += '_'
        # add the lowercase version of the character to the snake case name
        snake_case_name += char.lower()
    return snake_case_name


def pascal_to_camel(string):
    # convert the first letter of the string to lowercase
    camel = string[0].lower() + string[1:]

    # replace each instance of an uppercase letter with an underscore followed by the lowercase version of the same letter
    return camel.replace('_', '')


def pascal_to_snake(string):
    # insert an underscore before each uppercase letter and convert the entire string to lowercase
    return ''.join(['_' + letter.lower() if letter.isupper() else letter for letter in string]).lstrip('_')

def pascal_to_words(string):
    # Insert a space before each uppercase letter
    words = ''.join([' ' + letter if letter.isupper() else letter for letter in string]).strip()

    # Capitalize the first letter of each word
    return ' '.join(word.capitalize() for word in words.split())


# TODO rewrite parse_ddl to create the same output as parse_dbml
def parse_ddl(sql_file: str) -> Dict[str, Dict]:
    tables = {}
    current_table = None

    with open(sql_file) as f:
        stmts = sqlparse.parse(f.read())

    for stmt in stmts:
        if stmt.token_first(skip_ws=True).value.lower() == 'create':
            stmt_type = stmt.token_next(skip_ws=True).value.lower()

            if stmt_type == 'table':
                table_name = stmt.token_next(skip_ws=True).value
                columns = {}
                relationships = []

                for token in stmt.tokens:
                    if token.is_group:
                        if any(isinstance(t, Identifier) and t.value.lower() == 'primary' for t in token.tokens):
                            for sub_token in token.tokens:
                                if sub_token.is_group:
                                    for sub_sub_token in sub_token.tokens:
                                        if isinstance(sub_sub_token, Identifier):
                                            columns[sub_sub_token.value] = {
                                                'type': 'integer',
                                                'primary_key': True
                                            }
                        elif any(isinstance(t, Identifier) and t.value.lower() == 'foreign' for t in token.tokens):
                            for sub_token in token.tokens:
                                if isinstance(sub_token, Identifier):
                                    if current_table:
                                        col_name = sub_token.value
                                        ref_table = current_table
                                        relationships.append({
                                            'name': f'{ref_table}_{col_name}',
                                            'col1': col_name,
                                            'table1': table_name,
                                            'col2': 'id',
                                            'table2': ref_table,
                                            'bi_directional': True
                                        })

                    elif isinstance(token, IdentifierList):
                        for sub_token in token.tokens:
                            if isinstance(sub_token, Identifier):
                                col_name = sub_token.value

                                for sub_sub_token in sub_token.tokens:
                                    if isinstance(sub_sub_token, Keyword):
                                        col_type = sub_sub_token.value

                                columns[col_name] = {
                                    'type': col_type
                                }

            tables[table_name] = {
                'columns': columns,
                'relationships': relationships
            }
            current_table = table_name

    return tables


def parse_dbml_relationship(relationship_str):
    """
    Parses a relationship string into a human-readable format.

    Args:
        relationship_str (str): A string representing the relationship. Can be one of: "<", ">", "-", or "<>".

    Returns:
        A string representing the relationship in human-readable format.
    """
    if relationship_str == "<":
        return "one-to-many"
    elif relationship_str == ">":
        return "many-to-one"
    elif relationship_str == "-":
        return "one-to-one"
    elif relationship_str == "<>":
        return "many-to-many"
    else:
        return "unknown relationship type"


#
# def parse_dbml(dbml_file: str) -> List[dict]:
#     parsed = PyDBML(Path(dbml_file))
#     tables = []
#
#     for table in parsed.tables:
#         table_name = table.name
#         columns = {}
#         relationships = []
#
#         for column in table.columns:
#             column_name = column.name
#             column_type = column.type
#             nullable = not column.not_null
#             unique = column.unique
#             primary_key = column.pk
#
#             columns[column_name] = {
#                 'type': column_type,
#                 'nullable': nullable,
#                 'unique': unique,
#                 'primary_key': primary_key,
#             }
#
#         for constraint in table.get_refs():
#             name = constraint.name
#             col1 = constraint.col1[0]
#             table1 = constraint.table1
#             col2 = constraint.col2[0]
#             table2 = constraint.table2
#             relationships.append({
#                 'name': name,
#                 'col1': col1,
#                 'table1': table1,
#                 'col2': col2,
#                 'table2': table2,
#                 'bi_directional': True,
#             })
#
#         tables.append({
#             'table_name': table_name,
#             'columns': columns,
#             'relationships': relationships,
#         })
#
#     for table in tables:
#         for relationship in table['relationships']:
#             if relationship['bi_directional']:
#                 parent_table_name = relationship['table2'].name
#                 child_table_name = relationship['table1'].name
#                 parent_table = [t for t in tables if t['table_name'] == parent_table_name][0]
#                 parent_relationships = [r for r in parent_table['relationships'] if r['table1'].name == child_table_name]
#                 if not parent_relationships:
#                     parent_table['relationships'].append({
#                         'name': relationship['name'],
#                         'col1': relationship['col2'],
#                         'table1': relationship['table2'],
#                         'col2': relationship['col1'],
#                         'table2': relationship['table1'],
#                         'bi_directional': True,
#                     })
#
#     return tables

def parse_dbml(dbml_file: str) -> List[dict]:
    '''

    :param dbml_file:
    :return:
    {
        'table_name': table_name,
        'columns': columns,
        'relationships': relationships,
        }

        where:

        'table_name' is the name of the table.

        'columns' is a dictionary where each key is a column name and its value is another dictionary with the following keys:
        - 'type': the type of the column
        - 'nullable': whether the column is nullable or not
        - 'unique': whether the column is unique or not
        - 'primary_key': whether the column is a primary key or not

        'relationships' is a list of dictionaries representing relationships between tables, where each dictionary has the following keys:
        'name': the name of the relationship
        - 'col1': the column in table1
        - 'table1': the name of the first table in the relationship
        - 'col2': the column in table2
        - 'table2': the name of the second table in the relationship
        - 'bi_directional': whether the relationship is bi-directional or not
    '''
    parsed = PyDBML(Path(dbml_file))
    tables = []

    for table in parsed.tables:
        table_name = table.name
        columns = {}
        relationships = []

        for column in table.columns:
            column_name = column.name
            column_type = column.type
            is_nullable = not column.not_null
            is_unique = column.unique
            is_primary_key = column.pk

            columns[column_name] = {
                'type': column_type,
                'is_nullable': is_nullable,
                'is_unique': is_unique,
                'is_primary_key': is_primary_key,
                'is_foreign': False,
            }

        for constraint in table.get_refs():
            col1 = constraint.col1[0]
            col2 = constraint.col2[0]
            table1 = constraint.table1
            table2 = constraint.table2
            columns[col1.name]['is_foreign'] = True
            relationships.append({
                'name': None,
                'col1': col1,
                'table1': table1,
                'col2': col2,
                'table2': table2,
                'bi_directional': True,
            })

        tables.append({
            'table_name': table_name,
            'columns': columns,
            'relationships': relationships,
        })

    return tables


def save_to_sqlite(tables, db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    def create_tables(conn):
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS appTables (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL unique
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS appColumns (
                id INTEGER PRIMARY KEY,
                table_id INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                is_nullable INTEGER NOT NULL,
                is_unique INTEGER NOT NULL,
                is_primary_key INTEGER NOT NULL,
                is_foreign INTEGER NOT NULL,
                FOREIGN KEY (table_id) REFERENCES appTables(id),
                unique(table_name, name)
                
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS appRelations (
                id INTEGER PRIMARY KEY,
                parent_table_name TEXT NOT NULL,
                parent_table_id INTEGER NOT NULL,
                child_table_name TEXT NOT NULL,
                child_table_id INTEGER NOT NULL,
                parent_column_id INTEGER NOT NULL,
                child_column_id INTEGER NOT NULL,
                bi_directional INTEGER NOT NULL,
                FOREIGN KEY (parent_table_id) REFERENCES appTables(id),
                FOREIGN KEY (child_table_id) REFERENCES appTables(id),
                FOREIGN KEY (parent_column_id) REFERENCES appColumns(id),
                FOREIGN KEY (child_column_id) REFERENCES appColumns(id)
            )
        ''')
        conn.commit()

    def insert_data(conn, tables):
        cursor = conn.cursor()

        for table in tables:
            table_name = table['table_name']
            columns = table['columns']
            relationships = table['relationships']

            table_data = (table_name,)
            cursor.execute("""
                INSERT OR IGNORE INTO appTables (name)
                VALUES (?)
            """, table_data)
            table_id = cursor.lastrowid  ## Keep this for this iteration

            for column_name, column_info in columns.items():
                column_data = (table_id, table_name, column_name, column_info['type'], column_info['is_nullable'],
                               column_info['is_unique'], column_info['is_primary_key'], column_info['is_foreign'])
                cursor.execute("""
                    INSERT OR IGNORE INTO appColumns (table_id, table_name, name, type, is_nullable, is_unique, is_primary_key, is_Foreign)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, column_data)

        # Iterate again to sort out relationships
        for table in tables:
            table_name = table['table_name']
            columns = table['columns']
            relationships = table['relationships']
            for relationship in relationships:
                parent_table_id = table_id
                bi_directional = relationship['bi_directional']

                s = "SELECT id FROM appTables WHERE name='{}'".format(table_name)
                print('parent_table_id', s)
                parent_table_id = cursor.execute(s).fetchone()[0]

                s = "SELECT id FROM appTables WHERE name='{}'".format(relationship['table2'].name)
                print('child_table_id', relationship['table2'].name, s)
                child_table_id = cursor.execute(s).fetchone()[0]
                print(child_table_id)

                s = "SELECT id FROM appColumns WHERE table_id={} AND name='{}'".format(table_id,
                                                                                       relationship['col1'].name)
                print('parent_column_id', s)
                parent_column_id = cursor.execute(s).fetchone()
                print('parent_column_id:', parent_column_id)

                s = "SELECT id FROM appColumns WHERE table_id={} AND name='{}'".format(child_table_id,
                                                                                       relationship['col2'].name)
                print(s)
                child_column_id = cursor.execute(s).fetchone()[0]

                relationship_data = (
                    parent_table_id, table_name, child_table_id,
                    f"{relationship['table2'].name}", parent_column_id, child_column_id,
                    relationship['bi_directional'])
                if any(value is None for value in relationship_data):
                    continue
                cursor.execute("""
                                INSERT OR IGNORE INTO appRelations (parent_table_id, parent_table_name, child_table_id, child_table_name, 
                                parent_column_id, child_column_id, bi_directional)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, relationship_data)

        conn.commit()

    create_tables(conn)
    insert_data(conn, tables)


# Usage
# config_file = "config.py"
# setting_to_update = "SQLALCHEMY_DATABASE_URI"
# new_value = "your_new_database_uri"
# update_config_setting(config_file, setting_to_update, new_value)
def update_config_setting(config_file, setting, value):
    # Read the original content of the config file
    with open(config_file, "r") as file:
        lines = file.readlines()

    # Update the specific setting with the new value
    with open(config_file, "w") as file:
        for line in lines:
            if line.startswith(setting):
                file.write(f"{setting} = '{value}'\n")
            else:
                file.write(line)
# Selects the best display name given a list of column names

