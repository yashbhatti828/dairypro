import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from widgets import Table, make_label, make_entry, make_btn, make_combo, make_card, section_title, date_range_bar
from theme import get as T
import config
from datetime import date, datetime, timedelta

class EntryPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Customer Daily Entry")

        tab_row = ctk.CTkFrame(self,fg_color="transparent")
        tab_row.pack(fill="x",padx=20,pady=(0,8))
        self.mode = tk.StringVar(value="single")
        for label,val in [("Single Entry","single"),("Recurring (Fill Date Range)","recurring")]:
            ctk.CTkRadioButton(tab_row,text=label,variable=self.mode,value=val,
                               command=self._switch_mode,
                               text_color=t["text"],fg_color=t["btn"],
                               border_color=t["border"]).pack(side="left",padx=(0,20))

        self.single_frame    = ctk.CTkFrame(self,fg_color="transparent")
        self.recurring_frame = ctk.CTkFrame(self,fg_color="transparent")
        self._build_single()
        self._build_recurring()
        self._switch_mode()

    def _switch_mode(self):
        if self.mode.get()=="single":
            self.recurring_frame.pack_forget()
            self.single_frame.pack(fill="both",expand=True)
        else:
            self.single_frame.pack_forget()
            self.recurring_frame.pack(fill="both",expand=True)

    def _build_single(self):
        t = T()
        card = make_card(self.single_frame)
        card.pack(fill="x",padx=20,pady=(0,10))
        form = ctk.CTkFrame(card,fg_color="transparent")
        form.pack(padx=16,pady=14,fill="x")

        make_label(form,"Customer",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=6)
        customers = config.load("customers")
        names = [c["name"] for c in customers if c.get("active",True)]
        self.cust_c = make_combo(form,names if names else ["No customers"],width=220)
        self.cust_c.grid(row=0,column=1,pady=6,padx=(0,24))

        make_label(form,"Date",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.date_e = make_entry(form,"YYYY-MM-DD",width=150)
        self.date_e.insert(0,date.today().isoformat())
        self.date_e.grid(row=0,column=3,pady=6,padx=(0,24))

        make_label(form,"Session",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.session_c = make_combo(form,["Morning","Evening","Full Day"],width=130)
        self.session_c.grid(row=0,column=5,pady=6)

        products = config.load("products")
        self.active_prods = [p for p in products if p["active"]]
        self.qty_entries  = {}
        prod_frame = ctk.CTkFrame(card,fg_color="transparent")
        prod_frame.pack(padx=16,pady=(0,4),fill="x")
        for p in self.active_prods:
            box = ctk.CTkFrame(prod_frame,fg_color=t["card2"],
                               corner_radius=8,border_width=1,border_color=t["border"])
            box.pack(side="left",padx=(0,10),pady=4,ipadx=8,ipady=4)
            make_label(box,p["name"],size=12,bold=True).pack(pady=(6,0))
            make_label(box,f"₹{p['rate']}/{p['unit']}",size=10,color=t["text2"]).pack()
            e = make_entry(box,"0",width=90)
            e.pack(pady=(4,8))
            e.bind("<KeyRelease>",lambda ev: self._preview())
            self.qty_entries[p["id"]] = e

        self.preview_lbl = make_label(card,"Enter quantities to preview total",size=12,color=t["text2"])
        self.preview_lbl.pack(anchor="w",padx=16,pady=(0,4))
        make_btn(card,"Save Entry",self._save_single,width=150).pack(anchor="w",padx=16,pady=(0,14))

        make_label(self.single_frame,"Today's Entries",size=14,bold=True).pack(anchor="w",padx=20,pady=(8,4))
        tcard = make_card(self.single_frame)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        prod_names = [p["name"] for p in self.active_prods]
        self.today_table = Table(tcard,
            ["Customer","Date","Session"]+prod_names+["Total"],
            [160,110,100]+[80]*len(prod_names)+[110],height=200)
        self.today_table.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_today()

    def _preview(self):
        try:
            total,parts = 0.0,[]
            for p in self.active_prods:
                val = self.qty_entries[p["id"]].get().strip()
                qty = float(val) if val else 0.0
                if qty:
                    amt = qty*p["rate"]; total+=amt
                    parts.append(f"{p['name']}: {qty}×₹{p['rate']}=₹{amt:,.2f}")
            self.preview_lbl.configure(
                text=("  |  ".join(parts)+f"   →   ₹{total:,.2f}") if parts
                else "Enter quantities to preview total")
        except: pass

    def _save_single(self):
        cust_name = self.cust_c.get().strip()
        if not cust_name or cust_name=="No customers":
            messagebox.showerror("Error","Select a customer."); return
        customers = config.load("customers")
        cust = next((c for c in customers if c["name"]==cust_name and c.get("active",True)),None)
        if not cust: return
        date_str = self.date_e.get().strip()
        try: datetime.strptime(date_str,"%Y-%m-%d")
        except: messagebox.showerror("Error","Date must be YYYY-MM-DD."); return
        items,total,has_qty = {},0.0,False
        products = config.load("products")
        prod_map = {p["id"]:p for p in products}
        for pid,e in self.qty_entries.items():
            val = e.get().strip()
            try: qty = float(val) if val else 0.0
            except: qty = 0.0
            if qty>0:
                items[str(pid)]=qty; total+=qty*prod_map[pid]["rate"]; has_qty=True
        if not has_qty: messagebox.showerror("Error","Enter at least one quantity."); return
        entries = config.load("entries")
        entries.append({"id":config.next_id(entries),"cust_id":cust["id"],
                         "date":date_str,"session":self.session_c.get(),
                         "items":items,"total":round(total,2)})
        config.save("entries",entries)
        for e in self.qty_entries.values(): e.delete(0,"end")
        self.preview_lbl.configure(text=f"Saved — ₹{total:,.2f}")
        self.app.set_status(f"Entry saved — ₹{total:,.2f}")
        self.app.update_badge(); self._refresh_today()

    def _refresh_today(self):
        self.today_table.clear()
        today = date.today().isoformat()
        entries = config.load("entries"); customers = config.load("customers")
        cust_map = {c["id"]:c["name"] for c in customers}
        found = False
        for e in reversed(entries):
            if e["date"]!=today: continue
            found=True
            row=[cust_map.get(e["cust_id"],"?"),e["date"],e["session"]]
            for p in self.active_prods:
                qty=e.get("items",{}).get(str(p["id"]),0)
                row.append(str(qty) if qty else "-")
            row.append(f"₹{e.get('total',0):,.2f}")
            self.today_table.add_row(row)
        if not found: self.today_table.empty_state("No entries for today yet.")

    def _build_recurring(self):
        t = T()
        card = make_card(self.recurring_frame)
        card.pack(fill="x",padx=20,pady=(0,10))
        make_label(card,"Recurring Entry — Fill date range for Morning + Evening separately",
                   size=13,bold=True).pack(anchor="w",padx=16,pady=(12,4))

        form = ctk.CTkFrame(card,fg_color="transparent")
        form.pack(padx=16,pady=(0,8),fill="x")

        make_label(form,"Customer",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=6)
        customers = config.load("customers")
        names = [c["name"] for c in customers if c.get("active",True)]
        self.r_cust_c = make_combo(form,names if names else ["No customers"],width=200)
        self.r_cust_c.grid(row=0,column=1,pady=6,padx=(0,20))

        make_label(form,"Session",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.r_session_c = make_combo(form,["Both","Morning Only","Evening Only"],width=160)
        self.r_session_c.grid(row=0,column=3,pady=6,padx=(0,20))

        # Products per session
        products = config.load("products")
        self.r_active_prods = [p for p in products if p["active"]]

        # Morning row
        m_frame = ctk.CTkFrame(card,fg_color=t["card2"],corner_radius=8)
        m_frame.pack(fill="x",padx=16,pady=(0,6))
        make_label(m_frame,"🌅 Morning quantities:",size=12,bold=True).pack(anchor="w",padx=10,pady=(8,4))
        m_prod_row = ctk.CTkFrame(m_frame,fg_color="transparent")
        m_prod_row.pack(padx=10,pady=(0,8),fill="x")
        self.r_m_entries = {}
        for p in self.r_active_prods:
            box = ctk.CTkFrame(m_prod_row,fg_color=t["card"],corner_radius=6,border_width=1,border_color=t["border"])
            box.pack(side="left",padx=(0,8),ipadx=6,ipady=2)
            make_label(box,p["name"],size=11,bold=True).pack(pady=(4,0))
            e = make_entry(box,"0",width=80)
            e.pack(pady=(2,6))
            self.r_m_entries[p["id"]] = e

        # Evening row
        e_frame = ctk.CTkFrame(card,fg_color=t["card2"],corner_radius=8)
        e_frame.pack(fill="x",padx=16,pady=(0,8))
        make_label(e_frame,"🌙 Evening quantities:",size=12,bold=True).pack(anchor="w",padx=10,pady=(8,4))
        e_prod_row = ctk.CTkFrame(e_frame,fg_color="transparent")
        e_prod_row.pack(padx=10,pady=(0,8),fill="x")
        self.r_e_entries = {}
        for p in self.r_active_prods:
            box = ctk.CTkFrame(e_prod_row,fg_color=t["card"],corner_radius=6,border_width=1,border_color=t["border"])
            box.pack(side="left",padx=(0,8),ipadx=6,ipady=2)
            make_label(box,p["name"],size=11,bold=True).pack(pady=(4,0))
            e = make_entry(box,"0",width=80)
            e.pack(pady=(2,6))
            self.r_e_entries[p["id"]] = e

        # Date range bar
        date_row = ctk.CTkFrame(card,fg_color="transparent")
        date_row.pack(padx=16,pady=(0,4),fill="x")
        rbar, self.r_from_var, self.r_to_var = date_range_bar(date_row, lambda: None)
        rbar.pack(fill="x")

        opt_row = ctk.CTkFrame(card,fg_color="transparent")
        opt_row.pack(padx=16,pady=(0,4),anchor="w")
        self.skip_existing = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_row,text="Skip days that already have an entry",
                         variable=self.skip_existing,
                         text_color=t["text"],fg_color=t["btn"],
                         border_color=t["border"]).pack(side="left")

        self.r_result_lbl = make_label(self.recurring_frame,"",size=12,color=t["success"])
        self.r_result_lbl.pack(anchor="w",padx=20,pady=4)
        make_btn(card,"Fill All Days in Range",self._save_recurring,width=200).pack(
            anchor="w",padx=16,pady=(4,14))

    def _save_recurring(self):
        cust_name = self.r_cust_c.get().strip()
        if not cust_name or cust_name=="No customers":
            messagebox.showerror("Error","Select a customer."); return
        customers = config.load("customers")
        cust = next((c for c in customers if c["name"]==cust_name),None)
        if not cust: return

        from_d = self.r_from_var.get().strip()
        to_d   = self.r_to_var.get().strip()
        try: dates = config.date_range(from_d,to_d)
        except: messagebox.showerror("Error","Invalid dates."); return

        session_mode = self.r_session_c.get()
        products = config.load("products")
        prod_map = {p["id"]:p for p in products}

        def get_items(entry_dict):
            items,total = {},0.0
            for pid,e in entry_dict.items():
                val = e.get().strip()
                try: qty = float(val) if val else 0.0
                except: qty=0.0
                if qty>0:
                    items[str(pid)]=qty; total+=qty*prod_map[pid]["rate"]
            return items,round(total,2)

        m_items,m_total = get_items(self.r_m_entries)
        e_items,e_total = get_items(self.r_e_entries)

        if not m_items and not e_items:
            messagebox.showerror("Error","Enter at least one quantity."); return

        entries = config.load("entries")
        existing= {(e["cust_id"],e["date"],e["session"]) for e in entries}
        added   = 0

        for d in dates:
            sessions = []
            if session_mode in ("Both","Morning Only") and m_items:
                sessions.append(("Morning",m_items,m_total))
            if session_mode in ("Both","Evening Only") and e_items:
                sessions.append(("Evening",e_items,e_total))
            for sess,items,total in sessions:
                if self.skip_existing.get() and (cust["id"],d,sess) in existing:
                    continue
                entries.append({"id":config.next_id(entries),"cust_id":cust["id"],
                                  "date":d,"session":sess,
                                  "items":dict(items),"total":total})
                added+=1

        config.save("entries",entries)
        msg = f"Done: {added} entries added ({from_d} → {to_d})"
        self.r_result_lbl.configure(text=msg)
        self.app.set_status(msg); self.app.update_badge()
