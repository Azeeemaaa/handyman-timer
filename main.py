import time
import json
from datetime import datetime, timedelta

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

timer = get_timer()
running = timer is not None and not timer.get("pause")

# Живое обновление секунд только пока таймер реально идёт
if running:
    st_autorefresh(interval=1000, limit=None, key="refresh")

# ---------- ввод ставки ----------
st.subheader("⚙️ Параметры")
rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=5.0)
materials = st.number_input("🧱 Материалы ($), необязательно", min_value=0.0, value=0.0, step=1.0)

st.divider()

# ---------- управление таймером ----------
if timer is None and st.session_state.last_result is None:
    # таймер не запущен
    if st.button("▶️ Старт", use_container_width=True, type="primary"):
        set_timer({"start": time.time(), "pause": None, "rate": rate, "materials": materials})
        st.rerun()
    st.info("Нажми «Старт», когда начинаешь работу у клиента.")

elif timer is not None:
    # таймер запущен (идёт или на паузе)
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
            # сдвигаем старт на длительность паузы, чтобы не считать время простоя
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

# ---------- результат после "Стоп": показать сумму и сохранить ----------
if st.session_state.last_result is not None:
    r = st.session_state.last_result
    st.success("🛑 Работа завершена")
    st.markdown(f"<h3>⏰ Общее время: {r['elapsed']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3>📦 Оплачиваемое время: {r['hours']:.2f} ч</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='color:green;'>💲 К оплате с клиента: ${r['total']:.2f}</h2>",
        unsafe_allow_html=True,
    )

    client = st.text_input("👤 Имя клиента", value="", placeholder="Например: Иван, кухня")
    cc1, cc2 = st.columns(2)
    if cc1.button("💾 Сохранить в историю", use_container_width=True, type="primary"):
        history = get_history()
        history.insert(0, {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "client": client.strip() or "—",
            "elapsed": r["elapsed"],
            "hours": r["hours"],
            "rate": r["rate"],
            "materials": r["materials"],
            "total": r["total"],
        })
        set_history(history)
        st.session_state.last_result = None
        st.rerun()
    if cc2.button("❌ Не сохранять", use_container_width=True):
        st.session_state.last_result = None
        st.rerun()

# ---------- история работ ----------
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
    st.caption("Пока нет сохранённых работ. Заверши работу кнопкой «Стоп» и сохрани её.")
