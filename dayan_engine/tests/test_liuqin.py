"""六亲配位模块测试."""

import pytest
from dayan_engine.core.types import Line
from dayan_engine.core.liuqin import assign_six_relations, LIUQIN_BATTLE_ROLE


def _make_line(position: int, element: str) -> Line:
    """快速创建测试用爻."""
    return Line(position=position, is_yang=True, element=element)


class TestAssignSixRelations:
    """六亲分配测试."""

    def test_parents_relation(self):
        """生我者 → 父母."""
        lines = [_make_line(1, "火")]  # 火生土
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "父母"

    def test_children_relation(self):
        """我生者 → 子孙."""
        lines = [_make_line(1, "金")]  # 土生金
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "子孙"

    def test_brothers_relation(self):
        """同我者 → 兄弟."""
        lines = [_make_line(1, "土")]  # 土同土
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "兄弟"

    def test_wealth_relation(self):
        """我克者 → 妻财."""
        lines = [_make_line(1, "水")]  # 土克水
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "妻财"

    def test_officer_relation(self):
        """克我者 → 官鬼."""
        lines = [_make_line(1, "木")]  # 木克土
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "官鬼"

    def test_multiple_lines(self):
        """多个爻同时分配."""
        lines = [
            _make_line(1, "火"),  # 父母
            _make_line(2, "金"),  # 子孙
            _make_line(3, "土"),  # 兄弟
            _make_line(4, "水"),  # 妻财
            _make_line(5, "木"),  # 官鬼
            _make_line(6, "土"),  # 兄弟
        ]
        result = assign_six_relations(lines, "土")
        assert result[0].six_relation == "父母"
        assert result[1].six_relation == "子孙"
        assert result[2].six_relation == "兄弟"
        assert result[3].six_relation == "妻财"
        assert result[4].six_relation == "官鬼"
        assert result[5].six_relation == "兄弟"

    def test_empty_element_handled(self):
        """无五行的爻不报错."""
        ln = Line(position=1, is_yang=True, element="")
        result = assign_six_relations([ln], "土")
        assert result[0].six_relation == ""


class TestLiuqinBattleRole:
    """六亲战役角色测试."""

    def test_all_five_relations_have_role(self):
        for relation in ["父母", "兄弟", "子孙", "妻财", "官鬼"]:
            assert relation in LIUQIN_BATTLE_ROLE

    def test_parents_is_logistics(self):
        assert "后勤" in LIUQIN_BATTLE_ROLE["父母"]

    def test_children_is_vanguard(self):
        assert "先锋" in LIUQIN_BATTLE_ROLE["子孙"]
