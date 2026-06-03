"""
Supplier Entry — separate form with 3 calculation modes.
Global fatrate at top. Mode remembered per supplier.
Morning + Evening sessions.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from widgets import make_label, make_entry, make_btn, make_combo, make_card, section_title, date_range_bar, Table
from theme import get as T
import config
from datetime import date, datetime, timedelta

MODES = ["Full (Fat + SNF)", "Direct Rate", "Fixed Rate"]

class SupplierEntryPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self, "Supplier Milk Entry")

        # ── Global fatrate bar ───────────────────────────────────────────────
        fat_bar = make_card(self)
        fat_bar.pack(fill="x", padx=20, pady=(0,8))
        fb_inner = ctk.CTkFrame(fat_bar, fg_color="transparent")
        fb_inner.pack(padx=16, pady=10, fill="x")
        make_label(fb_inner,"Global Fat Rate (default for all suppliers):",size=12,bold=True).pack(side="left",padx=(0,10))
        settings = config.load("settings")
        self.global_fatrate = tk.StringVar(value=str(settings.get("global_fatrate",5850.0)))
        fr_e = ctk.CTkEntry(fb_inner, textvariable=self.global_fatrate, width=120,
                             fg_color=t["input_bg"], border_color=t["btn"],
                             text_color=t["text"], border_width=2)
        fr_e.pack(side="left", padx=(0,10))
        make_btn(fb_inner,"Save as Default", self._save_global_fatrate, style="ghost", width=140).pack(side="left")
        make_label(fb_inner,"(suppliers can override per entry)",size=11,color=t["text3"]).pack(side="left",padx=(10,0))

        # ── Entry form ───────────────────────────────────────────────────────
        card = make_card(self)
        card.pack(fill="x", padx=20, pady=(0,8))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=16, pady=14, fill="x")

        # Row 1 — Supplier + Date + Mode
        make_label(form,"Supplier",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=6)
        suppliers = config.load("suppliers")
        names = [s["name"] for s in suppliers if s.get("active",True)]
        self.sup_c = make_combo(form, names if names else ["No suppliers"], width=200,
                                 command=self._on_supplier_change)
        self.sup_c.grid(row=0,column=1,pady=6,padx=(0,20))

        make_label(form,"Date",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.date_e = make_entry(form,"YYYY-MM-DD",width=140)
        self.date_e.insert(0,date.today().isoformat())
        self.date_e.grid(row=0,column=3,pady=6,padx=(0,20))

        make_label(form,"Calc Mode",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.mode_c = make_combo(form, MODES, width=200, command=self._on_mode_change)
        self.mode_c.grid(row=0,column=5,pady=6)

        # Dynamic input area
        self.inputs_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.inputs_frame.pack(padx=16, pady=(0,8), fill="x")

        # Preview + result
        self.result_frame = ctk.CTkFrame(card, fg_color=t["card2"], corner_radius=8)
        self.result_frame.pack(padx=16, pady=(0,8), fill="x")
        self.result_lbl = make_label(self.result_frame,"Enter values to calculate",size=12,color=t["text2"])
        self.result_lbl.pack(padx=12,pady=8,anchor="w")

        # Session + save
        sess_row = ctk.CTkFrame(card, fg_color="transparent")
        sess_row.pack(padx=16, pady=(0,14), fill="x")
        make_label(sess_row,"Session:",size=12,color=t["text2"]).pack(side="left",padx=(0,8))
        self.session_c = make_combo(sess_row,["Morning","Evening","Full Day"],width=130)
        self.session_c.pack(side="left",padx=(0,16))
        make_btn(sess_row,"Save Entry",self._save,width=140).pack(side="left")

        # Load saved mode for first supplier
        self._on_supplier_change(self.sup_c.get())

        # ── Recurring ────────────────────────────────────────────────────────
        rec_card = make_card(self)
        rec_card.pack(fill="x", padx=20, pady=(0,8))
        make_label(rec_card,"Recurring Entry",size=13,bold=True).pack(anchor="w",padx=16,pady=(12,4))
        make_label(rec_card,"Fill a date range with fixed values. Morning and Evening set separately.",
                   size=11,color=t["text2"]).pack(anchor="w",padx=16,pady=(0,8))

        rform = ctk.CTkFrame(rec_card, fg_color="transparent")
        rform.pack(padx=16, pady=(0,4), fill="x")

        make_label(rform,"Supplier",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=4)
        self.r_sup_c = make_combo(rform, names if names else ["No suppliers"], width=180)
        self.r_sup_c.grid(row=0,column=1,pady=4,padx=(0,16))

        make_label(rform,"Mode",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.r_mode_c = make_combo(rform, MODES, width=180)
        self.r_mode_c.grid(row=0,column=3,pady=4,padx=(0,16))

        make_label(rform,"Fat Rate",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.r_fatrate_e = make_entry(rform,str(settings.get("global_fatrate",5850)),width=100)
        self.r_fatrate_e.grid(row=0,column=5,pady=4)

        # Morning/Evening qty rows
        make_label(rform,"Morning Qty",size=12,color=t["text2"]).grid(row=1,column=0,sticky="w",padx=(0,8),pady=4)
        self.r_m_qty = make_entry(rform,"0",width=100)
        self.r_m_qty.grid(row=1,column=1,pady=4,padx=(0,16),sticky="w")

        make_label(rform,"Morning Fat%",size=12,color=t["text2"]).grid(row=1,column=2,sticky="w",padx=(0,8))
        self.r_m_fat = make_entry(rform,"0",width=100)
        self.r_m_fat.grid(row=1,column=3,pady=4,padx=(0,16),sticky="w")

        make_label(rform,"Evening Qty",size=12,color=t["text2"]).grid(row=2,column=0,sticky="w",padx=(0,8),pady=4)
        self.r_e_qty = make_entry(rform,"0",width=100)
        self.r_e_qty.grid(row=2,column=1,pady=4,padx=(0,16),sticky="w")

        make_label(rform,"Evening Fat%",size=12,color=t["text2"]).grid(row=2,column=2,sticky="w",padx=(0,8))
        self.r_e_fat = make_entry(rform,"0",width=100)
        self.r_e_fat.grid(row=2,column=3,pady=4,padx=(0,16),sticky="w")

        # Date range bar
        rdate_row = ctk.CTkFrame(rec_card, fg_color="transparent")
        rdate_row.pack(padx=16, pady=(0,4), fill="x")
        rbar, self.r_from_var, self.r_to_var = date_range_bar(rdate_row, lambda: None)
        rbar.pack(fill="x")

        skip_row = ctk.CTkFrame(rec_card, fg_color="transparent")
        skip_row.pack(padx=16, pady=(0,4), anchor="w")
        self.r_skip_existing = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(skip_row, text="Skip days that already have an entry",
                         variable=self.r_skip_existing,
                         text_color=t["text"], fg_color=t["btn"],
                         border_color=t["border"]).pack(side="left")

        self.r_result_lbl = make_label(rec_card,"",size=12,color=t["success"])
        self.r_result_lbl.pack(anchor="w",padx=16,pady=(0,4))
        make_btn(rec_card,"Fill Date Range",self._save_recurring,width=160).pack(
            anchor="w",padx=16,pady=(0,14))

        # ── Today's supplier entries ─────────────────────────────────────────
        make_label(self,"Today's Supplier Entries",size=14,bold=True).pack(anchor="w",padx=20,pady=(8,4))
        tcard = make_card(self)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        self.today_tbl = Table(tcard,
            ["Supplier","Date","Session","Qty","Fat%","Meter","SNF","Mode","Amount"],
            [150,110,90,60,60,70,60,130,110], height=200)
        self.today_tbl.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_today()

    def _save_global_fatrate(self):
        try: val = float(self.global_fatrate.get())
        except: messagebox.showerror("Error","Enter valid fatrate."); return
        settings = config.load("settings")
        settings["global_fatrate"] = val
        config.save("settings",settings)
        self.app.set_status(f"Global fat rate set to {val}")

    def _on_supplier_change(self, name):
        suppliers = config.load("suppliers")
        sup = next((s for s in suppliers if s["name"]==name), None)
        if sup and sup.get("calc_mode"):
            self.mode_c.set(sup["calc_mode"])
        self._on_mode_change(self.mode_c.get())

    def _on_mode_change(self, mode):
        for w in self.inputs_frame.winfo_children(): w.destroy()
        t = T()
        settings = config.load("settings")
        default_fr = str(settings.get("global_fatrate",5850))

        self.input_vars = {}

        def add_field(label, key, default="", width=120):
            f = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
            f.pack(side="left", padx=(0,16))
            make_label(f,label,size=11,color=t["text2"]).pack(anchor="w")
            var = tk.StringVar(value=default)
            e = ctk.CTkEntry(f, textvariable=var, width=width,
                             fg_color=t["input_bg"], border_color=t["border"], text_color=t["text"])
            e.pack()
            e.bind("<KeyRelease>", lambda ev: self._calc_preview())
            self.input_vars[key] = var

        if "Full" in mode:
            add_field("Quantity (L)","qty")
            add_field("Fat %","fat")
            add_field("Meter","meter")
            add_field("Fat Rate","fatrate",default_fr,width=100)
        elif "Direct" in mode:
            add_field("Quantity (L)","qty")
            add_field("Fat %","fat")
            add_field("Fat Rate","fatrate",default_fr,width=100)
        else:  # Fixed
            add_field("Quantity (L)","qty")
            add_field("Fixed Rate (₹/L)","rate")

    def _calc_preview(self):
        try:
            mode = self.mode_c.get()
            v    = self.input_vars
            def fv(k): return float(v[k].get()) if v.get(k) and v[k].get().strip() else 0.0
            if "Full" in mode:
                r = config.calc_full(fv("qty"),fv("fat"),fv("meter"),fv("fatrate"))
                self.result_lbl.configure(
                    text=f"SNF: {r['SNF']}   |   Amount: ₹{r['amount']:,.2f}")
            elif "Direct" in mode:
                r = config.calc_direct(fv("qty"),fv("fat"),fv("fatrate"))
                self.result_lbl.configure(text=f"Amount: ₹{r['amount']:,.2f}")
            else:
                r = config.calc_fixed(fv("qty"),fv("rate"))
                self.result_lbl.configure(text=f"Amount: ₹{r['amount']:,.2f}")
        except: pass

    def _save(self):
        sup_name = self.sup_c.get().strip()
        if not sup_name or sup_name=="No suppliers":
            messagebox.showerror("Error","Select a supplier."); return
        suppliers = config.load("suppliers")
        sup = next((s for s in suppliers if s["name"]==sup_name),None)
        if not sup: return
        date_str = self.date_e.get().strip()
        try: datetime.strptime(date_str,"%Y-%m-%d")
        except: messagebox.showerror("Error","Invalid date."); return

        mode = self.mode_c.get()
        v    = self.input_vars
        def fv(k): return float(v[k].get()) if v.get(k) and v[k].get().strip() else 0.0

        try:
            if "Full" in mode:
                qty,fat,meter,fatrate = fv("qty"),fv("fat"),fv("meter"),fv("fatrate")
                r = config.calc_full(qty,fat,meter,fatrate)
                entry = {"qty":qty,"fat":fat,"meter":meter,"fatrate":fatrate,"SNF":r["SNF"]}
            elif "Direct" in mode:
                qty,fat,fatrate = fv("qty"),fv("fat"),fv("fatrate")
                r = config.calc_direct(qty,fat,fatrate)
                entry = {"qty":qty,"fat":fat,"fatrate":fatrate,"SNF":None}
            else:
                qty,rate = fv("qty"),fv("rate")
                r = config.calc_fixed(qty,rate)
                entry = {"qty":qty,"rate":rate,"SNF":None}
        except Exception as ex:
            messagebox.showerror("Error",str(ex)); return

        if entry["qty"] <= 0:
            messagebox.showerror("Error","Enter valid quantity."); return

        entries = config.load("sup_entries")
        entries.append({
            "id":config.next_id(entries),
            "sup_id":sup["id"],
            "date":date_str,
            "session":self.session_c.get(),
            "mode":mode,
            "amount":r["amount"],
            **entry
        })
        config.save("sup_entries",entries)

        # Remember mode for this supplier
        sup["calc_mode"] = mode
        config.save("suppliers",suppliers)

        self.result_lbl.configure(text=f"Saved — ₹{r['amount']:,.2f}")
        self.app.set_status(f"Supplier entry saved — ₹{r['amount']:,.2f}")
        self.app.update_badge()
        self._refresh_today()

    def _save_recurring(self):
        sup_name = self.r_sup_c.get().strip()
        if not sup_name or sup_name=="No suppliers":
            messagebox.showerror("Error","Select a supplier."); return
        suppliers = config.load("suppliers")
        sup = next((s for s in suppliers if s["name"]==sup_name),None)
        if not sup: return

        mode = self.r_mode_c.get()
        try: fatrate = float(self.r_fatrate_e.get())
        except: fatrate = 5850.0
        try: m_qty = float(self.r_m_qty.get()) if self.r_m_qty.get().strip() else 0.0
        except: m_qty = 0.0
        try: e_qty = float(self.r_e_qty.get()) if self.r_e_qty.get().strip() else 0.0
        except: e_qty = 0.0
        try: m_fat = float(self.r_m_fat.get()) if self.r_m_fat.get().strip() else 0.0
        except: m_fat = 0.0
        try: e_fat = float(self.r_e_fat.get()) if self.r_e_fat.get().strip() else 0.0
        except: e_fat = 0.0

        if m_qty <= 0 and e_qty <= 0:
            messagebox.showerror("Error","Enter at least morning or evening quantity."); return

        from_d = self.r_from_var.get().strip()
        to_d   = self.r_to_var.get().strip()
        try: dates = config.date_range(from_d,to_d)
        except: messagebox.showerror("Error","Invalid dates."); return

        entries = config.load("sup_entries")
        existing = {(e["sup_id"],e["date"],e["session"]) for e in entries}
        added = 0

        for d in dates:
            sessions = []
            if m_qty > 0: sessions.append(("Morning",m_qty,m_fat))
            if e_qty > 0: sessions.append(("Evening",e_qty,e_fat))
            for sess, qty, fat in sessions:
                if self.r_skip_existing.get() and (sup["id"],d,sess) in existing:
                    continue
                if "Full" in mode:
                    r = config.calc_full(qty,fat,0,fatrate)
                    entry = {"qty":qty,"fat":fat,"meter":0,"fatrate":fatrate,"SNF":r["SNF"]}
                elif "Direct" in mode:
                    r = config.calc_direct(qty,fat,fatrate)
                    entry = {"qty":qty,"fat":fat,"fatrate":fatrate,"SNF":None}
                else:
                    r = config.calc_fixed(qty,fatrate)
                    entry = {"qty":qty,"rate":fatrate,"SNF":None}
                entries.append({
                    "id":config.next_id(entries),
                    "sup_id":sup["id"],
                    "date":d,"session":sess,"mode":mode,
                    "amount":r["amount"],**entry
                })
                added += 1

        config.save("sup_entries",entries)
        msg = f"Done: {added} supplier entries added"
        self.r_result_lbl.configure(text=msg)
        self.app.set_status(msg)
        self.app.update_badge()
        self._refresh_today()

    def _refresh_today(self):
        self.today_tbl.clear()
        today   = date.today().isoformat()
        entries = config.load("sup_entries")
        sups    = config.load("suppliers")
        sup_map = {s["id"]:s["name"] for s in sups}
        found   = False
        for e in reversed(entries):
            if e["date"]!=today: continue
            found = True
            self.today_tbl.add_row([
                sup_map.get(e["sup_id"],"?"),
                e["date"], e["session"],
                e.get("qty",""),
                e.get("fat","") or "—",
                e.get("meter","") or "—",
                e.get("SNF","") or "—",
                e.get("mode","")[:10],
                f"₹{e['amount']:,.2f}"
            ])
        if not found:
            self.today_tbl.empty_state("No supplier entries today.")
