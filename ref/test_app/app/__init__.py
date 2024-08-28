import logging

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA

# from flask_graphql import GraphQLView
# from graphql_server.flask import GraphQLView
# from graphql import GraphQLSchema
# from graphene import Schema

from app.index import MyIndexView

# from .gql_schema import schema
"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
# appbuilder = AppBuilder(app, db.session)
appbuilder = AppBuilder(app, db.session, indexview=MyIndexView)


"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

from . import models, views, api  # , gql_schema

# app.add_url_rule(
#     "/graphql", view_func=GraphQLView.as_view("graphql", graphql_schema=schema, graphiql=True))
#
#
# app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
#     'graphql',
#     schema=schema,
#     graphiql=True,
# ))
# #
# # Optional, for adding batch query support (used in Apollo-Client)
# app.add_url_rule('/graphql/batch', view_func=GraphQLView.as_view(
#     'graphql',
#     schema=schema,
#     batch=True
# ))
