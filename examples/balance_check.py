#!/usr/bin/env python3
"""平衡性验证脚本 (Balance Check Script).

对大衍引擎战役判定进行统计分析, 检测极端胜率和偏态分布,
确保引擎产出合理的战役结果。

用法:
    python3 examples/balance_check.py            # 默认 500 场
    python3 examples/balance_check.py 1000       # 自定义场数
    python3 examples/balance_check.py 500 qimen  # 使用奇门遁甲方法
"""

import sys
import os
import random
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dayan_engine.core.types import BattleConfig
from dayan_engine.core.battle import run_battle


def _make_configs(num_battles: int) -> list[BattleConfig]:
    """生成多样化的战役配置, 用于全面测试."""
    configs = []
    templates = [
        # (attacker_name, defender_name, atk_traits, def_traits, desc)
        ("曹操", "孙权",
         {"主帅": 0.90, "军师": 0.85, "先锋": 0.70, "后勤": 0.80, "军资": 0.95, "联盟": 0.30},
         {"主帅": 0.70, "军师": 0.95, "先锋": 0.75, "后勤": 0.85, "军资": 0.90, "联盟": 0.70},
         "赤壁-曹强孙智"),
        ("刘备", "曹操",
         {"主帅": 0.75, "军师": 0.90, "先锋": 0.80, "后勤": 0.65, "军资": 0.55, "联盟": 0.95},
         {"主帅": 0.90, "军师": 0.85, "先锋": 0.70, "后勤": 0.80, "军资": 0.95, "联盟": 0.30},
         "汉中-刘攻曹守"),
        ("诸葛亮", "司马懿",
         {"主帅": 0.80, "军师": 1.00, "先锋": 0.65, "后勤": 0.90, "军资": 0.75, "联盟": 0.85},
         {"主帅": 0.85, "军师": 0.95, "先锋": 0.60, "后勤": 0.85, "军资": 0.80, "联盟": 0.40},
         "北伐-诸葛对司马"),
        ("周瑜", "曹操",
         {"主帅": 0.85, "军师": 0.90, "先锋": 0.80, "后勤": 0.75, "军资": 0.80, "联盟": 0.70},
         {"主帅": 0.90, "军师": 0.85, "先锋": 0.70, "后勤": 0.80, "军资": 0.95, "联盟": 0.30},
         "赤壁-周瑜对曹操"),
    ]

    symmetric_tpl = (
        "袁绍", "袁术",
        {"主帅": 0.70, "军师": 0.70, "先锋": 0.70, "后勤": 0.70, "军资": 0.70, "联盟": 0.50},
        {"主帅": 0.70, "军师": 0.70, "先锋": 0.70, "后勤": 0.70, "军资": 0.70, "联盟": 0.50},
        "对称测试",
    )

    for i in range(num_battles):
        if i < num_battles * 0.2:
            tpl = symmetric_tpl
        elif i < num_battles * 0.5:
            tpl = templates[i % len(templates)]
        else:
            tpl = random.choice(templates)

        cast_nums = (
            random.randint(1, 30),
            random.randint(1, 30),
            random.randint(1, 30),
        )

        configs.append(BattleConfig(
            attacker_name=tpl[0],
            defender_name=tpl[1],
            attacker_traits=tpl[2],
            defender_traits=tpl[3],
            time_desc=f"测试战役{i}",
            location=tpl[4],
            cast_nums=cast_nums,
        ))

    return configs


def _compute_stats(results: list) -> dict:
    """从战役结果列表计算统计指标."""
    n = len(results)
    winners = Counter(r.winner for r in results)

    atk_cas = [r.total_casualties_attacker for r in results]
    def_cas = [r.total_casualties_defender for r in results]

    def _desc(vals: list[float]) -> dict:
        sorted_vals = sorted(vals)
        m = len(sorted_vals)
        return {
            "mean": sum(vals) / m,
            "median": sorted_vals[m // 2],
            "std": (sum((v - sum(vals) / m) ** 2 for v in vals) / m) ** 0.5,
            "min": min(vals),
            "max": max(vals),
        }

    # 阶段统计
    stage_advantage: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        for s in r.stages:
            stage_advantage[s.stage_name][s.advantage] += 1

    return {
        "n": n,
        "winners": dict(winners),
        "win_rates": {k: v / n for k, v in winners.items()},
        "atk_casualties": _desc(atk_cas),
        "def_casualties": _desc(def_cas),
        "stage_advantage": {k: dict(v) for k, v in stage_advantage.items()},
    }


def _check_warnings(stats: dict) -> list[str]:
    """检测平衡性问题."""
    warnings = []
    wr = stats["win_rates"]

    for side, label in [("attacker", "攻方"), ("defender", "守方")]:
        rate = wr.get(side, 0)
        if rate > 0.70:
            warnings.append(f"⚠ {label}胜率 {rate:.1%} 偏高 (>70%)")
        if rate < 0.15 and stats["n"] >= 200:
            warnings.append(f"⚠ {label}胜率 {rate:.1%} 偏低 (<15%)")

    draw_rate = wr.get("draw", 0)
    if draw_rate > 0.50:
        warnings.append(f"⚠ 平局率 {draw_rate:.1%} 偏高 (>50%), 可能存在区分度不足")

    atk_mean = stats["atk_casualties"]["mean"]
    def_mean = stats["def_casualties"]["mean"]
    if atk_mean > 0 and def_mean > 0:
        ratio = max(atk_mean, def_mean) / min(atk_mean, def_mean)
        if ratio > 2.5:
            warnings.append(f"⚠ 双方平均伤亡差异 {ratio:.1f}x, 超出 2.5x 阈值")

    # 决战阶段优势与最终胜负一致性
    climax = stats["stage_advantage"].get("决战", {})
    climax_total = sum(climax.values())
    if climax_total > 0:
        climax_atk = climax.get("attacker", 0)
        climax_def = climax.get("defender", 0)
        climax_winner_rate = max(climax_atk, climax_def) / climax_total
        if climax_winner_rate > 0.85:
            warnings.append(
                f"⚠ 决战阶段优势方最终胜率 {climax_winner_rate:.1%}, "
                "决战几乎完全决定全局 (>85%)"
            )

    return warnings


def _print_report(stats: dict, warnings: list[str], method: str) -> None:
    """格式化打印平衡性报告."""
    n = stats["n"]
    wr = stats["win_rates"]

    print("═" * 58)
    print(f"  大衍引擎 · 平衡性验证报告")
    print(f"  Method: {'六爻纳甲' if method == 'liuyao' else '奇门遁甲'}"
          f"    Battles: {n}")
    print("═" * 58)
    print()

    # 胜率
    print("  ▸ 胜率分布")
    for side, label in [("attacker", "攻方"), ("defender", "守方"), ("draw", "平局")]:
        rate = wr.get(side, 0)
        bar = "█" * int(rate * 40)
        print(f"    {label}: {rate:6.1%} {bar} ({wr.get(side, 0)} 场)")
    print()

    # 伤亡
    print("  ▸ 伤亡统计")
    print(f"    {'':>12} {'平均值':>7} {'中位数':>7} {'标准差':>7} {'最小值':>7} {'最大值':>7}")
    for side, key in [("攻方", "atk_casualties"), ("守方", "def_casualties")]:
        d = stats[key]
        print(f"    {side:>10}: {d['mean']:7.3f} {d['median']:7.3f} "
              f"{d['std']:7.3f} {d['min']:7.3f} {d['max']:7.3f}")
    print()

    # 阶段优势
    print("  ▸ 阶段优势分布")
    stage_order = ["开战", "相持", "决战", "追击", "善后"]
    header = f"    {'阶段':<8} {'攻方优':>7} {'守方优':>7} {'均势':>7}"
    print(header)
    for stage in stage_order:
        sa = stats["stage_advantage"].get(stage, {})
        print(f"    {stage:<8} {sa.get('attacker', 0):>7} "
              f"{sa.get('defender', 0):>7} {sa.get('even', 0):>7}")
    print()

    # 警告
    if warnings:
        print("  ▸ 平衡性警告/提示")
        for w in warnings:
            print(f"    {w}")
    else:
        print("  ▸ 平衡性: ✓ 未发现明显问题")
    print()

    print("═" * 58)


def main() -> None:
    num_battles = 500
    method = "liuyao"

    for arg in sys.argv[1:]:
        try:
            num_battles = int(arg)
        except ValueError:
            if arg in ("liuyao", "qimen"):
                method = arg

    print(f"  正在运行 {num_battles} 场战役推演 ({method})...")
    print()

    configs = _make_configs(num_battles)
    results = []

    for i, cfg in enumerate(configs):
        result = run_battle(cfg, seed=i, method=method)
        results.append(result)
        if (i + 1) % 100 == 0:
            print(f"    已完成 {i + 1}/{num_battles} ...")

    stats = _compute_stats(results)
    warnings = _check_warnings(stats)
    _print_report(stats, warnings, method)


if __name__ == "__main__":
    main()
