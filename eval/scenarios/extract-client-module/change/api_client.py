import json
from http.client import HTTPSConnection

API_HOST = "api.example.internal"


def get_json(path: str) -> dict:
    connection = HTTPSConnection(API_HOST)
    connection.request("GET", path)
    response = connection.getresponse()
    return json.loads(response.read())
