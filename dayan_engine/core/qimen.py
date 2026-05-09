"""奇门遁甲排盘与战局判定 (Qimen Dunjia Plate Arrangement).

奇门遁甲是中国古代最高层次的预测学之一, 号称"帝王之学".
本模块实现奇门遁甲的时家排盘算法, 并将其接入战役判定引擎.

排盘流程:
  1. 节气 → 阳遁/阴遁
  2. 三元(上/中/下元) → 局数 (1-9)
  3. 排地盘: 三奇六仪按阳顺阴逆入九宫
  4. 排天盘: 值符星随时干
  5. 排人盘: 八门随时支
  6. 排神盘: 八神阳顺阴逆
  7. 综合吉凶判定

参考: 时家奇门, 置闰法
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from dayan_engine.core.wuxing import generates, overcomes, FIVE_ELEMENTS

# ============================================================
# 基础数据
# ============================================================

# 九宫 (Luoshu magic square): 戴九履一, 左三右七, 二四为肩, 六八为足
# 宫位 → (方位, 五行, 八卦)
JIU_GONG: dict[int, dict] = {
    1: {"direction": "北", "element": "水", "trigram": "坎", "name": "坎一宫"},
    2: {"direction": "西南", "element": "土", "trigram": "坤", "name": "坤二宫"},
    3: {"direction": "东", "element": "木", "trigram": "震", "name": "震三宫"},
    4: {"direction": "东南", "element": "木", "trigram": "巽", "name": "巽四宫"},
    5: {"direction": "中", "element": "土", "trigram": None, "name": "中五宫"},
    6: {"direction": "西北", "element": "金", "trigram": "乾", "name": "乾六宫"},
    7: {"direction": "西", "element": "金", "trigram": "兑", "name": "兑七宫"},
    8: {"direction": "东北", "element": "土", "trigram": "艮", "name": "艮八宫"},
    9: {"direction": "南", "element": "火", "trigram": "离", "name": "离九宫"},
}

# 八门: 休生伤杜景死惊开
BA_MEN = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]

BA_MEN_ATTRS: dict[str, dict] = {
    "休门": {"ji_xiong": "吉", "element": "水", "desc": "休养生息, 宜守不宜攻"},
    "生门": {"ji_xiong": "吉", "element": "土", "desc": "生机勃勃, 宜进攻发展"},
    "伤门": {"ji_xiong": "凶", "element": "木", "desc": "损伤破坏, 主战斗伤亡"},
    "杜门": {"ji_xiong": "平", "element": "木", "desc": "堵塞不通, 宜防守待援"},
    "景门": {"ji_xiong": "平", "element": "火", "desc": "光明景象, 宜谋划策略"},
    "死门": {"ji_xiong": "凶", "element": "土", "desc": "死亡终结, 大凶之地"},
    "惊门": {"ji_xiong": "凶", "element": "金", "desc": "惊恐不定, 主突袭溃败"},
    "开门": {"ji_xiong": "吉", "element": "金", "desc": "开创通达, 宜发动总攻"},
}

# 九星: 天蓬/天芮/天冲/天辅/天禽/天心/天柱/天任/天英
JIU_XING = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]

JIU_XING_ATTRS: dict[str, dict] = {
    "天蓬": {"element": "水", "ji_xiong": "凶", "desc": "大盗之星, 宜偷袭不宜正战"},
    "天芮": {"element": "土", "ji_xiong": "凶", "desc": "病符之星, 主疾病后勤问题"},
    "天冲": {"element": "木", "ji_xiong": "平", "desc": "冲锋之星, 宜快速决战"},
    "天辅": {"element": "木", "ji_xiong": "吉", "desc": "辅佐之星, 宜军师谋划"},
    "天禽": {"element": "土", "ji_xiong": "吉", "desc": "中正之星, 百事皆宜"},
    "天心": {"element": "金", "ji_xiong": "吉", "desc": "策划之星, 宜统帅决策"},
    "天柱": {"element": "金", "ji_xiong": "凶", "desc": "破军之星, 宜破坏敌阵"},
    "天任": {"element": "土", "ji_xiong": "吉", "desc": "担当之星, 宜固守阵地"},
    "天英": {"element": "火", "ji_xiong": "平", "desc": "火光之星, 宜火攻奇袭"},
}

# 八神: 值符/螣蛇/太阴/六合/白虎/玄武/九地/九天
BA_SHEN = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

BA_SHEN_ATTRS: dict[str, dict] = {
    "值符": {"ji_xiong": "吉", "desc": "天乙贵人, 百恶消散"},
    "螣蛇": {"ji_xiong": "凶", "desc": "虚诈惊恐, 诡谲多变"},
    "太阴": {"ji_xiong": "吉", "desc": "阴佑暗助, 宜密谋伏击"},
    "六合": {"ji_xiong": "吉", "desc": "和合联盟, 宜合纵连横"},
    "白虎": {"ji_xiong": "凶", "desc": "凶杀猛将, 宜猛攻强袭"},
    "玄武": {"ji_xiong": "凶", "desc": "盗贼水患, 宜水战偷袭"},
    "九地": {"ji_xiong": "吉", "desc": "坚牢稳固, 宜深沟高垒"},
    "九天": {"ji_xiong": "吉", "desc": "扬兵天际, 宜主动出击"},
}

# 十天干
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 十二地支
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 三奇六仪: 乙丙丁为三奇, 戊己庚辛壬癸为六仪
# 六仪隐甲: 甲子戊, 甲戌己, 甲申庚, 甲午辛, 甲辰壬, 甲寅癸
LIU_YI: dict[str, str] = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
}

# 符头 → 局数基数
_FUTOU_HIDDEN: dict[str, str] = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
}

# 二十四节气 (近似日期范围: month, day_start, day_end)
# 阳遁从冬至到夏至, 阴遁从夏至到冬至
SOLAR_TERMS: list[tuple[str, int, int, int]] = [
    # (名称, 月, 开始日, 结束日)
    ("冬至", 12, 21, 23),   # 0  — 阳遁开始
    ("小寒", 1, 5, 7),
    ("大寒", 1, 20, 23),
    ("立春", 2, 3, 5),
    ("雨水", 2, 18, 20),
    ("惊蛰", 3, 5, 7),
    ("春分", 3, 20, 22),
    ("清明", 4, 4, 6),
    ("谷雨", 4, 19, 21),
    ("立夏", 5, 5, 7),
    ("小满", 5, 20, 22),
    ("芒种", 6, 5, 7),
    ("夏至", 6, 21, 23),    # 12 — 阴遁开始
    ("小暑", 7, 6, 8),
    ("大暑", 7, 22, 24),
    ("立秋", 8, 7, 9),
    ("处暑", 8, 22, 24),
    ("白露", 9, 7, 9),
    ("秋分", 9, 22, 24),
    ("寒露", 10, 8, 10),
    ("霜降", 10, 23, 25),
    ("立冬", 11, 7, 9),
    ("小雪", 11, 22, 24),
    ("大雪", 12, 6, 8),
]

# 洛书九宫顺序 (阳遁顺排宫位)
_LUOSHU_ORDER_YANG = [1, 2, 3, 4, 5, 6, 7, 8, 9]
# 阴遁逆排宫位
_LUOSHU_ORDER_YIN = [9, 8, 7, 6, 5, 4, 3, 2, 1]

# 八门原始宫位: 休1 生8 伤3 杜4 景9 死2 惊7 开6
_BA_MEN_ORIGINAL_PALACE: dict[str, int] = {
    "休门": 1, "生门": 8, "伤门": 3, "杜门": 4,
    "景门": 9, "死门": 2, "惊门": 7, "开门": 6,
}

# 九星原始宫位: 蓬1 芮2 冲3 辅4 禽5 心6 柱7 任8 英9
_JIU_XING_ORIGINAL_PALACE: dict[str, int] = {
    "天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4,
    "天禽": 5, "天心": 6, "天柱": 7, "天任": 8, "天英": 9,
}

# ============================================================
# Dataclasses
# ============================================================

@dataclass
class QimenPalaceData:
    """单宫奇门数据."""
    palace_index: int
    direction: str
    element: str
    di_pan_stem: str = ""       # 地盘天干
    tian_pan_stem: str = ""     # 天盘天干
    ren_pan_door: str = ""      # 人盘八门
    shen_pan_spirit: str = ""   # 神盘八神
    tian_pan_star: str = ""     # 天盘九星
    ji_xiong: str = ""          # 综合吉凶


@dataclass
class QimenPlate:
    """奇门遁甲排盘结果."""
    datetime_str: str
    dun_type: str               # "阳遁" / "阴遁"
    ju_number: int              # 局数 1-9
    yuan: str                   # 上元/中元/下元
    solar_term: str             # 节气
    palaces: dict[int, QimenPalaceData] = field(default_factory=dict)


# ============================================================
# 排盘算法
# ============================================================

def _get_solar_term_index(month: int, day: int) -> int:
    """根据月日近似确定节气索引 (0-23)."""
    for i, (name, m, d_start, d_end) in enumerate(SOLAR_TERMS):
        if month == m and d_start <= day <= d_end:
            return i
    # 未精确匹配时按月份估算
    if month in (12, 1, 2):
        # 冬季
        return 0 if month == 12 and day >= 21 else (1 if month == 1 else 0)
    elif month in (3, 4, 5):
        return 3 + (month - 3) * 2
    elif month in (6, 7, 8):
        return 12 + (month - 6) * 2
    else:
        return 18 + (month - 9) * 2


def _determine_dun_type(solar_term_index: int) -> str:
    """阳遁/阴遁判定: 冬至(0)→夏至(12)为阳遁, 夏至→冬至为阴遁."""
    # 阳遁: 冬至到芒种 (0-11), 阴遁: 夏至到大雪 (12-23)
    return "阳遁" if 0 <= solar_term_index < 12 else "阴遁"


def _determine_ju_and_yuan(
    year: int, month: int, day: int, hour: int, dun_type: str
) -> tuple[int, str]:
    """确定局数和三元 (上元/中元/下元).

    三元规则: 以甲子为符头, 五日为一元, 十五日为一气.
    简化: 根据日干支的甲子周期推算.
    """
    # 用日数简化推算三元
    # 以冬至为基准日, 计算距冬至的天数
    # 简化: 直接用 day + month*30 + hour/24 来推算

    # 三日一元, 五日为一候, 十五日一气
    day_of_season = (month * 30 + day) % 15
    if day_of_season < 5:
        yuan = "上元"
    elif day_of_season < 10:
        yuan = "中元"
    else:
        yuan = "下元"

    # 局数: 以年月日时之和推算
    # 简化算法: 用三元 + 时辰地支 推算局数
    total = year + month + day + hour
    ju = (total % 9)
    if ju == 0:
        ju = 9

    return ju, yuan


def _get_hour_stem_branch(hour: int) -> tuple[str, str]:
    """时辰 → 天干地支 (简化)."""
    branch_index = (hour + 1) // 2 % 12
    # 日干以甲日起算, 五鼠遁
    # 简化: 使用固定映射
    stem_index = (hour // 2) % 10
    return TIAN_GAN[stem_index], DI_ZHI[branch_index]


def _find_futou(day_stem_idx: int) -> tuple[str, str]:
    """根据日干找符头."""
    # 符头是甲子/甲戌/甲申/甲午/甲辰/甲寅
    futou_list = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
    idx = (day_stem_idx // 2) % 6
    futou = futou_list[idx]
    return futou, _FUTOU_HIDDEN[futou]


def _arrange_di_pan(ju_number: int, dun_type: str) -> dict[int, str]:
    """排地盘: 三奇六仪按局数 + 阳顺阴逆排入九宫."""
    # 六仪: 戊己庚辛壬癸, 三奇: 乙丙丁
    # 戊为起点, 按局数落宫
    stems_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    order = _LUOSHU_ORDER_YANG if dun_type == "阳遁" else _LUOSHU_ORDER_YIN

    # 戊从局数宫位开始
    start_idx = order.index(ju_number)
    di_pan: dict[int, str] = {}
    for i, stem in enumerate(stems_order):
        palace = order[(start_idx + i) % 9]
        di_pan[palace] = stem
    return di_pan


def arrange_qimen_plate(
    year: int, month: int, day: int, hour: int, minute: int = 0
) -> QimenPlate:
    """奇门遁甲时家排盘.

    Args:
        year: 年 (如 208)
        month: 月 1-12
        day: 日 1-31
        hour: 时 0-23
        minute: 分 0-59

    Returns:
        QimenPlate 完整排盘结果
    """
    # 1. 节气 → 遁别
    solar_idx = _get_solar_term_index(month, day)
    dun_type = _determine_dun_type(solar_idx)
    term_name = SOLAR_TERMS[solar_idx][0] if 0 <= solar_idx < 24 else "?"

    # 2. 三元 → 局数
    ju_number, yuan = _determine_ju_and_yuan(year, month, day, hour, dun_type)

    # 3. 排地盘
    di_pan = _arrange_di_pan(ju_number, dun_type)

    # 4. 时辰干支
    hour_stem, hour_branch = _get_hour_stem_branch(hour)
    hour_stem_idx = TIAN_GAN.index(hour_stem)
    hour_branch_idx = DI_ZHI.index(hour_branch)

    # 5. 找值符 (地盘时干所在宫对应的原始星)
    zhifu_palace = None
    for palace, stem in di_pan.items():
        if stem == hour_stem:
            zhifu_palace = palace
            break
    if zhifu_palace is None:
        zhifu_palace = 1

    # 6. 值符星: 地盘时干所在宫的原始星
    zhifu_star: Optional[str] = None
    for star, orig_palace in _JIU_XING_ORIGINAL_PALACE.items():
        if orig_palace == zhifu_palace:
            zhifu_star = star
            break
    if zhifu_star is None:
        zhifu_star = "天禽"

    # 7. 值使门: 地盘时支所在宫的原始门
    zhishi_palace = None
    for palace, stem in di_pan.items():
        # 时支对应: 用时辰地支序号映射到宫位
        branch_palace = (hour_branch_idx % 9) + 1
        # 简化: 直接用地支序号推算值使宫
        pass
    # 简化推算: 根据地支序数
    zhishi_door: Optional[str] = None
    door_orig = hour_branch_idx % 8
    zhishi_door = BA_MEN[door_orig]

    # 8. 排天盘: 九星按值符所在 + 阳顺阴逆 分配到各宫
    star_order = _LUOSHU_ORDER_YANG if dun_type == "阳遁" else _LUOSHU_ORDER_YIN
    zhifu_star_idx = JIU_XING.index(zhifu_star)
    tian_pan_stars: dict[int, str] = {}
    zhifu_pos = star_order.index(zhifu_palace)
    for i in range(9):
        star = JIU_XING[(zhifu_star_idx + i) % 9]
        palace = star_order[(zhifu_pos + i) % 9]
        tian_pan_stars[palace] = star

    # 天盘天干: 随值符星转动
    tian_pan_stems: dict[int, str] = {}
    zhifu_di_stem = di_pan.get(zhifu_palace, "戊")
    stem_rotation = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    zhifu_stem_idx = stem_rotation.index(zhifu_di_stem)
    for i in range(9):
        stem = stem_rotation[(zhifu_stem_idx + i) % 9]
        palace = star_order[(zhifu_pos + i) % 9]
        tian_pan_stems[palace] = stem

    # 9. 排人盘 (八门): 值使门随时支
    ren_pan_doors: dict[int, str] = {}
    zhishi_door_idx = BA_MEN.index(zhishi_door)
    hour_offset = hour_branch_idx % 8
    door_order = _LUOSHU_ORDER_YANG if dun_type == "阳遁" else _LUOSHU_ORDER_YIN
    for i in range(8):
        door = BA_MEN[(zhishi_door_idx + i) % 8]
        palace = door_order[(hour_offset + i) % 9]
        if palace == 5:
            palace = 2  # 中五寄坤二
        ren_pan_doors[palace] = door

    # 10. 排神盘 (八神): 值符起于值符宫, 阳顺阴逆
    shen_pan_spirits: dict[int, str] = {}
    shen_order = _LUOSHU_ORDER_YANG if dun_type == "阳遁" else _LUOSHU_ORDER_YIN
    shen_start = shen_order.index(zhifu_palace)
    for i in range(8):
        spirit = BA_SHEN[i]
        palace = shen_order[(shen_start + i) % 9]
        if palace == 5:
            palace = 2 if dun_type == "阳遁" else 8
        shen_pan_spirits[palace] = spirit

    # 11. 组装九宫数据
    palaces: dict[int, QimenPalaceData] = {}
    for pi in range(1, 10):
        gong = JIU_GONG[pi]
        pd = QimenPalaceData(
            palace_index=pi,
            direction=gong["direction"],
            element=gong["element"],
            di_pan_stem=di_pan.get(pi, ""),
            tian_pan_stem=tian_pan_stems.get(pi, ""),
            ren_pan_door=ren_pan_doors.get(pi, ""),
            shen_pan_spirit=shen_pan_spirits.get(pi, ""),
            tian_pan_star=tian_pan_stars.get(pi, ""),
        )
        pd.ji_xiong = _assess_palace_ji_xiong(pd)
        palaces[pi] = pd

    dt_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

    return QimenPlate(
        datetime_str=dt_str,
        dun_type=dun_type,
        ju_number=ju_number,
        yuan=yuan,
        solar_term=term_name,
        palaces=palaces,
    )


def _assess_palace_ji_xiong(palace: QimenPalaceData) -> str:
    """综合判定单宫吉凶."""
    score = 0

    # 门吉凶
    door_attr = BA_MEN_ATTRS.get(palace.ren_pan_door, {})
    if door_attr.get("ji_xiong") == "吉":
        score += 2
    elif door_attr.get("ji_xiong") == "凶":
        score -= 2

    # 星吉凶
    star_attr = JIU_XING_ATTRS.get(palace.tian_pan_star, {})
    if star_attr.get("ji_xiong") == "吉":
        score += 1
    elif star_attr.get("ji_xiong") == "凶":
        score -= 1

    # 神吉凶
    shen_attr = BA_SHEN_ATTRS.get(palace.shen_pan_spirit, {})
    if shen_attr.get("ji_xiong") == "吉":
        score += 1
    elif shen_attr.get("ji_xiong") == "凶":
        score -= 1

    # 天盘生地盘 → 吉
    if palace.tian_pan_stem and palace.di_pan_stem:
        t_stem_elem = _stem_element(palace.tian_pan_stem)
        d_stem_elem = _stem_element(palace.di_pan_stem)
        if generates(t_stem_elem, d_stem_elem):
            score += 1
        if overcomes(d_stem_elem, t_stem_elem):
            score -= 1

    if score >= 3:
        return "大吉"
    elif score >= 1:
        return "吉"
    elif score == 0:
        return "平"
    elif score >= -2:
        return "凶"
    else:
        return "大凶"


def _stem_element(stem: str) -> str:
    """天干 → 五行."""
    mapping = {
        "甲": "木", "乙": "木",
        "丙": "火", "丁": "火",
        "戊": "土", "己": "土",
        "庚": "金", "辛": "金",
        "壬": "水", "癸": "水",
    }
    return mapping.get(stem, "土")


# ============================================================
# 战役集成: 奇门 → 阶段判定
# ============================================================

# 阶段 → 对应八门
_STAGE_DOOR_MAP: dict[str, str] = {
    "开战": "开门",   # 开局进攻
    "相持": "杜门",   # 堵塞相持
    "决战": "伤门",   # 战斗损伤
    "追击": "惊门",   # 惊恐追击
    "善后": "休门",   # 休养生息
}

_DOOR_PALACE_MAP: dict[str, int] = {
    "休门": 1, "生门": 8, "伤门": 3, "杜门": 4,
    "景门": 9, "死门": 2, "惊门": 7, "开门": 6,
}


def qimen_stage_judgment(
    plate: QimenPlate,
    stage_name: str,
    attacker_element: str,
    defender_element: str,
    prev_score_atk: float = 0.5,
    prev_score_def: float = 0.5,
) -> dict:
    """用奇门遁甲判定单阶段战果.

    返回与六爻 _judge_stage 兼容的判据.
    """
    door_name = _STAGE_DOOR_MAP.get(stage_name, "景门")
    target_palace = _DOOR_PALACE_MAP.get(door_name, 1)

    palace = plate.palaces.get(target_palace)
    if not palace:
        return {
            "advantage": "even",
            "casualties_attacker": 0.15,
            "casualties_defender": 0.15,
            "supply_loss": "中",
            "turning_point": "盘局不明",
        }

    # 宫吉凶 → 分数
    ji_score = {"大吉": 0.9, "吉": 0.7, "平": 0.5, "凶": 0.3, "大凶": 0.1}
    base_score = ji_score.get(palace.ji_xiong, 0.5)

    # 宫元素与攻守方元素的生克关系
    pal_elem = palace.element
    bias = 0.0
    if generates(pal_elem, attacker_element):
        bias += 0.15
    elif overcomes(pal_elem, attacker_element):
        bias -= 0.15
    if generates(pal_elem, defender_element):
        bias -= 0.15
    elif overcomes(pal_elem, defender_element):
        bias += 0.15

    atk_score = min(1.0, max(0.0, base_score + bias + (prev_score_atk - 0.5) * 0.2))
    def_score = min(1.0, max(0.0, base_score - bias + (prev_score_def - 0.5) * 0.2))

    # 优势
    if atk_score > def_score + 0.15:
        advantage = "attacker"
    elif def_score > atk_score + 0.15:
        advantage = "defender"
    else:
        advantage = "even"

    # 伤亡
    atk_cas = max(0.05, min(0.7, (1.0 - atk_score) * 0.4 + random.uniform(-0.05, 0.05)))
    def_cas = max(0.05, min(0.7, (1.0 - def_score) * 0.4 + random.uniform(-0.05, 0.05)))

    # 后勤
    supply_scores = {"大吉": "无", "吉": "轻", "平": "中", "凶": "中", "大凶": "重"}
    supply_loss = supply_scores.get(palace.ji_xiong, "中")

    # 转折
    turning = (
        f"{door_name}在{palace.direction}方{palace.palace_index}宫, "
        f"{palace.ji_xiong}, {palace.ren_pan_door}{palace.tian_pan_star}临{palace.shen_pan_spirit}"
    )

    return {
        "advantage": advantage,
        "casualties_attacker": round(atk_cas, 3),
        "casualties_defender": round(def_cas, 3),
        "supply_loss": supply_loss,
        "turning_point": turning,
        "atk_score": round(atk_score, 3),
        "def_score": round(def_score, 3),
    }
