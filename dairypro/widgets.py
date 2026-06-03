import tkinter as tk
import customtkinter as ctk
from theme import get as T

def make_label(parent, text, size=13, bold=False, color=None, **kw):
    c = color or T()["text"]
    return ctk.CTkLabel(parent, text=text, text_color=c,
                        font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"), **kw)

def make_entry(parent, placeholder="", width=200, **kw):
    t = T()
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                        fg_color=t["input_bg"], border_color=t["border"],
                        text_color=t["text"], **kw)

def make_btn(parent, text, command, style="primary", width=140, **kw):
    t = T()
    styles = {
        "primary": {"fg_color":t["btn"],    "hover_color":t["btn_h"],  "text_color":"#ffffff"},
        "ghost":   {"fg_color":"transparent","hover_color":t["card2"], "text_color":t["text"],
                    "border_width":1,"border_color":t["border"]},
        "danger":  {"fg_color":t["danger"], "hover_color":"#8b0000",   "text_color":"#ffffff"},
        "success": {"fg_color":t["success"],"hover_color":"#1b5e20",   "text_color":"#ffffff"},
        "warning": {"fg_color":t["warning"],"hover_color":"#e65100",   "text_color":"#ffffff"},
    }
    s = styles.get(style, styles["primary"])
    return ctk.CTkButton(parent, text=text, command=command, width=width, **s, **kw)

def make_combo(parent, values, width=200, command=None, **kw):
    t = T()
    c = ctk.CTkComboBox(parent, values=values, width=width,
                        fg_color=t["input_bg"], border_color=t["border"],
                        text_color=t["text"], button_color=t["btn"],
                        dropdown_fg_color=t["card"], command=command, **kw)
    c.set(values[0] if values else "")
    return c

def make_card(parent, **kw):
    t = T()
    return ctk.CTkFrame(parent, fg_color=t["card"],
                        border_color=t["border"], border_width=1,
                        corner_radius=10, **kw)

def section_title(parent, text):
    t = T()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", padx=20, pady=(18,6))
    ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=20, weight="bold"),
                 text_color=t["text"]).pack(side="left")
    return f

def date_range_bar(parent, on_change):
    """Quick date range selector bar — returns (from_var, to_var)."""
    import config
    from tkinter import StringVar
    t = T()
    bar = ctk.CTkFrame(parent, fg_color="transparent")
    from_var = StringVar()
    to_var   = StringVar()
    f,to = config.this_month_range()
    from_var.set(f); to_var.set(to)

    def set_range(f,t2):
        from_var.set(f); to_var.set(t2)
        on_change()

    for label, cmd in [
        ("This Month", lambda: set_range(*config.this_month_range())),
        ("Last 10",    lambda: set_range(*config.last_n_days(10))),
        ("Last 15",    lambda: set_range(*config.last_n_days(15))),
        ("Last 20",    lambda: set_range(*config.last_n_days(20))),
    ]:
        ctk.CTkButton(bar, text=label, command=cmd, width=90, height=28,
                      fg_color="transparent", hover_color=t["card2"],
                      text_color=t["text2"], border_width=1, border_color=t["border"],
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=(0,4))

    ctk.CTkLabel(bar, text="From:", text_color=t["text2"],
                 font=ctk.CTkFont(size=11)).pack(side="left", padx=(8,4))
    fe = ctk.CTkEntry(bar, textvariable=from_var, width=110,
                      fg_color=t["input_bg"], border_color=t["border"], text_color=t["text"])
    fe.pack(side="left", padx=(0,4))
    fe.bind("<Return>", lambda e: on_change())

    ctk.CTkLabel(bar, text="To:", text_color=t["text2"],
                 font=ctk.CTkFont(size=11)).pack(side="left", padx=(4,4))
    te = ctk.CTkEntry(bar, textvariable=to_var, width=110,
                      fg_color=t["input_bg"], border_color=t["border"], text_color=t["text"])
    te.pack(side="left", padx=(0,4))
    te.bind("<Return>", lambda e: on_change())

    return bar, from_var, to_var

class Table(tk.Frame):
    def __init__(self, parent, columns, col_widths, height=240, on_select=None):
        t = T()
        super().__init__(parent, bg=t["card"], highlightthickness=0)
        self.columns    = columns
        self.col_widths = col_widths
        self.on_select  = on_select
        self._rows      = []
        self._selected  = None
        self.t          = t
        self._build(height)

    def _build(self, height):
        t = self.t
        hdr = tk.Frame(self, bg=t["header_bg"])
        hdr.pack(fill="x")
        for col, w in zip(self.columns, self.col_widths):
            tk.Label(hdr, text=col, width=w//8, bg=t["header_bg"], fg=t["text2"],
                     font=("Segoe UI",9,"bold"), anchor="w", padx=8).pack(side="left")
        wrap = tk.Frame(self, bg=t["card"], height=height)
        wrap.pack(fill="both", expand=True)
        wrap.pack_propagate(False)
        self.canvas = tk.Canvas(wrap, bg=t["card"], highlightthickness=0, bd=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=t["card"])
        self._cw  = self.canvas.create_window((0,0), window=self.body, anchor="nw")
        self.body.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._cw, width=e.width))
        self.body.bind("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1 if e.delta>0 else 1,"units"))

    def clear(self):
        for w in self.body.winfo_children(): w.destroy()
        self._rows = []; self._selected = None

    def add_row(self, values, tag=None, bold=False, bg_override=None):
        t   = self.t
        idx = len(self._rows)
        bg  = bg_override or (t["row_even"] if idx%2==0 else t["row_odd"])
        row = tk.Frame(self.body, bg=bg, cursor="hand2")
        row.pack(fill="x")
        for val, w in zip(values, self.col_widths):
            lbl = tk.Label(row, text=str(val), width=w//8, bg=bg, fg=t["text"],
                           font=("Segoe UI",10,"bold" if bold else "normal"),
                           anchor="w", padx=8)
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, r=row, tg=tag: self._click(r, tg))
        row.bind("<Button-1>", lambda e, r=row, tg=tag: self._click(r, tg))
        row.bind("<Enter>",  lambda e, r=row, ob=bg: r.configure(bg=t["row_hover"]))
        row.bind("<Leave>",  lambda e, r=row, ob=bg: r.configure(bg=ob))
        self._rows.append((row, bg, tag))
        return row

    def _click(self, row, tag):
        t = self.t
        if self._selected:
            pr, pb, _ = self._selected
            try: pr.configure(bg=pb)
            except: pass
        for item in self._rows:
            if item[0] == row:
                self._selected = item
                row.configure(bg=t["btn"])
                for child in row.winfo_children():
                    try: child.configure(bg=t["btn"])
                    except: pass
                break
        if self.on_select and tag is not None:
            self.on_select(tag)

    def empty_state(self, msg="No records found"):
        t = self.t
        tk.Label(self.body, text=msg, bg=t["card"], fg=t["text3"],
                 font=("Segoe UI",11), pady=30).pack(fill="x")

class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, sub="", color=None):
        t = T()
        super().__init__(parent, fg_color=t["card"], border_color=t["border"],
                         border_width=1, corner_radius=10)
        c = color or t["btn"]
        ctk.CTkFrame(self, fg_color=c, width=4, corner_radius=2).pack(side="left", fill="y")
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", padx=14, pady=12)
        ctk.CTkLabel(inner, text=value, font=ctk.CTkFont(size=22,weight="bold"),
                     text_color=t["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=11),
                     text_color=t["text2"]).pack(anchor="w")
        if sub:
            ctk.CTkLabel(inner, text=sub, font=ctk.CTkFont(size=10),
                         text_color=t["text3"]).pack(anchor="w")
