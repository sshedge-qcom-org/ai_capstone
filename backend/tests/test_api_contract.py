import json
import re
from pathlib import Path

from app.main import app


def normalized(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


def test_postman_covers_every_api_operation_with_protected_profile():
    root = Path(__file__).resolve().parents[2]
    collection = json.loads((root / "postman/procurement.postman_collection.json").read_text())
    covered = set()
    for item in collection["item"]:
        request = item["request"]
        path = request["url"].replace("{{base_url}}", "").split("?")[0]
        path = re.sub(r"\{\{[^}]+\}\}", "{}", path)
        covered.add((request["method"].lower(), "/api/v1" + path))
        if path == "/auth/me":
            assert request.get("auth", {}).get("type") != "noauth"
        assert item["event"][0]["script"]["exec"]
    required = {
        (method, normalized(path))
        for path, methods in app.openapi()["paths"].items()
        for method in methods
    }
    assert not required - covered
    assert all(
        not variable["value"]
        for variable in collection["variable"]
        if variable["key"] in ("password", "access_token")
    )
