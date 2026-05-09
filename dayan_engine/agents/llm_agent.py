"""LLM Agent — 接入真实大语言模型的 AI 将领.

通过 Anthropic SDK 调用 LLM, 根据卦象和战局上下文生成策略、反应和反思.
"""

import os
import time
import logging
from typing import Optional

from anthropic import Anthropic, APIConnectionError, APITimeoutError, APIStatusError

logger = logging.getLogger(__name__)

# ---- 环境变量读取 (兼容多组命名) ----


def _get_api_key() -> str:
    return (
        os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or os.environ.get("ANTHROPIC_API_KEY")
        or ""
    )


def _get_base_url() -> str:
    return (
        os.environ.get("ANTHROPIC_BASE_URL")
        or os.environ.get("ANTHROPIC_API_BASE")
        or "https://api.anthropic.com"
    )


def _get_model() -> str:
    return (
        os.environ.get("ANTHROPIC_MODEL")
        or os.environ.get("LLM_MODEL")
        or "claude-sonnet-4-6"
    )


def _extract_text(content: list) -> str:
    """从 API 返回的 content 列表中提取文本.

    处理 TextBlock(text=...), ThinkingBlock(thinking=...), 以及 raw dict.
    """
    parts = []
    for block in content:
        if isinstance(block, dict):
            t = block.get("text") or block.get("thinking")
            if t:
                parts.append(t)
        elif hasattr(block, "text"):
            t = getattr(block, "text", "")
            if t:
                parts.append(t)
        elif hasattr(block, "thinking"):
            t = getattr(block, "thinking", "")
            if t:
                parts.append(t)
    return "".join(parts)


def _build_client() -> Anthropic:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "未设置 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY 环境变量, "
            "无法创建 LLM agent"
        )
    base_url = _get_base_url().rstrip("/")
    return Anthropic(base_url=base_url + "/", api_key=api_key)


# ---- Fallback 模板 ----


_FALLBACK_STRATEGIES = [
    "{name}观{hex_name}之象, 审时度势, 决定在{stage}阶段{action}。",
    "天象{hex_name}昭示, {name}令三军{action}, 以应此兆。",
]

_FALLBACK_REACTIONS = [
    "{name}闻报, 抚剑沉吟: 此{event_desc}, 传令全军稳住阵脚。",
    "报! {name}得讯, 当即升帐点将, 应对{event_desc}之变。",
]

_FALLBACK_REFLECTIONS = [
    "{name}叹曰: 此役{result}, 然天意难违, 当{lesson}。",
    "战后, {name}收拢残兵, 感慨{result}, 暗下决心{lesson}。",
]


def _advantage_action(advantage: str) -> str:
    if advantage == "attacker":
        return "乘势猛攻"
    elif advantage == "defender":
        return "固守待援"
    else:
        return "严阵以待"


class LLMAgent:
    """接入 LLM 的 AI 将领."""

    def __init__(
        self,
        name: str,
        traits: dict[str, float],
        style: str = "",
        model: str | None = None,
    ):
        self.name = name
        self._traits = traits
        self.style = style or f"{name}的战术风格"
        self._history: list[dict] = []
        self._client = _build_client()
        self._model = model or _get_model()

    def get_traits(self) -> dict[str, float]:
        return dict(self._traits)

    # ---- 核心 LLM 调用 (重试 + fallback) ----

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 300,
        temperature: float = 0.9,
        max_retries: int = 3,
        fallback: str = "",
    ) -> str:
        """调用 LLM, 含重试和 fallback 机制."""
        last_error = ""
        for attempt in range(1, max_retries + 1):
            try:
                resp = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking=None,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = _extract_text(resp.content).strip()
                if text:
                    return text
                last_error = "empty response"
            except (APIConnectionError, APITimeoutError) as e:
                last_error = str(e)
            except APIStatusError as e:
                last_error = f"HTTP {e.status_code}: {e.message}"
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"

            if attempt < max_retries:
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "LLM call attempt %d/%d failed (%s), retrying in %ds...",
                    attempt, max_retries, last_error, wait,
                )
                time.sleep(wait)

        logger.error(
            "LLM call failed after %d attempts (%s), using fallback",
            max_retries, last_error,
        )
        return fallback if fallback else ""

    # ---- 公开接口 ----

    def get_strategy(
        self,
        context: dict,
        hexagram_context: dict | None = None,
    ) -> str:
        stage = context.get("stage", "未知阶段")
        advantage = context.get("advantage", "均势")

        prompt_parts = [
            f"你是{self.name}, 三国时代的将领。",
            f"你的战术风格: {self.style}",
        ]

        if self.name == "曹操":
            prompt_parts.append("你已统一北方, 率八十三万大军南征。")
        elif self.name == "孙权":
            prompt_parts.append("你据有江东, 联刘抗曹。")
        elif self.name == "刘备":
            prompt_parts.append("你是汉室宗亲, 以仁义聚人心。")

        prompt_parts.append("")
        prompt_parts.append(f"当前处于战役的「{stage}」阶段。")
        prompt_parts.append(f"当前战局优势在: {advantage}")

        if hexagram_context:
            prompt_parts.append("")
            prompt_parts.append("天象卦兆:")
            prompt_parts.append(f"  当前子卦: {hexagram_context.get('hex_name', '?')}")
            prompt_parts.append(f"  用神: {hexagram_context.get('yongshen', '?')}")
            prompt_parts.append(f"  动爻: {hexagram_context.get('moving_line', '?')}")
            prompt_parts.append(f"  五行: {hexagram_context.get('wuxing_relation', '?')}")

        if "turning_point" in context:
            prompt_parts.append(f"  战场转折: {context['turning_point']}")

        prompt_parts.append("")
        prompt_parts.append("请以三国演义的口吻, 用一段话(不超过100字)说出你在此阶段的军事决策和理由。")
        prompt_parts.append("不要说「作为AI」之类的话, 也不要复述任务。直接以将领的身份说话。")

        user_prompt = "\n".join(prompt_parts)
        hex_name = hexagram_context.get("hex_name", "?") if hexagram_context else "?"

        fallback = (
            f"{self.name}观{hex_name}之象, 审视{stage}阶段战局, "
            f"决定{_advantage_action(advantage)}。"
        )

        strategy = self._call_llm(
            system_prompt="你是一个精通《周易》的三国时代将领。你相信天命和卦象能指导军事决策。说话风格模仿《三国演义》的文言白话。保持简洁有力。",
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.9,
            fallback=fallback,
        )

        self._history.append({
            "type": "strategy",
            "stage": stage,
            "advantage": advantage,
            "response": strategy,
        })
        return strategy

    def react_to_event(
        self,
        event: dict[str, str],
        hexagram_context: dict | None = None,
    ) -> str:
        event_type = event.get("type", "未知")
        desc = event.get("desc", "")

        prompt_parts = [
            f"你是{self.name}, 三国时代的将领。",
            f"战术风格: {self.style}",
            "",
            f"战场上发生了一个事件: {desc}",
            f"事件类型: {event_type}",
        ]

        if hexagram_context:
            prompt_parts.append(f"当前卦象: {hexagram_context.get('hex_name', '?')}")
            prompt_parts.append(f"用神状态: {hexagram_context.get('yongshen', '?')}")

        prompt_parts.append("")
        prompt_parts.append("请以三国演义的口吻, 用一段话(不超过80字)说出你对此事件的即时反应和应对。")

        user_prompt = "\n".join(prompt_parts)
        short_desc = desc[:30] + "..." if len(desc) > 30 else desc
        fallback = f"{self.name}闻报{short_desc}, 传令全军稳住阵脚, 以待天时。"

        reaction = self._call_llm(
            system_prompt="你是一个精通《周易》的三国时代将领。说话风格模仿《三国演义》的文言白话。保持简洁有力。",
            user_prompt=user_prompt,
            max_tokens=250,
            temperature=0.9,
            fallback=fallback,
        )

        self._history.append(event)
        self._history[-1]["reaction"] = reaction
        return reaction

    def reflect(self, report: dict[str, str]) -> str:
        winner = report.get("winner", "未知")

        prompt_parts = [
            f"你是{self.name}, 三国时代的将领。",
            f"战术风格: {self.style}",
            "",
            "战役已经结束。",
            f"胜方: {winner}",
            f"我({self.name})方伤亡: {report.get('my_casualties', '?')}",
            f"敌方伤亡: {report.get('enemy_casualties', '?')}",
        ]

        if "main_hex" in report:
            prompt_parts.append(f"总卦: {report['main_hex']}")
        if "stages_summary" in report:
            prompt_parts.append(f"各阶段回顾: {report['stages_summary']}")

        prompt_parts.append("")
        prompt_parts.append("请以三国演义的口吻, 用一段话(不超过120字)做出战后总结和反思。")

        user_prompt = "\n".join(prompt_parts)

        if winner == self.name:
            fallback = f"{self.name}大胜而归, 犒赏三军, 总结经验以利再战。"
        elif winner == "平局":
            fallback = f"{self.name}收拢兵马, 此战不分胜负, 当整军经武, 再图良机。"
        else:
            fallback = f"{self.name}败而不馁, 收拢残兵, 分析教训以待来日。"

        reflection = self._call_llm(
            system_prompt="你是一个精通《周易》的三国时代将领。说话风格模仿《三国演义》的文言白话。保持简洁有力。",
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.9,
            fallback=fallback,
        )

        self._history.append({
            "type": "reflection",
            "winner": winner,
            "response": reflection,
        })
        return reflection

    def get_history(self) -> list[dict]:
        return list(self._history)


def create_llm_agents(model: str | None = None) -> dict[str, "LLMAgent"]:
    """创建三国典型将领的 LLM agent."""
    return {
        "曹操": LLMAgent("曹操", {
            "主帅": 0.90, "军师": 0.85, "先锋": 0.70,
            "后勤": 0.80, "军资": 0.95, "联盟": 0.30,
        }, style="挟天子以令诸侯, 用兵大胆诡谲, 善用奇兵", model=model),
        "孙权": LLMAgent("孙权", {
            "主帅": 0.70, "军师": 0.95, "先锋": 0.75,
            "后勤": 0.85, "军资": 0.90, "联盟": 0.70,
        }, style="据江东之险, 善于用人谋略, 水战见长", model=model),
        "刘备": LLMAgent("刘备", {
            "主帅": 0.75, "军师": 0.90, "先锋": 0.80,
            "后勤": 0.65, "军资": 0.55, "联盟": 0.95,
        }, style="仁义之师, 善于聚拢人心, 坚韧不拔", model=model),
        "诸葛亮": LLMAgent("诸葛亮", {
            "主帅": 0.80, "军师": 1.00, "先锋": 0.65,
            "后勤": 0.90, "军资": 0.75, "联盟": 0.85,
        }, style="神机妙算, 运筹帷幄之中决胜千里之外, 精通奇门遁甲", model=model),
        "周瑜": LLMAgent("周瑜", {
            "主帅": 0.85, "军师": 0.90, "先锋": 0.80,
            "后勤": 0.75, "军资": 0.80, "联盟": 0.70,
        }, style="年少有为, 精通水战火攻, 智勇双全", model=model),
        "司马懿": LLMAgent("司马懿", {
            "主帅": 0.85, "军师": 0.95, "先锋": 0.60,
            "后勤": 0.85, "军资": 0.80, "联盟": 0.40,
        }, style="老谋深算, 善于隐忍待机, 不动如山", model=model),
    }
