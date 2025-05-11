import streamlit as st
import time
import os

st.set_page_config(page_title="Калькулятор хэндимена")

st.title("⏱ Калькулятор стоимости работы")

# Путь к файлу, где сохраняется время запуска
start_time_file = "start_time.txt"

rate = st.number_input("Введите вашу почасовую ставку ($)", min_value=0.0, value=60.0, step=1.0)
min_hours = st.number_input("Минимальное время (в часах)", min_value=0.0, value=2.0, step=0.5)

# Кнопка Старт
if st.button("▶️ Старт таймера"):
    with open(start_time_file, "w") as f:
        f.write(str(time.time()))
    st.success("⏳ Таймер запущен и сохранён. Можно закрыть страницу — он продолжит работать.")

# Кнопка Стоп
if st.button("⏹ Стоп таймера"):
    if os.path.exists(start_time_file):
        with open(start_time_file, "r") as f:
            start_time = float(f.read())
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        elapsed_hours = elapsed_seconds / 3600
        billable_hours = max(elapsed_hours, min_hours)
        total_cost = billable_hours * rate

        st.write(f"⏰ Прошло времени: **{elapsed_hours:.2f} ч**")
        st.write(f"💼 Оплачиваемое время: **{billable_hours:.2f} ч**")
        st.write(f"💰 Сумма к оплате: **${total_cost:.2f}**")

        os.remove(start_time_file)
    else:
        st.warning("❗️Таймер не был запущен или файл потерян.")
