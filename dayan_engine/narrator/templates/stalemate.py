"""相持阶段战报模板 (Stalemate Stage Templates)."""

STALEMATE_TEMPLATES: list[str] = [
    # 模板 0
    """两军交战已逾数日, 各有损伤, 胜负未分。
{attacker}见久攻不下, 心生一计: {strategy_attacker}。
{defender}亦非等闲之辈, {strategy_defender}。
双方你来我往, 战局陷入胶着。""",

    # 模板 1
    """{stage_hex_name}之象, {moving_desc}。
战场上{side_with_advantage}稍占上风, 但{other_side}阵脚未乱。
{attacker}的先锋部队{attacker_casualty_desc},
{defender}的防线{defender_casualty_desc}。""",

    # 模板 2
    """双方在{location}已对峙多日, 军中粮草渐少。
探马来报: "{supply_report}"
{attacker}闻报, 召众将商议。帐下军师进言: "{strategy_attacker}"
{defender}亦在对面营中, 灯下观图, 谋定{strategy_defender}。""",

    # 模板 3
    """月照{location}, 两军阵前篝火点点。
{attacker}巡营时激励士卒, {defender}则加固营防以待明日。
{stage_hex_name}卦象显示, 此时{key_omen}。
双方谋士都在计算下一着棋该如何走。""",
]


def get_stalemate_template(index: int, **kwargs) -> str:
    """填充相持模板."""
    tmpl = STALEMATE_TEMPLATES[index % len(STALEMATE_TEMPLATES)]
    return tmpl.format(**kwargs)
