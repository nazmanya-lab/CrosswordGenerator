import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")

class FinalCrossword:
    
    def __init__(self, csv_file):
        self.kelimeler = []
        with open(csv_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                kelime = row.get("kelime", "").strip().upper()
                if kelime:
                    self.kelimeler.append({
                        "no": int(row["sira"]),
                        "word": kelime,
                        "clue": row["ipucu"].strip(),
                        "harf_sayisi": len(kelime)
                    })
        
        if len(self.kelimeler) < 3:
            print("❌ En az 3 kelime gerekli!")
            return
        
        self.size = 150
        self.grid = [[" " for _ in range(self.size)] for _ in range(self.size)]
        self.yerlesenler = []
        
    def ortak_harf_bul(self, kelime1, kelime2):
        ortaklar = []
        for i, h1 in enumerate(kelime1):
            for j, h2 in enumerate(kelime2):
                if h1 == h2:
                    ortaklar.append((i, j, h1))
        return ortaklar
    
    def iliski_grafi(self):
        self.graf = defaultdict(list)
        for i, w1 in enumerate(self.kelimeler):
            for j, w2 in enumerate(self.kelimeler):
                if i != j:
                    ortaklar = self.ortak_harf_bul(w1["word"], w2["word"])
                    if ortaklar:
                        self.graf[w1["word"]].append({
                            "kelime": w2,
                            "ortaklar": ortaklar
                        })
    
    def en_cok_baglantili(self):
        en_iyi = None
        en_cok = -1
        for w in self.kelimeler:
            baglanti = len(self.graf.get(w["word"], []))
            if baglanti > en_cok:
                en_cok = baglanti
                en_iyi = w
        return en_iyi, en_cok
    
    def yaz(self, kelime, r, c, horizontal):
        w = kelime["word"]
        for i, ch in enumerate(w):
            if horizontal:
                self.grid[r][c + i] = ch
            else:
                self.grid[r + i][c] = ch
                
        self.yerlesenler.append({
            **kelime,
            "row": r,
            "col": c,
            "horizontal": horizontal
        })
    
    def sil(self):
        if not self.yerlesenler:
            return None
        son = self.yerlesenler.pop()
        w = son["word"]
        
        for i in range(len(w)):
            if son["horizontal"]:
                rr, cc = son["row"], son["col"] + i
            else:
                rr, cc = son["row"] + i, son["col"]
            
            hala_kullaniliyor = False
            for y in self.yerlesenler:
                for j in range(len(y["word"])):
                    yr = y["row"] + (0 if y["horizontal"] else j)
                    yc = y["col"] + (j if y["horizontal"] else 0)
                    if yr == rr and yc == cc:
                        hala_kullaniliyor = True
                        break
            if not hala_kullaniliyor:
                self.grid[rr][cc] = " "
        return son

    def fits(self, kelime, r, c, horizontal):
        w = kelime["word"]
        uz = len(w)
        
        if horizontal:
            if r < 0 or r >= self.size or c < 0 or c + uz > self.size: return False
        else:
            if c < 0 or c >= self.size or r < 0 or r + uz > self.size: return False
        
        if horizontal:
            if c > 0 and self.grid[r][c-1] != " ": return False
            if c + uz < self.size and self.grid[r][c+uz] != " ": return False
        else:
            if r > 0 and self.grid[r-1][c] != " ": return False
            if r + uz < self.size and self.grid[r+uz][c] != " ": return False
        
        kesisme = 0
        
        for i, ch in enumerate(w):
            if horizontal:
                rr, cc = r, c + i
            else:
                rr, cc = r + i, c
            
            cell = self.grid[rr][cc]
            
            if cell != " " and cell != ch:
                return False
            
            if cell == ch:
                kesisme += 1
                continue
            
            if horizontal:
                if rr > 0 and self.grid[rr-1][cc] != " ": return False
                if rr < self.size-1 and self.grid[rr+1][cc] != " ": return False
            else:
                if cc > 0 and self.grid[rr][cc-1] != " ": return False
                if cc < self.size-1 and self.grid[rr][cc+1] != " ": return False
        
        if self.yerlesenler and kesisme == 0:
            return False
            
        return True

    def kesisme_sayisi(self, kelime, r, c, horizontal):
        w = kelime["word"]
        sayi = 0
        for i, ch in enumerate(w):
            if horizontal:
                rr, cc = r, c + i
            else:
                rr, cc = r + i, c
            if self.grid[rr][cc] == ch:
                sayi += 1
        return sayi

    def en_iyi_konum(self, kelime, baglanti_kelime, ortaklar, baglanti_yatay):
        en_iyi = None
        en_cok_kesisme = -1
        
        for idx1, idx2, harf in ortaklar:
            if baglanti_yatay:
                r = baglanti_kelime["row"] - idx1
                c = baglanti_kelime["col"] + idx2
                if self.fits(kelime, r, c, False):
                    ks = self.kesisme_sayisi(kelime, r, c, False)
                    if ks > en_cok_kesisme:
                        en_cok_kesisme = ks
                        en_iyi = (r, c, False)
            else:
                r = baglanti_kelime["row"] + idx2
                c = baglanti_kelime["col"] - idx1
                if self.fits(kelime, r, c, True):
                    ks = self.kesisme_sayisi(kelime, r, c, True)
                    if ks > en_cok_kesisme:
                        en_cok_kesisme = ks
                        en_iyi = (r, c, True)
        
        return en_iyi, en_cok_kesisme

    def backtrack(self, index):
        if index >= len(self.kelimeler):
            return True
        
        kelime = self.kelimeler[index]
        
        if index == 0:
            merkez = self.size // 2
            r = merkez
            c = merkez - len(kelime["word"]) // 2
            if self.fits(kelime, r, c, True):
                self.yaz(kelime, r, c, True)
                if self.backtrack(index + 1):
                    return True
                self.sil()
            return False
        
        for yerlesen in self.yerlesenler:
            ortaklar = self.ortak_harf_bul(kelime["word"], yerlesen["word"])
            if not ortaklar:
                continue
            
            pos, kesisme = self.en_iyi_konum(kelime, yerlesen, ortaklar, yerlesen["horizontal"])
            if pos:
                self.yaz(kelime, pos[0], pos[1], pos[2])
                if self.backtrack(index + 1):
                    return True
                self.sil()
                
        return False
    
    def build(self):
        self.kelimeler.sort(key=lambda x: x["harf_sayisi"], reverse=True)
        print(f"📌 İlk kelime: {self.kelimeler[0]['word']}")
        
        if self.backtrack(0):
            print(f"\n✅ Çözüm bulundu! {len(self.yerlesenler)}/{len(self.kelimeler)} kelime yerleşti.")
        else:
            print("\n❌ Tüm kombinasyonlar denendi ama çözüm bulunamadı.")
            
        return self.grid, self.yerlesenler

    def crop(self):
        if not self.yerlesenler: return 0, 0, 0, 0
        rs, cs = [], []
        for p in self.yerlesenler:
            for i in range(len(p["word"])):
                if p["horizontal"]:
                    rs.append(p["row"])
                    cs.append(p["col"] + i)
                else:
                    rs.append(p["row"] + i)
                    cs.append(p["col"])
        return min(rs), max(rs), min(cs), max(cs)
    
    def save_txt(self, filename="bulmaca_cikti.txt"):
        if not self.yerlesenler: return
        r0, r1, c0, c1 = self.crop()
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== BULMACA GÖRÜNÜMÜ ===\n\n")
            for r in range(r0, r1 + 1):
                satir = "".join([self.grid[r][c] if self.grid[r][c] != " " else "." for c in range(c0, c1 + 1)])
                f.write(satir + "\n")
            f.write("\n=== İPUÇLARI ===\n")
            for y in sorted(self.yerlesenler, key=lambda x: x['no']):
                yon = "Yatay" if y["horizontal"] else "Dikey"
                f.write(f"{y['no']}. ({yon}) İpucu: {y['clue']}\n")

    def draw(self, show_letters=False, outfile="bulmaca.png"):
        if not self.yerlesenler:
            print("❌ Hiç kelime yerleşmedi!")
            return
        
        r0, r1, c0, c1 = self.crop()
        padding = 2
        r0 = max(0, r0 - padding)
        r1 = min(self.size - 1, r1 + padding)
        c0 = max(0, c0 - padding)
        c1 = min(self.size - 1, c1 + padding)
        
        h = r1 - r0 + 1
        w = c1 - c0 + 1
        
        # Geniş bir tuval: Solda bulmaca, sağda ipuçları olsun diye width'i 2 katına çıkarıyoruz
        fig, ax = plt.subplots(figsize=(max(16, w * 0.5), max(6, h * 0.5)))
        
        # Bulmacayı sol tarafa yerleştir
        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.invert_yaxis()
        ax.axis('off')
        
        # Hücreleri çiz
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                ch = self.grid[r][c]
                x = c - c0
                y = r - r0
                
                # Tüm hücreleri çiz (hem boş hem dolu)
                facecolor = '#F5F5F5'
                if ch != " ":
                    facecolor = '#FFF9C4' if show_letters else '#E8F4FD'
                
                rect = patches.Rectangle((x, y), 1, 1, linewidth=1, edgecolor='#666', facecolor=facecolor)
                ax.add_patch(rect)
                
                if ch != " ":
                    if show_letters:
                        ax.text(x + 0.5, y + 0.5, ch, ha="center", va="center", fontsize=14, fontweight="bold", color='#1a1a1a')
                    
                    # Rakamları kutuya tam oturt (Büyütülmüş ve merkezlenmiş hali)
                    if (r, c) in {(p["row"], p["col"]) for p in self.yerlesenler}:
                        num = [p["no"] for p in self.yerlesenler if p["row"] == r and p["col"] == c][0]
                        ax.text(x + 0.15, y + 0.30, str(num), fontsize=13, ha="center", va="center", color='#D32F2F', fontweight='bold')

        # İpuçlarını sağ tarafta, dikey olarak listele
        ipuclari = "📝 SORULAR:\n\n"
        for i, w in enumerate(self.kelimeler):
            yon = "Yatay" if any(p["word"] == w["word"] and p["horizontal"] for p in self.yerlesenler) else "Dikey"
            ipuclari += f"{w['no']}. ({yon}) {w['clue']}\n"
        
        # Sağ taraftaki yazı alanı
        plt.figtext(1.02, 0.5, ipuclari, ha='left', va='center', fontsize=12, 
                   bbox=dict(facecolor='white', edgecolor='#333', alpha=0.9, pad=10), 
                   transform=ax.transAxes)

        plt.tight_layout()
        plt.savefig(outfile, dpi=300, bbox_inches="tight", facecolor='white')
        plt.close(fig)
        print(f"✅ {outfile} oluşturuldu!")
    
    def save_all(self):
        import os

        # 1. Öğrenci bulmacası için numara bul
        counter = 1
        while True:
            student_file = f"ogrenci_bulmaca_{counter}.jpg"
            if not os.path.exists(student_file):
                break
            counter += 1
        self.draw(show_letters=False, outfile=student_file)

        # 2. Cevap anahtarı için numara bul (öğrenci ile aynı numarayı kullan)
        answer_file = f"cevap_anahtari_{counter}.jpg"
        self.draw(show_letters=True, outfile=answer_file)

        # 3. TXT dosyası için numara bul
        txt_counter = 1
        while True:
            txt_file = f"bulmaca_cikti_{txt_counter}.txt"
            if not os.path.exists(txt_file):
                break
            txt_counter += 1
        self.save_txt(filename=txt_file)

        print(f"\n✅ Dosyalar kaydedildi:")
        print(f"   📘 Öğrenci: {student_file}")
        print(f"   📗 Cevap:   {answer_file}")
        print(f"   📄 TXT:     {txt_file}")

# ----------------------------------------------------
# ÇALIŞTIR
# ----------------------------------------------------
if __name__ == "__main__":
    print("🧩 FİNAL CROSSWORD")
    print("-" * 50)
    
    cw = FinalCrossword("bulmaca_sorulari.csv")
    cw.build()
    cw.save_all()