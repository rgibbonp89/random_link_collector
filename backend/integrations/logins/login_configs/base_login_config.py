# noqa
from typing import Dict, Union, Optional, Callable

from google.cloud.firestore_v1 import CollectionReference
from googleapiclient.discovery import Resource
import abc

from requests import Session


class SiteConfig(abc.ABC):
    search_query_gmail: str
    login_url: str
    firestore_session_id: str
    data_login_redirect: Dict = None
    data_login_endpoint: Dict = None

    @abc.abstractmethod
    def extract_login_code_from_mail(
        self, msg_str: str, message: Resource
    ) -> Dict[str, str]:
        pass

    @abc.abstractmethod
    def request_code_for_login_and_create_session(
        self,
        service: Resource,
        search_query: str,
        sess: Session,
        doc_ref: CollectionReference,
    ) -> Session:
        pass
