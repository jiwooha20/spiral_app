import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa
import os
import pygame

# Convert polar coordinates to Cartesian coordinates
def polar_to_cartesian(r, theta):
    return r * np.cos(theta), r * np.sin(theta)

# Calculate the radius based on frequency
def cal_r(freq):
    thresholds = [55, 110, 220, 440, 880, 1760, 3520, 7040, 14080, 28160]
    values = [14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
    for threshold, value in zip(thresholds, values):
        if freq < threshold:
            return value / 15
    return 0.

# Main application class
class MidiVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Input Display")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.idx = 0
        self.current_step = 0
        self.update_plot_id = None
        self.audio_file = None

        # Initialize frequency and angle lists
        self.freq_init = 55
        self.freq_list = np.array(range(1, 1025)) * (22050 / 1024)
        self.r_list = [cal_r(freq) for freq in self.freq_list]
        self.theta_list = (np.pi / 2) - 2 * np.pi * np.log2(self.freq_list / self.freq_init)

        # Initialize note frequencies and angles
        self.note_freq = 55 * 2 ** (np.arange(12) / 12)
        self.note_thetas = (np.pi / 2) - 2 * np.pi * np.log2(self.note_freq / self.freq_init)
        self.note_labels = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

        self.setup_ui()
        pygame.mixer.init()

    # Set up the user interface
    def setup_ui(self):
        window_width, window_height = 800, 600
        screen_width, screen_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        position_top, position_right = (screen_height - window_height) // 2, (screen_width - window_width) // 2
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # Frame for file selection
        file_frame = ttk.Frame(self.root)
        file_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        file_label = ttk.Label(file_frame, text="Select folder")
        file_label.pack(side=tk.TOP)

        self.load_button = ttk.Button(file_frame, text="Load Files", command=self.load_files)
        self.load_button.pack(side=tk.BOTTOM, padx=5)

        self.listbox = tk.Listbox(file_frame)
        self.listbox.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Frame for execute button
        execute_frame = ttk.Frame(self.root)
        execute_frame.pack(side=tk.BOTTOM)

        self.execute_button = ttk.Button(execute_frame, text="Execute", command=self.execute)
        self.execute_button.pack(side=tk.LEFT)

    # Handle the closing of the application
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.update_plot_id is not None:
                self.root.after_cancel(self.update_plot_id)
            pygame.mixer.music.stop()
            self.root.quit()
            self.root.destroy()

    # Load audio files from the selected folder
    def load_files(self):
        try:
            folder_selected = filedialog.askdirectory()
            audio_files = [f for f in os.listdir(folder_selected) if f.endswith(('.mp3', '.wav'))]
            self.listbox.delete(0, tk.END)
            for file in audio_files:
                self.listbox.insert(tk.END, os.path.join(folder_selected, file))
            if audio_files:
                self.listbox.select_set(0)
                self.listbox.activate(0)
        except Exception as e:
            print(f"Error loading files: {e}")

    # Update the plot based on the current audio position
    def update_plot(self):
        current_time = pygame.mixer.music.get_pos() / 1000.0
        if current_time > 0:
            self.current_step = int(current_time / self.real_time)
            if self.current_step < self.time_slot:
                A = self.spectrogram[1:, self.current_step]
                B = self.spectrogram2[1:, self.current_step]
                self.scatter.set_offsets(np.c_[self.theta_list, self.r_list])
                self.scatter.set_array(A)
                self.scatter.set_sizes(B)  
                self.canvas.draw_idle()
                self.update_plot_id = self.root.after(1, self.update_plot)
            else:
                self.root.after_cancel(self.update_plot_id)

    # Execute the visualization
    def execute(self):
        # Program name
        title = self.listbox.get(self.listbox.curselection())

        # Load the audio file
        try:
            audio, sr = librosa.load(title, sr=None)
            self.audio_file = title
        except Exception as e:
            messagebox.showerror("Import Error", f"File does not exist or cannot be opened: {e}. Please try again.")
            return

        # Make spectrogram
        audio = librosa.stft(audio, hop_length=2048, n_fft=2048)
        self.real_time = 2048 / sr
        audio = np.abs(audio)
        audio_max = np.max(audio)

        self.spectrogram = 1 - audio / audio_max
        self.spectrogram2 = (audio / audio_max * 10) ** 2

        self.time_slot = self.spectrogram.shape[1]
        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'})

        # Set grid and label
        self.add_labels_grids()
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.ax.grid(False)

        self.scatter = self.ax.scatter(self.theta_list, self.r_list, c='grey', s=1, cmap='grey', marker='o', vmax=1, vmin=0)

        # Set widget
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # delete initial UI
        self.listbox.pack_forget()
        self.load_button.pack_forget()
        self.execute_button.pack_forget()

        # Playing music
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()

        # Start loop
        self.update_plot_id = self.root.after(1, self.update_plot)

    # Add note labels and grid lines
    def add_labels_grids(self):
        # Add note labels (A, A#, B, C, ...)
        for theta, label in zip(self.note_thetas, self.note_labels):
            self.ax.text(theta, 1, label, fontsize=12, ha='center', va='center')
        
        # Add grid lines for angles (theta)
        for angle in self.note_thetas:
            self.ax.axvline(x=angle, color='yellow', linestyle='--', linewidth=1, alpha=0.5)

        # Add grid lines for radii (r)
        theta = np.linspace(0, 2 * np.pi, 100)
        radii = [14/15, 13/15, 12/15, 11/15, 10/15, 9/15, 8/15, 7/15, 6/15, 5/15]
        for r in radii:
            self.ax.plot(theta, [r] * len(theta), color='yellow', alpha=0.5)


if __name__ == "__main__":
    root = tk.Tk()
    app = MidiVisualizerApp(root)
    root.mainloop()

# pyinstaller -w cont_spiral.py
