import streamlit as st
import time
import os
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")
st.title("🛠 Калькулятор стоимости работы")

start_file = "start_time.txt"
pause_file = "pause_time.txt"

# --- состояние ---
if "paused" not in st.session_state:
    st.session_state.paused = False
if "stop_pressed" not in st.session_state:
    st.session_state.stop_pressed = False
if "stop_data" not in st.session_state:
    st.session_state.stop_data = None

# --- автообновление ---
if not st.session_state.stop_pressed:
    st_autorefresh(interval=2000, limit=None, key="refresh")

# --- ввод данных ---
rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=1.0)
materials = st.number_input("🧱 Стоимость материалов ($)", min_value=0.0, value=0.0, step=1.0)
min_hours = 0.0  # фиксированно 0

# ▶️ Старт
if st.button("▶️ Старт таймера"):
    with open(start_file, "w") as f:
        f.write(str(time.time()))
    if os.path.exists(pause_file):
        os.remove(pause_file)
    st.session_state.paused = False
    st.session_state.stop_pressed = False
    st.session_state.stop_data = None
    st.success("✅ Таймер запущен!")

# ⏸ Пауза
if st.button("⏸ Пауза"):
    if os.path.exists(start_file) and not os.path.exists(pause_file):
        with open(pause_file, "w") as f:
            f.write(str(time.time()))
        st.session_state.paused = True
        st.info("⏸ Таймер на паузе")

# ▶️ Продолжить
if st.button("🔄 Продолжить"):
    if os.path.exists(start_file) and os.path.exists(pause_file):
        with open(start_file, "r") as f:
            start_time = float(f.read())
        with open(pause_file, "r") as f:
            pause_time = float(f.read())
        paused_duration = time.time() - pause_time
        new_start_time = start_time + paused_duration
        with open(start_file, "w") as f:
            f.write(str(new_start_time))
        os.remove(pause_file)
        st.session_state.paused = False
        st.success("▶️ Таймер возобновлён")

# 🗑 Сброс
if st.button("🗑 Сбросить таймер"):
    if os.path.exists(start_file):
        os.remove(start_file)
    if os.path.exists(pause_file):
        os.remove(pause_file)
    st.session_state.paused = False
    st.session_state.stop_pressed = False
    st.session_state.stop_data = None
    st.info("♻️ Таймер сброшен")

# 🔢 Отображение таймера или итогов
if os.path.exists(start_file):
    with open(start_file, "r") as f:
        start_time = float(f.read())
    now = time.time()
    if os.path.exists(pause_file):
        with open(pause_file, "r") as f:
            now = float(f.read())  # время паузы фиксируем
    elapsed_seconds = now - start_time
    elapsed_td = timedelta(seconds=int(elapsed_seconds))
    elapsed_hours = elapsed_seconds / 3600
    billable_hours = max(elapsed_hours, min_hours)
    total_cost = billable_hours * rate + materials

    if st.session_state.stop_pressed:
        st.success("🛑 Таймер остановлен.")
        st.markdown(f"<h3>⏰ Общее время: {st.session_state.stop_data['elapsed_td']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3>📦 Оплачиваемое время: {st.session_state.stop_data['billable_hours']:.2f} ч</h3>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:green;'>💲 Итоговая сумма: ${st.session_state.stop_data['total_cost']:.2f}</h2>", unsafe_allow_html=True)
    else:
        st.info(f"⏳ Прошло времени: **{elapsed_td}**")
        st.write(f"💼 Оплачиваемое время: **{billable_hours:.2f} ч**")
        st.write(f"💰 Ставка + материалы: **${total_cost:.2f}**")

# ⏹ Стоп
if st.button("⏹ Стоп таймера"):
    if os.path.exists(start_file):
        with open(start_file, "r") as f:
            start_time = float(f.read())
        now = time.time()
        if os.path.exists(pause_file):
            with open(pause_file, "r") as f:
                now = float(f.read())
        elapsed_seconds = now - start_time
        elapsed_td = timedelta(seconds=int(elapsed_seconds))
        elapsed_hours = elapsed_seconds / 3600
        billable_hours = max(elapsed_hours, min_hours)
        total_cost = billable_hours * rate + materials

        st.session_state.stop_data = {
            "elapsed_td": elapsed_td,
            "billable_hours": billable_hours,
            "total_cost": total_cost
        }
        st.session_state.stop_pressed = True
        st.session_state.paused = False