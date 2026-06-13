from httpx import AsyncClient


async def test_list_categories_requires_auth(client: AsyncClient):
    res = await client.get("/categories")
    assert res.status_code == 401


async def test_list_categories_returns_defaults(client: AsyncClient, auth_headers: dict):
    res = await client.get("/categories", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 9
    names = [c["name"] for c in data]
    assert "Home" in names
    assert "Financial Obligations" in names
    home = next(c for c in data if c["name"] == "Home")
    assert len(home["items"]) == 9


async def test_create_custom_category(client: AsyncClient, auth_headers: dict):
    res = await client.post("/categories", headers=auth_headers, json={
        "name": "My Savings",
        "display_order": 99,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "My Savings"
    assert data["is_default"] is False
    assert "id" in data


async def test_custom_category_appears_in_list(client: AsyncClient, auth_headers: dict):
    await client.post("/categories", headers=auth_headers, json={"name": "Custom", "display_order": 99})
    cats = (await client.get("/categories", headers=auth_headers)).json()
    assert any(c["name"] == "Custom" for c in cats)


async def test_update_custom_category(client: AsyncClient, auth_headers: dict):
    cat_id = (await client.post("/categories", headers=auth_headers, json={
        "name": "Before", "display_order": 99,
    })).json()["id"]

    res = await client.put(f"/categories/{cat_id}", headers=auth_headers, json={"name": "After"})
    assert res.status_code == 200
    assert res.json()["name"] == "After"


async def test_update_system_category_not_allowed(client: AsyncClient, auth_headers: dict):
    system_id = (await client.get("/categories", headers=auth_headers)).json()[0]["id"]
    res = await client.put(f"/categories/{system_id}", headers=auth_headers, json={"name": "Renamed"})
    assert res.status_code == 404


async def test_delete_custom_category(client: AsyncClient, auth_headers: dict):
    cat_id = (await client.post("/categories", headers=auth_headers, json={
        "name": "ToDelete", "display_order": 99,
    })).json()["id"]

    assert (await client.delete(f"/categories/{cat_id}", headers=auth_headers)).status_code == 204

    cats = (await client.get("/categories", headers=auth_headers)).json()
    assert not any(c["id"] == cat_id for c in cats)


async def test_delete_system_category_not_allowed(client: AsyncClient, auth_headers: dict):
    system_id = (await client.get("/categories", headers=auth_headers)).json()[0]["id"]
    res = await client.delete(f"/categories/{system_id}", headers=auth_headers)
    assert res.status_code == 404


async def test_list_category_items(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home = next(c for c in cats if c["name"] == "Home")

    res = await client.get(f"/categories/{home['id']}/items", headers=auth_headers)
    assert res.status_code == 200
    names = [i["name"] for i in res.json()]
    assert "Mortgage/Rent" in names


async def test_create_custom_item_in_system_category(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home_id = next(c for c in cats if c["name"] == "Home")["id"]

    res = await client.post(f"/categories/{home_id}/items", headers=auth_headers, json={
        "name": "HOA Fees", "display_order": 99,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "HOA Fees"
    assert data["is_default"] is False


async def test_update_system_item_copy_on_write(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home = next(c for c in cats if c["name"] == "Home")
    item_id = home["items"][0]["id"]  # Mortgage/Rent

    res = await client.put(f"/items/{item_id}", headers=auth_headers, json={"custom_name": "My Rent"})
    assert res.status_code == 200
    assert res.json()["name"] == "My Rent"

    updated_cats = (await client.get("/categories", headers=auth_headers)).json()
    home_items = next(c for c in updated_cats if c["name"] == "Home")["items"]
    assert any(i["name"] == "My Rent" for i in home_items)
    assert not any(i["name"] == "Mortgage/Rent" for i in home_items)


async def test_update_custom_item_direct_mutation(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home_id = cats[0]["id"]
    item_id = (await client.post(f"/categories/{home_id}/items", headers=auth_headers, json={
        "name": "Original", "display_order": 99,
    })).json()["id"]

    res = await client.put(f"/items/{item_id}", headers=auth_headers, json={"custom_name": "Renamed"})
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed"
    assert res.json()["is_default"] is False


async def test_delete_system_item_hides_it(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home = next(c for c in cats if c["name"] == "Home")
    item_id = home["items"][0]["id"]  # Mortgage/Rent

    assert (await client.delete(f"/items/{item_id}", headers=auth_headers)).status_code == 204

    updated_cats = (await client.get("/categories", headers=auth_headers)).json()
    home_items = next(c for c in updated_cats if c["name"] == "Home")["items"]
    assert not any(i["id"] == item_id for i in home_items)


async def test_delete_custom_item(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home_id = cats[0]["id"]
    item_id = (await client.post(f"/categories/{home_id}/items", headers=auth_headers, json={
        "name": "Temp", "display_order": 99,
    })).json()["id"]

    assert (await client.delete(f"/items/{item_id}", headers=auth_headers)).status_code == 204


async def test_reset_defaults_clears_overrides(client: AsyncClient, auth_headers: dict):
    cats = (await client.get("/categories", headers=auth_headers)).json()
    home = next(c for c in cats if c["name"] == "Home")
    item_id = home["items"][0]["id"]
    await client.put(f"/items/{item_id}", headers=auth_headers, json={"custom_name": "Overridden"})

    assert (await client.post("/items/reset-defaults", headers=auth_headers)).status_code == 204

    updated_cats = (await client.get("/categories", headers=auth_headers)).json()
    home_items = next(c for c in updated_cats if c["name"] == "Home")["items"]
    assert any(i["name"] == "Mortgage/Rent" for i in home_items)


async def test_reset_defaults_removes_custom_categories(client: AsyncClient, auth_headers: dict):
    cat_id = (await client.post("/categories", headers=auth_headers, json={
        "name": "My Extra", "display_order": 99,
    })).json()["id"]

    await client.post("/items/reset-defaults", headers=auth_headers)

    cats = (await client.get("/categories", headers=auth_headers)).json()
    assert not any(c["id"] == cat_id for c in cats)
