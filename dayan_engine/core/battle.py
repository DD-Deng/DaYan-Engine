"""战役判定引擎 (Battle Judgment Engine).

整合梅花易数起卦 + 六爻纳甲 + 五行生克 + 六亲配位,
对一场战役进行分阶段推演, 输出最终战果。

分阶段推演流程:
  1. 梅花起卦得总卦 (本卦 + 变卦 + 动爻)
  2. 总卦纳甲, 配世应六亲
  3. 5 阶段循环:
     a. 基于总卦 + 阶段序数 + 前阶段累积 → 起子卦
     b. 子卦纳甲 → 用神判定 → 阶段结果
  4. 聚合阶段结果 → 最终战果
"""

import random
from dayan_engine.core.types import BattleConfig, BattleResult, StageResult, Hexagram, Line
from dayan_engine.core.meihua import cast as meihua_cast
from dayan_engine.core.liuyao import (
    build_hexagram, apply_moving_line,
    get_yongshen_line, judge_yongshen_status,
    judge_casualties, judge_supply, get_turning_point,
)
from dayan_engine.core.wuxing import element_of_trigram, TRIGRAM_NAMES
from dayan_engine.factors.battle_factors import (
    derive_factors_from_traits, get_factor_weights_for_lines,
)

# 战役五阶段
_BATTLE_STAGES = ["开战", "相持", "决战", "追击", "善后"]

# 阶段对应月建 (影响用神得令判定)
_STAGE_MONTH_ELEMENTS = {
    "开战": "木",  # 春 — 木旺
    "相持": "火",  # 夏 — 火旺
    "决战": "金",  # 秋 — 金旺
    "追击": "水",  # 冬 — 水旺
    "善后": "土",  # 季末 — 土旺
}


def _derive_sub_hexagram(
    main_hexagram: Hexagram,
    stage_index: int,
    prev_results: list[StageResult],
    battle_config: BattleConfig,
) -> tuple[Hexagram, int]:
    """基于总卦 + 阶段序数 + 前阶段结果推导子卦.

    子卦推导逻辑:
      - 以阶段序数为上卦变动基数
      - 以前阶段累积伤亡为下卦变动基数
      - 在总卦基础上微调产生子卦

    Returns:
        (子卦 hexagram, 子卦动爻)
    """
    # 用阶段序数扰动上下卦
    upper_shift = stage_index % 8
    lower_shift = (stage_index * 3 + sum(
        int(r.casualties_attacker * 10 + r.casualties_defender * 10)
        for r in prev_results
    )) % 8

    new_upper_idx = ((main_hexagram.upper.index - 1 + upper_shift) % 8) + 1
    new_lower_idx = ((main_hexagram.lower.index - 1 + lower_shift) % 8) + 1

    sub = build_hexagram(new_upper_idx, new_lower_idx)

    # 子卦动爻: 基于总卦动爻 + 阶段偏移
    moving_line = ((stage_index + 1) * 7 + sum(
        int(r.casualties_attacker * 5) for r in prev_results
    )) % 6
    if moving_line == 0:
        moving_line = 6

    # 标记动爻
    apply_moving_line(sub, moving_line)

    return sub, moving_line


def _judge_stage(
    sub_hexagram: Hexagram,
    moving_line: int,
    stage_name: str,
    battle_config: BattleConfig,
    prev_results: list[StageResult],
) -> StageResult:
    """判定单个阶段的战果.

    综合用神状态 + 因子权重 → 阶段优势方 + 伤亡 + 后勤损失.
    """
    # 双方用神
    attacker_ys = get_yongshen_line(sub_hexagram, "主帅", is_attacker=True)
    defender_ys = get_yongshen_line(sub_hexagram, "主帅", is_attacker=False)

    month_element = _STAGE_MONTH_ELEMENTS.get(stage_name, "土")

    # 攻方用神判定
    if attacker_ys:
        attacker_status = judge_yongshen_status(
            sub_hexagram, attacker_ys, month_element=month_element
        )
    else:
        attacker_status = {"status": "平和", "score": 0.5, "details": "未找到用神爻"}

    # 守方用神判定
    if defender_ys:
        defender_status = judge_yongshen_status(
            sub_hexagram, defender_ys, month_element=month_element
        )
    else:
        defender_status = {"status": "平和", "score": 0.5, "details": "未找到用神爻"}

    # 优势判定
    atk_score = attacker_status["score"]
    def_score = defender_status["score"]

    if atk_score > def_score + 0.15:
        advantage = "attacker"
    elif def_score > atk_score + 0.15:
        advantage = "defender"
    else:
        advantage = "even"

    # 伤亡计算
    atk_cas, def_cas = judge_casualties(sub_hexagram, atk_score)

    # 后勤损失
    supply_loss = judge_supply(sub_hexagram)

    # 关键转折
    turning_point = get_turning_point(sub_hexagram)

    # 用神状态综合描述
    if advantage == "attacker":
        ys_status = f"攻方用神{attacker_status['status']}({atk_score:.2f}), 守方用神{defender_status['status']}({def_score:.2f})"
    elif advantage == "defender":
        ys_status = f"守方用神{defender_status['status']}({def_score:.2f}), 攻方用神{attacker_status['status']}({atk_score:.2f})"
    else:
        ys_status = f"双方用神持平 (攻{atk_score:.2f}/守{def_score:.2f})"

    return StageResult(
        stage_name=stage_name,
        hexagram=sub_hexagram,
        moving_line=moving_line,
        yongshen_status=ys_status,
        advantage=advantage,
        casualties_attacker=round(atk_cas, 3),
        casualties_defender=round(def_cas, 3),
        supply_loss=supply_loss,
        turning_point=turning_point,
    )


def _aggregate_results(
    main_hexagram: Hexagram,
    changed_hexagram: Hexagram,
    stages: list[StageResult],
    battle_config: BattleConfig,
) -> tuple[str, float, float]:
    """聚合五个阶段结果, 得出最终战果.

    Returns:
        (winner, total_atk_casualties, total_def_casualties)
    """
    # 统计各阶段优势
    atk_wins = sum(1 for s in stages if s.advantage == "attacker")
    def_wins = sum(1 for s in stages if s.advantage == "defender")
    even_count = sum(1 for s in stages if s.advantage == "even")

    # 加权: 决战阶段权重最高
    stage_weights = {"开战": 0.8, "相持": 1.0, "决战": 2.0, "追击": 1.5, "善后": 0.7}

    weighted_atk = sum(
        stage_weights.get(s.stage_name, 1.0) * (1 if s.advantage == "attacker" else 0)
        for s in stages
    )
    weighted_def = sum(
        stage_weights.get(s.stage_name, 1.0) * (1 if s.advantage == "defender" else 0)
        for s in stages
    )

    # 总伤亡 = 各阶段加权平均
    total_atk_cas = sum(
        s.casualties_attacker * stage_weights.get(s.stage_name, 1.0)
        for s in stages
    ) / sum(stage_weights.values())
    total_def_cas = sum(
        s.casualties_defender * stage_weights.get(s.stage_name, 1.0)
        for s in stages
    ) / sum(stage_weights.values())

    if weighted_atk > weighted_def * 1.2:
        winner = "attacker"
    elif weighted_def > weighted_atk * 1.2:
        winner = "defender"
    else:
        winner = "draw"

    return winner, round(total_atk_cas, 3), round(total_def_cas, 3)


def run_battle(battle_config: BattleConfig, seed: int | None = None) -> BattleResult:
    """运行完整战役推演.

    Args:
        battle_config: 战役配置
        seed: 随机种子 (可选, 用于可复现推演)

    Returns:
        BattleResult 包含所有阶段结果、战果和战报
    """
    if seed is not None:
        random.seed(seed)

    # 1. 梅花易数起卦 → 总卦
    num1, num2, num3 = battle_config.cast_nums
    main_hex, changed_hex, main_moving = meihua_cast(num1, num2, num3)

    # 2. 总卦纳甲完整
    main_hex = build_hexagram(main_hex.upper.index, main_hex.lower.index)
    changed_hex = apply_moving_line(main_hex, main_moving)  # 标记动爻 + 返回变卦

    # 3. 分阶段推演
    stage_results: list[StageResult] = []
    for i, stage_name in enumerate(_BATTLE_STAGES):
        sub_hex, sub_moving = _derive_sub_hexagram(
            main_hex, i, stage_results, battle_config
        )
        stage_result = _judge_stage(
            sub_hex, sub_moving, stage_name, battle_config, stage_results
        )
        stage_results.append(stage_result)

    # 4. 聚合战果
    winner, total_atk_cas, total_def_cas = _aggregate_results(
        main_hex, changed_hex, stage_results, battle_config
    )

    result = BattleResult(
        config=battle_config,
        main_hexagram=main_hex,
        changed_hexagram=changed_hex,
        stages=stage_results,
        winner=winner,
        total_casualties_attacker=total_atk_cas,
        total_casualties_defender=total_def_cas,
    )

    return result
