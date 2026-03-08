import uuid
import logging
import asyncio
import httpx

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from config import settings
from services.upstox_feed import connect_upstox_feed

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active token
active_tokens = {}


@router.get("/login")
async def login():
    """
    Redirect user to Upstox OAuth login.
    """

    state = str(uuid.uuid4())

    auth_url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code"
        f"&client_id={settings.UPSTOX_API_KEY}"
        f"&redirect_uri={settings.UPSTOX_REDIRECT_URI}"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str):
    """
    Exchange authorization code for access token.
    """

    token_url = "https://api.upstox.com/v2/login/authorization/token"

    payload = {
        "code": code,
        "client_id": settings.UPSTOX_API_KEY,
        "client_secret": settings.UPSTOX_API_SECRET,
        "redirect_uri": settings.UPSTOX_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if response.status_code != 200:

            logger.error(response.text)

            raise HTTPException(
                status_code=400,
                detail="Token exchange failed"
            )

        token_data = response.json()

        access_token = token_data.get("access_token")

        if not access_token:

            raise HTTPException(
                status_code=400,
                detail="No access token received"
            )

        # Store token
        active_tokens["upstox"] = access_token

        # Start market feed
        asyncio.create_task(connect_upstox_feed(access_token))

        return {
            "status": "login_success",
            "message": "Upstox authentication successful"
        }

    except Exception as e:

        logger.error(f"OAuth error: {e}")

        raise HTTPException(
            status_code=500,
            detail="OAuth process failed"
        )
