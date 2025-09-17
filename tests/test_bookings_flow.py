def test_booking_and_payment_flow(client, auth_headers, driver_headers):
    # 1) un trip existe via conftest (driver@test.ci)
    # on récupère un trip publié
    r = client.get("/api/v1/trips/search", query_string={
        "from_lat": 5.35, "from_lon": -4.01, "to_lat": 6.81, "to_lon": -5.27, "radius_km": 100
    })
    trip_id = r.get_json()[0]["id"]

    # 2) créer une booking (passager)
    r = client.post("/api/v1/bookings", headers=auth_headers, json={"trip_id": trip_id, "seats": 1})
    assert r.status_code in (200, 201)
    booking = r.get_json()
    booking_id = booking["id"]

    # si auto_accept, la booking est déjà "accepted", sinon driver accepte :
    if booking["status"] == "pending":
        r = client.post(f"/api/v1/bookings/{booking_id}/accept", headers=driver_headers, json={})
        assert r.status_code == 200

    # 3) init paiement (passager)
    r = client.post("/api/v1/payments/init", headers=auth_headers, json={"booking_id": booking_id, "method":"wave"})
    assert r.status_code == 200
    payload = r.get_json()["data"]
    pref = payload["provider"]["provider_ref"]

    # 4) webhook provider → paid
    r = client.post(f"/api/v1/payments/webhook/wave", json={"provider_ref": pref, "status":"paid"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "paid"

    # 5) vérifier booking → paid
    r = client.get(f"/api/v1/bookings/{booking_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["status"] == "paid"
