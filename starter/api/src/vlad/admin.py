"""sqladmin views для всех ORM-моделей.

Подключается из main.py через setup_admin(app, engine).
"""
from __future__ import annotations

from sqladmin import Admin, BaseView, ModelView, expose
from starlette.requests import Request
from starlette.responses import HTMLResponse
from wtforms import IntegerField, SelectField, StringField, validators

from vlad.db import SessionLocal
from vlad.dump_seed import SEED_DIR, dump_all
from vlad.models import (
    NatalChart,
    Oracle,
    OracleEntry,
    Person,
    Plant,
    Recommendation,
)


# --- Справочники для форм OracleEntry ---------------------------------

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]
EYE_COLORS = ["blue", "grey", "green", "hazel", "brown", "dark", "amber"]

MATCHER_TYPES = [
    ("date_range_yearly", "Период (даты от/до, ежегодно)"),
    ("zodiac_sign", "Знак зодиака"),
    ("name_pythagorean_number", "Число имени (Пифагор)"),
    ("eye_color", "Цвет глаз"),
    ("name_match", "Имя клиента"),
]

_VIRTUAL_MATCHER_KEYS = (
    "matcher_type",
    "matcher_from",
    "matcher_to",
    "matcher_sign",
    "matcher_number",
    "matcher_color",
    "matcher_name",
)


def _build_matcher(data: dict) -> dict | None:
    """Собрать matcher-dict из плоских виртуальных полей формы."""
    mt = (data.get("matcher_type") or "").strip()
    if mt == "date_range_yearly":
        return {
            "type": mt,
            "from": (data.get("matcher_from") or "").strip(),
            "to": (data.get("matcher_to") or "").strip(),
        }
    if mt == "zodiac_sign":
        return {"type": mt, "sign": (data.get("matcher_sign") or "").strip()}
    if mt == "name_pythagorean_number":
        n = data.get("matcher_number")
        return {"type": mt, "number": int(n) if n not in (None, "") else None}
    if mt == "eye_color":
        return {"type": mt, "color": (data.get("matcher_color") or "").strip()}
    if mt == "name_match":
        return {"type": mt, "name": (data.get("matcher_name") or "").strip()}
    return None


# --- ModelViews -------------------------------------------------------


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

    form_args = {
        "slug": {
            "description": "Латинский ключ, по которому растение склеивается с оракулами и рекомендациями. Менять у уже привязанного растения нельзя — потеряются связи.",
        },
        "name_ru": {"description": "Имя на русском, как видит клиент в отчёте."},
        "name_lat": {"description": "Латинское имя для клиентского PDF (italic)."},
        "category": {
            "description": "Тип: tree / shrub / perennial / annual / grass / fern / vine / water / bulb / succulent / herb.",
        },
        "min_zone_usda": {
            "description": "Минимальная USDA-зона, в которой растение приживается. Если у клиента сад в зоне 4, а здесь 7 — растение отфильтруется.",
        },
        "max_zone_usda": {
            "description": "Максимальная USDA-зона. Чаще пусто. Заполнять только если растение реально не выносит юг.",
        },
        "sun": {
            "description": "Освещение: sun / part_shade / shade / sun_or_part_shade / any. Должно совпадать с garden_sun у клиента (mixed подходит ко всему).",
        },
        "soil_moisture": {
            "description": "Влажность почвы: dry / normal / wet / any.",
        },
        "hierarchy_potential": {
            "description": "1..5 — насколько растение «достойно» быть главным деревом гостьи. 5 — дуб, ива, яблоня; 1 — мелкая трава.",
        },
        "is_weed_like": {
            "description": "1 если растение склонно к экспансии (полынь, мята). Не выкидывает, но понижает вес ×0.5 в подборе.",
        },
        "short_story": {
            "description": "1–2 предложения для клиентского отчёта. Появляется под именем растения в PDF.",
        },
        "image_url": {
            "description": "Опционально: ссылка на иллюстрацию. Сейчас не используется (этап B7 заведёт SVG-иконки).",
        },
    }


class OracleAdmin(ModelView, model=Oracle):
    name = "Оракул"
    name_plural = "Оракулы"
    icon = "fa-solid fa-compass"
    column_list = [Oracle.id, Oracle.name_ru, Oracle.active, Oracle.weight, Oracle.sort_order]
    column_sortable_list = [Oracle.sort_order, Oracle.id]

    form_args = {
        "id": {
            "description": "Технический ключ оракула (druid_tree, zodiac, …). Должен совпадать с классом-наследником Oracle в коде.",
        },
        "name_ru": {"description": "Человеческое имя, видно в админке."},
        "active": {
            "description": "1 — оракул участвует в подборе. 0 — выключен (можно временно отключить, не удаляя записи).",
        },
        "weight": {
            "description": "Глобальный множитель: общий вклад этого оракула в total_weight каждой записи. По умолчанию 1.0.",
        },
        "sort_order": {
            "description": "Чем меньше — тем выше в списке оракулов и в источниках клиентского отчёта.",
        },
        "required_inputs": {
            "description": "JSON-список полей Person, без которых оракул не запускается. Например [\"birth_date\"] или [\"first_name\"].",
        },
    }


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

    # Используем FK-столбцы напрямую: relationship `plant` склеен по slug, а не по id,
    # и sqladmin не умеет автоматически проставлять такой ManyToOne. Для эксперта удобнее
    # явный выпадающий список slug'ов и id оракулов.
    form_columns = [
        "oracle_id",
        "plant_slug",
        "weight",
        "role",
        "reason_for_expert",
        "reason_for_client",
        "sort_order",
    ]

    form_args = {
        "oracle_id": {"description": "К какому оракулу относится эта запись (id оракула)."},
        "plant_slug": {"description": "slug растения из таблицы Plants (например, willow, oak)."},
        "weight": {"description": "Вес одного голоса этого оракула. main обычно 1.0, companion 0.7–0.9."},
        "role": {"description": "main — главное дерево клиента; companion — спутник."},
        "reason_for_expert": {"description": "Краткий текст для эксперта в подборе. Видно только в /expert/{id}, не в клиентском PDF."},
        "reason_for_client": {"description": "1 предложение, которое прочитает клиент. Появляется в листе гостьи."},
        "sort_order": {"description": "Порядок внутри записей одного оракула. Чаще всего 0."},
    }

    async def scaffold_form(self, rules=None):  # type: ignore[override]
        base_form = await super().scaffold_form(rules)

        with self.session_maker() as session:
            oracle_choices = [
                (o.id, f"{o.id} — {o.name_ru}")
                for o in session.query(Oracle).order_by(Oracle.sort_order, Oracle.id).all()
            ]
            plant_choices = [
                (p.slug, f"{p.slug} — {p.name_ru}")
                for p in session.query(Plant).order_by(Plant.slug).all()
            ]

        class _MatcherForm(base_form):
            oracle_id = SelectField(
                "Оракул",
                choices=[("", "— выберите —"), *oracle_choices],
                description="К какому оракулу относится эта запись.",
                validators=[validators.DataRequired(message="Выберите оракул.")],
            )
            plant_slug = SelectField(
                "Растение",
                choices=[("", "— выберите —"), *plant_choices],
                description="Какое растение выпадает при попадании в matcher.",
                validators=[validators.DataRequired(message="Выберите растение.")],
            )

            matcher_type = SelectField(
                "Тип matcher",
                choices=[("", "— выберите —"), *MATCHER_TYPES],
                description="Что именно сравнивает оракул с гостьей. От выбора зависят поля ниже.",
                validators=[validators.Optional()],
            )
            matcher_from = StringField(
                "Период «с» (MM-DD)",
                description="Только для типа «Период». Месяц-день: 03-05.",
                validators=[
                    validators.Optional(),
                    validators.Regexp(r"^\d{2}-\d{2}$", message="Формат MM-DD, например 03-05."),
                ],
            )
            matcher_to = StringField(
                "Период «по» (MM-DD)",
                description="Только для «Период». Можно обернуть через Новый год: 12-23 → 01-01.",
                validators=[
                    validators.Optional(),
                    validators.Regexp(r"^\d{2}-\d{2}$", message="Формат MM-DD, например 04-01."),
                ],
            )
            matcher_sign = SelectField(
                "Знак зодиака",
                choices=[("", "— выберите —"), *[(s, s.capitalize()) for s in ZODIAC_SIGNS]],
                description="Только для типа «Знак зодиака».",
                validators=[validators.Optional()],
            )
            matcher_number = IntegerField(
                "Число имени",
                description="Только для типа «Число имени». 1..9.",
                validators=[
                    validators.Optional(),
                    validators.NumberRange(min=1, max=9, message="1..9."),
                ],
            )
            matcher_color = SelectField(
                "Цвет глаз",
                choices=[("", "— выберите —"), *[(c, c) for c in EYE_COLORS]],
                description="Только для типа «Цвет глаз».",
                validators=[validators.Optional()],
            )
            matcher_name = StringField(
                "Имя клиента",
                description="Только для типа «Имя клиента». Сравнение нечувствительно к регистру.",
                validators=[validators.Optional()],
            )

            def process(self, formdata=None, obj=None, data=None, **kwargs):
                if obj is not None:
                    extra = {
                        "oracle_id": getattr(obj, "oracle_id", None),
                        "plant_slug": getattr(obj, "plant_slug", None),
                    }
                    if getattr(obj, "matcher", None):
                        m = obj.matcher or {}
                        extra.update({
                            "matcher_type": m.get("type"),
                            "matcher_from": m.get("from"),
                            "matcher_to": m.get("to"),
                            "matcher_sign": m.get("sign"),
                            "matcher_number": m.get("number"),
                            "matcher_color": m.get("color"),
                            "matcher_name": m.get("name"),
                        })
                    merged = dict(data or {})
                    for k, v in extra.items():
                        if v is not None and merged.get(k) in (None, ""):
                            merged[k] = v
                    data = merged
                super().process(formdata=formdata, obj=obj, data=data, **kwargs)

            def validate(self, *args, **kwargs):
                ok = super().validate(*args, **kwargs)
                mt = (self.matcher_type.data or "").strip()
                if not mt:
                    self.matcher_type.errors.append("Выберите тип matcher.")
                    return False
                if mt == "date_range_yearly":
                    if not (self.matcher_from.data or "").strip():
                        self.matcher_from.errors.append("Заполните «с (MM-DD)».")
                        ok = False
                    if not (self.matcher_to.data or "").strip():
                        self.matcher_to.errors.append("Заполните «по (MM-DD)».")
                        ok = False
                elif mt == "zodiac_sign":
                    if not (self.matcher_sign.data or "").strip():
                        self.matcher_sign.errors.append("Выберите знак.")
                        ok = False
                elif mt == "name_pythagorean_number":
                    if self.matcher_number.data is None:
                        self.matcher_number.errors.append("Введите число 1..9.")
                        ok = False
                elif mt == "eye_color":
                    if not (self.matcher_color.data or "").strip():
                        self.matcher_color.errors.append("Выберите цвет.")
                        ok = False
                elif mt == "name_match":
                    if not (self.matcher_name.data or "").strip():
                        self.matcher_name.errors.append("Введите имя.")
                        ok = False
                return ok

        return _MatcherForm

    async def on_model_change(self, data, model, is_created, request):  # type: ignore[override]
        matcher = _build_matcher(data)
        if matcher is not None:
            data["matcher"] = matcher
        for k in _VIRTUAL_MATCHER_KEYS:
            data.pop(k, None)


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


def _render_dump_page(rows: list[tuple[str, int]] | None, error: str | None) -> str:
    """Простая standalone-страница для выгрузки JSON. Без sqladmin layout (не критично — операция редкая)."""
    rows_html = ""
    if rows is not None:
        items = "".join(f"<li><code>{name}</code> — {n} записей</li>" for name, n in rows)
        rows_html = f"""
        <div style="margin-top:1rem;padding:1rem;background:#e6ffed;border:1px solid #2da44e;border-radius:6px;">
            <strong>Готово.</strong> Файлы записаны в <code>{SEED_DIR}</code>:
            <ul style="margin-top:0.5rem;">{items}</ul>
            <p style="margin-top:0.5rem;color:#555;">
                Чтобы зафиксировать изменения в git — сделай коммит этих JSON-файлов.
            </p>
        </div>
        """
    error_html = (
        f'<div style="margin-top:1rem;padding:1rem;background:#fff1f0;border:1px solid #d4380d;border-radius:6px;"><strong>Ошибка:</strong> {error}</div>'
        if error else ""
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Выгрузка справочников в JSON</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #1f2328; }}
    h1 {{ font-size: 1.4rem; }}
    p {{ line-height: 1.5; }}
    .btn {{ display: inline-block; padding: 0.6rem 1.2rem; background: #0969da; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }}
    .btn:hover {{ background: #0856b8; }}
    a {{ color: #0969da; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <p><a href="/admin/">← к админке</a></p>
  <h1>Выгрузить справочники в JSON</h1>
  <p>Эта кнопка читает текущее состояние БД (растения, оракулы, соответствия)
     и перезаписывает файлы <code>data/seed/*.json</code>. Используй её после
     ручных правок в админке, чтобы зафиксировать их в git.</p>
  <p style="color:#555;"><strong>Что не выгружается:</strong> клиенты (Person),
     рекомендации, натальные карты — это пользовательские данные, не справочник.</p>
  <form method="post" action="/admin/seed-dump">
    <button class="btn" type="submit">Выгрузить сейчас</button>
  </form>
  {rows_html}
  {error_html}
</body>
</html>"""


class SeedDumpView(BaseView):
    name = "Выгрузить в JSON"
    icon = "fa-solid fa-file-export"
    identity = "seed-dump"

    @expose("/seed-dump", methods=["GET", "POST"])
    async def dump(self, request: Request) -> HTMLResponse:
        if request.method == "POST":
            try:
                with SessionLocal() as session:
                    counts = dump_all(session)
                rows = sorted(counts.items())
                return HTMLResponse(_render_dump_page(rows, None))
            except Exception as e:
                return HTMLResponse(_render_dump_page(None, str(e)), status_code=500)
        return HTMLResponse(_render_dump_page(None, None))


def setup_admin(app, engine) -> Admin:
    admin = Admin(app, engine, title="Vlad rev1 — админка")
    admin.add_view(PersonAdmin)
    admin.add_view(PlantAdmin)
    admin.add_view(OracleAdmin)
    admin.add_view(OracleEntryAdmin)
    admin.add_view(RecommendationAdmin)
    admin.add_view(NatalChartAdmin)
    admin.add_base_view(SeedDumpView)
    return admin
