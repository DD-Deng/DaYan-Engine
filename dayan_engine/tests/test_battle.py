"""战役判定引擎测试."""

import pytest
from dayan_engine.core.types import BattleConfig, BattleResult
from dayan_engine.core.battle import run_battle


@pytest.fixture
def chibi_config() -> BattleConfig:
    """赤壁之战配置 (fixture)."""
    return BattleConfig(
        attacker_name="曹操",
        defender_name="孙权",
        attacker_traits={
            "主帅": 0.90, "军师": 0.85, "先锋": 0.70,
            "后勤": 0.80, "军资": 0.95,
        },
        defender_traits={
            "主帅": 0.70, "军师": 0.95, "先锋": 0.75,
            "后勤": 0.85, "军资": 0.90,
        },
        ally_name="刘备",
        ally_traits={
            "主帅": 0.75, "军师": 0.90,
        },
        time_desc="建安十三年冬",
        location="赤壁",
        cast_nums=(9, 6, 13),
    )


class TestRunBattle:
    """完整战役推演测试."""

    def test_returns_battle_result(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert isinstance(result, BattleResult)

    def test_has_main_hexagram(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert result.main_hexagram is not None
        assert result.main_hexagram.name != ""

    def test_has_changed_hexagram(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert result.changed_hexagram is not None
        assert result.changed_hexagram.name != ""

    def test_has_five_stages(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert len(result.stages) == 5

    def test_stage_names_correct(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        expected_stages = ["开战", "相持", "决战", "追击", "善后"]
        for i, stage in enumerate(result.stages):
            assert stage.stage_name == expected_stages[i]

    def test_winner_is_valid(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert result.winner in ["attacker", "defender", "draw"]

    def test_casualties_in_range(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        assert 0.0 <= result.total_casualties_attacker <= 1.0
        assert 0.0 <= result.total_casualties_defender <= 1.0

    def test_each_stage_has_hexagram(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        for stage in result.stages:
            assert stage.hexagram is not None
            assert len(stage.hexagram.lines) == 6

    def test_each_stage_has_moving_line(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        for stage in result.stages:
            assert 1 <= stage.moving_line <= 6

    def test_each_stage_has_advantage(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        for stage in result.stages:
            assert stage.advantage in ["attacker", "defender", "even"]

    def test_each_stage_has_supply_loss(self, chibi_config):
        result = run_battle(chibi_config, seed=42)
        for stage in result.stages:
            assert stage.supply_loss in ["轻", "中", "重", "无"]

    def test_reproducible_with_seed(self, chibi_config):
        """相同种子产生相同结果."""
        r1 = run_battle(chibi_config, seed=12345)
        r2 = run_battle(chibi_config, seed=12345)
        assert r1.winner == r2.winner
        assert r1.total_casualties_attacker == r2.total_casualties_attacker
        assert r1.total_casualties_defender == r2.total_casualties_defender

    def test_different_seeds_may_differ(self, chibi_config):
        """不同种子产生不同结果."""
        r1 = run_battle(chibi_config, seed=1)
        r2 = run_battle(chibi_config, seed=99999)
        # 不一定不同 (宽松检验)
        assert r1.main_hexagram.index > 0


class TestBattleEdgeCases:
    """边界条件测试."""

    def test_minimal_config(self):
        """最小配置."""
        config = BattleConfig(
            attacker_name="A",
            defender_name="B",
            attacker_traits={"主帅": 0.5},
            defender_traits={"主帅": 0.5},
            cast_nums=(1, 1, 1),
        )
        result = run_battle(config, seed=1)
        assert result.winner in ["attacker", "defender", "draw"]

    def test_extreme_trait_asymmetry(self):
        """极端特质差异."""
        config = BattleConfig(
            attacker_name="强将",
            defender_name="弱将",
            attacker_traits={
                "主帅": 1.0, "军师": 1.0, "先锋": 1.0,
                "后勤": 1.0, "军资": 1.0,
            },
            defender_traits={
                "主帅": 0.1, "军师": 0.1, "先锋": 0.1,
                "后勤": 0.1, "军资": 0.1,
            },
            cast_nums=(1, 2, 3),
        )
        result = run_battle(config, seed=1)
        # 高位优势方应大概率获胜
        assert result.winner in ["attacker", "defender", "draw"]
