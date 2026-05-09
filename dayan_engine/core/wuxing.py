"""五行生克 (Five Elements generation and overcoming).

五行: 木火土金水 (Wood, Fire, Earth, Metal, Water)

生 (Generation cycle): 木生火 → 火生土 → 土生金 → 金生水 → 水生木
克 (Overcoming cycle): 木克土 → 土克水 → 水克火 → 火克金 → 金克木

此文件还包含天干地支→五行的映射, 以及八卦→五行的映射.
"""

# --- 五行基本数据 ---

FIVE_ELEMENTS = ["木", "火", "土", "金", "水"]

# 生序: key 生 value
_GENERATES_MAP: dict[str, str] = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

# 克序: key 克 value
_OVERCOMES_MAP: dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

# 被生序 (反向): key 被 value 生
_GENERATED_BY_MAP: dict[str, str] = {v: k for k, v in _GENERATES_MAP.items()}

# 被克序 (反向): key 被 value 克
_OVERCOME_BY_MAP: dict[str, str] = {v: k for k, v in _OVERCOMES_MAP.items()}


def generates(a: str, b: str) -> bool:
    """判断 a 是否生 b (a → b)."""
    return _GENERATES_MAP.get(a) == b


def overcomes(a: str, b: str) -> bool:
    """判断 a 是否克 b (a → b)."""
    return _OVERCOMES_MAP.get(a) == b


def generated_by(element: str) -> str:
    """返回生我者 (谁生 element?)."""
    return _GENERATED_BY_MAP.get(element, "")


def overcome_by(element: str) -> str:
    """返回克我者 (谁克 element?)."""
    return _OVERCOME_BY_MAP.get(element, "")


def generated_element(element: str) -> str:
    """返回我生者 (element 生谁?)."""
    return _GENERATES_MAP.get(element, "")


def overcome_element(element: str) -> str:
    """返回我克者 (element 克谁?)."""
    return _OVERCOMES_MAP.get(element, "")


# --- 天干五行 ---
# 甲乙→木, 丙丁→火, 戊己→土, 庚辛→金, 壬癸→水
STEM_ELEMENT: dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}


def element_of_stem(stem: str) -> str:
    """返回天干对应的五行."""
    return STEM_ELEMENT.get(stem, "")


# --- 地支五行 ---
# 寅卯→木, 巳午→火, 辰戌丑未→土, 申酉→金, 亥子→水
BRANCH_ELEMENT: dict[str, str] = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
}


def element_of_branch(branch: str) -> str:
    """返回地支对应的五行."""
    return BRANCH_ELEMENT.get(branch, "")


# --- 八卦五行 ---
# 乾兑→金, 震巽→木, 坎→水, 离→火, 艮坤→土
TRIGRAM_ELEMENT: dict[int, str] = {
    1: "金",  # 乾
    2: "金",  # 兑
    3: "火",  # 离
    4: "木",  # 震
    5: "木",  # 巽
    6: "水",  # 坎
    7: "土",  # 艮
    8: "土",  # 坤
}


def element_of_trigram(index: int) -> str:
    """返回八卦对应的五行. index 为 1-8 先天八卦数."""
    return TRIGRAM_ELEMENT.get(index, "")


# --- 八卦名称 ---
TRIGRAM_NAMES: dict[int, str] = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}


# --- 生克关系描述 (用于战报生成) ---

def relation_desc(my_element: str, other_element: str) -> str:
    """返回我与对方的五行关系中文描述.

    Returns:
        如 "我生彼" / "彼生我" / "我克彼" / "彼克我" / "比和"
    """
    if my_element == other_element:
        return "比和"
    if generates(my_element, other_element):
        return "我生彼"
    if generates(other_element, my_element):
        return "彼生我"
    if overcomes(my_element, other_element):
        return "我克彼"
    if overcomes(other_element, my_element):
        return "彼克我"
    return "未知"
