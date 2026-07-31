"""
Crossword Puzzle Generator - GUI Version
- No CMD window.
- Browse and select CSV.
- Progress bar & status updates.
- Auto-generates PDF, JPG, TXT into 'output' folder.
- Includes 'Open Output' button.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

# ------------------------------------------------------------------
# ALGORİTMA KODU (CMD'den alınan tam mantık)
# ------------------------------------------------------------------
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import random
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")


class FinalCrossword:
    
    def __init__(self, csv_file):
        self.words = []
        with open(csv_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                # Türkçe ve İngilizce başlıkları aynı anda destekle
                word = row.get("kelime") or row.get("word")
                if word:
                    word = word.strip().upper()
                    self.words.append({
                        "id": int(row.get("sira") or row.get("id")),
                        "word": word,
                        "clue": (row.get("ipucu") or row.get("clue")).strip(),
                        "length": len(word)
                    })
        
        if len(self.words) < 3:
            raise ValueError("CSV dosyasında en az 3 kelime olmalı!")
        
        self.size = 150
        self.grid = [[" " for _ in range(self.size)] for _ in range(self.size)]
        self.placed_words = []
        
    def find_common_letters(self, word1, word2):
        common = []
        for i, ch1 in enumerate(word1):
            for j, ch2 in enumerate(word2):
                if ch1 == ch2:
                    common.append((i, j, ch1))
        return common
    
    def build_graph(self):
        self.graph = defaultdict(list)
        for i, w1 in enumerate(self.words):
            for j, w2 in enumerate(self.words):
                if i != j:
                    common = self.find_common_letters(w1["word"], w2["word"])
                    if common:
                        self.graph[w1["word"]].append({
                            "word": w2,
                            "common": common
                        })
    
    def get_most_connected_word(self):
        best = None
        max_connections = -1
        for w in self.words:
            connections = len(self.graph.get(w["word"], []))
            if connections > max_connections:
                max_connections = connections
                best = w
        return best, max_connections
    
    def place_word(self, word, r, c, horizontal):
        w = word["word"]
        for i, ch in enumerate(w):
            if horizontal:
                self.grid[r][c + i] = ch
            else:
                self.grid[r + i][c] = ch
                
        self.placed_words.append({
            **word,
            "row": r,
            "col": c,
            "horizontal": horizontal
        })
    
    def remove_word(self):
        if not self.placed_words:
            return None
        last = self.placed_words.pop()
        w = last["word"]
        
        for i in range(len(w)):
            if last["horizontal"]:
                rr, cc = last["row"], last["col"] + i
            else:
                rr, cc = last["row"] + i, last["col"]
            
            still_used = False
            for p in self.placed_words:
                for j in range(len(p["word"])):
                    pr = p["row"] + (0 if p["horizontal"] else j)
                    pc = p["col"] + (j if p["horizontal"] else 0)
                    if pr == rr and pc == cc:
                        still_used = True
                        break
            if not still_used:
                self.grid[rr][cc] = " "
        return last

    def fits(self, word, r, c, horizontal):
        w = word["word"]
        length = len(w)
        
        if horizontal:
            if r < 0 or r >= self.size or c < 0 or c + length > self.size: return False
        else:
            if c < 0 or c >= self.size or r < 0 or r + length > self.size: return False
        
        if horizontal:
            if c > 0 and self.grid[r][c-1] != " ": return False
            if c + length < self.size and self.grid[r][c+length] != " ": return False
        else:
            if r > 0 and self.grid[r-1][c] != " ": return False
            if r + length < self.size and self.grid[r+length][c] != " ": return False
        
        intersections = 0
        
        for i, ch in enumerate(w):
            if horizontal:
                rr, cc = r, c + i
            else:
                rr, cc = r + i, c
            
            cell = self.grid[rr][cc]
            
            if cell != " " and cell != ch:
                return False
            
            if cell == ch:
                intersections += 1
                continue
            
            if horizontal:
                if rr > 0 and self.grid[rr-1][cc] != " ": return False
                if rr < self.size-1 and self.grid[rr+1][cc] != " ": return False
            else:
                if cc > 0 and self.grid[rr][cc-1] != " ": return False
                if cc < self.size-1 and self.grid[rr][cc+1] != " ": return False
        
        if self.placed_words and intersections == 0:
            return False
            
        return True

    def count_intersections(self, word, r, c, horizontal):
        w = word["word"]
        count = 0
        for i, ch in enumerate(w):
            if horizontal:
                rr, cc = r, c + i
            else:
                rr, cc = r + i, c
            if self.grid[rr][cc] == ch:
                count += 1
        return count

    def get_best_position(self, word, connected_word, common_letters, connected_is_horizontal):
        best = None
        max_intersections = -1
        
        for idx1, idx2, ch in common_letters:
            if connected_is_horizontal:
                r = connected_word["row"] - idx1
                c = connected_word["col"] + idx2
                if self.fits(word, r, c, False):
                    inter = self.count_intersections(word, r, c, False)
                    if inter > max_intersections:
                        max_intersections = inter
                        best = (r, c, False)
            else:
                r = connected_word["row"] + idx2
                c = connected_word["col"] - idx1
                if self.fits(word, r, c, True):
                    inter = self.count_intersections(word, r, c, True)
                    if inter > max_intersections:
                        max_intersections = inter
                        best = (r, c, True)
        
        return best, max_intersections

    def backtrack(self, index):
        if index >= len(self.words):
            return True
        
        word = self.words[index]
        
        if index == 0:
            center = self.size // 2
            r = center
            c = center - len(word["word"]) // 2
            if self.fits(word, r, c, True):
                self.place_word(word, r, c, True)
                if self.backtrack(index + 1):
                    return True
                self.remove_word()
            return False
        
        for placed in self.placed_words:
            common = self.find_common_letters(word["word"], placed["word"])
            if not common:
                continue
            
            pos, intersections = self.get_best_position(word, placed, common, placed["horizontal"])
            if pos:
                self.place_word(word, pos[0], pos[1], pos[2])
                if self.backtrack(index + 1):
                    return True
                self.remove_word()
                
        return False
    
    def build(self):
        random.shuffle(self.words)
        self.build_graph()
        self.words.sort(key=lambda x: x["length"], reverse=True)
        if self.backtrack(0):
            return True
        return False

    def crop(self):
        if not self.placed_words: return 0, 0, 0, 0
        rs, cs = [], []
        for p in self.placed_words:
            for i in range(len(p["word"])):
                if p["horizontal"]:
                    rs.append(p["row"])
                    cs.append(p["col"] + i)
                else:
                    rs.append(p["row"] + i)
                    cs.append(p["col"])
        return min(rs), max(rs), min(cs), max(cs)
    
    def save_txt(self, folder_path):
        if not self.placed_words: return
        r0, r1, c0, c1 = self.crop()
        
        txt_counter = 1
        while True:
            filename = os.path.join(folder_path, f"grid_output_{txt_counter}.txt")
            if not os.path.exists(filename):
                break
            txt_counter += 1
            
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== CROSSWORD GRID ===\n\n")
            for r in range(r0, r1 + 1):
                line = "".join([self.grid[r][c] if self.grid[r][c] != " " else "." for c in range(c0, c1 + 1)])
                f.write(line + "\n")
            f.write("\n=== CLUES ===\n")
            for p in sorted(self.placed_words, key=lambda x: x['id']):
                direction = "Across" if p["horizontal"] else "Down"
                f.write(f"{p['id']}. ({direction}) Clue: {p['clue']}\n")
        return filename

    def draw_single(self, show_letters=False):
        if not self.placed_words:
            return None
        
        r0, r1, c0, c1 = self.crop()
        padding = 2
        r0 = max(0, r0 - padding)
        r1 = min(self.size - 1, r1 + padding)
        c0 = max(0, c0 - padding)
        c1 = min(self.size - 1, c1 + padding)
        
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        
        fig, ax = plt.subplots(figsize=(max(16, w * 0.5), max(6, h * 0.5)))
        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.invert_yaxis()
        ax.axis('off')
        
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                ch = self.grid[r][c]
                x = c - c0
                y = r - r0
                
                if ch != " ":
                    facecolor = '#FFF9C4'
                    rect = patches.Rectangle((x, y), 1, 1, linewidth=1.5, edgecolor='#111', facecolor=facecolor)
                    ax.add_patch(rect)
                    
                    if show_letters:
                        ax.text(x + 0.5, y + 0.5, ch, ha="center", va="center", fontsize=14, fontweight="bold", color='#1a1a1a')
                    
                    if (r, c) in {(p["row"], p["col"]) for p in self.placed_words}:
                        num = [p["id"] for p in self.placed_words if p["row"] == r and p["col"] == c][0]
                        ax.text(x + 0.15, y + 0.30, str(num), fontsize=13, ha="center", va="center", color='#D32F2F', fontweight='bold')

        clues_text = "📝 CLUES:\n\n"
        for w in self.words:
            direction = "Across" if any(p["word"] == w["word"] and p["horizontal"] for p in self.placed_words) else "Down"
            clues_text += f"{w['id']}. ({direction}) {w['clue']}\n"
        
        plt.figtext(1.02, 0.5, clues_text, ha='left', va='center', fontsize=12, 
                   bbox=dict(facecolor='white', edgecolor='#333', alpha=0.9, pad=10), 
                   transform=ax.transAxes)

        plt.tight_layout()
        return fig

    def save_all(self):
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        counter = 1
        while True:
            pdf_filename = os.path.join(output_dir, f"crossword_{counter}.pdf")
            if not os.path.exists(pdf_filename):
                break
            counter += 1
            
        with PdfPages(pdf_filename) as pdf:
            fig1 = self.draw_single(show_letters=False)
            pdf.savefig(fig1, bbox_inches="tight")
            plt.close(fig1)
            
            fig2 = self.draw_single(show_letters=True)
            pdf.savefig(fig2, bbox_inches="tight")
            plt.close(fig2)
        
        txt_filename = self.save_txt(output_dir)

        fig_student = self.draw_single(show_letters=False)
        student_jpg = os.path.join(output_dir, f"student_crossword_{counter}.jpg")
        fig_student.savefig(student_jpg, dpi=300, bbox_inches="tight", facecolor='white')
        plt.close(fig_student)

        fig_answer = self.draw_single(show_letters=True)
        answer_jpg = os.path.join(output_dir, f"answer_key_{counter}.jpg")
        fig_answer.savefig(answer_jpg, dpi=300, bbox_inches="tight", facecolor='white')
        plt.close(fig_answer)

        return pdf_filename, student_jpg, answer_jpg, txt_filename


# ------------------------------------------------------------------
# GUI ARAYÜZÜ
# ------------------------------------------------------------------
class CrosswordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧩 Crossword Generator")
        self.root.geometry("520x400")
        self.root.resizable(False, False)

        # Başlık
        tk.Label(root, text="🧩 Crossword Generator", font=("Arial", 20, "bold")).pack(pady=15)

        # CSV Seçim Alanı
        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Label(frame, text="CSV File:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.file_label = tk.Label(frame, text="No file selected", fg="gray", font=("Arial", 10))
        self.file_label.pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Browse", command=self.select_file, bg="#ddd").pack(side=tk.LEFT, padx=5)

        # Durum Etiketi
        self.status_label = tk.Label(root, text="Waiting for file...", font=("Arial", 10), fg="#666")
        self.status_label.pack(pady=10)

        # İlerleme Çubuğu
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=350, mode='indeterminate')
        self.progress.pack(pady=5)

        # Butonlar
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        self.btn_gen = tk.Button(btn_frame, text="Generate", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white",
                                 width=12, command=self.start_generation, state=tk.DISABLED)
        self.btn_gen.pack(side=tk.LEFT, padx=10)

        self.btn_open = tk.Button(btn_frame, text="📂 Open Output", font=("Arial", 11), bg="#2196F3", fg="white",
                                  width=12, command=self.open_output, state=tk.DISABLED)
        self.btn_open.pack(side=tk.LEFT, padx=10)

        # Alt not
        tk.Label(root, text="Files will be saved to 'output' folder", font=("Arial", 9), fg="#888").pack(side=tk.BOTTOM, pady=10)

        self.csv_path = None

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.csv_path = path
            self.file_label.config(text=os.path.basename(path), fg="green")
            self.btn_gen.config(state=tk.NORMAL)
            self.status_label.config(text="Ready to generate", fg="blue")
            self.btn_open.config(state=tk.DISABLED)

    def open_output(self):
        output_dir = os.path.join(os.getcwd(), "output")
        if os.path.exists(output_dir):
            os.startfile(output_dir) if sys.platform == "win32" else os.system(f"open '{output_dir}'")
        else:
            messagebox.showinfo("Info", "No output folder found yet. Generate first.")

    def start_generation(self):
        if not self.csv_path:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return

        self.btn_gen.config(state=tk.DISABLED, text="Generating...")
        self.progress.start()
        self.status_label.config(text="Solving crossword... Please wait.", fg="orange")
        self.root.update()

        thread = threading.Thread(target=self._run_generation)
        thread.daemon = True
        thread.start()

    def _run_generation(self):
        try:
            cw = FinalCrossword(self.csv_path)
            if cw.build():
                cw.save_all()
                self.root.after(0, self._on_success)
            else:
                self.root.after(0, self._on_fail, "No valid placement found. Try a different CSV.")
        except Exception as e:
            self.root.after(0, self._on_fail, str(e))

    def _on_success(self):
        self.progress.stop()
        self.btn_gen.config(state=tk.NORMAL, text="Generate")
        self.status_label.config(text="✅ Done! Crossword generated successfully.", fg="green")
        self.btn_open.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "Crossword generated successfully!\n\nCheck the 'output' folder.")

    def _on_fail(self, msg):
        self.progress.stop()
        self.btn_gen.config(state=tk.NORMAL, text="Generate")
        self.status_label.config(text=f"❌ Error: {msg}", fg="red")
        self.btn_open.config(state=tk.DISABLED)
        messagebox.showerror("Error", msg)


# ------------------------------------------------------------------
# BAŞLAT
# ------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CrosswordApp(root)
    root.mainloop()