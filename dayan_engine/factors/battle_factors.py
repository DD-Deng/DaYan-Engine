"""战役因素映射 — 12 因素 → 爻位 + 用神映射.

将战役元数据 (兵力、地形、天气、士气等) 映射为各爻位的影响因子,
影响五行生克判定中的权重。

用神映射定义战役角色与六亲/世应爻的对应关系.
"""

from typing import Optional

# ============================================================
# 用神映射: 战役角色 → 六亲 / 世应
# ============================================================

YONGSHEN_MAP: dict[str, str] = {
    "主帅": "世/应",   # 攻方=世爻, 守方=应爻
    "军师": "兄弟",    # 谋士/军师 → 兄弟爻
    "先锋": "子孙",    # 先锋/武将 → 子孙爻
    "后勤": "父母",    # 粮草/辎重 → 父母爻
    "军资": "妻财",    # 财力/物资 → 妻财爻
    "敌将": "官鬼",    # 敌军将领 → 官鬼爻
    "谋士": "应",      # 谋士 → 应爻的提醒/反映
}

# 用神角色说明 (用于战报)
YONGSHEN_ROLE_DESC: dict[str, str] = {
    "主帅": "统兵之将, 用神所在, 胜负之关键",
    "军师": "运筹帷幄, 兄弟相助, 决策之智囊",
    "先锋": "冲锋陷阵, 子孙克敌, 杀伤之主力",
    "后勤": "粮草补给, 父母护佑, 持久之根基",
    "军资": "财力物资, 妻财支撑, 战争之血脉",
    "敌将": "敌方将领, 官鬼相克, 威胁之来源",
    "谋士": "应爻之兆, 洞悉敌情, 转机之先声",
}


# ============================================================
# 12 因素 → 爻位映射
# ============================================================
# 每个战役因素对应一个或多个爻位, 并有一个权重 (0.0-1.0)
# 影响该爻位所在五行的"得令"判定

class BattleFactor:
    """单个战役因子."""

    def __init__(
        self,
        name: str,
        line_positions: list[int],  # 影响的爻位 1-6
        weight: float,               # 权重 0.0-1.0
        desc: str = "",
    ):
        self.name = name
        self.line_positions = line_positions
        self.weight = weight
        self.desc = desc


# 12 因素定义
FACTOR_DEFINITIONS: list[BattleFactor] = [
    BattleFactor("兵力对比", [1, 4], 0.9, "攻守双方兵力多寡直接影响初爻(基础)和四爻(外围)"),
    BattleFactor("地形优势", [2, 5], 0.7, "地利影响二爻(内应)和五爻(统帅)"),
    BattleFactor("天气条件", [3, 6], 0.5, "天时影响三爻(践行)和上爻(终局)"),
    BattleFactor("士气高低", [1, 3], 0.6, "士气影响初爻(基层)和三爻(行动)"),
    BattleFactor("粮草补给", [2], 0.8, "补给影响二爻(后勤内应)"),
    BattleFactor("将领能力", [5], 0.85, "将领决定五爻(君位/统帅)"),
    BattleFactor("谋士计策", [4], 0.7, "计谋影响四爻(近君/参谋)"),
    BattleFactor("联盟关系", [4, 6], 0.5, "联盟影响四爻(外交)和上爻(结果)"),
    BattleFactor("军心凝聚", [1, 2], 0.6, "军心影响初爻(士卒)和二爻(中层)"),
    BattleFactor("情报准确", [3], 0.65, "情报影响三爻(决策执行)"),
    BattleFactor("后方稳定", [2, 6], 0.55, "后方影响二爻(根基)和上爻(终局)"),
    BattleFactor("运气变数", [1, 2, 3, 4, 5, 6], 0.3, "天意难测, 遍及六爻"),
]


def get_factor_weights_for_lines(factors: dict[str, float]) -> dict[int, float]:
    """将指定因子的权重聚合到各爻位.

    Args:
        factors: {因子名: 生效值 0.0-1.0}, 如 {"兵力对比": 0.8, "士气高低": 0.6}

    Returns:
        {爻位 1-6: 总权重}
    """
    line_weights: dict[int, float] = {i: 0.0 for i in range(1, 7)}
    factor_lookup = {f.name: f for f in FACTOR_DEFINITIONS}

    for factor_name, value in factors.items():
        factor = factor_lookup.get(factor_name)
        if factor is None:
            continue
        contribution = factor.weight * value
        for pos in factor.line_positions:
            line_weights[pos] += contribution

    # 归一化
    max_w = max(line_weights.values()) if line_weights else 1.0
    if max_w > 0:
        for pos in line_weights:
            line_weights[pos] = min(1.0, line_weights[pos] / max_w)

    return line_weights


def derive_factors_from_traits(traits: dict[str, float]) -> dict[str, float]:
    """从 agent traits 推导战役因子的生效值.

    将 agent 特质映射到因子, 使用双方差异作为因子值.

    Args:
        traits: {"主帅": 0.9, "军师": 0.7, "先锋": 0.8, "后勤": 0.6, "军资": 0.7}

    Returns:
        {因子名: 生效值}
    """
    mapping = {
        "将领能力": traits.get("主帅", 0.5),
        "谋士计策": traits.get("军师", 0.5),
        "士气高低": traits.get("先锋", 0.5),
        "粮草补给": traits.get("后勤", 0.5),
        "军心凝聚": traits.get("后勤", 0.5) * 0.7 + traits.get("主帅", 0.5) * 0.3,
        "情报准确": traits.get("军师", 0.5) * 0.6 + traits.get("先锋", 0.5) * 0.4,
        "后方稳定": traits.get("后勤", 0.5) * 0.4 + traits.get("军资", 0.5) * 0.6,
        "联盟关系": traits.get("联盟", 0.3),
        "兵力对比": traits.get("主帅", 0.5) * 0.5 + traits.get("军资", 0.5) * 0.5,
        "地形优势": traits.get("先锋", 0.5),
        "天气条件": 0.5,  # 不可控因素, 固定中等
        "运气变数": 0.3,   # 低保底
    }
    return mapping
