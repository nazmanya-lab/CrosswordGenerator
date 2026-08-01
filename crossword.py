"""
Crossword Puzzle Generator - Final Version (CMD, Output Folder + PDF)
- Creates an 'output' folder.
- Saves all files (JPG, TXT, PDF) into that folder.
- Student page & Answer key combined into a single PDF.
"""

import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import random
import os
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
        print(f"📌 First word placed: {self.words[0]['word']}")
        
        if self.backtrack(0):
            print(f"\n✅ Solution found! {len(self.placed_words)}/{len(self.words)} words placed.")
        else:
            print("\n❌ All combinations tried, but no solution was found.")
            return False
        return True

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
        
        # --- DÜZELTİLEN KISIM BAŞLANGICI ---
        # Her başlangıç karesine (yatay veya dikey) 1'den başlayarak sırayla numara ver
        start_positions = set()
        for p in self.placed_words:
            start_positions.add((p["row"], p["col"]))
        
        number_map = {}
        counter = 1
        for r, c in sorted(start_positions):
            number_map[(r, c)] = counter
            counter += 1
        # --- DÜZELTİLEN KISIM SONU ---
        
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
                    
                    # --- NUMARA BASMA KISMI DÜZELTİLDİ ---
                    if (r, c) in number_map:
                        num = number_map[(r, c)]
                        ax.text(x + 0.15, y + 0.30, str(num), fontsize=13, ha="center", va="center", color='#D32F2F', fontweight='bold')
                    # -------------------------------------

        # --- İPUCU LİSTESİ DÜZELTİLDİ ---
        clues_text = "📝 CLUES:\n\n"
        # Sırayla gitmek için numaraları sıralı dolaş
        for (r, c), num in sorted(number_map.items(), key=lambda x: x[1]):
            # Bu kareden başlayan kelimeleri bul
            for p in self.placed_words:
                if p["row"] == r and p["col"] == c:
                    direction = "Across" if p["horizontal"] else "Down"
                    clues_text += f"{num}. ({direction}) {p['clue']}\n"
        # ---------------------------------
        
        plt.figtext(1.02, 0.5, clues_text, ha='left', va='center', fontsize=12, 
                   bbox=dict(facecolor='white', edgecolor='#333', alpha=0.9, pad=10), 
                   transform=ax.transAxes)

        plt.tight_layout()
        return fig

    def save_all(self):
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created folder: {output_dir}")
        
        counter = 1
        while True:
            pdf_filename = os.path.join(output_dir, f"crossword_{counter}.pdf")
            if not os.path.exists(pdf_filename):
                break
            counter += 1
            
        with PdfPages(pdf_filename) as pdf:
            print("📄 Generating student page...")
            fig1 = self.draw_single(show_letters=False)
            pdf.savefig(fig1, bbox_inches="tight")
            plt.close(fig1)
            
            print("📄 Generating answer key page...")
            fig2 = self.draw_single(show_letters=True)
            pdf.savefig(fig2, bbox_inches="tight")
            plt.close(fig2)
            
        print(f"✅ PDF saved: {pdf_filename}")
        
        txt_filename = self.save_txt(output_dir)
        print(f"✅ TXT saved: {txt_filename}")

        fig_student = self.draw_single(show_letters=False)
        student_jpg = os.path.join(output_dir, f"student_crossword_{counter}.jpg")
        fig_student.savefig(student_jpg, dpi=300, bbox_inches="tight", facecolor='white')
        plt.close(fig_student)
        print(f"✅ Student JPG saved: {student_jpg}")

        fig_answer = self.draw_single(show_letters=True)
        answer_jpg = os.path.join(output_dir, f"answer_key_{counter}.jpg")
        fig_answer.savefig(answer_jpg, dpi=300, bbox_inches="tight", facecolor='white')
        plt.close(fig_answer)
        print(f"✅ Answer JPG saved: {answer_jpg}")

        return pdf_filename, student_jpg, answer_jpg, txt_filename


# ----------------------------------------------------
# MAIN EXECUTION (CMD)
# ----------------------------------------------------
def create_sample_csv():
    sample_file = "sample_words.csv"
    if not os.path.exists(sample_file):
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("id,word,clue,length\n")
            f.write("1,ACCEPT,To agree to receive or take something,6\n")
            f.write("2,ENCOURAGE,To give support or confidence to someone,9\n")
            f.write("3,EXPLAIN,To make an idea or situation clear,7\n")
            f.write("4,POSSESS,To have or own something,8\n")
            f.write("5,EXPRESS,To convey thoughts or feelings,7\n")
            f.write("6,OCCUR,To happen or take place unexpectedly,5\n")
            f.write("7,WANDER,To walk without a specific goal,6\n")
            f.write("8,LOSE,To misplace or fail to keep something,4\n")
            f.write("9,CARE,To feel concern or interest in something,4\n")
            f.write("10,REQUIRE,To need something for a purpose,7\n")
            f.write("11,ACHIEVE,To successfully reach a goal,7\n")
            f.write("12,DECIDE,To make a choice or judgment,6\n")
        print(f"✅ Sample CSV created: '{sample_file}'")
    return sample_file


def select_csv_file():
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    
    if not csv_files:
        print("⚠️ No CSV files found. Creating sample...")
        sample = create_sample_csv()
        csv_files.append(sample)
    
    print("\n📂 Available CSV files:")
    for i, file in enumerate(csv_files):
        print(f"   {i+1}. {file}")
    
    while True:
        try:
            choice = input("\n👉 Select a file number (or press Enter for #1): ").strip()
            if choice == "":
                return csv_files[0]
            idx = int(choice) - 1
            if 0 <= idx < len(csv_files):
                return csv_files[idx]
            else:
                print(f"❌ Please enter a number between 1 and {len(csv_files)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


# ----------------------------------------------------
# MAIN EXECUTION (OTOMATİK DENEME DÖNGÜSÜ)
# ----------------------------------------------------
if __name__ == "__main__":
    while True:
        print("\n🧩 CROSSWORD GENERATOR")
        print("=====================")
        selected_file = select_csv_file()
        print(f"\n📂 Using file: {selected_file}")
        
        deneme_sayisi = 0
        while True:
            deneme_sayisi += 1
            print(f"\n🔄 Attempt #{deneme_sayisi}...", end=" ")
            
            try:
                cw = FinalCrossword(selected_file)
                if cw.build():
                    cw.save_all()
                    print(f"✅ Found a solution on attempt #{deneme_sayisi}!")
                    break
                else:
                    print("❌ Failed, trying a different order...")
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print("\n" + "="*50)
        choice = input("🔄 Try a different CSV file? (Press Enter for YES, type 'q' and Enter to QUIT): ").strip().lower()
        if choice == "q":
            print("👋 Goodbye!")
            break
        print("\n" + "="*50)