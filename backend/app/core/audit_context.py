from contextvars import ContextVar
from typing import Optional

request_ip: ContextVar[Optional[str]] = ContextVar("request_ip", default=None)


def get_request_ip() -> Optional[str]:
    return request_ip.get()
