# WebSocket Platform Configuration

## Overview

The WebSocket platform allows users to connect to Hermes Agent through web browsers or any WebSocket client, enabling terminal-like interaction from anywhere.

## Features

- **Token Authentication**: Secure connections with configurable tokens
- **Rate Limiting**: Protection against message flooding
- **Connection Management**: Automatic cleanup of stale connections
- **Cross-Platform Delivery**: Can route messages to other platforms (Telegram, Discord, etc.)
- **Web Interface**: Built-in status page and health check endpoint

## Configuration

### config.yaml

Add the following to your `~/.hermes/config.yaml`:

```yaml
platforms:
  websocket:
    enabled: true
    extra:
      host: "127.0.0.1"        # WebSocket bind address
      port: 8765               # WebSocket port
      token: "your-secret-token"  # Authentication token
      max_connections: 10     # Maximum concurrent connections
```

### Environment Variables

You can also configure via environment variables:

```bash
export WEBSOCKET_TOKEN="your-secret-token"
```

### Configuration Options

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| host | - | `127.0.0.1` | Bind address |
| port | - | `8765` | WebSocket port |
| token | `WEBSOCKET_TOKEN` | (none) | Authentication token |
| max_connections | - | `10` | Max concurrent connections |

## Usage

### Starting the Gateway

```bash
# Start Hermes Gateway with WebSocket enabled
hermes gateway start

# Or run gateway in foreground
hermes gateway
```

### Connecting via WebSocket

#### Browser JavaScript

```javascript
const token = "your-secret-token";
const wsUrl = `ws://127.0.0.1:8765/ws?token=${token}`;

const ws = new WebSocket(wsUrl);

ws.onopen = () => {
    console.log("Connected to Hermes");
    ws.send(JSON.stringify({
        type: "chat",
        content: "Hello, Hermes!"
    }));
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "message") {
        console.log("Hermes:", msg.content);
    } else if (msg.type === "typing") {
        console.log("Hermes is typing...");
    }
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
};

ws.onclose = () => {
    console.log("Disconnected");
};
```

#### Python

```python
import asyncio
import websockets
import json

async def main():
    uri = "ws://127.0.0.1:8765/ws?token=your-secret-token"

    async with websockets.connect(uri) as ws:
        # Send a message
        await ws.send(json.dumps({
            "type": "chat",
            "content": "Hello, Hermes!"
        }))

        # Receive response
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "message":
                print(f"Hermes: {data['content']}")
            elif data["type"] == "typing":
                print("Hermes is typing...")

asyncio.run(main())
```

#### Web Terminal (HTML)

Save this as `websocket_terminal.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Hermes Terminal</title>
    <style>
        body {
            font-family: monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
        }
        #output {
            white-space: pre-wrap;
            height: calc(100vh - 100px);
            overflow-y: auto;
        }
        #input {
            width: 100%;
            background: #2d2d2d;
            color: #d4d4d4;
            border: 1px solid #3e3e3e;
            padding: 10px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div id="output"></div>
    <input type="text" id="input" placeholder="Type your message..." autofocus>
    <script>
        const token = prompt("Enter WebSocket token:");
        const ws = new WebSocket(`ws://127.0.0.1:8765/ws?token=${token}`);

        const output = document.getElementById('output');
        const input = document.getElementById('input');

        ws.onopen = () => {
            output.textContent += "Connected to Hermes\n";
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "message") {
                output.textContent += `Hermes: ${msg.content}\n`;
            } else if (msg.type === "connected") {
                output.textContent += "Connection established\n";
            }
            output.scrollTop = output.scrollHeight;
        };

        ws.onerror = () => {
            output.textContent += "Error: Connection failed\n";
        };

        ws.onclose = () => {
            output.textContent += "Disconnected\n";
        };

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                const content = input.value.trim();
                output.textContent += `You: ${content}\n`;
                ws.send(JSON.stringify({ type: "chat", content }));
                input.value = '';
            }
        });
    </script>
</body>
</html>
```

## API Endpoints

### WebSocket `/ws`

Main WebSocket endpoint for real-time communication.

**Query Parameters:**
- `token` (optional): Authentication token

**Message Types (Client → Server):**

```json
// Chat message
{"type": "chat", "content": "Hello!"}

// Ping
{"type": "ping"}

// Terminal resize
{"type": "resize", "cols": 120, "rows": 30}
```

**Message Types (Server → Client):**

```json
// Connection established
{"type": "connected", "client_id": "...", "authenticated": true}

// Chat response
{"type": "message", "content": "Hello! How can I help?", "timestamp": 1234567890}

// Typing indicator
{"type": "typing", "status": "start"}

// Pong
{"type": "pong", "timestamp": 1234567890}

// Error
{"type": "error", "error": "Rate limit exceeded"}
```

### Health Check `/health`

```bash
curl http://127.0.0.1:8765/health
```

Response:
```json
{
    "status": "ok",
    "platform": "websocket",
    "clients": 2,
    "max_clients": 10
}
```

### Index Page `/`

Simple HTML page showing connection status.

## Security Considerations

1. **Use a Strong Token**: Always use a secure, random token
2. **Bind to Localhost**: For development, bind to `127.0.0.1`
3. **Use TLS**: For production, use a reverse proxy with TLS (nginx, etc.)
4. **Rate Limiting**: Built-in rate limiting prevents abuse

## Production Deployment

For production, use a reverse proxy with TLS:

```nginx
server {
    listen 443 ssl;
    server_name hermes.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /ws {
        proxy_pass http://127.0.0.1:8765/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8765/;
    }
}
```

## Troubleshooting

### Connection Refused

Check if the port is already in use:
```bash
lsof -i :8765
```

### Invalid Token

Ensure the token matches exactly (case-sensitive):
```bash
curl http://127.0.0.1:8765/health
```

### Max Connections Reached

Wait for existing connections to close, or increase `max_connections` in config.

## Example Full Configuration

```yaml
# ~/.hermes/config.yaml
platforms:
  websocket:
    enabled: true
    extra:
      host: "127.0.0.1"
      port: 8765
      token: "your-very-secure-token-here"
      max_connections: 10
```

Then run:
```bash
hermes gateway
```

Access at: `http://127.0.0.1:8765/`
