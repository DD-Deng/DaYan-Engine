"""追击阶段战报模板 (Pursuit Stage Templates)."""

PURSUIT_TEMPLATES: list[str] = [
    # 模板 0
    """{winner_side}乘胜追击, {loser_side}且战且退, 沿途丢弃辎重无数。
{winner}的骑兵紧追不舍, 直杀得{loser}溃不成军。
{loser}叹道: "{loser_reflection}"
此时{stage_hex_name}之变, {turning_point}。""",

    # 模板 1
    """{loser}率残部夺路而逃, 行至中途, 又遇{winner}的伏兵。
前有堵截, 后有追兵, {loser}仰天长叹。
{yongshen_desc}, 此乃天意使然。
{winner}令旗一挥: "{winner_strategy}"。""",

    # 模板 2
    """{winner}深知穷寇勿追之理, 但{loser}的残部实在太诱人。
{winner}亲率轻骑疾追三十里, 截获粮草军械不计其数。
{loser}在亲兵护卫下夺路而去, {loser_reflection}。""",

    # 模板 3
    """夜色中, {loser}收拢残兵, 缓缓撤退。
{winner}亦不深追, 鸣金收兵, 清理战场。
{loser}对左右叹道: "{loser_reflection}"
战场上一片狼藉, {supply_description}。""",
]


def get_pursuit_template(index: int, **kwargs) -> str:
    """填充追击模板."""
    tmpl = PURSUIT_TEMPLATES[index % len(PURSUIT_TEMPLATES)]
    return tmpl.format(**kwargs)
