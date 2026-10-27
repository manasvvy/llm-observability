import time
import json
import os
from fastapi import APIRouter
from pydantic import BaseModel
import anthropic

router = APIRouter()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024

@router.post("/chat")
def chat(request: LLMRequest):
    start = time.time()
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=request.max_tokens,
        messages=[{"role": "user", "content": request.prompt}]
    )
    
    latency = round(time.time() - start, 3)
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    reply = response.content[0].text

    log = {
        "prompt": request.prompt,
        "latency_seconds": latency,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }

    with open("logs.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")

    return {
        "reply": reply,
        "latency_seconds": latency,
        "tokens_used": input_tokens + output_tokens
    }