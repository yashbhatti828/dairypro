"""
Formula Manager — Phase 1
Multiple formula sets, each with custom user-defined inputs.
Rows reference inputs and previous rows by name. Cascades on Calculate.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from widgets import make_label, make_entry, make_btn, make_card, make_combo, section_title
from theme import get as T
import config, math

class FormulasPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app         = app
        self.active_set  = None   # currently open formula set id
        self.input_widgets = {}   # name -> Entry widget
        self.formula_rows  = []   # list of dicts per row

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Formula Manager")

        # ── Top: formula set selector ─────────────────────────────────────────
        sets_card = make_card(self)
        sets_card.pack(fill="x", padx=20, pady=(0,10))
        sets_inner = ctk.CTkFrame(sets_card, fg_color="transparent")
        sets_inner.pack(padx=16, pady=12, fill="x")

        make_label(sets_inner,"Formula Sets",size=13,bold=True).pack(side="left",padx=(0,12))

        formulas = config.load("formulas")
        # formulas is now a list of sets:
        # [{"id":1,"name":"Milk Rate","inputs":[...],"rows":[...]}, ...]
        if not isinstance(formulas, list) or (formulas and "rows" not in formulas[0]):
            # migrate old format
            formulas = []
            config.save("formulas", formulas)

        self.sets = formulas
        self.sets_frame = ctk.CTkFrame(sets_inner, fg_color="transparent")
        self.sets_frame.pack(side="left", fill="x", expand=True)
        self._render_set_tabs()

        make_btn(sets_inner,"+ New Set",self._new_set,style="ghost",width=110).pack(side="right")

        # ── Main editor area ─────────────────────────────────────────────────
        self.editor = ctk.CTkFrame(self, fg_color="transparent")
        self.editor.pack(fill="both", expand=True, padx=20, pady=(0,16))

        if self.active_set is not None:
            self._render_editor()
        else:
            make_label(self.editor,
                "Create or select a formula set to begin.",
                size=12, color=T()["text3"]).pack(pady=40)

    def _render_set_tabs(self):
        for w in self.sets_frame.winfo_children(): w.destroy()
        t = T()
        for s in self.sets:
            active = s["id"] == self.active_set
            ctk.CTkButton(
                self.sets_frame,
                text=s["name"],
                width=120, height=30,
                fg_color=t["btn"] if active else "transparent",
                hover_color=t["btn_h"],
                text_color="#fff" if active else t["text"],
                border_width=1, border_color=t["border"],
                font=ctk.CTkFont(size=12, weight="bold" if active else "normal"),
                command=lambda sid=s["id"]: self._select_set(sid)
            ).pack(side="left", padx=(0,6))

    def _select_set(self, sid):
        self.active_set = sid
        for w in self.editor.winfo_children(): w.destroy()
        self._render_set_tabs()
        self._render_editor()

    def _new_set(self):
        name = simpledialog.askstring("New Formula Set","Enter a name (e.g. Milk Rate, Cream Rate):")
        if not name: return
        new_set = {"id": config.next_id(self.sets), "name": name.strip(), "inputs": [], "rows": []}
        self.sets.append(new_set)
        config.save("formulas", self.sets)
        self.active_set = new_set["id"]
        self._render_set_tabs()
        for w in self.editor.winfo_children(): w.destroy()
        self._render_editor()

    def _get_active(self):
        return next((s for s in self.sets if s["id"]==self.active_set), None)

    def _render_editor(self):
        s = self._get_active()
        if not s: return
        t = T()
        for w in self.editor.winfo_children(): w.destroy()

        # ── Inputs section ───────────────────────────────────────────────────
        inp_card = make_card(self.editor)
        inp_card.pack(fill="x", pady=(0,10))

        hdr = ctk.CTkFrame(inp_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10,4))
        make_label(hdr,"Inputs",size=13,bold=True).pack(side="left")
        make_label(hdr,"Define your inputs. These become available in formulas by name.",
                   size=11, color=t["text2"]).pack(side="left", padx=(12,0))
        make_btn(hdr,"+ Add Input",lambda: self._add_input(s),style="ghost",width=110).pack(side="right")

        self.inputs_frame = ctk.CTkFrame(inp_card, fg_color="transparent")
        self.inputs_frame.pack(fill="x", padx=16, pady=(0,10))
        self.input_widgets = {}
        self._render_inputs(s)

        # ── Formula rows ─────────────────────────────────────────────────────
        rows_card = make_card(self.editor)
        rows_card.pack(fill="both", expand=True, pady=(0,0))

        rhdr = ctk.CTkFrame(rows_card, fg_color="transparent")
        rhdr.pack(fill="x", padx=16, pady=(10,4))
        make_label(rhdr,"Formula Rows",size=13,bold=True).pack(side="left")
        make_label(rhdr,"Each row can use input names and previous row names.",
                   size=11, color=t["text2"]).pack(side="left", padx=(12,0))

        # Column headers
        col_hdr = tk.Frame(rows_card, bg=t["header_bg"])
        col_hdr.pack(fill="x", padx=8)
        for txt, w in [("Row Name",140),("Formula",320),("Description",200),("Result",120),("Output?",70),("",50)]:
            tk.Label(col_hdr, text=txt, bg=t["header_bg"], fg=t["text2"],
                     font=("Segoe UI",9,"bold"), anchor="w", padx=6,
                     width=w//8).pack(side="left")

        # Scrollable rows
        wrap = tk.Frame(rows_card, bg=t["card"])
        wrap.pack(fill="both", expand=True, padx=8, pady=4)
        canvas = tk.Canvas(wrap, bg=t["card"], highlightthickness=0, height=220)
        sb = tk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.rows_body = tk.Frame(canvas, bg=t["card"])
        cwin = canvas.create_window((0,0), window=self.rows_body, anchor="nw")
        self.rows_body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cwin, width=e.width))

        self.formula_rows = []
        for row in s.get("rows",[]):
            self._add_row_widget(row)

        # Buttons
        btn_bar = ctk.CTkFrame(rows_card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=8)
        make_btn(btn_bar,"+ Add Row",   self._add_new_row,  style="ghost",width=120).pack(side="left",padx=(0,8))
        make_btn(btn_bar,"Calculate",   self._calculate,    width=120).pack(side="left",padx=(0,8))
        make_btn(btn_bar,"Save Set",    self._save_set,     width=120).pack(side="left",padx=(0,8))
        make_btn(btn_bar,"Apply Output → Milk Rate",self._apply_output,style="success",width=200).pack(side="left",padx=(0,8))
        make_btn(btn_bar,"Delete Set",  self._delete_set,   style="danger",width=110).pack(side="right")

    def _render_inputs(self, s):
        for w in self.inputs_frame.winfo_children(): w.destroy()
        t = T()
        self.input_widgets = {}
        for inp in s.get("inputs",[]):
            row = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            make_label(row, inp["label"], size=12, color=t["text"]).pack(side="left", padx=(0,6))
            make_label(row, f"({inp['name']})", size=11, color=t["text3"]).pack(side="left", padx=(0,10))
            e = make_entry(row, inp.get("default",""), width=120)
            e.pack(side="left", padx=(0,10))
            self.input_widgets[inp["name"]] = e
            make_btn(row,"✕",
                     lambda n=inp["name"],s=s: self._remove_input(s,n),
                     style="danger", width=32).pack(side="left")

    def _add_input(self, s):
        t = T()
        # Simple dialog
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add Input")
        dlg.geometry("360x240")
        dlg.grab_set()
        dlg.configure(fg_color=t["bg"])

        make_label(dlg,"Input Name (used in formulas):",size=12).pack(padx=20,pady=(16,4),anchor="w")
        name_e = make_entry(dlg,"e.g. fat",width=300)
        name_e.pack(padx=20, pady=(0,8))

        make_label(dlg,"Label (shown to user):",size=12).pack(padx=20,pady=(0,4),anchor="w")
        label_e = make_entry(dlg,"e.g. Fat %",width=300)
        label_e.pack(padx=20, pady=(0,8))

        make_label(dlg,"Default value (optional):",size=12).pack(padx=20,pady=(0,4),anchor="w")
        default_e = make_entry(dlg,"e.g. 0",width=300)
        default_e.pack(padx=20, pady=(0,12))

        def _add():
            nm  = name_e.get().strip()
            lbl = label_e.get().strip()
            if not nm or not lbl: return
            s.setdefault("inputs",[]).append({
                "name":nm, "label":lbl, "default":default_e.get().strip()})
            config.save("formulas",self.sets)
            dlg.destroy()
            self._render_inputs(s)

        make_btn(dlg,"Add Input",_add,width=140).pack(pady=(0,12))

    def _remove_input(self, s, name):
        s["inputs"] = [i for i in s.get("inputs",[]) if i["name"]!=name]
        config.save("formulas",self.sets)
        self._render_inputs(s)

    def _add_row_widget(self, data=None):
        t  = T()
        idx= len(self.formula_rows)
        bg = t["row_even"] if idx%2==0 else t["row_odd"]
        row = tk.Frame(self.rows_body, bg=bg)
        row.pack(fill="x", pady=1)

        name_e    = tk.Entry(row, width=16, bg=bg, fg=t["text"], insertbackground=t["text"],
                             relief="flat", font=("Segoe UI",10),
                             highlightthickness=1, highlightbackground=t["border"])
        formula_e = tk.Entry(row, width=38, bg=bg, fg=t["text"], insertbackground=t["text"],
                             relief="flat", font=("Segoe UI",10,"italic"),
                             highlightthickness=1, highlightbackground=t["border"])
        desc_e    = tk.Entry(row, width=24, bg=bg, fg=t["text"], insertbackground=t["text"],
                             relief="flat", font=("Segoe UI",10),
                             highlightthickness=1, highlightbackground=t["border"])
        result_lbl= tk.Label(row, text="—", width=13, bg=bg, fg=t["highlight"],
                             font=("Segoe UI",10,"bold"), anchor="w", padx=4)
        is_output = tk.BooleanVar(value=data.get("is_output",False) if data else False)
        out_chk   = tk.Checkbutton(row, variable=is_output, bg=bg,
                                    activebackground=bg, selectcolor=bg)
        del_btn   = tk.Button(row, text="✕", bg=t["danger"], fg="#fff",
                              relief="flat", bd=0, width=3,
                              font=("Segoe UI",9),
                              command=lambda r=row,d=None: self._del_row(r))

        for w in [name_e, formula_e, desc_e, result_lbl, out_chk, del_btn]:
            w.pack(side="left", padx=2, pady=4)

        if data:
            name_e.insert(0,    data.get("name",""))
            formula_e.insert(0, data.get("formula",""))
            desc_e.insert(0,    data.get("description",""))

        self.formula_rows.append({
            "frame":row,"name":name_e,"formula":formula_e,
            "desc":desc_e,"result":result_lbl,"is_output":is_output
        })

    def _add_new_row(self):
        self._add_row_widget()

    def _del_row(self, frame):
        self.formula_rows = [r for r in self.formula_rows if r["frame"]!=frame]
        frame.destroy()

    def _calculate(self):
        s = self._get_active()
        if not s: return
        # Build namespace from inputs
        namespace = {"sqrt":math.sqrt,"abs":abs,"round":round,
                     "min":min,"max":max,"pi":math.pi}
        for inp in s.get("inputs",[]):
            widget = self.input_widgets.get(inp["name"])
            val    = widget.get().strip() if widget else inp.get("default","0")
            try: namespace[inp["name"]] = float(val)
            except: namespace[inp["name"]] = 0.0

        for r in self.formula_rows:
            name    = r["name"].get().strip()
            formula = r["formula"].get().strip()
            if not name or not formula:
                r["result"].configure(text="—"); continue
            try:
                result = eval(formula, {"__builtins__":{}}, namespace)
                result = round(float(result),4)
                namespace[name] = result
                r["result"].configure(text=str(result))
            except Exception as ex:
                r["result"].configure(text="Error")

        self.app.set_status("Calculated.")

    def _apply_output(self):
        # Find last row marked as output, apply to milk rate
        output_val = None
        for r in self.formula_rows:
            if r["is_output"].get():
                try: output_val = float(r["result"].cget("text"))
                except: pass
        if output_val is None:
            # fallback: last computed result
            for r in reversed(self.formula_rows):
                try:
                    output_val = float(r["result"].cget("text"))
                    break
                except: pass
        if output_val is None:
            messagebox.showinfo("Info","Calculate first."); return
        products = config.load("products")
        for p in products:
            if p["name"]=="Milk": p["rate"] = round(output_val,2)
        config.save("products",products)
        self.app.set_status(f"Milk rate set to ₹{output_val:.2f}")
        messagebox.showinfo("Applied",f"Milk rate updated to ₹{output_val:.2f}/L")

    def _save_set(self):
        s = self._get_active()
        if not s: return
        rows = []
        for r in self.formula_rows:
            name = r["name"].get().strip()
            if not name: continue
            rows.append({
                "name":       name,
                "formula":    r["formula"].get().strip(),
                "description":r["desc"].get().strip(),
                "is_output":  r["is_output"].get(),
            })
        s["rows"] = rows
        config.save("formulas",self.sets)
        self.app.set_status(f"Formula set '{s['name']}' saved.")

    def _delete_set(self):
        s = self._get_active()
        if not s: return
        if not messagebox.askyesno("Delete",f"Delete formula set '{s['name']}'?"): return
        self.sets = [x for x in self.sets if x["id"]!=self.active_set]
        config.save("formulas",self.sets)
        self.active_set = None
        self.refresh()
