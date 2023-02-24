import string
from pathlib import Path
import random
from typing import Dict

import requests
from bs4 import BeautifulSoup
from google.cloud import firestore
from google.cloud.firestore_v1 import CollectionReference

from integrations.logins.parse_mail import get_message_content

LOGIN = "https://accounts.ft.com/login"

db = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
)

doc_ref: CollectionReference = db.collection("otps")

docs = doc_ref.stream()

list_in_first_tab = sorted(
    [doc for doc in docs], key=lambda x: x.create_time, reverse=True
)


def create_doc_id() -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase)
        for _ in range(15)
    )


def authenticate_news_site(service):
    with requests.Session() as sess:
        text = sess.get(LOGIN)
        doc = BeautifulSoup(text.text)
        _csrf = doc.find("input", value=True)["value"]
        data = {
            "_csrf": _csrf,
            "formType": "one-time-login-token",
            "formAction": "token-create",
            "email": "rprice1989aws@gmail.com",
            "rememberMe": "true",
            "siteKey": "ab5cba1f-f466-4cc5-bcc3-a77be0a9c5df",
        }
        sess.post(LOGIN, data)
        code_dict: Dict[str, str] = get_message_content(service)
        db = firestore.Client.from_service_account_json(
            f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
        )

        doc_ref: CollectionReference = db.collection("otps")

        docs = doc_ref.stream()

        list_in_first_tab = sorted(
            [doc for doc in docs], key=lambda x: x.create_time, reverse=True
        )
        # this is a mess!
        # (TODO) richard: design a mechanism to use the code received from FT if it's new. how to do that though!
        while code_dict.get("code") != list_in_first_tab[0].get("code"):
            code_dict: Dict[str, str] = get_message_content(service)
            docs = doc_ref.stream()
            list_in_first_tab = sorted(
                [doc for doc in docs], key=lambda x: x.create_time, reverse=True
            )
            if code_dict.get("code") == list_in_first_tab[0].get("code"):
                doc_ref.document(create_doc_id()).set({"code": code_dict.get("code")})
                docs = doc_ref.stream()
                list_in_first_tab = sorted(
                    [doc for doc in docs], key=lambda x: x.create_time, reverse=True
                )
            else:
                doc_ref.document(list_in_first_tab[0].id).set(
                    {"code": list_in_first_tab[0].get("code")}
                )
                docs = doc_ref.stream()
                list_in_first_tab = sorted(
                    [doc for doc in docs], key=lambda x: x.create_time, reverse=True
                )

        data_login_endpoint = {
            "_csrf": _csrf,
            "formType": "one-time-login-token",
            "formAction": "login-with-token",
            "email": "rprice1989aws@gmail.com",
            "rememberMe": "true",
            "ssoTokenForm": "false",
            "location": "",
            "token": code_dict.get("code"),
        }
        sess.post(LOGIN, data_login_endpoint)
