#####################################################
#                                                   #
#                Notion OAuth 라우터                 #
#                                                   #
#####################################################

import os
import secrets
import base64
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from tools.notion.store import upsert_workspace, set_webhook_info, set_incoming_secret
from logs.logging_util import LoggerSingleton
import logging


logger = LoggerSingleton.get_logger(logger_name="notion_oauth", level=logging.INFO)

router = APIRouter(prefix="/notion", tags=["notion"])


NOTION_API_BASE = os.getenv("NOTION_API_BASE", "https://api.notion.com")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
CLIENT_ID = os.getenv("NOTION_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "")

# 단일 엔드포인트(콜백) URL - 사용자별 동일 URL 사용
WEBHOOK_CALLBACK_URL = os.getenv("NOTION_WEBHOOK_CALLBACK_URL", "")


def _require_env_vars() -> None:
    missing = [
        ("NOTION_CLIENT_ID", CLIENT_ID),
        ("NOTION_CLIENT_SECRET", CLIENT_SECRET),
        ("NOTION_REDIRECT_URI", REDIRECT_URI),
        ("NOTION_WEBHOOK_CALLBACK_URL", WEBHOOK_CALLBACK_URL),
    ]
    not_set = [name for name, value in missing if not value]
    if not_set:
        raise HTTPException(status_code=500, detail=f"환경변수 누락: {', '.join(not_set)}")


@router.get("/oauth/start")
async def notion_oauth_start() -> RedirectResponse:
    _require_env_vars()
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": REDIRECT_URI,
    }
    authorize_url = f"{NOTION_API_BASE}/v1/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(authorize_url)


@router.get("/oauth/callback")
async def notion_oauth_callback(code: str, state: str | None = None):
    _require_env_vars()
    token_url = f"{NOTION_API_BASE}/v1/oauth/token"

    basic_token = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {basic_token}",
        # OAuth 토큰 교환에는 보통 Notion-Version이 필요 없지만, 보내도 무방합니다.
        "Notion-Version": NOTION_VERSION,
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(token_url, headers=headers, json=payload)
        if resp.status_code >= 400:
            logger.error("Notion 토큰 교환 실패: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=500, detail="Notion 토큰 교환 실패")

        data = resp.json()
        access_token = data.get("access_token")
        workspace_id = data.get("workspace_id")
        bot_id = data.get("bot_id")

        if not access_token or not workspace_id:
            logger.error("토큰 응답 누락: %s", data)
            raise HTTPException(status_code=500, detail="Notion 토큰 응답 누락")

        # 워크스페이스 정보 저장
        upsert_workspace(workspace_id=workspace_id, access_token=access_token, bot_id=bot_id)

        # 사용자 고유 시크릿 발급 (자동화 Webhook 호출 헤더로 사용)
        incoming_secret = secrets.token_hex(32)
        set_incoming_secret(workspace_id=workspace_id, secret=incoming_secret)

    return JSONResponse({
        "ok": True,
        "workspace_id": workspace_id,
        # Notion 자동화에서 사용할 사용자 고유 시크릿과 콜백 URL 안내
        "automation": {
            "callback_url": WEBHOOK_CALLBACK_URL,
            "header_name": "X-Notion-Automation-Secret",
            "header_value": incoming_secret,
        },
    })


async def _create_user_webhook(*, access_token: str, workspace_id: str, callback_url: str, webhook_secret: str) -> str | None:
    """Notion 웹훅 구독을 생성합니다. 엔드포인트 사양 변화에 견고하도록 필드명을 호환 처리합니다."""
    create_urls = [
        f"{NOTION_API_BASE}/v1/webhooks",
        f"{NOTION_API_BASE}/v1/subscriptions",
    ]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    # 요청 본문 후보 (사양 차이에 대비)
    bodies = [
        {"name": "EasyConnect Webhook", "url": callback_url, "secret": webhook_secret, "active": True},
        {"callback_url": callback_url, "secret": webhook_secret, "workspace_id": workspace_id},
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        for url in create_urls:
            for body in bodies:
                try:
                    resp = await client.post(url, headers=headers, json=body)
                    if resp.status_code < 300:
                        resp_json = resp.json()
                        webhook_id = (
                            resp_json.get("id")
                            or resp_json.get("webhook_id")
                            or resp_json.get("subscription_id")
                        )
                        logger.info("웹훅 생성 성공 url=%s id=%s", url, webhook_id)
                        return webhook_id
                    else:
                        logger.warning("웹훅 생성 실패 url=%s code=%s body=%s resp=%s", url, resp.status_code, body, resp.text)
                except Exception as e:
                    logger.exception("웹훅 생성 시 예외: %s", e)

    return None


