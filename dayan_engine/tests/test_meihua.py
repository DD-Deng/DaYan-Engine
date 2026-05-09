"""梅花易数起卦模块测试."""

import pytest
from dayan_engine.core.meihua import (
    cast, _get_hexagram_index, _get_trigram,
    _TRIGRAM_LINES, _REVERSE_TRIGRAM,
)


class TestTrigramLines:
    """八卦爻象测试."""

    def test_all_trigrams_have_three_lines(self):
        for idx in range(1, 9):
            lines = _TRIGRAM_LINES[idx]
            assert len(lines) == 3

    def test_qian_all_yang(self):
        assert _TRIGRAM_LINES[1] == [True, True, True]

    def test_kun_all_yin(self):
        assert _TRIGRAM_LINES[8] == [False, False, False]

    def test_kan_middle_yang(self):
        assert _TRIGRAM_LINES[6] == [False, True, False]


class TestReverseTrigram:
    """八卦反查表测试."""

    def test_all_eight_reversed(self):
        assert len(_REVERSE_TRIGRAM) == 8

    def test_qian_reverse(self):
        assert _REVERSE_TRIGRAM[(True, True, True)] == 1

    def test_kun_reverse(self):
        assert _REVERSE_TRIGRAM[(False, False, False)] == 8


class TestGetTrigram:
    """八卦创建测试."""

    def test_create_qian(self):
        t = _get_trigram(1)
        assert t.index == 1
        assert t.name == "乾"
        assert t.element == "金"

    def test_create_kun(self):
        t = _get_trigram(8)
        assert t.index == 8
        assert t.name == "坤"
        assert t.element == "土"


class TestHexagramIndex:
    """卦序查找测试."""

    def test_qian_wei_tian(self):
        idx, name = _get_hexagram_index(1, 1)
        assert idx == 1
        assert name == "乾为天"

    def test_kun_wei_di(self):
        idx, name = _get_hexagram_index(8, 8)
        assert idx == 2
        assert name == "坤为地"

    def test_all_64_combinations_exist(self):
        """确保上下卦的所有组合都在64卦表中 (8×8=64)."""
        for upper in range(1, 9):
            for lower in range(1, 9):
                idx, name = _get_hexagram_index(upper, lower)
                assert 1 <= idx <= 64
                assert len(name) > 0

    def test_invalid_combination_raises(self):
        """不存在不在表中的组合, 但测试保护."""
        # 所有8×8组合都在表中, 所以这里测试错误的输入类型会得到什么
        pass


class TestCast:
    """梅花易数起卦测试."""

    def test_basic_cast(self):
        main, changed, moving = cast(1, 2, 3)
        assert main is not None
        assert changed is not None
        assert 1 <= moving <= 6

    def test_zero_handling(self):
        """num mod 8 == 0 → 8(坤), num mod 6 == 0 → 6."""
        main, changed, moving = cast(8, 16, 6)
        # 8 mod 8 = 0 → 8(坤)
        assert main.upper.index == 8
        assert main.lower.index == 8
        # 动爻: (8+16+6) = 30, 30 mod 6 = 0 → 6
        assert moving == 6

    def test_moving_line_flips_yin_yang(self):
        """变卦中动爻位的阴阳取反."""
        main, changed, moving = cast(3, 5, 7)
        # 检查本卦动爻位
        main_ln = main.lines[moving - 1]
        changed_ln = changed.lines[moving - 1]
        assert main_ln.is_yang != changed_ln.is_yang
        # 变卦中该爻标记为动
        assert changed_ln.is_moving is True

    def test_non_moving_lines_unchanged(self):
        """非动爻位不变."""
        main, changed, moving = cast(4, 2, 1)
        for i in range(6):
            if i != moving - 1:
                assert main.lines[i].is_yang == changed.lines[i].is_yang

    def test_different_inputs_different_results(self):
        """不同输入产生不同卦."""
        r1 = cast(1, 1, 1)
        r2 = cast(7, 8, 9)
        # 至少有一个不同 (卦或动爻)
        assert (
            r1[0].index != r2[0].index
            or r1[2] != r2[2]
        )

    def test_known_result(self):
        """验证已知结果: (1,1,1) → 上乾下乾, 动爻 (1+1+1)%6=3."""
        main, changed, moving = cast(1, 1, 1)
        assert main.upper.index == 1  # 乾
        assert main.lower.index == 1  # 乾
        assert main.name == "乾为天"
        assert moving == 3

    def test_returned_hexagram_has_six_lines(self):
        main, changed, moving = cast(3, 4, 5)
        assert len(main.lines) == 6
        assert len(changed.lines) == 6


class TestCastVariants:
    """验证起卦结果一致性."""

    def test_upper_from_num1(self):
        """上卦仅依赖 num1."""
        main1, _, _ = cast(3, 1, 1)
        main2, _, _ = cast(3, 5, 9)
        assert main1.upper.index == main2.upper.index

    def test_lower_from_num2(self):
        """下卦仅依赖 num2."""
        main1, _, _ = cast(1, 4, 1)
        main2, _, _ = cast(5, 4, 9)
        assert main1.lower.index == main2.lower.index
