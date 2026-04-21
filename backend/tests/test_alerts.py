from unittest.mock import patch


def test_check_alerts_triggers_price_rule(client):
    client.post("/users", json={"user_id": "ian", "phone_number": "+17325551234"})
    client.post("/users/ian/watchlist", json={"symbol": "AAPL"})
    client.post(
        "/users/ian/watchlist/AAPL/rules",
        json={
            "rule_type": "price",
            "condition": "above",
            "target_value": 200,
            "cooldown_seconds": 300,
        },
    )

    fake_stock_data = {
        "symbol": "AAPL",
        "price": 250.0,
        "day_percent_change": 3.5,
    }

    with patch("app.alert_service.get_stock_data", return_value=fake_stock_data):
        with patch("app.alert_service.send_sms", return_value={"status": "queued"}):
            response = client.get("/users/ian/alerts/check")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["triggered"] is True
    assert results[0]["sms_sent"] is True
