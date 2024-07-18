import numpy as np
import tkinter as tk
from tkinter import ttk
import mido
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from tkinter import messagebox
import os

idx = 0
current_step=0
on_note = np.array([], dtype=int)

def update_plot():
    global current_step
    global idx
    global on_note
    if current_step <= total_t:
        track = seq[idx]
        t = current_step
        if track[3] <= t :
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

        # 다음 업데이트 예약 (1000ms 후)
        root.after(1, update_plot)


def mid2seq(mid):
    # input: midi, output: np.array(note_on/off, note, velocity, time)
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

# 기초 상수 정리
pi = np.pi
N = 12*8
r = 2**(1/12)
f_i = 33
note_i = -1
f = f_i*r**np.linspace(-32+note_i, N-2, num=128)
f_P = f_i*r**np.linspace(-32+note_i, N-2, num=512)
theta = pi/2 - 2*pi*np.log2(f/f_i)
theta_P = pi/2 - 2*pi*np.log2(f_P/f_i)
A = np.log2(1./f)
A_P = np.log2(1./f_P)

title = "./barabom.mid"
mid = mido.MidiFile(title)
seq = mid2seq(mid)
total_t = np.max(seq[:, 3])

# Tkinter 설정
root = tk.Tk()
root.title("MIDI Input Display")

# 윈도우 크기 및 위치 설정
window_width = 400
window_height = 300
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height/2 - window_height/2)
position_right = int(screen_width/2 - window_width/2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# Matplotlib 설정
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.set_ylim(0, 10)

# Figure를 Tkinter 캔버스에 넣기
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# 초기 업데이트 호출
root.after(1, update_plot)

# Tkinter 메인 루프 실행
root.mainloop()