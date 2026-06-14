"""
Статистика Чемпионата мира 2026 — Streamlit-приложение.

Данные тянутся живьём через Anthropic API с инструментом web_search.
API-ключ берётся из st.secrets["ANTHROPIC_API_KEY"].
"""

import json
import datetime as dt

import streamlit as st

try:
    from anthropic import Anthropic
except Exception:  # noqa: BLE001 — anthropic может быть не установлен в момент импорта
    Anthropic = None


# ---------------------------------------------------------------------------
# Конфигурация страницы
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Статистика ЧМ-2026",
    page_icon="⚽",
    layout="centered",
)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1000
TOURNAMENT_START = dt.date(2026, 6, 11)


# ---------------------------------------------------------------------------
# Флаги стран-участниц ЧМ-2026 (англ. название → эмодзи). Fallback ⚽.
# ---------------------------------------------------------------------------
FLAGS = {
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Brazil": "🇧🇷",
    "Cameroon": "🇨🇲",
    "Canada": "🇨🇦",
    "Colombia": "🇨🇴",
    "Costa Rica": "🇨🇷",
    "Croatia": "🇭🇷",
    "Denmark": "🇩🇰",
    "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬",
    "England": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",
    "Iran": "🇮🇷",
    "Italy": "🇮🇹",
    "Ivory Coast": "🇨🇮",
    "Japan": "🇯🇵",
    "Mexico": "🇲🇽",
    "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿",
    "Nigeria": "🇳🇬",
    "Norway": "🇳🇴",
    "Panama": "🇵🇦",
    "Paraguay": "🇵🇾",
    "Peru": "🇵🇪",
    "Poland": "🇵🇱",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦",
    "Senegal": "🇸🇳",
    "Serbia": "🇷🇸",
    "South Korea": "🇰🇷",
    "Korea Republic": "🇰🇷",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "Türkiye": "🇹🇷",
    "Ukraine": "🇺🇦",
    "United States": "🇺🇸",
    "USA": "🇺🇸",
    "Uruguay": "🇺🇾",
    "Wales": "🏴\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f",
}


def flag(team: str) -> str:
    """Вернуть эмодзи-флаг сборной или ⚽ как fallback."""
    if not team:
        return "⚽"
    return FLAGS.get(team.strip(), "⚽")


# ---------------------------------------------------------------------------
# Стартовый снимок стоимости сборных (€ млн) — чтобы раздел не был пустым.
# ---------------------------------------------------------------------------
VALUE_SNAPSHOT = {
    "updated": "2026-06-11",
    "items": [
        {"team": "England", "value_m": 1345},
        {"team": "France", "value_m": 1195},
        {"team": "Brazil", "value_m": 1135},
        {"team": "Portugal", "value_m": 1000},
        {"team": "Spain", "value_m": 861},
        {"team": "Argentina", "value_m": 821},
        {"team": "Germany", "value_m": 775},
        {"team": "Netherlands", "value_m": 672},
        {"team": "Belgium", "value_m": 640},
        {"team": "Uruguay", "value_m": 480},
        {"team": "Denmark", "value_m": 347},
        {"team": "Croatia", "value_m": 326},
        {"team": "Morocco", "value_m": 318},
        {"team": "Serbia", "value_m": 292},
        {"team": "Japan", "value_m": 285},
        {"team": "Switzerland", "value_m": 282},
        {"team": "USA", "value_m": 270},
        {"team": "Poland", "value_m": 254},
        {"team": "Ghana", "value_m": 242},
        {"team": "Ecuador", "value_m": 236},
    ],
}


# ---------------------------------------------------------------------------
# Промты для каждой категории
# ---------------------------------------------------------------------------
def _scorers_prompt(today: str) -> str:
    return (
        "Найди в интернете актуальную статистику Чемпионата мира по футболу 2026 "
        "(FIFA World Cup 2026). Источник — официальный FIFA. "
        f"Сегодня {today}. Нужен топ-5 бомбардиров (лучшие по голам). "
        "Верни ТОЛЬКО валидный JSON без markdown и без каких-либо пояснений, "
        "строго по схеме: "
        '{"updated":"YYYY-MM-DD","items":[{"name":"...","team":"...","goals":N}]}. '
        "Названия сборных пиши на английском. goals — целое число. "
        "Если турнир только стартовал и данных мало — верни столько игроков, "
        "сколько есть (можно пустой items)."
    )


def _assists_prompt(today: str) -> str:
    return (
        "Найди в интернете актуальную статистику Чемпионата мира по футболу 2026 "
        "(FIFA World Cup 2026). Источник — официальный FIFA. "
        f"Сегодня {today}. Нужен топ-5 игроков по голевым передачам (ассистам). "
        "Верни ТОЛЬКО валидный JSON без markdown и без каких-либо пояснений, "
        "строго по схеме: "
        '{"updated":"YYYY-MM-DD","items":[{"name":"...","team":"...","assists":N}]}. '
        "Названия сборных пиши на английском. assists — целое число. "
        "Если турнир только стартовал и данных мало — верни столько игроков, "
        "сколько есть (можно пустой items)."
    )


def _values_prompt(today: str) -> str:
    return (
        "Найди в интернете актуальную рыночную стоимость составов сборных — "
        "участниц Чемпионата мира 2026. Источник — Transfermarkt. "
        f"Сегодня {today}. Нужен топ-20 самых дорогих сборных по суммарной "
        "стоимости состава в евро (млн), по убыванию. "
        "Верни ТОЛЬКО валидный JSON без markdown и без каких-либо пояснений, "
        "строго по схеме: "
        '{"updated":"YYYY-MM-DD","items":[{"team":"...","value_m":N}]}. '
        "Названия сборных пиши на английском. value_m — стоимость в € млн (число)."
    )


# ---------------------------------------------------------------------------
# Работа с Anthropic API
# ---------------------------------------------------------------------------
def _extract_json(raw: str) -> dict:
    """Собрать JSON из текста: убрать ```-обёртки, взять подстроку { ... }."""
    text = (raw or "").strip()
    # Убираем тройные обратные кавычки, если модель всё же обернула ответ.
    if text.startswith("```"):
        text = text.strip("`")
        # после strip может остаться префикс 'json'
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("В ответе модели не найден JSON")
    return json.loads(text[start : end + 1])


def _call_claude(prompt: str) -> dict:
    """Один запрос к Claude с web_search, возврат распарсенного JSON."""
    if Anthropic is None:
        raise RuntimeError(
            "Пакет anthropic не установлен. Выполните: pip install -r requirements.txt"
        )
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Не найден ANTHROPIC_API_KEY в st.secrets. "
            "Добавьте ключ в .streamlit/secrets.toml или в Secrets на Streamlit Cloud."
        ) from exc

    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )

    # Берём только текстовые блоки.
    texts = [
        block.text
        for block in resp.content
        if getattr(block, "type", None) == "text"
    ]
    raw = "\n".join(texts).strip()
    if not raw:
        raise ValueError("Модель не вернула текстового ответа")
    return _extract_json(raw)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_scorers() -> dict:
    today = dt.date.today().isoformat()
    return _call_claude(_scorers_prompt(today))


@st.cache_data(ttl=600, show_spinner=False)
def fetch_assists() -> dict:
    today = dt.date.today().isoformat()
    return _call_claude(_assists_prompt(today))


@st.cache_data(ttl=600, show_spinner=False)
def fetch_values() -> dict:
    today = dt.date.today().isoformat()
    return _call_claude(_values_prompt(today))


# ---------------------------------------------------------------------------
# Тёмная тема в стиле табло
# ---------------------------------------------------------------------------
def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg:#0B0F12; --panel:#11171C; --line:#1E2832;
            --green:#19E37D; --gold:#FFCB45; --text:#E8EEF2; --muted:#7C8B96;
        }
        .stApp { background: radial-gradient(1200px 600px at 50% -10%, #13201A 0%, #0B0F12 55%); }
        .block-container { max-width: 720px; padding-top: 1.2rem; }
        html, body, [class*="css"] {
            color: var(--text);
            font-family: "DejaVu Sans Mono", ui-monospace, Menlo, Consolas, monospace;
        }
        h1, h2, h3 { color: var(--text); letter-spacing: 0.02em; }

        .tablo-title {
            text-align:center; font-weight:800; font-size:1.9rem;
            color: var(--green); text-shadow: 0 0 18px rgba(25,227,125,0.45);
            margin: 0 0 2px;
        }
        .tablo-sub { text-align:center; color: var(--muted); margin: 0 0 16px; font-size:0.9rem; }

        .note {
            background: rgba(255,203,69,0.08); border:1px solid rgba(255,203,69,0.3);
            color: var(--gold); padding:10px 14px; border-radius:10px;
            font-size:0.85rem; margin: 6px 0 14px;
        }
        .updated { color: var(--muted); font-size:0.8rem; margin: 2px 0 10px; }

        /* Строка статистики */
        .row {
            display:flex; align-items:center; gap:12px;
            background: var(--panel); border:1px solid var(--line);
            border-radius:12px; padding:10px 14px; margin-bottom:8px;
        }
        .rank {
            min-width:28px; height:28px; border-radius:8px;
            background:#0E1519; border:1px solid var(--line);
            display:flex; align-items:center; justify-content:center;
            color: var(--green); font-weight:700; font-size:0.9rem;
        }
        .who { flex:1; min-width:0; }
        .who .name { font-weight:700; font-size:1rem; }
        .who .team { color: var(--muted); font-size:0.82rem; }
        .stat-num { color: var(--green); font-weight:800; font-size:1.25rem; min-width:42px; text-align:right; }

        /* Строка стоимости с баром */
        .vrow { background: var(--panel); border:1px solid var(--line);
                border-radius:12px; padding:10px 14px; margin-bottom:7px; }
        .vrow-top { display:flex; align-items:center; gap:10px; }
        .vrow .team { flex:1; font-weight:700; }
        .vrow .val { color: var(--gold); font-weight:800; }
        .bar-track { height:9px; background:#0E1519; border-radius:6px; margin-top:8px; overflow:hidden; }
        .bar-fill {
            height:100%; border-radius:6px;
            background: linear-gradient(90deg, #B8860B 0%, var(--gold) 100%);
            box-shadow: 0 0 10px rgba(255,203,69,0.35);
        }

        .empty { color: var(--muted); text-align:center; padding:18px; }
        div.stButton > button {
            background: var(--panel); color: var(--green);
            border:1px solid var(--green); border-radius:10px; font-weight:700;
        }
        div.stButton > button:hover { background: var(--green); color:#06120B; border-color: var(--green); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Рендеринг разделов
# ---------------------------------------------------------------------------
def _esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_players(data: dict, stat_key: str, stat_label: str) -> None:
    """Отрисовать топ игроков (бомбардиры/ассистенты)."""
    updated = data.get("updated")
    if updated:
        st.markdown(f'<div class="updated">Обновлено: {_esc(updated)}</div>', unsafe_allow_html=True)

    items = data.get("items") or []
    items = sorted(items, key=lambda x: x.get(stat_key, 0), reverse=True)[:5]

    if not items:
        st.markdown(
            '<div class="empty">Пока нет данных — турнир только начался.<br>'
            'Нажмите «Обновить» чуть позже.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for i, it in enumerate(items, start=1):
        name = _esc(it.get("name", "—"))
        team = it.get("team", "")
        num = it.get(stat_key, 0)
        rows.append(
            f'<div class="row">'
            f'<div class="rank">{i}</div>'
            f'<div class="who"><div class="name">{name}</div>'
            f'<div class="team">{flag(team)} {_esc(team)}</div></div>'
            f'<div class="stat-num" title="{_esc(stat_label)}">{_esc(num)}</div>'
            f"</div>"
        )
    st.markdown("\n".join(rows), unsafe_allow_html=True)


def render_values(data: dict) -> None:
    """Отрисовать топ-20 сборных по стоимости с барами."""
    updated = data.get("updated")
    if updated:
        st.markdown(f'<div class="updated">Обновлено: {_esc(updated)}</div>', unsafe_allow_html=True)

    items = data.get("items") or []
    items = sorted(items, key=lambda x: x.get("value_m", 0), reverse=True)[:20]

    if not items:
        st.markdown('<div class="empty">Нет данных о стоимости.</div>', unsafe_allow_html=True)
        return

    max_val = max((it.get("value_m", 0) or 0) for it in items) or 1

    rows = []
    for it in items:
        team = it.get("team", "")
        val = it.get("value_m", 0) or 0
        pct = max(2, round(val / max_val * 100))
        rows.append(
            f'<div class="vrow">'
            f'<div class="vrow-top">'
            f'<span>{flag(team)}</span>'
            f'<span class="team">{_esc(team)}</span>'
            f'<span class="val">€{_esc(val)} млн</span>'
            f"</div>"
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f"</div>"
        )
    st.markdown("\n".join(rows), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Загрузка с обработкой ошибок
# ---------------------------------------------------------------------------
def safe_fetch(fetcher, label: str):
    """Вызвать fetcher, вернуть (data|None). Ошибку показать на русском."""
    try:
        with st.spinner(f"Обновляю: {label}…"):
            return fetcher()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Не удалось обновить «{label}»: {exc}")
        return None


# ---------------------------------------------------------------------------
# Основное приложение
# ---------------------------------------------------------------------------
def main() -> None:
    inject_css()

    # Инициализация состояния.
    if "scorers" not in st.session_state:
        st.session_state.scorers = {"updated": None, "items": []}
    if "assists" not in st.session_state:
        st.session_state.assists = {"updated": None, "items": []}
    if "team_values" not in st.session_state:
        # Стартовый снимок, чтобы раздел не был пустым.
        # ВНИМАНИЕ: ключ называется team_values, а не values —
        # имя "values" конфликтует с методом st.session_state.values().
        st.session_state.team_values = VALUE_SNAPSHOT

    st.markdown('<div class="tablo-title">⚽ ЧМ-2026 · ТАБЛО</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tablo-sub">Статистика Чемпионата мира 2026 · live через Anthropic web_search</div>',
        unsafe_allow_html=True,
    )

    # Кнопка «Обновить всё».
    if st.button("🔄 Обновить всё", use_container_width=True):
        s = safe_fetch(fetch_scorers, "Бомбардиры")
        if s is not None:
            st.session_state.scorers = s
        a = safe_fetch(fetch_assists, "Ассистенты")
        if a is not None:
            st.session_state.assists = a
        v = safe_fetch(fetch_values, "Стоимость сборных")
        if v is not None:
            st.session_state.team_values = v

    # Подпись о раннем этапе турнира.
    if dt.date.today() <= TOURNAMENT_START + dt.timedelta(days=14):
        st.markdown(
            '<div class="note">⏱ Турнир стартовал 11 июня 2026. На раннем этапе '
            'списки бомбардиров и ассистентов могут быть короткими или пустыми.</div>',
            unsafe_allow_html=True,
        )

    tab1, tab2, tab3 = st.tabs(["⚽ Бомбардиры", "🅰️ Ассистенты", "💰 Стоимость сборных"])

    with tab1:
        st.subheader("Бомбардиры — Топ-5")
        st.caption("Источник: FIFA")
        if st.button("🔄 Обновить", key="upd_scorers"):
            s = safe_fetch(fetch_scorers, "Бомбардиры")
            if s is not None:
                st.session_state.scorers = s
        render_players(st.session_state.scorers, "goals", "голы")

    with tab2:
        st.subheader("Ассистенты — Топ-5")
        st.caption("Источник: FIFA")
        if st.button("🔄 Обновить", key="upd_assists"):
            a = safe_fetch(fetch_assists, "Ассистенты")
            if a is not None:
                st.session_state.assists = a
        render_players(st.session_state.assists, "assists", "ассисты")

    with tab3:
        st.subheader("Стоимость сборных — Топ-20")
        st.caption("Источник: Transfermarkt · € млн")
        render_values(st.session_state.team_values)


if __name__ == "__main__":
    main()
