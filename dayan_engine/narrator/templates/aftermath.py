"""善后阶段战报模板 (Aftermath Stage Templates)."""

AFTERMATH_TEMPLATES: list[str] = [
    # 模板 0
    """大战已毕, {winner}立于{location}之巅, 望着满目疮痍的战场, 感慨万千。
此役{winner}大获全胜, 斩获颇丰。{loser}经此大败, 元气大伤。
{winner}犒赏三军, 并下令: "{supply_report}"
{loser}则{loser_reflection}。""",

    # 模板 1
    """战后清点, {winner}军伤亡{winner_casualties_pct},
{loser}军伤亡{loser_casualties_pct}。
{winner}的谋士上表: "{key_lesson}"
{winner}深以为然, 传令: "{supply_report}"。""",

    # 模板 2
    """{location}一战, 震动天下。
{winner}威名远扬, {loser}则低调行事, {loser_reflection}。
百姓们口耳相传: "{folk_saying}"
史官秉笔直书, 将这一战载入青史。""",

    # 模板 3
    """尘埃落定, {winner}与{loser}各自收兵回营。
此战的教训是深刻的: {key_lesson}
{winner}抚恤死伤, 整编降卒, {supply_report}。
{loser}远远望着{location}的方向, 暗暗发誓{loser_reflection}。""",
]


def get_aftermath_template(index: int, **kwargs) -> str:
    """填充善后模板."""
    tmpl = AFTERMATH_TEMPLATES[index % len(AFTERMATH_TEMPLATES)]
    return tmpl.format(**kwargs)
