def test_create_user(client):
    response = client.post(
        "/users",
        json={"user_id": "ian", "phone_number": "+17325551234"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "ian"
    assert data["phone_number"] == "+17325551234"


def test_get_user(client):
    client.post("/users", json={"user_id": "ian"})

    response = client.get("/users/ian")
    assert response.status_code == 200
    assert response.json()["user_id"] == "ian"
