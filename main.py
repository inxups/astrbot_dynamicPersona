from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register


@register(
    "astrbot_plugin_dynamic_persona",
    "inxups",
    "通过 /log 和 /info 指令使用插件配置页指定的人格回答单条问题",
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
        """使用插件配置页设置的 log 人格回答本条问题。"""
        async for result in self._handle_persona_request(
            event,
            config_key="log_persona_id",
            command_name="log",
        ):
            yield result

    @filter.command("info")
    async def info_persona(self, event: AstrMessageEvent):
        """使用插件配置页设置的 info 人格回答本条问题。"""
        async for result in self._handle_persona_request(
            event,
            config_key="info_persona_id",
            command_name="info",
        ):
            yield result

    @filter.event_message_type(EventMessageType.ALL)
    async def fallback_reply(self, event: AstrMessageEvent):
        """没有使用本插件指令时，回复配置的固定内容。"""
        if not event.is_at_or_wake_command:
            return
        if self._is_command_message(event):
            return

        reply = str(self.config.get("fallback_reply", "")).strip()
        if not reply:
            return

        event.should_call_llm(True)
        event.stop_event()
        yield event.plain_result(reply)

    async def _handle_persona_request(
        self,
        event: AstrMessageEvent,
        config_key: str,
        command_name: str,
    ):
        event.should_call_llm(True)

        persona = self._get_configured_persona(config_key, command_name)
        if not persona:
            self._stop_without_response(event)
            return

        prompt = self._extract_prompt(event, command_name)
        if not prompt:
            self._stop_without_response(event)
            logger.info("/%s 未附带问题，不触发模型回复。", command_name)
            return

        logger.info("使用 /%s 人格回答单条问题：%s", command_name, persona["name"])
        yield event.request_llm(
            prompt=prompt,
            system_prompt=persona["prompt"],
            contexts=persona.get("_begin_dialogs_processed", []),
        )
        self._stop_without_response(event)

    def _get_configured_persona(self, config_key: str, command_name: str):
        persona_id = str(self.config.get(config_key, "")).strip()
        if not persona_id:
            logger.warning("请先在插件配置页设置 /%s 对应的人格。", command_name)
            return None

        persona = self.context.persona_manager.get_persona_v3_by_id(persona_id)
        if not persona:
            logger.warning("未找到 /%s 对应的人格：%s", command_name, persona_id)
            return None
        return persona

    def _extract_prompt(self, event: AstrMessageEvent, command_name: str) -> str:
        prompt = event.get_message_str().strip()
        prefixes = (f"/{command_name}", command_name)
        for prefix in prefixes:
            if prompt == prefix:
                return ""
            if prompt.startswith(f"{prefix} "):
                return prompt[len(prefix) :].strip()
        return prompt

    def _stop_without_response(self, event: AstrMessageEvent) -> None:
        event.stop_event()
        event.clear_result()

    def _is_persona_command(self, event: AstrMessageEvent) -> bool:
        message = event.get_message_str().strip()
        return any(
            message == command or message.startswith(f"{command} ")
            for command in ("/log", "log", "/info", "info")
        )

    def _is_command_message(self, event: AstrMessageEvent) -> bool:
        message = event.get_message_str().strip()
        return message.startswith("/") or self._is_persona_command(event)

    async def terminate(self):
        logger.info("dynamic persona plugin terminated")
