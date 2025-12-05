import os

import pytest

from fieldflux.app import FieldFluxApp, PermissionError


@pytest.fixture
def app():
    os.environ["DATABASE_URL"] = "postgresql://example"
    os.environ["MAPS_API_KEY"] = "fake-map-key"
    os.environ["ANALYTICS_WRITE_KEY"] = "segment-key"
    instance = FieldFluxApp()
    admin = instance.register_user("alice", "admin")
    editor = instance.register_user("edgar", "editor")
    viewer = instance.register_user("victor", "viewer")
    return instance, admin, editor, viewer


def test_authentication_success(app):
    instance, admin, _, _ = app
    user = instance.authenticate(admin.username)
    assert user.token
    assert user.username == admin.username


def test_authentication_failure(app):
    instance, *_ = app
    with pytest.raises(PermissionError):
        instance.authenticate("ghost")
    assert instance.error_monitor.errors[-1]["error"] == "auth_failed"


def test_crud_flow_and_permissions(app):
    instance, admin, editor, viewer = app

    created = instance.create_field(admin, name="Prairie", crop="Corn", acres="120")
    fetched = instance.get_field(admin, created.id)
    assert fetched.name == "Prairie"

    updated = instance.update_field(editor, created.id, crop="Soybeans", irrigation="drip")
    assert updated.crop == "Soybeans"
    assert updated.attributes["irrigation"] == "drip"

    with pytest.raises(PermissionError):
        instance.update_field(viewer, created.id, crop="Wheat")

    with pytest.raises(PermissionError):
        instance.delete_field(editor, created.id)

    instance.delete_field(admin, created.id)
    assert created.id not in instance.fields


def test_list_permissions(app):
    instance, _, _, viewer = app
    record = None
    if viewer.role == "admin":
        record = instance.create_field(viewer, name="Public Plot", crop="Barley")

    # viewer should be able to list even with no create permission
    assert instance.list_fields(viewer) == ([] if record is None else [record])


def test_read_operations_return_copies(app):
    instance, admin, _, viewer = app
    created = instance.create_field(admin, name="Prairie", crop="Corn", acres="120")

    fetched = instance.get_field(viewer, created.id)
    fetched.name = "Tampered"
    fetched.attributes["acres"] = "999"

    original = instance.get_field(admin, created.id)
    assert original.name == "Prairie"
    assert original.attributes["acres"] == "120"

    listed = instance.list_fields(viewer)[0]
    listed.attributes["acres"] = "0"
    assert instance.fields[created.id].attributes["acres"] == "120"


def test_healthcheck_tracks_env_flags(app):
    instance, *_ = app
    health = instance.healthcheck()
    assert health["db_url_configured"] is True
    assert health["map_api_key_configured"] is True
    assert health["analytics_key_configured"] is True


def test_telemetry_captures_events(app):
    instance, admin, *_ = app
    instance.create_field(admin, name="Telemetry", crop="Corn")
    assert any(event.get("event") == "field_created" for event in instance.logger.events)
