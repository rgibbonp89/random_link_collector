from typing import Callable
from backend.integrations.utils.utils import _make_db_connection
from backend.batch_jobs.batch_update_config import add_site_label, add_read_status


def batch_update_db_with_new_key_value(
    key_name: str, new_value_func: Callable, **kwargs
) -> None:
    db, doc_ref, _, _ = _make_db_connection()
    for d in list(doc_ref.stream()):
        updated_value = new_value_func(d, **kwargs)
        doc_ref.document(d.id).update({key_name: updated_value})


batch_update_db_with_new_key_value("ReadStatus", add_read_status)
