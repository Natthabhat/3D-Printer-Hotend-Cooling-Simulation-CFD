"""Number figures (รูปที่ N) and tables (ตารางที่ N) in the open report with Word SEQ fields. Captions are found from
the pictures themselves (cover logo excluded); data tables get a title paragraph above them. Safe to re-run."""
from wordops import Doc

PDF_CHECK = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad\report_revised_check.pdf"
TITLES = {"ส่วนประกอบ": "คุณสมบัติวัสดุที่ใช้ในการจำลอง", "ส่วน": "ส่วนประกอบและน้ำหนักโดยประมาณ",
          "รายการ": "ข้อมูลจำเพาะของพัดลม", "Q (CFM)": "กราฟพัดลมที่ใช้ในการวิเคราะห์ (Piecewise-linear)",
          "ผลลัพธ์": "ผลการคำนวณของแบบเดิม (อากาศแวดล้อม 45 °C)", "แบบจำลอง": "ผลของแบบจำลองความปั่นป่วนต่อแบบพัฒนา 2",
          "แบบ": "เปรียบเทียบผลการวิเคราะห์ (อากาศแวดล้อม 45 °C)", "กรณี": "สมดุลมวลและพลังงาน และการลู่เข้า",
          "Mesh": "ผลการศึกษาความเป็นอิสระของ Mesh (แบบพัฒนา 2)"}   # longer keys first where prefixes overlap

w = Doc()
d = w.doc
part1 = w.find("Part 1: Title, Objective and Design Criteria").Start
with w.undo_record("Number figures and tables"):
    # figures: the caption is the paragraph right after the picture (same cell for side-by-side figures)
    captions = []
    for i in range(1, d.InlineShapes.Count + 1):
        shp = d.InlineShapes(i)
        if shp.Range.Start < part1:
            continue
        para = shp.Range.Paragraphs(1)
        if para.Range.Information(12) and para.Range.Cells(1).Range.Text.count("\r") > 1:
            cap = para.Next()                                            # caption in the same table cell
        else:
            t_end = None
            if para.Range.Information(12):                               # picture alone in a 1-cell table
                for k in range(1, d.Tables.Count + 1):
                    t = d.Tables(k)
                    if t.Range.Start <= shp.Range.Start < t.Range.End:
                        t_end = t.Range.End
                        break
            cap = d.Range(t_end, t_end).Paragraphs(1) if t_end else para.Next()
        txt = cap.Range.Text.strip()
        if cap is not None and txt and not txt.startswith("รูปที่"):
            captions.append(cap)
    for cap in captions:
        w.numbered(cap.Range, "รูปที่", "Figure")
    # tables: title paragraph above each data table (no pictures, more than one row)
    added = 0
    for k in range(1, d.Tables.Count + 1):
        t = d.Tables(k)
        if t.Range.InlineShapes.Count or t.Rows.Count < 2:
            continue
        head = t.Cell(1, 1).Range.Text[:-2].strip()
        title = next((v for key, v in sorted(TITLES.items(), key=lambda kv: -len(kv[0])) if head.startswith(key)), None)
        if title is None:
            w.skipped.append("table " + head); continue
        before = d.Range(t.Range.Start - 1, t.Range.Start - 1).Paragraphs(1)
        if before.Range.Text.strip().startswith("ตารางที่"):
            continue
        cap = w.para_after(before, title)
        cap.Range.ParagraphFormat.Alignment = 1
        cap.Range.ParagraphFormat.FirstLineIndent = 0
        cap.Range.ListFormat.RemoveNumbers()
        cap.Range.Font.Italic = cap.Range.Font.ItalicBi = False
        cap.Range.Font.Bold = cap.Range.Font.BoldBi = True
        w.numbered(cap.Range, "ตารางที่", "Table")
        added += 1
    d.Fields.Update()

print("figures numbered:", len(captions), "| tables titled:", added, "| skipped:", w.skipped or "none")
d.ExportAsFixedFormat(PDF_CHECK, 17)
print("exported check PDF; saved state:", d.Saved)
