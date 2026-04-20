"""Application use cases for local analytical chats."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from .api_contracts import ChatDetail, ChatMessage, ChatSummary, RunDetail, RunSummary
from .contracts import RunError, RunRequest
from .run_analysis import RunAnalysisUseCase
from .run_history import GetRunUseCase


def _utcnow_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_chat_message_id() -> str:
    return f"msg-{uuid4().hex}"


def _title_from_prompt(prompt: str, dataset_path: str) -> str:
    title = " ".join(prompt.strip().split())
    if title:
        return title[:80]
    return dataset_path.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1]


class ChatStore(Protocol):
    def create_chat(self, *, agent_id: str, dataset_path: str, title: str, created_at: str) -> ChatDetail: ...

    def save(self, chat: ChatDetail) -> None: ...

    def list_chats(self) -> list[ChatSummary]: ...

    def get_chat(self, chat_id: str) -> ChatDetail: ...

    def append_message(self, chat_id: str, message: ChatMessage, *, updated_at: str) -> ChatDetail: ...


class RunHistoryReader(Protocol):
    def list_runs(self) -> list[RunSummary]: ...

    def get_run(self, run_id: str) -> RunDetail: ...


class ListChatsUseCase:
    def __init__(self, store: ChatStore) -> None:
        self._store = store

    def execute(self) -> list[ChatSummary]:
        return self._store.list_chats()


class GetChatUseCase:
    def __init__(self, store: ChatStore) -> None:
        self._store = store

    def execute(self, chat_id: str) -> ChatDetail:
        return self._store.get_chat(chat_id)


class CreateChatUseCase:
    def __init__(self, store: ChatStore, send_message_use_case: "SendChatMessageUseCase") -> None:
        self._store = store
        self._send_message_use_case = send_message_use_case

    def execute(self, *, agent_id: str, dataset_path: str, user_prompt: str) -> ChatDetail:
        timestamp = _utcnow_timestamp()
        chat = self._store.create_chat(
            agent_id=agent_id,
            dataset_path=dataset_path,
            title=_title_from_prompt(user_prompt, dataset_path),
            created_at=timestamp,
        )
        return self._send_message_use_case.execute(chat.chat_id, user_prompt)


class SendChatMessageUseCase:
    def __init__(
        self,
        *,
        store: ChatStore,
        run_use_case: RunAnalysisUseCase,
        get_run_use_case: GetRunUseCase,
        run_history_reader: RunHistoryReader,
    ) -> None:
        self._store = store
        self._run_use_case = run_use_case
        self._get_run_use_case = get_run_use_case
        self._run_history_reader = run_history_reader

    def execute(self, chat_id: str, user_prompt: str) -> ChatDetail:
        chat = self._store.get_chat(chat_id)
        context = self._build_conversation_context(chat.messages)
        timestamp = _utcnow_timestamp()
        self._store.append_message(
            chat.chat_id,
            ChatMessage(
                message_id=_new_chat_message_id(),
                role="user",
                content=user_prompt,
                created_at=timestamp,
            ),
            updated_at=timestamp,
        )

        request = RunRequest(
            agent_id=chat.agent_id,
            dataset_path=chat.dataset_path,
            user_prompt=user_prompt,
            session_id=chat.chat_id,
            conversation_context=context,
        )

        try:
            result = self._run_use_case.execute(request)
            detail = self._get_run_use_case.execute(result.artifact_manifest.run_id)
        except RunError as exc:
            failed_detail = self._latest_run_for_chat(chat.chat_id)
            failure_timestamp = failed_detail.updated_at if failed_detail is not None else _utcnow_timestamp()
            self._store.append_message(
                chat.chat_id,
                ChatMessage(
                    message_id=_new_chat_message_id(),
                    role="assistant",
                    content=exc.message,
                    created_at=failure_timestamp,
                    run_id=None if failed_detail is None else failed_detail.run_id,
                    status="failed",
                    error=failed_detail.error if failed_detail is not None and failed_detail.error is not None else exc,
                ),
                updated_at=failure_timestamp,
            )
            raise

        assistant_timestamp = detail.updated_at
        return self._store.append_message(
            chat.chat_id,
            ChatMessage(
                message_id=_new_chat_message_id(),
                role="assistant",
                content=detail.result.narrative if detail.result is not None else result.narrative,
                created_at=assistant_timestamp,
                run_id=detail.run_id,
                status="succeeded",
                result=detail.result,
            ),
            updated_at=assistant_timestamp,
        )

    def _latest_run_for_chat(self, chat_id: str) -> RunDetail | None:
        for summary in self._run_history_reader.list_runs():
            if summary.session_id == chat_id:
                return self._run_history_reader.get_run(summary.run_id)
        return None

    def _build_conversation_context(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        context: list[dict[str, str]] = []
        for message in messages:
            if message.role == "assistant" and message.status == "failed":
                continue
            context.append({"role": message.role, "content": message.content})
        return context[-6:]
