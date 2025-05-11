import streamlit as st
import time
import os
from datetime import timedelta

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")

st.title("🛠 Калькулятор стоимости работы")

start_time_file = "start_time.txt"

# 📥 Ввод ставки и минимального времени
rate = st.number_input("💵 Почасовая ставка ($)", min_value=0.0, value=60.0, step=1.0)
min_hours = st.number_input("⏱ Минимальное время (в часах)", min_value=0.0, value=2.0, step=0.5)

# ▶️ Старт
if st.button("▶️ Старт таймера"):
    with open(start_time_file, "w") as f:
        f.write(str(time.time()))
    st.success("✅ Таймер запущен. Можно закрыть страницу или телефон — всё сохранится.")

# 🗑 Сброс
if st.button("🗑 Сбросить таймер"):
    if os.path.exists(start_time_file):
        os.remove(start_time_file)
        st.info("♻️ Таймер сброшен.")
    else:
        st.warning("⛔️ Таймер ещё не был запущен.")

# 🔄 Автообновление каждые 2 сек (только если таймер активен)
if os.path.exists(start_time_file):
    st.experimental_rerun()
    time.sleep(2)

    with open(start_time_file, "r") as f:
        start_time = float(f.read())

    now = time.time()
    elapsed_seconds = now - start_time
    elapsed_td = timedelta(seconds=int(elapsed_seconds))
    elapsed_hours = elapsed_seconds / 3600
    billable_hours = max(elapsed_hours, min_hours)
    total_cost = billable_hours * rate

    st.info(f"⏳ Прошло времени: **{elapsed_td}**")
    st.write(f"💼 Оплачиваемое время: **{billable_hours:.2f} ч**")
    st.write(f"💰 Текущая стоимость: **${total_cost:.2f}**")

# ⏹ Стоп
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

        st.success("🛑 Таймер остановлен.")
        st.write(f"⏰ Общее время: **{elapsed_td}**")
        st.write(f"📦 Оплачиваемое время: **{billable_hours:.2f} ч**")
        st.write(f"💲 Итоговая сумма: **${total_cost:.2f}**")

        os.remove(start_time_file)
    else:
        st.warning("❗️Таймер не был запущен.")
