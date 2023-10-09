import os
from logging import getLogger
from pathlib import Path
from uuid import uuid4

import requests
from requests.auth import HTTPBasicAuth

from . import constants
from .exceptions import CocalcError

logger = getLogger(__file__)


class CocalcApiClient:
    def __init__(
        self,
        *,
        api_key=os.environ.get(constants.COCALC_APIKEY_NAME),
        base_url=os.environ.get(constants.COCALC_BASEURL_NAME),
    ):
        if api_key is None:
            raise ValueError(f"{constants.COCALC_APIKEY_NAME} is not set")

        if base_url is None:
            raise ValueError(f"{constants.COCALC_BASEURL_NAME} is not set")

        self.api_key = api_key
        self.base_url = base_url

    def _request(self, endpoint, method="GET", data=None):
        auth = HTTPBasicAuth(self.api_key, None)
        return requests.request(
            method=method,
            url=f"{self.base_url}/{endpoint}",
            data=data,
            auth=auth,
        )

    def _download_pdf(self, url):
        return requests.get(url).content

    def latex(self, path=None, content=None, command=constants.COCALC_LATEX_COMMAND):
        path = Path(f"temp/{uuid4()}/main.tex" if not path else path)
        params = {
            "path": path,
            "content": content,
            "command": command,
        }

        response_json = self._request(f"v2/latex", "POST", params).json()

        try:
            if (compile_msg := response_json["compile"])["event"] == "error":
                logger.error(compile_msg.get("error"))
                raise CocalcError(compile_msg.get("error"))
        finally:
            self._rm_dir(path.parent)

        return self._download_pdf(response_json["url"])

    def exec(self, command):
        return self._request("v1/project_exec", "POST", {"command": command})

    def _rm_dir(self, path):
        return self.exec(f"rm -rf {path}")
