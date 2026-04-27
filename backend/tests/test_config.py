from backend.app.core.config import load_settings


def test_load_settings_returns_members():
    settings = load_settings()
    assert len(settings.members) == 16


def test_member_assignment_flags_are_loaded():
    settings = load_settings()
    for m in settings.members:
        assert m.active is True
        assert isinstance(m.assignable_day1, bool)
        assert isinstance(m.assignable_day2, bool)
        assert isinstance(m.assignable_night, bool)
    assert any(m.assignable_day1 for m in settings.members)
    assert any(m.assignable_day2 for m in settings.members)
    assert any(m.assignable_night for m in settings.members)


def test_schedule_config_defaults():
    settings = load_settings()
    assert settings.schedule.day_shift_weekdays == [5, 6]
    assert settings.schedule.night_shift_start_weekday == 0


def test_constraints_config():
    settings = load_settings()
    assert settings.constraints.day_min_interval > 0
    assert settings.constraints.night_cooldown_days >= 0
