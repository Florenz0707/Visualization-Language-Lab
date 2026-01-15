"""LLM API endpoints."""

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from src.services.llm import LLMFactory

router = APIRouter()

# Initialize LLM factory (singleton)
llm_factory = LLMFactory()


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(
        ..., description="User message text", min_length=1, max_length=10000
    )
    system_prompt: str | None = Field(
        None, description="Optional system prompt", max_length=5000
    )


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="LLM response text")
    model: str = Field(..., description="Model name used")


@router.post("/llm/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with LLM using default model.

    Args:
        request: Chat request with user message

    Returns:
        ChatResponse with LLM response text

    Raises:
        HTTPException: If LLM service fails
    """
    try:
        # Get default provider
        provider = llm_factory.get_provider()

        if not provider:
            logger.error("Failed to get LLM provider")
            raise HTTPException(status_code=503, detail="LLM service unavailable")

        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})

        # Get response (non-streaming)
        response_text = provider.chat(messages, stream=False)

        logger.info(f"LLM chat completed using model: {provider.model_name}")

        return ChatResponse(response=response_text, model=provider.model_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM service error: {str(e)}")
