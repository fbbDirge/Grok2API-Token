# Grok2API Token 监控插件

一个 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 插件，用于监控 [Grok2API](https://github.com/chenyme/grok2api) Token 号池的实时状态。

## 功能

发送 `/grokstat` 指令，即可查看：

- 🔢 Token 总数
- ✅ 正常 Token 数量
- ⏳ 限流 Token 数量
- ❌ 失效 Token 数量
- 💬 Chat 剩余次数
- 🖼️ Image 剩余次数
- 🎬 Video 剩余（当前 API 不支持统计，显示 N/A）
- 📈 总调用次数

## 安装

在 AstrBot 管理面板 → 插件市场中搜索并安装，或手动将本仓库克隆到 AstrBot 的 `addons/plugins/` 目录下。
可以配合[Grok AI 助手](https://github.com/fbbDirge/Grok-AI-AstrBot-Plugin)使用,来实时监控Grok2API Token 号池状态。

## 配置

安装后，在 AstrBot 管理面板 → 插件列表 → **Grok2API Token 监控** → ⚙️ 配置 中填写以下两项：

| 配置项 | 说明 | 示例 |
|---|---|---|
| `service_url` | Grok2API 服务完整地址 | `http://your-server:8000` |
| `service_password` | 管理员密码（即 `app.app_key`） | `grok2api` |

填写后点击**保存并关闭**，然后**重载插件**使配置生效。

## 使用

在任意会话中发送：

```
/grokstat
```

回复示例：

```
📊 Grok2API Token 号池状态
──────────────────────
🔢 Token 总数：12
✅ 正常 Token：9
⏳ 限流 Token：2
❌ 失效 Token：1
──────────────────────
💬 Chat 剩余：720 次
🖼️ Image 剩余：360 次
🎬 Video 剩余：N/A
📈 总调用次数：156 次
──────────────────────
```

## 依赖

- `aiohttp`（AstrBot 内置，无需额外安装）

## 相关项目

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)
- [Grok2API](https://github.com/chenyme/grok2api)
