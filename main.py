import streamlit as st
import time
import os
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")
st.title("🛠 Калькулятор стоимости работы")

start_time_file = "start_time.txt"

# --- состояние ---
if "stop_pressed" not in st.session_state:
    st.session_state.stop_pressed = False
if "stop_data" not in st.session_state:
    st.session_state.stop_data = None

# --- автообновление ---
if not st.session_state.stop_pressed:
    st_autorefresh(interval=2000, limit=None, key="timer-refresh")

# --- ввод ---
rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=1.0)
min_hours = st.number_input("⏱ Минимальное время (в часах)", min_value=0.0, value=2.0, step=0.5)

# --- кнопка старт ---
if st.button("▶️ Старт таймера"):
    with open(start_time_file, "w") as f:
        f.write(str(time.time()))
    st.session_state.stop_pressed = False
    st.session_state.stop_data = None
    st.success("✅ Таймер запущен!")

# --- кнопка сброс ---
if st.button("🗑 Сбросить таймер"):
    if os.path.exists(start_time_file):
        os.remove(start_time_file)
    st.session_state.stop_pressed = False
    st.session_state.stop_data = None
    st.info("♻️ Таймер сброшен.")

# --- текущий таймер или результат ---
if os.path.exists(start_time_file):
    with open(start_time_file, "r") as f:
        start_time = float(f.read())

    now = time.time()
    elapsed_seconds = now - start_time
    elapsed_td = timedelta(seconds=int(elapsed_seconds))
    elapsed_hours = elapsed_seconds / 3600
    billable_hours = max(elapsed_hours, min_hours)
    total_cost = billable_hours * rate

    if st.session_state.stop_pressed:
        st.success("🛑 Таймер остановлен.")
        st.write(f"⏰ Общее время: **{st.session_state.stop_data['elapsed_td']}**")
        st.write(f"📦 Оплачиваемое время: **{st.session_state.stop_data['billable_hours']:.2f} ч**")
        st.write(f"💲 Итоговая сумма: **${st.session_state.stop_data['total_cost']:.2f}**")
    else:
        st.info(f"⏳ Прошло времени: **{elapsed_td}**")
        st.write(f"💼 Оплачиваемое время: **{billable_hours:.2f} ч**")
        st.write(f"💰 Текущая стоимость: **${total_cost:.2f}**")

# --- кнопка стоп ---
if st.button("⏹ Стоп таймера"):
    if os.path.exists(start_time_file):
        with open(start_time_file, "r") as f:
            start_time = float(f.read())

        end_time = time.time()
        elapsed_seconds = end_time - start_time
        elapsed_td = timedelta(seconds=int(elapsed_seconds))
        elapsed_hours = elapsed_seconds / 3600
        billable_hours = max(elapsed_hours, min_hours)
        total_cost = billable_hours * rate

        # сохраняем данные во временное состояние
        st.session_state.stop_data = {
            "elapsed_td": elapsed_td,
            "billable_hours": billable_hours,
            "total_cost": total_cost
        }
        st.session_state.stop_pressed = True