from flask_appbuilder import IndexView
from flask import render_template, url_for


class MyIndexView(IndexView):
    index_template = "my_index.html"
