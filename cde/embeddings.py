import hashlib
import os
from google import genai
from google.genai import types

async def embed_question(text: str) -> dict:
    normalized = " ".join(text.split())
    if not normalized or len(normalized) > 12000:
        raise ValueError("Question embedding text must be 1–12000 characters")
        
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    model_id = "text-embedding-004"
    
    config = types.EmbedContentConfig(
        output_dimensionality=768
    )
    
    response = await client.aio.models.embed_content(
        model=model_id,
        contents=normalized,
        config=config
    )
    
    vector = response.embeddings[0].values
    if len(vector) != 768:
        raise ValueError("Unexpected embedding dimension")
        
    return {
        "embedding": vector, 
        "model": model_id,
        "input_sha256": hashlib.sha256(normalized.encode()).hexdigest()
    }
