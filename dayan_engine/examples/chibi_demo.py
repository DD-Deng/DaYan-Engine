#!/usr/bin/env python3
"""赤壁之战 Demo — 大衍引擎战役推演演示.

攻方: 曹操, 守方: 孙权, 盟友: 刘备
时间: 建安十三年冬, 地点: 赤壁

用法:
    python examples/chibi_demo.py              # 使用随机种子
    python examples/chibi_demo.py 42           # 指定随机种子
    python examples/chibi_demo.py 42 --llm     # 使用 LLM agent
    python examples/chibi_demo.py --llm        # LLM agent + 随机种子
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dayan_engine.core.types import BattleConfig
from dayan_engine.core.battle import run_battle
from dayan_engine.narrator.template_narrator import generate


def _has_llm_env() -> bool:
    """检查是否有可用的 LLM API 环境."""
    key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    return bool(key)


def _print_agent_section(title: str, text: str, icon: str = "⚔") -> None:
    """打印 agent 输出."""
    if text:
        print(f"  {icon} 【{title}】: {text}")


def main() -> None:
    seed = None
    use_llm = False
    model = None

    for arg in sys.argv[1:]:
        if arg == "--llm":
            use_llm = True
        elif arg.startswith("--model="):
            model = arg.split("=", 1)[1]
        else:
            try:
                seed = int(arg)
            except ValueError:
                pass

    # ---- 配置 ----
    cast_nums = (9, 6, 13)
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

    # ---- LLM agent 接入 ----
    if use_llm:
        if not _has_llm_env():
            print("[警告] 未设置 ANTHROPIC_AUTH_TOKEN, 降级为 Mock agent")
            use_llm = False
        else:
            from dayan_engine.agents.llm_agent import LLMAgent
            config.attacker_agent = LLMAgent(
                "曹操", config.attacker_traits,
                style="挟天子以令诸侯, 用兵大胆诡谲, 不习水战",
                model=model,
            )
            config.defender_agent = LLMAgent(
                "孙权", config.defender_traits,
                style="据江东之险, 善于用人谋略, 水战见长",
                model=model,
            )
            config.ally_agent = LLMAgent(
                "刘备", config.ally_traits,
                style="仁义之师, 汉室宗亲, 善于聚拢人心",
                model=model,
            )

    # ---- 打印开场 ----
    print("═" * 60)
    print("  大衍引擎 · 赤壁之战推演")
    print("  DaYan Engine · Battle of Red Cliffs")
    if use_llm:
        print("  [LLM Agent 模式]")
    print("═" * 60)
    print()
    print(f"  攻方: {config.attacker_name} (主帅 {config.attacker_traits['主帅']})")
    print(f"  守方: {config.defender_name} (军师 {config.defender_traits['军师']})")
    print(f"  盟友: {config.ally_name} (联盟 {config.ally_traits['联盟']})")
    print(f"  时间: {config.time_desc}")
    print(f"  地点: {config.location}")
    print(f"  起卦: {cast_nums}")
    if seed is not None:
        print(f"  种子: {seed}")
    print()

    # ---- 运行 ----
    result = run_battle(config, seed=seed)

    # ---- Agent 输出 ----
    agent_outputs = result.agent_outputs
    if agent_outputs:
        print("═" * 58)
        print("  【AI 将领决策实录】")
        print("═" * 58)

        # 战前策略
        pre = agent_outputs.get("pre_battle", {})
        if pre:
            print()
            print("  ── 战前军议 ──")
            _print_agent_line = _print_agent_section
            _print_agent_section(config.attacker_name, pre.get("attacker_strategy", ""), "⚔")
            _print_agent_section(config.defender_name, pre.get("defender_strategy", ""), "🛡")
            if config.ally_name:
                _print_agent_section(config.ally_name, pre.get("ally_strategy", ""), "🤝")

        # 各阶段策略 + 反应
        for stage_name in ["开战", "相持", "决战", "追击", "善后"]:
            stage_data = agent_outputs.get(stage_name, {})
            if not stage_data:
                continue
            print()
            print(f"  ── {stage_name} ──")
            _print_agent_section(
                config.attacker_name, stage_data.get("attacker_strategy", ""), "⚔"
            )
            _print_agent_section(
                config.defender_name, stage_data.get("defender_strategy", ""), "🛡"
            )
            print()
            _print_agent_section(
                config.attacker_name, stage_data.get("attacker_reaction", ""), "  ↳"
            )
            _print_agent_section(
                config.defender_name, stage_data.get("defender_reaction", ""), "  ↳"
            )

        # 战后反思
        refl = agent_outputs.get("reflection", {})
        if refl:
            print()
            print("  ── 战后反思 ──")
            _print_agent_section(config.attacker_name, refl.get("attacker_reflection", ""), "⚔")
            _print_agent_section(config.defender_name, refl.get("defender_reflection", ""), "🛡")

        print()
        print("═" * 58)

    # ---- 战报 ----
    print()
    narrative = generate(result)
    print(narrative)

    # ---- 统计 ----
    if use_llm and agent_outputs:
        atk_hist = config.attacker_agent.get_history() if config.attacker_agent else []
        def_hist = config.defender_agent.get_history() if config.defender_agent else []
        total_calls = len(atk_hist) + len(def_hist)
        print(f"\n  LLM 调用统计: {total_calls} 次 (攻{len(atk_hist)} + 守{len(def_hist)})")


if __name__ == "__main__":
    main()
