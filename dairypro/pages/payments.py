import customtkinter as ctk
import tkinter as tk
from widgets import Table, make_label, make_entry, make_btn, make_combo, make_card, section_title
from theme import get as T
import config
from tkinter import messagebox
from datetime import date

class PaymentsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Payments")

        card = make_card(self)
        card.pack(fill="x",padx=20,pady=(0,10))
        form = ctk.CTkFrame(card,fg_color="transparent")
        form.pack(padx=16,pady=14,fill="x")

        make_label(form,"Customer",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=6)
        customers = config.load("customers")
        names = [c["name"] for c in customers if c.get("active",True)]
        self.cust_c = make_combo(form,names if names else ["No customers"],width=220,
                                  command=self._update_pending)
        self.cust_c.grid(row=0,column=1,pady=6,padx=(0,24))

        make_label(form,"Date",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.date_e = make_entry(form,"YYYY-MM-DD",width=150)
        self.date_e.insert(0,date.today().isoformat())
        self.date_e.grid(row=0,column=3,pady=6,padx=(0,24))

        make_label(form,"Amount (₹)",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.amt_e = make_entry(form,"0.00",width=140)
        self.amt_e.grid(row=0,column=5,pady=6)

        make_label(form,"Note",size=12,color=t["text2"]).grid(row=1,column=0,sticky="w",padx=(0,8),pady=6)
        self.note_e = make_entry(form,"e.g. Cash, Raju, UPI",width=300)
        self.note_e.grid(row=1,column=1,columnspan=3,pady=6,padx=(0,24),sticky="ew")

        self.pending_lbl = make_label(form,"Pending: —",size=12,color=t["warning"])
        self.pending_lbl.grid(row=1,column=4,columnspan=2,sticky="w",padx=(0,8))

        make_btn(card,"Record Payment",self._save,width=160).pack(anchor="w",padx=16,pady=(0,14))

        # Payment history
        make_label(self,"Payment History",size=14,bold=True).pack(anchor="w",padx=20,pady=(4,4))
        tcard = make_card(self)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        self.table = Table(tcard,
            ["Date","Customer","Amount","Note"],
            [130,200,150,280], height=300, on_select=None)
        self.table.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_table()
        self._update_pending(None)

    def _update_pending(self, val):
        try:
            cust_name = self.cust_c.get()
            customers = config.load("customers")
            cust = next((c for c in customers if c["name"]==cust_name),None)
            if not cust: return
            entries  = config.load("entries")
            payments = config.load("payments")
            supply  = sum(e.get("total",0) for e in entries  if e["cust_id"]==cust["id"])
            paid    = sum(p["amount"] for p in payments if p["cust_id"]==cust["id"])
            opening = cust.get("opening_balance",0)
            pending = opening + supply - paid
            self.pending_lbl.configure(text=f"Pending: ₹{pending:,.2f}")
        except: pass

    def _save(self):
        cust_name = self.cust_c.get().strip()
        if not cust_name or cust_name=="No customers":
            messagebox.showerror("Error","Select a customer."); return
        customers = config.load("customers")
        cust = next((c for c in customers if c["name"]==cust_name),None)
        if not cust: return
        date_str = self.date_e.get().strip()
        try: amt = float(self.amt_e.get())
        except: messagebox.showerror("Error","Enter valid amount."); return
        if amt <= 0: messagebox.showerror("Error","Amount must be > 0."); return
        note = self.note_e.get().strip()
        payments = config.load("payments")
        payments.append({"id":config.next_id(payments),"cust_id":cust["id"],
                          "date":date_str,"amount":amt,"note":note})
        config.save("payments",payments)
        self.amt_e.delete(0,"end")
        self.note_e.delete(0,"end")
        self.app.set_status(f"Payment of ₹{amt:,.2f} recorded.")
        self._refresh_table()
        self._update_pending(None)

    def _refresh_table(self):
        self.table.clear()
        payments  = config.load("payments")
        customers = config.load("customers")
        cust_map  = {c["id"]:c["name"] for c in customers}
        for p in reversed(payments):
            self.table.add_row([p["date"],cust_map.get(p["cust_id"],"?"),
                                 f"₹{p['amount']:,.2f}",p.get("note","")])
        if not payments:
            self.table.empty_state("No payments recorded yet.")
