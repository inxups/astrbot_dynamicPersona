# astrbot_plugin_dynamic_persona

通过固定指令切换当前会话的人格，并在插件配置页选择对应的人格。

## 使用方式

1. 先在 AstrBot 的人格管理中创建好要使用的人格。
2. 在插件配置页选择：
   - `log_persona_id`：`/log` 要切换到的人格
   - `info_persona_id`：`/info` 要切换到的人格
3. 在聊天中发送 `/log 问题` 或 `/info 问题`，插件会先把当前会话切换到对应人格，再让模型继续回答后面的 `问题`。

插件自身不会向群聊发送回复，执行结果只会写入 AstrBot 日志。
