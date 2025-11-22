"""AI service for interacting with language models."""

from typing import Optional, List, Dict, Any, AsyncGenerator
import json

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import settings


class AIService:
    """Service for AI-powered text generation and analysis."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = provider or settings.DEFAULT_AI_PROVIDER
        self.model = model or settings.DEFAULT_MODEL

        # Initialize clients
        self._openai_client = None
        self._anthropic_client = None

        if settings.OPENAI_API_KEY:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        if settings.ANTHROPIC_API_KEY:
            self._anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using the configured AI provider."""
        if self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, max_tokens, temperature)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, system_prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate text using OpenAI."""
        if not self._openai_client:
            raise ValueError("OpenAI API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate text using Anthropic."""
        if not self._anthropic_client:
            raise ValueError("Anthropic API key not configured")

        response = await self._anthropic_client.messages.create(
            model=self.model or "claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        return response.content[0].text

    async def stream_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream text generation for real-time output."""
        if self.provider == "openai":
            async for chunk in self._stream_openai(prompt, system_prompt, max_tokens, temperature):
                yield chunk
        elif self.provider == "anthropic":
            async for chunk in self._stream_anthropic(prompt, system_prompt, max_tokens, temperature):
                yield chunk
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _stream_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream text using OpenAI."""
        if not self._openai_client:
            raise ValueError("OpenAI API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self._openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _stream_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream text using Anthropic."""
        if not self._anthropic_client:
            raise ValueError("Anthropic API key not configured")

        async with self._anthropic_client.messages.stream(
            model=self.model or "claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def analyze_document(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze document content using AI."""
        prompts = {
            "general": """Analyze the following document and provide:
1. A brief summary (2-3 sentences)
2. Key points (bullet list)
3. Main topics covered
4. Any action items or requirements mentioned

Document:
{text}""",
            "guidelines": """Analyze these grant guidelines and extract:
1. Eligibility criteria
2. Application requirements
3. Evaluation criteria
4. Important deadlines
5. Budget constraints
6. Required proposal sections
7. Submission instructions

Guidelines:
{text}""",
            "beneficiary": """Analyze this beneficiary information and extract:
1. Organization overview
2. Key capabilities
3. Past experience relevant to grants
4. Target beneficiaries
5. Geographic focus
6. Financial capacity indicators

Information:
{text}""",
        }

        prompt = prompts.get(analysis_type, prompts["general"]).format(text=text[:15000])

        system_prompt = """You are an expert grant writing assistant. Provide structured,
actionable analysis. Format your response as JSON with clear sections."""

        response = await self.generate_text(prompt, system_prompt, temperature=0.3)

        # Try to parse as JSON, otherwise return as structured text
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"analysis": response}

    async def check_compliance(
        self,
        proposal_text: str,
        guidelines_text: str,
    ) -> Dict[str, Any]:
        """Check proposal compliance against guidelines."""
        prompt = f"""Compare this grant proposal against the provided guidelines and evaluate compliance.

GUIDELINES:
{guidelines_text[:8000]}

PROPOSAL:
{proposal_text[:8000]}

Provide a detailed compliance analysis including:
1. Overall compliance score (0-100)
2. Met requirements (list)
3. Missing requirements (list)
4. Suggestions for improvement
5. Word count compliance (if applicable)

Format your response as JSON."""

        system_prompt = """You are a grant compliance expert. Be thorough and precise
in your evaluation. Identify specific gaps and provide actionable recommendations."""

        response = await self.generate_text(prompt, system_prompt, temperature=0.2)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"analysis": response, "score": None}

    async def improve_section(
        self,
        section_content: str,
        section_name: str,
        guidelines: str,
        feedback: Optional[str] = None,
    ) -> str:
        """Improve a specific proposal section."""
        prompt = f"""Improve this grant proposal section based on the guidelines.

SECTION NAME: {section_name}

CURRENT CONTENT:
{section_content}

RELEVANT GUIDELINES:
{guidelines[:3000]}

{f'FEEDBACK TO ADDRESS: {feedback}' if feedback else ''}

Provide an improved version that:
1. Better aligns with guidelines
2. Uses stronger, more persuasive language
3. Includes specific, measurable outcomes
4. Maintains professional tone
5. Addresses any feedback provided

Return only the improved section content."""

        system_prompt = """You are an expert grant writer. Write compelling,
clear, and compliant proposal content."""

        return await self.generate_text(prompt, system_prompt, temperature=0.6)

    async def generate_executive_summary(
        self,
        full_proposal: str,
        max_words: int = 300,
    ) -> str:
        """Generate an executive summary from the full proposal."""
        prompt = f"""Create a compelling executive summary (maximum {max_words} words)
for this grant proposal:

{full_proposal[:10000]}

The executive summary should:
1. Clearly state the problem being addressed
2. Describe the proposed solution
3. Highlight expected outcomes and impact
4. Mention the organization's qualifications
5. State the funding request

Be concise, persuasive, and professional."""

        system_prompt = """You are an expert grant writer specializing in
executive summaries. Make every word count."""

        return await self.generate_text(prompt, system_prompt, temperature=0.5)
