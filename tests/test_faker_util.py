"""
Tests for the SeededFaker utility — deterministic test data generation.
"""

import pytest
from data_gen.faker_util import SeededFaker, get_run_specific_faker, clear_faker_cache


@pytest.fixture(autouse=True)
def clean_cache():
    clear_faker_cache()
    yield
    clear_faker_cache()


class TestSeededFaker:
    def test_same_run_id_same_data(self):
        f1 = SeededFaker("run-abc")
        f2 = SeededFaker("run-abc")
        assert f1.user_profile() == f2.user_profile()

    def test_different_run_id_different_data(self):
        f1 = SeededFaker("run-abc")
        f2 = SeededFaker("run-xyz")
        assert f1.user_profile()["username"] != f2.user_profile()["username"]

    def test_user_profile_fields(self):
        f = SeededFaker("test-run")
        profile = f.user_profile()
        required_keys = [
            "first_name", "last_name", "full_name", "username",
            "email", "phone", "date_of_birth", "job_title", "company"
        ]
        for key in required_keys:
            assert key in profile, f"Missing key: {key}"
            assert profile[key], f"Empty value for: {key}"

    def test_user_profile_cache(self):
        f = SeededFaker("test-run")
        p1 = f.user_profile()
        p2 = f.user_profile()
        assert p1 == p2  # Cached

    def test_user_profile_no_cache_produces_different_data(self):
        f = SeededFaker("test-run")
        p1 = f.user_profile(cache=True)
        p2 = f.user_profile(cache=False)
        # The uncached call advances the Faker state, so it will differ
        assert p1["first_name"] != p2["first_name"] or p1["username"] != p2["username"]

    def test_email_contains_run_suffix(self):
        f = SeededFaker("myrun123")
        email = f.email()
        assert "myrun1" in email  # get_run_id_suffix returns first 6 chars
        assert "@" in email

    def test_address_data_fields(self):
        f = SeededFaker("test-run")
        addr = f.address_data()
        assert "street_address" in addr
        assert "city" in addr
        assert "postal_code" in addr

    def test_payment_data_uses_test_cards(self):
        f = SeededFaker("test-run")
        pay = f.payment_data()
        test_cards = ["4111111111111111", "5555555555554444", "378282246310005"]
        assert pay["card_number"] in test_cards
        assert len(pay["cvv"]) == 3

    def test_form_data_maps_common_fields(self):
        f = SeededFaker("test-run")
        data = f.form_data(["email", "password", "first_name", "unknown_field"])
        assert "@" in data["email"]
        assert data["password"] == "TestPass123!"
        assert data["first_name"]  # Not empty
        assert data["unknown_field"]  # Falls back to sentence

    def test_reset_cache(self):
        f = SeededFaker("test-run")
        f.user_profile()
        assert len(f._cache) > 0
        f.reset_cache()
        assert len(f._cache) == 0


class TestGetRunSpecificFaker:
    def test_returns_same_instance(self):
        f1 = get_run_specific_faker("run-a")
        f2 = get_run_specific_faker("run-a")
        assert f1 is f2

    def test_different_runs_different_instances(self):
        f1 = get_run_specific_faker("run-a")
        f2 = get_run_specific_faker("run-b")
        assert f1 is not f2
