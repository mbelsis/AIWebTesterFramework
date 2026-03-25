"""
Modern OpenAI provider with the latest SDK features, JSON mode, and robust retry logic.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
import os
from dataclasses import dataclass
from enum import Enum

# Import redaction utilities for secure LLM communications
try:
    from utils.redaction import get_redactor, redact_text, redact_json, ContentType
    REDACTION_AVAILABLE = True
except ImportError:
    from enum import Enum
    REDACTION_AVAILABLE = False
    
    # Define minimal fallback to satisfy type checker
    class ContentType(Enum):
        TEXT = "text"
        JSON = "json"
        HTML = "html"
        XML = "xml"
        URL = "url"
    
    def get_redactor():
        return None

try:
    import backoff
    HAS_BACKOFF = True
except ImportError:
    backoff = None
    HAS_BACKOFF = False

try:
    from openai import OpenAI, AsyncOpenAI
    from openai.types.chat import ChatCompletion
    HAS_OPENAI = True
except ImportError:
    OpenAI = None
    AsyncOpenAI = None
    ChatCompletion = None
    HAS_OPENAI = False


logger = logging.getLogger(__name__)


def retry_on_exception(func):
    """Decorator that applies backoff if available, otherwise uses simple retry."""
    if HAS_BACKOFF and backoff is not None:
        return backoff.on_exception(
            backoff.expo,
            Exception,
            max_time=90,
            giveup=lambda e: "api_key" in str(e).lower() or "auth" in str(e).lower()
        )(func)
    else:
        # Simple retry wrapper if backoff not available
        def wrapper(*args, **kwargs):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    if "api_key" in str(e).lower() or "auth" in str(e).lower():
                        raise e
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    import time
                    time.sleep(wait_time)
        return wrapper


def async_retry_on_exception(func):
    """Async decorator that applies backoff if available, otherwise uses simple retry."""
    if HAS_BACKOFF and backoff is not None:
        return backoff.on_exception(
            backoff.expo,
            Exception,
            max_time=90,
            giveup=lambda e: "api_key" in str(e).lower() or "auth" in str(e).lower()
        )(func)
    else:
        # Simple async retry wrapper if backoff not available
        async def wrapper(*args, **kwargs):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    if "api_key" in str(e).lower() or "auth" in str(e).lower():
                        raise e
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(f"Async request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
        return wrapper


class OpenAIModel(Enum):
    """Supported OpenAI models with their capabilities."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    
    @property
    def supports_json_mode(self) -> bool:
        """Check if model supports JSON mode."""
        return True  # All modern models support JSON mode
    
    @property
    def max_tokens(self) -> int:
        """Maximum tokens for the model."""
        if self == OpenAIModel.GPT_4O_MINI:
            return 128000
        elif self == OpenAIModel.GPT_4_TURBO:
            return 128000
        elif self == OpenAIModel.GPT_4O:
            return 128000
        elif self == OpenAIModel.GPT_4:
            return 8192
        return 4096


@dataclass
class OpenAIResponse:
    """Structured response from OpenAI API."""
    content: str
    json_data: Optional[Dict[str, Any]] = None
    model_used: str = ""
    tokens_used: int = 0
    success: bool = True
    error_message: Optional[str] = None


class OpenAIProvider:
    """Modern OpenAI provider with robust retry logic and JSON mode support."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: OpenAIModel = OpenAIModel.GPT_4O_MINI,
                 max_retries: int = 5,
                 timeout: float = 90.0):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key. If not provided, tries to get from environment.
            model: OpenAI model to use for requests.
            max_retries: Maximum number of retry attempts.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize redaction if available
        self.redactor = None
        if REDACTION_AVAILABLE:
            try:
                self.redactor = get_redactor()
                if self.redactor and self.redactor.is_enabled():
                    logger.info("Security redaction enabled for OpenAI communications")
            except Exception as e:
                logger.warning(f"Failed to initialize redactor in OpenAI provider: {e}")
                self.redactor = None
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided. AI features will not be available.")
            self.client = None
            self.async_client = None
        else:
            if not HAS_OPENAI:
                raise ImportError("OpenAI library not available. Install with: pip install openai")
            
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
        
        logger.info(f"OpenAI provider initialized with model: {model.value}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return self.client is not None and self.api_key is not None
    
    @retry_on_exception
    def generate_completion(self,
                           messages: List[Dict[str, str]],
                           json_mode: bool = True,
                           temperature: float = 0.1,
                           max_tokens: Optional[int] = None,
                           **kwargs) -> OpenAIResponse:
        """
        Generate completion with retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            json_mode: Whether to use JSON response format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional parameters for the API call.
        
        Returns:
            OpenAIResponse object with completion data.
        """
        if not self.is_available():
            return OpenAIResponse(
                content="",
                success=False,
                error_message="OpenAI API key not available"
            )
        
        try:
            # Prepare redacted messages for logging
            redacted_messages = messages
            if self.redactor and self.redactor.is_enabled():
                try:
                    redacted_messages = [{
                        "role": msg["role"],
                        "content": self.redactor.redact_text(msg["content"], ContentType.TEXT)
                    } for msg in messages]
                except Exception as e:
                    logger.error(f"Error redacting messages for logging: {e}")
                    redacted_messages = messages
            
            # Build a local copy of messages to avoid mutating the caller's list
            api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

            # Ensure system message mentions JSON output when using JSON mode
            if json_mode and self.model.supports_json_mode:
                if api_messages and api_messages[0].get("role") == "system":
                    if "json" not in api_messages[0]["content"].lower():
                        api_messages[0]["content"] += "\n\nReturn your response as valid JSON."

            # Prepare request parameters (Responses API format)
            request_params = {
                "model": self.model.value,
                "input": api_messages,
                "temperature": temperature,
                **kwargs
            }

            # Add JSON mode using Responses API text format
            if json_mode and self.model.supports_json_mode:
                request_params["text"] = {"format": {"type": "json_object"}}

            # Set max_output_tokens if not provided
            if max_tokens is None:
                max_tokens = min(4096, self.model.max_tokens // 2)
            request_params["max_output_tokens"] = max_tokens

            logger.debug(f"Making OpenAI API request with {len(redacted_messages)} messages")

            # Make API call using Responses API
            if self.client is None:
                raise ValueError("OpenAI client not initialized")

            response = self.client.responses.create(**request_params)
            
            # Extract response data from Responses API
            content = response.output_text or ""
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            
            # Apply redaction to response content if needed
            if self.redactor and self.redactor.is_enabled():
                try:
                    content = self.redactor.redact_text(content, ContentType.TEXT)
                except Exception as e:
                    logger.error(f"Error redacting OpenAI response: {e}")
            
            # Parse JSON if in JSON mode
            json_data = None
            if json_mode and content.strip():
                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Try to extract JSON from response
                    json_data = self._extract_json_from_text(content)
            
            logger.info(f"OpenAI request successful. Tokens used: {tokens_used}")
            
            return OpenAIResponse(
                content=content,
                json_data=json_data,
                model_used=self.model.value,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            # Apply redaction to error messages that might contain sensitive data
            error_message = str(e)
            if self.redactor and self.redactor.is_enabled():
                try:
                    error_message = self.redactor.redact_text(error_message, ContentType.TEXT)
                except Exception as redact_error:
                    logger.error(f"Error redacting OpenAI error message: {redact_error}")
            
            logger.error(f"OpenAI API request failed: {error_message}")
            return OpenAIResponse(
                content="",
                success=False,
                error_message=error_message
            )
    
    @async_retry_on_exception
    async def generate_completion_async(self,
                                      messages: List[Dict[str, str]],
                                      json_mode: bool = True,
                                      temperature: float = 0.1,
                                      max_tokens: Optional[int] = None,
                                      **kwargs) -> OpenAIResponse:
        """
        Generate completion asynchronously with retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            json_mode: Whether to use JSON response format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional parameters for the API call.
        
        Returns:
            OpenAIResponse object with completion data.
        """
        if not self.is_available():
            return OpenAIResponse(
                content="",
                success=False,
                error_message="OpenAI API key not available"
            )
        
        try:
            # Prepare redacted messages for logging
            redacted_messages = messages
            if self.redactor and self.redactor.is_enabled():
                try:
                    redacted_messages = [{
                        "role": msg["role"],
                        "content": self.redactor.redact_text(msg["content"], ContentType.TEXT)
                    } for msg in messages]
                except Exception as e:
                    logger.error(f"Error redacting messages for logging: {e}")
                    redacted_messages = messages
            
            # Build a local copy of messages to avoid mutating the caller's list
            api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

            # Ensure system message mentions JSON output when using JSON mode
            if json_mode and self.model.supports_json_mode:
                if api_messages and api_messages[0].get("role") == "system":
                    if "json" not in api_messages[0]["content"].lower():
                        api_messages[0]["content"] += "\n\nReturn your response as valid JSON."

            # Prepare request parameters (Responses API format)
            request_params = {
                "model": self.model.value,
                "input": api_messages,
                "temperature": temperature,
                **kwargs
            }

            # Add JSON mode using Responses API text format
            if json_mode and self.model.supports_json_mode:
                request_params["text"] = {"format": {"type": "json_object"}}

            # Set max_output_tokens if not provided
            if max_tokens is None:
                max_tokens = min(4096, self.model.max_tokens // 2)
            request_params["max_output_tokens"] = max_tokens

            logger.debug(f"Making async OpenAI API request with {len(redacted_messages)} messages")

            # Make API call using Responses API
            if self.async_client is None:
                raise ValueError("OpenAI async client not initialized")

            response = await self.async_client.responses.create(**request_params)
            
            # Extract response data from Responses API
            content = response.output_text or ""
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            
            # Parse JSON if in JSON mode
            json_data = None
            if json_mode and content.strip():
                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Try to extract JSON from response
                    json_data = self._extract_json_from_text(content)
            
            logger.info(f"Async OpenAI request successful. Tokens used: {tokens_used}")
            
            return OpenAIResponse(
                content=content,
                json_data=json_data,
                model_used=self.model.value,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Async OpenAI API request failed: {str(e)}")
            return OpenAIResponse(
                content="",
                success=False,
                error_message=str(e)
            )
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try to extract JSON from text that might contain other content.
        
        Args:
            text: Text that might contain JSON.
        
        Returns:
            Parsed JSON data or None if no valid JSON found.
        """
        # Try to find JSON-like content between braces
        import re
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def generate_test_plan(self, 
                          page_analysis: Dict[str, Any], 
                          test_description: str = "") -> Dict[str, Any]:
        """
        Generate test plan using AI based on page analysis.
        
        Args:
            page_analysis: Analysis data from PageAnalyzer.
            test_description: Optional description of what to test.
        
        Returns:
            Dictionary containing the generated test plan.
        """
        if not self.is_available():
            logger.warning("OpenAI not available, falling back to rule-based generation")
            return self._generate_fallback_test_plan(page_analysis)
        
        # Prepare AI prompt
        prompt = self._create_test_plan_prompt(page_analysis, test_description)
        
        messages = [
            {
                "role": "system",
                "content": ("You are an expert QA engineer who creates comprehensive test plans. "
                           "Generate detailed, practical test steps based on the provided web page analysis. "
                           "Return valid JSON format with the structure specified in the user message.")
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Generate test plan
        response = self.generate_completion(
            messages=messages,
            json_mode=True,
            temperature=0.1
        )
        
        if response.success and response.json_data:
            logger.info("Successfully generated test plan with AI")
            return response.json_data
        else:
            logger.warning(f"AI generation failed: {response.error_message}, falling back to rule-based")
            return self._generate_fallback_test_plan(page_analysis)
    
    async def generate_test_plan_async(self, 
                                     page_analysis: Dict[str, Any], 
                                     test_description: str = "") -> Dict[str, Any]:
        """
        Generate test plan using AI asynchronously based on page analysis.
        
        Args:
            page_analysis: Analysis data from PageAnalyzer.
            test_description: Optional description of what to test.
        
        Returns:
            Dictionary containing the generated test plan.
        """
        if not self.is_available():
            logger.warning("OpenAI not available, falling back to rule-based generation")
            return self._generate_fallback_test_plan(page_analysis)
        
        # Prepare AI prompt
        prompt = self._create_test_plan_prompt(page_analysis, test_description)
        
        messages = [
            {
                "role": "system",
                "content": ("You are an expert QA engineer who creates comprehensive test plans. "
                           "Generate detailed, practical test steps based on the provided web page analysis. "
                           "Return valid JSON format with the structure specified in the user message.")
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Generate test plan
        response = await self.generate_completion_async(
            messages=messages,
            json_mode=True,
            temperature=0.1
        )
        
        if response.success and response.json_data:
            logger.info("Successfully generated test plan with AI")
            return response.json_data
        else:
            logger.warning(f"AI generation failed: {response.error_message}, falling back to rule-based")
            return self._generate_fallback_test_plan(page_analysis)
    
    def _create_test_plan_prompt(self, page_analysis: Dict[str, Any], test_description: str) -> str:
        """Create a detailed prompt for AI test plan generation."""
        
        # Extract relevant elements for prompt
        elements_summary = []
        for element in page_analysis.get("elements", []):
            if element.get("visible", False) and element.get("enabled", False):
                elements_summary.append({
                    "type": element.get("type", ""),
                    "selector": element.get("selector", ""),
                    "text": element.get("text", "")[:100],  # Limit text length
                    "input_type": element.get("input_type", ""),
                    "placeholder": element.get("placeholder", "")
                })
        
        prompt = f"""
Analyze this web page and generate a comprehensive test plan:

URL: {page_analysis.get("url", "")}
Page Title: {page_analysis.get("title", "")}
Page Type: {page_analysis.get("structure", {}).get("page_type", "unknown")}

Interactive Elements Found:
{json.dumps(elements_summary[:20], indent=2)}

Forms on Page:
{json.dumps(page_analysis.get("structure", {}).get("forms", []), indent=2)}

Test Description/Requirements: {test_description or "Create comprehensive tests covering all major functionality"}

Please generate a detailed test plan that:
1. Tests all critical user flows on this page
2. Validates form submissions and input validation  
3. Tests navigation and interactive elements
4. Includes appropriate verification steps
5. Uses realistic test data

Return the response as JSON with this exact structure:
{{
  "name": "Test Plan Name",
  "description": "Test plan description", 
  "steps": [
    {{
      "title": "Step description",
      "action": "navigate|fill|click|submit|wait|verify",
      "target": "CSS selector",
      "data": {{"value": "test data"}},
      "verification": {{"text": "expected text"}}
    }}
  ]
}}

Focus on practical, executable test steps that cover the main user journey.
"""
        
        return prompt
    
    def _generate_fallback_test_plan(self, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic test plan without AI as fallback.

        Delegates to PageAnalyzer's fallback which handles all common input types.
        """
        from orchestrator.page_analyzer import PageAnalyzer
        analyzer = PageAnalyzer.__new__(PageAnalyzer)
        return analyzer._generate_fallback_test_plan(page_analysis)