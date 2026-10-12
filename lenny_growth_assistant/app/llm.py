import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

async def generate(prompt: str, system: str = "") -> str:
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        url = settings.ollama_base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": settings.ollama_model,
            "stream": False,
            "messages": ([{"role": "system", "content": system}] if system else []) +
                        [{"role": "user", "content": prompt}],
            "options": {  "num_predict": 250,"temperature": 0.2}
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as exc:
            logger.exception("ollama_request_failed")
            raise RuntimeError("Ollama is unavailable. Start Ollama and pull the configured model.") from exc
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic.")
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=90)
            result = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=4000,
                system=system or "You are a careful assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return "".join(block.text for block in result.content if getattr(block, "type", "") == "text")
        except Exception as exc:
            logger.exception("anthropic_request_failed")
            raise RuntimeError("Anthropic request failed. Check the API key, model, and connectivity.") from exc
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")
