# agy — AGY Proxy Wrapper for OpenDesign

Python CLI wrapper that connects OpenDesign (`antigravity` agent) to multiple LLM sources:

| Priority | Source | Models |
|----------|--------|--------|
| 1 | Local proxy `172.17.0.1:18880` | standard-proxy, coding-proxy, agent-proxy, ... |
| 2 | AGY3 tablet `192.168.3.162:8080` | gemini-*, claude-* |
| 3 | AGY phone `192.168.3.25:8080` | gemini-*, claude-* (fallback) |

## Usage

```bash
# Version check (used by OpenDesign to detect CLI)
agy --version

# With model
echo "Hello" | agy --model gemini-2.5-pro

# Default (standard-proxy via local proxy)
echo "Hello" | agy
```

## OpenDesign Integration

OpenDesign agent config:
- **id**: `antigravity`
- **bin**: `agy`
- **streamFormat**: `plain`

## Docker

```bash
docker build -t open-design-custom:latest .

docker run -d --name open-design \
  --restart always --read-only --tmpfs /tmp \
  --security-opt no-new-privileges:true \
  --memory 512m --pids-limit 256 \
  -p 0.0.0.0:7459:7456 \
  -e NODE_ENV=production \
  -e OD_BIND_HOST=0.0.0.0 \
  -e OD_PORT=7456 \
  -e OD_API_TOKEN=<your-token> \
  -e OD_ALLOWED_ORIGINS=http://192.168.3.184:7459 \
  -e LOCAL_PROXY_TOKEN=freecc \
  -e AGY_API_KEY=proxy-key \
  -v open_design_data:/app/.od \
  open-design-custom:latest
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_PROXY_TOKEN` | `freecc` | Token for local free-claude-code-proxy |
| `AGY_API_KEY` | `proxy-key` | Token for AGY proxy |
| `AGY_MODEL` | `standard-proxy` | Override default model |
