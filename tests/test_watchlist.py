def test_add_stock_to_watchlist(client):
    client.post("/users", json={"user_id": "ian"})

    response = client.post(
        "/users/ian/watchlist",
        json={"symbol": "AAPL"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"


def test_add_rule_to_stock(client):
    client.post("/users", json={"user_id": "ian"})
    client.post("/users/ian/watchlist", json={"symbol": "AAPL"})

    response = client.post(
        "/users/ian/watchlist/AAPL/rules",
        json={
            "rule_type": "price",
            "condition": "above",
            "target_value": 220,
            "cooldown_seconds": 300,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rule_type"] == "price"
    assert data["condition"] == "above"
    assert data["target_value"] == 220
