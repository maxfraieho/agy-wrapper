# agy — AGY Proxy Wrapper for OpenDesign

Python CLI wrapper that connects OpenDesign (`antigravity` agent) to multiple LLM sources with automatic fallback.

| Priority | Source | IP | Models |
|----------|--------|----|--------|
| 1 | AGY3 tablet | `192.168.3.204:8080` | gemini-*, claude-* |
| 2 | AGY phone | `192.168.3.195:8080` | gemini-*, claude-* |
| 3 | Local proxy | `172.17.0.1:18880` | standard-proxy, coding-proxy, ... |

---

## Quick Start

```bash
cd ~/open-design-custom
docker build -t open-design-custom:latest .
bash run.sh
```

Після старту доступно два URL:

| URL | Особливість |
|-----|------------|
| `http://192.168.3.184:7459/` | Прямий доступ, потрібен Bearer токен або BYOK |
| `http://192.168.3.184:7460/` | **NGINX proxy** — токен вбудовано, просто відкрий і користуйся |

---

## Підключення через :7460 (рекомендовано)

NGINX на порту `:7460` автоматично вставляє Bearer токен в кожен запит.  
Ніяких налаштувань у браузері — просто відкрий `http://192.168.3.184:7460/`.

При першому відкритті:
1. **Welcome** → Continue
2. **Connect** → вибери **Local CLI** (агент `antigravity` вже доступний)
3. **About you** → вибери роль → Continue
4. **New Chat** → введи запит → Shift+Enter

> Відповідь може зайняти 40-60 секунд — AGY обробляє через Gemini/Claude.

---

## Підключення через :7459 (BYOK)

Якщо хочеш підключитись напряму через BYOK (Bring Your Own Key):

### Варіант A — Local CLI з токеном

Bearer токен: `2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a`

### Варіант B — Custom OpenAI provider (agy-server)

У Settings → Providers → Add Custom:
- **Provider:** OpenAI (Custom)
- **API Key:** `freecc`
- **Base URL:** `http://192.168.3.184:18882/v1`
- **Model:** `default`

agy-server — OpenAI-compatible HTTP wrapper навколо `agy` CLI, порт `:18882`.

---

## agy-server (OpenAI-compatible HTTP API)

Файл: `server.py`

Запускається автоматично з `run.sh` всередині контейнера:
```sh
docker exec -d open-design sh -c "python3 /usr/local/bin/agy-server 18882 2>/tmp/agy-server.log"
```

Ендпоінти:
```
GET  /v1/models               — список моделей
POST /v1/chat/completions     — OpenAI-compatible chat
GET  /health                  — статус
```

Тест:
```bash
curl http://192.168.3.184:18882/health
curl http://192.168.3.184:18882/v1/models
curl -X POST http://192.168.3.184:18882/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"hello"}]}'
```

---

## NGINX proxy конфіг (/etc/nginx/http.d/opendesign.conf)

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ""      close;
}

server {
    listen 7460;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:7459;
        proxy_http_version 1.1;
        proxy_set_header Authorization "Bearer 2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a";
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

Перезапуск NGINX:
```bash
sudo nginx -s reload
```

---

## run.sh (повна команда Docker)

```sh
#!/bin/sh
docker stop open-design 2>/dev/null; docker rm open-design 2>/dev/null
docker run -d \
  --name open-design \
  --restart unless-stopped \
  -p 7459:7456 -p 18882:18882 \
  -v open_design_data:/app/.od \
  -e OD_ALLOWED_ORIGINS="http://192.168.3.184:7459,http://192.168.3.195:7459,http://192.168.3.162:7459,http://192.168.3.25:7459,http://192.168.3.184:7460,http://192.168.3.195:7460,http://192.168.3.162:7460,http://192.168.3.25:7460" \
  -e LOCAL_PROXY_TOKEN=freecc \
  -e AGY_API_KEY=proxy-key \
  -e OD_BIND_HOST=0.0.0.0 \
  -e OD_PORT=7456 \
  -e OD_API_TOKEN=2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a \
  open-design-custom:latest \
  node apps/daemon/dist/cli.js --no-open
sleep 3
docker exec -d open-design sh -c "python3 /usr/local/bin/agy-server 18882 2>/tmp/agy-server.log"
```

> **OD_ALLOWED_ORIGINS** повинен містити і `:7459` і `:7460` варіанти для кожного IP — інакше 403.

---

## Використання ai-drakon в OpenDesign

Проект `ai-drakon` вже зареєстровано в OpenDesign (project_id: `ai-drakon`).

### Через MCP (Claude → OpenDesign)

Claude має MCP інструменти для прямого керування OpenDesign:

```
mcp__opendesign__run(
  project_id="ai-drakon",
  agent_id="antigravity",
  prompt="Generate a mobile navigation component for ai-drakon with dark theme, Tailwind, Lucide icons"
)
```

### Через браузер

1. Відкрий `http://192.168.3.184:7460/`
2. Вибери або створи проект **AI-Drakon Platform**
3. Вибери агент **Antigravity**
4. Вводь запити на генерацію компонентів

### Стиль компонентів ai-drakon

При запитах до OpenDesign для ai-drakon завжди вказуй:
```
Framework: React 18 + TypeScript + Tailwind CSS + Vite
Icons: Lucide React  
Router: react-router-dom v6
Theme: dark, Modern minimal (Vercel/Linear style)
Mobile-first: md:hidden responsive classes
Glassmorphism overlays: bg-black/60 backdrop-blur-lg
Output: single .tsx file, TypeScript interfaces, usage example
```

### Компоненти що потребують покращення

```
src/components/mobile/     — мобільна навігація
src/components/pipeline/   — DRAKON pipeline UI
src/components/workspace/  — workspace view
src/pages/                 — всі сторінки (16 pages)
```

---

## Модель в OpenDesign → реальний маршрут

| Модель в UI | ID | Ендпоінт |
|-------------|-----|---------|
| `Default` | gemini-2.5-flash | AGY3 або AGY phone |
| `Gemini 3.1 Pro (High)` | gemini-3.1-pro-high | AGY3 → AGY phone |
| `Gemini 3.5 Flash (Medium)` | gemini-3.5-flash-medium | AGY3 → AGY phone |
| `Claude Sonnet 4.6 (Thinking)` | claude-sonnet-4-6 | AGY3 → AGY phone |
| `Claude Opus 4.6 (Thinking)` | claude-opus-4-6-thinking | AGY3 → AGY phone |
| `GPT-OSS 120B (Medium)` | standard-proxy | local 172.17.0.1:18880 |

---

## CLI Usage

```bash
echo "Hello" | agy
echo "Write a component" | agy --model "Claude Sonnet 4.6 (Thinking)"
agy --version
```

---

## Якщо щось не працює

**403 в браузері** → IP браузера не в `OD_ALLOWED_ORIGINS`. Додай в `run.sh` і перезапусти.

**Порожня відповідь** → Всі ендпоінти на квоті:
```bash
ssh vokov@192.168.3.184 'docker exec open-design python3 -c "
import socket
for n,h,p in [(\"agy3\",\"192.168.3.204\",8080),(\"phone\",\"192.168.3.195\",8080),(\"local\",\"172.17.0.1\",18880)]:
    try: socket.create_connection((h,p),2); print(\"OK\",n)
    except: print(\"ERR\",n)
"'
```

**agy-server не відповідає** → Запусти вручну:
```bash
docker exec -d open-design sh -c "python3 /usr/local/bin/agy-server 18882"
```

**AGY IP змінився** → Оновити в `agy` скрипт (рядки `ENDPOINTS`) і `docker build + bash run.sh`.

---

## Docker Build

```bash
cd ~/open-design-custom
docker build -t open-design-custom:latest .
bash run.sh
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PROXY_TOKEN` | `freecc` | Token для local free-claude-code-proxy |
| `AGY_API_KEY` | `proxy-key` | Token для AGY3 / AGY phone |
| `OD_API_TOKEN` | — | OpenDesign Bearer token (web UI auth) |
| `OD_ALLOWED_ORIGINS` | — | Comma-separated дозволені браузерні origin |
| `AGY_HTTP_PORT` | `18882` | Port для agy-server |

---

## OpenDesign: ai-drakon design workflow

Plugin `ai-drakon-mobile` registered in OpenDesign with defaults.
**Always pass `pluginId: "ai-drakon-mobile"`** — skips discovery form, generates directly.

### REST API (direct, no MCP needed)

```bash
# 1. Start run
curl -s -X POST \
  -H "Authorization: Bearer 2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a" \
  -H "Content-Type: application/json" \
  -H "Origin: http://192.168.3.184:7459" \
  http://192.168.3.184:7459/api/runs \
  -d '{"projectId":"ai-drakon","agentId":"antigravity","pluginId":"ai-drakon-mobile","message":"YOUR PROMPT"}'

# 2. Poll until done (replace RUN_ID)
until curl -s -H "Authorization: Bearer 2269d21455f772f62878631c5665d7ff1e57fe58790d976e80871c427a3dee4a" \
  http://192.168.3.184:7459/api/runs/RUN_ID | grep -q '"succeeded"'; do sleep 5; done

# 3. Read output (via SSH into Docker)
ssh vokov@192.168.3.184 \
  'docker exec open-design cat /app/.od/runs/RUN_ID/events.jsonl | python3 -c "
import sys,json
for l in sys.stdin:
    try:
        e=json.loads(l)
        if e.get(\"event\")==\"stdout\": print(e[\"data\"].get(\"chunk\",\"\"),end=\"\")
    except: pass
"'
```

### Continue conversation (conversationId)

First run returns `conversationId`. Pass it in follow-up runs for design iterations:
```bash
-d '{"projectId":"ai-drakon","conversationId":"CONV_ID","pluginId":"ai-drakon-mobile","message":"Refine..."}'
```

Current ai-drakon conversationId: `b045d5ce-20d3-46c4-9554-96d933800dba`

### Generated components location

```
workspace/ai-drakon-scaffolder/src/components/mobile/MobileNavBar.tsx   # first generated
```

### Prompt template for ai-drakon components

```
Generate a [COMPONENT] for ai-drakon platform.
React 18 TypeScript Tailwind CSS, dark theme (Vercel/Linear style).
Lucide icons, react-router-dom v6, mobile-first md:hidden.
Glassmorphism: bg-black/60 backdrop-blur-lg border-t border-white/10.
Output: full .tsx file, TypeScript interfaces, usage example.
```