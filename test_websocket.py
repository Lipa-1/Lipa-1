#!/usr/bin/env python3
"""
WebSocket Test Client for Hermes Agent

Usage:
    python test_websocket.py [token]

If no token is provided, attempts to read from WEBSOCKET_TOKEN environment variable.
"""

import asyncio
import json
import sys
import os
import websockets
from datetime import datetime


async def test_websocket(token: str = None, host: str = "127.0.0.1", port: int = 8765):
    """Test WebSocket connection to Hermes Agent."""

    # Get token
    if not token:
        token = os.environ.get("WEBSOCKET_TOKEN", "")

    if not token:
        print("⚠️  Warning: No token provided. Connection may be rejected.")
        token = ""

    uri = f"ws://{host}:{port}/ws"
    if token:
        uri += f"?token={token}"

    print(f"\n{'='*60}")
    print(f"WebSocket Test Client for Hermes Agent")
    print(f"{'='*60}")
    print(f"Host: {host}:{port}")
    print(f"Token: {'*' * len(token) if token else '(none)'}")
    print(f"{'='*60}\n")

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri, ping_interval=30) as ws:
            print("✅ Connected successfully!\n")

            # Listen for messages
            async def receive_messages():
                try:
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type", "unknown")

                            if msg_type == "connected":
                                print(f"📡 Connection confirmed")
                                print(f"   Client ID: {data.get('client_id', 'N/A')}")
                                print(f"   Authenticated: {data.get('authenticated', False)}")
                                print()

                            elif msg_type == "message":
                                content = data.get("content", "")
                                print(f"\n🤖 Hermes:")
                                print(f"   {content}\n")

                            elif msg_type == "typing":
                                status = data.get("status", "")
                                if status == "start":
                                    print("⌨️  Hermes is typing...")

                            elif msg_type == "pong":
                                ts = data.get("timestamp", 0)
                                print(f"🏓 Pong received at {ts}")

                            elif msg_type == "error":
                                error = data.get("error", "Unknown error")
                                print(f"❌ Error: {error}")

                            else:
                                print(f"📨 Received: {data}")

                        except json.JSONDecodeError:
                            print(f"📨 Raw message: {message}")

                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed by server")
                except Exception as e:
                    print(f"\n❌ Error receiving: {e}")

            # Start receiving in background
            receive_task = asyncio.create_task(receive_messages())

            # Send test messages
            print("\n--- Sending Test Messages ---\n")

            # Test 1: Ping
            print("Sending ping...")
            await ws.send(json.dumps({"type": "ping"}))
            await asyncio.sleep(1)

            # Test 2: Simple chat message
            print("Sending test message...")
            await ws.send(json.dumps({
                "type": "chat",
                "content": "Hello! This is a test message from the WebSocket test client."
            }))

            # Wait for response
            await asyncio.sleep(5)

            # Cancel receiving task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

            print("\n✅ Test completed!")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Connection failed: Invalid status code {e.code}")
        if e.code == 4001:
            print("   → Invalid token. Check your WEBSOCKET_TOKEN configuration.")
        elif e.code == 1013:
            print("   → Max connections reached.")
        else:
            print(f"   → Server returned: {e.reason}")

    except ConnectionRefusedError:
        print(f"\n❌ Connection refused!")
        print(f"   → Is Hermes Gateway running with WebSocket enabled?")
        print(f"   → Check if port {port} is available.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()


async def health_check(host: str = "127.0.0.1", port: int = 8765):
    """Check health of WebSocket server."""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            url = f"http://{host}:{port}/health"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"\n✅ WebSocket server is healthy:")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Platform: {data.get('platform')}")
                    print(f"   Clients: {data.get('clients')}/{data.get('max_clients')}")
                else:
                    print(f"\n❌ Health check failed: HTTP {resp.status}")
    except ImportError:
        print("\n⚠️  aiohttp not installed. Install with: pip install aiohttp")
        print("   Skipping health check.")
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket Test Client for Hermes Agent")
    parser.add_argument("token", nargs="?", help="WebSocket authentication token")
    parser.add_argument("--host", default="127.0.0.1", help="WebSocket host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port (default: 8765)")
    parser.add_argument("--health", action="store_true", help="Only run health check")

    args = parser.parse_args()

    # Run health check first
    await health_check(args.host, args.port)

    if not args.health:
        await test_websocket(args.token, args.host, args.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
