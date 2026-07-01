from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register(
    "astrbot_plugin_dynamic_persona",
    "inxups",
    "通过 /log 和 /info 指令切换到插件配置页指定的人格",
    "1.0.0",
)
class DynamicPersonaPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        logger.info("dynamic persona plugin initialized")

    @filter.command("log")
    async def log_persona(self, event: AstrMessageEvent):
        """切换到插件配置页设置的 log 人格。"""
        await self._switch_configured_persona(
            event,
            config_key="log_persona_id",
            command_name="log",
        )

    @filter.command("info")
    async def info_persona(self, event: AstrMessageEvent):
        """切换到插件配置页设置的 info 人格。"""
        await self._switch_configured_persona(
            event,
            config_key="info_persona_id",
            command_name="info",
        )

    async def _switch_configured_persona(
        self,
        event: AstrMessageEvent,
        config_key: str,
        command_name: str,
    ) -> None:
        persona_id = str(self.config.get(config_key, "")).strip()
        if not persona_id:
            logger.warning("请先在插件配置页设置 /%s 对应的人格。", command_name)
            return

        if not self.context.persona_manager.get_persona_v3_by_id(persona_id):
            logger.warning("未找到 /%s 对应的人格：%s", command_name, persona_id)
            return

        await self._switch_conversation_persona(event, persona_id)
        logger.info("已切换到 /%s 人格：%s", command_name, persona_id)

    async def _switch_conversation_persona(
        self,
        event: AstrMessageEvent,
        persona_id: str,
    ) -> None:
        conversation_manager = self.context.conversation_manager
        umo = event.unified_msg_origin
        conversation_id = await conversation_manager.get_curr_conversation_id(umo)
        if not conversation_id:
            await conversation_manager.new_conversation(umo, persona_id=persona_id)
        else:
            await self._update_conversation_persona(
                conversation_manager,
                umo,
                conversation_id,
                persona_id,
            )

    async def _update_conversation_persona(
        self,
        conversation_manager,
        umo: str,
        conversation_id: str,
        persona_id: str,
    ) -> None:
        if hasattr(conversation_manager, "update_conversation_persona_id"):
            await conversation_manager.update_conversation_persona_id(
                umo,
                persona_id=persona_id,
                conversation_id=conversation_id,
            )
            return

        await conversation_manager.update_conversation(
            unified_msg_origin=umo,
            conversation_id=conversation_id,
            persona_id=persona_id,
        )

    async def terminate(self):
        logger.info("dynamic persona plugin terminated")
