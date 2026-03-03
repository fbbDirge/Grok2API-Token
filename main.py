from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
import aiohttp

# 业务规则常量：Image 配额 = Chat 配额 / IMAGE_QUOTA_DIVISOR
IMAGE_QUOTA_DIVISOR = 2


class Grok2APIMonitorPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        config = config or {}
        self.service_url: str = config.get("service_url", "").rstrip("/")
        self.service_password: str = config.get("service_password", "")
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """插件初始化：创建复用的 HTTP 会话"""
        self.session = aiohttp.ClientSession()
        logger.info("Grok2API Monitor 插件已加载")

        # 安全提示：非本地 http:// 地址存在中间人窃听风险
        if self.service_url.startswith("http://"):
            from urllib.parse import urlparse
            host = urlparse(self.service_url).hostname or ""
            if host not in ("localhost", "127.0.0.1", "::1"):
                logger.warning(
                    f"Grok2API Monitor：service_url 使用了非加密的 http:// 协议（{self.service_url}），"
                    "管理员 Bearer Token 在传输过程中存在被中间人窃听的风险，建议改用 https://。"
                )

    @filter.command("grokstat")
    async def grok_status(self, event: AstrMessageEvent):
        """查询 Grok2API Token 号池状态。用法：/grokstat"""

        if not self.service_url:
            yield event.plain_result(
                "⚠️ 请先在插件配置中设置 service_url（Grok2API 服务地址）"
            )
            return

        if not self.service_password:
            yield event.plain_result(
                "⚠️ 请先在插件配置中设置 service_password（管理员密码）"
            )
            return

        api_url = f"{self.service_url}/v1/admin/tokens"
        headers = {
            "Authorization": f"Bearer {self.service_password}",
            "Accept": "application/json",
        }

        try:
            async with self.session.get(
                api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 401:
                    yield event.plain_result("❌ 认证失败，请检查插件配置中的密码是否正确")
                    return
                if resp.status != 200:
                    yield event.plain_result(
                        f"❌ 请求失败，HTTP 状态码：{resp.status}"
                    )
                    return

                data = await resp.json()

                # 数据结构校验：接口应返回 dict，而非 list 或其他类型
                if not isinstance(data, dict):
                    logger.error(
                        f"Grok2API Monitor：接口返回了非预期的数据类型 {type(data).__name__}，"
                        f"原始内容：{data}"
                    )
                    yield event.plain_result(
                        "❌ 接口返回数据格式异常（期望 JSON 对象，实际非字典类型），请检查服务端或反向代理配置"
                    )
                    return

                # 汇总所有类型的 Token 统计信息
                total = 0
                normal = 0
                rate_limited = 0
                invalid = 0
                chat_remaining = 0
                total_use_count = 0

                # 遍历所有 token 类型（ssoBasic, cookie, account, ...）
                for token_type, token_list in data.items():
                    if not isinstance(token_list, list):
                        continue
                    for token in token_list:
                        if not isinstance(token, dict):
                            continue

                        total += 1
                        status = token.get("status", "")
                        quota = token.get("quota", 0) or 0
                        use_count = token.get("use_count", 0) or 0

                        if status == "active":
                            normal += 1
                        elif status == "rate_limited":
                            rate_limited += 1
                        else:
                            invalid += 1

                        chat_remaining += quota
                        total_use_count += use_count

        except aiohttp.ClientConnectorError:
            yield event.plain_result(
                f"❌ 无法连接到服务器：{self.service_url}\n请检查插件配置中的 service_url 是否正确"
            )
            return
        except Exception as e:
            logger.error(f"Grok2API Monitor 请求异常: {e}")
            yield event.plain_result(f"❌ 请求出错：{e}")
            return

        # Image 剩余 = Chat 剩余 / IMAGE_QUOTA_DIVISOR（由管理面板业务规则决定）
        image_remaining = chat_remaining // IMAGE_QUOTA_DIVISOR

        result = (
            f"📊 Grok2API Token 号池状态\n"
            f"{'─' * 22}\n"
            f"🔢 Token 总数：{total}\n"
            f"✅ 正常 Token：{normal}\n"
            f"⏳ 限流 Token：{rate_limited}\n"
            f"❌ 失效 Token：{invalid}\n"
            f"{'─' * 22}\n"
            f"💬 Chat 剩余：{chat_remaining} 次\n"
            f"🖼️ Image 剩余：{image_remaining} 次\n"
            f"🎬 Video 剩余：N/A\n"
            f"📈 总调用次数：{total_use_count} 次\n"
            f"{'─' * 22}"
        )

        yield event.plain_result(result)

    async def terminate(self):
        """插件卸载时关闭 HTTP 会话，释放底层 TCP 连接"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("Grok2API Monitor 插件已卸载")
