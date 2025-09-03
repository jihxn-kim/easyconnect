#####################################################
#                                                   #
#            Notion 워크스페이스 저장소 모듈            #
#                                                   #
#####################################################

import json
import os
import threading
from typing import Dict, Optional, Any, List, Tuple


_STORE_DIR = os.path.join(os.getcwd(), "data")
_STORE_FILE = os.path.join(_STORE_DIR, "notion_store.json")
_LOCK = threading.Lock()


def _ensure_store_file() -> None:
    if not os.path.isdir(_STORE_DIR):
        os.makedirs(_STORE_DIR, exist_ok=True)
    if not os.path.exists(_STORE_FILE):
        with open(_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"workspaces": {}, "webhooks": {}}, f, ensure_ascii=False, indent=2)


def _read_store() -> Dict[str, Any]:
    _ensure_store_file()
    with open(_STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_store(content: Dict[str, Any]) -> None:
    _ensure_store_file()
    with open(_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)


def upsert_workspace(
    *,
    workspace_id: str,
    access_token: str,
    bot_id: Optional[str] = None,
    webhook_id: Optional[str] = None,
    webhook_secret: Optional[str] = None,
    webhook_url: Optional[str] = None,
    incoming_secret: Optional[str] = None,
) -> None:
    """워크스페이스 매핑 정보를 병합 저장합니다."""
    with _LOCK:
        store = _read_store()
        workspaces = store.setdefault("workspaces", {})
        existing = workspaces.get(workspace_id, {})
        existing.update(
            {
                "access_token": access_token,
                "bot_id": bot_id or existing.get("bot_id"),
                "webhook_id": webhook_id or existing.get("webhook_id"),
                "webhook_secret": webhook_secret or existing.get("webhook_secret"),
                "webhook_url": webhook_url or existing.get("webhook_url"),
                "incoming_secret": incoming_secret or existing.get("incoming_secret"),
            }
        )
        workspaces[workspace_id] = existing

        # webhooks 역색인도 업데이트
        if webhook_id and (webhook_secret or existing.get("webhook_secret")):
            webhooks = store.setdefault("webhooks", {})
            webhooks[webhook_id] = {
                "workspace_id": workspace_id,
                "secret": webhook_secret or existing.get("webhook_secret"),
            }

        _write_store(store)


def get_workspace(workspace_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        store = _read_store()
        return store.get("workspaces", {}).get(workspace_id)


def list_webhook_secrets() -> List[Tuple[str, str]]:
    """(webhook_id, secret) 목록을 반환합니다."""
    with _LOCK:
        store = _read_store()
        webhooks = store.get("webhooks", {})
        return [(wid, info.get("secret", "")) for wid, info in webhooks.items() if info.get("secret")]


def get_secret_by_webhook_id(webhook_id: str) -> Optional[str]:
    with _LOCK:
        store = _read_store()
        info = store.get("webhooks", {}).get(webhook_id)
        if info:
            return info.get("secret")
        return None


def get_access_token_by_workspace(workspace_id: str) -> Optional[str]:
    ws = get_workspace(workspace_id)
    return ws.get("access_token") if ws else None


def get_workspace_id_by_webhook_id(webhook_id: str) -> Optional[str]:
    with _LOCK:
        store = _read_store()
        info = store.get("webhooks", {}).get(webhook_id)
        if info:
            return info.get("workspace_id")
        return None


def set_incoming_secret(*, workspace_id: str, secret: str) -> None:
    with _LOCK:
        store = _read_store()
        workspaces = store.setdefault("workspaces", {})
        existing = workspaces.get(workspace_id, {})
        existing["incoming_secret"] = secret
        workspaces[workspace_id] = existing
        _write_store(store)


def get_workspace_id_by_incoming_secret(secret: str) -> Optional[str]:
    with _LOCK:
        store = _read_store()
        for ws_id, info in store.get("workspaces", {}).items():
            if info.get("incoming_secret") == secret:
                return ws_id
        return None


def set_webhook_info(
    *, workspace_id: str, webhook_id: str, webhook_secret: str, webhook_url: Optional[str] = None
) -> None:
    with _LOCK:
        store = _read_store()
        workspaces = store.setdefault("workspaces", {})
        existing = workspaces.get(workspace_id, {})
        existing.update(
            {
                "webhook_id": webhook_id,
                "webhook_secret": webhook_secret,
            }
        )
        if webhook_url:
            existing["webhook_url"] = webhook_url
        workspaces[workspace_id] = existing

        webhooks = store.setdefault("webhooks", {})
        webhooks[webhook_id] = {
            "workspace_id": workspace_id,
            "secret": webhook_secret,
        }

        _write_store(store)


