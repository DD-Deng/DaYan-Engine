"""模板战报生成器 (Template-based Battle Narrator).

根据卦象、用神状态、五行生克关系, 选择匹配的战报模板,
填充阶段变量, 生成三国演义风格的中文战报。

模板变量:
  {attacker} {defender} {time} {location}
  {hex_name} {hex_index} {main_hex_name}
  {stage_hex_name} {moving_line_pos} {moving_desc}
  {yongshen_status} {advantage_desc}
  {attacker_casualties} {defender_casualties}
  {supply_loss} {turning_point} {winner}
"""

import random
from dayan_engine.core.types import BattleResult, StageResult, BattleConfig, Hexagram
from dayan_engine.core.wuxing import relation_desc

from dayan_engine.narrator.templates.opening import get_opening_template
from dayan_engine.narrator.templates.stalemate import get_stalemate_template
from dayan_engine.narrator.templates.climax import get_climax_template
from dayan_engine.narrator.templates.pursuit import get_pursuit_template
from dayan_engine.narrator.templates.aftermath import get_aftermath_template
from dayan_engine.narrator.templates.final_report import get_final_report_template


def _get_position_name(pos: int) -> str:
    """爻位 → 中文名."""
    names = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}
    return names.get(pos, "?")


def _format_casualty_desc(rate: float, name: str) -> str:
    """伤亡比例 → 中文描述."""
    if rate >= 0.5:
        return f"{name}军伤亡惨重, 折损过半"
    elif rate >= 0.3:
        return f"{name}军损失不小, 折损三成有余"
    elif rate >= 0.15:
        return f"{name}军略有伤亡"
    else:
        return f"{name}军损伤轻微"


def _generate_opening_narrative(stage: StageResult, config: BattleConfig) -> str:
    """生成开战阶段叙述."""
    idx = random.randint(0, 3)
    sub_hex = stage.hexagram

    attacker_agent = config.attacker_name
    defender_agent = config.defender_name

    strategy_a = f"以{stage.hexagram.name}之象, 布阵{stage.advantage}之势"
    strategy_d = f"据{stage.hexagram.name}之卦, 以守为攻"

    return get_opening_template(
        idx, attacker_agent, defender_agent,
        config.time_desc, config.location,
        strategy_a, strategy_d
    )


def _generate_stalemate_narrative(stage: StageResult, config: BattleConfig) -> str:
    """生成相持阶段叙述."""
    idx = random.randint(0, 3)
    sub_hex = stage.hexagram

    if stage.advantage == "attacker":
        side_with = config.attacker_name
        other = config.defender_name
    elif stage.advantage == "defender":
        side_with = config.defender_name
        other = config.attacker_name
    else:
        side_with = "双方"
        other = "对方"

    kwargs = {
        "attacker": config.attacker_name,
        "defender": config.defender_name,
        "location": config.location,
        "stage_hex_name": sub_hex.name,
        "moving_desc": stage.turning_point,
        "side_with_advantage": side_with,
        "other_side": other,
        "attacker_casualty_desc": _format_casualty_desc(
            stage.casualties_attacker, config.attacker_name
        ),
        "defender_casualty_desc": _format_casualty_desc(
            stage.casualties_defender, config.defender_name
        ),
        "supply_report": f"粮草{stage.supply_loss}损",
        "strategy_attacker": f"以{sub_hex.name}之象调整部署",
        "strategy_defender": f"据{sub_hex.name}之卦稳固防线",
        "key_omen": f"{sub_hex.name}主{sub_hex.lower.name}上{sub_hex.upper.name}, {stage.yongshen_status}",
    }
    return get_stalemate_template(idx, **kwargs)


def _generate_climax_narrative(stage: StageResult, config: BattleConfig) -> str:
    """生成决战阶段叙述."""
    idx = random.randint(0, 3)
    sub_hex = stage.hexagram

    kwargs = {
        "attacker": config.attacker_name,
        "defender": config.defender_name,
        "location": config.location,
        "hex_name": sub_hex.name,
        "stage_hex_name": f"{sub_hex.name}({sub_hex.upper.name}上{sub_hex.lower.name}下)",
        "yongshen_desc": stage.yongshen_status,
        "turning_point": stage.turning_point,
        "strategy_defender": f"{config.defender_name}据{sub_hex.name}之示, 定下决胜之策",
    }
    return get_climax_template(idx, **kwargs)


def _generate_pursuit_narrative(stage: StageResult, config: BattleConfig,
                                 winner: str) -> str:
    """生成追击阶段叙述."""
    idx = random.randint(0, 3)
    sub_hex = stage.hexagram

    if winner == "attacker":
        winner_side = config.attacker_name
        loser_side = config.defender_name
        winner_strategy = f"乘{sub_hex.name}之势, 穷追猛打"
    elif winner == "defender":
        winner_side = config.defender_name
        loser_side = config.attacker_name
        winner_strategy = f"据{sub_hex.name}之卦, 扩大战果"
    else:
        winner_side = config.attacker_name
        loser_side = config.defender_name
        winner_strategy = "鸣金收兵"

    kwargs = {
        "winner_side": winner_side,
        "loser_side": loser_side,
        "winner": winner_side,
        "loser": loser_side,
        "winner_strategy": winner_strategy,
        "loser_reflection": f"此乃天意, 非战之罪也",
        "stage_hex_name": sub_hex.name,
        "turning_point": stage.turning_point,
        "yongshen_desc": stage.yongshen_status,
        "supply_description": f"辎重{stage.supply_loss}损, 军资{'匮乏' if stage.supply_loss == '重' else '尚可'}",
    }
    return get_pursuit_template(idx, **kwargs)


def _generate_aftermath_narrative(stage: StageResult, config: BattleConfig,
                                   winner: str, total_atk_cas: float,
                                   total_def_cas: float) -> str:
    """生成善后阶段叙述."""
    idx = random.randint(0, 3)

    if winner == "attacker":
        winner_name = config.attacker_name
        loser_name = config.defender_name
        winner_cas = total_atk_cas
        loser_cas = total_def_cas
    elif winner == "defender":
        winner_name = config.defender_name
        loser_name = config.attacker_name
        winner_cas = total_def_cas
        loser_cas = total_atk_cas
    else:
        winner_name = "双方"
        loser_name = "各自"
        winner_cas = (total_atk_cas + total_def_cas) / 2
        loser_cas = (total_atk_cas + total_def_cas) / 2

    kwargs = {
        "winner": winner_name,
        "loser": loser_name,
        "location": config.location,
        "winner_casualties_pct": f"{winner_cas:.0%}",
        "loser_casualties_pct": f"{loser_cas:.0%}",
        "supply_report": f"清点{stage.supply_loss}损之辎重, 抚恤伤亡将士",
        "loser_reflection": f"卧薪尝胆, 以图再起",
        "key_lesson": "胜负不但在力, 亦在天时人和",
        "folk_saying": f"{stage.hexagram.name}之验, 果不虚也",
    }
    return get_aftermath_template(idx, **kwargs)


def generate(battle_result: BattleResult) -> str:
    """生成完整战报.

    Args:
        battle_result: 完整战役结果 (含所有阶段)

    Returns:
        战报全文 (纯文本)
    """
    config = battle_result.config
    main_hex = battle_result.main_hexagram
    changed_hex = battle_result.changed_hexagram

    # --- 生成各阶段叙述 ---
    stage_narratives: list[str] = []
    for stage in battle_result.stages:
        stage_name = stage.stage_name

        if stage_name == "开战":
            text = _generate_opening_narrative(stage, config)
        elif stage_name == "相持":
            text = _generate_stalemate_narrative(stage, config)
        elif stage_name == "决战":
            text = _generate_climax_narrative(stage, config)
        elif stage_name == "追击":
            text = _generate_pursuit_narrative(stage, config, battle_result.winner)
        elif stage_name == "善后":
            text = _generate_aftermath_narrative(
                stage, config, battle_result.winner,
                battle_result.total_casualties_attacker,
                battle_result.total_casualties_defender,
            )
        else:
            text = f"【{stage_name}】{stage.turning_point}"

        stage_narratives.append(f"【{stage_name}】\n{text}")

    # --- 生成总卦描述 ---
    main_moving = 0
    for ln in main_hex.lines:
        if ln.is_moving:
            main_moving = ln.position
            break

    main_hex_desc = _describe_hexagram(main_hex)

    moving_desc = f"动在{_get_position_name(main_moving)}, 主{main_hex.name}之变, 此爻变动引发全局转折"

    shi_pos = main_hex.shi_position
    ying_pos = ((shi_pos - 1 + 3) % 6) + 1

    shi_ln = None
    ying_ln = None
    for ln in main_hex.lines:
        if ln.shi_ying == "世":
            shi_ln = ln
        elif ln.shi_ying == "应":
            ying_ln = ln

    shi_relation = shi_ln.six_relation if shi_ln else "?"
    ying_relation = ying_ln.six_relation if ying_ln else "?"
    shi_ying_desc = f"世爻{shi_relation}持世, 应爻{ying_relation}临应"

    # --- 生成阶段摘要 ---
    stage_summary_lines = []
    for stage in battle_result.stages:
        advantage_icon = {"attacker": "◉", "defender": "◎", "even": "○"}
        icon = advantage_icon.get(stage.advantage, "○")

        summary = (
            f"  {icon} {stage.stage_name} | "
            f"卦: {stage.hexagram.name} | "
            f"动爻: {_get_position_name(stage.moving_line)} | "
            f"攻亡{stage.casualties_attacker:.0%} 守亡{stage.casualties_defender:.0%} | "
            f"后勤{stage.supply_loss}损"
        )
        stage_summary_lines.append(summary)
    stage_summaries = "\n".join(stage_summary_lines)

    # --- 最终战果 ---
    if battle_result.winner == "attacker":
        winner_name = f"{config.attacker_name}(攻方)"
    elif battle_result.winner == "defender":
        winner_name = f"{config.defender_name}(守方)"
    else:
        winner_name = "平局"

    # 找关键转折 (取决战阶段的)
    key_tp = "无"
    for stage in battle_result.stages:
        if stage.stage_name == "决战":
            key_tp = stage.turning_point
            break

    # --- 后记 ---
    epilogue = _generate_epilogue(battle_result)

    # --- 组装最终报告 ---
    report = get_final_report_template(
        0,  # 使用史诗风格模板
        time=config.time_desc,
        attacker=config.attacker_name,
        defender=config.defender_name,
        main_hex_name=main_hex.name,
        main_hex_index=main_hex.index,
        main_upper=main_hex.upper.name,
        main_lower=main_hex.lower.name,
        main_palace=main_hex.palace,
        main_element=main_hex.lower.element,
        main_hex_desc=main_hex_desc,
        changed_hex_name=changed_hex.name,
        changed_hex_index=changed_hex.index,
        changed_upper=changed_hex.upper.name,
        changed_lower=changed_hex.lower.name,
        changed_palace=changed_hex.palace,
        main_moving_line_name=_get_position_name(main_moving),
        moving_desc=moving_desc,
        shi_pos=shi_pos,
        shi_relation=shi_relation,
        ying_pos=ying_pos,
        ying_relation=ying_relation,
        shi_ying_desc=shi_ying_desc,
        stage_summaries=stage_summaries,
        winner_name=winner_name,
        attacker_casualties_pct=f"{battle_result.total_casualties_attacker:.0%}",
        defender_casualties_pct=f"{battle_result.total_casualties_defender:.0%}",
        key_turning_point=key_tp,
        epilogue=epilogue,
        location=config.location,
    )

    return report


def _describe_hexagram(hexagram: Hexagram) -> str:
    """生成卦象的简要文字描述."""
    parts = []

    # 卦的组成
    parts.append(f"上{hexagram.upper.name}下{hexagram.lower.name}")

    # 爻象简述
    line_chars = "".join(
        "⚊" if ln.is_yang else "⚋" for ln in hexagram.lines
    )
    parts.append(f"爻象: {line_chars} (自下而上)")

    # 世应
    for ln in hexagram.lines:
        if ln.shi_ying:
            parts.append(f"{ln.position}爻({ln.six_relation}·{ln.earthly_branch})为{ln.shi_ying}")

    return ", ".join(parts)


def _generate_epilogue(result: BattleResult) -> str:
    """生成后记 — 对战役的总结评价."""
    config = result.config
    main_hex = result.main_hexagram

    lines = []

    if result.winner == "attacker":
        lines.append(f"此役{config.attacker_name}大获全胜, 威震天下。")
        lines.append(f"{config.defender_name}虽败, 然根基未毁。")
    elif result.winner == "defender":
        lines.append(f"此役{config.defender_name}以弱胜强, 名垂青史。")
        lines.append(f"{config.attacker_name}大败而归, 锐气大挫。")
    else:
        lines.append(f"此役双方皆损伤惨重, 胜负未分。")
        lines.append(f"或许, 真正的赢家是{main_hex.name}所昭示的天命。")

    lines.append(f"大衍引擎以{main_hex.name}之象推演: ")
    lines.append(f"  {main_hex.lower.name}({main_hex.lower.element})为内, "
                 f"{main_hex.upper.name}({main_hex.upper.element})为外。")
    lines.append(f"  五行{main_hex.lower.element}主内, {main_hex.upper.element}主外, "
                 f"{relation_desc(main_hex.lower.element, main_hex.upper.element)}。")

    if main_hex.palace:
        lines.append(f"  宫属{main_hex.palace}, 世在{main_hex.shi_position}爻。")

    return "\n".join(lines)
