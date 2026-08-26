from datetime import date

from app.features.task_course.course_service import CourseService

_HEADER = "weekday,start_time,end_time,name,room\n"


def _write_csv(tmp_path, rows: list[str]) -> str:
    path = tmp_path / "courses.csv"
    path.write_text(_HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


def test_import_valid_rows(tmp_path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "1,08:00,09:40,高等数学,N101",
            "3,10:00,11:40,大学英语,N202",
        ],
    )
    service = CourseService(db_path=tmp_path / "db.sqlite")

    assert service.import_csv(path) == 2
    week = service.list_week()
    assert [c.name for c in week] == ["高等数学", "大学英语"]
    assert week[0].weekday == 1
    assert week[0].room == "N101"


def test_import_skips_bad_rows(tmp_path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "1,08:00,09:40,正常课程,N101",
            "9,08:00,09:40,星期越界,N101",
            "2,25:00,26:00,时间非法,N101",
            "3,,10:00,缺少开始时间,N101",
            "4,14:00,15:40,,机房3",
            "not-a-number,14:00,15:40,星期非数字,机房3",
        ],
    )
    service = CourseService(db_path=tmp_path / "db.sqlite")

    assert service.import_csv(path) == 1
    assert [c.name for c in service.list_week()] == ["正常课程"]


def test_import_tolerates_missing_optional_fields(tmp_path) -> None:
    path = _write_csv(tmp_path, ["5,14:00,,计算机基础,"])
    service = CourseService(db_path=tmp_path / "db.sqlite")

    assert service.import_csv(path) == 1
    course = service.list_week()[0]
    assert course.end_time == ""
    assert course.room == ""


def test_import_handles_bom_and_bad_end_time(tmp_path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text("\ufeff" + _HEADER + "2,09:00,坏时间,线性代数,\n", encoding="utf-8")
    service = CourseService(db_path=tmp_path / "db.sqlite")

    assert service.import_csv(str(path)) == 1
    assert service.list_week()[0].end_time == ""


def test_import_replaces_previous_data(tmp_path) -> None:
    service = CourseService(db_path=tmp_path / "db.sqlite")
    first = _write_csv(tmp_path, ["1,08:00,09:40,旧课,N101"])
    service.import_csv(first)

    second = tmp_path / "new.csv"
    second.write_text(_HEADER + "2,10:00,11:00,新课,N202\n", encoding="utf-8")
    assert service.import_csv(str(second)) == 1
    assert [c.name for c in service.list_week()] == ["新课"]


def test_list_week_sorted_by_weekday_and_time(tmp_path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "3,10:00,11:40,大学英语",
            "1,14:00,15:40,下午课",
            "1,08:00,09:40,早课",
        ],
    )
    service = CourseService(db_path=tmp_path / "db.sqlite")
    service.import_csv(path)

    assert [c.name for c in service.list_week()] == ["早课", "下午课", "大学英语"]


def test_list_tomorrow_filters_by_weekday(tmp_path) -> None:
    path = _write_csv(
        tmp_path,
        [
            "2,08:00,09:40,周二课",
            "3,10:00,11:40,周三课",
        ],
    )
    service = CourseService(db_path=tmp_path / "db.sqlite")
    service.import_csv(path)

    # 2026-08-24 是周一，明天周二
    assert [c.name for c in service.list_tomorrow(date(2026, 8, 24))] == ["周二课"]
    # 2026-08-26 是周三，明天周四，无课
    assert service.list_tomorrow(date(2026, 8, 26)) == []
