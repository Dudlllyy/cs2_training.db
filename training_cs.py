import customtkinter as ctk
import sqlite3
import threading
import time
import os
import re
from datetime import datetime

# ==========================================
# БАЗА ДАННЫХ И ХРАНИЛИЩЕ
# ==========================================
session_results = []
is_tracking = False  # Флаг для управления фоновым потоком


def init_db():
    with sqlite3.connect("cs2_stats.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions
                          (
                              id
                              INTEGER
                              PRIMARY
                              KEY
                              AUTOINCREMENT,
                              date
                              TEXT,
                              good
                              INTEGER,
                              normal
                              INTEGER,
                              bad
                              INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS results
                          (
                              id
                              INTEGER
                              PRIMARY
                              KEY
                              AUTOINCREMENT,
                              session_id
                              INTEGER,
                              mode
                              TEXT,
                              score
                              TEXT,
                              grade
                              TEXT
                          )''')
        conn.commit()


def save_and_get_previous(good, normal, bad):
    with sqlite3.connect("cs2_stats.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, good, normal, bad FROM sessions ORDER BY id DESC LIMIT 1")
        last_session = cursor.fetchone()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO sessions (date, good, normal, bad) VALUES (?, ?, ?, ?)", (now, good, normal, bad))
        session_id = cursor.lastrowid

        for r in session_results:
            cursor.execute("INSERT INTO results (session_id, mode, score, grade) VALUES (?, ?, ?, ?)",
                           (session_id, r['mode'], str(r['score']), r['grade']))
        conn.commit()
    return last_session


# ==========================================
# ЛОГИКА ПАРСЕРА
# ==========================================
def time_to_seconds(time_str):
    if not time_str: return 0
    m, s = time_str.split(':')
    return int(m) * 60 + float(s)


def get_grade(current, pb, lower_is_better=False):
    if not pb or pb == 0: return "🟩 Отлично (Первая игра)"
    percent = (pb / current) * 100 if lower_is_better else (current / pb) * 100
    if percent >= 90:
        return "🟩 Отлично"
    elif percent >= 75:
        return "🟨 Нормально"
    else:
        return "🟥 Плохо"


def analyze_log_line(line, log_callback):
    global session_results

    if "- Accuracy:" in line:
        is_pb = "You beat your personal best for" in line
        pattern = r"(?:for\s)?(.*?):\s(\d{2}:\d{2}\.\d{2})\s-\sAccuracy:\s([\d.]+)%\s-\sKPS:\s([\d.]+)"
        match = re.search(pattern, line)
        if match:
            mode = match.group(1).strip()
            if ":" in mode: mode = mode.split(":")[-1].strip()
            if is_pb: mode = mode.replace("You beat your personal best ", "").replace(
                "You beat your personal best for ", "")

            time_str = match.group(2)
            current_sec = time_to_seconds(time_str)
            grade = get_grade(current_sec, 0, lower_is_better=True)

            session_results.append({"mode": mode, "score": time_str, "grade": grade})
            log_callback(f"[+] Записан результат: {mode} | Время: {time_str} | Оценка: {grade}")

    elif "Reached round" in line:
        pattern = r"Reached round (\d+) with (\d+) bots still alive\.\s*\(Best:\s*(\d+)\)"
        match = re.search(pattern, line)
        if match:
            round_num = int(match.group(1))
            best_score = int(match.group(3))
            grade = get_grade(round_num, best_score)

            session_results.append({"mode": "Combat", "score": f"Раунд {round_num}", "grade": grade})
            log_callback(f"[+] Записан результат: Combat | Раунд: {round_num} | Оценка: {grade}")

    elif any(x in line for x in ["Flick Score:", "Blitz Score:", "Yuki Score:", "Multi Score:", "Strafe Score:"]):
        pattern = r"(Flick|Blitz|Yuki|Multi|Strafe)\s+Score:\s*(\d+)\s*\|\s*Accuracy:\s*([\d.]+)%(?:\s*\(\s*PB:\s*(\d+)\s*\))?"
        match = re.search(pattern, line)
        if match:
            mode_name = match.group(1)
            score = int(match.group(2))
            pb_score = int(match.group(4)) if match.group(4) else 0
            grade = get_grade(score, pb_score)

            session_results.append({"mode": mode_name, "score": str(score), "grade": grade})
            log_callback(f"[+] Записан результат: {mode_name} | Очки: {score} | Оценка: {grade}")

    elif "kills" in line and "Best:" in line:
        pattern = r"(\d+)\s+kills\s*\(\s*Best:\s*(\d+)\s+on\s+(\d+)\s+bots\s*\)"
        match = re.search(pattern, line)
        if match:
            kills = int(match.group(1))
            best_kills = int(match.group(2))
            grade = get_grade(kills, best_kills)

            session_results.append({"mode": "Rush", "score": f"{kills} kills", "grade": grade})
            log_callback(f"[+] Записан результат: Rush | Убито: {kills} | Оценка: {grade}")


def tail_log_file(file_path, log_callback):
    global is_tracking
    while not os.path.exists(file_path) and is_tracking:
        time.sleep(2)

    if not is_tracking: return

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, os.SEEK_END)
            log_callback("Файл найден! Бот слушает результаты...")
            while is_tracking:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                analyze_log_line(line, log_callback)
    except Exception as e:
        log_callback(f"Ошибка чтения файла: {e}")


# ==========================================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (CustomTkinter)
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CS2TrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CS2 Training Analyzer")
        self.geometry("700x550")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        init_db()

        # Поле ввода пути к логу (по умолчанию твой путь)
        self.path_entry = ctk.CTkEntry(self, width=500, placeholder_text="Путь к console.log")
        self.path_entry.insert(0, r"S:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\console.log")
        self.path_entry.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Текстовое окно для вывода логов
        self.log_box = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 13))
        self.log_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # Фрейм для кнопок управления
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="▶ Запустить трекер", fg_color="green",
                                       hover_color="darkgreen", command=self.start_tracking)
        self.start_btn.grid(row=0, column=0, padx=10, pady=0, sticky="ew")

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="⏹ Остановить и показать итоги", fg_color="red",
                                      hover_color="darkred", state="disabled", command=self.stop_and_summarize)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=0, sticky="ew")

    def print_to_gui(self, text):
        """Безопасный вывод текста в виджет из любого потока"""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")  # Автоскролл вниз
        self.log_box.configure(state="disabled")

    def start_tracking(self):
        global is_tracking, session_results
        session_results = []  # Очищаем результаты прошлой сессии
        is_tracking = True

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        self.print_to_gui("🤖 Запуск аналитика...")
        self.print_to_gui("Можно сворачивать окно и идти тренироваться.\n")

        log_path = self.path_entry.get()
        self.thread = threading.Thread(target=tail_log_file, args=(log_path, self.print_to_gui), daemon=True)
        self.thread.start()

    def stop_and_summarize(self):
        global is_tracking, session_results
        is_tracking = False  # Останавливаем фоновый цикл

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        self.print_to_gui("\n" + "=" * 50)
        self.print_to_gui("🏆 ИТОГИ ТРЕНИРОВКИ 🏆")
        self.print_to_gui("=" * 50)

        if not session_results:
            self.print_to_gui("Нет данных. Ты не прошел ни одной тренировки.")
            return

        good, normal, bad = 0, 0, 0
        for i, res in enumerate(session_results, 1):
            self.print_to_gui(f"{i}. {res['mode']} -> Результат: {res['score']} | Вердикт: {res['grade']}")
            if "Отлично" in res['grade']:
                good += 1
            elif "Нормально" in res['grade']:
                normal += 1
            elif "Плохо" in res['grade']:
                bad += 1

        last_session = save_and_get_previous(good, normal, bad)

        self.print_to_gui("-" * 50)
        self.print_to_gui(f"📊 ОБЩИЙ БАЛЛ ЗА СЕГОДНЯ: 🟩 {good} | 🟨 {normal} | 🟥 {bad}")

        if last_session:
            last_date, last_good, last_normal, last_bad = last_session
            self.print_to_gui(f"\n📈 СРАВНЕНИЕ С ПРОШЛОЙ ТРЕНИРОВКОЙ (от {last_date}):")
            if good > last_good:
                self.print_to_gui(f"🚀 Прогресс! Сегодня 'Отличных' больше ({good} vs {last_good}).")
            elif good < last_good:
                self.print_to_gui(f"📉 В прошлый раз было больше 'Отличных' ({last_good} vs {good}).")
            else:
                self.print_to_gui(f"⚖️ Стабильность! Количество 'Отличных' не изменилось.")
        else:
            self.print_to_gui("\n📈 Это твоя первая сессия. Сравнивать пока не с чем!")

        self.print_to_gui("=" * 50)


if __name__ == "__main__":
    app = CS2TrackerApp()
    app.mainloop()