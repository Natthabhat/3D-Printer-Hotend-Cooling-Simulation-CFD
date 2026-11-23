"""Helpers for editing the report that is open in Word (COM). Thai text here displays at the regular size,
so every edit sets SizeBi = Size; new paragraphs are made by splitting before a paragraph mark (inserting after
the mark can land inside a following table)."""
import win32com.client as win32

WD_CHAR = 1


class Doc:
    def __init__(self, name="Hotend_Cooling_Report.docx"):
        self.wd = win32.GetActiveObject("Word.Application")
        docs = [self.wd.Documents(i) for i in range(1, self.wd.Documents.Count + 1)]
        match = [d for d in docs if d.Name == name]
        assert match, f"{name} is not open in Word (open: {[d.Name for d in docs]})"
        self.doc = match[0]
        self.skipped = []

    def find(self, text):
        rg = self.doc.Content
        return rg if rg.Find.Execute(FindText=text, MatchCase=True, Wrap=0) else None

    @staticmethod
    def thai_size(rg):
        for w in rg.Words:
            if w.Font.Size and w.Font.Size < 100:
                w.Font.SizeBi = w.Font.Size

    def replace(self, old, new):
        rg = self.find(old)
        if rg is None:
            self.skipped.append(old[:45]); return None
        rg.Text = new
        rg.HighlightColorIndex = 0
        self.thai_size(rg)
        return rg

    def para_text(self, start, new):
        rg = self.find(start)
        if rg is None:
            self.skipped.append(start[:45]); return None
        p = rg.Paragraphs(1)
        r = p.Range
        r.MoveEnd(WD_CHAR, -1)
        r.Text = new
        r.HighlightColorIndex = 0
        self.thai_size(p.Range)
        return p

    def para_after(self, p, text, plain=True):
        end = p.Range.End - 1
        self.doc.Range(end, end).InsertAfter("\r")
        n = self.doc.Range(end + 1, end + 1).Paragraphs(1)
        r = n.Range
        r.MoveEnd(WD_CHAR, -1)
        r.Text = text
        r.HighlightColorIndex = 0
        if plain:
            r.Font.Bold = r.Font.BoldBi = False
        self.thai_size(n.Range)
        return n

    def picture_after(self, p, path, width=400):
        pic = self.para_after(p, "")
        pic.Range.ParagraphFormat.Alignment = 1
        shp = pic.Range.InlineShapes.AddPicture(path, False, True)
        r = shp.Height / shp.Width
        shp.Width, shp.Height = width, width * r
        return pic

    def box_to_picture(self, placeholder, path, width=380):
        rg = self.find(placeholder)
        if rg is None:
            self.skipped.append(placeholder[:45]); return
        cell = rg.Cells(1)
        cell.Range.Text = ""
        cell.Shading.BackgroundPatternColor = -16777216
        shp = cell.Range.InlineShapes.AddPicture(path, False, True)
        r = shp.Height / shp.Width
        shp.Width, shp.Height = width, width * r

    def figure_shape(self, caption_para):
        """The picture belonging to a caption: in the paragraph above it, or inside a table ending right above it."""
        prev = caption_para.Previous()
        if prev is not None and prev.Range.InlineShapes.Count and not prev.Range.Information(12):
            return prev.Range.InlineShapes(1)
        if caption_para.Range.Information(12):           # caption inside a table cell (side-by-side figures)
            cell = caption_para.Range.Cells(1).Range
            return cell.InlineShapes(1) if cell.InlineShapes.Count else None
        for i in range(1, self.doc.Tables.Count + 1):
            t = self.doc.Tables(i)
            if 0 <= caption_para.Range.Start - t.Range.End <= 2 and t.Range.InlineShapes.Count:
                return t.Range.InlineShapes(1)
        return None

    def swap_picture(self, caption_start, path):
        cap = self.find(caption_start)
        if cap is None:
            self.skipped.append("picture " + caption_start[:30]); return
        old = self.figure_shape(cap.Paragraphs(1))
        if old is None:
            self.skipped.append("no picture for " + caption_start[:30]); return
        w = old.Width
        rg = old.Range
        old.Delete()
        new = rg.InlineShapes.AddPicture(path, False, True)
        r = new.Height / new.Width
        new.Width, new.Height = w, w * r

    def fill_row(self, head, label, values):
        for i in range(1, self.doc.Tables.Count + 1):
            t = self.doc.Tables(i)
            if not t.Cell(1, 1).Range.Text.startswith(head):
                continue
            for ri in range(2, t.Rows.Count + 1):
                if t.Cell(ri, 1).Range.Text.startswith(label):
                    for ci, val in values.items():
                        c = t.Cell(ri, ci).Range
                        c.Text = val
                        c.HighlightColorIndex = 0
                        self.thai_size(c)
                    return
        self.skipped.append(f"table {head}/{label}")

    def paint(self, src, dst):
        """Copy all formatting (paragraph + characters) of range src onto range dst (Word's format painter)."""
        self.doc.Activate()
        src.Select(); self.wd.Selection.CopyFormat()
        dst.Select(); self.wd.Selection.PasteFormat()

    def table_after(self, p, rows, style_from=None):
        """Insert a bordered table after paragraph p (header row shaded + bold); returns the paragraph after it."""
        holder = self.para_after(p, "")
        t = self.doc.Tables.Add(holder.Range, len(rows), len(rows[0]))
        t.Borders.Enable = True
        t.Rows.Alignment = 1
        ref = style_from.Cell(2, 2).Range.Font if style_from else None
        for i, row in enumerate(rows, 1):
            for j, val in enumerate(row, 1):
                c = t.Cell(i, j).Range
                c.Text = val
                if ref:
                    c.Font.Name, c.Font.NameBi, c.Font.Size = ref.Name, ref.NameBi, ref.Size
                c.Font.Bold = c.Font.BoldBi = i == 1
                c.Font.Italic = c.Font.ItalicBi = False
                c.ParagraphFormat.Alignment = 0 if (j == 1 and i > 1) else 1
                c.ParagraphFormat.SpaceAfter = 0
                c.ParagraphFormat.FirstLineIndent = 0
                c.HighlightColorIndex = 0
                self.thai_size(c)
                if i == 1:
                    t.Cell(i, j).Shading.BackgroundPatternColor = 0xF3E2D9
        t.Rows(1).HeadingFormat = True
        t.AutoFitBehavior(1); t.AutoFitBehavior(2)
        nxt = self.doc.Range(t.Range.End, t.Range.End)
        nxt.InsertBefore("\r")                        # fresh empty paragraph right after the table
        tail = self.doc.Range(t.Range.End, t.Range.End).Paragraphs(1)
        tail.Range.Font.Bold = tail.Range.Font.BoldBi = False
        return tail

    def numbered(self, rg, label, seq, sep=" "):
        """Put '<label> <SEQ field><sep>' at the start of range rg (a caption)."""
        start = self.doc.Range(rg.Start, rg.Start)
        start.InsertBefore(label + " ")
        pos = self.doc.Range(rg.Start + len(label) + 1, rg.Start + len(label) + 1)
        f = self.doc.Fields.Add(pos, -1, f"SEQ {seq} \\* ARABIC", False)
        after = self.doc.Range(f.Result.End + 1, f.Result.End + 1)
        after.InsertBefore(sep)
        return f

    def undo_record(self, name):
        return _Undo(self.wd, name)


class _Undo:
    def __init__(self, wd, name):
        self.wd, self.name = wd, name

    def __enter__(self):
        self.sel = (self.wd.Selection.Start, self.wd.Selection.End)
        self.wd.UndoRecord.StartCustomRecord(self.name)

    def __exit__(self, *exc):
        self.wd.UndoRecord.EndCustomRecord()
        try:
            self.wd.ActiveDocument.Range(*self.sel).Select()
        except Exception:                    # another document may be active; the selection is cosmetic
            pass
        return False
