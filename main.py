import time
import json
from datetime import datetime, timedelta, time as dt_time

import streamlit as st
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", page_icon="🛠", layout="centered")


# ---------- iOS-светлый дизайн ----------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --ios-blue:#007AFF; --ios-green:#34C759; --ios-red:#FF3B30;
            --ios-gray:#8E8E93; --ios-fill:#E9E9EF; --bg:#F2F2F7; --card:#FFFFFF;
        }
        .stApp { background: var(--bg); }
        .block-container {
            max-width: 460px; padding-top: 1.4rem; padding-bottom: 4rem;
        }
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        }
        h1 { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; }
        h2, h3 { letter-spacing: -0.01em; }

        /* Карточки (st.container(border=True)) в стиле iOS */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card);
            border: none !important;
            border-radius: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            padding: 14px 16px;
            margin-bottom: 6px;
        }

        /* Кнопки — крупные pill */
        .stButton > button, .stDownloadButton > button {
            border-radius: 14px;
            padding: 0.7rem 1rem;
            font-weight: 600;
            font-size: 17px;
            border: none;
            width: 100%;
            min-height: 50px;
            transition: transform .06s ease, filter .15s ease;
        }
        .stButton > button:active, .stDownloadButton > button:active { transform: scale(0.97); }
        .stButton > button[kind="primary"] { background: var(--ios-blue); color:#fff; }
        .stButton > button[kind="secondary"], .stDownloadButton > button {
            background: var(--ios-fill); color: var(--ios-blue);
        }
        .stButton > button[kind="primary"]:hover { filter: brightness(1.05); color:#fff; }

        /* Цветные акценты по ключам */
        .st-key-start_btn button { background: var(--ios-green) !important; color:#fff !important; }
        .st-key-stop_btn button   { background: var(--ios-red) !important; color:#fff !important; }

        /* Поля ввода */
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input {
            border-radius: 12px; font-size: 16px;
        }

        /* Вкладки -> сегмент-контрол iOS */
        [data-testid="stTabs"] [role="tablist"] {
            background: var(--ios-fill); border-radius: 12px; padding: 4px; gap: 4px;
            border-bottom: none;
        }
        [data-testid="stTabs"] [role="tablist"] button {
            flex: 1; border-radius: 9px; padding: 6px 4px; font-weight: 600;
            color: #1C1C1E;
        }
        [data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] {
            background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }

        /* Метрики */
        [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; }

        /* Заголовок секции (caption) */
        .sec-label {
            color: var(--ios-gray); font-size: 13px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.03em;
            margin: 2px 0 2px 4px;
        }
        /* Большой таймер */
        .big-timer {
            text-align:center; font-size: 3.2rem; font-weight: 800;
            font-variant-numeric: tabular-nums; letter-spacing: -0.02em;
            margin: 4px 0 2px; color:#1C1C1E;
        }
        .timer-status { text-align:center; color: var(--ios-gray); font-weight:600; margin-bottom: 6px; }
        .pay-now { text-align:center; font-size: 1.1rem; color:#1C1C1E; margin-top: 2px; }
        .pay-big { text-align:center; color: var(--ios-green); font-weight:800; font-size: 2rem; margin: 6px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()
st.markdown("<h1>🛠 Расчёт стоимости работы</h1>", unsafe_allow_html=True)

# Хранилище в браузере телефона: данные остаются у тебя и переживают
# перезапуск сервера. Время считается от момента старта, поэтому таймер
# "идёт" даже когда приложение закрыто.
localS = LocalStorage()

TIMER_KEY = "ht_timer"      # активный таймер: {"start": ts, "pause": ts|null, "rate": r, "materials": m}
HISTORY_KEY = "ht_history"  # список завершённых работ


# ---------- работа с хранилищем ----------
def get_timer():
    raw = localS.getItem(TIMER_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def set_timer(data):
    localS.setItem(TIMER_KEY, json.dumps(data), key="set_timer")


def clear_timer():
    if localS.getItem(TIMER_KEY):
        localS.deleteItem(TIMER_KEY, key="del_timer")


def get_history():
    raw = localS.getItem(HISTORY_KEY)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return []


def set_history(items):
    localS.setItem(HISTORY_KEY, json.dumps(items), key="set_history")


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
               border:none; border-radius:14px; background:#007AFF; color:#fff; cursor:pointer;">
        📋 Скопировать текст
      </button>
      <div id="ok_{key}" style="text-align:center; color:#34C759; font-weight:600; margin-top:8px; min-height:20px;"></div>
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
    total = hours * timer.get("rate", 0) + timer.get("materials", 0)
    return timedelta(seconds=int(elapsed_seconds)), hours, total


# ---------- состояние ----------
if "last_result" not in st.session_state:
    st.session_state.last_result = None  # результат после "Стоп", ждёт сохранения

# ---------- общие параметры ----------
st.markdown('<div class="sec-label">Параметры</div>', unsafe_allow_html=True)
with st.container(border=True):
    rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=5.0)
    materials = st.number_input("🧱 Материалы ($), необязательно", min_value=0.0, value=0.0, step=1.0)

tab_timer, tab_manual = st.tabs(["⏱ Таймер", "✍️ Вручную"])

# =======================================================================
#  Вкладка 1: живой таймер
# =======================================================================
with tab_timer:
    timer = get_timer()
    running = timer is not None and not timer.get("pause")

    if running:
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
                st.rerun()

    elif timer is not None:
        elapsed_td, hours, total = compute(timer)
        paused = bool(timer.get("pause"))

        with st.container(border=True):
            st.markdown(f'<div class="big-timer">{elapsed_td}</div>', unsafe_allow_html=True)
            status = "⏸ На паузе" if paused else "🟢 Идёт"
            st.markdown(f'<div class="timer-status">{status}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="pay-now">💼 {hours:.2f} ч &nbsp;·&nbsp; 💰 <b>{money(total)}</b></div>',
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            if paused:
                if c1.button("🔄 Продолжить", use_container_width=True, type="primary", key="resume_btn"):
                    paused_duration = time.time() - timer["pause"]
                    timer["start"] = timer["start"] + paused_duration
                    timer["pause"] = None
                    set_timer(timer)
                    st.rerun()
            else:
                if c1.button("⏸ Пауза", use_container_width=True, key="pause_btn"):
                    timer["pause"] = time.time()
                    set_timer(timer)
                    st.rerun()

            if c2.button("⏹ Стоп", use_container_width=True, type="primary", key="stop_btn"):
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
                clear_timer()
                st.rerun()

    # Результат после "Стоп": показать сумму и сохранить
    if st.session_state.last_result is not None:
        r = st.session_state.last_result
        with st.container(border=True):
            st.markdown('<div style="text-align:center;font-weight:700;">🛑 Работа завершена</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="timer-status">⏰ {r["elapsed"]} · 📦 {r["hours"]:.2f} ч</div>',
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
            total = hours * rate + materials

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
#  История работ (общая для обеих вкладок)
# =======================================================================
st.markdown('<div class="sec-label" style="margin-top:14px;">История работ</div>', unsafe_allow_html=True)

history = get_history()
with st.container(border=True):
    if history:
        total_earned = 0.0
        rows = []
        for item in history:
            try:
                total_earned += float(item.get("total", 0) or 0)
            except (ValueError, TypeError):
                pass
            rows.append({
                "Дата": item.get("date", ""),
                "Клиент": item.get("client", ""),
                "Время": item.get("elapsed", ""),
                "Перерыв": item.get("break", 0),
                "Часы": item.get("hours", ""),
                "Сумма $": item.get("total", ""),
            })

        m1, m2 = st.columns(2)
        m1.metric("Всего работ", len(history))
        m2.metric("💰 Заработано", money(total_earned))

        st.dataframe(rows, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Скачать историю (JSON)",
            data=json.dumps(history, ensure_ascii=False, indent=2),
            file_name="history.json",
            mime="application/json",
            use_container_width=True,
        )

        with st.expander("🗑 Очистить историю"):
            st.warning("Это удалит все сохранённые работы без возможности восстановления.")
            if st.button("Да, удалить всё", type="primary"):
                localS.deleteItem(HISTORY_KEY, key="del_history")
                st.rerun()
    else:
        st.markdown(
            '<p style="text-align:center;color:#8E8E93;margin:10px 0;">'
            'Пока нет сохранённых работ.<br>Заверши работу и сохрани её.</p>',
            unsafe_allow_html=True,
        )
