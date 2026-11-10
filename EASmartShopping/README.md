# Zentra

A self-hosted, full-stack e-commerce storefront with a **local-LLM shopping assistant**.
Next.js front end, FastAPI back end, SQLite, and a RAG pipeline (ChromaDB + Ollama) that
runs entirely on your own machine — no cloud API keys, no data leaving the box.

```
┌──────────────┐      ┌────────────────────┐      ┌──────────────┐
│   Next.js    │─────▶│  FastAPI backend   │─────▶│  SQLite DB   │
│  storefront  │      │  REST + SSE chat   │      └──────────────┘
│    :3000     │      │       :8000        │
└──────────────┘      │                    │      ┌──────────────┐
                      │  /api/chat/stream ─┼─────▶│  LangChain   │
                      │                    │      │  + ChromaDB  │
                      └─────────┬──────────┘      └──────┬───────┘
                                │                        │
                                ▼                        ▼
                      ┌─────────────────────────────────────────┐
                      │   Ollama  :11434   (local, on your PC)   │
                      │   chat  → qwen3.5:2b                    │
                      │   embed → nomic-embed-text              │
                      └─────────────────────────────────────────┘

┌──────────────┐
│  MCP Server  │──── stdio ──── any MCP client (Claude Code, etc.)
└──────────────┘
```

---

## 0. Rename the folder

Everything inside the project is already branded **Zentra**. The containing folder is
the one thing that must be renamed from outside a running session, because whatever
process has it open as its working directory holds a lock on it.

Close any editor / terminal sitting in the folder, then run once from the parent:

```powershell
Rename-Item "D:\Ai testing\DeepEval\EASmartShopping" -NewName "Zentra"
```

Nothing in the code depends on the folder name, so this is safe at any time. The only
place that references the path is the MCP `cwd` in section 6 below.

---

## 1. Prerequisites

| Requirement | Version | Check with |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Ollama | any recent | `ollama --version` |

---

## 2. Local LLM setup (Ollama)

Everything the assistant does — chat, product Q&A, bundles, semantic search — is powered
by models running locally through [Ollama](https://ollama.com). Two models are needed:

| Role | Model | Why |
|---|---|---|
| **Chat / reasoning** | `qwen3.5:2b` | Generates assistant replies. ~1.9 B params, Q8_0, 262 k context, supports tool-calling and thinking mode. Fast enough for token streaming on CPU/iGPU. |
| **Embeddings** | `nomic-embed-text` | Turns product names + descriptions into vectors for ChromaDB. `qwen3.5` **cannot** do this — Ollama serves it without the embedding head, so a dedicated embedding model is required. |

### Install the models

```bash
ollama pull qwen3.5:2b
ollama pull nomic-embed-text
```

Already have them? Confirm with:

```bash
ollama list
curl http://localhost:11434/api/tags
```

### Make sure Ollama is serving

Ollama normally runs as a background service on Windows. If it isn't:

```bash
ollama serve
```

Quick sanity check that both models respond:

```bash
# chat
curl http://localhost:11434/api/generate -d "{\"model\":\"qwen3.5:2b\",\"prompt\":\"hi\",\"stream\":false}"

# embeddings
curl http://localhost:11434/api/embed -d "{\"model\":\"nomic-embed-text\",\"input\":\"running shoes\"}"
```

### Where it's wired up

| File | Role |
|---|---|
| `backend/config.yaml` | The knobs you actually edit — model names, temperature, token limits, history length. |
| `backend/config.py` | Loads `config.yaml`, applies env-var overrides, supplies defaults. |
| `backend/rag.py` | `get_llm()` builds `ChatOllama`; `get_embeddings()` builds `OllamaEmbeddings`; both read from `config`. |

`backend/config.yaml`:

```yaml
ollama:
  base_url: "http://localhost:11434"
  chat_model: "qwen3.5:2b"        # swap to qwen3.5:4b for better answers, slower
  embed_model: "nomic-embed-text"

llm:
  temperature: 0.7
  max_tokens: 400                 # must be -1 when reasoning: true
  reasoning: false                # Qwen3.5 thinking mode — adds 30-100 s latency

chat:
  max_history_turns: 8
  vague_query_max_words: 8
```

### Swapping models

Edit `config.yaml` and restart the backend, **or** override per-run without touching files:

```powershell
$env:OLLAMA_CHAT_MODEL = "qwen3.5:4b"
$env:OLLAMA_EMBED_MODEL = "nomic-embed-text"
.\start.ps1
```

Env overrides: `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL`,
`LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_REASONING`, `CHAT_MAX_HISTORY_TURNS`.

> **Changing `embed_model` invalidates the vector store.** Delete `backend/chroma_db/`
> so it rebuilds with the new model's vectors — mixed embeddings return nonsense.

---

## 3. Install

```powershell
# from the project root
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd frontend
npm install
cd ..
```

---

## 4. Run

**One command (Windows):**

```powershell
.\start.ps1
```

**One command (macOS / Linux / Git Bash):**

```bash
./start.sh
```

**Or run the two halves manually:**

```powershell
# terminal 1 — backend
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# terminal 2 — frontend
cd frontend
npm run dev
```

| Surface | URL |
|---|---|
| Storefront | http://localhost:3000 |
| REST API | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |

On the **first** backend start it creates `backend/ecommerce.db`, seeds the catalogue,
and embeds every product into `backend/chroma_db/`. That initial embedding pass takes a
few minutes; later starts reuse the store and boot in seconds.

---

## 5. API reference

### Products

```bash
curl http://localhost:8000/api/products
curl "http://localhost:8000/api/products?search=backpack"
curl "http://localhost:8000/api/products?category=Electronics"
curl http://localhost:8000/api/products/1
curl "http://localhost:8000/api/products/semantic-search?q=something+to+keep+me+hydrated"
curl http://localhost:8000/api/products/1/similar
```

### Cart

```bash
curl http://localhost:8000/api/cart/my-session

curl -X POST http://localhost:8000/api/cart/my-session/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

curl -X PUT http://localhost:8000/api/cart/my-session/update \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 3}'

curl -X DELETE http://localhost:8000/api/cart/my-session/remove/1
curl -X DELETE http://localhost:8000/api/cart/my-session/clear
```

### Orders

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"session_id":"my-session","customer_name":"Jane Doe","customer_email":"jane@example.com","shipping_address":"12 Market St, Springfield"}'

curl http://localhost:8000/api/orders/1
curl "http://localhost:8000/api/orders?session_id=my-session"
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what headphones do you have?","session_id":"my-session"}'
```

The storefront uses the streaming variant (`/api/chat/stream`, server-sent events) so
replies appear token by token.

### Health

```bash
curl http://localhost:8000/api/health
```

A ready-made Postman collection lives at `Zentra.postman_collection.json`.

---

## 6. MCP server

`mcp_server.py` exposes the store over the Model Context Protocol (JSON-RPC over stdio):

```json
{
  "mcpServers": {
    "zentra": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "D:/Ai testing/DeepEval/Zentra"
    }
  }
}
```

| Tool | Description |
|---|---|
| `search_products` | Search by keyword or category |
| `get_product` | Product details by ID |
| `add_to_cart` | Add a product to a session cart |
| `get_cart` | Read cart contents |
| `create_order` | Place an order from the cart |
| `get_order` | Order details |
| `list_orders` | All orders for a session |

---

## 7. Project layout

```
Zentra/
├── backend/
│   ├── main.py                 # FastAPI app + routes
│   ├── database.py             # schema + catalogue seed
│   ├── crud.py                 # SQLite data access
│   ├── schemas.py              # Pydantic models
│   ├── rag.py                  # RAG, bundles, chat orchestration
│   ├── add_pc_components.py    # optional extra PC-parts seed
│   ├── config.py               # settings loader (yaml + env)
│   └── config.yaml             # <- LLM settings live here
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx      # shell: navbar + chat widget
│       │   ├── globals.css     # <- design tokens / theme
│       │   ├── page.tsx        # catalogue
│       │   ├── products/[id]/  # product detail
│       │   ├── cart/           # cart
│       │   ├── checkout/       # checkout
│       │   └── orders/         # order history
│       ├── components/
│       │   ├── Navbar.tsx
│       │   └── ChatWidget.tsx  # streaming chat, bundles, option pickers
│       └── lib/api.ts          # typed API client
├── mcp_server.py
├── start.ps1                   # Windows launcher
├── start.sh                    # bash launcher
├── requirements.txt
├── Features.md                 # full feature list
└── Zentra.postman_collection.json
```

---

## 8. Theme

The whole look is driven by CSS custom properties in `frontend/src/app/globals.css`.

| Token | Value | Role |
|---|---|---|
| `--primary` | `#0f766e` | Jade — buttons, links, focus rings |
| `--primary-hover` | `#115e59` | Pressed / hover |
| `--primary-deep` | `#134e4a` | Navbar gradient, dark fills |
| `--accent` | `#e07a3f` | Copper — badges, highlights |
| `--success` | `#3f9142` | Confirmations |
| `--danger` | `#e0485f` | Errors, destructive actions |
| `--bg` / `--surface-2` | `#faf8f5` / `#f3efe9` | Warm stone backgrounds |
| `--text` / `--text-2` / `--text-3` | `#1c1917` / `#57534e` / `#a8a29e` | Type ramp |

Typeface: **Plus Jakarta Sans**. Radii: `--radius-sm` 6px, `--radius` 10px, `--radius-lg` 18px.
Recolour the whole app by editing those tokens.

---

## 9. House brands

The catalogue is organised into in-house product lines, so every item carries a Zentra
sub-brand rather than a generic name:

| Line | Covers | Example |
|---|---|---|
| **Lumen** | Everyday apparel | Lumen Merino Wool Sweater |
| **Kinetix** | Sport & fitness | Kinetix Sports Water Bottle |
| **Veltra** | Footwear | Veltra Ridge Trail Running Shoes |
| **Stormline** | Outerwear | Stormline Waterproof Windbreaker Jacket |
| **Haverly** | Bags & luggage | Haverly Laptop Backpack |
| **Volta** | Consumer electronics | Volta Wireless Bluetooth Headphones |
| **Hearthen** | Home & kitchen | Hearthen Ceramic Coffee Mug Set |
| **Forge** | PC components | Forge DDR5 RAM Kit |

Real vendor names (ASUS, MSI, Corsair, Crucial, Kingston, Samsung, Seagate, Anker) are
kept on PC parts, because the spec sheets cite them factually.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Chat replies never arrive | Ollama isn't running → `ollama serve`; confirm `curl http://localhost:11434/api/tags` |
| `model "..." not found` | `ollama pull qwen3.5:2b` |
| `This server does not support embeddings` | You pointed `embed_model` at a chat model. Use `nomic-embed-text`. |
| Search returns irrelevant products | Embedding model changed — delete `backend/chroma_db/` and restart |
| Backend start is very slow the first time | Expected: it's embedding the catalogue. Subsequent starts are fast. |
| Port 3000/8000 already in use | `start.ps1` frees them automatically; otherwise kill the process yourself |
| Replies take 30-100 s | `reasoning: true` in `config.yaml`. Set it to `false` (and `max_tokens: 400`). |

---

## 11. Tech stack

- **Frontend** — Next.js 16, React 19, TypeScript, CSS custom properties
- **Backend** — FastAPI, Uvicorn, Pydantic v2, SQLite (WAL)
- **AI** — LangChain, `langchain-ollama`, ChromaDB, Ollama (`qwen3.5:2b` + `nomic-embed-text`)
- **Protocol** — MCP over JSON-RPC 2.0 / stdio
- **Testing** — pytest + DeepEval
