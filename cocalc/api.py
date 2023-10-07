import os
from logging import getLogger
from pathlib import Path
from uuid import uuid4

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from .exceptions import CocalcError

logger = getLogger(__file__)
load_dotenv()


class CocalcApiClient:
    def __init__(
        self,
        api_key=os.environ.get("COCALC_APIKEY"),
        project_id=os.environ.get("COCALC_PROJECTID"),
        base_url=os.environ.get("COCALC_BASEURL"),
    ):
        if not api_key:
            raise ValueError("COCALC_APIKEY is not set")
        self.api_key = api_key
        self.project_id = project_id
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

    def latex(
        self,
        path=None,
        content=None,
        command="latexmk -xelatex -f -g -bibtex -deps -synctex=1 -interaction=nonstopmode",
    ):
        params = {"project_id": self.project_id}

        path = Path(f"temp/{uuid4()}/main.tex" if not path else path)
        params.update(
            {
                "path": path,
                "content": content,
                "command": command,
            }
        )

        response_json = self._request(f"v2/latex", "POST", params).json()

        try:
            if (compile_msg := response_json["compile"])["event"] == "error":
                logger.error(compile_msg.get("error"))
                raise CocalcError(compile_msg.get("error"))
        finally:
            self._rm_dir(path.parent)

        return self._download_pdf(response_json["url"])

    def exec(self, command):
        params = {"command": command, "project_id": self.project_id}
        return self._request("v1/project_exec", "POST", params)

    def _rm_dir(self, path):
        return self.exec(f"rm -rf {path}")
