from __future__ import print_function

import flask
from flask_cors import CORS
from backend.endpoints.existing_articles import articles_blue
from backend.endpoints.submit import submit_blue


app = flask.Flask(__name__, static_folder="build", static_url_path="/")
app.register_blueprint(articles_blue)
app.register_blueprint(submit_blue)

CORS(app)


@app.route("/")
def main():
    return app.send_static_file("index.html")
