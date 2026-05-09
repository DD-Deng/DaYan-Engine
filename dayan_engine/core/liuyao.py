"""六爻纳甲推演 (Liuyao Najia Calculation).

基于京房纳甲法, 为六十四卦的每一爻配:
  - 天干地支 (Heavenly Stem + Earthly Branch)
  - 五行 (Five Elements)
  - 六亲 (Six Relations)
  - 世应 (Shi/Ying positions)

然后进行用神判定 (Yongshen Judgment):
  - 用神得令 + 不受克 → 吉
  - 用神受克且无救 → 凶
  - 子孙爻受克程度 → 伤亡
  - 父母/妻财爻状态 → 后勤损失
"""

from dayan_engine.core.types import Trigram, Line, Hexagram
from dayan_engine.core.wuxing import (
    element_of_trigram, element_of_branch, element_of_stem,
    generates, overcomes, generated_by, overcome_by,
    generated_element, overcome_element, relation_desc,
)
from dayan_engine.core.liuqin import assign_six_relations

# ============================================================
# 京房纳甲干支表 — 八纯卦每爻的天干地支
# ============================================================
# 格式: {trigram_index: {is_upper: [(stem, branch), ...]}}
# 每个 trigram 在下卦位置用一组干, 在上卦位置用另一组干
# 阳卦(乾坎艮震)用阳支顺行, 阴卦(巽离坤兑)用阴支逆行

_NAJIA_STEM_BRANCH: dict[int, dict[bool, list[tuple[str, str]]]] = {
    # 乾 ☰ — 金
    1: {
        False: [("甲", "子"), ("甲", "寅"), ("甲", "辰")],  # 下卦: 初/二/三爻
        True:  [("壬", "午"), ("壬", "申"), ("壬", "戌")],  # 上卦: 四/五/上爻
    },
    # 坎 ☵ — 水
    6: {
        False: [("戊", "寅"), ("戊", "辰"), ("戊", "午")],
        True:  [("戊", "申"), ("戊", "戌"), ("戊", "子")],
    },
    # 艮 ☶ — 土
    7: {
        False: [("丙", "辰"), ("丙", "午"), ("丙", "申")],
        True:  [("丙", "戌"), ("丙", "子"), ("丙", "寅")],
    },
    # 震 ☳ — 木
    4: {
        False: [("庚", "子"), ("庚", "寅"), ("庚", "辰")],
        True:  [("庚", "午"), ("庚", "申"), ("庚", "戌")],
    },
    # 巽 ☴ — 木 (阴卦)
    5: {
        False: [("辛", "丑"), ("辛", "亥"), ("辛", "酉")],
        True:  [("辛", "未"), ("辛", "巳"), ("辛", "卯")],
    },
    # 离 ☲ — 火 (阴卦)
    3: {
        False: [("己", "卯"), ("己", "丑"), ("己", "亥")],
        True:  [("己", "酉"), ("己", "未"), ("己", "巳")],
    },
    # 坤 ☷ — 土 (阴卦)
    8: {
        False: [("乙", "未"), ("乙", "巳"), ("乙", "卯")],
        True:  [("癸", "丑"), ("癸", "亥"), ("癸", "酉")],
    },
    # 兑 ☱ — 金 (阴卦)
    2: {
        False: [("丁", "巳"), ("丁", "卯"), ("丁", "丑")],
        True:  [("丁", "亥"), ("丁", "酉"), ("丁", "未")],
    },
}

# ============================================================
# 八宫卦序 — 每宫8卦, 按世应位置排列
# ============================================================
# 世爻位置: 本宫6, 一世1, 二世2, 三世3, 四世4, 五世5, 游魂4, 归魂3
_SHI_POSITIONS = [6, 1, 2, 3, 4, 5, 4, 3]

# 八宫: 乾/坎/艮/震/巽/离/坤/兑
# 每宫 = (宫名, 宫五行, [8卦的周易序索引])
_PALACE_DATA: list[tuple[str, str, list[int]]] = [
    # 宫名, 宫五行, 卦序列表(1-indexed)
    ("乾", "金", [1, 44, 33, 12, 20, 23, 35, 14]),
    ("坎", "水", [29, 60, 3, 63, 49, 55, 36, 7]),
    ("艮", "土", [52, 22, 26, 41, 38, 10, 61, 53]),
    ("震", "木", [51, 16, 40, 32, 46, 48, 28, 17]),
    ("巽", "木", [57, 9, 37, 42, 25, 21, 27, 18]),
    ("离", "火", [30, 56, 50, 64, 4, 59, 6, 13]),
    ("坤", "土", [2, 24, 19, 11, 34, 43, 5, 8]),
    ("兑", "金", [58, 47, 45, 31, 39, 15, 62, 54]),
]

# 构建: hex_index → (palace_name, palace_element, shi_position)
_HEX_PALACE_MAP: dict[int, tuple[str, str, int]] = {}
for _palace_name, _palace_element, _hex_list in _PALACE_DATA:
    for _order, _hex_idx in enumerate(_hex_list):
        _shi = _SHI_POSITIONS[_order]
        _HEX_PALACE_MAP[_hex_idx] = (_palace_name, _palace_element, _shi)


def _apply_najia(lines: list[Line], upper_idx: int, lower_idx: int) -> list[Line]:
    """为六爻配天干地支 + 五行.

    规则: 每爻的干支跟随其所在三爻组的纯卦纳甲.
      - 初/二/三爻 → 下卦的纳甲
      - 四/五/上爻 → 上卦的纳甲
    """
    for ln in lines:
        if ln.position <= 3:
            # 下卦
            trigram_idx = lower_idx
            is_upper = False
            pos_in_trigram = ln.position - 1  # 0, 1, 2
        else:
            # 上卦
            trigram_idx = upper_idx
            is_upper = True
            pos_in_trigram = ln.position - 4  # 0, 1, 2

        najia_data = _NAJIA_STEM_BRANCH.get(trigram_idx, {})
        trigram_pattern = najia_data.get(is_upper, [("?", "?"), ("?", "?"), ("?", "?")])
        stem, branch = trigram_pattern[pos_in_trigram]

        ln.heavenly_stem = stem
        ln.earthly_branch = branch
        ln.element = element_of_branch(branch)  # 五行以地支定

    return lines


def _apply_shi_ying(hexagram: Hexagram) -> Hexagram:
    """根据卦序查找宫位, 标记世应爻."""
    palace_info = _HEX_PALACE_MAP.get(hexagram.index)
    if palace_info is None:
        return hexagram

    palace_name, palace_element, shi_pos = palace_info
    hexagram.palace = palace_name
    hexagram.shi_position = shi_pos
    ying_pos = ((shi_pos - 1 + 3) % 6) + 1  # 应爻与世爻相隔三位

    for ln in hexagram.lines:
        if ln.position == shi_pos:
            ln.shi_ying = "世"
        elif ln.position == ying_pos:
            ln.shi_ying = "应"

    return hexagram


def build_hexagram(upper_idx: int, lower_idx: int) -> Hexagram:
    """构建完整的六爻纳甲卦.

    给定上下卦号, 返回包含完整 six lines (含干支/五行/六亲/世应) 的 Hexagram.

    Args:
        upper_idx: 上卦号 1-8
        lower_idx: 下卦号 1-8

    Returns:
        完整的 Hexagram (尚未标记动爻)
    """
    from dayan_engine.core.meihua import _get_hexagram_index, _get_trigram
    from dayan_engine.core.meihua import _TRIGRAM_LINES

    hex_idx, hex_name = _get_hexagram_index(upper_idx, lower_idx)

    upper_trigram = _get_trigram(upper_idx)
    lower_trigram = _get_trigram(lower_idx)

    lower_yangs = _TRIGRAM_LINES[lower_idx]
    upper_yangs = _TRIGRAM_LINES[upper_idx]

    lines = []
    for i, is_yang in enumerate(lower_yangs):
        lines.append(Line(position=i + 1, is_yang=is_yang))
    for i, is_yang in enumerate(upper_yangs):
        lines.append(Line(position=i + 4, is_yang=is_yang))

    hexagram = Hexagram(
        index=hex_idx,
        name=hex_name,
        upper=upper_trigram,
        lower=lower_trigram,
        lines=lines,
    )

    # Step 1: 纳甲 — 配干支+五行
    _apply_najia(hexagram.lines, upper_idx, lower_idx)

    # Step 2: 世应 — 查宫位
    _apply_shi_ying(hexagram)

    # Step 3: 六亲 — 以宫五行为"我"
    palace_info = _HEX_PALACE_MAP.get(hex_idx)
    if palace_info:
        palace_element = palace_info[1]
        assign_six_relations(hexagram.lines, palace_element)

    return hexagram


def apply_moving_line(hexagram: Hexagram, moving_position: int) -> Hexagram:
    """在指定位置标记动爻, 并返回变卦.

    Args:
        hexagram: 已纳甲的卦
        moving_position: 动爻位置 1-6

    Returns:
        变卦 (动爻位阴阳翻转, 其余保持不变)
    """
    for ln in hexagram.lines:
        if ln.position == moving_position:
            ln.is_moving = True
        else:
            ln.is_moving = False

    # 构建变卦 — 动爻位取反
    changed_lower_yangs = []
    changed_upper_yangs = []
    for ln in hexagram.lines:
        is_yang = not ln.is_yang if ln.position == moving_position else ln.is_yang
        if ln.position <= 3:
            changed_lower_yangs.append(is_yang)
        else:
            changed_upper_yangs.append(is_yang)

    # 反转查找八卦号 (使用 meihua 模块的查找表)
    from dayan_engine.core.meihua import _REVERSE_TRIGRAM

    new_lower = _REVERSE_TRIGRAM[tuple(changed_lower_yangs)]
    new_upper = _REVERSE_TRIGRAM[tuple(changed_upper_yangs)]

    return build_hexagram(new_upper, new_lower)


def get_yongshen_line(hexagram: Hexagram, role: str, is_attacker: bool = True) -> Line | None:
    """根据战役角色获取对应的用神爻.

    映射规则:
      - 主帅: 攻方=世爻, 守方=应爻
      - 军师: 兄弟爻
      - 先锋: 子孙爻
      - 后勤: 父母爻
      - 军资: 妻财爻
      - 敌将: 官鬼爻

    Args:
        hexagram: 已纳甲的卦
        role: 角色名 (主帅/军师/先锋/后勤/军资/敌将/谋士)
        is_attacker: 是否攻方视角 (用于决定主帅用世还是应)

    Returns:
        对应的爻, 或 None 如果找不到
    """
    if role == "主帅":
        target = "世" if is_attacker else "应"
        for ln in hexagram.lines:
            if ln.shi_ying == target:
                return ln
    elif role == "谋士":
        # 谋士 = 应爻的提醒 (使用应爻)
        for ln in hexagram.lines:
            if ln.shi_ying == "应":
                return ln
    else:
        six_relation_map = {
            "军师": "兄弟",
            "先锋": "子孙",
            "后勤": "父母",
            "军资": "妻财",
            "敌将": "官鬼",
        }
        target_relation = six_relation_map.get(role)
        if target_relation:
            for ln in hexagram.lines:
                if ln.six_relation == target_relation:
                    return ln
    return None


def judge_yongshen_status(
    hexagram: Hexagram, yongshen: Line,
    month_element: str = "", day_element: str = ""
) -> dict:
    """判定用神的综合状态.

    返回:
      {
        "status": "得令" | "受克" | "得令有生" | "受克有救" | "受克无救" | "平和",
        "score": 0.0-1.0,  得分 (1.0=极佳, 0.0=极差)
        "details": str     中文描述
      }
    """
    ys_element = yongshen.element
    details_parts = []
    score = 0.5  # 基准分

    # 1. 用神得令判定: 月建或日辰生扶用神
    has_month_support = month_element and generates(month_element, ys_element)
    has_day_support = day_element and generates(day_element, ys_element)
    month_same = month_element == ys_element
    day_same = day_element == ys_element

    if has_month_support:
        details_parts.append(f"月建{month_element}生用神{ys_element}")
        score += 0.15
    elif month_same and month_element:
        details_parts.append(f"月建{month_element}与用神比和")
        score += 0.1

    if has_day_support:
        details_parts.append(f"日辰{day_element}生用神{ys_element}")
        score += 0.1
    elif day_same and day_element:
        details_parts.append(f"日辰{day_element}与用神比和")
        score += 0.05

    # 2. 查克用神之爻
    # 克用神者: 官鬼克兄弟、兄弟克妻财、妻财克父母、父母克子孙、子孙克官鬼, etc.
    # 直接查: 哪一爻五行克用神五行
    overcoming_lines = []
    for ln in hexagram.lines:
        if overcomes(ln.element, ys_element):
            overcoming_lines.append(ln)

    if overcoming_lines:
        for ol in overcoming_lines:
            details_parts.append(
                f"{ol.position_name}爻{ol.six_relation}({ol.element})克用神"
            )
            score -= 0.12

        # 3. 查是否有救: 有通关五行 (生用神且泄克神之气)
        rescue_element = generated_by(ys_element)  # 生用神的五行
        has_rescue = any(
            ln.element == rescue_element and not overcomes(ln.element, ys_element)
            for ln in hexagram.lines
        )

        # 或者有克制克神之爻
        has_counter = False
        for ol in overcoming_lines:
            counter_element = overcome_by(ol.element)
            for ln in hexagram.lines:
                if ln.element == counter_element:
                    has_counter = True
                    break

        if has_rescue:
            details_parts.append(f"有{rescue_element}通关相救")
            score += 0.1
        if has_counter:
            details_parts.append("有制克神之爻相救")
            score += 0.05

        if not has_rescue and not has_counter:
            details_parts.append("无救")

    # 4. 动爻的额外影响
    for ln in hexagram.lines:
        if ln.is_moving:
            if generates(ln.element, ys_element):
                details_parts.append(f"动爻{ln.position_name}生用神")
                score += 0.1
            elif overcomes(ln.element, ys_element):
                details_parts.append(f"动爻{ln.position_name}克用神")
                score -= 0.1

    # 5. 分类
    score = max(0.0, min(1.0, score))
    if score >= 0.65:
        status = "得令有生" if score >= 0.75 else "得令"
    elif score >= 0.4:
        status = "平和"
    elif score >= 0.25:
        status = "受克有救"
    else:
        status = "受克无救"

    return {
        "status": status,
        "score": score,
        "details": "; ".join(details_parts) if details_parts else "用神平和无冲无生",
    }


def judge_casualties(hexagram: Hexagram, yongshen_score: float) -> tuple[float, float]:
    """根据子孙爻受克程度推算攻守双方伤亡比例.

    子孙爻 = 先锋/杀伤力
      子孙受克严重 → 攻方伤亡高
      子孙爻旺相 → 守方伤亡高

    Returns:
        (attacker_casualties, defender_casualties) 0.0-1.0
    """
    # 找子孙爻
    zisun_lines = [ln for ln in hexagram.lines if ln.six_relation == "子孙"]
    if not zisun_lines:
        # 无子孙爻 → 中等伤亡
        base_attacker = 0.3
        base_defender = 0.3
    else:
        # 子孙爻的平均"受克程度"
        total_penalty = 0
        for zs in zisun_lines:
            for ln in hexagram.lines:
                if overcomes(ln.element, zs.element):
                    total_penalty += 1
                elif generates(ln.element, zs.element):
                    total_penalty -= 0.5

        # 子孙受克 → 攻方伤亡高
        if total_penalty > 0:
            base_attacker = 0.3 + 0.1 * total_penalty
            base_defender = 0.15
        else:
            base_attacker = 0.2
            base_defender = 0.3 - 0.05 * total_penalty

    # 用神分数影响
    base_attacker *= (1.2 - yongshen_score)
    base_defender *= yongshen_score

    return (
        max(0.05, min(0.8, base_attacker)),
        max(0.05, min(0.8, base_defender)),
    )


def judge_supply(hexagram: Hexagram) -> str:
    """根据父母爻和妻财爻判定后勤损失程度.

    Returns:
        "轻" / "中" / "重" / "无"
    """
    fumu_lines = [ln for ln in hexagram.lines if ln.six_relation == "父母"]
    qicai_lines = [ln for ln in hexagram.lines if ln.six_relation == "妻财"]

    damage = 0
    for fl in fumu_lines:
        for ln in hexagram.lines:
            if overcomes(ln.element, fl.element):
                damage += 1
    for ql in qicai_lines:
        for ln in hexagram.lines:
            if overcomes(ln.element, ql.element):
                damage += 1

    if damage == 0:
        return "无"
    elif damage <= 1:
        return "轻"
    elif damage <= 3:
        return "中"
    else:
        return "重"


def get_turning_point(hexagram: Hexagram) -> str:
    """根据动爻位置和六亲生成关键转折点描述."""
    for ln in hexagram.lines:
        if ln.is_moving:
            pos = ln.position_name
            relation = ln.six_relation
            shi_ying = ln.shi_ying or ""

            if shi_ying == "世":
                return f"{pos}爻(世爻){relation}动, 主帅亲自介入, 战场态势剧变"
            elif shi_ying == "应":
                return f"{pos}爻(应爻){relation}动, 敌军突发变故, 战局逆转"
            elif relation == "官鬼":
                return f"{pos}爻官鬼动, 敌军发动致命一击"
            elif relation == "子孙":
                return f"{pos}爻子孙动, 先锋突袭得手, 打破僵局"
            elif relation == "妻财":
                return f"{pos}爻妻财动, 后勤补给出现变故"
            elif relation == "父母":
                return f"{pos}爻父母动, 天时变化影响战局"
            else:
                return f"{pos}爻{relation}动, 战场出现意外转折"

    return "无动爻, 战局平稳推进, 无戏剧性转折"
