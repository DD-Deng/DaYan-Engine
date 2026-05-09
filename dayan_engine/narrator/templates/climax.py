"""决战阶段战报模板 (Climax Stage Templates)."""

CLIMAX_TEMPLATES: list[str] = [
    # 模板 0: 火攻
    """是日东南风大起, {attacker}军中忽见火起。
原来{defender}早已定下火攻之计! 火借风势, 风助火威,
{attacker}的战船顷刻间化为一片火海。
{yongshen_desc}, 此乃{turning_point}!""",

    # 模板 1: 正面决战
    """{attacker}与{defender}终于迎来了决战时刻。
金鼓齐鸣, 两军精锐尽出。{attacker}亲执长槊冲入敌阵,
{defender}亦拔剑迎战。杀声震天, 血流成河。
{hex_name}卦有{stage_hex_name}之变, {turning_point}。""",

    # 模板 2: 计谋破敌
    """{defender}设下伏兵, 待{attacker}进入埋伏圈。
一声炮响, 伏兵四起。{attacker}大惊, 急令后军变前军撤退。
然而{defender}早已算到此着, {strategy_defender}。
{yongshen_desc}, 胜负在此一举!""",

    # 模板 3: 突袭决胜
    """夜半时分, {defender}的敢死队摸入{attacker}大营。
{attacker}从梦中惊醒, 披甲上马应战。
火光之中, 两军混战, {defender}亲自擂鼓助威。
{stage_hex_name}显示{turning_point}。""",
]


def get_climax_template(index: int, **kwargs) -> str:
    """填充决战模板."""
    tmpl = CLIMAX_TEMPLATES[index % len(CLIMAX_TEMPLATES)]
    return tmpl.format(**kwargs)
