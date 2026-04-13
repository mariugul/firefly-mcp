import os
import httpx

FIREFLY_URL = os.environ.get("FIREFLY_URL", "http://localhost:8080/api/v1")
FIREFLY_TOKEN = os.environ.get("FIREFLY_TOKEN", "")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {FIREFLY_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{FIREFLY_URL}{path}", headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()


async def post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{FIREFLY_URL}{path}", headers=_headers(), json=body)
        r.raise_for_status()
        return r.json()


async def put(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{FIREFLY_URL}{path}", headers=_headers(), json=body)
        r.raise_for_status()
        return r.json()


async def delete(path: str) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{FIREFLY_URL}{path}", headers=_headers())
        r.raise_for_status()


# --- Accounts ---

async def list_accounts(account_type: str | None = None) -> list[dict]:
    params = {"limit": 100}
    if account_type:
        params["type"] = account_type
    data = await get("/accounts", params=params)
    return [
        {
            "id": a["id"],
            "name": a["attributes"]["name"],
            "type": a["attributes"]["type"],
            "currency": a["attributes"]["currency_code"],
            "balance": a["attributes"]["current_balance"],
            "account_number": a["attributes"]["account_number"],
        }
        for a in data.get("data", [])
    ]


async def create_account(
    name: str,
    account_type: str,
    currency_code: str = "NOK",
    account_number: str | None = None,
    account_role: str = "defaultAsset",
    liability_type: str | None = None,
    liability_direction: str | None = None,
) -> dict:
    body: dict = {
        "name": name,
        "type": account_type,
        "currency_code": currency_code,
        "active": True,
    }
    if account_number:
        body["account_number"] = account_number
    if account_type == "asset":
        body["account_role"] = account_role
    if account_type == "liabilities":
        body["liability_type"] = liability_type or "debt"
        body["liability_direction"] = liability_direction or "debit"
    data = await post("/accounts", body)
    return {"id": data["data"]["id"], "name": data["data"]["attributes"]["name"]}


async def update_account(account_id: str, fields: dict) -> dict:
    data = await put(f"/accounts/{account_id}", fields)
    return {"id": data["data"]["id"], "name": data["data"]["attributes"]["name"]}


async def delete_account(account_id: str) -> str:
    await delete(f"/accounts/{account_id}")
    return f"Account {account_id} deleted."


# --- Transactions ---

async def list_transactions(
    account_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 50,
) -> list[dict]:
    params: dict = {"limit": limit}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    path = f"/accounts/{account_id}/transactions" if account_id else "/transactions"
    data = await get(path, params=params)
    results = []
    for t in data.get("data", []):
        attrs = t["attributes"]
        for split in attrs.get("transactions", []):
            results.append({
                "id": t["id"],
                "date": split["date"],
                "description": split["description"],
                "amount": split["amount"],
                "type": split["type"],
                "source": split.get("source_name"),
                "destination": split.get("destination_name"),
                "category": split.get("category_name"),
            })
    return results


async def create_transaction(
    description: str,
    amount: float,
    date: str,
    transaction_type: str,
    source_name: str | None = None,
    destination_name: str | None = None,
    category_name: str | None = None,
    budget_name: str | None = None,
) -> dict:
    split: dict = {
        "type": transaction_type,
        "date": date,
        "amount": str(amount),
        "description": description,
    }
    if source_name:
        split["source_name"] = source_name
    if destination_name:
        split["destination_name"] = destination_name
    if category_name:
        split["category_name"] = category_name
    if budget_name:
        split["budget_name"] = budget_name
    data = await post("/transactions", {"transactions": [split]})
    return {"id": data["data"]["id"]}


# --- Budgets ---

async def list_budgets() -> list[dict]:
    data = await get("/budgets", params={"limit": 100})
    return [
        {
            "id": b["id"],
            "name": b["attributes"]["name"],
            "amount": b["attributes"].get("auto_budget_amount"),
        }
        for b in data.get("data", [])
    ]


async def create_budget(name: str, amount: float | None = None) -> dict:
    body: dict = {"name": name}
    if amount is not None:
        body["auto_budget_amount"] = str(amount)
        body["auto_budget_period"] = "monthly"
        body["auto_budget_type"] = "reset"
    data = await post("/budgets", body)
    return {"id": data["data"]["id"], "name": data["data"]["attributes"]["name"]}


# --- Categories ---

async def list_categories() -> list[dict]:
    data = await get("/categories", params={"limit": 100})
    return [
        {"id": c["id"], "name": c["attributes"]["name"]}
        for c in data.get("data", [])
    ]


async def create_category(name: str) -> dict:
    data = await post("/categories", {"name": name})
    return {"id": data["data"]["id"], "name": data["data"]["attributes"]["name"]}


# --- Import ---

async def trigger_import(csv_path: str, config_path: str) -> str:
    """Trigger the Firefly data importer via the /autoupload endpoint."""
    importer_url = os.environ.get("FIREFLY_IMPORTER_URL", "http://localhost:8081")
    secret = os.environ.get("AUTO_IMPORT_SECRET", "")
    async with httpx.AsyncClient(timeout=120) as client:
        with open(csv_path, "rb") as csv_file, open(config_path, "rb") as cfg_file:
            r = await client.post(
                f"{importer_url}/autoupload",
                data={"secret": secret},
                files={
                    "importable": (os.path.basename(csv_path), csv_file, "text/csv"),
                    "json": (os.path.basename(config_path), cfg_file, "application/json"),
                },
                headers={"Authorization": f"Bearer {FIREFLY_TOKEN}"},
            )
        r.raise_for_status()
        return r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
