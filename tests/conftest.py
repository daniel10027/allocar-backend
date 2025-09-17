import pytest
from app import create_app
from extensions.db import db

@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        JWT_SECRET_KEY="test",
        SECRET_KEY="test",
        PROPAGATE_EXCEPTIONS=True,
    )
    with app.app_context():
        db.create_all()
        # seed minimal pour tests : un user + un driver + un trip
        from common.security import hash_password
        from domain.users.models import User
        from domain.trips.models import Trip
        from datetime import datetime, timedelta, timezone
        from decimal import Decimal

        u = User(email="test@user.ci", password_hash=hash_password("pwd"), first_name="Test", role="user")
        d = User(email="driver@test.ci", password_hash=hash_password("pwd"), first_name="Driver", role="user")
        db.session.add_all([u, d]); db.session.commit()

        t = Trip(
            driver_id=d.id,
            origin_lat=5.3575, origin_lon=-4.0083, origin_text="Abidjan, Plateau",
            destination_lat=6.8190, destination_lon=-5.2760, destination_text="Yamoussoukro",
            departure_time=datetime.now(timezone.utc)+timedelta(hours=12),
            price_per_seat=Decimal("6000"),
            seats_available=3,
            allow_auto_accept=True,
            status="published",
        )
        db.session.add(t); db.session.commit()

    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def auth_headers(client):
    # login test user
    r = client.post("/api/v1/users/auth/register", json={"email":"p@t.ci","password":"pwd","first_name":"P"})
    assert r.status_code in (200, 201)
    r = client.post("/api/v1/users/auth/login", json={"identifier":"p@t.ci","password":"pwd"})
    token = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def driver_headers(client):
    # login driver
    r = client.post("/api/v1/users/auth/login", json={"identifier":"driver@test.ci","password":"pwd"})
    token = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
