from __future__ import print_function

import json

from flask import Blueprint

from backend.integrations.authenticate import (
    authenticate_user_and_provide_gmail_service,
)
from backend.integrations.submission_form import _submit_article


submit_blue = Blueprint("submitblue", __name__)


@submit_blue.route("/submit", endpoint="submit", methods=["POST"])
def submit_article():
    service = authenticate_user_and_provide_gmail_service()
    _submit_article(service)
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
