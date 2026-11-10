# RUN

```powershell
cd "D:\Ai testing\DeepEval\Zentra"
.\start.ps1
```

Store → http://localhost:3000 · API → http://localhost:8000 · Docs → http://localhost:8000/docs
`Ctrl+C` stops both.

Script blocked? `powershell -ExecutionPolicy Bypass -File ".\start.ps1"`

## Manual (two terminals)

```powershell
 cd "D:\Ai testing\DeepEval\Zentra\backend"
  ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
cd "D:\Ai testing\DeepEval\Zentra\frontend"
  npm run dev
```

## Ollama (needed for chat)

```bash
ollama serve
ollama pull qwen3.5:2b
ollama pull nomic-embed-text
```

## Fresh clone only

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend ; npm install ; cd ..
```

## Notes

- `start.ps1` kills anything already on :3000 / :8000.
- Models/settings: `backend/config.yaml`. Change `embed_model` → delete `backend/chroma_db/`.
- Slow replies → `reasoning: false` in `config.yaml`.
