"""五行生克模块测试."""

import pytest
from dayan_engine.core.wuxing import (
    generates, overcomes,
    generated_by, overcome_by,
    generated_element, overcome_element,
    element_of_stem, element_of_branch, element_of_trigram,
    relation_desc, TRIGRAM_NAMES,
)


class TestGenerates:
    """五行相生测试."""

    def test_wood_generates_fire(self):
        assert generates("木", "火") is True

    def test_fire_generates_earth(self):
        assert generates("火", "土") is True

    def test_earth_generates_metal(self):
        assert generates("土", "金") is True

    def test_metal_generates_water(self):
        assert generates("金", "水") is True

    def test_water_generates_wood(self):
        assert generates("水", "木") is True

    def test_not_generates_reverse(self):
        """反向不成立."""
        assert generates("火", "木") is False
        assert generates("土", "火") is False

    def test_not_generates_self(self):
        assert generates("木", "木") is False


class TestOvercomes:
    """五行相克测试."""

    def test_wood_overcomes_earth(self):
        assert overcomes("木", "土") is True

    def test_earth_overcomes_water(self):
        assert overcomes("土", "水") is True

    def test_water_overcomes_fire(self):
        assert overcomes("水", "火") is True

    def test_fire_overcomes_metal(self):
        assert overcomes("火", "金") is True

    def test_metal_overcomes_wood(self):
        assert overcomes("金", "木") is True

    def test_not_overcomes_reverse(self):
        assert overcomes("土", "木") is False
        assert overcomes("水", "土") is False


class TestDerivedRelations:
    """反向查询测试."""

    def test_generated_by(self):
        assert generated_by("火") == "木"
        assert generated_by("水") == "金"

    def test_overcome_by(self):
        assert overcome_by("土") == "木"
        assert overcome_by("火") == "水"

    def test_generated_element(self):
        assert generated_element("木") == "火"
        assert generated_element("金") == "水"

    def test_overcome_element(self):
        assert overcome_element("木") == "土"
        assert overcome_element("金") == "木"


class TestStemElement:
    """天干五行测试."""

    def test_jia_yi_wood(self):
        assert element_of_stem("甲") == "木"
        assert element_of_stem("乙") == "木"

    def test_bing_ding_fire(self):
        assert element_of_stem("丙") == "火"
        assert element_of_stem("丁") == "火"

    def test_wu_ji_earth(self):
        assert element_of_stem("戊") == "土"
        assert element_of_stem("己") == "土"

    def test_geng_xin_metal(self):
        assert element_of_stem("庚") == "金"
        assert element_of_stem("辛") == "金"

    def test_ren_gui_water(self):
        assert element_of_stem("壬") == "水"
        assert element_of_stem("癸") == "水"


class TestBranchElement:
    """地支五行测试."""

    def test_yin_mao_wood(self):
        assert element_of_branch("寅") == "木"
        assert element_of_branch("卯") == "木"

    def test_si_wu_fire(self):
        assert element_of_branch("巳") == "火"
        assert element_of_branch("午") == "火"

    def test_chen_xu_chou_wei_earth(self):
        for b in ["辰", "戌", "丑", "未"]:
            assert element_of_branch(b) == "土"

    def test_shen_you_metal(self):
        assert element_of_branch("申") == "金"
        assert element_of_branch("酉") == "金"

    def test_hai_zi_water(self):
        assert element_of_branch("亥") == "水"
        assert element_of_branch("子") == "水"


class TestTrigramElement:
    """八卦五行测试."""

    def test_qian_dui_metal(self):
        assert element_of_trigram(1) == "金"
        assert element_of_trigram(2) == "金"

    def test_zhen_xun_wood(self):
        assert element_of_trigram(4) == "木"
        assert element_of_trigram(5) == "木"

    def test_kan_water(self):
        assert element_of_trigram(6) == "水"

    def test_li_fire(self):
        assert element_of_trigram(3) == "火"

    def test_gen_kun_earth(self):
        assert element_of_trigram(7) == "土"
        assert element_of_trigram(8) == "土"


class TestRelationDesc:
    """五行关系描述测试."""

    def test_bihe(self):
        assert relation_desc("木", "木") == "比和"

    def test_wo_sheng_bi(self):
        assert relation_desc("木", "火") == "我生彼"

    def test_bi_sheng_wo(self):
        assert relation_desc("火", "木") == "彼生我"

    def test_wo_ke_bi(self):
        assert relation_desc("木", "土") == "我克彼"

    def test_bi_ke_wo(self):
        assert relation_desc("土", "木") == "彼克我"


class TestTrigramNames:
    """八卦名称测试."""

    def test_all_eight_names(self):
        assert TRIGRAM_NAMES[1] == "乾"
        assert TRIGRAM_NAMES[2] == "兑"
        assert TRIGRAM_NAMES[3] == "离"
        assert TRIGRAM_NAMES[4] == "震"
        assert TRIGRAM_NAMES[5] == "巽"
        assert TRIGRAM_NAMES[6] == "坎"
        assert TRIGRAM_NAMES[7] == "艮"
        assert TRIGRAM_NAMES[8] == "坤"
