"""奇门遁甲模块测试."""

import pytest
from dayan_engine.core.qimen import (
    arrange_qimen_plate,
    qimen_stage_judgment,
    _get_solar_term_index,
    _determine_dun_type,
    _determine_ju_and_yuan,
    _arrange_di_pan,
    _assess_palace_ji_xiong,
    JIU_GONG, BA_MEN, JIU_XING, BA_SHEN,
    QimenPalaceData,
)


class TestSolarTerms:
    def test_winter_solstice(self):
        idx = _get_solar_term_index(12, 22)
        assert idx == 0

    def test_summer_solstice(self):
        idx = _get_solar_term_index(6, 22)
        assert idx == 12

    def test_spring_equinox(self):
        idx = _get_solar_term_index(3, 21)
        assert idx in (5, 6)


class TestYangYinDun:
    def test_yang_dun_after_winter(self):
        assert _determine_dun_type(0) == "阳遁"

    def test_yin_dun_after_summer(self):
        assert _determine_dun_type(12) == "阴遁"

    def test_yang_dun_spring(self):
        assert _determine_dun_type(6) == "阳遁"

    def test_yin_dun_autumn(self):
        assert _determine_dun_type(18) == "阴遁"


class TestJuNumber:
    def test_returns_valid_ju(self):
        ju, yuan = _determine_ju_and_yuan(208, 11, 20, 10, "阳遁")
        assert 1 <= ju <= 9
        assert yuan in ("上元", "中元", "下元")

    def test_yang_dun_ju(self):
        ju, _ = _determine_ju_and_yuan(208, 12, 22, 0, "阳遁")
        assert 1 <= ju <= 9

    def test_yin_dun_ju(self):
        ju, _ = _determine_ju_and_yuan(208, 6, 22, 0, "阴遁")
        assert 1 <= ju <= 9


class TestArrangeDiPan:
    def test_all_nine_palaces(self):
        di_pan = _arrange_di_pan(1, "阳遁")
        assert len(di_pan) == 9
        for i in range(1, 10):
            assert i in di_pan

    def test_yang_dun_order(self):
        di_pan = _arrange_di_pan(1, "阳遁")
        assert di_pan[1] == "戊"  # 阳遁1局, 戊在坎1

    def test_yin_dun_reverse(self):
        di_pan = _arrange_di_pan(1, "阴遁")
        assert di_pan[1] == "戊"  # 阴遁1局, 戊在坎1, 但逆排
        assert di_pan[9] == "己"  # 逆排: 己在离9


class TestArrangePlate:
    def test_returns_valid_plate(self):
        plate = arrange_qimen_plate(208, 11, 20, 10)
        assert plate.dun_type in ("阳遁", "阴遁")
        assert 1 <= plate.ju_number <= 9
        assert plate.yuan in ("上元", "中元", "下元")
        assert len(plate.solar_term) > 0

    def test_has_all_palaces(self):
        plate = arrange_qimen_plate(208, 11, 20, 10)
        assert len(plate.palaces) == 9
        for i in range(1, 10):
            assert i in plate.palaces

    def test_palaces_have_data(self):
        plate = arrange_qimen_plate(208, 11, 20, 10)
        for pi in range(1, 10):
            p = plate.palaces[pi]
            assert p.palace_index == pi
            assert len(p.direction) > 0
            assert len(p.element) > 0
            assert len(p.di_pan_stem) > 0
            assert len(p.ji_xiong) > 0

    def test_reproducible(self):
        p1 = arrange_qimen_plate(208, 11, 20, 10)
        p2 = arrange_qimen_plate(208, 11, 20, 10)
        assert p1.ju_number == p2.ju_number
        assert p1.dun_type == p2.dun_type

    def test_different_time_different_plate(self):
        p1 = arrange_qimen_plate(208, 6, 15, 8)
        p2 = arrange_qimen_plate(208, 12, 15, 8)
        # 夏/冬不同节气, 遁别不同
        assert p1.dun_type != p2.dun_type or p1.ju_number != p2.ju_number


class TestJiXiong:
    def test_returns_valid_ji_xiong(self):
        pd = QimenPalaceData(
            palace_index=1,
            direction="北",
            element="水",
            di_pan_stem="戊",
            tian_pan_stem="乙",
            ren_pan_door="休门",
            shen_pan_spirit="值符",
            tian_pan_star="天蓬",
        )
        result = _assess_palace_ji_xiong(pd)
        assert result in ("大吉", "吉", "平", "凶", "大凶")

    def test_lucky_door_star_gives_ji(self):
        pd = QimenPalaceData(
            palace_index=1, direction="北", element="水",
            di_pan_stem="戊", tian_pan_stem="乙",
            ren_pan_door="开门",
            shen_pan_spirit="值符",
            tian_pan_star="天心",
        )
        result = _assess_palace_ji_xiong(pd)
        assert result in ("大吉", "吉")


class TestBattleIntegration:
    def test_returns_valid_judgment(self):
        plate = arrange_qimen_plate(208, 11, 20, 10)
        result = qimen_stage_judgment(plate, "开战", "金", "水")
        assert result["advantage"] in ("attacker", "defender", "even")
        assert 0.0 <= result["casualties_attacker"] <= 1.0
        assert 0.0 <= result["casualties_defender"] <= 1.0
        assert result["supply_loss"] in ("无", "轻", "中", "重")
        assert len(result["turning_point"]) > 0

    def test_all_stages(self):
        plate = arrange_qimen_plate(208, 11, 20, 10)
        for stage in ("开战", "相持", "决战", "追击", "善后"):
            result = qimen_stage_judgment(plate, stage, "金", "水")
            assert result["advantage"] in ("attacker", "defender", "even")


class TestDataIntegrity:
    def test_jiu_gong_count(self):
        assert len(JIU_GONG) == 9

    def test_ba_men_count(self):
        assert len(BA_MEN) == 8

    def test_jiu_xing_count(self):
        assert len(JIU_XING) == 9

    def test_ba_shen_count(self):
        assert len(BA_SHEN) == 8
