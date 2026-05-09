"""最终战报总结模板 (Final Report Templates)."""

FINAL_REPORT_TEMPLATES: list[str] = [
    # 模板 0: 史诗风格
    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  《三国演义》· {time}
  大衍战报 · {attacker} 对 {defender}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【总卦】
{main_hex_name} ({main_hex_index}/64)
上{main_upper}下{main_lower}, 属{main_palace}宫, 五行属{main_element}。
{main_hex_desc}

【变卦】
{changed_hex_name} ({changed_hex_index}/64)
上{changed_upper}下{changed_lower}, 属{changed_palace}宫。
动爻在{main_moving_line_name}位, {moving_desc}。

【世应】
世爻在{shi_pos}位({shi_relation}), 应爻在{ying_pos}位({ying_relation})。
{shi_ying_desc}

【战役推演】
{stage_summaries}

【最终战果】
胜方: {winner_name}
攻方({attacker})伤亡率: {attacker_casualties_pct}
守方({defender})伤亡率: {defender_casualties_pct}
关键转折: {key_turning_point}

【后记】
{epilogue}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  大衍引擎 v0.1.0 · MIT 开源
  用《周易》推演战局 · 以卦象洞见胜负
━━━━━━━━━━━━━━━━━━━━━━━━━━━━""",

    # 模板 1: 简洁风格
    """══════════════════════════════
  大衍战报: {attacker} vs {defender}
  {time} · {location}
══════════════════════════════

▶ 起卦: {main_hex_name} → {changed_hex_name}
　 动爻: {main_moving_line_name}位
　 {moving_desc}

▶ 推演过程:
{stage_summaries}

▶ 战果: {winner_name} 胜
　 攻方伤亡 {attacker_casualties_pct}, 守方伤亡 {defender_casualties_pct}
　 关键转折: {key_turning_point}

▶ {epilogue}

══════════════════════════════""",
]


def get_final_report_template(index: int, **kwargs) -> str:
    """填充最终战报模板."""
    tmpl = FINAL_REPORT_TEMPLATES[index % len(FINAL_REPORT_TEMPLATES)]
    return tmpl.format(**kwargs)
