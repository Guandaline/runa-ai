# src/nala/athomic/ai/llm/providers/google_genai_provider.py
"""
Google GenAI implementation for LLM using the unified SDK (v2).
Supports both Vertex AI (GCP) and AI Studio execution modes.
"""

import json
from http import HTTPStatus
from typing import (  # Added AsyncIterator
    Any,
    AsyncIterator,
    List,
    Optional,
    Type,
    TypeVar,
)

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.llm.exceptions import (
    AuthenticationError,
    ContextWindowExceededError,
    InvalidRequestError,
    ProviderError,
    ProviderInitializationError,
    RateLimitError,
    StructuredOutputError,
)
from nala.athomic.ai.schemas import ToolCall
from nala.athomic.ai.schemas.llms import (  # Added LLMResponseChunk
    LLMResponse,
    LLMResponseChunk,
    TokenUsage,
)
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.config.schemas.ai import GoogleGenAIProviderSettings

T = TypeVar("T", bound=BaseModel)


class GoogleGenAIProvider(BaseLLM[GoogleGenAIProviderSettings]):
    """
    Unified adapter for Google's GenAI models (Gemini) using the `google-genai` SDK.

    This provider supersedes specific Vertex implementations by leveraging the
    unified SDK which handles both Vertex AI (GCP) and AI Studio endpoints.
    It currently utilizes `GoogleGenAIProviderSettings` for configuration compatibility.
    """

    def __init__(self, connection_settings: Any) -> None:
        """
        Initializes the Google GenAI provider.

        Args:
            connection_settings: The configuration object containing backend credentials
                                 and model parameters.
        """
        super().__init__(connection_settings)
        self._client: Optional[genai.Client] = None

    async def _connect(self) -> None:
        """
        Initializes the Google GenAI Client.

        Detects the operating mode based on settings (Vertex AI vs AI Studio).
        If `project_id` and `location` are present, it initializes in Vertex AI mode.
        Otherwise, it falls back to standard mode (AI Studio) which requires an API Key.
        """
        try:
            # Current mapping assumes Vertex mode if project_id/location are present
            use_vertex = bool(self.settings.project_id and self.settings.location)

            api_key = None
            if self.settings.api_key:
                api_key = self.settings.api_key.get_secret_value()

            self._client = genai.Client(
                vertexai=use_vertex,
                project=self.settings.project_id,
                location=self.settings.location,
                api_key=api_key,
            )
        except Exception as e:
            raise ProviderInitializationError(
                self.service_name, f"Failed to initialize Google GenAI Client: {e}"
            ) from e

    async def _close(self) -> None:
        """
        Closes the underlying client resources.

        The `google-genai` client manages its own connection pool, but this hook
        ensures protocol compliance for graceful shutdowns.
        """
        pass

    def _convert_tools(self, tools: List[AIToolProtocol]) -> Optional[List[types.Tool]]:
        """
        Converts Athomic AITools into GenAI Tool/FunctionDeclaration format.

        Args:
            tools: A list of objects implementing the AIToolProtocol.

        Returns:
            A list of `types.Tool` objects compatible with the GenAI SDK, or None if empty.
        """
        if not tools:
            return None

        function_declarations = []
        for tool in tools:
            # The SDK expects OpenAPI-compatible schemas
            func_decl = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.schema,
            )
            function_declarations.append(func_decl)

        return [types.Tool(function_declarations=function_declarations)]

    def _parse_response(self, response: types.GenerateContentResponse) -> LLMResponse:
        """
        Normalizes the GenAI response into a Athomic LLMResponse.

        Delegates extraction logic to specialized helper methods to reduce cognitive complexity.

        Args:
            response: The raw response object from the GenAI SDK.

        Returns:
            A standardized LLMResponse object containing content, tool calls, and usage metrics.
        """
        # Handle edge case: No candidates returned
        if not response.candidates:
            return LLMResponse(
                finish_reason="unknown",
                model=self.default_model,
                usage=self._extract_usage(response),
            )

        candidate = response.candidates[0]

        return LLMResponse(
            content=self._extract_content(candidate),
            tool_calls=self._extract_tool_calls(candidate),
            finish_reason=self._resolve_finish_reason(candidate),
            usage=self._extract_usage(response),
            model=self.default_model,
        )

    def _extract_content(self, candidate: Any) -> Optional[str]:
        """
        Extracts and concatenates text parts from the candidate.

        Args:
            candidate: A single generation candidate from the response.

        Returns:
            The concatenated text content, or None if no text parts exist.
        """
        if not candidate.content or not candidate.content.parts:
            return None

        text_parts = [part.text for part in candidate.content.parts if part.text]

        return "".join(text_parts) if text_parts else None

    def _extract_tool_calls(self, candidate: Any) -> List[ToolCall]:
        """
        Iterates through content parts to extract function calls.

        Args:
            candidate: A single generation candidate from the response.

        Returns:
            A list of normalized ToolCall objects.
        """
        tool_calls: List[ToolCall] = []

        if not candidate.content or not candidate.content.parts:
            return tool_calls

        for part in candidate.content.parts:
            if not part.function_call:
                continue

            fc = part.function_call
            # Ensure args are dict; SDK usually returns Map/Dict
            args = fc.args if isinstance(fc.args, dict) else {}

            call_id = f"call_{fc.name}_{id(fc)}"

            tool_calls.append(
                ToolCall(
                    id=call_id,
                    name=fc.name,
                    arguments=args,
                )
            )

        return tool_calls

    def _resolve_finish_reason(self, candidate: Any) -> str:
        """
        Determines the stop reason for the generation.

        Args:
            candidate: A single generation candidate.

        Returns:
            The finish reason as a string (e.g., 'STOP', 'MAX_TOKENS').
        """
        if candidate.finish_reason:
            return candidate.finish_reason.name
        return "unknown"

    def _extract_usage(self, response: types.GenerateContentResponse) -> TokenUsage:
        """
        Normalizes token usage metadata from the response.

        Args:
            response: The raw response object.

        Returns:
            A TokenUsage object with prompt and completion token counts.
        """
        if not response.usage_metadata:
            return TokenUsage()

        return TokenUsage(
            prompt_tokens=response.usage_metadata.prompt_token_count or 0,
            completion_tokens=response.usage_metadata.candidates_token_count or 0,
            total_tokens=response.usage_metadata.total_token_count or 0,
        )

    async def _generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates content using the GenAI model.

        Overrides the base method to implement the specific call logic for the
        google-genai SDK, including tool conversion and parameter mapping.

        Args:
            prompt: The user prompt.
            system_message: Optional system instruction.
            tools: List of tools available to the model.
            **kwargs: Additional generation parameters (e.g., temperature).

        Returns:
            A normalized LLMResponse.

        Raises:
            ProviderInitializationError: If client is not connected.
            ProviderError: If the API call fails.
        """
        if not self._client:
            raise ProviderInitializationError(self.service_name, "Client not connected")

        genai_tools = self._convert_tools(tools)
        gen_defaults = self.connection_settings.generation

        # Configuration mapping
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", gen_defaults.temperature),
            max_output_tokens=kwargs.get("max_tokens", gen_defaults.max_output_tokens),
            top_p=kwargs.get("top_p", gen_defaults.top_p),
            top_k=kwargs.get("top_k", gen_defaults.top_k),
            stop_sequences=kwargs.get("stop", gen_defaults.stop_sequences),
            system_instruction=system_message,
            tools=genai_tools,
        )

        try:
            # Using the AsyncIO capabilities of the new client
            response = await self._client.aio.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=config,
            )
            return self._parse_response(response)

        except errors.ClientError as e:
            self._handle_genai_error(e)
            raise ProviderError(f"GenAI Client error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error in GoogleGenAI provider: {e}") from e

    async def _stream_generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Streams the LLM response chunks using the Google GenAI API.

        Args:
            prompt: The user prompt.
            system_message: Optional system instruction.
            tools: List of tools available to the model.
            **kwargs: Additional generation parameters.

        Yields:
            LLMResponseChunk: Incremental response objects.

        Raises:
            ProviderInitializationError: If the client is not connected.
            ProviderError: If the API call fails or returns an error.
        """
        if not self._client:
            raise ProviderInitializationError(self.service_name, "Client not connected")

        genai_tools = self._convert_tools(tools)
        gen_defaults = self.connection_settings.generation

        # Configuration mapping
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", gen_defaults.temperature),
            max_output_tokens=kwargs.get("max_tokens", gen_defaults.max_output_tokens),
            top_p=kwargs.get("top_p", gen_defaults.top_p),
            top_k=kwargs.get("top_k", gen_defaults.top_k),
            stop_sequences=kwargs.get("stop", gen_defaults.stop_sequences),
            system_instruction=system_message,
            tools=genai_tools,
        )

        try:
            # Use the streaming method from the async client
            stream = self._client.aio.models.generate_content_stream(
                model=self.default_model,
                contents=prompt,
                config=config,
            )

            # Process the Stream
            async for chunk in stream:
                content_delta = (
                    self._extract_content(chunk.candidates[0])
                    if chunk.candidates
                    else None
                )
                finish_reason = (
                    self._resolve_finish_reason(chunk.candidates[0])
                    if chunk.candidates
                    else None
                )
                usage_model = None

                # Usage and token counts often come in the final chunk's usage_metadata
                if chunk.usage_metadata:
                    usage_model = TokenUsage(
                        prompt_tokens=chunk.usage_metadata.prompt_token_count or 0,
                        completion_tokens=chunk.usage_metadata.candidates_token_count
                        or 0,
                        total_tokens=chunk.usage_metadata.total_token_count or 0,
                    )

                # Yield incremental data if present
                if content_delta or finish_reason or usage_model:
                    yield LLMResponseChunk(
                        content_delta=content_delta,
                        finish_reason=finish_reason,
                        usage=usage_model,
                        model=self.default_model,
                    )

        except errors.ClientError as e:
            self._handle_genai_error(e)
            raise ProviderError(f"GenAI streaming Client error: {e}") from e
        except Exception as e:
            raise ProviderError(
                f"Unexpected error in GoogleGenAI streaming provider: {e}"
            ) from e

    async def _generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Generates structured output using GenAI's native schema enforcement.

        Leverages the `response_schema` and `response_mime_type` capabilities of the
        Gemini models to ensure the output strictly adheres to the requested Pydantic model.

        Args:
            prompt: The user prompt.
            response_model: The Pydantic model class defining the expected structure.
            system_message: Optional system instruction.
            max_retries: Number of internal retries (not used by native schema enforcement, but kept for protocol).
            **kwargs: Additional generation parameters.

        Returns:
            An instance of `response_model` populated with the generated data.

        Raises:
            StructuredOutputError: If the output cannot be parsed into the model.
            ProviderError: If the API call fails.
        """
        if not self._client:
            raise ProviderInitializationError(self.service_name, "Client not connected")

        gen_defaults = self.connection_settings.generation
        json_schema = response_model.model_json_schema()

        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", gen_defaults.temperature),
            max_output_tokens=kwargs.get("max_tokens", gen_defaults.max_output_tokens),
            top_p=kwargs.get("top_p", gen_defaults.top_p),
            system_instruction=system_message,
            response_mime_type="application/json",
            response_schema=json_schema,
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self.default_model,
                contents=prompt,
                config=config,
            )

            if response.usage_metadata:
                self.record_token_usage(
                    prompt_tokens=response.usage_metadata.prompt_token_count or 0,
                    completion_tokens=response.usage_metadata.candidates_token_count
                    or 0,
                )

            raw_content = response.text

            if not raw_content:
                raise StructuredOutputError(
                    response_model.__name__, "Empty response from GenAI."
                )

            try:
                cleaned_content = self._sanitize_json_markdown(raw_content)
                parsed_json = json.loads(cleaned_content)
                return response_model(**parsed_json)
            except (json.JSONDecodeError, ValidationError) as e:
                raise StructuredOutputError(
                    response_model.__name__, f"Failed to parse output: {e}"
                ) from e

        except errors.ClientError as e:
            self._handle_genai_error(e)
            raise ProviderError(f"GenAI Client error: {e}") from e
        except StructuredOutputError:
            # Allow StructuredOutputError to propagate without being wrapped in ProviderError
            raise
        except Exception as e:
            raise ProviderError(f"Unexpected error in GoogleGenAI provider: {e}") from e

    def _sanitize_json_markdown(self, text: str) -> str:
        """
        Removes potential markdown code blocks from a JSON response string.

        Args:
            text: The raw string response from the model.

        Returns:
            A cleaned string ready for JSON parsing.
        """
        if "```json" in text:
            text = text.split("```json")[1]
            if "```" in text:
                text = text.split("```")[0]
        elif "```" in text:
            text = text.strip("`")
        return text.strip()

    def _handle_genai_error(self, e: Exception) -> None:
        """
        Maps Google GenAI SDK errors to standardized Athomic exceptions.
        Uses HTTPStatus codes from the exception object where available for robustness.

        Args:
            e: The original exception raised by the SDK.

        Raises:
            RateLimitError: For 429/Quota errors.
            AuthenticationError: For 401/403 errors.
            InvalidInputError: For 400 errors.
            ContextWindowExceededError: For context length violations.
            ProviderError: For generic 500 or unknown errors.
        """
        # Attempts to extract status code safely; falls back to None if missing
        code = getattr(e, "code", None)
        error_str = str(e).lower()

        if (
            code == HTTPStatus.TOO_MANY_REQUESTS
            or "429" in error_str
            or "quota" in error_str
        ):
            raise RateLimitError(f"GenAI rate limit exceeded: {e}") from e

        if (
            code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
            or "401" in error_str
            or "403" in error_str
            or "permission" in error_str
        ):
            raise AuthenticationError(f"GenAI auth failed: {e}") from e

        if (
            code == HTTPStatus.BAD_REQUEST
            or "400" in error_str
            or "invalid" in error_str
        ):
            if "context" in error_str and "length" in error_str:
                raise ContextWindowExceededError(
                    model=self.default_model, token_count=0, limit=0
                ) from e
            raise InvalidRequestError(f"Invalid request to GenAI: {e}") from e

        # Fallback for unknown client errors
        raise ProviderError(f"GenAI API error ({code}): {e}") from e
