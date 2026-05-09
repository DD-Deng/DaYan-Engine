"""六亲配位 (Six Relations Assignment).

六亲: 父母 / 兄弟 / 子孙 / 妻财 / 官鬼

以卦宫五行为"我" (self_element), 比较每爻五行:
  - 生我者 → 父母
  - 我生者 → 子孙
  - 同我者 → 兄弟
  - 我克者 → 妻财
  - 克我者 → 官鬼
"""

from dayan_engine.core.wuxing import generates, overcomes
from dayan_engine.core.types import Line


def assign_six_relations(lines: list[Line], self_element: str) -> list[Line]:
    """为六爻分配六亲.

    Args:
        lines: 已配五行的六爻 (element 字段须已赋值)
        self_element: 卦宫五行 (即本卦五行, 作为"我")

    Returns:
        修改后的 lines (原地修改 + 返回引用)
    """
    for ln in lines:
        if not ln.element:
            ln.six_relation = ""
            continue
        if generates(ln.element, self_element):
            ln.six_relation = "父母"  # 爻生宫 → 父母
        elif generates(self_element, ln.element):
            ln.six_relation = "子孙"  # 宫生爻 → 子孙
        elif ln.element == self_element:
            ln.six_relation = "兄弟"  # 同五行 → 兄弟
        elif overcomes(self_element, ln.element):
            ln.six_relation = "妻财"  # 宫克爻 → 妻财
        elif overcomes(ln.element, self_element):
            ln.six_relation = "官鬼"  # 爻克宫 → 官鬼
    return lines


def get_six_relation_name(relation: str) -> str:
    """返回六亲的英文解释."""
    names = {
        "父母": "Parents (生我者)",
        "兄弟": "Brothers (同我者)",
        "子孙": "Children (我生者)",
        "妻财": "Wealth (我克者)",
        "官鬼": "Officer (克我者)",
    }
    return names.get(relation, relation)


# 六亲在战役中的角色映射
LIUQIN_BATTLE_ROLE: dict[str, str] = {
    "父母": "后勤 (补给/粮草/辎重)",
    "兄弟": "军师 (谋略/决策/计策)",
    "子孙": "先锋 (进攻/突袭/杀伤)",
    "妻财": "军资 (财力/物资/储备)",
    "官鬼": "敌将 (敌军/威胁/压力)",
}
