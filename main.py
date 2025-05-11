import streamlit as st
import time

st.set_page_config(page_title="Калькулятор хэндимена")

st.title("⏱ Калькулятор стоимости работы")

if 'start_time' not in st.session_state:
    st.session_state.start_time = None

rate = st.number_input("Введите вашу почасовую ставку ($)", min_value=0.0, value=60.0, step=1.0)
min_hours = st.number_input("Минимальное время (в часах)", min_value=0.0, value=2.0, step=0.5)

if st.button("▶️ Старт таймера"):
    st.session_state.start_time = time.time()
    st.success("⏳ Таймер запущен...")

if st.button("⏹ Стоп таймера") and st.session_state.start_time:
    end_time = time.time()
    elapsed_seconds = end_time - st.session_state.start_time
    elapsed_hours = elapsed_seconds / 3600
    billable_hours = max(elapsed_hours, min_hours)
    total_cost = billable_hours * rate

    st.write(f"⏰ Прошло времени: **{elapsed_hours:.2f} ч**")
    st.write(f"💼 Оплачиваемое время: **{billable_hours:.2f} ч**")
    st.write(f"💰 Сумма к оплате: **${total_cost:.2f}**")

    st.session_state.start_time = None
