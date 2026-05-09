#!/usr/bin/env python3
"""LLM 三国战役 — 大衍引擎 + 真实大语言模型将领.

本 demo 将 LLM agent 接入战役推演流水线:
  1. 梅花起卦 → 总卦 + 变卦
  2. 五阶段推演, 每阶段:
     - 双方 LLM agent 根据卦象制定策略
     - 子卦判定 → 阶段战果
     - 双方 LLM agent 对战果做出反应
  3. 战后 LLM agent 反思

用法:
    python examples/llm_campaign.py              # 默认: 曹操 vs 孙权(赤壁)
    python examples/llm_campaign.py 42           # 指定种子
    python examples/llm_campaign.py 42 guandu    # 官渡之战
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dayan_engine.core.types import BattleConfig, BattleResult, StageResult, Hexagram
from dayan_engine.core.battle import run_battle
from dayan_engine.narrator.template_narrator import generate as generate_narrative
from dayan_engine.agents.llm_agent import LLMAgent, create_llm_agents

# 战役五阶段
_BATTLE_STAGES = ["开战", "相持", "决战", "追击", "善后"]


def _hex_to_context(hexagram: Hexagram, stage: StageResult) -> dict:
    """将卦象和阶段结果转为 LLM 可读的上下文."""
    lines_desc = []
    for ln in hexagram.lines:
        move_mark = " ◈动" if ln.is_moving else ""
        shi_ying_mark = f" [{ln.shi_ying}]" if ln.shi_ying else ""
        lines_desc.append(
            f"  {ln.position_name}爻 {'阳' if ln.is_yang else '阴'} "
            f"({ln.six_relation}·{ln.element}·{ln.earthly_branch}支)"
            f"{shi_ying_mark}{move_mark}"
        )

    return {
        "hex_name": f"{hexagram.name}(上{hexagram.upper.name}下{hexagram.lower.name})",
        "hex_index": hexagram.index,
        "palace": hexagram.palace,
        "yongshen": stage.yongshen_status,
        "moving_line": f"{stage.moving_line}爻",
        "turning_point": stage.turning_point,
        "wuxing_relation": f"上{hexagram.upper.element}下{hexagram.lower.element}",
        "lines_detail": "\n".join(lines_desc),
    }


def _build_hex_context_for_agent(hexagram: Hexagram, stage: StageResult) -> dict:
    """构建给 LLM agent 的卦象上下文 (精简版)."""
    return {
        "hex_name": hexagram.name,
        "yongshen": stage.yongshen_status,
        "moving_line": f"第{stage.moving_line}爻动",
        "wuxing_relation": f"上卦{hexagram.upper.element}·下卦{hexagram.lower.element}",
    }


def _print_stage_header(stage_name: str, hex_name: str, moving_line: int) -> None:
    """打印阶段头部."""
    print()
    print("─" * 58)
    print(f"  ✦ {stage_name} ✦    子卦: {hex_name}    动爻: 第{moving_line}爻")
    print("─" * 58)


def _print_agent_line(name: str, text: str, icon: str = "⚔") -> None:
    """打印 agent 的行."""
    print(f"  {icon} 【{name}】: {text}")


def main() -> None:
    seed = None
    battle_name = "chibi"

    for arg in sys.argv[1:]:
        try:
            seed = int(arg)
        except ValueError:
            battle_name = arg

    # ---- 选择战役 ----
    if battle_name == "guandu":
        config = BattleConfig(
            attacker_name="曹操",
            defender_name="袁绍",
            attacker_traits={"主帅": 0.90, "军师": 0.85, "先锋": 0.75, "后勤": 0.70, "军资": 0.80, "联盟": 0.40},
            defender_traits={"主帅": 0.60, "军师": 0.70, "先锋": 0.80, "后勤": 0.90, "军资": 0.95, "联盟": 0.30},
            time_desc="建安五年冬",
            location="官渡",
            cast_nums=(5, 10, 7),  # 建安五年 + 官渡
        )
        attacker_style = "挟天子以令诸侯, 用兵大胆诡谲, 善于出奇制胜"
        defender_style = "四世三公, 兵多粮广, 但优柔寡断"

    elif battle_name == "yiling":
        config = BattleConfig(
            attacker_name="刘备",
            defender_name="陆逊",
            attacker_traits={"主帅": 0.75, "军师": 0.70, "先锋": 0.85, "后勤": 0.55, "军资": 0.50, "联盟": 0.40},
            defender_traits={"主帅": 0.85, "军师": 0.90, "先锋": 0.70, "后勤": 0.80, "军资": 0.75, "联盟": 0.60},
            time_desc="章武二年夏",
            location="猇亭",
            cast_nums=(2, 6, 15),
        )
        attacker_style = "仁义之师, 以復仇之名倾国而出, 气势汹汹"
        defender_style = "年少老成, 以逸待劳, 善于火攻"

    else:  # 赤壁 (默认)
        config = BattleConfig(
            attacker_name="曹操",
            defender_name="孙权",
            attacker_traits={"主帅": 0.90, "军师": 0.85, "先锋": 0.70, "后勤": 0.80, "军资": 0.95, "联盟": 0.30},
            defender_traits={"主帅": 0.70, "军师": 0.95, "先锋": 0.75, "后勤": 0.85, "军资": 0.90, "联盟": 0.70},
            ally_name="周瑜",
            ally_traits={"主帅": 0.85, "军师": 0.90, "先锋": 0.80, "后勤": 0.75, "军资": 0.80, "联盟": 0.85},
            time_desc="建安十三年冬",
            location="赤壁",
            cast_nums=(9, 6, 13),
        )
        attacker_style = "挟天子以令诸侯, 用兵大胆诡谲, 不习水战"
        defender_style = "据江东之险, 善于用人谋略, 水战见长"

    # ---- 创建 LLM agents ----
    attacker_agent = LLMAgent(
        config.attacker_name,
        config.attacker_traits,
        style=attacker_style,
    )
    defender_agent = LLMAgent(
        config.defender_name,
        config.defender_traits,
        style=defender_style,
    )

    ally_agent = None
    if config.ally_name:
        ally_agent = LLMAgent(
            config.ally_name,
            config.ally_traits,
            style="年少有为, 精通水战火攻, 智勇双全",
        )

    # ---- 打印开场 ----
    print()
    print("█" * 60)
    print(f"  大衍引擎 · {config.location}之战  (LLM Agent 版本)")
    print("  DaYan Engine — AI Generals Campaign")
    print("█" * 60)
    print()
    print(f"  时间: {config.time_desc}")
    print(f"  地点: {config.location}")
    print(f"  攻方: {config.attacker_name}  {'⭐' * int(config.attacker_traits['主帅'] * 10)}")
    print(f"  守方: {config.defender_name}  {'⭐' * int(config.defender_traits['军师'] * 10)}")
    if config.ally_name:
        print(f"  盟军: {config.ally_name}  {'⭐' * int(config.ally_traits['军师'] * 10)}")
    print(f"  起卦: {config.cast_nums}")
    if seed is not None:
        print(f"  种子: {seed}")
    print()

    # ========================================================
    # Phase 1: 战前 — LLM agent 制定总战略
    # ========================================================
    print("═" * 58)
    print("  【战前军议】双方将领观天象、卜卦象, 制定总体方略")
    print("═" * 58)
    print()

    # 先起卦看总卦象, 让 agent 据此制定战略
    from dayan_engine.core.meihua import cast as meihua_cast
    n1, n2, n3 = config.cast_nums
    pre_main, pre_changed, pre_moving = meihua_cast(n1, n2, n3)

    pre_context = {
        "stage": "开战前",
        "advantage": "unknown",
    }
    pre_hex = {
        "hex_name": f"{pre_main.name}(上{pre_main.upper.name}下{pre_main.lower.name})",
        "yongshen": f"总卦{pre_main.name}, 变{pre_changed.name}, 动在{pre_moving}爻",
        "moving_line": f"第{pre_moving}爻",
        "wuxing_relation": f"上{pre_main.upper.element}下{pre_main.lower.element}",
    }

    attacker_strategy = attacker_agent.get_strategy(pre_context, pre_hex)
    def_pre_context = dict(pre_context)
    def_pre_context["advantage"] = "defender"
    defender_strategy = defender_agent.get_strategy(def_pre_context, pre_hex)

    _print_agent_line(config.attacker_name, attacker_strategy, "⚔")
    _print_agent_line(config.defender_name, defender_strategy, "🛡")

    if ally_agent:
        ally_strategy = ally_agent.get_strategy(
            {"stage": "开战前", "advantage": "defender"}, pre_hex
        )
        _print_agent_line(config.ally_name, ally_strategy, "🤝")

    # ========================================================
    # Phase 2: 运行战役推演
    # ========================================================
    if seed is not None:
        random.seed(seed)

    result = run_battle(config, seed=seed)

    # ========================================================
    # Phase 3: 各阶段 LLM agent 策略 + 反应
    # ========================================================
    print()
    print("═" * 58)
    print("  【战役推演】五阶段, 步步惊心")
    print("═" * 58)

    stage_summary_lines: list[str] = []
    attacker_stage_strategies: list[str] = []
    defender_stage_strategies: list[str] = []

    for i, stage in enumerate(result.stages):
        stage_name = stage.stage_name
        hex_ctx = _build_hex_context_for_agent(stage.hexagram, stage)

        _print_stage_header(stage_name, stage.hexagram.name, stage.moving_line)

        # 双方 agent 制定阶段策略
        ctx = {
            "stage": stage_name,
            "advantage": stage.advantage,
            "yongshen_status": stage.yongshen_status,
            "turning_point": stage.turning_point,
        }

        atk_strat = attacker_agent.get_strategy(ctx, hex_ctx)
        _print_agent_line(config.attacker_name, atk_strat, "⚔")

        def_strat = defender_agent.get_strategy(ctx, hex_ctx)
        _print_agent_line(config.defender_name, def_strat, "🛡")

        # 阶段战果
        print()
        print(f"  📊 战果: 优势在{stage.advantage} | "
              f"攻方伤亡{stage.casualties_attacker:.0%} | "
              f"守方伤亡{stage.casualties_defender:.0%} | "
              f"补给{stage.supply_loss}损")
        print(f"  🔮 卦象: {stage.yongshen_status}")

        # 双方 agent 对阶段结果的反应
        if stage.advantage == "attacker":
            atk_event = {
                "type": "阶段战果",
                "desc": f"我军在{stage_name}阶段占据上风, 敌伤亡{stage.casualties_defender:.0%}, "
                        f"补给{stage.supply_loss}损。{stage.turning_point}",
            }
            def_event = {
                "type": "阶段战果",
                "desc": f"我军在{stage_name}阶段处于劣势, 伤亡{stage.casualties_defender:.0%}, "
                        f"补给{stage.supply_loss}损。{stage.turning_point}",
            }
        elif stage.advantage == "defender":
            atk_event = {
                "type": "阶段战果",
                "desc": f"我军在{stage_name}阶段受挫, 伤亡{stage.casualties_attacker:.0%}, "
                        f"补给{stage.supply_loss}损。{stage.turning_point}",
            }
            def_event = {
                "type": "阶段战果",
                "desc": f"我军在{stage_name}阶段占据上风, 敌伤亡{stage.casualties_attacker:.0%}, "
                        f"补给{stage.supply_loss}损。{stage.turning_point}",
            }
        else:
            atk_event = {
                "type": "阶段战果",
                "desc": f"我军在{stage_name}阶段与敌相持, 各伤亡{stage.casualties_attacker:.0%}和"
                        f"{stage.casualties_defender:.0%}。{stage.turning_point}",
            }
            def_event = dict(atk_event)

        print()
        atk_reaction = attacker_agent.react_to_event(atk_event, hex_ctx)
        _print_agent_line(config.attacker_name, atk_reaction, "  ↳")

        def_reaction = defender_agent.react_to_event(def_event, hex_ctx)
        _print_agent_line(config.defender_name, def_reaction, "  ↳")

        # 记录摘要
        icon = {"attacker": "◉", "defender": "◎", "even": "○"}
        summary = (
            f"  {icon[stage.advantage]} {stage_name}: "
            f"卦{stage.hexagram.name} 动{stage.moving_line}爻 | "
            f"攻亡{stage.casualties_attacker:.0%} 守亡{stage.casualties_defender:.0%}"
        )
        stage_summary_lines.append(summary)
        attacker_stage_strategies.append(atk_strat)
        defender_stage_strategies.append(def_strat)

    # ========================================================
    # Phase 4: 战后反思
    # ========================================================
    print()
    print("═" * 58)
    print("  【战后反思】成王败寇, 历史长河中的一页")
    print("═" * 58)
    print()

    if result.winner == "attacker":
        winner_name = config.attacker_name
        loser_name = config.defender_name
        atk_report = {
            "winner": config.attacker_name,
            "my_casualties": f"{result.total_casualties_attacker:.0%}",
            "enemy_casualties": f"{result.total_casualties_defender:.0%}",
            "main_hex": f"{result.main_hexagram.name}→{result.changed_hexagram.name}",
            "stages_summary": "; ".join(stage_summary_lines),
        }
        def_report = {
            "winner": config.attacker_name,
            "my_casualties": f"{result.total_casualties_defender:.0%}",
            "enemy_casualties": f"{result.total_casualties_attacker:.0%}",
            "main_hex": f"{result.main_hexagram.name}→{result.changed_hexagram.name}",
            "stages_summary": "; ".join(stage_summary_lines),
        }
    elif result.winner == "defender":
        winner_name = config.defender_name
        loser_name = config.attacker_name
        atk_report = {
            "winner": config.defender_name,
            "my_casualties": f"{result.total_casualties_attacker:.0%}",
            "enemy_casualties": f"{result.total_casualties_defender:.0%}",
            "main_hex": f"{result.main_hexagram.name}→{result.changed_hexagram.name}",
            "stages_summary": "; ".join(stage_summary_lines),
        }
        def_report = {
            "winner": config.defender_name,
            "my_casualties": f"{result.total_casualties_defender:.0%}",
            "enemy_casualties": f"{result.total_casualties_attacker:.0%}",
            "main_hex": f"{result.main_hexagram.name}→{result.changed_hexagram.name}",
            "stages_summary": "; ".join(stage_summary_lines),
        }
    else:
        winner_name = "平局"
        loser_name = "平局"
        atk_report = {
            "winner": "平局",
            "my_casualties": f"{result.total_casualties_attacker:.0%}",
            "enemy_casualties": f"{result.total_casualties_defender:.0%}",
            "main_hex": f"{result.main_hexagram.name}→{result.changed_hexagram.name}",
            "stages_summary": "; ".join(stage_summary_lines),
        }
        def_report = dict(atk_report)

    atk_reflection = attacker_agent.reflect(atk_report)
    _print_agent_line(config.attacker_name, atk_reflection, "⚔")

    def_reflection = defender_agent.reflect(def_report)
    _print_agent_line(config.defender_name, def_reflection, "🛡")

    # ========================================================
    # Phase 5: 引擎战报 (传统模板)
    # ========================================================
    print()
    print("█" * 60)
    print("  最终战果")
    print("█" * 60)
    print()

    narrative = generate_narrative(result)
    print(narrative)

    # ========================================================
    # Phase 6: 最终统计
    # ========================================================
    print()
    print("█" * 60)
    print("  LLM Agent 统计")
    print("█" * 60)
    print()
    print(f"  {config.attacker_name}: {len(attacker_agent.get_history())} 次 LLM 调用")
    print(f"  {config.defender_name}: {len(defender_agent.get_history())} 次 LLM 调用")
    print()
    print(f"  总共: {len(attacker_agent.get_history()) + len(defender_agent.get_history())} 次 LLM 调用")
    print()

    print("─" * 58)
    print(f"  🏆 胜者: {winner_name}")
    if config.ally_name:
        print(f"  🤝 盟军: {config.ally_name} ({'助守方' if config.defender_name else ''})")
    print("─" * 58)
    print()


if __name__ == "__main__":
    main()
