"""Mock Agent — 雏形阶段用固定数据代替 LLM agent.

以后接真实 LLM agent 时只替换实现, 接口保持不变.
"""

from typing import Optional


class MockAgent:
    """模拟的 AI 将领 agent.

    雏形阶段返回预设的 trait 值, 以后替换为 LLM 调用.
    """

    def __init__(self, name: str, traits: dict[str, float], style: str = ""):
        """初始化 mock agent.

        Args:
            name: 将领名
            traits: 能力特质值, 如 {"主帅": 0.9, "军师": 0.7, ...}
                   值域 0.0-1.0
            style: 战术风格描述 (可选)
        """
        self.name = name
        self._traits = traits
        self.style = style or f"{name}的战术风格"
        self._history: list[dict] = []

    def get_traits(self) -> dict[str, float]:
        """返回将领能力特质."""
        return dict(self._traits)

    def get_strategy(self, context: dict[str, str]) -> str:
        """根据战局上下文返回策略描述.

        Args:
            context: {"stage": 阶段名, "advantage": 当前优势方, ...}

        Returns:
            策略描述文本 (雏形用模板, 以后接 LLM)
        """
        stage = context.get("stage", "未知阶段")
        advantage = context.get("advantage", "均势")

        if advantage == "attacker":
            return f"{self.name}趁势猛攻, 力图在{stage}阶段扩大战果"
        elif advantage == "defender":
            return f"{self.name}固守待援, 在{stage}阶段以逸待劳"
        else:
            return f"{self.name}审时度势, 在{stage}阶段寻找战机"

    def react_to_event(self, event: dict[str, str]) -> str:
        """对战场事件的反应.

        Args:
            event: {"type": 事件类型, "desc": 事件描述}

        Returns:
            反应描述
        """
        event_type = event.get("type", "未知")
        desc = event.get("desc", "")
        self._history.append(event)
        return f"{self.name}面对'{desc}', 迅速调整部署应对{event_type}"

    def reflect(self, report: dict[str, str]) -> str:
        """战后反思.

        Args:
            report: {"winner": 胜方, "casualties": 伤亡, ...}

        Returns:
            反思文本
        """
        winner = report.get("winner", "未知")
        if winner == self.name:
            return f"{self.name}大胜而归, 犒赏三军, 总结经验以利再战"
        else:
            return f"{self.name}败而不馁, 收拢残兵, 分析教训以待来日"


def create_three_kingdoms_agents() -> dict[str, MockAgent]:
    """创建三国典型将领的预置 mock agent.

    Returns:
        {"曹操": MockAgent, "孙权": MockAgent, "刘备": MockAgent, ...}
    """
    return {
        "曹操": MockAgent("曹操", {
            "主帅": 0.90, "军师": 0.85, "先锋": 0.70,
            "后勤": 0.80, "军资": 0.95, "联盟": 0.30,
        }, style="挟天子以令诸侯, 用兵大胆诡谲"),
        "孙权": MockAgent("孙权", {
            "主帅": 0.70, "军师": 0.95, "先锋": 0.75,
            "后勤": 0.85, "军资": 0.90, "联盟": 0.70,
        }, style="据江东之险, 善于用人谋略"),
        "刘备": MockAgent("刘备", {
            "主帅": 0.75, "军师": 0.90, "先锋": 0.80,
            "后勤": 0.65, "军资": 0.55, "联盟": 0.95,
        }, style="仁义之师, 善于聚拢人心"),
        "诸葛亮": MockAgent("诸葛亮", {
            "主帅": 0.80, "军师": 1.00, "先锋": 0.65,
            "后勤": 0.90, "军资": 0.75, "联盟": 0.85,
        }, style="神机妙算, 运筹帷幄之中决胜千里之外"),
        "周瑜": MockAgent("周瑜", {
            "主帅": 0.85, "军师": 0.90, "先锋": 0.80,
            "后勤": 0.75, "军资": 0.80, "联盟": 0.70,
        }, style="年少有为, 精通水战火攻"),
        "司马懿": MockAgent("司马懿", {
            "主帅": 0.85, "军师": 0.95, "先锋": 0.60,
            "后勤": 0.85, "军资": 0.80, "联盟": 0.40,
        }, style="老谋深算, 善于隐忍待机"),
    }
