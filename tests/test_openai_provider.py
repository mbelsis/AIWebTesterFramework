"""
Tests for the OpenAI provider — availability checks, fallback logic, JSON extraction.
Does not call the real OpenAI API.
"""

import pytest
from unittest.mock import patch, MagicMock
from providers.openai_provider import OpenAIProvider, OpenAIModel, OpenAIResponse


class TestOpenAIProviderInit:
    def test_no_api_key_marks_unavailable(self):
        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAIProvider(api_key=None)
            assert not provider.is_available()
            assert provider.client is None
            assert provider.async_client is None

    def test_api_key_from_param(self):
        provider = OpenAIProvider(api_key="sk-test-fake-key-1234567890")
        assert provider.is_available()
        assert provider.api_key == "sk-test-fake-key-1234567890"

    def test_default_model(self):
        provider = OpenAIProvider(api_key="sk-test-fake-key-1234567890")
        assert provider.model == OpenAIModel.GPT_4O_MINI


class TestOpenAIModel:
    def test_all_models_support_json_mode(self):
        for model in OpenAIModel:
            assert model.supports_json_mode is True

    def test_max_tokens(self):
        assert OpenAIModel.GPT_4O.max_tokens == 128000
        assert OpenAIModel.GPT_4.max_tokens == 8192


class TestExtractJsonFromText:
    def test_extracts_json_object(self):
        provider = OpenAIProvider(api_key=None)
        text = 'Here is the result: {"name": "test", "value": 42} end.'
        result = provider._extract_json_from_text(text)
        assert result == {"name": "test", "value": 42}

    def test_returns_none_for_no_json(self):
        provider = OpenAIProvider(api_key=None)
        result = provider._extract_json_from_text("no json here")
        assert result is None

    def test_handles_nested_json(self):
        provider = OpenAIProvider(api_key=None)
        text = '{"outer": {"inner": [1, 2, 3]}}'
        result = provider._extract_json_from_text(text)
        assert result["outer"]["inner"] == [1, 2, 3]


class TestGenerateCompletionUnavailable:
    def test_returns_failure_when_no_api_key(self):
        provider = OpenAIProvider(api_key=None)
        result = provider.generate_completion(
            messages=[{"role": "user", "content": "test"}]
        )
        assert isinstance(result, OpenAIResponse)
        assert result.success is False
        assert "not available" in result.error_message


class TestFallbackTestPlan:
    def test_fallback_generates_navigation_step(self):
        provider = OpenAIProvider(api_key=None)
        page_analysis = {
            "url": "https://app.com/login",
            "title": "Login",
            "structure": {"page_type": "login", "forms": []},
            "elements": [
                {"type": "inputs", "input_type": "email", "visible": True, "enabled": True,
                 "selector": "#email", "placeholder": "Email", "name": "email", "id": "email",
                 "tag": "input", "text": ""},
                {"type": "inputs", "input_type": "password", "visible": True, "enabled": True,
                 "selector": "#pass", "placeholder": "Password", "name": "password", "id": "pass",
                 "tag": "input", "text": ""},
                {"type": "buttons", "input_type": "submit", "visible": True, "enabled": True,
                 "selector": "button", "text": "Login", "name": "", "id": "",
                 "tag": "button"},
            ],
        }
        plan = provider._generate_fallback_test_plan(page_analysis)
        assert plan["name"].startswith("Generated Test")

        actions = [s["action"] for s in plan["steps"]]
        assert "navigate" in actions
        assert "fill" in actions  # Should fill email AND password now

        # Check that password field is filled (this was the bug — it used to skip non-text types)
        fill_targets = [s["target"] for s in plan["steps"] if s["action"] == "fill"]
        assert "#email" in fill_targets
        assert "#pass" in fill_targets

    def test_fallback_handles_empty_elements(self):
        provider = OpenAIProvider(api_key=None)
        plan = provider._generate_fallback_test_plan({
            "url": "https://app.com",
            "title": "Empty",
            "structure": {"page_type": "content"},
            "elements": [],
        })
        assert len(plan["steps"]) == 1  # Just navigate
        assert plan["steps"][0]["action"] == "navigate"
