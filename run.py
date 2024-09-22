import os
import openai
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from dotenv import load_dotenv
import time
from datetime import datetime


# โหลดตัวแปรจากไฟล์ .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API Key not found. Please set OPENAI_API_KEY in the .env file.")

# รับ API Key จาก environment variable
client = openai.OpenAI(api_key=api_key)

# สร้างฐานข้อมูล SQLite
def create_db():
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thai_text TEXT,
            translated_text TEXT,
            created_at TEXT,
            translation_duration REAL,
            speech_duration REAL,
            total_duration REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# บันทึกการแปลลง SQLite เฉพาะครั้งแรก
def save_translation_if_first_time(thai_text, translated_text, translation_duration, speech_duration):
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM history WHERE thai_text = ? AND translated_text = ?', (thai_text, translated_text))
    result = c.fetchone()
    
    if result is None:
        total_duration = translation_duration + speech_duration
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO history (thai_text, translated_text, created_at, translation_duration, speech_duration, total_duration) VALUES (?, ?, ?, ?, ?, ?)', 
                  (thai_text, translated_text, created_at, translation_duration, speech_duration, total_duration))
        conn.commit()
    
    conn.close()

# ดึงประวัติจาก SQLite
def get_history():
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    c.execute('SELECT id, thai_text, translated_text FROM history order by id desc')
    records = c.fetchall()
    conn.close()
    return records

# แปลภาษาไทยเป็นภาษาอังกฤษ
# แปลภาษาไทยเป็นภาษาอังกฤษ
def translate_text_thai_to_english(text):
    start_time = time.time()
    try:
        response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                      {"role": "system", "content": 
                          "You are a translation assistant that only translates Thai to English. "
                            "Always respond in English, even if the input is in English. "
                        "Ensure the translation is formatted with appropriate spacing and punctuation to make it easier for Text-to-Speech systems to read it clearly."},
                            {"role": "user", "content": text}
                    ],
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=0.7
                    )
        translated_text = response.choices[0].message.content.strip()
        translation_duration = time.time() - start_time
        return translated_text, translation_duration
    except Exception as e:
        messagebox.showerror("Translation Error", f"Error occurred: {str(e)}")
        return No
# แปลงข้อความเป็นเสียงด้วย 'say'
def text_to_speech_with_say(text):
    start_time = time.time()
    try:
        os.system(f'say -v Daniel "{text}"')  # ใช้เสียง Daniel
        speech_duration = time.time() - start_time
        return speech_duration
    except Exception as e:
        messagebox.showerror("Text-to-Speech Error", f"Error occurred: {str(e)}")
        return 0

# เมื่อกดปุ่ม Translate
def translate_text():
    thai_text = input_box.get("1.0", tk.END).strip()
    if thai_text:
        translated_text, translation_duration = translate_text_thai_to_english(thai_text)
        if translated_text:
            output_box.delete(1.0, tk.END)
            output_box.insert(tk.END, translated_text)
            play_button.config(state=tk.NORMAL)
        return translated_text, translation_duration
    else:
        messagebox.showwarning("Input Error", "Please provide Thai text for translation.")
        return None, 0

# เมื่อกดปุ่ม Translate and Play
def translate_and_play():
    translated_text, translation_duration = translate_text()
    if translated_text:
        thai_text = input_box.get("1.0", tk.END).strip()
        speech_duration = text_to_speech_with_say(translated_text)
        save_translation_if_first_time(thai_text, translated_text, translation_duration, speech_duration)
        clear_inputs()
        load_history()

# เมื่อกดปุ่ม Play Sound
def play_sound():
    translated_text = output_box.get("1.0", tk.END).strip()
    if translated_text:
        thai_text = input_box.get("1.0", tk.END).strip()
        speech_duration = text_to_speech_with_say(translated_text)
        save_translation_if_first_time(thai_text, translated_text, 0, speech_duration)
        clear_inputs()
        load_history()

# ฟังก์ชันสำหรับเล่นเสียงจากประวัติ
def play_sound_from_history(translated_text):
    text_to_speech_with_say(translated_text)

# เคลียร์ช่อง input
def clear_inputs():
    input_box.delete(1.0, tk.END)
    output_box.delete(1.0, tk.END)
    play_button.config(state=tk.DISABLED)

# โหลดประวัติการแปล
def load_history():
    records = get_history()
    for row in history_tree.get_children():
        history_tree.delete(row)
    
    # เพิ่ม ORDER BY id DESC เพื่อให้แสดงประวัติจากล่าสุดก่อน
    for record in reversed(records):  
        history_tree.insert('', 'end', values=(record[0], record[1], record[2]))

# ฟังก์ชันสำหรับสร้างปุ่ม Play สำหรับรายการประวัติ
def on_history_select(event):
    selected_item = history_tree.selection()
    if selected_item:
        item = history_tree.item(selected_item)
        translated_text = item['values'][2]  # ดึงข้อความที่แปลจากรายการที่เลือก
        play_sound_from_history(translated_text)

# สร้างหน้าต่างหลัก
root = tk.Tk()
root.title("Thai to English Translator and Speech")
root.geometry("600x500")

# สร้าง input box สำหรับข้อความภาษาไทย
input_label = tk.Label(root, text="Enter Thai Text:")
input_label.pack(pady=5)
input_box = tk.Text(root, height=5, width=60)
input_box.pack(pady=5)

# สร้าง output box สำหรับผลลัพธ์การแปล
output_label = tk.Label(root, text="Translated Text:")
output_label.pack(pady=5)
output_box = tk.Text(root, height=5, width=60)
output_box.pack(pady=5)

# ปุ่ม Translate, Play, และ Translate and Play
translate_button = tk.Button(root, text="Translate", command=translate_text, height=2, width=20)
translate_button.pack(pady=5)

play_button = tk.Button(root, text="Play Sound", command=play_sound, height=2, width=20, state=tk.DISABLED)
play_button.pack(pady=5)

translate_play_button = tk.Button(root, text="Translate and Play", command=translate_and_play, height=2, width=20)
translate_play_button.pack(pady=5)

# แสดงประวัติการแปล
history_label = tk.Label(root, text="Translation History:")
history_label.pack(pady=5)

history_tree = ttk.Treeview(root, columns=('ID', 'Thai Text', 'Translated Text'), show='headings')
history_tree.heading('ID', text='ID')
history_tree.heading('Thai Text', text='Thai Text')
history_tree.heading('Translated Text', text='Translated Text')
history_tree.pack(pady=5, fill=tk.BOTH, expand=True)

# เพิ่มการเลือกประวัติการแปลเพื่อลงปุ่ม Play
history_tree.bind('<Double-1>', on_history_select)

# เริ่มต้นแอป
create_db()  # สร้างฐานข้อมูลหากยังไม่มี
load_history()  # โหลดประวัติการแปล
root.bind('<Return>', lambda event: translate_and_play())
root.mainloop()