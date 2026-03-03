from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp


@register(
    "grok2api_monitor",
    "Fan",
    "Grok2API Token 号池状态监控插件",
    "1.0.0",
    "https://github.com/Soulter/helloworld",
)
class Grok2APIMonitorPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        config = config or {}
        self.service_url: str = config.get("service_url", "").rstrip("/")
        self.service_password: str = config.get("service_password", "")

    async def initialize(self):
        """插件初始化"""
        logger.info("Grok2API Monitor 插件已加载")

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
            async with aiohttp.ClientSession() as session:
                async with session.get(
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

                    data: dict = await resp.json()

        except aiohttp.ClientConnectorError:
            yield event.plain_result(
                f"❌ 无法连接到服务器：{self.service_url}\n请检查插件配置中的 service_url 是否正确"
            )
            return
        except Exception as e:
            logger.error(f"Grok2API Monitor 请求异常: {e}")
            yield event.plain_result(f"❌ 请求出错：{e}")
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

        # Image 剩余 = Chat 剩余 / 2（根据管理面板逻辑）
        image_remaining = chat_remaining // 2

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
        """插件卸载时调用"""
        logger.info("Grok2API Monitor 插件已卸载")
