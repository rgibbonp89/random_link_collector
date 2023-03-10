from google.cloud.firestore_v1 import DocumentSnapshot
from urllib.parse import urlparse


def add_site_label(doc: DocumentSnapshot) -> str:
    url = doc.to_dict().get("URL")
    return urlparse(url).netloc
