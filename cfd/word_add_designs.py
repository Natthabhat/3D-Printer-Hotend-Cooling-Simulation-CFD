"""Add Design 1 / Design 2 descriptions, figures, comparison table and conclusion to the open report (45 °C runs)."""
import json, os
from wordops import Doc

RES = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\cfd\results"
PDF_CHECK = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad\report_designs_check.pdf"
LIMIT = 50.0
AREA = {"stock": 4634, "d2": 5980}               # heatsink surface area mm2 (Fusion)
VOL = {"stock": 2761, "d2": 2741}                # heatsink volume mm3


def load(name):
    r = json.load(open(os.path.join(RES, name)))
    v_fan = r["fan_vol"] / 2.8274e-4
    return dict(hb=r["t_stub_avg"] - 273.15, hs=r["t_heatsink_max"] - 273.15, hs_avg=r["t_heatsink_avg"] - 273.15,
                q=r["q_heatsink"], flow=r["fan_vol"] * 3600,
                dp=86.3243 - 34.064 * v_fan + 4.6118 * v_fan ** 2 - 0.2213 * v_fan ** 3)


S, D1, D2 = load("stock_results_45C.json"), load("design1_45C.json"), load("design2_45C.json")
ok = lambda t: "✓" if t <= LIMIT else "✗"
row = lambda d: {2: f"{d['hb']:.1f} {ok(d['hb'])}", 3: f"{d['hs']:.1f} {ok(d['hs'])}", 4: f"{d['q']:.2f}", 5: f"≈ {d['dp']:.0f}"}

w = Doc()
with w.undo_record("Add design 1 and 2"):
    # comparison table (Part 4)
    w.fill_row("แบบ", "แบบเดิม", row(S))
    w.fill_row("แบบ", "แบบพัฒนา 1", row(D1))
    w.fill_row("แบบ", "แบบพัฒนา 2", row(D2))

    # Part 3 section 4: design descriptions + figures
    p = w.para_text("[อธิบายแบบที่เลือกพัฒนา",
                    "แบบพัฒนา 1 (ฮีตเบรกไทเทเนียม): คงรูปทรงฮีตซิงก์เดิม แต่เปลี่ยนวัสดุฮีตเบรกจากเหล็กกล้าไร้สนิม "
                    "(k = 16.3 W/m·K) เป็นไทเทเนียมอัลลอย Ti-6Al-4V (k = 6.7 W/m·K) เพื่อลดความร้อนที่ไหลจากหัวฉีดเข้าสู่ฮีตซิงก์ "
                    "เนื่องจากผลของแบบเดิมแสดงว่าความต้านทานความร้อนของฮีตเบรก (ประมาณ 56 K/W) เป็นประมาณ 93% "
                    "ของความต้านทานรวมจากหัวฉีดถึงอากาศ")
    if p:
        p = w.para_after(p, f"แบบพัฒนา 2 (ฮีตเบรกไทเทเนียม + ฮีตซิงก์ใหม่): ใช้ฮีตเบรกไทเทเนียมเช่นเดียวกับแบบพัฒนา 1 "
                            f"ร่วมกับฮีตซิงก์รูปทรงใหม่ภายในขนาดเดิม 17.5 × 21 × 18.5 mm และใช้พัดลมเดิม โดยเปลี่ยนครีบแนวนอนเป็น "
                            f"6 ครีบ หนา 0.7 mm (เดิม 5 ครีบ หนา 1 mm) ระยะห่างระหว่างครีบ 1.05 mm (ไม่แคบกว่าเดิมเพื่อไม่ให้พัดลมทำงาน"
                            f"ใกล้จุดหยุดไหลมากขึ้น) และเพิ่มครีบตั้งด้านล่างเป็น 5 ครีบต่อข้าง (เดิม 3 ครีบ) คงร่องแผ่นล็อก ซ็อกเก็ต "
                            f"และบอสเดิมไว้ ทำให้พื้นที่ผิวเพิ่มจาก {AREA['stock']:,} เป็น {AREA['d2']:,} mm² "
                            f"(+{(AREA['d2'] / AREA['stock'] - 1) * 100:.0f}%) โดยปริมาตรใกล้เคียงเดิม "
                            f"({VOL['d2']:,} mm³ เทียบกับ {VOL['stock']:,} mm³)")
        p.Range.ParagraphFormat.FirstLineIndent = 36
    w.box_to_picture("[ใส่รูปแบบจำลองหลังการพัฒนา", os.path.join(RES, "design2_heatsink_side.png"), width=300)
    cap = w.para_text("รูปแสดงการออกแบบและผลการวิเคราะห์หลังการพัฒนา",
                      "รูปแสดงฮีตซิงก์แบบพัฒนา 2 (ภาพด้านข้าง) ครีบ 6 ครีบ หนา 0.7 mm และครีบตั้ง 5 ครีบต่อข้าง")
    if cap:
        p = cap
        for img, text in (("design1_45C/temp_solids_iso.png", "รูปแสดงการกระจายอุณหภูมิของแบบพัฒนา 1 (อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)"),
                          ("design2_45C/temp_solids_iso.png", "รูปแสดงการกระจายอุณหภูมิของแบบพัฒนา 2 (อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)"),
                          ("design2_45C/velocity_section_fins.png", "รูปแสดงความเร็วอากาศผ่านช่องครีบของแบบพัฒนา 2 (y = −6 mm)")):
            pic = w.picture_after(p, os.path.join(RES, img))
            p = w.para_after(pic, text)
            p.Range.ParagraphFormat.Alignment = 1
            p.Range.Font.Italic = p.Range.Font.ItalicBi = True

    # conclusion
    passes = [n for n, d in (("แบบพัฒนา 1", D1), ("แบบพัฒนา 2", D2)) if d["hb"] <= LIMIT and d["hs"] <= LIMIT]
    w.para_text("[สรุปผลว่าแบบใดผ่านเกณฑ์",
                f"ที่อุณหภูมิหัวฉีด 220 °C (พิมพ์ PLA) และอากาศแวดล้อม 45 °C แบบเดิมมีอุณหภูมิทางเข้าฮีตเบรก {S['hb']:.1f} °C "
                f"และฮีตซิงก์สูงสุด {S['hs']:.1f} °C ซึ่งไม่ผ่านเกณฑ์ 50 °C แบบพัฒนา 1 (ฮีตเบรกไทเทเนียม) ลดอุณหภูมิทางเข้าฮีตเบรกเหลือ "
                f"{D1['hb']:.1f} °C ({D1['hb'] - S['hb']:+.1f} °C) และฮีตซิงก์สูงสุด {D1['hs']:.1f} °C ({D1['hs'] - S['hs']:+.1f} °C) "
                f"เพราะความร้อนที่ไหลเข้าฮีตซิงก์ลดลงจาก {S['q']:.2f} W เหลือ {D1['q']:.2f} W "
                f"แบบพัฒนา 2 (ฮีตเบรกไทเทเนียม + ฮีตซิงก์ใหม่) ได้อุณหภูมิทางเข้าฮีตเบรก {D2['hb']:.1f} °C ({D2['hb'] - S['hb']:+.1f} °C) "
                f"และฮีตซิงก์สูงสุด {D2['hs']:.1f} °C ({D2['hs'] - S['hs']:+.1f} °C) โดยใช้ขนาดติดตั้งและพัดลมเดิม "
                + (f"แบบที่ผ่านเกณฑ์ทั้งสองข้อคือ {' และ '.join(passes)} " if passes else "ยังไม่มีแบบใดผ่านเกณฑ์ทั้งสองข้อ ")
                + ("ทั้งสองแบบพัฒนามีอุณหภูมิต่ำกว่าแบบเดิม จึงผ่านเกณฑ์ที่ต้องดีกว่าหรือใกล้เคียงแบบเดิม "
                   if D1["hb"] < S["hb"] and D2["hb"] < S["hb"] and D1["hs"] < S["hs"] and D2["hs"] < S["hs"] else "")
                + (f"ผลจากการเปลี่ยนวัสดุฮีตเบรก ({S['hb'] - D1['hb']:.1f} °C) มีมากกว่าผลจากการเปลี่ยนฮีตซิงก์ "
                   f"({D1['hb'] - D2['hb']:.1f} °C) เนื่องจากความต้านทานความร้อนส่วนใหญ่อยู่ที่ฮีตเบรก"
                   if (S["hb"] - D1["hb"]) > (D1["hb"] - D2["hb"]) else
                   f"ผลจากการเปลี่ยนฮีตซิงก์ ({D1['hb'] - D2['hb']:.1f} °C) มีมากกว่าผลจากการเปลี่ยนวัสดุฮีตเบรก "
                   f"({S['hb'] - D1['hb']:.1f} °C)"))

print("skipped:", w.skipped or "none")
for n, d in (("stock", S), ("D1", D1), ("D2", D2)):
    print(f"{n:6s} hb {d['hb']:.2f}  hs max {d['hs']:.2f}  hs avg {d['hs_avg']:.2f}  Q {d['q']:.3f} W  flow {d['flow']:.3f} m3/h  dp {d['dp']:.1f} Pa")
w.doc.ExportAsFixedFormat(PDF_CHECK, 17)
print("exported check PDF; saved state:", w.doc.Saved)
