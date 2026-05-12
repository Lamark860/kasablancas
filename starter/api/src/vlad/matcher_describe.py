"""Human-readable описание matcher.

Используется в /admin (column_formatters), в CSV-импорте (preview-diff)
и в будущей live-подсказке на форме.

Возвращает короткую строку вида:
    «период 25.06 → 07.07»
    «знак Cancer»
    «число имени 4»
    «цвет глаз blue»
    «имя „Дарья“»

Если matcher пустой/невалидный — возвращает «—».
"""
from __future__ import annotations


_ZODIAC_RU = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы", "cancer": "Рак",
    "leo": "Лев", "virgo": "Дева", "libra": "Весы", "scorpio": "Скорпион",
    "sagittarius": "Стрелец", "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы",
}


def _fmt_mmdd(s: str | None) -> str:
    """'03-05' → '05.03'. Если формат не распознан — вернуть как есть."""
    if not s or not isinstance(s, str) or len(s) != 5 or s[2] != "-":
        return s or "?"
    m, d = s.split("-")
    return f"{d}.{m}"


def describe_matcher(matcher: dict | None) -> str:
    if not matcher or not isinstance(matcher, dict):
        return "—"
    t = matcher.get("type")
    if t == "date_range_yearly":
        return f"период {_fmt_mmdd(matcher.get('from'))} → {_fmt_mmdd(matcher.get('to'))}"
    if t == "zodiac_sign":
        sign = (matcher.get("sign") or "").strip()
        return f"знак {_ZODIAC_RU.get(sign.lower(), sign or '?')}"
    if t == "name_pythagorean_number":
        n = matcher.get("number")
        return f"число имени {n if n is not None else '?'}"
    if t == "eye_color":
        return f"цвет глаз {matcher.get('color') or '?'}"
    if t == "name_match":
        nm = matcher.get("name") or "?"
        return f"имя «{nm}»"
    return f"({t})"
