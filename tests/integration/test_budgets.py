from httpx import AsyncClient

_BUDGET = {
    "name": "June 2026",
    "period_type": "MONTHLY",
    "period_start": "2026-06-01",
    "period_end": "2026-06-30",
}

_INCOME_SOURCE = {
    "name": "Salary",
    "type": "WAGES",
    "amount": "5000.00",
    "frequency": "MONTHLY",
    "reference_date": "2026-01-01",
}


# --- helpers ---

async def _create_budget(client, auth_headers):
    return (await client.post("/budgets", headers=auth_headers, json=_BUDGET)).json()["id"]


async def _create_income_source(client, auth_headers):
    return (await client.post("/income-sources", headers=auth_headers, json=_INCOME_SOURCE)).json()["id"]


async def _first_item_id(client, auth_headers, category_name="Home"):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    cat = next(c for c in cats if c["name"] == category_name)
    return cat["items"][0]["id"]


# --- budget CRUD ---

async def test_create_budget(client: AsyncClient, auth_headers: dict):
    res = await client.post("/budgets", headers=auth_headers, json=_BUDGET)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "June 2026"
    assert data["period_type"] == "MONTHLY"
    assert "id" in data


async def test_create_budget_end_before_start_is_rejected(client: AsyncClient, auth_headers: dict):
    res = await client.post("/budgets", headers=auth_headers, json={
        **_BUDGET, "period_start": "2026-06-30", "period_end": "2026-06-01",
    })
    assert res.status_code == 422


async def test_list_budgets(client: AsyncClient, auth_headers: dict):
    await _create_budget(client, auth_headers)
    res = await client.get("/budgets", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_list_budgets_empty(client: AsyncClient, auth_headers: dict):
    res = await client.get("/budgets", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


async def test_get_budget(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    res = await client.get(f"/budgets/{budget_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == budget_id


async def test_get_nonexistent_budget(client: AsyncClient, auth_headers: dict):
    res = await client.get("/budgets/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert res.status_code == 404


async def test_update_budget_name(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    res = await client.put(f"/budgets/{budget_id}", headers=auth_headers, json={"name": "Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Updated"


async def test_delete_budget(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    assert (await client.delete(f"/budgets/{budget_id}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/budgets/{budget_id}", headers=auth_headers)).status_code == 404


# --- income entries ---

async def test_upsert_income_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = await _create_income_source(client, auth_headers)

    res = await client.put(
        f"/budgets/{budget_id}/income/{source_id}",
        headers=auth_headers,
        json={"amount": "5000.00"},
    )
    assert res.status_code == 200


async def test_list_income_entries(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = await _create_income_source(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "5000.00"})

    entries = (await client.get(f"/budgets/{budget_id}/income", headers=auth_headers)).json()
    assert len(entries) == 1
    assert entries[0]["name"] == "Salary"
    assert float(entries[0]["amount"]) == 5000.0


async def test_update_income_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = await _create_income_source(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "5000.00"})
    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "6000.00"})

    entries = (await client.get(f"/budgets/{budget_id}/income", headers=auth_headers)).json()
    assert len(entries) == 1
    assert float(entries[0]["amount"]) == 6000.0


async def test_delete_income_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = await _create_income_source(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "5000.00"})

    assert (await client.delete(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/budgets/{budget_id}/income", headers=auth_headers)).json() == []


async def test_income_entry_rejects_unknown_source(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    res = await client.put(
        f"/budgets/{budget_id}/income/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
        json={"amount": "100.00"},
    )
    assert res.status_code == 404


# --- expense entries ---

async def test_upsert_expense_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    item_id = await _first_item_id(client, auth_headers)

    res = await client.put(
        f"/budgets/{budget_id}/expenses/{item_id}",
        headers=auth_headers,
        json={"amount": "1200.00", "is_fixed": True},
    )
    assert res.status_code == 200


async def test_list_expense_entries(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    item_id = await _first_item_id(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers, json={"amount": "1500.00"})

    entries = (await client.get(f"/budgets/{budget_id}/expenses", headers=auth_headers)).json()
    assert len(entries) == 1
    assert float(entries[0]["amount"]) == 1500.0
    assert entries[0]["category"] == "Home"


async def test_update_expense_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    item_id = await _first_item_id(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers, json={"amount": "1000.00"})
    await client.put(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers, json={"amount": "1200.00"})

    entries = (await client.get(f"/budgets/{budget_id}/expenses", headers=auth_headers)).json()
    assert len(entries) == 1
    assert float(entries[0]["amount"]) == 1200.0


async def test_delete_expense_entry(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    item_id = await _first_item_id(client, auth_headers)
    await client.put(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers, json={"amount": "1000.00"})

    assert (await client.delete(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"/budgets/{budget_id}/expenses", headers=auth_headers)).json() == []


# --- report ---

async def test_budget_report_calculations(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = await _create_income_source(client, auth_headers)
    item_id = await _first_item_id(client, auth_headers)

    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "5000.00"})
    await client.put(f"/budgets/{budget_id}/expenses/{item_id}", headers=auth_headers, json={"amount": "1500.00"})

    res = await client.get(f"/budgets/{budget_id}/report", headers=auth_headers)
    assert res.status_code == 200
    report = res.json()

    assert report["budget_name"] == "June 2026"
    assert float(report["total_income"]) == 5000.0   # monthly source → no conversion needed
    assert float(report["total_expenses"]) == 1500.0
    assert float(report["net"]) == 3500.0
    assert len(report["income_entries"]) == 1
    assert len(report["categories"]) == 1
    assert report["categories"][0]["category_name"] == "Home"


async def test_budget_report_empty_budget(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    report = (await client.get(f"/budgets/{budget_id}/report", headers=auth_headers)).json()

    assert float(report["total_income"]) == 0.0
    assert float(report["total_expenses"]) == 0.0
    assert float(report["net"]) == 0.0
    assert report["income_entries"] == []
    assert report["categories"] == []


async def test_budget_report_weekly_income_normalized(client: AsyncClient, auth_headers: dict):
    budget_id = await _create_budget(client, auth_headers)
    source_id = (await client.post("/income-sources", headers=auth_headers, json={
        "name": "Weekly Pay",
        "type": "WAGES",
        "amount": "1200.00",
        "frequency": "WEEKLY",
        "reference_date": "2026-01-01",
    })).json()["id"]

    await client.put(f"/budgets/{budget_id}/income/{source_id}", headers=auth_headers, json={"amount": "1200.00"})

    report = (await client.get(f"/budgets/{budget_id}/report", headers=auth_headers)).json()
    # 1200 * 52 / 12 = 5200
    assert float(report["total_income"]) == 5200.0
    assert float(report["income_entries"][0]["monthly_equivalent"]) == 5200.0
