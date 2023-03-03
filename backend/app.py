from __future__ import print_function

from backend.integrations.authenticate import (
    authenticate_user_and_provide_gmail_service,
)
from backend.submission_form.submission_form import create_text_submission_form
import flask

from backend.pages.articles import articles_blue


app = flask.Flask(__name__)
app.register_blueprint(articles_blue)


@app.route("/home", endpoint="home", methods=["POST"])
def main():
    service = authenticate_user_and_provide_gmail_service()
    create_text_submission_form(service)
