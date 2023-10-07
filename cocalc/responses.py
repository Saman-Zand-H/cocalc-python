from abc import ABC


class BaseCoCalcResponse(ABC):
    def __init__(self, response):
        self.payload = response.json()


class LatexResponse(BaseCoCalcResponse):
    @property
    def pdf(self):
        return self.payload.get("pdf")
