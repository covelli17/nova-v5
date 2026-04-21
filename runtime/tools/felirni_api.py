from __future__ import annotations
import ipaddress
import re
from urllib.parse import urlparse

import httpx

from runtime.tools.secrets_manager import get_felirni_config

# M-1: IDs solo alfanuméricos + guiones/underscore/#
_ID_RE = re.compile(r"^[A-Za-z0-9\-_#]+$")

# A-1: Redes bloqueadas — link-local completo + RFC1918 + loopback
_BLOCKED_NETS = [
    ipaddress.ip_network("169.254.0.0/16"),  # link-local: EC2 + ECS task metadata
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
]


class FelirniAPIError(RuntimeError):
    """Error opaco — sin objetos httpx, sin tokens."""
    def __init__(self, status_code: int, path: str) -> None:
        self.status_code = status_code
        self.path = path
        super().__init__(f"Felirni API error: {status_code} en {path}")


def _validate_url(url: str) -> str:
    """A-1: HTTPS + bloqueo de IPs internas literales en el URL.
    
    Cubre ataques directos por IP (169.254.170.2, 10.x, 127.x).
    DNS rebinding se mitiga por Security Group en ECS (defense-in-depth).
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("API_URL debe usar HTTPS")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("API_URL sin hostname válido")
    # Si el hostname ES una IP literal, validarla contra blocklist
    try:
        ip = ipaddress.ip_address(hostname)
        for net in _BLOCKED_NETS:
            if ip in net:
                raise ValueError("API_URL apunta a dirección interna bloqueada")
    except ValueError as e:
        # Si el mensaje es el nuestro, re-raise
        if "bloqueada" in str(e):
            raise
        # Si no parsea como IP es un hostname — permitir (validación de red en ECS SG)
    return url.rstrip("/")


def _validate_id(value: str, name: str = "id") -> str:
    """M-1: path params solo chars seguros."""
    if not _ID_RE.match(value):
        raise ValueError(f"Caracter inválido en {name}")
    return value


def _load_credentials() -> tuple[str, str]:
    secrets = get_felirni_config()
    return _validate_url(secrets["api_url"]), secrets["api_key"]


class FelirniAPI:
    def __init__(self, *, base_url: str | None = None, token: str | None = None) -> None:
        if base_url and token:
            self._base = _validate_url(base_url)
            self._token = token
        else:
            self._base, self._token = _load_credentials()
        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
            timeout=15.0,
        )

    async def _get(self, path, **params):
        r = await self._client.get(path, params={k: v for k, v in params.items() if v is not None})
        self._raise(r); return r.json()

    async def _post(self, path, body):
        r = await self._client.post(path, json=body); self._raise(r); return r.json()

    async def _put(self, path, body):
        r = await self._client.put(path, json=body); self._raise(r); return r.json()

    async def _delete(self, path):
        r = await self._client.delete(path); self._raise(r); return r.json()

    @staticmethod
    def _raise(r: httpx.Response) -> None:
        """M-2: error opaco sin objetos request/response ni token."""
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise FelirniAPIError(e.response.status_code, e.response.url.path) from None

    async def close(self): await self._client.aclose()
    async def __aenter__(self): return self
    async def __aexit__(self, *_): await self.close()

    # HEALTH
    async def health(self): return await self._get("/")

    # TICKETS
    async def list_tickets(self, *, status=None, epic_id=None, sprint_id=None, assignee_id=None):
        return await self._get("/tickets", status=status, epicId=epic_id, sprintId=sprint_id, assigneeId=assignee_id)
    async def create_ticket(self, body): return await self._post("/tickets", body)
    async def get_ticket(self, tid): return await self._get(f"/tickets/{_validate_id(tid, 'ticket_id')}")
    async def update_ticket(self, tid, body): return await self._put(f"/tickets/{_validate_id(tid, 'ticket_id')}", body)
    async def delete_ticket(self, tid): return await self._delete(f"/tickets/{_validate_id(tid, 'ticket_id')}")
    async def add_comment(self, tid, body): return await self._post(f"/tickets/{_validate_id(tid, 'ticket_id')}/comments", body)
    async def get_blocked_tickets(self): return await self._get("/tickets/blocked")
    async def get_overdue_tickets(self): return await self._get("/tickets/overdue")
    async def get_stale_tickets(self): return await self._get("/tickets/stale")

    # EPICS
    async def list_epics(self): return await self._get("/epics")
    async def create_epic(self, body): return await self._post("/epics", body)
    async def update_epic(self, eid, body): return await self._put(f"/epics/{_validate_id(eid, 'epic_id')}", body)
    async def delete_epic(self, eid): return await self._delete(f"/epics/{_validate_id(eid, 'epic_id')}")
    async def get_epic_tasks(self, eid): return await self._get(f"/epics/{_validate_id(eid, 'epic_id')}/tasks")
    async def get_epic_progress(self, eid): return await self._get(f"/epics/{_validate_id(eid, 'epic_id')}/progress")
    async def get_at_risk_epics(self): return await self._get("/epics/at-risk")

    # SPRINTS
    async def list_sprints(self): return await self._get("/sprints")
    async def create_sprint(self, body): return await self._post("/sprints", body)
    async def update_sprint(self, sid, body): return await self._put(f"/sprints/{_validate_id(sid, 'sprint_id')}", body)
    async def delete_sprint(self, sid): return await self._delete(f"/sprints/{_validate_id(sid, 'sprint_id')}")
    async def get_active_sprint(self): return await self._get("/sprints/active")
    async def get_sprint_metrics(self, sid): return await self._get(f"/sprints/{_validate_id(sid, 'sprint_id')}/metrics")
    async def close_sprint(self, sid, body=None): return await self._post(f"/sprints/{_validate_id(sid, 'sprint_id')}/close", body or {})

    # PEOPLE
    async def list_people(self): return await self._get("/people")
    async def create_person(self, body): return await self._post("/people", body)
    async def update_person(self, pid, body): return await self._put(f"/people/{_validate_id(pid, 'person_id')}", body)
    async def get_person_tasks(self, pid): return await self._get(f"/people/{_validate_id(pid, 'person_id')}/tasks")
    async def get_person_tcc(self, pid): return await self._get(f"/people/{_validate_id(pid, 'person_id')}/tcc")

    # METRICS
    async def get_team_metrics(self): return await self._get("/metrics/team")

    # DECISIONS
    async def list_decisions(self): return await self._get("/decisions")
    async def create_decision(self, body): return await self._post("/decisions", body)
    async def update_decision(self, did, body): return await self._put(f"/decisions/{_validate_id(did, 'decision_id')}", body)
