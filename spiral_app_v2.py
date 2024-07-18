import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox, filedialog
import mido
import os

idx = 0
current_step = 0
on_note = np.array([], dtype=int)
update_plot_id = None

# 기초 상수 정리
pi = np.pi
N = 12 * 8
r = 2 ** (1 / 12)
f_i = 33
note_i = -1
f = f_i * r ** np.linspace(-32 + note_i, N - 2, num=128)
f_P = f_i * r ** np.linspace(-32 + note_i, N - 2, num=512)
theta = pi / 2 - 2 * pi * np.log2(f / f_i)
theta_P = pi / 2 - 2 * pi * np.log2(f_P / f_i)
A = np.log2(1. / f)
A_P = np.log2(1. / f_P)

# 그래프를 업데이트하는 함수
def update_plot():
    global current_step, idx, on_note, update_plot_id
    if current_step <= total_t:
        track = seq[idx]
        t = current_step
        if track[3] <= t:
            idx += 1
            if track[0] == 1:
                on_note = np.append(on_note, track[1])
            else:
                on_note = np.delete(on_note, np.where(on_note == track[1]))

        x = theta[on_note]
        y = A[on_note]

        # 그래프 초기화
        ax.clear()

        # 새로운 점 플롯
        ax.plot(theta, A, 'b-', x, y, 'ro')

        # 캔버스 업데이트
        canvas.draw()
        current_step += 1

        # 다음 업데이트 예약 (tick_time 후)
        update_plot_id = (root.after(tick_time, update_plot))

# 프로그램 종료 함수
def on_closing():
    global update_plot_id
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        if update_plot_id is not None:
            root.after_cancel(update_plot_id)
        root.quit()
        root.destroy()

# numpy 파일 목록을 불러오는 함수
def load_files():
    try:
        folder_selected = filedialog.askdirectory()
        mid_files = [f for f in os.listdir(folder_selected) if f.endswith('.mid')]
        listbox.delete(0, tk.END)  # 기존 항목 삭제
        for file in mid_files:
            listbox.insert(tk.END, os.path.join(folder_selected, file))
        if mid_files:
            listbox.select_set(0)  # 첫 번째 항목 선택
            listbox.activate(0)    # 첫 번째 항목 활성화
    except Exception as e:
        print(f"Error loading files: {e}")
        return

# 한 타임 스텝당 시간 계산 함수
def calculate_tick_time(midi_file_path):
    midi_file = mido.MidiFile(midi_file_path)
    tempo = 500000  # 기본 템포 (120 BPM)
    ticks_per_beat = midi_file.ticks_per_beat

    for msg in midi_file:
        if msg.type == 'set_tempo':
            tempo = msg.tempo
            break  # 첫 번째 템포 이벤트만 고려

    tick_time_ms = (tempo / ticks_per_beat) / 1000  # 밀리초 단위로 변환
    return tick_time_ms

# 그래프 제목 설정 및 그래프 표시 함수
def set_title_and_show_graph():
    global total_t, seq, tick_time, fig, ax, canvas
    title = listbox.get(listbox.curselection())
    if not title.endswith('.mid'):
        messagebox.showerror("Input Error", "The title must end with an '.mid'. Please try again.")
        return

    try:
        mid = mido.MidiFile(title)
    except Exception as e:
        messagebox.showerror("Import Error", f"File does not exist or cannot be opened: {e}. Please try again.")
        return

    seq = mid2seq(mid)
    total_t = np.max(seq[:, 3])
    tick_time = int(calculate_tick_time(title))
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})

    # Figure를 Tkinter 캔버스에 넣기
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # 입력 프레임 숨기기
    listbox.pack_forget()
    load_button.pack_forget()
    execute_button.pack_forget()

    # 초기 업데이트 호출
    global update_plot_id
    update_plot_id=(root.after(tick_time, update_plot))

# MIDI 파일을 배열로 변환하는 함수
def mid2seq(mid):
    seq = np.zeros((len(mid.tracks[0]), 4), dtype=int)
    idx = 0
    t = 0
    for msg in mid.tracks[0]:
        if msg.type == 'note_on':
            n = msg.note
            v = msg.velocity
            t += msg.time
            ty = 1
            seq[idx] = np.array([ty, n, v, t])
            idx += 1
        elif msg.type == 'note_off':
            n = msg.note
            v = msg.velocity
            t += msg.time
            ty = 0
            seq[idx] = np.array([ty, n, v, t])
            idx += 1
    return seq

# Tkinter 설정
root = tk.Tk()
root.title("MIDI Input Display")
root.protocol("WM_DELETE_WINDOW", on_closing)

# 윈도우 크기 및 위치 설정
window_width = 800
window_height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

file_frame = ttk.Frame(root)
file_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

file_label = ttk.Label(file_frame, text="Select folder")
file_label.pack(side=tk.TOP)

# 파일 불러오기 버튼
load_button = ttk.Button(file_frame, text="Load Files", command=load_files)
load_button.pack(side=tk.BOTTOM, padx=5)

# Listbox 설정
listbox = tk.Listbox(file_frame)
listbox.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

execute_frame = ttk.Frame(root)
execute_frame.pack(side=tk.BOTTOM)

# 실행 버튼
execute_button = ttk.Button(execute_frame, text="execute", command=set_title_and_show_graph)
execute_button.pack(side=tk.LEFT)

# Tkinter 메인 루프 실행
root.mainloop()
