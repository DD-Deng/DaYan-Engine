"""大衍引擎 Web 服务 — FastAPI 后端.

启动: python3 -m dayan_engine.web
"""

import os
import json
import random
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dayan_engine.core.types import BattleConfig, BattleResult
from dayan_engine.core.battle import run_battle
from dayan_engine.narrator.template_narrator import generate as generate_narrative
from dayan_engine.core.wuxing import (
    FIVE_ELEMENTS, TRIGRAM_NAMES, TRIGRAM_ELEMENT,
    generates, overcomes, relation_desc,
)
from dayan_engine.core.meihua import _HEXAGRAM_TABLE, _get_trigram
from dayan_engine.core.liuyao import build_hexagram

_TEMPLATE_DIR = Path(__file__).parent / "templates"
app = FastAPI(title="大衍引擎", version="0.1.0")


# ── Pydantic models ──

class BattleRequest(BaseModel):
    attacker_name: str = "曹操"
    defender_name: str = "孙权"
    attacker_traits: dict[str, float] = Field(default_factory=lambda: {
        "主帅": 0.90, "军师": 0.85, "先锋": 0.70,
        "后勤": 0.80, "军资": 0.95, "联盟": 0.30,
    })
    defender_traits: dict[str, float] = Field(default_factory=lambda: {
        "主帅": 0.70, "军师": 0.95, "先锋": 0.75,
        "后勤": 0.85, "军资": 0.90, "联盟": 0.70,
    })
    ally_name: str = ""
    ally_traits: dict[str, float] = Field(default_factory=dict)
    time_desc: str = "建安十三年冬"
    location: str = "赤壁"
    cast_num1: int = 9
    cast_num2: int = 6
    cast_num3: int = 13
    seed: Optional[int] = None
    method: str = "liuyao"
    use_llm: bool = False


def _serialize_result(result: BattleResult) -> dict:
    """将 BattleResult 序列化为 JSON 安全格式."""
    stages = []
    for s in result.stages:
        stages.append({
            "stage_name": s.stage_name,
            "hex_name": s.hexagram.name,
            "hex_index": s.hexagram.index,
            "hex_upper": s.hexagram.upper.name,
            "hex_lower": s.hexagram.lower.name,
            "hex_element": s.hexagram.lower.element,
            "moving_line": s.moving_line,
            "yongshen_status": s.yongshen_status,
            "advantage": s.advantage,
            "casualties_attacker": s.casualties_attacker,
            "casualties_defender": s.casualties_defender,
            "supply_loss": s.supply_loss,
            "turning_point": s.turning_point,
        })

    return {
        "winner": result.winner,
        "attacker_name": result.config.attacker_name,
        "defender_name": result.config.defender_name,
        "time_desc": result.config.time_desc,
        "location": result.config.location,
        "total_casualties_attacker": result.total_casualties_attacker,
        "total_casualties_defender": result.total_casualties_defender,
        "main_hexagram": {
            "name": result.main_hexagram.name,
            "index": result.main_hexagram.index,
            "upper": result.main_hexagram.upper.name,
            "lower": result.main_hexagram.lower.name,
            "element": result.main_hexagram.lower.element,
            "palace": result.main_hexagram.palace,
            "lines": [
                {
                    "position": ln.position,
                    "is_yang": ln.is_yang,
                    "six_relation": ln.six_relation,
                    "element": ln.element,
                    "earthly_branch": ln.earthly_branch,
                    "shi_ying": ln.shi_ying,
                    "is_moving": ln.is_moving,
                }
                for ln in result.main_hexagram.lines
            ],
        },
        "changed_hexagram": {
            "name": result.changed_hexagram.name,
            "index": result.changed_hexagram.index,
            "upper": result.changed_hexagram.upper.name,
            "lower": result.changed_hexagram.lower.name,
        },
        "stages": stages,
        "narrative": generate_narrative(result),
        "agent_outputs": result.agent_outputs if result.agent_outputs else {},
    }


# ── API endpoints ──

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = _TEMPLATE_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>大衍引擎</h1><p>模板文件未找到</p>")


@app.post("/api/battle/run")
async def api_run_battle(req: BattleRequest):
    """运行一场战役推演."""
    config = BattleConfig(
        attacker_name=req.attacker_name,
        defender_name=req.defender_name,
        attacker_traits=req.attacker_traits,
        defender_traits=req.defender_traits,
        ally_name=req.ally_name,
        ally_traits=req.ally_traits,
        time_desc=req.time_desc,
        location=req.location,
        cast_nums=(req.cast_num1, req.cast_num2, req.cast_num3),
    )

    if req.use_llm:
        try:
            from dayan_engine.agents.llm_agent import LLMAgent
            config.attacker_agent = LLMAgent(
                config.attacker_name, config.attacker_traits,
                style=f"{config.attacker_name}的战术风格",
            )
            config.defender_agent = LLMAgent(
                config.defender_name, config.defender_traits,
                style=f"{config.defender_name}的战术风格",
            )
        except Exception:
            pass

    result = run_battle(config, seed=req.seed, method=req.method)
    return JSONResponse(_serialize_result(result))


@app.get("/api/hexagram/{index}")
async def api_hexagram_detail(index: int):
    """返回单个卦的详细信息."""
    if index < 1 or index > 64:
        return JSONResponse({"error": "卦序需在 1-64 之间"}, status_code=400)

    upper_idx, lower_idx, name = _HEXAGRAM_TABLE[index - 1]
    hexagram = build_hexagram(upper_idx, lower_idx)

    return JSONResponse({
        "index": index,
        "name": name,
        "upper": {"index": upper_idx, "name": TRIGRAM_NAMES[upper_idx], "element": TRIGRAM_ELEMENT[upper_idx]},
        "lower": {"index": lower_idx, "name": TRIGRAM_NAMES[lower_idx], "element": TRIGRAM_ELEMENT[lower_idx]},
        "palace": hexagram.palace,
        "shi_position": hexagram.shi_position,
        "ying_position": hexagram.ying_position,
        "lines": [
            {
                "position": ln.position,
                "is_yang": ln.is_yang,
                "heavenly_stem": ln.heavenly_stem,
                "earthly_branch": ln.earthly_branch,
                "element": ln.element,
                "six_relation": ln.six_relation,
                "shi_ying": ln.shi_ying,
            }
            for ln in hexagram.lines
        ],
    })


@app.get("/api/hexagrams")
async def api_hexagrams_list():
    """返回全部 64 卦的基本信息."""
    result = []
    for idx, (upper_idx, lower_idx, name) in enumerate(_HEXAGRAM_TABLE, start=1):
        result.append({
            "index": idx,
            "name": name,
            "upper": TRIGRAM_NAMES[upper_idx],
            "lower": TRIGRAM_NAMES[lower_idx],
            "upper_element": TRIGRAM_ELEMENT[upper_idx],
            "lower_element": TRIGRAM_ELEMENT[lower_idx],
        })
    return JSONResponse(result)


@app.get("/api/reference/wuxing")
async def api_wuxing_reference():
    return JSONResponse({
        "elements": ["木", "火", "土", "金", "水"],
        "generates": [{"from": k, "to": v} for k, v in [
            ("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木"),
        ]],
        "overcomes": [{"from": k, "to": v} for k, v in [
            ("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木"),
        ]],
    })


@app.get("/api/trigrams")
async def api_trigrams():
    return JSONResponse([
        {"index": i, "name": TRIGRAM_NAMES[i], "element": TRIGRAM_ELEMENT[i]}
        for i in range(1, 9)
    ])


def run(host: str = "0.0.0.0", port: int = 8080):
    import uvicorn
    print(f"  大衍引擎 Web 服务启动: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
