# Runbook: local setup and troubleshooting

Written for Windows + PowerShell + Docker Desktop. Linux and macOS work the same, minus the
Windows notes.

## One-time setup

1. **Docker context.** `docker context show` must print `desktop-linux`. If not:
   `docker context use desktop-linux`. For any other server, pass `--context <name>` per
   command instead of switching, so a forgotten context never sends Citadel elsewhere.
2. **GNU make.** `winget install ezwinports.make`, then restart the terminal (fully close
   VS Code if using its terminal). Check `where.exe make`.
3. **uv.** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`, then `uv --version`.
4. **Git line endings.** `git config --global core.autocrlf input`.
5. **Ollama.** Set the user environment variable `OLLAMA_HOST=0.0.0.0`, quit Ollama from the
   tray, start it again. Pull models:
   `ollama pull qwen2.5-coder:7b; ollama pull llama3.1:8b; ollama pull nomic-embed-text`.
6. **`.env`.** `Copy-Item .env.example .env`. Generate each secret with:
   ```powershell
   -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
   ```
   Put the Postgres password in both `POSTGRES_PASSWORD` and `DATABASE_URL`.

## Start

```powershell
docker compose up -d omniroute
curl.exe http://127.0.0.1:20128/healthz          # expect: ok
# dashboard: providers → combos (citadel-brain/worker/cheap) → endpoint key → OMNIROUTE_API_KEY
make up
make smoke                                        # all four tiers answer
make notify-test
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `make` not recognized | Not installed, or PATH not refreshed | Install with winget; restart the terminal or VS Code |
| "variable is not set" warnings | `.env` missing or saved as `.env.txt` | `Get-ChildItem -Force .env*`; rename |
| Container "healthy" but `localhost` can't connect; `netstat` shows nothing | Docker is using a **remote context** | `docker context show`; `docker context use desktop-linux` |
| `invalid volume specification: 'C:\...'` | Same: a remote engine can't see laptop paths | Same fix |
| Postgres fails: port already allocated | Windows PostgreSQL on 5432 | Change the compose port to `"127.0.0.1:5433:5432"` |
| `private` tier fails in smoke | Ollama only on 127.0.0.1 | `OLLAMA_HOST=0.0.0.0`, restart Ollama |
| `brain`/`worker`/`cheap` return 401 | Endpoint key missing or wrong | Recreate in the OmniRoute dashboard |
| 404 "model not found" | `MODEL_*` doesn't match the combo name | Match names exactly |
| OmniRoute won't start | Required env vars changed in a new version | Compare with OmniRoute's `.env.example`; pin the image tag |
| Arena leaderboard 429 in OmniRoute logs | Optional ranking data rate-limited | Ignore |
| Schema changes not applied | `init.sql` runs only on an empty volume | `make down; docker volume rm citadel_pg-data; make up` |
| `curl` behaves oddly | PowerShell aliases `curl` | Use `curl.exe` |
| Port forwarding broken on a correct local context | Docker Desktop networking stuck | Quit Docker Desktop from the tray, `wsl --shutdown`, start again |
