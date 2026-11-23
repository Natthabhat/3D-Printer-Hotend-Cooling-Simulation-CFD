"""Revise the open report per the review: reconciled fan curve results, consistent setup text, verification
section (residuals, balances, mesh study + GCI, turbulence-model sensitivity), qualified conclusion, baseline
caveat, numbered figures/tables, new images (°C, large legends), complete references. One undo record."""
import json, math, os, re
import numpy as np
from wordops import Doc
from gci import gci
from run_case import fan_table, A_FAN

CFD = r"C:\Users\natth\Documents\Asys Com aid\Ansys Project\cfd"
RES = os.path.join(CFD, "results")
PDF_CHECK = r"C:\Users\natth\AppData\Local\Temp\claude\5b299854331cdbb0\4e4d068d-c5a2-4680-8b88-553b1334336a\scratchpad\report_revised_check.pdf"
T_AMB, LIMIT, BOX_VOL = 45.0, 50.0, 90 * 60 * 90          # °C, °C, mm3 (cancels in the GCI ratios)
TABLE = fan_table()                                       # (v on the Ø23 face, Δp)


def load(tag):
    r = json.load(open(os.path.join(RES, f"{tag}.json")))
    v = r["fan_vol"] / A_FAN
    return dict(hb=r["t_stub_avg"] - 273.15, hs=r["t_heatsink_max"] - 273.15, hs_avg=r["t_heatsink_avg"] - 273.15,
                q=r["q_heatsink"], flow=r["fan_vol"] * 3600, v=v,
                dp=float(np.interp(v, [p[0] for p in TABLE], [p[1] for p in TABLE])),
                d50=max(abs(r["change_last50"][k]) for k in ("t_stub_avg", "t_heatsink_max")),
                mass=r["balance"]["mass_imbalance_pct"], energy=r["balance"]["energy_imbalance_pct"],
                q_in=r["balance"]["q_nozzle_out"])


def cells(log):
    m = re.findall(r"(\d+) cells were created", open(os.path.join(CFD, log), encoding="utf-8", errors="ignore").read())
    return int(m[-1])


S, D1, D2 = load("stock_45C_pl"), load("design1_45C_pl"), load("design2_45C_pl")
LAM = load("design2_45C_pl_laminar")
CO, FI = load("design2_45C_pl_coarse"), load("design2_45C_pl_fine")
N = dict(coarse=cells("mesh_coarse_log.txt"), medium=441435, fine=cells("mesh_fine_log.txt"))
G = {k: gci(N["fine"], N["medium"], N["coarse"], FI[k] - T_AMB, D2[k] - T_AMB, CO[k] - T_AMB, BOX_VOL) for k in ("hb", "hs")}
# oscillatory convergence or an apparent order far above the 2nd-order scheme makes the GCI unreliable (Celik 2008);
# then use the largest difference between meshes as the band instead
OSC = {k: G[k]["oscillatory"] or G[k]["p"] > 4 for k in G}
U_MESH = {k: (max(abs(FI[k] - D2[k]), abs(CO[k] - D2[k])) if OSC[k] else G[k]["gci_medium"] / 100 * (D2[k] - T_AMB))
          for k in G}                                                         # °C band on the medium-mesh result
U_TURB = {k: abs(LAM[k] - D2[k]) for k in ("hb", "hs")}
f1 = lambda x: f"{x:.1f}"
f2 = lambda x: f"{x:.2f}"
mark = lambda t: "✓" if t <= LIMIT else "✗"
diff = lambda a, b: round(a, 1) - round(b, 1)              # differences of the printed (rounded) values

w = Doc()
with w.undo_record("Revise report per review"):
    # ---------------- consistency fixes ----------------
    w.para_text("ช่องระหว่างครีบกว้างประมาณ 1 mm",
                "ช่องระหว่างครีบกว้างประมาณ 1 mm ทำให้ Dₕ ≈ 2 mm ผลจาก CFD พบว่าความเร็วลมในช่องครีบประมาณ 5–7 m/s "
                "และความหนืดจลน์ของอากาศที่ 45 °C ประมาณ 1.75 × 10⁻⁵ m²/s จะได้ Re ≈ 570–800 ซึ่งเป็นการไหลแบบราบเรียบ "
                "(Laminar) ภายในช่องครีบ แต่บริเวณอื่นมีลำลมจากพัดลมและการผสมของอากาศ จึงเลือกแบบจำลอง k-ω SST "
                "ซึ่งใช้ได้ทั้งการไหลใกล้ผนังและการไหลแบบปั่นป่วน และตรวจสอบผลกระทบด้วยการคำนวณแบบ Laminar เปรียบเทียบ "
                "(Part 3 หัวข้อ 5.3)")
    w.replace("แต่กำหนดอุณหภูมิที่ผิวลำตัวหัวฉีดที่สัมผัสกับฮีตเตอร์แทน",
              "แต่กำหนดอุณหภูมิคงที่ 220 °C ให้ลำตัวหัวฉีดทั้งก้อน (z = 0–27 mm) แทน")
    w.replace("กำหนดที่ผิวลำตัวหัวฉีดที่สัมผัสกับฮีตเตอร์ (ช่วง z ≈ 3.5–27 mm)",
              "กำหนดเป็นค่าคงที่ (Fixed Value) ให้ลำตัวหัวฉีดทั้งก้อน (z = 0–27 mm) แทนชุดฮีตเตอร์")
    p = w.find("ใช้การวิเคราะห์การถ่ายเทความร้อนร่วมกับการไหล (Conjugate Heat Transfer) แบบสภาวะคงตัว")
    if p:
        w.para_after(p.Paragraphs(1), "เหตุผลที่เลือก k-ω SST: การไหลในช่องครีบเป็นแบบราบเรียบ (Re ≈ 570–800) แต่ลำลมจากพัดลม "
                                     "ท่อนำลม และการผสมของอากาศด้านท้ายเป็นการไหลแบบผสม แบบจำลอง SST ใช้ได้จนถึงผนังโดยไม่ต้องใช้ "
                                     "Wall Function จึงเหมาะกับทั้งสองลักษณะ ผลกระทบของการเลือกแบบจำลองแสดงในหัวข้อ 5.3")
    else:
        w.skipped.append("procedure paragraph")
    w.para_text("จำนวน 2,034,515 Nodes",
                f"แบบเดิมและแบบพัฒนา 1: {404389:,} เซลล์ (2,034,515 Nodes, Orthogonal Quality ต่ำสุด 0.07) "
                f"แบบพัฒนา 2: {N['medium']:,} เซลล์ (Orthogonal Quality ต่ำสุด 0.20) การตรวจสอบความเป็นอิสระของ Mesh "
                "แสดงในหัวข้อ 5.2")

    # ---------------- fan curve (section 2.3.3) ----------------
    for i in range(1, w.doc.Tables.Count + 1):
        t = w.doc.Tables(i)
        if t.Cell(1, 1).Range.Text.startswith("Q (CFM)"):
            c = t.Cell(1, 3).Range
            c.Text = "v ผ่านหน้าตัดพัดลม Ø23 (m/s)"; w.thai_size(c)
            for ri, (v, _) in zip(range(2, t.Rows.Count + 1), TABLE):
                c = t.Cell(ri, 3).Range
                c.Text = f"{v:.2f}"; w.thai_size(c)
            break
    else:
        w.skipped.append("fan table")
    w.para_text("ในโปรแกรม ANSYS Fluent กำหนดเงื่อนไขพัดลมแบบ Pressure Jump",
                f"ในโปรแกรม ANSYS Fluent กำหนดเงื่อนไขพัดลมแบบ Pressure Jump ชนิด Piecewise-linear โดยใช้ค่าในตารางโดยตรง "
                f"ความเร็ว v คำนวณจากพื้นที่หน้าตัดพัดลมในแบบจำลอง CFD (Ø23 mm ลบดุม Ø13 mm, A = {A_FAN * 1e4:.3f} × 10⁻⁴ m²) "
                f"ซึ่งเล็กกว่าช่องลมจริง Ø24 mm เพื่อให้สร้าง Mesh ได้ การคำนวณรอบแรกใช้สมการพหุนามกำลังสามที่ประมาณกราฟ "
                f"ซึ่งให้ความดันสูงเกินจริงสูงสุดประมาณ 7.5 Pa ในช่วงกราฟแบน (Stall Plateau) จึงเปลี่ยนเป็นตารางค่าและคำนวณผลทั้งหมดใหม่ "
                f"ทำให้อัตราการไหลลดลงประมาณ 7% และอุณหภูมิเพิ่มขึ้น 0.2–0.5 °C ผลในรายงานนี้ทั้งหมดใช้ตารางค่า")

    # ---------------- stock results ----------------
    w.fill_row("ผลลัพธ์", "อุณหภูมิที่ทางเข้าฮีตเบรก", {2: f1(S["hb"])})
    w.fill_row("ผลลัพธ์", "อุณหภูมิสูงสุดของฮีตซิงก์", {2: f1(S["hs"])})
    w.fill_row("ผลลัพธ์", "อัตราการระบายความร้อน", {2: f2(S["q"])})
    w.fill_row("ผลลัพธ์", "อัตราการไหลของอากาศ", {2: f2(S["flow"])})
    w.fill_row("ผลลัพธ์", "ความดันตก", {2: f"{S['dp']:.1f} (จุดทำงานบนกราฟพัดลม)"})
    w.para_text("ผลการวิเคราะห์ของแบบเดิมที่อุณหภูมิหัวฉีด 220 °C",
                f"ผลการวิเคราะห์ของแบบเดิมที่อุณหภูมิหัวฉีด 220 °C (พิมพ์ PLA) และอุณหภูมิอากาศแวดล้อม 45 °C พบว่าอุณหภูมิเฉลี่ยของ"
                f"ฮีตเบรกส่วนที่สวมอยู่ในซ็อกเก็ตของฮีตซิงก์ (ทางเข้าฮีตเบรก) มีค่า {f1(S['hb'])} °C และอุณหภูมิสูงสุดของฮีตซิงก์ "
                f"{f1(S['hs'])} °C ซึ่งไม่ผ่านเกณฑ์ 50 °C ทั้งสองข้อ ฮีตซิงก์มีอุณหภูมิค่อนข้างสม่ำเสมอ (เฉลี่ย {f1(S['hs_avg'])} °C) "
                f"ระบายความร้อนสู่อากาศได้ {f2(S['q'])} W พัดลมทำงานที่อัตราการไหล {f2(S['flow'])} m³/h "
                f"({S['flow'] / 1.699:.2f} CFM) ประมาณ {S['flow'] / 5.03 * 100:.0f}% ของอัตราการไหลอิสระ ที่ความดัน "
                f"{S['dp']:.1f} Pa ซึ่งอยู่ในช่วงกราฟแบน (Stall Plateau) ของพัดลม ความต้านทานความร้อนจากหัวฉีดถึงฮีตซิงก์ "
                f"(ผ่านฮีตเบรก) ประมาณ {(220 - S['hs']) / S['q']:.0f} K/W มากกว่าความต้านทานจากฮีตซิงก์ถึงอากาศ "
                f"(ประมาณ {(S['hs'] - T_AMB) / S['q']:.1f} K/W) มาก จึงเป็นแนวทางหลักในการพัฒนา")
    for cap, img in (("รูปแสดงการกระจายอุณหภูมิของแบบเดิม", "stock_45C_pl/temp_solids_iso.png"),
                     ("รูปแสดงอุณหภูมิบนระนาบตัดผ่านช่องครีบ", "stock_45C_pl/temp_section_fins.png"),
                     ("รูปแสดงความเร็วอากาศบนระนาบตัดผ่านช่องครีบ", "stock_45C_pl/velocity_section_fins.png"),
                     ("รูปแสดงการกระจายอุณหภูมิของแบบพัฒนา 1", "design1_45C_pl/temp_solids_iso.png"),
                     ("รูปแสดงการกระจายอุณหภูมิของแบบพัฒนา 2", "design2_45C_pl/temp_solids_iso.png"),
                     ("รูปแสดงความเร็วอากาศผ่านช่องครีบของแบบพัฒนา 2", "design2_45C_pl/velocity_section_fins.png")):
        w.swap_picture(cap, os.path.join(RES, img))
    for old in ("(อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)", "(อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)",
                "(อากาศแวดล้อม 45 °C, ช่วงสี 45–80 °C)"):
        w.replace(old, "(อากาศแวดล้อม 45 °C, ช่วงสี 45–60 °C; หัวฉีด 220 °C แสดงเป็นสีแดงเกินช่วง)")
    w.replace("(y = −6 mm) ช่วงสี 45–80 °C", "(y = −6 mm) ช่วงสี 45–60 °C")

    # ---------------- comparison table + verification section ----------------
    row = lambda d: {2: f"{f2(d['hb'])} {mark(d['hb'])}", 3: f"{f2(d['hs'])} {mark(d['hs'])}", 4: f2(d["q"]),
                     5: f"{d['dp']:.1f}"}
    w.fill_row("แบบ", "แบบเดิม", row(S))
    w.fill_row("แบบ", "แบบพัฒนา 1", row(D1))
    w.fill_row("แบบ", "แบบพัฒนา 2", row(D2))

    ref_table = next(w.doc.Tables(i) for i in range(1, w.doc.Tables.Count + 1)
                     if w.doc.Tables(i).Cell(1, 1).Range.Text.startswith("แบบ"))
    head_ref = w.find("4) การพัฒนาการออกแบบ").Paragraphs(1)
    sub_ref = w.find("1.1) การเตรียมโดเมนการคำนวณ").Paragraphs(1)
    body_ref = w.find("จากผลการวิเคราะห์ของแบบเดิม แนวทางในการพัฒนา").Paragraphs(1)
    cap_ref = w.find("รูปแสดงความเร็วอากาศผ่านช่องครีบของแบบพัฒนา 2").Paragraphs(1)

    def add(prev, text, ref):
        n = w.para_after(prev, text)
        w.paint(ref.Range, n.Range)
        return n

    p = cap_ref
    p = add(p, "5) การตรวจสอบความถูกต้องของผลการคำนวณ (Verification)", head_ref)
    p = add(p, "5.1) การลู่เข้าและสมดุลมวล/พลังงาน", sub_ref)
    p = add(p, "ผลทุกกรณีคำนวณจนค่า Scaled Residual ลดลงประมาณ 4 อันดับและคงที่ (รูปด้านล่าง) และตรวจสอบสมดุลมวลและพลังงาน "
               "โดยเทียบอัตราการไหลสุทธิผ่านผิวกล่องอากาศกับอัตราการไหลของพัดลม และเทียบความร้อนที่ออกจากลำตัวหัวฉีด (220 °C) "
               "กับความร้อนสุทธิที่ออกทางผิวกล่องอากาศ ค่าความไม่สมดุลทุกกรณีน้อยกว่า 0.01% และอุณหภูมิเปลี่ยนแปลงน้อยกว่า "
               "10⁻⁴ K ใน 50 รอบสุดท้าย", body_ref)
    pic = w.picture_after(p, os.path.join(RES, "residuals_45C_pl.png"), width=440)
    p = add(pic, "รูปแสดงประวัติค่า Scaled Residual ของแบบเดิม แบบพัฒนา 1 และแบบพัฒนา 2 (เริ่มจากผลเดิมหลังเปลี่ยนเป็นตารางค่าพัดลม)",
            cap_ref)
    p = w.table_after(p, [["กรณี", "ความไม่สมดุลมวล (%)", "ความไม่สมดุลพลังงาน (%)", "ความร้อนจากหัวฉีด (W)",
                           "การเปลี่ยนแปลงอุณหภูมิ 50 รอบสุดท้าย (K)"]] +
                      [[n, f"{d['mass']:.4f}", f"{d['energy']:.4f}", f2(d["q_in"]), f"{d['d50']:.1e}"]
                       for n, d in (("แบบเดิม", S), ("แบบพัฒนา 1", D1), ("แบบพัฒนา 2", D2))], ref_table)
    p = add(p, "5.2) ความเป็นอิสระของ Mesh (Mesh Independence) – แบบพัฒนา 2", sub_ref)
    p = add(p, f"คำนวณแบบพัฒนา 2 ด้วย Mesh 3 ระดับ และประเมินความไม่แน่นอนจากการแบ่ง Mesh ด้วยวิธี Grid Convergence Index (GCI) "
               f"ตาม Celik et al. (2008) โดยใช้ค่าอุณหภูมิที่สูงกว่าอากาศแวดล้อม (T − 45 °C) อัตราส่วนการปรับละเอียด "
               f"r₂₁ = {G['hb']['r21']:.2f}, r₃₂ = {G['hb']['r32']:.2f} ผลใช้ Mesh ระดับกลางเป็นค่าหลักของรายงาน", body_ref)
    p = w.table_after(p, [["Mesh", "จำนวนเซลล์", "T ทางเข้าฮีตเบรก (°C)", "T ฮีตซิงก์สูงสุด (°C)", "อัตราการไหล (m³/h)"],
                          ["หยาบ (Coarse)", f"{N['coarse']:,}", f2(CO["hb"]), f2(CO["hs"]), f2(CO["flow"])],
                          ["กลาง (Medium)", f"{N['medium']:,}", f2(D2["hb"]), f2(D2["hs"]), f2(D2["flow"])],
                          ["ละเอียด (Fine)", f"{N['fine']:,}", f2(FI["hb"]), f2(FI["hs"]), f2(FI["flow"])],
                          (["ผลต่างสูงสุดเทียบกับ Mesh กลาง", "–", f"±{U_MESH['hb']:.2f}", f"±{U_MESH['hs']:.2f}", "–"]
                           if any(OSC.values()) else
                           ["ค่าประมาณที่ Mesh ละเอียดมาก (Richardson)", "–", f2(G["hb"]["f_ext"] + T_AMB),
                            f2(G["hs"]["f_ext"] + T_AMB), "–"])], ref_table)
    if any(OSC.values()):
        p = add(p, f"ผลไม่ลู่เข้าแบบทางเดียว (Oscillatory Convergence): อุณหภูมิทางเข้าฮีตเบรกเป็น {f2(CO['hb'])}, "
                   f"{f2(D2['hb'])} และ {f2(FI['hb'])} °C สำหรับ Mesh หยาบ กลาง และละเอียด ค่า apparent order ที่คำนวณได้ "
                   f"(p ≈ {G['hb']['p']:.0f}–{G['hs']['p']:.0f}) สูงกว่าอันดับความแม่นยำของวิธีคำนวณ (อันดับ 2) มาก และอัตราส่วน "
                   f"การปรับละเอียด (r = {G['hb']['r32']:.2f}–{G['hb']['r21']:.2f}) ต่ำกว่าค่าแนะนำ 1.3 เนื่องจากข้อจำกัดจำนวนเซลล์ "
                   f"ของ Ansys Student จึงไม่ใช้ค่า GCI แต่ประมาณความไม่แน่นอนจาก Mesh จากผลต่างสูงสุดระหว่าง Mesh ได้ "
                   f"±{U_MESH['hb']:.2f} °C ที่ทางเข้าฮีตเบรก และ ±{U_MESH['hs']:.2f} °C ที่ฮีตซิงก์ ผลจาก Mesh ละเอียด "
                   f"({N['fine']:,} เซลล์) สูงกว่า Mesh กลาง แสดงว่าผลที่รายงานจาก Mesh กลางอาจประเมินอุณหภูมิต่ำไปประมาณ "
                   f"{FI['hb'] - D2['hb']:.1f} °C", body_ref)
    else:
        p = add(p, f"ความไม่แน่นอนจาก Mesh ของผลระดับกลาง (GCI): ทางเข้าฮีตเบรก ±{U_MESH['hb']:.2f} °C "
                   f"(p = {G['hb']['p']:.2f}) และฮีตซิงก์สูงสุด ±{U_MESH['hs']:.2f} °C (p = {G['hs']['p']:.2f})", body_ref)
    p = add(p, "5.3) ความไวต่อแบบจำลองความปั่นป่วน – แบบพัฒนา 2", sub_ref)
    p = w.table_after(p, [["แบบจำลอง", "T ทางเข้าฮีตเบรก (°C)", "T ฮีตซิงก์สูงสุด (°C)", "อัตราการไหล (m³/h)"],
                          ["k-ω SST (ค่าหลัก)", f2(D2["hb"]), f2(D2["hs"]), f2(D2["flow"])],
                          ["Laminar", f2(LAM["hb"]), f2(LAM["hs"]), f2(LAM["flow"])]], ref_table)
    add(p, f"การเปลี่ยนแบบจำลองความปั่นป่วนทำให้อุณหภูมิทางเข้าฮีตเบรกเปลี่ยน {U_TURB['hb']:.2f} °C และฮีตซิงก์สูงสุด "
           f"{U_TURB['hs']:.2f} °C ซึ่งมากกว่าระยะห่างจากเกณฑ์ของแบบพัฒนา 2 ที่ทางเข้าฮีตเบรก ({LIMIT - D2['hb']:.2f} °C)",
        body_ref)

    # ---------------- qualified conclusion ----------------
    margin_hb, margin_hs = LIMIT - D2["hb"], LIMIT - D2["hs"]
    band_hb = math.hypot(U_MESH["hb"], U_TURB["hb"])
    band_hs = math.hypot(U_MESH["hs"], U_TURB["hs"])
    robust = margin_hb > band_hb and margin_hs > band_hs
    w.para_text("ที่อุณหภูมิหัวฉีด 220 °C (พิมพ์ PLA) และอากาศแวดล้อม 45 °C แบบเดิม",
                f"ที่อุณหภูมิหัวฉีด 220 °C (พิมพ์ PLA) และอากาศแวดล้อม 45 °C แบบเดิมมีอุณหภูมิทางเข้าฮีตเบรก {f1(S['hb'])} °C และ"
                f"ฮีตซิงก์สูงสุด {f1(S['hs'])} °C ซึ่งไม่ผ่านเกณฑ์ 50 °C แบบพัฒนา 1 (ฮีตเบรกไทเทเนียม) ลดอุณหภูมิเหลือ "
                f"{f1(D1['hb'])} °C ({diff(D1['hb'], S['hb']):+.1f} °C) และ {f1(D1['hs'])} °C ({diff(D1['hs'], S['hs']):+.1f} °C) "
                f"เพราะความร้อนที่ไหลเข้าฮีตซิงก์ลดลงจาก {f2(S['q'])} W เหลือ {f2(D1['q'])} W แบบพัฒนา 2 (ฮีตเบรกไทเทเนียม "
                f"+ ฮีตซิงก์ใหม่ ขนาดและพัดลมเดิม) ได้ {f2(D2['hb'])} °C ({diff(D2['hb'], S['hb']):+.1f} °C) และ "
                f"{f2(D2['hs'])} °C ({diff(D2['hs'], S['hs']):+.1f} °C) ซึ่งอยู่ต่ำกว่าเกณฑ์เพียง {margin_hb:.2f} °C และ "
                f"{margin_hs:.2f} °C ตามลำดับ "
                + (f"เมื่อรวมความไม่แน่นอนจาก Mesh และแบบจำลองความปั่นป่วน (±{band_hb:.2f} °C และ ±{band_hs:.2f} °C) "
                   f"แบบพัฒนา 2 จึงผ่านเกณฑ์อย่างมีระยะเผื่อ" if robust else
                   f"ซึ่งน้อยกว่าความไม่แน่นอนที่ประเมินได้ (±{band_hb:.2f} °C ที่ทางเข้าฮีตเบรก และ ±{band_hs:.2f} °C "
                   f"ที่ฮีตซิงก์ จาก Mesh และแบบจำลองความปั่นป่วน) จึงสรุปได้เพียงว่าแบบพัฒนา 2 ผ่านเกณฑ์ตามค่าที่คำนวณได้ "
                   f"(Nominal Pass) ภายใต้เงื่อนไขของแบบจำลอง ยังไม่ใช่การผ่านเกณฑ์อย่างมั่นใจ "
                   + (f"และผลจาก Mesh ละเอียดได้ {f2(FI['hb'])} °C และ {f2(FI['hs'])} °C ซึ่งเกินเกณฑ์เล็กน้อย "
                      f"จึงถือว่าแบบพัฒนา 2 อยู่ที่ขอบเกณฑ์ (Borderline) " if max(FI['hb'], FI['hs']) > LIMIT else ""))
                + f"ทั้งสองแบบพัฒนามีอุณหภูมิต่ำกว่าแบบเดิม ผลจากการเปลี่ยนวัสดุฮีตเบรก ({diff(S['hb'], D1['hb']):.1f} °C) "
                f"มีมากกว่าผลจากการเปลี่ยนฮีตซิงก์ ({diff(D1['hb'], D2['hb']):.1f} °C) เพราะความต้านทานความร้อนส่วนใหญ่อยู่ที่ฮีตเบรก "
                f"ทั้งนี้การเปรียบเทียบเทียบกับฮีตเบรกเหล็กกล้าไร้สนิมที่สมมติเป็นแบบเดิม หากผลิตภัณฑ์จริงใช้ฮีตเบรกไทเทเนียมหรือแบบสองโลหะอยู่แล้ว "
                f"ผลที่ได้จะไม่ใช่การปรับปรุงจากผลิตภัณฑ์จริง หากต้องการระยะเผื่อเพิ่ม ควรลดความร้อนผ่านฮีตเบรกต่อ "
                f"(เช่น ผนังบางลงหรือเพิ่มระยะคอ) มากกว่าการเพิ่มพื้นที่ครีบ")
    w.para_text("ยังไม่ได้ศึกษาความเป็นอิสระของ Mesh",
                f"ความไม่แน่นอนจาก Mesh ของแบบพัฒนา 2 ประมาณ ±{U_MESH['hb']:.2f} °C ที่ทางเข้าฮีตเบรก และ "
                f"±{U_MESH['hs']:.2f} °C ที่ฮีตซิงก์ (หัวข้อ 5.2) ส่วนแบบเดิมและแบบพัฒนา 1 ใช้การตั้งค่า Mesh เดียวกันแต่ไม่ได้ศึกษาแยก")
    p = w.find("ไม่ได้จำลองชุดฮีตเตอร์และปลอกซิลิโคน")
    if p:
        w.para_after(p.Paragraphs(1), "แบบเดิมสมมติฮีตเบรกเป็นเหล็กกล้าไร้สนิม (k = 16.3 W/m·K) ฮีตเบรกของผลิตภัณฑ์จริงอาจเป็นไทเทเนียม "
                                      "หรือแบบสองโลหะ ผลการพัฒนาจึงเทียบกับแบบเดิมที่สมมติ ไม่ใช่กับผลิตภัณฑ์จริงโดยตรง")
    else:
        w.skipped.append("baseline bullet")

    # ---------------- references ----------------
    refs = [
        "Bambu Lab, “Hotend Replacement Guide for the P2S,” Bambu Lab Wiki. [Online]. Available: "
        "https://wiki.bambulab.com/en/p2s/maintenance/replace-hotend-and-silicone-sock (accessed Nov. 21, 2026).",
        "Bambu Lab, “Hotend Heating Assembly and Cooling Fan Replacement Guide for the P2S,” Bambu Lab Wiki. [Online]. Available: "
        "https://wiki.bambulab.com/en/p2s/maintenance/replace-hotend-heating-assembly-and-cooling-fan (accessed Nov. 21, 2026).",
        "3DJake, “Bambu Lab Cooling Fan for Hotend, P2S (FAF021) – technical specifications.” [Online]. Available: "
        "https://www.3djake.com/bambu-lab/cooling-fan-for-hotend (accessed Nov. 21, 2026).",
        "F. P. Incropera, D. P. DeWitt, T. L. Bergman, and A. S. Lavine, Fundamentals of Heat and Mass Transfer, 7th ed. "
        "Hoboken, NJ, USA: John Wiley & Sons, 2011.",
        "ANSYS, Inc., Ansys Fluent User's Guide, Release 2026 R1. Canonsburg, PA, USA: ANSYS, Inc., 2026.",
        "Pelonis Technologies, “2510-5 DC Fans (C2510X05BPLBx-5) datasheet.” [Online]. Available: "
        "https://catalog.pelonistechnologies.com/Asset/C2510-5.pdf (accessed Nov. 21, 2026).",
    ]
    for old, new in zip(("Bambu Lab Wiki, Hotend Replacement Guide", "Bambu Lab Wiki, Hotend Heating Assembly",
                         "3DJake, Bambu Lab Cooling Fan", "Incropera, F. P., et al.", "ANSYS Inc., Ansys Fluent User",
                         "Pelonis Technologies, 2510-5"), refs):
        w.para_text(old, new)
    last = w.find("Pelonis Technologies, “2510-5")
    if last:
        p = w.para_after(last.Paragraphs(1),
                         "F. R. Menter, “Two-equation eddy-viscosity turbulence models for engineering applications,” "
                         "AIAA Journal, vol. 32, no. 8, pp. 1598–1605, 1994.")
        w.para_after(p, "I. B. Celik, U. Ghia, P. J. Roache, C. J. Freitas, H. Coleman, and P. E. Raad, “Procedure for estimation "
                        "and reporting of uncertainty due to discretization in CFD applications,” Journal of Fluids Engineering, "
                        "vol. 130, no. 7, Art. no. 078001, 2008.")

print("skipped:", w.skipped or "none")
print("GCI:", {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in g.items()} for k, g in G.items()})
print("U_mesh", {k: round(v, 3) for k, v in U_MESH.items()}, "U_turb", {k: round(v, 3) for k, v in U_TURB.items()})
for n, d in (("stock", S), ("D1", D1), ("D2", D2), ("D2 lam", LAM), ("D2 coarse", CO), ("D2 fine", FI)):
    print(f"{n:9s} hb {d['hb']:.3f} hs {d['hs']:.3f} Q {d['q']:.3f} flow {d['flow']:.3f} dp {d['dp']:.1f}")
