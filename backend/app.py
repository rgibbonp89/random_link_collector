from __future__ import print_function

import flask

from backend.endpoints.existing_articles import articles_blue
from backend.endpoints.submit import submit_blue


app = flask.Flask(__name__)
app.register_blueprint(articles_blue)
app.register_blueprint(submit_blue)


@app.route("/main", endpoint="main")
def main():
    pass
