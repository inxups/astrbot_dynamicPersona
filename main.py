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
        yield event.plain_result(
            await self._apply_persona(
                event,
                persona_id="dynamic_persona_log",
                config_key="log_persona",
                command_name="log",
            )
        )

    @filter.command("info")
    async def info_persona(self, event: AstrMessageEvent):
        """切换到插件配置页设置的 info 人格。"""
        yield event.plain_result(
            await self._apply_persona(
                event,
                persona_id="dynamic_persona_info",
                config_key="info_persona",
                command_name="info",
            )
        )

    async def _apply_persona(
        self,
        event: AstrMessageEvent,
        persona_id: str,
        config_key: str,
        command_name: str,
    ) -> str:
        persona_prompt = str(self.config.get(config_key, "")).strip()
        if not persona_prompt:
            return f"请先在插件配置页设置 /{command_name} 对应的人格。"

        await self._upsert_persona(persona_id, persona_prompt)
        await self._switch_conversation_persona(event, persona_id)
        return f"已切换到 /{command_name} 人格。"

    async def _upsert_persona(self, persona_id: str, persona_prompt: str) -> None:
        persona_manager = self.context.persona_manager
        try:
            await persona_manager.update_persona(
                persona_id,
                system_prompt=persona_prompt,
            )
        except ValueError:
            await persona_manager.create_persona(
                persona_id,
                system_prompt=persona_prompt,
            )

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
