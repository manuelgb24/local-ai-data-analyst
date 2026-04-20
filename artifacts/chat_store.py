"""Filesystem-backed local chat persistence."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from application import ChatDetail, ChatMessage, ChatNotFoundError, ChatSummary
from runtime.serialization import deserialize_agent_result, deserialize_run_error, to_jsonable


CHAT_METADATA_FILENAME = "chat.json"


class FilesystemChatStore:
    """Persist product-level chats next to run metadata."""

    def __init__(self, artifacts_root: str | Path = "artifacts/runs", chat_root: str | Path | None = None) -> None:
        artifacts_path = Path(artifacts_root)
        self._chat_root = Path(chat_root) if chat_root is not None else artifacts_path.parent / "chats"

    def create_chat(self, *, agent_id: str, dataset_path: str, title: str, created_at: str) -> ChatDetail:
        chat_id = f"chat-{uuid4().hex}"
        chat = ChatDetail(
            chat_id=chat_id,
            agent_id=agent_id,
            dataset_path=dataset_path,
            title=title,
            created_at=created_at,
            updated_at=created_at,
            messages=[],
            run_ids=[],
            latest_run_id=None,
        )
        self.save(chat)
        return chat

    def save(self, chat: ChatDetail) -> None:
        if not isinstance(chat, ChatDetail):
            raise TypeError("chat must be a ChatDetail instance")
        metadata_path = self._metadata_path(chat.chat_id)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(to_jsonable(chat), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_chats(self) -> list[ChatSummary]:
        chats = [self._read_chat(path) for path in self._iter_metadata_paths()]
        chats.sort(key=lambda item: (item.updated_at, item.created_at, item.chat_id), reverse=True)
        return [self._to_summary(chat) for chat in chats]

    def get_chat(self, chat_id: str) -> ChatDetail:
        metadata_path = self._metadata_path(chat_id)
        if not metadata_path.exists():
            raise ChatNotFoundError(chat_id)
        return self._read_chat(metadata_path)

    def append_message(self, chat_id: str, message: ChatMessage, *, updated_at: str) -> ChatDetail:
        chat = self.get_chat(chat_id)
        chat.messages.append(message)
        chat.updated_at = updated_at
        if message.run_id is not None and message.run_id not in chat.run_ids:
            chat.run_ids.append(message.run_id)
            chat.latest_run_id = message.run_id
        self.save(chat)
        return chat

    def _iter_metadata_paths(self) -> list[Path]:
        if not self._chat_root.exists():
            return []
        return sorted(path for path in self._chat_root.glob(f"*/{CHAT_METADATA_FILENAME}") if path.is_file())

    def _metadata_path(self, chat_id: str) -> Path:
        normalized_chat_id = str(chat_id).strip()
        if not normalized_chat_id:
            raise ValueError("chat_id must be a non-empty string")
        return self._chat_root / normalized_chat_id / CHAT_METADATA_FILENAME

    def _read_chat(self, metadata_path: Path) -> ChatDetail:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ChatNotFoundError(metadata_path.parent.name) from exc

        return ChatDetail(
            chat_id=str(payload["chat_id"]),
            agent_id=str(payload["agent_id"]),
            dataset_path=str(payload["dataset_path"]),
            title=str(payload["title"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            messages=[self._deserialize_message(item) for item in payload.get("messages", [])],
            run_ids=[str(item) for item in payload.get("run_ids", [])],
            latest_run_id=None if payload.get("latest_run_id") is None else str(payload["latest_run_id"]),
        )

    def _deserialize_message(self, payload: dict[str, object]) -> ChatMessage:
        result_payload = payload.get("result")
        error_payload = payload.get("error")
        return ChatMessage(
            message_id=str(payload["message_id"]),
            role=str(payload["role"]),
            content=str(payload["content"]),
            created_at=str(payload["created_at"]),
            run_id=None if payload.get("run_id") is None else str(payload["run_id"]),
            status=None if payload.get("status") is None else str(payload["status"]),
            result=None if not isinstance(result_payload, dict) else deserialize_agent_result(result_payload),
            error=None if not isinstance(error_payload, dict) else deserialize_run_error(error_payload),
        )

    def _to_summary(self, chat: ChatDetail) -> ChatSummary:
        return ChatSummary(
            chat_id=chat.chat_id,
            agent_id=chat.agent_id,
            dataset_path=chat.dataset_path,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            latest_run_id=chat.latest_run_id,
            message_count=len(chat.messages),
        )
