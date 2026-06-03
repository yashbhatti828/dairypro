import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from widgets import Table, make_label, make_entry, make_btn, make_combo, make_card, section_title
from theme import get as T
import config

class CustomersPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.editing_id = None

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Customers")

        card = make_card(self)
        card.pack(fill="x", padx=20, pady=(0,12))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=16, pady=14, fill="x")

        make_label(form,"Name",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=4)
        self.name_e = make_entry(form,"Full name",width=200)
        self.name_e.grid(row=0,column=1,pady=4,padx=(0,20))

        make_label(form,"Phone",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.phone_e = make_entry(form,"Phone",width=160)
        self.phone_e.grid(row=0,column=3,pady=4,padx=(0,20))

        make_label(form,"Type",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.type_c = make_combo(form,["Supplier","Buyer"],width=130)
        self.type_c.grid(row=0,column=5,pady=4,padx=(0,20))

        make_label(form,"Address",size=12,color=t["text2"]).grid(row=1,column=0,sticky="w",padx=(0,8),pady=4)
        self.addr_e = make_entry(form,"Village / Area",width=260)
        self.addr_e.grid(row=1,column=1,columnspan=3,pady=4,padx=(0,20),sticky="ew")

        make_label(form,"Opening Balance (₹)",size=12,color=t["text2"]).grid(row=1,column=4,sticky="w",padx=(0,8))
        self.bal_e = make_entry(form,"0.00",width=130)
        self.bal_e.grid(row=1,column=5,pady=4,padx=(0,20))

        make_label(form,"Expected Daily (qty)",size=12,color=t["text2"]).grid(row=2,column=0,sticky="w",padx=(0,8),pady=4)
        self.exp_e = make_entry(form,"e.g. 2 (0 = not tracked)",width=200)
        self.exp_e.grid(row=2,column=1,pady=4,padx=(0,20))

        make_label(form,"Expected Product",size=12,color=t["text2"]).grid(row=2,column=2,sticky="w",padx=(0,8))
        products = config.load("products")
        prod_names = [p["name"] for p in products if p["active"]]
        self.exp_prod_c = make_combo(form, prod_names if prod_names else ["Milk"], width=140)
        self.exp_prod_c.grid(row=2,column=3,pady=4,padx=(0,20))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(padx=16, pady=(0,12), anchor="w")
        self.save_btn = make_btn(btn_row,"Add Customer",self._save,width=150)
        self.save_btn.pack(side="left",padx=(0,8))
        self.del_btn  = make_btn(btn_row,"Delete",self._delete,style="danger",width=100)
        self.del_btn.pack(side="left",padx=(0,8))
        self.del_btn.configure(state="disabled")
        make_btn(btn_row,"Open Ledger",self._open_ledger,style="ghost",width=130).pack(side="left",padx=(0,8))
        make_btn(btn_row,"Clear",self._clear,style="ghost",width=80).pack(side="left")

        if self.editing_id:
            self._load_edit(self.editing_id)

        make_label(self,"Customer List",size=14,bold=True).pack(anchor="w",padx=20,pady=(4,4))
        tcard = make_card(self)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        self.table = Table(tcard,
            ["ID","Name","Phone","Type","Address","Exp.Qty","Opening","Supply","Paid","Pending"],
            [40,150,110,80,150,70,90,100,90,100], height=280,
            on_select=self._select)
        self.table.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_table()

    def _refresh_table(self):
        self.table.clear()
        customers = config.load("customers")
        entries   = config.load("entries")
        payments  = config.load("payments")
        for c in customers:
            if not c.get("active",True): continue
            supply  = sum(e.get("total",0) for e in entries if e["cust_id"]==c["id"])
            paid    = sum(p["amount"] for p in payments if p["cust_id"]==c["id"])
            opening = c.get("opening_balance",0)
            pending = opening + supply - paid
            exp     = c.get("expected_qty",0)
            self.table.add_row([
                c["id"],c["name"],c.get("phone",""),c["type"],
                c.get("address",""),
                str(exp) if exp else "—",
                f"₹{opening:,.0f}",f"₹{supply:,.0f}",
                f"₹{paid:,.0f}",f"₹{pending:,.0f}",
            ], tag=c["id"])

    def _select(self, cid):
        self.editing_id = cid
        self._load_edit(cid)

    def _load_edit(self, cid):
        customers = config.load("customers")
        c = next((x for x in customers if x["id"]==cid),None)
        if not c: return
        self.name_e.delete(0,"end");  self.name_e.insert(0,c["name"])
        self.phone_e.delete(0,"end"); self.phone_e.insert(0,c.get("phone",""))
        self.type_c.set(c["type"])
        self.addr_e.delete(0,"end");  self.addr_e.insert(0,c.get("address",""))
        self.bal_e.delete(0,"end");   self.bal_e.insert(0,str(c.get("opening_balance",0)))
        self.exp_e.delete(0,"end");   self.exp_e.insert(0,str(c.get("expected_qty",0)))
        if c.get("expected_product"): self.exp_prod_c.set(c.get("expected_product","Milk"))
        self.save_btn.configure(text="Update Customer")
        self.del_btn.configure(state="normal")

    def _save(self):
        name = self.name_e.get().strip()
        if not name: messagebox.showerror("Error","Name required."); return
        phone   = self.phone_e.get().strip()
        ctype   = self.type_c.get()
        addr    = self.addr_e.get().strip()
        try: opening = float(self.bal_e.get()) if self.bal_e.get().strip() else 0.0
        except: opening = 0.0
        try: exp_qty = float(self.exp_e.get()) if self.exp_e.get().strip() else 0.0
        except: exp_qty = 0.0
        exp_prod = self.exp_prod_c.get()

        customers = config.load("customers")
        if self.editing_id:
            for c in customers:
                if c["id"]==self.editing_id:
                    c.update({"name":name,"phone":phone,"type":ctype,"address":addr,
                               "opening_balance":opening,"expected_qty":exp_qty,
                               "expected_product":exp_prod})
            self.app.set_status("Customer updated.")
        else:
            customers.append({"id":config.next_id(customers),"name":name,"phone":phone,
                               "type":ctype,"address":addr,"opening_balance":opening,
                               "expected_qty":exp_qty,"expected_product":exp_prod,"active":True})
            self.app.set_status("Customer added.")
        config.save("customers",customers)
        self._clear(); self._refresh_table(); self.app.refresh_combos()
        self.app.update_badge()

    def _open_ledger(self):
        if not self.editing_id:
            messagebox.showinfo("Info","Select a customer first."); return
        customers = config.load("customers")
        c = next((x for x in customers if x["id"]==self.editing_id),None)
        if not c: return
        self.app.open_ledger(c["name"])

    def _delete(self):
        if not self.editing_id: return
        if not messagebox.askyesno("Confirm","Delete this customer?"): return
        customers = config.load("customers")
        for c in customers:
            if c["id"]==self.editing_id: c["active"]=False
        config.save("customers",customers)
        self._clear(); self._refresh_table(); self.app.refresh_combos()
        self.app.update_badge()
        self.app.set_status("Customer deleted.")

    def _clear(self):
        self.editing_id = None
        for e in [self.name_e,self.phone_e,self.addr_e,self.bal_e,self.exp_e]:
            e.delete(0,"end")
        self.type_c.set("Supplier")
        self.save_btn.configure(text="Add Customer")
        self.del_btn.configure(state="disabled")
