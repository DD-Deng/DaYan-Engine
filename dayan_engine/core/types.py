"""核心数据类型定义 — 八卦、爻、卦、战役配置与结果."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Trigram:
    """八卦 (Eight Trigrams).

    Attributes:
        index: 1-8, 按先天八卦数: 乾1兑2离3震4巽5坎6艮7坤8
        name: 卦名中文
        element: 所属五行 (金/木/水/火/土)
    """

    index: int
    name: str
    element: str


@dataclass
class Line:
    """一爻 (a single hexagram line).

    Attributes:
        position: 爻位 1-6, 自下而上 (初爻=1, 上爻=6)
        is_yang: True=阳爻(—), False=阴爻(--)
        heavenly_stem: 天干, 纳甲后赋值
        earthly_branch: 地支, 纳甲后赋值
        element: 本爻五行, 纳甲后赋值
        six_relation: 六亲 (父母/兄弟/子孙/妻财/官鬼), 纳甲后赋值
        shi_ying: 世应标记 ("世"/"应"/None)
        is_moving: 是否为动爻 (梅花起卦后的变爻)
    """

    position: int
    is_yang: bool
    heavenly_stem: str = ""
    earthly_branch: str = ""
    element: str = ""
    six_relation: str = ""
    shi_ying: Optional[str] = None
    is_moving: bool = False

    @property
    def position_name(self) -> str:
        """返回爻位中文名: 初/二/三/四/五/上."""
        names = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}
        return names[self.position]

    @property
    def yin_yang_char(self) -> str:
        """返回爻的阴阳显示字符."""
        return "—" if self.is_yang else "--"


@dataclass
class Hexagram:
    """六十四卦之一 (a 64-hexagram).

    Attributes:
        index: 1-64, 通行本周易卦序
        name: 卦名 (如"乾为天""坤为地")
        upper: 上卦 (外卦)
        lower: 下卦 (内卦)
        lines: 六爻, 自下而上 index 0=初爻, index 5=上爻
        palace: 所属八宫 (乾/坎/艮/震/巽/离/坤/兑)
        shi_position: 世爻位置 (1-6)
    """

    index: int
    name: str
    upper: Trigram
    lower: Trigram
    lines: list[Line] = field(default_factory=list)
    palace: str = ""
    shi_position: int = 0

    @property
    def ying_position(self) -> int:
        """应爻位置 — 与世爻相隔三位."""
        if not self.shi_position:
            return 0
        return ((self.shi_position + 2) % 6) + 1

    @property
    def moving_lines(self) -> list[Line]:
        """返回所有动爻."""
        return [ln for ln in self.lines if ln.is_moving]


@dataclass
class BattleConfig:
    """战役配置.

    Attributes:
        attacker_name: 攻方名称
        defender_name: 守方名称
        attacker_traits: 攻方将领特质, 如 {"主帅": 0.9, "军师": 0.7, ...}
        defender_traits: 守方将领特质
        ally_name: 盟友名称 (可选)
        ally_traits: 盟友特质 (可选)
        time_desc: 时间描述 (如"建安十三年冬")
        location: 地点 (如"赤壁")
        cast_nums: 梅花易数起卦三数 (num1, num2, num3)
    """

    attacker_name: str
    defender_name: str
    attacker_traits: dict[str, float]
    defender_traits: dict[str, float]
    time_desc: str = ""
    location: str = ""
    cast_nums: tuple[int, int, int] = (1, 2, 3)
    ally_name: str = ""
    ally_traits: dict[str, float] = field(default_factory=dict)


@dataclass
class StageResult:
    """单个战役阶段的推演结果.

    Attributes:
        stage_name: 阶段名 (开战/相持/决战/追击/善后)
        hexagram: 该阶段的子卦
        moving_line: 动爻位置
        yongshen_status: 用神状态描述 — 得令/受克/有救/无救
        advantage: 优势方 ("attacker"/"defender"/"even")
        casualties_attacker: 攻方伤亡比例 (0.0-1.0)
        casualties_defender: 守方伤亡比例
        supply_loss: 后勤损失程度 ("轻"/"中"/"重"/"无")
        turning_point: 关键转折描述
    """

    stage_name: str
    hexagram: Hexagram
    moving_line: int
    yongshen_status: str
    advantage: str
    casualties_attacker: float
    casualties_defender: float
    supply_loss: str
    turning_point: str


@dataclass
class BattleResult:
    """完整战役推演结果.

    Attributes:
        config: 原始战役配置
        main_hexagram: 总卦 (梅花易数起卦得出的本卦)
        changed_hexagram: 变卦
        stages: 五个阶段的推演结果
        winner: 胜方 ("attacker"/"defender"/"draw")
        total_casualties_attacker: 攻方总伤亡比例
        total_casualties_defender: 守方总伤亡比例
        narrative: 生成的战报文本
    """

    config: BattleConfig
    main_hexagram: Hexagram
    changed_hexagram: Hexagram
    stages: list[StageResult] = field(default_factory=list)
    winner: str = "draw"
    total_casualties_attacker: float = 0.0
    total_casualties_defender: float = 0.0
    narrative: str = ""
