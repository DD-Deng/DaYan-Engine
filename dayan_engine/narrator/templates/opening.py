"""开战阶段战报模板 (Opening Stage Templates)."""

OPENING_TEMPLATES: list[str] = [
    # 模板 0: 攻势开局
    """却说{attacker}亲率大军, 浩浩荡荡杀奔{location}而来。
时值{time}, {attacker}帐下谋士献计: "{strategy_attacker}"。
阵前{attacker}令旗一挥, 先锋部队如潮水般涌向{defender}营寨。""",

    # 模板 1: 对峙开局
    """{time}, {attacker}与{defender}两军对峙于{location}。
{attacker}厉声道: "{strategy_attacker}"
{defender}冷笑道: "{strategy_defender}"
两军列阵, 旌旗蔽日, 战鼓如雷。""",

    # 模板 2: 突袭开局
    """{defender}方在{location}安营未稳, 忽听得寨外喊声大震。
原来{attacker}早已定下{strategy_attacker}之策, 趁夜突袭。
{defender}仓促应战, {strategy_defender}。""",

    # 模板 3: 水战开局
    """大江之上, 战船如云。{attacker}的水军顺流而下, 直逼{location}。
{defender}登高远望, 见敌船连绵不绝, 对左右道: "{strategy_defender}"
江风猎猎, 一场水战一触即发。""",
]


def get_opening_template(index: int, attacker: str, defender: str,
                         time: str, location: str,
                         strategy_attacker: str, strategy_defender: str) -> str:
    """填充开战模板."""
    tmpl = OPENING_TEMPLATES[index % len(OPENING_TEMPLATES)]
    return tmpl.format(
        attacker=attacker, defender=defender,
        time=time, location=location,
        strategy_attacker=strategy_attacker,
        strategy_defender=strategy_defender,
    )
