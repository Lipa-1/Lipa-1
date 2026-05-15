# Hermes Agent WebSocket 平台适配器 - 架构与实现文档

## 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)2.1 整体架构2.2 组件关系
3. [新增功能](#3-新增功能)
4. [实现细节](#4-实现细节)4.1 WebSocket 适配器实现4.2 配置系统集成4.3 网关集成
5. [测试验证](#5-测试验证)
6. [使用指南](#6-使用指南)
7. [文件变更清单](#7-文件变更清单)

* * *

## 1. 项目概述

### 1.1 背景

本项目将 WebSocket 代理功能集成到 Hermes Agent Gateway 中，允许 Web 客户端（如浏览器、自定义应用）通过 WebSocket 协议与 Hermes Agent 进行实时交互。

### 1.2 目标

* 提供基于 WebSocket 的实时消息通道
* 支持 token 认证机制
* 集成到现有的 Hermes Gateway 平台适配器系统
* 支持跨平台消息路由

### 1.3 方案选择

采用 **方案3：集成到 Hermes Gateway**，将 WebSocket 作为一个新的平台适配器实现。

* * *

## 2. 架构设计

### 2.1 整体架构

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        Hermes Agent Gateway                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
    │  │  Platform    │    │  Platform    │    │   WebSocket         │  │
    │  │  Adapters    │    │  Adapters    │    │   Platform Adapter   │  │
    │  │  (Telegram,  │    │  (Discord,   │    │                      │  │
    │  │   Slack,     │    │   WhatsApp,  │    │  ┌────────────────┐ │  │
    │  │   ...)       │    │   ...)       │    │  │ WebSocket       │ │  │
    │  └──────┬───────┘    └──────┬───────┘    │  │   Server        │ │  │
    │         │                   │             │  │  (aiohttp)     │ │  │
    │         └───────────────────┴─────────────┼──┤                 │ │  │
    │                                           │  │  ┌────────────┐ │ │  │
    │                                           │  │  │ Client     │ │ │  │
    │                                           │  │  │ Manager    │ │ │  │
    │                                           │  │  └────────────┘ │ │  │
    │                                           │  └────────────────┘ │  │
    │                                           └──────────────────────┘  │
    │                              │                                     │
    │                              ▼                                     │
    │                   ┌─────────────────┐                              │
    │                   │  Message Router │                              │
    │                   │  (统一消息路由)   │                              │
    │                   └────────┬────────┘                              │
    │                            ▼                                       │
    │                   ┌─────────────────┐                              │
    │                   │  Session Store  │                              │
    │                   └─────────────────┘                              │
    └─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        Web Clients                                  │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
    │  │  Browser     │  │  Custom App  │  │  IoT Device  │             │
    │  │  WebSocket   │  │  WebSocket   │  │  WebSocket   │             │
    │  └──────────────┘  └──────────────┘  └──────────────┘             │
    └─────────────────────────────────────────────────────────────────────┘

### 2.2 组件关系

| 组件  | 职责  | 状态  |
| --- | --- | --- |
| **WebSocketAdapter** | 平台适配器主类，管理 WebSocket 服务器生命周期 | 新增  |
| **WebSocketClient** | 客户端连接封装，处理单个连接的状态管理 | 新增  |
| **GatewayRunner** | 网关运行器，协调所有平台适配器 | 修改  |
| **GatewayConfig** | 网关配置系统，管理平台配置 | 修改  |
| **Platform** | 平台枚举，定义支持的消息平台 | 修改  |

### 2.3 数据流

    客户端消息 → WebSocket Server → WebSocketAdapter → Message Router → Agent
                                                               │
    Agent 响应 ←───────────────────────────────────────────────┘

* * *

## 3. 新增功能

### 3.1 核心功能

| 功能  | 描述  | 实现方式 |
| --- | --- | --- |
| **WebSocket 服务器** | 基于 aiohttp 的 WebSocket 服务 | `aiohttp.web.Application` |
| **Token 认证** | 连接时的 token 验证机制 | URL 参数 + 环境变量 |
| **客户端管理** | 连接状态、消息计数、速率限制 | `WebSocketClient` 类 |
| **消息路由** | 集成到 Gateway 消息路由系统 | `BasePlatformAdapter` 继承 |
| **健康检查** | HTTP 健康检查端点 | `/health` 路由 |
| **跨平台消息投递** | 支持向其他平台发送消息 | `gateway_runner` 引用 |

### 3.2 安全特性

| 特性  | 实现  |
| --- | --- |
| Token 认证 | 所有连接必须携带有效 token |
| 速率限制 | 每分钟最多 60 条消息 |
| 连接限制 | 最大并发连接数可配置 |
| 连接超时 | 5 分钟无活动自动断开 |

### 3.3 配置参数

| 参数  | 类型  | 默认值 | 说明  |
| --- | --- | --- | --- |
| `host` | string | `127.0.0.1` | 绑定地址 |
| `port` | int | `8765` | 绑定端口 |
| `token` | string | -   | 认证令牌 |
| `max_connections` | int | `10` | 最大连接数 |

* * *

## 4. 实现细节

### 4.1 WebSocket 适配器实现

**文件**: `gateway/platforms/websocket.py`

#### 4.1.1 类结构

    class WebSocketAdapter(BasePlatformAdapter):
        """WebSocket 平台适配器"""
    
        def __init__(self, config: PlatformConfig):
            # 初始化配置参数
            self._host = config.extra.get("host", "127.0.0.1")
            self._port = config.extra.get("port", 8765)
            self._token = config.extra.get("token", "") or os.getenv("WEBSOCKET_TOKEN", "")
            self._max_connections = config.extra.get("max_connections", 10)
            self._clients: Dict[str, WebSocketClient] = {}

#### 4.1.2 核心方法

| 方法  | 功能  |
| --- | --- |
| `connect()` | 启动 WebSocket 服务器 |
| `disconnect()` | 停止服务器并断开所有连接 |
| `send()` | 向指定客户端发送消息 |
| `get_chat_info()` | 获取会话信息 |
| `_handle_websocket()` | WebSocket 连接处理协程 |
| `_authenticate()` | Token 认证验证 |

#### 4.1.3 客户端管理

    class WebSocketClient:
        """单个 WebSocket 客户端的状态管理"""
        client_id: str          # 客户端唯一标识
        connected_at: float     # 连接时间
        last_message_at: float  # 最后消息时间
        authenticated: bool     # 认证状态
        rate_counts: list       # 速率限制计数器

### 4.2 配置系统集成

**文件**: `gateway/config.py`

#### 4.2.1 Platform 枚举扩展

    class Platform(Enum):
        # ... 其他平台 ...
        WEBSOCKET = "websocket"  # 新增

#### 4.2.2 连接检查器

    _PLATFORM_CONNECTED_CHECKERS = {
        # ... 其他平台 ...
        Platform.WEBSOCKET: lambda cfg: bool(
            cfg.token or cfg.extra.get("token") or os.getenv("WEBSOCKET_TOKEN")
        ),
    }

### 4.3 网关集成

**文件**: `gateway/run.py`

#### 4.3.1 适配器工厂

    def _create_adapter(self, platform: Platform, config: Any) -> Optional[BasePlatformAdapter]:
        # ... 其他平台处理 ...
        elif platform == Platform.WEBSOCKET:
            from gateway.platforms.websocket import WebSocketAdapter, check_websocket_requirements
            if not check_websocket_requirements():
                logger.warning("WebSocket: aiohttp not installed")
                return None
            adapter = WebSocketAdapter(config)
            adapter.gateway_runner = self  # 用于跨平台消息投递
            return adapter

#### 4.3.2 授权配置

    # WebSocket 平台免授权（通过 token 自行认证）
    if source.platform in {Platform.HOMEASSISTANT, Platform.WEBHOOK, Platform.WEBSOCKET}:
        return True
    
    # 授权映射
    platform_env_map = {
        # ... 其他平台 ...
        Platform.WEBSOCKET: "WEBSOCKET_ALLOWED_USERS",
    }

* * *

## 5. 测试验证

### 5.1 测试脚本

**文件**: `test_websocket.py`

#### 测试功能

| 测试项 | 说明  |
| --- | --- |
| 健康检查 | 验证服务器是否正常运行 |
| 连接测试 | 建立 WebSocket 连接 |
| 认证测试 | 验证 token 认证 |
| 消息测试 | 发送/接收消息 |

#### 测试结果

    ✅ WebSocket server is healthy:
       Status: ok
       Platform: websocket
       Clients: 0/10
    
    ✅ Connected successfully!
    📡 Connection confirmed
       Client ID: 1778810189796-1
       Authenticated: True
    
    🏓 Pong received
    🤖 Hermes response received
    ✅ Test completed!

### 5.2 验证方法

    # 启动网关
    $env:HERMES_HOME="C:\Users\a\Desktop\hermes-agent-main\hermes-agent-main\.hermes"
    $env:WEBSOCKET_TOKEN="my-secret-token"
    python -c "from hermes_cli.gateway import run_gateway; run_gateway(verbose=2)"
    
    # 测试连接
    python test_websocket.py my-secret-token

* * *

## 6. 使用指南

### 6.1 配置方式

**配置文件**: `.hermes/config.yaml`

    platforms:
      websocket:
        enabled: true
        extra:
          host: "127.0.0.1"
          port: 8765
          token: "my-secret-token"
          max_connections: 10

**环境变量方式**:

    $env:WEBSOCKET_TOKEN="my-secret-token"

### 6.2 连接方式

**WebSocket URL**:

    ws://127.0.0.1:8765/ws?token=my-secret-token

**健康检查**:

    http://127.0.0.1:8765/health

### 6.3 消息格式

**客户端发送**:

    {
      "type": "message",
      "content": "Hello, Hermes!",
      "session_id": "optional-session-id"
    }

**服务端响应**:

    {
      "type": "response",
      "content": "Hi there!",
      "session_id": "session-id"
    }

* * *

## 7. 文件变更清单

### 7.1 新增文件

| 文件  | 路径  | 说明  |
| --- | --- | --- |
| `websocket.py` | `gateway/platforms/websocket.py` | WebSocket 平台适配器 |
| `test_websocket.py` | `test_websocket.py` | 测试脚本 |
| `config.yaml` | `.hermes/config.yaml` | 测试配置文件 |
| `WEBSOCKET_PLATFORM_DOCUMENTATION.md` | `WEBSOCKET_PLATFORM_DOCUMENTATION.md` | 本文档 |

### 7.2 修改文件

| 文件  | 路径  | 修改内容 |
| --- | --- | --- |
| `config.py` | `gateway/config.py` | 添加 Platform.WEBSOCKET 枚举 |
| `config.py` | `gateway/config.py` | 添加连接检查器 |
| `run.py` | `gateway/run.py` | 添加适配器工厂逻辑 |
| `run.py` | `gateway/run.py` | 添加授权配置 |

### 7.3 技术栈

| 技术  | 版本  | 用途  |
| --- | --- | --- |
| Python | 3.11+ | 主语言 |
| aiohttp | ^3.9 | WebSocket 服务器 |
| Hermes Agent | -   | 基础框架 |

* * *

## 附录：启动命令汇总

    # 开发环境启动
    cd C:\Users\a\Desktop\hermes-agent-main\hermes-agent-main
    $env:HERMES_HOME="C:\Users\a\Desktop\hermes-agent-main\hermes-agent-main\.hermes"
    python -c "from hermes_cli.gateway import run_gateway; run_gateway(verbose=2)"
    
    # 生产环境启动（使用默认 HERMES_HOME）
    python -c "from hermes_cli.gateway import run_gateway; run_gateway()"
    
    # 测试 WebSocket 连接
    python test_websocket.py <your-token>

* * *

**文档版本**: v1.0**创建日期**: 2026-05-15**作者**: Hermes Agent Development Team
