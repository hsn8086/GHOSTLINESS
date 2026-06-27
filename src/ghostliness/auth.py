from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from enum import StrEnum


class AuthMode(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class GameProfile:
    uuid: uuid.UUID
    username: str
    properties: tuple[dict[str, str], ...] = ()
    online: bool = False


class Authenticator:
    def __init__(self, mode: str) -> None:
        self.mode = AuthMode(mode)

    async def authenticate_offline(
        self,
        username: str,
        client_uuid: uuid.UUID | None = None,
    ) -> GameProfile:
        profile_uuid = client_uuid or offline_uuid(username)
        return GameProfile(uuid=profile_uuid, username=username, online=False)

    async def authenticate_online(self, username: str) -> GameProfile:
        raise NotImplementedError(
            "online authentication requires the encryption/session-server flow, "
            "which is intentionally isolated behind this backend"
        )

    async def authenticate(
        self,
        username: str,
        client_uuid: uuid.UUID | None = None,
    ) -> GameProfile:
        if self.mode == AuthMode.OFFLINE:
            return await self.authenticate_offline(username, client_uuid)
        if self.mode == AuthMode.ONLINE:
            return await self.authenticate_online(username)
        try:
            return await self.authenticate_online(username)
        except NotImplementedError:
            return await self.authenticate_offline(username, client_uuid)


def offline_uuid(username: str) -> uuid.UUID:
    digest = hashlib.md5(f"OfflinePlayer:{username}".encode(), usedforsecurity=False)
    data = bytearray(digest.digest())
    data[6] = (data[6] & 0x0F) | 0x30
    data[8] = (data[8] & 0x3F) | 0x80
    return uuid.UUID(bytes=bytes(data))
