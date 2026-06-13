import time
import json
from datetime import datetime, timedelta, time as dt_time

import streamlit as st
from streamlit_local_storage import LocalStorage
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")
st.title("🛠 Калькулятор стоимости работы")

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
st.subheader("⚙️ Параметры")
rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=5.0)
materials = st.number_input("🧱 Материалы ($), необязательно", min_value=0.0, value=0.0, step=1.0)

tab_timer, tab_manual = st.tabs(["⏱ Таймер", "✍️ Ввести вручную"])

# =======================================================================
#  Вкладка 1: живой таймер
# =======================================================================
with tab_timer:
    timer = get_timer()
    running = timer is not None and not timer.get("pause")

    # Живое обновление секунд только пока таймер реально идёт
    if running:
        st_autorefresh(interval=1000, limit=None, key="refresh")

    if timer is None and st.session_state.last_result is None:
        if st.button("▶️ Старт", use_container_width=True, type="primary"):
            set_timer({"start": time.time(), "pause": None, "rate": rate, "materials": materials})
            st.rerun()
        st.info("Нажми «Старт», когда начинаешь работу у клиента.")

    elif timer is not None:
        elapsed_td, hours, total = compute(timer)
        paused = bool(timer.get("pause"))

        st.markdown(
            f"<h1 style='text-align:center; font-variant-numeric: tabular-nums;'>⏱ {elapsed_td}</h1>",
            unsafe_allow_html=True,
        )
        status = "⏸ На паузе" if paused else "🟢 Идёт"
        st.markdown(f"<p style='text-align:center;'>{status}</p>", unsafe_allow_html=True)
        st.write(f"💼 Оплачиваемое время: **{hours:.2f} ч**")
        st.write(f"💰 К оплате сейчас: **${total:.2f}**")

        c1, c2 = st.columns(2)
        if paused:
            if c1.button("🔄 Продолжить", use_container_width=True):
                paused_duration = time.time() - timer["pause"]
                timer["start"] = timer["start"] + paused_duration
                timer["pause"] = None
                set_timer(timer)
                st.rerun()
        else:
            if c1.button("⏸ Пауза", use_container_width=True):
                timer["pause"] = time.time()
                set_timer(timer)
                st.rerun()

        if c2.button("⏹ Стоп", use_container_width=True, type="primary"):
            elapsed_td, hours, total = compute(timer)
            st.session_state.last_result = {
                "elapsed": str(elapsed_td),
                "hours": round(hours, 2),
                "rate": timer.get("rate", 0),
                "materials": timer.get("materials", 0),
                "total": round(total, 2),
            }
            clear_timer()
            st.rerun()

    # Результат после "Стоп": показать сумму и сохранить
    if st.session_state.last_result is not None:
        r = st.session_state.last_result
        st.success("🛑 Работа завершена")
        st.markdown(f"<h3>⏰ Общее время: {r['elapsed']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3>📦 Оплачиваемое время: {r['hours']:.2f} ч</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='color:green;'>💲 К оплате с клиента: ${r['total']:.2f}</h2>",
            unsafe_allow_html=True,
        )

        client = st.text_input("👤 Имя клиента", value="", placeholder="Например: Иван, кухня", key="t_client")
        cc1, cc2 = st.columns(2)
        if cc1.button("💾 Сохранить в историю", use_container_width=True, type="primary", key="t_save"):
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
    st.caption("Если забыл нажать «Старт» — просто укажи, когда начал и закончил.")

    work_date = st.date_input("📅 Дата работы", value=datetime.now().date(), key="m_date")
    c1, c2 = st.columns(2)
    start_t = c1.time_input("🕘 Начало", value=dt_time(9, 0), step=300, key="m_start")
    end_t = c2.time_input("🕔 Конец", value=dt_time(17, 0), step=300, key="m_end")

    # Перерыв: шаг 15 минут, кнопки −/+ у поля
    break_min = st.number_input(
        "☕ Перерыв (минут, шаг 15)", min_value=0, max_value=600, value=0, step=15, key="m_break"
    )
    if break_min:
        st.caption(f"Перерыв: {break_min // 60} ч {break_min % 60} мин" if break_min >= 60
                   else f"Перерыв: {break_min} мин")

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

            st.divider()
            st.write(f"🕒 Интервал: **{fmt_hms(total_seconds)}**  (минус перерыв {break_min} мин)")
            st.write(f"💼 Оплачиваемое время: **{hours:.2f} ч**")
            if materials:
                st.write(f"🧱 Материалы: **${materials:.2f}**")
            st.markdown(
                f"<h2 style='color:green;'>💲 К оплате с клиента: ${total:.2f}</h2>",
                unsafe_allow_html=True,
            )

            client = st.text_input("👤 Имя клиента", value="", placeholder="Например: Иван, кухня", key="m_client")
            if st.button("💾 Сохранить в историю", use_container_width=True, type="primary", key="m_save"):
                add_history_entry(
                    f"{work_date:%Y-%m-%d} {start_t:%H:%M}–{end_t:%H:%M}",
                    client, fmt_hms(worked_seconds), hours, rate, materials, total,
                    break_min=break_min,
                )
                st.toast("💾 Работа сохранена в историю")

# =======================================================================
#  История работ (общая для обеих вкладок)
# =======================================================================
st.divider()
st.subheader("📜 История работ")

history = get_history()
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
    m2.metric("💰 Всего заработано", f"${total_earned:.2f}")

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
    st.caption("Пока нет сохранённых работ. Заверши работу и сохрани её.")
