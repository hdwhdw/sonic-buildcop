"""HTTP session factory with default timeout configuration."""

import requests
from requests.adapters import HTTPAdapter


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that applies default timeout to all requests."""

    def __init__(
        self,
        *args,
        timeout: tuple[float, float] = (30.0, 60.0),
        **kwargs,
    ):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        """Send with default timeout if none specified."""
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def create_session(
    timeout: tuple[float, float] = (30.0, 60.0),
) -> requests.Session:
    """Create a requests.Session with default timeout on all requests.

    Args:
        timeout: (connect_timeout, read_timeout) in seconds.
                 Default: (30, 60) per CFG-03.

    Returns:
        Configured requests.Session.
    """
    session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=timeout)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
