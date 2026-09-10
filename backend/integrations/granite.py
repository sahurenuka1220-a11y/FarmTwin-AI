"""
IBM Granite & watsonx Integration
Handles all AI model calls with Demo Mode fallback
"""
import os
import json
import httpx
import asyncio
from typing import Optional, Dict, Any

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_TEXT_MODEL = os.getenv("GRANITE_TEXT_MODEL", "ibm/granite-13b-instruct-v2")
GRANITE_VISION_MODEL = os.getenv("GRANITE_VISION_MODEL", "ibm/granite-vision-3-2b")


async def get_iam_token() -> Optional[str]:
    """Get IBM Cloud IAM token from API key"""
    if DEMO_MODE or not WATSONX_API_KEY or WATSONX_API_KEY == "demo_key":
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": WATSONX_API_KEY
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
    except Exception as e:
        print(f"IAM token error: {e}")
    return None


async def granite_text_inference(prompt: str, max_tokens: int = 512) -> str:
    """Call IBM Granite text model for inference"""
    if DEMO_MODE or not WATSONX_API_KEY or WATSONX_API_KEY in ("demo_key", "your_watsonx_api_key_here"):
        return None  # Signal to use demo response

    token = await get_iam_token()
    if not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {
                "model_id": GRANITE_TEXT_MODEL,
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "stop_sequences": ["Human:", "###"]
                },
                "project_id": WATSONX_PROJECT_ID
            }
            resp = await client.post(
                f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["results"][0]["generated_text"].strip()
    except Exception as e:
        print(f"Granite inference error: {e}")
    return None


async def granite_vision_inference(image_path: str, prompt: str) -> Dict[str, Any]:
    """Call IBM Granite Vision model for crop disease analysis"""
    if DEMO_MODE or not WATSONX_API_KEY or WATSONX_API_KEY in ("demo_key", "your_watsonx_api_key_here"):
        return None  # Signal to use demo response

    token = await get_iam_token()
    if not token:
        return None

    try:
        import base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        ext = image_path.split(".")[-1].lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        async with httpx.AsyncClient(timeout=90) as client:
            payload = {
                "model_id": GRANITE_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                "parameters": {"max_new_tokens": 512},
                "project_id": WATSONX_PROJECT_ID
            }
            resp = await client.post(
                f"{WATSONX_URL}/ml/v1/text/chat?version=2024-01-15",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                return {"raw_response": text}
    except Exception as e:
        print(f"Granite vision error: {e}")
    return None
