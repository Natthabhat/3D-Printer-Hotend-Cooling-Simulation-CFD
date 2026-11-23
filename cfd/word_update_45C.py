"""Update the open report to the 45 °C ambient run and add the two new design criteria (COM, one undo record).
Reads cfd/results/stock_results_45C.json (and the 25 °C json for the comparison sentence)."""
import json, os
import win32com.client as win32

PROJ = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project"
RES = os.path.join(PROJ, "cfd", "results")
IMG = os.path.join(RES, "45C")
PDF_CHECK = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad\report_45C_check.pdf"
r = json.load(open(os.path.join(RES, "stock_results_45C.json")))
r25 = json.load(open(os.path.join(RES, "stock_results.json")))
C = lambda d, k: d[k] - 273.15
T_HB, T_HS_MAX, T_HS_AVG, Q_HS = C(r, "t_stub_avg"), C(r, "t_heatsink_max"), C(r, "t_heatsink_avg"), r["q_heatsink"]
T_HB25 = C(r25, "t_stub_avg")
FLOW = r["fan_vol"] * 3600
V_FAN = r["fan_vol"] / 2.8274e-4
DP = 86.3243 - 34.064 * V_FAN + 4.6118 * V_FAN ** 2 - 0.2213 * V_FAN ** 3
LIMIT = 50.0
ok = lambda t: "ผ่านเกณฑ์" if t <= LIMIT else "ไม่ผ่านเกณฑ์"

wd = win32.GetActiveObject("Word.Application")
doc = wd.Documents(1)
assert doc.Name == "Hotend_Cooling_Report.docx"
WD_CHAR = 1
skipped = []


def find(text, within=None):
    rg = (within or doc.Content).Duplicate if within else doc.Content
    return rg if rg.Find.Execute(FindText=text, MatchCase=True, Wrap=0) else None


def thai_size(rg):
    for w in rg.Words:
        if w.Font.Size and w.Font.Size < 100:
            w.Font.SizeBi = w.Font.Size


def replace(old, new, within=None):
    rg = find(old, within)
    if rg is None:
        skipped.append(old[:45]); return None
    rg.Text = new
    rg.HighlightColorIndex = 0
    thai_size(rg)
    return rg


def para_text(start, new):
    """Replace the whole text of the paragraph that contains `start`."""
    rg = find(start)
    if rg is None:
        skipped.append(start[:45]); return None
    p = rg.Paragraphs(1).Range
    p.MoveEnd(WD_CHAR, -1)
    p.Text = new
    p.HighlightColorIndex = 0
    thai_size(p)
    return p


def para_after(p, text):
    end = p.Range.End - 1                       # split before p's mark (inserting after it can land in a table)
    doc.Range(end, end).InsertAfter("\r")
    n = doc.Range(end + 1, end + 1).Paragraphs(1)
    rg = n.Range
    rg.MoveEnd(WD_CHAR, -1)
    rg.Text = text
    rg.HighlightColorIndex = 0
    rg.Font.Bold = rg.Font.BoldBi = False
    thai_size(n.Range)
    return n


def swap_picture(caption_start, path):
    """Replace the inline picture just above the caption (same paragraph-before or table cell before)."""
    cap = find(caption_start)
    if cap is None:
        skipped.append("picture " + caption_start[:30]); return
    p = cap.Paragraphs(1).Previous()
    shapes = p.Range.InlineShapes
    if shapes.Count == 0:
        skipped.append("no picture above " + caption_start[:30]); return
    old = shapes(1)
    w = old.Width
    rg = old.Range
    old.Delete()
    new = rg.InlineShapes.AddPicture(path, False, True)
    ratio = new.Height / new.Width
    new.Width, new.Height = w, w * ratio


def fill_row(head, label, values):
    for i in range(1, doc.Tables.Count + 1):
        t = doc.Tables(i)
        if not t.Cell(1, 1).Range.Text.startswith(head):
            continue
        for ri in range(2, t.Rows.Count + 1):
            if t.Cell(ri, 1).Range.Text.startswith(label):
                for ci, val in values.items():
                    c = t.Cell(ri, ci).Range
                    c.Text = val
                    c.HighlightColorIndex = 0
                    thai_size(c)
                return
    skipped.append(f"table {head}/{label}")


sel = (wd.Selection.Start, wd.Selection.End)
wd.UndoRecord.StartCustomRecord("Results at 45 °C ambient + new criteria")
try:
    # Part 1 criteria
    amb = find("อุณหภูมิอากาศแวดล้อม (Ambient Temperature)")
    if amb:
        pr = amb.Paragraphs(1).Range
        replace("25 °C", "45 °C", within=pr)
        if not replace("[ปรับเป็นอุณหภูมิภายในห้องพิมพ์ถ้าต้องการ]", "(ใกล้เคียงอุณหภูมิภายในห้องพิมพ์ขณะใช้งานจริง)"):
            skipped.pop()
    else:
        skipped.append("ambient criterion")
    hb = find("อุณหภูมิที่ทางเข้าฮีตเบรก (บริเวณซ็อกเก็ตของฮีตซิงก์) ต้อง")
    if hb:
        n = para_after(hb.Paragraphs(1), "อุณหภูมิสูงสุดของฮีตซิงก์ต้องไม่เกิน 50 °C")
        other = find("[เกณฑ์อื่น ๆ")
        text = ("ฮีตซิงก์ที่ออกแบบใหม่ต้องมีอุณหภูมิทางเข้าฮีตเบรกและอุณหภูมิสูงสุดของฮีตซิงก์ "
                "ต่ำกว่าหรือใกล้เคียงกับแบบเดิม")
        if other:
            para_text("[เกณฑ์อื่น ๆ", text)
        else:
            para_after(n, text)
    else:
        skipped.append("heat-break criterion")

    # setup text
    replace("อุณหภูมิอากาศแวดล้อม 25 °C และเปิดผลของแรงโน้มถ่วง", "อุณหภูมิอากาศแวดล้อม 45 °C และเปิดผลของแรงโน้มถ่วง")
    replace("อากาศที่ไหลย้อนเข้ามีอุณหภูมิ 25 °C", "อากาศที่ไหลย้อนเข้ามีอุณหภูมิ 45 °C")

    # results
    fill_row("ผลลัพธ์", "อุณหภูมิที่ทางเข้าฮีตเบรก", {2: f"{T_HB:.1f}"})
    fill_row("ผลลัพธ์", "อุณหภูมิสูงสุดของฮีตซิงก์", {2: f"{T_HS_MAX:.1f}", 3: "≤ 50"})
    fill_row("ผลลัพธ์", "อัตราการระบายความร้อน", {2: f"{Q_HS:.2f}"})
    fill_row("ผลลัพธ์", "อัตราการไหลของอากาศ", {2: f"{FLOW:.2f}"})
    fill_row("ผลลัพธ์", "ความดันตก", {2: f"≈ {DP:.0f} (จากกราฟพัดลม)"})
    fill_row("แบบ", "แบบเดิม", {2: f"{T_HB:.1f}", 3: f"{T_HS_MAX:.1f}", 4: f"{Q_HS:.2f}", 5: f"≈ {DP:.0f}"})
    para_text("ผลการวิเคราะห์ของแบบเดิมพบว่า",
              f"ผลการวิเคราะห์ของแบบเดิมที่อุณหภูมิหัวฉีด 220 °C (พิมพ์ PLA) และอุณหภูมิอากาศแวดล้อม 45 °C พบว่า "
              f"อุณหภูมิเฉลี่ยของฮีตเบรกส่วนที่สวมอยู่ในซ็อกเก็ตของฮีตซิงก์ (ทางเข้าฮีตเบรก) มีค่า {T_HB:.1f} °C "
              f"({ok(T_HB)} 50 °C) และอุณหภูมิสูงสุดของฮีตซิงก์มีค่า {T_HS_MAX:.1f} °C ({ok(T_HS_MAX)} 50 °C) "
              f"ฮีตซิงก์มีอุณหภูมิค่อนข้างสม่ำเสมอ (เฉลี่ย {T_HS_AVG:.1f} °C) และระบายความร้อนสู่อากาศได้ {Q_HS:.2f} W "
              f"พัดลมทำงานที่อัตราการไหล {FLOW:.2f} m³/h ({FLOW / 1.699:.2f} CFM) ประมาณ {FLOW / 5.03 * 100:.0f}% "
              f"ของอัตราการไหลอิสระ ที่ความดันประมาณ {DP:.0f} Pa ซึ่งอยู่ในช่วงกราฟแบน (Stall Plateau) ของพัดลม "
              f"เมื่อเทียบกับกรณีอากาศแวดล้อม 25 °C ซึ่งได้อุณหภูมิทางเข้าฮีตเบรก {T_HB25:.1f} °C "
              f"อุณหภูมิเพิ่มขึ้นประมาณ {T_HB - T_HB25:.1f} °C ใกล้เคียงกับผลต่างของอุณหภูมิอากาศ (20 °C) "
              f"แสดงว่าอุณหภูมิของฮีตซิงก์ขึ้นกับอุณหภูมิอากาศโดยตรง ผลลัพธ์ลู่เข้าแล้ว "
              f"(อุณหภูมิเปลี่ยนแปลงน้อยกว่า 10⁻⁵ K ใน 50 รอบสุดท้าย)")
    replace("รูปแสดงการกระจายอุณหภูมิของแบบเดิม", "รูปแสดงการกระจายอุณหภูมิของแบบเดิม (อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)")
    replace("(y = −6 mm) ช่วงสี 25–60 °C", "(y = −6 mm) ช่วงสี 45–80 °C")
    swap_picture("รูปแสดงการกระจายอุณหภูมิของแบบเดิม", os.path.join(IMG, "temp_solids_iso.png"))
    swap_picture("รูปแสดงอุณหภูมิบนระนาบตัดผ่านช่องครีบ", os.path.join(IMG, "temp_section_fins.png"))
    swap_picture("รูปแสดงความเร็วอากาศบนระนาบตัดผ่านช่องครีบ", os.path.join(IMG, "velocity_section_fins.png"))
    para_text("จำลองที่อุณหภูมิอากาศแวดล้อม 25 °C",
              "จำลองที่อุณหภูมิอากาศแวดล้อมคงที่ 45 °C อุณหภูมิห้องพิมพ์จริงขึ้นกับวัสดุ ระยะเวลาพิมพ์ และการเปิดฝาเครื่อง "
              "(ที่ 25 °C อุณหภูมิทุกจุดต่ำลงประมาณ 20 °C)")
finally:
    wd.UndoRecord.EndCustomRecord()
    doc.Range(*sel).Select()

print("skipped:", skipped or "none")
print(f"45C: T_hb {T_HB:.2f} ({ok(T_HB)}), T_hs max {T_HS_MAX:.2f} ({ok(T_HS_MAX)}), avg {T_HS_AVG:.2f}, "
      f"Q {Q_HS:.3f} W, flow {FLOW:.3f} m3/h, dp {DP:.1f} Pa | 25C T_hb {T_HB25:.2f}")
doc.ExportAsFixedFormat(PDF_CHECK, 17)
print("exported check PDF; saved state:", doc.Saved)
