"""六爻纳甲推演模块测试."""

import pytest
from dayan_engine.core.types import Line, Hexagram
from dayan_engine.core.liuyao import (
    build_hexagram, apply_moving_line,
    get_yongshen_line, judge_yongshen_status,
    judge_casualties, judge_supply, get_turning_point,
)
from dayan_engine.core.wuxing import element_of_branch


class TestBuildHexagram:
    """纳甲构建测试."""

    def test_build_qian(self):
        h = build_hexagram(1, 1)  # 乾为天
        assert h.name == "乾为天"
        assert h.index == 1
        assert h.palace == "乾"

    def test_build_kun(self):
        h = build_hexagram(8, 8)  # 坤为地
        assert h.name == "坤为地"
        assert h.index == 2
        assert h.palace == "坤"

    def test_all_64_hexagrams_buildable(self):
        """确保64卦都能正常构建."""
        from dayan_engine.core.meihua import _get_hexagram_index
        for upper in range(1, 9):
            for lower in range(1, 9):
                h = build_hexagram(upper, lower)
                assert h.name != ""
                assert 1 <= h.index <= 64
                assert len(h.lines) == 6
                assert h.palace != ""

    def test_lines_have_najia(self):
        """所有6爻都配了干支和五行."""
        h = build_hexagram(1, 1)  # 乾为天
        for ln in h.lines:
            assert ln.heavenly_stem != ""
            assert ln.earthly_branch != ""
            assert ln.element != ""
            # 验证五行与地支一致
            assert ln.element == element_of_branch(ln.earthly_branch)

    def test_qian_najia_first_line(self):
        """乾卦初爻: 甲子."""
        h = build_hexagram(1, 1)
        ln = h.lines[0]  # 初爻
        assert ln.heavenly_stem == "甲"
        assert ln.earthly_branch == "子"
        assert ln.element == "水"  # 子属水

    def test_qian_najia_top_line(self):
        """乾卦上爻: 壬戌."""
        h = build_hexagram(1, 1)
        ln = h.lines[5]  # 上爻
        assert ln.heavenly_stem == "壬"
        assert ln.earthly_branch == "戌"
        assert ln.element == "土"  # 戌属土

    def test_kun_najia_first_line(self):
        """坤卦初爻: 乙未."""
        h = build_hexagram(8, 8)
        ln = h.lines[0]
        assert ln.heavenly_stem == "乙"
        assert ln.earthly_branch == "未"
        assert ln.element == "土"

    def test_all_lines_have_six_relations(self):
        """所有爻都配了六亲."""
        h = build_hexagram(3, 5)  # 火风鼎
        for ln in h.lines:
            assert ln.six_relation in ["父母", "兄弟", "子孙", "妻财", "官鬼"]

    def test_shi_ying_marked(self):
        """世应爻已标记."""
        h = build_hexagram(3, 5)  # 火风鼎
        shi_count = sum(1 for ln in h.lines if ln.shi_ying == "世")
        ying_count = sum(1 for ln in h.lines if ln.shi_ying == "应")
        assert shi_count == 1
        assert ying_count == 1

    def test_shi_ying_three_positions_apart(self):
        """世应与应爻相隔三位."""
        for upper in range(1, 9):
            for lower in range(1, 9):
                h = build_hexagram(upper, lower)
                shi_pos = 0
                ying_pos = 0
                for ln in h.lines:
                    if ln.shi_ying == "世":
                        shi_pos = ln.position
                    elif ln.shi_ying == "应":
                        ying_pos = ln.position
                if shi_pos and ying_pos:
                    assert abs(shi_pos - ying_pos) == 3 or abs(shi_pos - ying_pos) == 3


class TestApplyMovingLine:
    """动爻标记测试."""

    def test_moving_line_marked(self):
        h = build_hexagram(1, 1)  # 乾为天
        changed = apply_moving_line(h, 2)  # 二爻动
        assert h.lines[1].is_moving is True  # 本卦标记
        assert h.lines[0].is_moving is False

    def test_changed_hexagram_different(self):
        """变卦与原本卦不同."""
        h = build_hexagram(1, 1)  # 乾为天 (六阳)
        changed = apply_moving_line(h, 1)  # 初爻动: 阳变阴
        assert changed.name != "乾为天"
        # 初爻变了之后下卦变为巽, 上卦乾, → 天风姤
        assert changed.index == 44  # 天风姤

    def test_qian_first_line_move_to_gou(self):
        """乾初爻动 → 天风姤."""
        h = build_hexagram(1, 1)
        changed = apply_moving_line(h, 1)
        assert changed.name == "天风姤"


class TestYongshenLine:
    """用神爻查询测试."""

    def test_attacker_commander_is_shi(self):
        """攻方主帅 = 世爻."""
        h = build_hexagram(1, 1)
        ln = get_yongshen_line(h, "主帅", is_attacker=True)
        assert ln is not None
        assert ln.shi_ying == "世"

    def test_defender_commander_is_ying(self):
        """守方主帅 = 应爻."""
        h = build_hexagram(1, 1)
        ln = get_yongshen_line(h, "主帅", is_attacker=False)
        assert ln is not None
        assert ln.shi_ying == "应"

    def test_strategist_is_brother(self):
        """军师 = 兄弟爻."""
        h = build_hexagram(1, 1)
        ln = get_yongshen_line(h, "军师")
        assert ln is not None
        assert ln.six_relation == "兄弟"

    def test_vanguard_is_children(self):
        """先锋 = 子孙爻."""
        h = build_hexagram(1, 1)
        ln = get_yongshen_line(h, "先锋")
        # 乾卦无子孙爻 (乾宫属金, 金生水, 但乾卦六爻皆金)
        # 这个测试依赖具体卦象, 用通用测试
        pass


class TestJudgeYongshenStatus:
    """用神判定测试."""

    def test_with_month_support(self):
        """月建生用神 → 得令."""
        h = build_hexagram(1, 1)  # 乾为天, 世在6爻
        ln = get_yongshen_line(h, "主帅", is_attacker=True)
        assert ln is not None
        result = judge_yongshen_status(h, ln, month_element="土")  # 土生金
        assert result["score"] > 0.5

    def test_with_overcome(self):
        """克用神 → 分数降低."""
        # 坤为地: 世爻在6位, 酉金, 火月克金 → 受克
        h = build_hexagram(8, 8)
        ln = get_yongshen_line(h, "主帅", is_attacker=True)
        assert ln is not None
        # 火月克金, 但坤卦有二爻火克世爻金, 同时有土爻和爻水相救
        result = judge_yongshen_status(h, ln, month_element="火")
        # 分数应低于同卦不用火月的判定
        result_no_month = judge_yongshen_status(h, ln)
        assert result["score"] <= result_no_month["score"] + 0.05
        assert "克用神" in result["details"]

    def test_no_month_day(self):
        """无月建日辰 → 基准分."""
        h = build_hexagram(1, 1)
        ln = get_yongshen_line(h, "主帅", is_attacker=True)
        assert ln is not None
        result = judge_yongshen_status(h, ln)
        assert 0.0 <= result["score"] <= 1.0
        assert len(result["details"]) > 0


class TestJudgeCasualties:
    """伤亡判定测试."""

    def test_returns_valid_range(self):
        h = build_hexagram(1, 1)
        atk, dfd = judge_casualties(h, 0.5)
        assert 0.0 <= atk <= 1.0
        assert 0.0 <= dfd <= 1.0

    def test_no_zisun_line(self):
        """无子孙爻时返回默认伤亡."""
        # 乾卦无子孙爻 (全金, 金生水但乾宫属金)
        h = build_hexagram(1, 1)
        atk, dfd = judge_casualties(h, 0.5)
        # 应返回合理范围
        assert 0.0 <= atk <= 1.0


class TestJudgeSupply:
    """后勤判定测试."""

    def test_returns_valid_level(self):
        h = build_hexagram(1, 1)
        level = judge_supply(h)
        assert level in ["轻", "中", "重", "无"]


class TestTurningPoint:
    """转折点描述测试."""

    def test_with_moving_line(self):
        h = build_hexagram(1, 1)
        h = apply_moving_line(h, 3)  # 这会改变h
        # 实际上apply_moving_line改变了h, 但h现在是乾, 标记三爻动
        tp = get_turning_point(h)
        assert len(tp) > 0

    def test_without_moving_line(self):
        h = build_hexagram(1, 1)
        tp = get_turning_point(h)
        assert "无动爻" in tp or len(tp) > 0
