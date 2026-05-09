"""梅花易数起卦 (Plum Blossom Divination).

输入任意三个正整数, 输出本卦 + 变卦 + 动爻位置.

算法:
  1. 上卦数 = num1 mod 8, 0 视为 8 (坤)
  2. 下卦数 = num2 mod 8, 0 视为 8 (坤)
  3. 动爻数 = (num1 + num2 + num3) mod 6, 0 视为 6
  4. 变卦 = 本卦在动爻位取反 (阳变阴, 阴变阳)

八卦序: 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8

64 卦查找表: (上卦号, 下卦号) → (卦序, 卦名)
"""

from dayan_engine.core.types import Trigram, Hexagram, Line
from dayan_engine.core.wuxing import element_of_trigram, TRIGRAM_NAMES

# --- 八卦爻象 (自下而上) ---
# 乾☰ 兑☱ 离☲ 震☳ 巽☴ 坎☵ 艮☶ 坤☷
_TRIGRAM_LINES: dict[int, list[bool]] = {
    1: [True, True, True],    # 乾 ☰
    2: [True, True, False],   # 兑 ☱
    3: [True, False, True],   # 离 ☲
    4: [False, False, True],  # 震 ☳
    5: [False, True, True],   # 巽 ☴
    6: [False, True, False],  # 坎 ☵
    7: [True, False, False],  # 艮 ☶
    8: [False, False, False], # 坤 ☷
}

# --- 三爻阴阳 → 八卦号反查表 ---
_REVERSE_TRIGRAM: dict[tuple[bool, bool, bool], int] = {
    (True, True, True): 1,
    (True, True, False): 2,
    (True, False, True): 3,
    (False, False, True): 4,
    (False, True, True): 5,
    (False, True, False): 6,
    (True, False, False): 7,
    (False, False, False): 8,
}

# --- 64卦名表, 按通行本周易序 ---
# (上卦, 下卦, 卦名)
_HEXAGRAM_TABLE: list[tuple[int, int, str]] = [
    (1, 1, "乾为天"),   # 1
    (8, 8, "坤为地"),   # 2
    (6, 4, "水雷屯"),   # 3
    (7, 6, "山水蒙"),   # 4
    (6, 1, "水天需"),   # 5
    (1, 6, "天水讼"),   # 6
    (8, 6, "地水师"),   # 7
    (6, 8, "水地比"),   # 8
    (5, 1, "风天小畜"), # 9
    (1, 2, "天泽履"),   # 10
    (8, 1, "地天泰"),   # 11
    (1, 8, "天地否"),   # 12
    (1, 3, "天火同人"), # 13
    (3, 1, "火天大有"), # 14
    (8, 7, "地山谦"),   # 15
    (4, 8, "雷地豫"),   # 16
    (2, 4, "泽雷随"),   # 17
    (7, 5, "山风蛊"),   # 18
    (8, 2, "地泽临"),   # 19
    (5, 8, "风地观"),   # 20
    (3, 4, "火雷噬嗑"), # 21
    (7, 3, "山火贲"),   # 22
    (7, 8, "山地剥"),   # 23
    (8, 4, "地雷复"),   # 24
    (1, 4, "天雷无妄"), # 25
    (7, 1, "山天大畜"), # 26
    (7, 4, "山雷颐"),   # 27
    (2, 5, "泽风大过"), # 28
    (6, 6, "坎为水"),   # 29
    (3, 3, "离为火"),   # 30
    (2, 7, "泽山咸"),   # 31
    (4, 5, "雷风恒"),   # 32
    (1, 7, "天山遁"),   # 33
    (4, 1, "雷天大壮"), # 34
    (3, 8, "火地晋"),   # 35
    (8, 3, "地火明夷"), # 36
    (5, 3, "风火家人"), # 37
    (3, 2, "火泽睽"),   # 38
    (6, 7, "水山蹇"),   # 39
    (4, 6, "雷水解"),   # 40
    (7, 2, "山泽损"),   # 41
    (5, 4, "风雷益"),   # 42
    (2, 1, "泽天夬"),   # 43
    (1, 5, "天风姤"),   # 44
    (2, 8, "泽地萃"),   # 45
    (8, 5, "地风升"),   # 46
    (2, 6, "泽水困"),   # 47
    (6, 5, "水风井"),   # 48
    (2, 3, "泽火革"),   # 49
    (3, 5, "火风鼎"),   # 50
    (4, 4, "震为雷"),   # 51
    (7, 7, "艮为山"),   # 52
    (5, 7, "风山渐"),   # 53
    (4, 2, "雷泽归妹"), # 54
    (4, 3, "雷火丰"),   # 55
    (3, 7, "火山旅"),   # 56
    (5, 5, "巽为风"),   # 57
    (2, 2, "兑为泽"),   # 58
    (5, 6, "风水涣"),   # 59
    (6, 2, "水泽节"),   # 60
    (5, 2, "风泽中孚"), # 61
    (4, 7, "雷山小过"), # 62
    (6, 3, "水火既济"), # 63
    (3, 6, "火水未济"), # 64
]

# 构建查询索引: (upper_idx, lower_idx) → (hex_index, name)
_HEXAGRAM_INDEX: dict[tuple[int, int], tuple[int, str]] = {}
for _idx, (u, l, n) in enumerate(_HEXAGRAM_TABLE, start=1):
    _HEXAGRAM_INDEX[(u, l)] = (_idx, n)


def _get_trigram(index: int) -> Trigram:
    """根据先天八卦数(1-8)创建 Trigrams."""
    return Trigram(
        index=index,
        name=TRIGRAM_NAMES.get(index, "?"),
        element=element_of_trigram(index),
    )


def _get_hexagram_index(upper_idx: int, lower_idx: int) -> tuple[int, str]:
    """根据上下卦号查找卦序和卦名.

    Returns:
        (卦序 1-64, 卦名)
    Raises:
        ValueError: 上下卦组合不在64卦表中
    """
    result = _HEXAGRAM_INDEX.get((upper_idx, lower_idx))
    if result is None:
        raise ValueError(f"无效的上下卦组合: 上={upper_idx}, 下={lower_idx}")
    return result


def cast(num1: int, num2: int, num3: int) -> tuple[Hexagram, Hexagram, int]:
    """梅花易数起卦.

    Args:
        num1: 第一个数字 → 上卦
        num2: 第二个数字 → 下卦
        num3: 第三个数字 → 参与动爻计算

    Returns:
        (本卦 hexagram, 变卦 hexagram, 动爻位 1-6)
        hexagram 中仅填充上下卦和索引/名称, 六爻未纳甲.
    """
    # 1. 计算上下卦号 (0→8)
    upper_idx = num1 % 8
    if upper_idx == 0:
        upper_idx = 8
    lower_idx = num2 % 8
    if lower_idx == 0:
        lower_idx = 8

    # 2. 计算动爻 (0→6)
    moving_line = (num1 + num2 + num3) % 6
    if moving_line == 0:
        moving_line = 6

    # 3. 查找本卦
    hex_idx, hex_name = _get_hexagram_index(upper_idx, lower_idx)

    upper_trigram = _get_trigram(upper_idx)
    lower_trigram = _get_trigram(lower_idx)

    # 4. 创建本卦的六爻 (仅填充基本结构, 阴阳由上下卦推导)
    lower_yangs = _TRIGRAM_LINES[lower_idx]   # 下卦三爻 (初/二/三)
    upper_yangs = _TRIGRAM_LINES[upper_idx]   # 上卦三爻 (四/五/上)

    lines = []
    # 初爻至三爻 = 下卦
    for i, is_yang in enumerate(lower_yangs):
        lines.append(Line(position=i + 1, is_yang=is_yang))
    # 四爻至上爻 = 上卦
    for i, is_yang in enumerate(upper_yangs):
        lines.append(Line(position=i + 4, is_yang=is_yang))

    original = Hexagram(
        index=hex_idx,
        name=hex_name,
        upper=upper_trigram,
        lower=lower_trigram,
        lines=lines,
    )

    # 5. 创建变卦 — 动爻位取反
    changed_lines = []
    for ln in lines:
        if ln.position == moving_line:
            changed_lines.append(Line(
                position=ln.position,
                is_yang=not ln.is_yang,
                is_moving=True,
            ))
        else:
            changed_lines.append(Line(
                position=ln.position,
                is_yang=ln.is_yang,
            ))

    # 变卦的上下卦号可能变了
    changed_lower_yangs = [ln.is_yang for ln in changed_lines[:3]]
    changed_upper_yangs = [ln.is_yang for ln in changed_lines[3:]]

    new_lower_idx = _REVERSE_TRIGRAM[tuple(changed_lower_yangs)]
    new_upper_idx = _REVERSE_TRIGRAM[tuple(changed_upper_yangs)]

    new_hex_idx, new_hex_name = _get_hexagram_index(new_upper_idx, new_lower_idx)

    changed = Hexagram(
        index=new_hex_idx,
        name=new_hex_name,
        upper=_get_trigram(new_upper_idx),
        lower=_get_trigram(new_lower_idx),
        lines=changed_lines,
    )

    return original, changed, moving_line
