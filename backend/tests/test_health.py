def test_health_returns_200(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_payload_structure(client) -> None:
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "content_databases" in data
    for key in ("ege", "oge", "lectures"):
        assert key in data["content_databases"]
        entry = data["content_databases"][key]
        assert "path" in entry
        assert "exists" in entry
        assert isinstance(entry["exists"], bool)
