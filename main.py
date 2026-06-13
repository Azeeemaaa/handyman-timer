import streamlit as st
import time
import os
import csv
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Калькулятор хэндимена", layout="centered")
st.title("🛠 Калькулятор стоимости работы")

start_file = "start_time.txt"
pause_file = "pause_time.txt"
history_file = "history.csv"

HISTORY_FIELDS = ["date", "client", "elapsed", "billable_hours", "rate", "materials", "total"]

# --- работа с историей ---
def load_history():
    if not os.path.exists(history_file):
        return []
    rows = []
    with open(history_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_history_entry(entry):
    file_exists = os.path.exists(history_file)
    with open(history_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

def clear_history():
    if os.path.exists(history_file):
        os.remove(history_file)

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
client = st.text_input("👤 Клиент / описание работы", value="")
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

        # 💾 Сохраняем работу в историю
        save_history_entry({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "client": client.strip() or "—",
            "elapsed": str(elapsed_td),
            "billable_hours": f"{billable_hours:.2f}",
            "rate": f"{rate:.2f}",
            "materials": f"{materials:.2f}",
            "total": f"{total_cost:.2f}",
        })
        st.success("💾 Работа сохранена в историю")

# 📜 История работ
st.divider()
st.subheader("📜 История работ")

history = load_history()
if history:
    # таблица для отображения с понятными заголовками
    display_rows = []
    total_earned = 0.0
    for row in history:
        try:
            total_earned += float(row.get("total", 0) or 0)
        except ValueError:
            pass
        display_rows.append({
            "Дата": row.get("date", ""),
            "Клиент": row.get("client", ""),
            "Время": row.get("elapsed", ""),
            "Часы": row.get("billable_hours", ""),
            "Ставка $": row.get("rate", ""),
            "Материалы $": row.get("materials", ""),
            "Сумма $": row.get("total", ""),
        })

    st.dataframe(display_rows, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Всего работ", len(history))
    with col2:
        st.metric("Общий заработок", f"${total_earned:.2f}")

    # ⬇️ Скачать историю
    with open(history_file, "r", encoding="utf-8") as f:
        csv_data = f.read()
    st.download_button(
        "⬇️ Скачать историю (CSV)",
        data=csv_data,
        file_name="history.csv",
        mime="text/csv",
    )

    # 🗑 Очистить историю
    if st.button("🗑 Очистить историю"):
        clear_history()
        st.rerun()
else:
    st.caption("Пока нет сохранённых работ. Нажмите «⏹ Стоп таймера», чтобы сохранить работу.")
