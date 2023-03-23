from __future__ import print_function

import json

from flask import Blueprint
from flask_cors import CORS
from googleapiclient.discovery import Resource

from backend.integrations.authenticate import (
    authenticate_user_and_provide_gmail_service,
)
from backend.integrations.submission_form import _submit_article


submit_blue = Blueprint("submitblue", __name__)
CORS(submit_blue)


@submit_blue.route("/submit", endpoint="submit", methods=["POST"])
def submit_article():
    service: Resource = authenticate_user_and_provide_gmail_service()
    _submit_article(service)
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
