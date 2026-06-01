# agy — AGY Proxy Wrapper for OpenDesign

Python CLI wrapper that connects OpenDesign (`antigravity` agent) to multiple LLM sources with automatic fallback.

| Priority | Source | IP | Models |
|----------|--------|----|--------|
| 1 | AGY3 tablet | `192.168.3.204:8080` | gemini-*, claude-* |
| 2 | AGY phone | `192.168.3.195:8080` | gemini-*, claude-* |
| 3 | Local proxy | `172.17.0.1:18880` | standard-proxy, coding-proxy, ... |

If a source returns 503 (quota exceeded) or is unreachable, the next one is tried automatically.

---

## Quick Start — Run on dev server

```bash
cd ~/open-design-custom
bash run.sh
```

OpenDesign UI буде доступний на: **http://192.168.3.184:7459/**

---

## Підключення через web UI (покрокова інструкція)

### Крок 1 — Відкрити інтерфейс

Відкрий у браузері: `http://192.168.3.184:7459/`

### Крок 2 — Ввести API токен

При першому відкритті або якщо питає авторизацію, введи токен:

```
2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a
```

> Токен можна зберегти в браузері — він зберігається в localStorage.

### Крок 3 — Вибрати агента

У вікні вибору агента обери **Antigravity** (єдиний зі статусом ✓ Available).

- Якщо агенти не відображаються — переконайся що токен введено правильно.
- Antigravity = наш `agy` wrapper, вже встановлений всередині контейнера.

### Крок 4 — Вибрати модель

Після вибору Antigravity зʼявиться список моделей:

| Модель в UI | Реальний маршрут |
|-------------|-----------------|
| `Default (CLI config)` | gemini-2.5-flash через AGY |
| `Gemini 3.1 Pro (High)` | gemini-3.1-pro-high |
| `Gemini 3.1 Pro (Low)` | gemini-3.1-pro-low |
| `Gemini 3.5 Flash (High)` | gemini-pro-agent |
| `Gemini 3.5 Flash (Medium)` | gemini-3.5-flash-medium |
| `Gemini 3.5 Flash (Low)` | gemini-3.5-flash-low |
| `Claude Sonnet 4.6 (Thinking)` | claude-sonnet-4-6 |
| `Claude Opus 4.6 (Thinking)` | claude-opus-4-6-thinking |
| `GPT-OSS 120B (Medium)` | standard-proxy (local) |

**Рекомендація:** починай з `Default` або `Gemini 3.5 Flash (Medium)` — швидкі та стабільні.

### Крок 5 — Почати чат

Натисни **New Chat**, введи запит. Якщо AGY3 на квоті — `agy` автоматично переключиться на AGY phone або local proxy без помилки.

---

## Якщо щось не працює

### Пустий список агентів / "No agents available"
→ Перевір токен (Крок 2). Токен чутливий до пробілів.

### "Agent not available" або помилка при запиті
→ Перевір статус контейнера:
```bash
sshpass -p '805235io.' ssh vokov@192.168.3.184 'docker ps | grep open-design'
```
→ Переглянь логи:
```bash
sshpass -p '805235io.' ssh vokov@192.168.3.184 'docker logs open-design --tail 30'
```

### Порожня відповідь або "empty response"
→ Всі ендпоінти на квоті або недоступні. Перевір:
```bash
sshpass -p '805235io.' ssh vokov@192.168.3.184 'docker exec open-design python3 -c "
import socket
for name,host,port in [(\"agy3\",\"192.168.3.204\",8080),(\"agy-phone\",\"192.168.3.195\",8080),(\"local\",\"172.17.0.1\",18880)]:
    try:
        with socket.create_connection((host,port),timeout=2): print(f\"OK  {name}\")
    except: print(f\"ERR {name}\")
"'
```

### AGY phone/tablet змінили IP
→ Оновити `agy` скрипт (рядки `ENDPOINTS`) і перезібрати:
```bash
# на dev сервері (192.168.3.184):
cd ~/open-design-custom
nano agy          # змінити IP
cp agy ~/agy-wrapper/agy
docker build -t open-design-custom:latest .
bash run.sh
```

---

## CLI Usage

```bash
# Version check
agy --version

# Default model via stdin
echo "Hello" | agy

# Specific model
echo "Write a function" | agy --model "Claude Sonnet 4.6 (Thinking)"

# Or by internal ID
echo "Hello" | agy --model gemini-3.1-pro-high
```

---

## OpenDesign Integration Details

OpenDesign agent config (embedded in `antigravity.js` inside container):
- **id**: `antigravity`
- **bin**: `agy`
- **streamFormat**: `plain`
- **promptViaStdin**: `true`

---

## Docker Build & Deploy

```bash
# Build
docker build -t open-design-custom:latest .

# Run (full command)
docker stop open-design 2>/dev/null; docker rm open-design 2>/dev/null
docker run -d \
  --name open-design \
  --restart unless-stopped \
  -p 7459:7456 \
  -v open_design_data:/app/.od \
  -e OD_ALLOWED_ORIGINS="http://192.168.3.184:7459,http://192.168.3.195:7459,http://192.168.3.162:7459,http://192.168.3.25:7459" \
  -e LOCAL_PROXY_TOKEN=freecc \
  -e AGY_API_KEY=proxy-key \
  -e OD_BIND_HOST=0.0.0.0 \
  -e OD_PORT=7456 \
  -e OD_API_TOKEN=2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a \
  open-design-custom:latest \
  node apps/daemon/dist/cli.js --no-open
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PROXY_TOKEN` | `freecc` | Token for local free-claude-code-proxy |
| `AGY_API_KEY` | `proxy-key` | Token for AGY3 / AGY phone proxy |
| `OD_API_TOKEN` | — | OpenDesign web UI auth token |
| `OD_ALLOWED_ORIGINS` | — | Comma-separated allowed browser origins |
