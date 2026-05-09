#!/usr/bin/env python3
"""赤壁之战 Demo — 大衍引擎战役推演演示.

攻方: 曹操 (mock agent, 主帅特质 0.9)
守方: 孙权 (mock agent, 军师特质 0.95)
盟友: 刘备 (mock agent, 联盟特质 0.8)
时间: 建安十三年冬
地点: 赤壁

用法:
    python examples/chibi_demo.py           # 使用随机种子
    python examples/chibi_demo.py 42        # 指定随机种子
"""

import sys
import os

# 将项目根目录加入 path (支持直接运行)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dayan_engine.core.types import BattleConfig
from dayan_engine.core.battle import run_battle
from dayan_engine.narrator.template_narrator import generate
from dayan_engine.agents.mock_agent import create_three_kingdoms_agents


def main() -> None:
    # 解析种子
    seed = None
    if len(sys.argv) > 1:
        seed = int(sys.argv[1])

    # 预置的赤壁之战配置
    # 起卦三数: 取自"建安十三年" + "赤壁"对应数字
    # 建=9, 安=6, 十三=13 (梅花易数取数可任意, 这里用有意义的数字)
    cast_nums = (9, 6, 13)  # 9=建, 6=安, 13=十三年

    config = BattleConfig(
        attacker_name="曹操",
        defender_name="孙权",
        attacker_traits={
            "主帅": 0.90, "军师": 0.85, "先锋": 0.70,
            "后勤": 0.80, "军资": 0.95, "联盟": 0.30,
        },
        defender_traits={
            "主帅": 0.70, "军师": 0.95, "先锋": 0.75,
            "后勤": 0.85, "军资": 0.90, "联盟": 0.70,
        },
        ally_name="刘备",
        ally_traits={
            "主帅": 0.75, "军师": 0.90, "先锋": 0.80,
            "后勤": 0.65, "军资": 0.55, "联盟": 0.95,
        },
        time_desc="建安十三年冬",
        location="赤壁",
        cast_nums=cast_nums,
    )

    print("═" * 60)
    print("  大衍引擎 · 赤壁之战推演")
    print("  DaYan Engine · Battle of Red Cliffs")
    print("═" * 60)
    print()
    print(f"  攻方: {config.attacker_name} (主帅 {config.attacker_traits['主帅']})")
    print(f"  守方: {config.defender_name} (军师 {config.defender_traits['军师']})")
    print(f"  盟友: {config.ally_name} (联盟 {config.ally_traits['联盟']})")
    print(f"  时间: {config.time_desc}")
    print(f"  地点: {config.location}")
    print(f"  起卦: {cast_nums}")
    print()

    if seed is not None:
        print(f"  [随机种子: {seed}]")
        print()

    # 运行战役推演
    result = run_battle(config, seed=seed)

    # 生成战报
    narrative = generate(result)

    print(narrative)


if __name__ == "__main__":
    main()
