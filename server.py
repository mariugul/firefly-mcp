import asyncio
import base64
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import firefly_client as fc

app = Server("firefly-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_accounts",
            description="List Firefly III accounts. Optionally filter by type: asset, liabilities, expense, revenue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "description": "Filter by account type: asset, liabilities, expense, revenue",
                    }
                },
            },
        ),
        types.Tool(
            name="create_account",
            description="Create a new Firefly III account.",
            inputSchema={
                "type": "object",
                "required": ["name", "account_type"],
                "properties": {
                    "name": {"type": "string"},
                    "account_type": {"type": "string", "description": "asset or liabilities"},
                    "currency_code": {"type": "string", "default": "NOK"},
                    "account_number": {"type": "string"},
                    "account_role": {"type": "string", "default": "defaultAsset"},
                    "liability_type": {"type": "string", "description": "loan, debt, or mortgage"},
                    "liability_direction": {"type": "string", "description": "debit or credit"},
                },
            },
        ),
        types.Tool(
            name="update_account",
            description="Update fields on an existing Firefly III account by ID.",
            inputSchema={
                "type": "object",
                "required": ["account_id", "fields"],
                "properties": {
                    "account_id": {"type": "string"},
                    "fields": {"type": "object", "description": "Key-value pairs to update"},
                },
            },
        ),
        types.Tool(
            name="delete_account",
            description="Delete a Firefly III account by ID.",
            inputSchema={
                "type": "object",
                "required": ["account_id"],
                "properties": {
                    "account_id": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="list_transactions",
            description="List transactions, optionally filtered by account, date range, and limit.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Filter by account ID"},
                    "start": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        types.Tool(
            name="create_transaction",
            description="Create a transaction in Firefly III.",
            inputSchema={
                "type": "object",
                "required": ["description", "amount", "date", "transaction_type"],
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "transaction_type": {"type": "string", "description": "withdrawal, deposit, or transfer"},
                    "source_name": {"type": "string"},
                    "destination_name": {"type": "string"},
                    "category_name": {"type": "string"},
                    "budget_name": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="trigger_import",
            description="Trigger a CSV import via the Firefly III data importer. Pass the raw CSV content and the name of a config stored on the server (e.g. 'normalized-brukskonto').",
            inputSchema={
                "type": "object",
                "required": ["csv_content", "config_name"],
                "properties": {
                    "csv_content": {"type": "string", "description": "Raw CSV file content as a string"},
                    "config_name": {"type": "string", "description": "Name of the import config stored on the server under ~/imports/configs/, without .json extension"},
                },
            },
        ),
        types.Tool(
            name="list_import_configs",
            description="List available import config names stored on the server.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_budgets",
            description="List all budgets in Firefly III.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_budget",
            description="Create a budget in Firefly III.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": "number", "description": "Monthly auto-budget amount"},
                },
            },
        ),
        types.Tool(
            name="list_categories",
            description="List all categories in Firefly III.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_category",
            description="Create a category in Firefly III.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "list_accounts":
            result = await fc.list_accounts(arguments.get("account_type"))
        elif name == "create_account":
            result = await fc.create_account(
                name=arguments["name"],
                account_type=arguments["account_type"],
                currency_code=arguments.get("currency_code", "NOK"),
                account_number=arguments.get("account_number"),
                account_role=arguments.get("account_role", "defaultAsset"),
                liability_type=arguments.get("liability_type"),
                liability_direction=arguments.get("liability_direction"),
            )
        elif name == "update_account":
            result = await fc.update_account(arguments["account_id"], arguments["fields"])
        elif name == "delete_account":
            result = await fc.delete_account(arguments["account_id"])
        elif name == "list_transactions":
            result = await fc.list_transactions(
                account_id=arguments.get("account_id"),
                start=arguments.get("start"),
                end=arguments.get("end"),
                limit=arguments.get("limit", 50),
            )
        elif name == "create_transaction":
            result = await fc.create_transaction(
                description=arguments["description"],
                amount=arguments["amount"],
                date=arguments["date"],
                transaction_type=arguments["transaction_type"],
                source_name=arguments.get("source_name"),
                destination_name=arguments.get("destination_name"),
                category_name=arguments.get("category_name"),
                budget_name=arguments.get("budget_name"),
            )
        elif name == "trigger_import":
            result = await fc.trigger_import_with_config_name(arguments["csv_content"], arguments["config_name"])
        elif name == "list_import_configs":
            result = await fc.list_import_configs()
        elif name == "list_budgets":
            result = await fc.list_budgets()
        elif name == "create_budget":
            result = await fc.create_budget(arguments["name"], arguments.get("amount"))
        elif name == "list_categories":
            result = await fc.list_categories()
        elif name == "create_category":
            result = await fc.create_category(arguments["name"])
        else:
            result = f"Unknown tool: {name}"
    except Exception as e:
        result = f"Error: {e}"

    return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
