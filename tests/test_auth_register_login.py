def test_register_and_login(client):
    # register
    r = client.post("/api/v1/users/auth/register", json={"email":"alice@test.ci","password":"pwd","first_name":"Alice"})
    assert r.status_code in (200, 201)
    # login
    r = client.post("/api/v1/users/auth/login", json={"identifier":"alice@test.ci","password":"pwd"})
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "access_token" in data and "user" in data
