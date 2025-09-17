def test_search_trips_public(client):
    r = client.get("/api/v1/trips/search", query_string={
        "from_lat": 5.35, "from_lon": -4.01, "to_lat": 6.81, "to_lon": -5.27,
        "radius_km": 80
    })
    assert r.status_code == 200
    trips = r.get_json()
    assert isinstance(trips, list)
    assert len(trips) >= 1
