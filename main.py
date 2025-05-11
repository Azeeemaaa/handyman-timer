import streamlit as st
import time
import os
from datetime import timedelta

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")

st.title("⏱ Калькулятор стоимости работы")

start_time_file = "start_time.txt"

rate = st.number_input("💵 Ваша почасовая ставка ($)", min_value=0.0, value=60.0, step=1.0)
min_hours = st.number_input("⏱ Минимальное время (в часах)", min_value=0.0, value=2.0, step=0.5)

# Старт
if st.button("▶️ Старт таймера"):
    with open(start_time_file, "w") as f:
        f.write(str(time.time()))
    st.success("✅ Таймер запущен. Можно закрыть страницу или телефон — он всё помнит.")

# Сброс
if st.button("🗑 Сбросить таймер"):
    if os.path.exists(start_time_file):
        os.remove(start_time_file)
        st.info("Таймер сброшен.")
    else:
        st.warning("⛔️ Таймер ещё не был запущен.")

# Отображение таймера (если таймер работает)
if os.path.exists(start_time_file):
    with open(start_time_file, "r") as f:
        start_time = float(f.read())

    while True:
        now = time.time()
        elapsed_seconds = now - start_time
        elapsed_hours = elapsed_seconds / 360
