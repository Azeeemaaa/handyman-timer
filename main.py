import time
import json
import html
import urllib.request
import urllib.error
from datetime import datetime, timedelta, time as dt_time

import streamlit as st
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", page_icon="🛠", layout="centered")


# ---------- Дизайн (фиолетовый, по макету) ----------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --accent:#6C4DF6; --accent2:#8B6CF8; --green:#2FBF71; --red:#FB3B40;
            --gray:#8E8EA9; --lav:#EEEAFE; --fill:#F4F4F8; --card:#FFFFFF;
            --grad:linear-gradient(135deg,#7E5BEF 0%,#6A45E0 100%);
        }
        .stApp { background: #FFFFFF; }
        .block-container {
            max-width: 460px; padding-top: 1.2rem; padding-bottom: 4rem;
        }
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        }
        h1 { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; }
        h2, h3 { letter-spacing: -0.01em; }

        /* Шапка с иконкой */
        .app-header { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
        .app-header .icon-box {
            width:54px; height:54px; min-width:54px; border-radius:16px;
            background: var(--fill); display:flex; align-items:center; justify-content:center;
            font-size:26px;
        }
        .app-sub { color: var(--gray); font-size:15px; margin:4px 0 14px; }

        /* Карточки */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card);
            border: 1px solid #EFEFF4 !important;
            border-radius: 22px;
            box-shadow: 0 6px 22px rgba(80,60,160,0.06);
            padding: 14px 16px;
            margin-bottom: 8px;
        }

        /* Кнопки — крупные pill */
        .stButton > button, .stDownloadButton > button {
            border-radius: 16px;
            padding: 0.8rem 1rem;
            font-weight: 700;
            font-size: 17px;
            border: none;
            width: 100%;
            min-height: 54px;
            transition: transform .06s ease, filter .15s ease;
        }
        .stButton > button:active, .stDownloadButton > button:active { transform: scale(0.97); }
        .stButton > button[kind="primary"] {
            background: var(--grad); color:#fff;
            box-shadow: 0 8px 18px rgba(108,77,246,0.28);
        }
        .stButton > button[kind="secondary"], .stDownloadButton > button {
            background: var(--lav); color: var(--accent);
        }
        .stButton > button[kind="primary"]:hover { filter: brightness(1.05); color:#fff; }

        /* Цветные акценты по ключам */
        .st-key-stop_btn button {
            background: var(--red) !important; color:#fff !important;
            box-shadow: 0 8px 18px rgba(251,59,64,0.28) !important;
        }
        .st-key-show_msg_btn button { background: var(--lav) !important; color: var(--accent) !important; }

        /* Поля ввода */
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input {
            border-radius: 14px; font-size: 16px; font-weight: 600;
            background: var(--fill);
        }
        [data-testid="stNumberInput"] div[data-baseweb="input"],
        [data-testid="stTextInput"] div[data-baseweb="input"] {
            border-radius: 14px; background: var(--fill);
        }
        /* Степперы +/- у числовых полей */
        [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {
            color: var(--accent); border-radius: 10px;
        }

        /* Вкладки -> сегмент-контрол */
        [data-testid="stTabs"] [role="tablist"] {
            background: var(--fill); border-radius: 14px; padding: 5px; gap: 5px;
            border-bottom: none;
        }
        [data-testid="stTabs"] [role="tablist"] button {
            flex: 1; border-radius: 11px; padding: 8px 4px; font-weight: 700;
            color: #5B5B72;
        }
        [data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] {
            background: var(--grad); color:#fff;
            box-shadow: 0 4px 12px rgba(108,77,246,0.3);
        }
        [data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] p { color:#fff; }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }

        /* Заголовок секции */
        .sec-label {
            color: var(--gray); font-size: 13px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.03em;
            margin: 2px 0 2px 4px;
        }

        /* Круговой прогресс вокруг таймера */
        .ring {
            width: 210px; height: 210px; border-radius: 50%;
            display:flex; align-items:center; justify-content:center;
            margin: 8px auto 4px;
        }
        .ring-inner {
            width: 178px; height: 178px; border-radius: 50%; background:#fff;
            display:flex; align-items:center; justify-content:center;
            font-size: 2.3rem; font-weight: 800; color:#1C1C2E;
            font-variant-numeric: tabular-nums; letter-spacing:-0.02em;
        }
        .timer-status { text-align:center; color: var(--gray); font-weight:700; margin-bottom: 6px; }
        .pay-now { text-align:center; font-size: 1.05rem; color:#1C1C2E; margin-top: 2px; }
        .pay-big { text-align:center; color: var(--green); font-weight:800; font-size: 2rem; margin: 6px 0; }
        .total-row {
            display:flex; align-items:center; justify-content:space-between;
            padding: 8px 6px 2px; font-weight:700;
        }
        .total-row .val { color: var(--accent); font-size:1.4rem; font-weight:800; }

        /* История: градиентный блок-итог */
        .summary-card {
            background: var(--grad); color:#fff; border-radius:22px; padding:18px 20px;
            display:flex; justify-content:space-between; align-items:center;
            box-shadow: 0 10px 24px rgba(108,77,246,0.30); margin-bottom:14px;
        }
        .summary-card .lbl { font-size:13px; opacity:0.9; font-weight:600; }
        .summary-card .big { font-size:2rem; font-weight:800; line-height:1.1; }
        .summary-card .mid { font-size:1.4rem; font-weight:800; line-height:1.1; }

        /* История: карточка работы */
        .job-card {
            background:#fff; border:1px solid #EFEFF4; border-radius:18px;
            padding:14px 16px; margin-bottom:10px; box-shadow:0 4px 14px rgba(80,60,160,0.05);
        }
        .job-card .top { display:flex; justify-content:space-between; align-items:baseline; }
        .job-card .date { color:var(--gray); font-size:12px; font-weight:600; }
        .job-card .client { font-size:1.05rem; font-weight:800; color:#1C1C2E; margin:3px 0 2px; }
        .job-card .amount { color:var(--green); font-size:1.15rem; font-weight:800; white-space:nowrap; }
        .job-card .meta { color:var(--gray); font-size:13px; font-weight:600; }

        /* История: средний заработок + спарклайн */
        .avg-card {
            background:#fff; border:1px solid #EFEFF4; border-radius:18px; padding:14px 16px;
            display:flex; justify-content:space-between; align-items:flex-end;
            box-shadow:0 4px 14px rgba(80,60,160,0.05); margin-top:4px;
        }
        .avg-card .lbl { color:var(--gray); font-size:13px; font-weight:600; }
        .avg-card .val { font-size:1.5rem; font-weight:800; color:#1C1C2E; }
        .spark { display:flex; align-items:flex-end; gap:4px; height:40px; }
        .spark span { width:7px; background:var(--accent2); border-radius:3px; opacity:0.55; }
        .spark span.hot { background:var(--accent); opacity:1; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()
st.markdown(
    '<div class="app-header">'
    '<h1>Расчёт<br>стоимости работы</h1>'
    '<div class="icon-box">🛠</div>'
    '</div>'
    '<div class="app-sub">Рассчитайте стоимость и отслеживайте свои заказы легко и быстро</div>',
    unsafe_allow_html=True,
)

# ====================== ХРАНИЛИЩЕ ДАННЫХ ======================
# Все данные (активный таймер и история работ) живут во внешнем надёжном
# хранилище — приватном GitHub Gist. Оно переживает засыпание приложения на
# Streamlit Cloud, перезапуск сервера и капризы памяти браузера на iPhone.
#
# Чтобы оно включилось, в Secrets приложения нужно добавить токен GH_GIST_TOKEN
# (одноразовая настройка, см. инструкцию). Пока токена нет — работает резерв
# (localStorage), как раньше, так что приложение не ломается ни при каких
# условиях. Сам файл-хранилище создаётся в gist автоматически при первом старте.
#
# Время всегда считается от таймстампа старта, поэтому таймер «идёт», даже когда
# приложение закрыто.

TIMER_KEY = "ht_timer"      # ключ активного таймера в localStorage-резерве
HISTORY_KEY = "ht_history"  # ключ истории в localStorage-резерве
MIN_TOTAL = 100.0           # минимальная итоговая цена за работу ($), даже за пару минут
GIST_FILENAME = "handyman-timer-state.json"  # имя файла-хранилища внутри gist
_QP_KEYS = ("ts", "pr", "mt", "pa")          # ключи активного таймера в адресе страницы


@st.cache_resource
def _store():
    """Рабочая копия всех данных в памяти процесса, общая для всех подключений.
    Подгружается из gist (или localStorage) при холодном старте и дальше читается
    мгновенно — чтобы автообновление таймера раз в секунду не дёргало сеть."""
    return {"timer": None, "history": None, "loaded": False, "gist_id": None, "source": None}


@st.cache_resource
def _local_storage():
    """Компонент localStorage создаём лениво и только как резерв: когда настроено
    внешнее хранилище, он не рисует свой iframe (и возможную ошибку
    «not connected to a server»)."""
    return LocalStorage()


def _gist_token():
    try:
        if "GH_GIST_TOKEN" in st.secrets:
            return st.secrets["GH_GIST_TOKEN"] or None
    except Exception:
        pass
    return None


# ---------- низкоуровневый доступ к GitHub Gist ----------
def _gh_api(method, url, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "handyman-timer")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _gist_find_id(token):
    """Находит id нашего gist по имени файла; кэширует в рабочей копии."""
    store = _store()
    if store.get("gist_id"):
        return store["gist_id"]
    gists = _gh_api("GET", "https://api.github.com/gists?per_page=100", token)
    for g in gists:
        if GIST_FILENAME in (g.get("files") or {}):
            store["gist_id"] = g["id"]
            return g["id"]
    return None


def _remote_load(token):
    """Читает {'timer':..., 'history':...} из gist.
    None — если произошла ошибка (тогда мы НЕ трогаем gist, чтобы не затереть данные)."""
    try:
        gid = _gist_find_id(token)
        if not gid:
            return {"timer": None, "history": []}  # gist ещё не создан — данных нет
        gist = _gh_api("GET", f"https://api.github.com/gists/{gid}", token)
        state = json.loads(gist["files"][GIST_FILENAME]["content"])
        return {"timer": state.get("timer"), "history": state.get("history") or []}
    except Exception:
        return None


def _remote_save(token, state):
    """Сохраняет полное состояние в gist (создаёт gist при первом сохранении)."""
    try:
        files = {GIST_FILENAME: {"content": json.dumps(state, ensure_ascii=False, indent=2)}}
        gid = _store().get("gist_id") or _gist_find_id(token)
        if gid:
            _gh_api("PATCH", f"https://api.github.com/gists/{gid}", token, {"files": files})
        else:
            created = _gh_api("POST", "https://api.github.com/gists", token, {
                "description": "Handyman timer — данные приложения (таймер и история)",
                "public": False,
                "files": files,
            })
            _store()["gist_id"] = created["id"]
        return True
    except Exception:
        return False


def _ls_get_json(key):
    try:
        raw = _local_storage().getItem(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _ensure_loaded():
    """Подгружает рабочую копию из надёжного хранилища один раз на «жизнь» процесса."""
    store = _store()
    if store["loaded"]:
        return store
    token = _gist_token()
    if token:
        remote = _remote_load(token)
        if remote is not None:
            store["timer"] = remote["timer"]
            store["history"] = remote["history"]
            store["source"] = "remote"
            store["loaded"] = True
        else:
            # Ошибка чтения gist: не помечаем как загруженное и НЕ перезаписываем
            # gist при сохранении — чтобы случайно не затереть историю. Повторим позже.
            store["history"] = store["history"] or []
            store["source"] = "error"
        return store
    # Без токена — резерв localStorage (прежнее поведение)
    store["timer"] = _ls_get_json(TIMER_KEY)
    store["history"] = _ls_get_json(HISTORY_KEY) or []
    store["source"] = "local"
    store["loaded"] = True
    return store


def _persist():
    """Сохраняет текущую рабочую копию в надёжное хранилище."""
    store = _store()
    state = {"timer": store["timer"], "history": store["history"] or []}
    token = _gist_token()
    if token and store.get("source") != "error" and _remote_save(token, state):
        store["source"] = "remote"
        store["loaded"] = True
        return
    # Резерв: localStorage
    try:
        ls = _local_storage()
        ls.setItem(TIMER_KEY, json.dumps(state["timer"]) if state["timer"] else "", key="set_timer")
        ls.setItem(HISTORY_KEY, json.dumps(state["history"]), key="set_history")
    except Exception:
        pass


# ---------- активный таймер ----------
# Активный таймер дублируется в параметрах URL (st.query_params): они читаются
# мгновенно и синхронно, поэтому автообновление раз в секунду обходится без сети,
# а перезагрузка страницы/переподключение не теряют таймер в пределах сессии.
def _timer_from_query():
    qp = st.query_params
    if "ts" not in qp:
        return None
    try:
        pause_raw = qp.get("pa")
        return {
            "start": float(qp["ts"]),
            "pause": float(pause_raw) if pause_raw else None,
            "rate": float(qp.get("pr", 0) or 0),
            "materials": float(qp.get("mt", 0) or 0),
        }
    except (ValueError, TypeError):
        return None


def _timer_to_query(data):
    if not data:
        for k in _QP_KEYS:
            if k in st.query_params:
                del st.query_params[k]
        return
    st.query_params["ts"] = repr(float(data["start"]))
    st.query_params["pr"] = repr(float(data.get("rate", 0) or 0))
    st.query_params["mt"] = repr(float(data.get("materials", 0) or 0))
    if data.get("pause"):
        st.query_params["pa"] = repr(float(data["pause"]))
    elif "pa" in st.query_params:
        del st.query_params["pa"]


def get_timer():
    # URL — мгновенно (основной путь, пока таймер идёт): не трогает сеть
    timer = _timer_from_query()
    if timer is not None:
        return timer
    # Иначе берём из рабочей копии (при холодном старте подгружена из gist)
    timer = _ensure_loaded().get("timer")
    if timer:
        _timer_to_query(timer)  # разложим в адрес, чтобы дальше читать без сети
        return timer
    return None


def set_timer(data):
    store = _ensure_loaded()
    store["timer"] = data
    _timer_to_query(data)
    _persist()


def clear_timer():
    store = _ensure_loaded()
    store["timer"] = None
    _timer_to_query(None)
    _persist()


# ---------- история работ ----------
def get_history():
    return _ensure_loaded().get("history") or []


def set_history(items):
    store = _ensure_loaded()
    store["history"] = items
    _persist()


def clear_history():
    set_history([])


def add_history_entry(date_str, client, elapsed_str, hours, rate, materials, total, break_min=0):
    history = get_history()
    history.insert(0, {
        "date": date_str,
        "client": (client or "").strip() or "—",
        "elapsed": elapsed_str,
        "break": break_min,
        "hours": round(hours, 2),
        "rate": rate,
        "materials": materials,
        "total": round(total, 2),
    })
    set_history(history)


def fmt_hms(seconds):
    return str(timedelta(seconds=int(max(0, seconds))))


def money(v):
    v = round(float(v), 2)
    return f"${v:.0f}" if v == int(v) else f"${v:.2f}"


def fmt_hours(h):
    return "%g" % round(float(h), 2)


def fmt_clock(t):
    """time/datetime -> '9am' или '4:30pm' (как в письме клиенту)."""
    s = t.strftime("%I:%M%p").lower()
    if s.startswith("0"):
        s = s[1:]
    return s.replace(":00", "")


def build_message(start_str, end_str, break_min, hours, rate, materials, total):
    """Собирает письмо клиенту в том же стиле, что ты отправляешь вручную."""
    labor = hours * rate
    lines = [
        "Hi sir 👋",
        "I've finished the work for today ✅",
        "",
        "Today:",
        "",
        f"I started {start_str} and finished {end_str}",
    ]
    if break_min:
        lines.append(f"Break: {break_min} min")
    lines += [
        "",
        f"Labor: {fmt_hours(hours)}h - {money(labor)}",
        f"Materials – {money(materials)}",
    ]
    # Если сработала минимальная цена — поясняем клиенту, почему итог выше суммы строк
    if round(labor + materials, 2) < round(total, 2):
        lines.append(f"Minimum service charge: {money(total)}")
    lines += [
        "",
        f"Total: {money(total)}",
        "",
        "Have a great day! 🤝",
    ]
    return "\n".join(lines)


def message_with_copy(message, key):
    """Показывает текст письма + кнопку «Скопировать текст» (работает на телефоне)."""
    payload = json.dumps(message)
    html_code = f"""
    <div style="font-family: -apple-system, system-ui, sans-serif;">
      <textarea id="ta_{key}" readonly
        style="width:100%; height:300px; font-size:15px; padding:12px; box-sizing:border-box;
               border:1px solid #E5E5EA; border-radius:14px; resize:vertical; background:#F9F9FB;"></textarea>
      <button id="btn_{key}"
        style="margin-top:10px; width:100%; padding:14px; font-size:17px; font-weight:600;
               border:none; border-radius:14px; background:#6C4DF6; color:#fff; cursor:pointer;">
        📋 Скопировать текст
      </button>
      <div id="ok_{key}" style="text-align:center; color:#2FBF71; font-weight:600; margin-top:8px; min-height:20px;"></div>
    </div>
    <script>
      (function() {{
        const msg = {payload};
        const ta = document.getElementById("ta_{key}");
        ta.value = msg;
        document.getElementById("btn_{key}").addEventListener("click", function() {{
          const done = function() {{
            document.getElementById("ok_{key}").innerText = "✅ Скопировано! Вставь клиенту";
          }};
          ta.focus(); ta.select(); ta.setSelectionRange(0, 999999);
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(msg).then(done, function() {{
              try {{ document.execCommand("copy"); }} catch (e) {{}}
              done();
            }});
          }} else {{
            try {{ document.execCommand("copy"); }} catch (e) {{}}
            done();
          }}
        }});
      }})();
    </script>
    """
    components.html(html_code, height=420)


def compute(timer):
    """Возвращает (elapsed_td, hours, total) для текущего состояния таймера."""
    start = timer["start"]
    now = timer["pause"] if timer.get("pause") else time.time()
    elapsed_seconds = max(0.0, now - start)
    hours = elapsed_seconds / 3600
    total = max(hours * timer.get("rate", 0) + timer.get("materials", 0), MIN_TOTAL)
    return timedelta(seconds=int(elapsed_seconds)), hours, total


# ---------- состояние ----------
if "last_result" not in st.session_state:
    st.session_state.last_result = None  # результат после "Стоп", ждёт сохранения
if "show_msg_running" not in st.session_state:
    st.session_state.show_msg_running = False  # показывать текст клиенту во время таймера

# ---------- общие параметры ----------
with st.container(border=True):
    rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=65.0, step=5.0)
    materials = st.number_input("🧱 Материалы ($), необязательно", min_value=0.0, value=0.0, step=1.0)
    st.markdown(
        '<div class="total-row"><span>ⓘ Минимальная базовая цена</span>'
        '<span class="val">$100</span></div>',
        unsafe_allow_html=True,
    )

tab_timer, tab_manual, tab_history = st.tabs(["⏱ Таймер", "✍️ Вручную", "📋 История"])

# =======================================================================
#  Вкладка 1: живой таймер
# =======================================================================
with tab_timer:
    timer = get_timer()
    running = timer is not None and not timer.get("pause")

    # Пока показываем текст клиенту — замораживаем автообновление (время не теряется)
    if running and not st.session_state.show_msg_running:
        st_autorefresh(interval=1000, limit=None, key="refresh")

    if timer is None and st.session_state.last_result is None:
        with st.container(border=True):
            st.markdown(
                '<p style="text-align:center;color:#8E8E93;margin:10px 0 14px;">'
                'Нажми «Старт», когда начинаешь работу у клиента.</p>',
                unsafe_allow_html=True,
            )
            if st.button("▶️ Старт", use_container_width=True, type="primary", key="start_btn"):
                set_timer({"start": time.time(), "pause": None, "rate": rate, "materials": materials})
                st.session_state.show_msg_running = False
                st.rerun()

    elif timer is not None:
        elapsed_td, hours, total = compute(timer)
        paused = bool(timer.get("pause"))

        with st.container(border=True):
            pct = (int(elapsed_td.total_seconds()) % 60) / 60 * 100
            st.markdown(
                f'<div class="ring" style="background:conic-gradient(var(--accent) {pct:.1f}%, #ECE9FB 0)">'
                f'<div class="ring-inner">{elapsed_td}</div></div>',
                unsafe_allow_html=True,
            )
            status = "⏸ На паузе" if paused else "🟢 Идёт"
            st.markdown(f'<div class="timer-status">{status}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="pay-now" style="margin-bottom:14px">'
                f'💰 Заработано: <b>{money(total)}</b></div>',
                unsafe_allow_html=True,
            )

            if paused:
                if st.button("🔄 Продолжить", use_container_width=True, type="primary", key="resume_btn"):
                    paused_duration = time.time() - timer["pause"]
                    timer["start"] = timer["start"] + paused_duration
                    timer["pause"] = None
                    set_timer(timer)
                    st.rerun()
            else:
                if st.button("⏸ Пауза", use_container_width=True, key="pause_btn"):
                    timer["pause"] = time.time()
                    set_timer(timer)
                    st.rerun()

            if st.button("⏹ Стоп", use_container_width=True, type="primary", key="stop_btn"):
                elapsed_td, hours, total = compute(timer)
                st.session_state.last_result = {
                    "elapsed": str(elapsed_td),
                    "hours": round(hours, 2),
                    "rate": timer.get("rate", 0),
                    "materials": timer.get("materials", 0),
                    "total": round(total, 2),
                    "start_clock": fmt_clock(datetime.fromtimestamp(timer["start"])),
                    "end_clock": fmt_clock(datetime.now()),
                }
                st.session_state.show_msg_running = False
                clear_timer()
                st.rerun()

            # Текст для клиента прямо во время работы
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            if not st.session_state.show_msg_running:
                if st.button("✉️ Текст для клиента", use_container_width=True, key="show_msg_btn"):
                    st.session_state.show_msg_running = True
                    st.rerun()
            else:
                msg = build_message(
                    fmt_clock(datetime.fromtimestamp(timer["start"])),
                    fmt_clock(datetime.now()), 0,
                    hours, timer.get("rate", 0), timer.get("materials", 0), total,
                )
                message_with_copy(msg, key="timer_live")
                st.caption("⏱ Таймер продолжает идти — время не теряется.")
                if st.button("⬅️ Скрыть и продолжить", use_container_width=True, key="hide_msg_btn"):
                    st.session_state.show_msg_running = False
                    st.rerun()

    # Результат после "Стоп": показать сумму и сохранить
    if st.session_state.last_result is not None:
        r = st.session_state.last_result
        with st.container(border=True):
            st.markdown('<div style="text-align:center;font-weight:700;">🛑 Работа завершена</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="timer-status">⏰ Время работы: {r["elapsed"]}</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="pay-big">💲 К оплате: {money(r["total"])}</div>', unsafe_allow_html=True)

            with st.expander("✉️ Текст для клиента"):
                msg = build_message(
                    r.get("start_clock", ""), r.get("end_clock", ""), 0,
                    r["hours"], r["rate"], r["materials"], r["total"],
                )
                message_with_copy(msg, key="timer")

            client = st.text_input("👤 Имя клиента", value="", placeholder="Например: Иван, кухня", key="t_client")
            cc1, cc2 = st.columns(2)
            if cc1.button("💾 Сохранить", use_container_width=True, type="primary", key="t_save"):
                add_history_entry(
                    datetime.now().strftime("%Y-%m-%d %H:%M"), client,
                    r["elapsed"], r["hours"], r["rate"], r["materials"], r["total"],
                )
                st.session_state.last_result = None
                st.rerun()
            if cc2.button("❌ Не сохранять", use_container_width=True, key="t_skip"):
                st.session_state.last_result = None
                st.rerun()

# =======================================================================
#  Вкладка 2: ручной ввод времени + перерыв
# =======================================================================
with tab_manual:
    with st.container(border=True):
        st.markdown(
            '<p style="color:#8E8E93;margin:2px 0 10px;">'
            'Если забыл нажать «Старт» — укажи, когда начал и закончил.</p>',
            unsafe_allow_html=True,
        )
        work_date = st.date_input("📅 Дата работы", value=datetime.now().date(), key="m_date")
        c1, c2 = st.columns(2)
        start_t = c1.time_input("🕘 Начало", value=dt_time(9, 0), step=300, key="m_start")
        end_t = c2.time_input("🕔 Конец", value=dt_time(17, 0), step=300, key="m_end")
        break_min = st.number_input(
            "☕ Перерыв (минут, шаг 15)", min_value=0, max_value=600, value=0, step=15, key="m_break"
        )

    start_dt = datetime.combine(work_date, start_t)
    end_dt = datetime.combine(work_date, end_t)

    if end_dt <= start_dt:
        st.warning("⚠️ Время конца должно быть позже времени начала.")
    else:
        total_seconds = (end_dt - start_dt).total_seconds()
        worked_seconds = total_seconds - break_min * 60

        if worked_seconds <= 0:
            st.warning("⚠️ Перерыв больше или равен отработанному времени.")
        else:
            hours = worked_seconds / 3600
            total = max(hours * rate + materials, MIN_TOTAL)

            with st.container(border=True):
                st.markdown(
                    f'<div class="timer-status" style="margin-top:4px;">'
                    f'🕒 {fmt_hms(total_seconds)} − перерыв {break_min} мин · 💼 {hours:.2f} ч</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="pay-big">💲 К оплате: {money(total)}</div>', unsafe_allow_html=True)

                with st.expander("✉️ Текст для клиента"):
                    msg = build_message(
                        fmt_clock(start_t), fmt_clock(end_t), break_min,
                        hours, rate, materials, total,
                    )
                    message_with_copy(msg, key="manual")

                client = st.text_input("👤 Имя клиента", value="", placeholder="Например: Иван, кухня", key="m_client")
                if st.button("💾 Сохранить", use_container_width=True, type="primary", key="m_save"):
                    add_history_entry(
                        f"{work_date:%Y-%m-%d} {start_t:%H:%M}–{end_t:%H:%M}",
                        client, fmt_hms(worked_seconds), hours, rate, materials, total,
                        break_min=break_min,
                    )
                    st.toast("💾 Работа сохранена в историю")

# =======================================================================
#  Вкладка 3: история работ
# =======================================================================
with tab_history:
    history = get_history()
    st.markdown(
        '<div class="sec-label" style="margin-bottom:6px;">История работ · '
        'все ваши расчёты и заработок</div>',
        unsafe_allow_html=True,
    )
    if history:
        # Один проход: общий заработок и суммы по дням (для среднего и графика)
        total_earned = 0.0
        per_day = {}
        for item in history:
            try:
                amt = float(item.get("total", 0) or 0)
            except (ValueError, TypeError):
                continue
            total_earned += amt
            day = str(item.get("date", ""))[:10]
            per_day[day] = per_day.get(day, 0.0) + amt

        # Градиентный блок-итог
        st.markdown(
            '<div class="summary-card">'
            '<div><div class="lbl">Всего работ</div>'
            f'<div class="big">{len(history)}</div></div>'
            '<div style="text-align:right"><div class="lbl">Заработано</div>'
            f'<div class="mid">{money(total_earned)}</div></div>'
            '<div style="font-size:30px;margin-left:8px">👛</div></div>',
            unsafe_allow_html=True,
        )

        # Карточки работ
        for item in history:
            client = html.escape(str(item.get("client", "—")))
            date = html.escape(str(item.get("date", "")))
            try:
                amount = money(float(item.get("total", 0) or 0))
            except (ValueError, TypeError):
                amount = "—"
            try:
                h = float(item.get("hours", 0) or 0)
            except (ValueError, TypeError):
                h = 0.0
            hh, mm = int(h), int(round((h - int(h)) * 60))
            brk = item.get("break", 0) or 0
            meta = f"{hh}ч {mm:02d}м"
            if brk:
                meta += f" · Перерыв {brk}м"
            st.markdown(
                '<div class="job-card"><div class="top">'
                f'<div><div class="date">{date}</div><div class="client">{client}</div></div>'
                f'<div class="amount">{amount}</div></div>'
                f'<div class="meta">⏱ {meta}</div></div>',
                unsafe_allow_html=True,
            )

        # Средний заработок в день + мини-график
        avg = total_earned / max(1, len(per_day))
        recent = [per_day[k] for k in sorted(per_day.keys())][-12:]
        bars = ""
        if recent:
            mx = max(recent) or 1
            for v in recent:
                hpx = 6 + int((v / mx) * 34)
                cls = "hot" if v == mx else ""
                bars += f'<span class="{cls}" style="height:{hpx}px"></span>'
        st.markdown(
            '<div class="avg-card"><div>'
            '<div class="lbl">Средний заработок в день</div>'
            f'<div class="val">{money(avg)}</div></div>'
            f'<div class="spark">{bars}</div></div>',
            unsafe_allow_html=True,
        )

        with st.expander("⚙️ Экспорт и очистка"):
            st.download_button(
                "⬇️ Скачать историю (JSON)",
                data=json.dumps(history, ensure_ascii=False, indent=2),
                file_name="history.json",
                mime="application/json",
                use_container_width=True,
            )
            st.warning("Удаление истории необратимо.")
            if st.button("🗑 Удалить всю историю", type="primary"):
                clear_history()
                st.rerun()
    else:
        with st.container(border=True):
            st.markdown(
                '<p style="text-align:center;color:#8E8EA9;margin:14px 0;">'
                'Пока нет сохранённых работ.<br>Заверши работу и сохрани её.</p>',
                unsafe_allow_html=True,
            )
