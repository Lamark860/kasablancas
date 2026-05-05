"""Базовый CRUD по моделям + relationships."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from vlad.models import NatalChart, Oracle, OracleEntry, Person, Plant, Recommendation


def test_person_create(db_session):
    p = Person(first_name="Анна", last_name="Иванова", birth_date="1990-03-05", eye_color="blue")
    db_session.add(p)
    db_session.commit()
    fetched = db_session.scalar(select(Person).where(Person.first_name == "Анна"))
    assert fetched is not None
    assert fetched.eye_color == "blue"
    assert fetched.created_at is not None


def test_plant_unique_slug(db_session):
    db_session.add(Plant(slug="willow", name_ru="Ива", category="tree"))
    db_session.commit()
    db_session.add(Plant(slug="willow", name_ru="Дубль", category="tree"))
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
    else:
        raise AssertionError("ожидался IntegrityError на дубль slug")


def test_oracle_with_entries(db_session):
    db_session.add(Plant(slug="willow", name_ru="Ива", category="tree"))
    db_session.add(Oracle(id="druid_tree", name_ru="Друиды", required_inputs=["birth_date"]))
    db_session.commit()

    db_session.add(
        OracleEntry(
            oracle_id="druid_tree",
            matcher={"type": "date_range", "from": "03-01", "to": "03-10"},
            plant_slug="willow",
            weight=1.0,
            reason_for_expert="Период Ивы",
        )
    )
    db_session.commit()

    oracle = db_session.get(Oracle, "druid_tree")
    assert len(oracle.entries) == 1
    assert oracle.entries[0].plant.name_ru == "Ива"


def test_recommendation_cascade(db_session):
    """Удаление Person каскадно удаляет его рекомендации и натальную карту."""
    person = Person(first_name="Тест", birth_date="2000-01-01")
    db_session.add(person)
    db_session.flush()
    db_session.add(
        Recommendation(
            person_id=person.id,
            input_snapshot={"first_name": "Тест"},
            active_oracles=["druid_tree"],
            raw_pool=[{"plant_slug": "willow", "matches": 1}],
        )
    )
    db_session.add(NatalChart(person_id=person.id, sun_sign="capricorn", full_chart={}))
    db_session.commit()

    db_session.delete(person)
    db_session.commit()
    assert db_session.scalar(select(Recommendation)) is None
    assert db_session.scalar(select(NatalChart)) is None


def test_eye_color_check_constraint(db_session):
    """SQLite в режиме PRAGMA foreign_keys + CheckConstraint должен ругнуться."""
    # Активируем check constraints (включены по умолчанию в современных версиях)
    db_session.add(Person(first_name="X", birth_date="2000-01-01", eye_color="purple"))
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
    else:
        raise AssertionError("ожидался IntegrityError на eye_color='purple'")
