"""Put the stock-design CFD results into the report open in Word (COM, one undo record, not saved).
Text that the user may have edited is skipped with a message instead of failing."""
import json, os
import win32com.client as win32

PROJ = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project"
RES = os.path.join(PROJ, "cfd", "results")
PDF_CHECK = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad\report_results_check.pdf"
r = json.load(open(os.path.join(RES, "stock_results.json")))
C = lambda k: r[k] - 273.15
T_HB, T_HS_MAX, T_HS_AVG, Q_HS = C("t_stub_avg"), C("t_heatsink_max"), C("t_heatsink_avg"), r["q_heatsink"]
FLOW = r["fan_vol"] * 3600                                     # m3/h
V_FAN = r["fan_vol"] / 2.8274e-4                               # m/s on the Ø23-Ø13 fan face
DP = 86.3243 - 34.064 * V_FAN + 4.6118 * V_FAN ** 2 - 0.2213 * V_FAN ** 3   # fan curve at the operating point
NODES, CELLS = "2,034,515", "404,389"

wd = win32.GetActiveObject("Word.Application")
doc = wd.Documents(1)
assert doc.Name == "Hotend_Cooling_Report.docx"
WD_CHAR = 1
skipped = []


def find(text):
    rg = doc.Content
    return rg if rg.Find.Execute(FindText=text, MatchCase=True, Wrap=0) else None


def thai_size(rg):
    """Thai text in this document displays at the regular size; match it (see earlier fan edits)."""
    for w in rg.Words:
        if w.Font.Size and w.Font.Size < 100:
            w.Font.SizeBi = w.Font.Size


def replace(old, new):
    rg = find(old)
    if rg is None:
        skipped.append(old[:50]); return None
    rg.Text = new
    rg.HighlightColorIndex = 0
    thai_size(rg)
    return rg


def para_after(p, text, keep_list=True):
    end = p.Range.End - 1                           # split before p's paragraph mark: inserting after the mark
    doc.Range(end, end).InsertAfter("\r")           # lands inside a table that directly follows p
    n = doc.Range(end + 1, end + 1).Paragraphs(1)
    if not keep_list:
        n.Range.ListFormat.RemoveNumbers()
    rg = n.Range
    rg.MoveEnd(WD_CHAR, -1)
    rg.Text = text
    rg.HighlightColorIndex = 0
    thai_size(n.Range)
    return n


def picture_in(rg, path, width):
    shp = rg.InlineShapes.AddPicture(path, False, True)
    ratio = shp.Height / shp.Width
    shp.Width, shp.Height = width, width * ratio


def box_to_picture(placeholder, path, width=380):
    rg = find(placeholder)
    if rg is None:
        skipped.append(placeholder); return
    cell = rg.Cells(1)
    cell.Range.Text = ""
    cell.Shading.BackgroundPatternColor = -16777216              # automatic (no grey fill)
    cell.TopPadding = cell.BottomPadding = 2
    picture_in(cell.Range, path, width)


def fill_row(table_head, row_label, values):
    for i in range(1, doc.Tables.Count + 1):
        t = doc.Tables(i)
        if not t.Cell(1, 1).Range.Text.startswith(table_head):
            continue
        for ri in range(2, t.Rows.Count + 1):
            if t.Cell(ri, 1).Range.Text.startswith(row_label):
                for ci, val in values.items():
                    c = t.Cell(ri, ci).Range
                    c.Text = val
                    c.HighlightColorIndex = 0
                    thai_size(c)
                return
    skipped.append(f"table {table_head}/{row_label}")


sel = (wd.Selection.Start, wd.Selection.End)
wd.UndoRecord.StartCustomRecord("Add stock CFD results")
try:
    # Part 3 setup text = what was actually done
    replace("นำไฟล์ STEP เข้าโปรแกรม SpaceClaim สร้างกล่องอากาศ (Enclosure) ล้อมรอบชุดประกอบ และใช้ Share Topology",
            "สร้างกล่องอากาศ (Enclosure) ขนาด 90 × 60 × 90 mm ล้อมรอบชุดประกอบในโปรแกรม Fusion 360 แล้วนำไฟล์ STEP "
            "เข้า Fluent Meshing (Watertight Geometry Workflow) และใช้ Share Topology")
    replace("เป็นวงแหวนระหว่างดุมกับโครงพัดลมที่ด้านออกของพัดลม",
            "เป็นวงแหวน Ø23 mm ลบดุม Ø13 mm ที่ด้านออกของพัดลม")
    replace("อุณหภูมิคงที่ 220 °C ที่ผิวลำตัวหัวฉีดที่สัมผัสกับฮีตเตอร์",
            "อุณหภูมิคงที่ 220 °C ทั้งก้อนลำตัวหัวฉีด (z = 0–27 mm) แทนชุดฮีตเตอร์")
    replace("Pressure Inlet และ Pressure Outlet ที่ 0 Pa (Gauge) อุณหภูมิ 25 °C",
            "ผิวทั้ง 6 ด้านของกล่องอากาศเป็น Pressure Outlet ที่ 0 Pa (Gauge) อากาศที่ไหลย้อนเข้ามีอุณหภูมิ 25 °C")
    rg = find("ผนังกล่องอากาศเป็นแบบ Adiabatic")
    if rg:
        rg.End = rg.Paragraphs(1).Range.End - 1
        rg.Text = "โครงพัดลม ดุม และท่อนำลมจำลองเป็นของแข็ง ABS ที่นำความร้อนร่วมกับอากาศ (ไม่มีผนังภายนอก)"
        rg.HighlightColorIndex = 0; thai_size(rg)
    else:
        skipped.append("outer wall bullet")
    replace("ใช้ Poly-Hexcore Mesh ขนาดเอลิเมนต์ 0.2–0.3 mm บริเวณครีบ และใช้ Inflation Layer 5 ชั้นที่ผิวครีบ",
            "ใช้ Poly-Hexcore Mesh ขนาดเอลิเมนต์ที่ผิว 0.35–4 mm (3 เซลล์ต่อช่องว่างระหว่างครีบ) "
            "และใช้ Inflation Layer 3 ชั้นในบริเวณอากาศ")
    replace("[จำนวน Nodes]", NODES)
    replace("[จำนวน Elements]", CELLS)
    replace("พร้อมตรวจสอบความเป็นอิสระของ Mesh (Mesh Independence)",
            "(Orthogonal Quality ต่ำสุด 0.07) ยังไม่ได้ตรวจสอบความเป็นอิสระของ Mesh (Mesh Independence)")

    # images
    box_to_picture("[ใส่รูปการตั้งค่าเงื่อนไขขอบเขตและ Mesh]", os.path.join(RES, "mesh_solids_iso.png"))
    replace("รูปแสดงการตั้งค่าเงื่อนไขขอบเขตของแบบเดิม",
            f"รูปแสดง Mesh บนผิวฮีตซิงก์ ฮีตเบรก และหัวฉีด (Poly-Hexcore {CELLS} เซลล์)")
    box_to_picture("[ใส่รูป Temperature Contour ของแบบเดิม]", os.path.join(RES, "temp_solids_iso.png"))
    cap = find("รูปแสดงการกระจายอุณหภูมิของแบบเดิม")
    if cap:
        p = cap.Paragraphs(1)
        for img, text in (("temp_section_fins.png", "รูปแสดงอุณหภูมิบนระนาบตัดผ่านช่องครีบ (y = −6 mm) ช่วงสี 25–60 °C"),
                          ("velocity_section_fins.png", "รูปแสดงความเร็วอากาศบนระนาบตัดผ่านช่องครีบ (y = −6 mm)")):
            pic = para_after(p, "", keep_list=False)
            picture_in(pic.Range, os.path.join(RES, img), 400)
            p = para_after(pic, text, keep_list=False)
        p.Range.ParagraphFormat.SpaceAfter = 12
    else:
        skipped.append("temperature caption")

    # results tables
    fill_row("ผลลัพธ์", "อุณหภูมิที่ทางเข้าฮีตเบรก", {2: f"{T_HB:.1f}"})
    fill_row("ผลลัพธ์", "อุณหภูมิสูงสุดของฮีตซิงก์", {2: f"{T_HS_MAX:.1f}"})
    fill_row("ผลลัพธ์", "อัตราการระบายความร้อน", {2: f"{Q_HS:.2f}"})
    fill_row("ผลลัพธ์", "อัตราการไหลของอากาศ", {2: f"{FLOW:.2f}"})
    fill_row("ผลลัพธ์", "ความดันตก", {2: f"≈ {DP:.0f} (จากกราฟพัดลม)"})
    fill_row("แบบ", "แบบเดิม", {2: f"{T_HB:.1f}", 3: f"{T_HS_MAX:.1f}", 4: f"{Q_HS:.2f}", 5: f"≈ {DP:.0f}"})

    replace("[อธิบายผลการวิเคราะห์ของแบบเดิม]",
            f"ผลการวิเคราะห์ของแบบเดิมพบว่าอุณหภูมิเฉลี่ยของฮีตเบรกส่วนที่สวมอยู่ในซ็อกเก็ตของฮีตซิงก์ (ทางเข้าฮีตเบรก) "
            f"มีค่า {T_HB:.1f} °C ต่ำกว่าเกณฑ์ 50 °C อยู่ {50 - T_HB:.1f} °C ฮีตซิงก์มีอุณหภูมิค่อนข้างสม่ำเสมอ "
            f"(สูงสุด {T_HS_MAX:.1f} °C เฉลี่ย {T_HS_AVG:.1f} °C) เนื่องจากอะลูมิเนียมนำความร้อนได้ดี "
            f"และระบายความร้อนสู่อากาศได้ {Q_HS:.2f} W พัดลมทำงานที่อัตราการไหล {FLOW:.2f} m³/h "
            f"({FLOW / 1.699:.2f} CFM) หรือประมาณ {FLOW / 5.03 * 100:.0f}% ของอัตราการไหลอิสระ ที่ความดันประมาณ "
            f"{DP:.0f} Pa ซึ่งอยู่ในช่วงกราฟแบน (Stall Plateau) ของพัดลม อากาศไหลผ่านช่องระหว่างครีบด้วยความเร็ว "
            f"ประมาณ 5–8 m/s ส่วนอากาศร้อนจากลำตัวหัวฉีดลอยตัวขึ้นและไหลผ่านใต้ท่อนำลม ผลลัพธ์ลู่เข้าแล้ว "
            f"(Residual ต่ำกว่า 3 × 10⁻⁶ และอุณหภูมิเปลี่ยนแปลงน้อยกว่า 10⁻⁵ K ใน 50 รอบสุดท้าย)")

    # simplifications and limitations
    rg = find("ตัดสกรู สายไฟ เปลือกหัวพิมพ์ และตะแกรงช่องลมออก")
    if rg:
        para_after(rg.Paragraphs(1), "ในแบบจำลอง CFD ตัดรูปลายหัวฉีด Ø0.38 mm แผ่นล็อก และรูสลักออก ปิดช่องว่าง 0.01 mm "
                                     "ระหว่างแกนสวมกับซ็อกเก็ต และใช้ช่องลมพัดลม Ø23 mm เพื่อให้สร้าง Mesh ได้")
    else:
        skipped.append("simplification bullet")
    rg = find("กราฟพัดลมเป็นค่าสมมติจากพัดลม Pelonis")
    if rg:
        p = rg.Paragraphs(1)
        for text in ("ยังไม่ได้ศึกษาความเป็นอิสระของ Mesh (Mesh Independence Study)",
                     "จำลองที่อุณหภูมิอากาศแวดล้อม 25 °C หากภายในห้องพิมพ์ร้อน 35–45 °C "
                     "อุณหภูมิทุกจุดจะสูงขึ้นประมาณเท่ากับผลต่างนี้",
                     "ไม่ได้จำลองชุดฮีตเตอร์และปลอกซิลิโคน จึงกำหนดลำตัวหัวฉีดทั้งก้อนที่ 220 °C แทน"):
            p = para_after(p, text)
    else:
        skipped.append("limitations")
finally:
    wd.UndoRecord.EndCustomRecord()
    doc.Range(*sel).Select()

print("skipped (not found, left as is):", skipped or "none")
print(f"values: T_hb {T_HB:.2f} C, T_hs max {T_HS_MAX:.2f}, avg {T_HS_AVG:.2f}, Q {Q_HS:.3f} W, flow {FLOW:.3f} m3/h, dp {DP:.1f} Pa")
doc.ExportAsFixedFormat(PDF_CHECK, 17)
print("exported check PDF; saved state:", doc.Saved)
