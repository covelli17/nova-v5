import pytest, respx
from httpx import Response
from runtime.tools.felirni_api import FelirniAPI

BASE = "https://api.felirni.test"

@pytest.fixture
def api():
    return FelirniAPI(base_url=BASE, token="test-tok")

@respx.mock
@pytest.mark.anyio
async def test_health(api):
    respx.get(f"{BASE}/").mock(return_value=Response(200, json={"status":"ok"}))
    assert (await api.health())["status"] == "ok"

@respx.mock
@pytest.mark.anyio
async def test_list_tickets(api):
    respx.get(f"{BASE}/tickets").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.list_tickets()

@respx.mock
@pytest.mark.anyio
async def test_create_ticket(api):
    respx.post(f"{BASE}/tickets").mock(return_value=Response(201, json={"id":"FL-020"}))
    assert (await api.create_ticket({"title":"x"}))["id"] == "FL-020"

@respx.mock
@pytest.mark.anyio
async def test_get_ticket(api):
    respx.get(f"{BASE}/tickets/FL-001").mock(return_value=Response(200, json={"id":"FL-001"}))
    assert (await api.get_ticket("FL-001"))["id"] == "FL-001"

@respx.mock
@pytest.mark.anyio
async def test_update_ticket(api):
    respx.put(f"{BASE}/tickets/FL-001").mock(return_value=Response(200, json={"updated":True}))
    assert (await api.update_ticket("FL-001", {"status":"Completado"}))["updated"] is True

@respx.mock
@pytest.mark.anyio
async def test_delete_ticket(api):
    respx.delete(f"{BASE}/tickets/FL-001").mock(return_value=Response(200, json={"deleted":True}))
    assert (await api.delete_ticket("FL-001"))["deleted"] is True

@respx.mock
@pytest.mark.anyio
async def test_add_comment(api):
    respx.post(f"{BASE}/tickets/FL-001/comments").mock(return_value=Response(201, json={"commentId":"c1"}))
    assert "commentId" in await api.add_comment("FL-001", {"text":"ok"})

@respx.mock
@pytest.mark.anyio
async def test_blocked(api):
    respx.get(f"{BASE}/tickets/blocked").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_blocked_tickets()

@respx.mock
@pytest.mark.anyio
async def test_overdue(api):
    respx.get(f"{BASE}/tickets/overdue").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_overdue_tickets()

@respx.mock
@pytest.mark.anyio
async def test_stale(api):
    respx.get(f"{BASE}/tickets/stale").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_stale_tickets()

@respx.mock
@pytest.mark.anyio
async def test_list_epics(api):
    respx.get(f"{BASE}/epics").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.list_epics()

@respx.mock
@pytest.mark.anyio
async def test_create_epic(api):
    respx.post(f"{BASE}/epics").mock(return_value=Response(201, json={"id":"EPIC-001"}))
    assert (await api.create_epic({"title":"INVIMA Q2"}))["id"] == "EPIC-001"

@respx.mock
@pytest.mark.anyio
async def test_epic_tasks(api):
    respx.get(f"{BASE}/epics/EPIC-001/tasks").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_epic_tasks("EPIC-001")

@respx.mock
@pytest.mark.anyio
async def test_epic_progress(api):
    respx.get(f"{BASE}/epics/EPIC-001/progress").mock(return_value=Response(200, json={"pct":42}))
    assert (await api.get_epic_progress("EPIC-001"))["pct"] == 42

@respx.mock
@pytest.mark.anyio
async def test_at_risk_epics(api):
    respx.get(f"{BASE}/epics/at-risk").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_at_risk_epics()

@respx.mock
@pytest.mark.anyio
async def test_list_sprints(api):
    respx.get(f"{BASE}/sprints").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.list_sprints()

@respx.mock
@pytest.mark.anyio
async def test_active_sprint(api):
    respx.get(f"{BASE}/sprints/active").mock(return_value=Response(200, json={"id":"SPRINT-003"}))
    assert (await api.get_active_sprint())["id"] == "SPRINT-003"

@respx.mock
@pytest.mark.anyio
async def test_sprint_metrics(api):
    respx.get(f"{BASE}/sprints/SPRINT-003/metrics").mock(return_value=Response(200, json={"tcc":0.85}))
    assert (await api.get_sprint_metrics("SPRINT-003"))["tcc"] == 0.85

@respx.mock
@pytest.mark.anyio
async def test_close_sprint(api):
    respx.post(f"{BASE}/sprints/SPRINT-003/close").mock(return_value=Response(200, json={"closed":True}))
    assert (await api.close_sprint("SPRINT-003"))["closed"] is True

@respx.mock
@pytest.mark.anyio
async def test_list_people(api):
    respx.get(f"{BASE}/people").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.list_people()

@respx.mock
@pytest.mark.anyio
async def test_person_tasks(api):
    respx.get(f"{BASE}/people/PERSON-001/tasks").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.get_person_tasks("PERSON-001")

@respx.mock
@pytest.mark.anyio
async def test_person_tcc(api):
    respx.get(f"{BASE}/people/PERSON-001/tcc").mock(return_value=Response(200, json={"tcc":0.9}))
    assert (await api.get_person_tcc("PERSON-001"))["tcc"] == 0.9

@respx.mock
@pytest.mark.anyio
async def test_team_metrics(api):
    respx.get(f"{BASE}/metrics/team").mock(return_value=Response(200, json={"team_tcc":0.88}))
    assert "team_tcc" in await api.get_team_metrics()

@respx.mock
@pytest.mark.anyio
async def test_list_decisions(api):
    respx.get(f"{BASE}/decisions").mock(return_value=Response(200, json={"items":[]}))
    assert "items" in await api.list_decisions()

@respx.mock
@pytest.mark.anyio
async def test_create_decision(api):
    respx.post(f"{BASE}/decisions").mock(return_value=Response(201, json={"id":"DEC-001"}))
    assert (await api.create_decision({"title":"Migrar"}))["id"] == "DEC-001"

@respx.mock
@pytest.mark.anyio
async def test_update_decision(api):
    respx.put(f"{BASE}/decisions/DEC-001").mock(return_value=Response(200, json={"updated":True}))
    assert (await api.update_decision("DEC-001", {"status":"Tomada"}))["updated"] is True

@respx.mock
@pytest.mark.anyio
async def test_http_500_raises(api):
    respx.get(f"{BASE}/tickets").mock(return_value=Response(500, json={"error":"internal"}))
    with pytest.raises(Exception): await api.list_tickets()

@respx.mock
@pytest.mark.anyio
async def test_404_raises(api):
    respx.get(f"{BASE}/tickets/FL-999").mock(return_value=Response(404))
    with pytest.raises(Exception): await api.get_ticket("FL-999")

@respx.mock
@pytest.mark.anyio
async def test_context_manager(api):
    respx.get(f"{BASE}/").mock(return_value=Response(200, json={"status":"ok"}))
    async with api: r = await api.health()
    assert r["status"] == "ok"
