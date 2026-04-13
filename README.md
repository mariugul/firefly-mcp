# firefly-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [Firefly III](https://firefly-iii.org), exposing its REST API as tools callable by AI assistants like Windsurf/Cascade.

## Tools

| Tool | Description |
|---|---|
| `list_accounts` | List accounts (filter by type) |
| `create_account` | Create asset or liability account |
| `update_account` | Update account fields |
| `delete_account` | Delete account by ID |
| `list_transactions` | Query transactions (by account, date, limit) |
| `create_transaction` | Create a withdrawal, deposit, or transfer |
| `trigger_import` | Trigger CSV import via data importer |
| `list_budgets` | List all budgets |
| `create_budget` | Create a monthly budget |
| `list_categories` | List all categories |
| `create_category` | Create a category |

## Requirements

- Python 3.12+ **or** Docker
- Firefly III running (Docker or standalone)

## Docker (recommended)

The image is published automatically to GHCR on every push to `main`.

### Run directly on the VM

```bash
docker pull ghcr.io/mariugul/firefly-mcp:latest
docker run --rm --network host -e FIREFLY_TOKEN=your_token ghcr.io/mariugul/firefly-mcp
```

`--network host` is required so the container can reach Firefly at `localhost:8080`.

### Windsurf MCP config (Docker)

```json
{
  "mcpServers": {
    "firefly": {
      "command": "ssh",
      "args": [
        "firefly",
        "docker run --rm --network host -e FIREFLY_TOKEN=your_token ghcr.io/mariugul/firefly-mcp:latest"
      ]
    }
  }
}
```

## Setup (manual / development)

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set FIREFLY_TOKEN to your Personal Access Token
# (Firefly UI → Profile → OAuth → Personal Access Tokens)
```

### 4. Configure Windsurf MCP

Add the following to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "firefly": {
      "command": "ssh",
      "args": [
        "firefly",
        "FIREFLY_TOKEN=your_token_here ~/firefly-mcp/.venv/bin/python ~/firefly-mcp/server.py"
      ]
    }
  }
}
```

Replace `your_token_here` with your Personal Access Token, then reload Windsurf.

### Deploy on VM

```bash
ssh firefly
git clone https://github.com/mariugul/firefly-mcp ~/firefly-mcp
cd ~/firefly-mcp
uv sync
cp .env.example .env
# edit .env
```

To update:
```bash
ssh firefly "cd ~/firefly-mcp && git pull && uv sync"
```

## Local development

```bash
uv run python server.py
```
