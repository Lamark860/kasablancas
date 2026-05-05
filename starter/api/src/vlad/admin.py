"""sqladmin views для всех ORM-моделей.

Подключается из main.py через setup_admin(app, engine).
"""
from sqladmin import Admin, ModelView

from vlad.models import (
    NatalChart,
    Oracle,
    OracleEntry,
    Person,
    Plant,
    Recommendation,
)


class PersonAdmin(ModelView, model=Person):
    name = "Клиент"
    name_plural = "Клиенты"
    icon = "fa-solid fa-user"
    column_list = [Person.id, Person.first_name, Person.last_name, Person.birth_date, Person.eye_color]
    column_searchable_list = [Person.first_name, Person.last_name]
    column_sortable_list = [Person.id, Person.created_at]


class PlantAdmin(ModelView, model=Plant):
    name = "Растение"
    name_plural = "Растения"
    icon = "fa-solid fa-seedling"
    column_list = [
        Plant.id,
        Plant.slug,
        Plant.name_ru,
        Plant.category,
        Plant.min_zone_usda,
        Plant.element,
    ]
    column_searchable_list = [Plant.slug, Plant.name_ru, Plant.name_lat]
    column_sortable_list = [Plant.id, Plant.slug, Plant.name_ru]


class OracleAdmin(ModelView, model=Oracle):
    name = "Оракул"
    name_plural = "Оракулы"
    icon = "fa-solid fa-compass"
    column_list = [Oracle.id, Oracle.name_ru, Oracle.active, Oracle.weight, Oracle.sort_order]
    column_sortable_list = [Oracle.sort_order, Oracle.id]


class OracleEntryAdmin(ModelView, model=OracleEntry):
    name = "Соответствие"
    name_plural = "Соответствия"
    icon = "fa-solid fa-link"
    column_list = [
        OracleEntry.id,
        OracleEntry.oracle_id,
        OracleEntry.plant_slug,
        OracleEntry.weight,
        OracleEntry.role,
    ]
    column_searchable_list = [OracleEntry.oracle_id, OracleEntry.plant_slug]


class RecommendationAdmin(ModelView, model=Recommendation):
    name = "Рекомендация"
    name_plural = "Рекомендации"
    icon = "fa-solid fa-list"
    column_list = [
        Recommendation.id,
        Recommendation.person_id,
        Recommendation.title_plant_slug,
        Recommendation.created_at,
    ]


class NatalChartAdmin(ModelView, model=NatalChart):
    name = "Натальная карта"
    name_plural = "Натальные карты"
    icon = "fa-solid fa-star"
    column_list = [
        NatalChart.person_id,
        NatalChart.sun_sign,
        NatalChart.moon_sign,
        NatalChart.calculated_at,
    ]


def setup_admin(app, engine) -> Admin:
    admin = Admin(app, engine, title="Vlad rev1 — админка")
    admin.add_view(PersonAdmin)
    admin.add_view(PlantAdmin)
    admin.add_view(OracleAdmin)
    admin.add_view(OracleEntryAdmin)
    admin.add_view(RecommendationAdmin)
    admin.add_view(NatalChartAdmin)
    return admin
