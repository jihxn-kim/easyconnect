#####################################################
#                                                   #
#             Notion 웹훅 수신/검증 라우터             #
#                                                   #
#####################################################

import hmac
import hashlib
import json
from typing import Optional, Tuple

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from tools.notion.store import (
    list_webhook_secrets,
    get_workspace_id_by_webhook_id,
    get_workspace_id_by_incoming_secret,
)
from logs.logging_util import LoggerSingleton
import logging


logger = LoggerSingleton.get_logger(logger_name="notion_webhook", level=logging.INFO)

router = APIRouter(prefix="/notion", tags=["notion-webhook"])


def _get_signature_from_headers(request: Request) -> Optional[str]:
    candidates = [
        "X-Notion-Signature",
        "x-notion-signature",
        "Notion-Signature",
        "notion-signature",
        # 자동화용 사용자 시크릿 헤더
        "X-Notion-Automation-Secret",
        "x-notion-automation-secret",
    ]
    for key in candidates:
        value = request.headers.get(key)
        if value:
            return value
    return None


def _constant_time_equals(a: str, b: str) -> bool:
    try:
        return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
    except Exception:
        return False


def _formats(body: bytes, secret: str) -> Tuple[str, str]:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return digest, f"sha256={digest}"


def _match_signature(body: bytes, signature_header: str) -> Optional[str]:
    """저장된 모든 시크릿에 대해 시그니처를 비교하여 일치하는 webhook_id를 반환합니다."""
    for webhook_id, secret in list_webhook_secrets():
        raw, prefixed = _formats(body, secret)
        if _constant_time_equals(signature_header, raw) or _constant_time_equals(signature_header, prefixed):
            return webhook_id
    return None


@router.post("/webhook")
async def notion_webhook(request: Request):
    # challenge 핸드셰이크 지원
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    # Notion/일반 웹훅에서 종종 challenge 필드 사용
    if isinstance(payload, dict) and payload.get("challenge"):
        return JSONResponse({"challenge": payload.get("challenge")})

    signature = _get_signature_from_headers(request)

    workspace_id = None

    # 1) 공식 웹훅 서명(HMAC) 검증 경로
    matched_webhook_id = None
    if signature and signature.lower().startswith("sha256="):
        matched_webhook_id = _match_signature(raw_body, signature)
        if not matched_webhook_id:
            logger.warning("시그니처 불일치")
            raise HTTPException(status_code=401, detail="invalid signature")
        workspace_id = get_workspace_id_by_webhook_id(matched_webhook_id)

    # 2) 자동화 비밀 헤더 경로
    if not workspace_id:
        automation_secret = request.headers.get("X-Notion-Automation-Secret") or request.headers.get("x-notion-automation-secret")
        if automation_secret:
            workspace_id = get_workspace_id_by_incoming_secret(automation_secret)
            if not workspace_id:
                logger.warning("자동화 시크릿 불일치")
                raise HTTPException(status_code=401, detail="invalid automation secret")

    if not workspace_id:
        # 페이로드에 workspace_id가 있으면 보강
        workspace_id = (
            (payload or {}).get("workspace_id")
            or (payload or {}).get("workspaceId")
        )

    if not workspace_id:
        logger.warning("워크스페이스 식별 실패 webhook_id=%s", matched_webhook_id)
        raise HTTPException(status_code=400, detail="workspace not found")

    # 이벤트 처리
    try:
        await _handle_events(workspace_id=workspace_id, payload=payload)
    except Exception as e:
        logger.exception("이벤트 처리 오류: %s", e)
        # 2xx가 아니면 재시도 정책을 유발할 수 있음. 처리 실패는 200으로 흡수하고 내부 알림으로 대체 가능
    return JSONResponse({"ok": True})


async def _handle_events(*, workspace_id: str, payload: dict) -> None:
    """이벤트 유형별 처리. 필요에 맞게 확장."""
    event_type = payload.get("type") or payload.get("event") or "unknown"
    logger.info("workspace=%s event=%s", workspace_id, event_type)

    # 단일/배치 모두 지원
    items = []
    if isinstance(payload, dict):
        if "events" in payload and isinstance(payload["events"], list):
            items = payload["events"]
        else:
            items = [payload]

    for item in items:
        _log_item(workspace_id, item)


def _log_item(workspace_id: str, item: dict) -> None:
    page_id = (
        item.get("page_id")
        or item.get("pageId")
        or item.get("data", {}).get("id")
    )
    logger.info("[NOTION] ws=%s page=%s item_keys=%s", workspace_id, page_id, list(item.keys()))


