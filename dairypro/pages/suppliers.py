import customtkinter as ctk
from tkinter import messagebox
from widgets import Table, make_label, make_entry, make_btn, make_combo, make_card, section_title
from theme import get as T
import config

class SuppliersPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.editing_id = None

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Suppliers")

        card = make_card(self)
        card.pack(fill="x",padx=20,pady=(0,12))
        form = ctk.CTkFrame(card,fg_color="transparent")
        form.pack(padx=16,pady=14,fill="x")

        make_label(form,"Name",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=4)
        self.name_e = make_entry(form,"Supplier name",width=200)
        self.name_e.grid(row=0,column=1,pady=4,padx=(0,20))

        make_label(form,"Phone",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.phone_e = make_entry(form,"Phone",width=160)
        self.phone_e.grid(row=0,column=3,pady=4,padx=(0,20))

        make_label(form,"Village",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.village_e = make_entry(form,"Village/Area",width=160)
        self.village_e.grid(row=0,column=5,pady=4)

        make_label(form,"Default Mode",size=12,color=t["text2"]).grid(row=1,column=0,sticky="w",padx=(0,8),pady=4)
        from pages.supplier_entry import MODES
        self.mode_c = make_combo(form,MODES,width=200)
        self.mode_c.grid(row=1,column=1,pady=4,padx=(0,20))

        make_label(form,"Opening Balance (₹)",size=12,color=t["text2"]).grid(row=1,column=2,sticky="w",padx=(0,8))
        self.bal_e = make_entry(form,"0.00",width=140)
        self.bal_e.grid(row=1,column=3,pady=4,padx=(0,20))

        btn_row = ctk.CTkFrame(card,fg_color="transparent")
        btn_row.pack(padx=16,pady=(0,12),anchor="w")
        self.save_btn = make_btn(btn_row,"Add Supplier",self._save,width=150)
        self.save_btn.pack(side="left",padx=(0,8))
        self.del_btn  = make_btn(btn_row,"Delete",self._delete,style="danger",width=100)
        self.del_btn.pack(side="left",padx=(0,8))
        self.del_btn.configure(state="disabled")
        make_btn(btn_row,"Clear",self._clear,style="ghost",width=80).pack(side="left")

        if self.editing_id: self._load_edit(self.editing_id)

        make_label(self,"Supplier List",size=14,bold=True).pack(anchor="w",padx=20,pady=(4,4))
        tcard = make_card(self)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        self.table = Table(tcard,
            ["ID","Name","Phone","Village","Mode","Opening","Total Supplied","Pending"],
            [40,160,120,140,150,100,120,110], height=300,
            on_select=self._select)
        self.table.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_table()

    def _refresh_table(self):
        self.table.clear()
        suppliers = config.load("suppliers")
        sup_entries = config.load("sup_entries")
        for s in suppliers:
            if not s.get("active",True): continue
            total = sum(e["amount"] for e in sup_entries if e["sup_id"]==s["id"])
            opening = s.get("opening_balance",0)
            self.table.add_row([
                s["id"],s["name"],s.get("phone",""),s.get("village",""),
                s.get("calc_mode","")[:14] if s.get("calc_mode") else "—",
                f"₹{opening:,.0f}",f"₹{total:,.0f}",
                f"₹{opening+total:,.0f}"
            ],tag=s["id"])

    def _select(self,sid):
        self.editing_id=sid; self._load_edit(sid)

    def _load_edit(self,sid):
        suppliers = config.load("suppliers")
        s = next((x for x in suppliers if x["id"]==sid),None)
        if not s: return
        self.name_e.delete(0,"end"); self.name_e.insert(0,s["name"])
        self.phone_e.delete(0,"end"); self.phone_e.insert(0,s.get("phone",""))
        self.village_e.delete(0,"end"); self.village_e.insert(0,s.get("village",""))
        if s.get("calc_mode"): self.mode_c.set(s["calc_mode"])
        self.bal_e.delete(0,"end"); self.bal_e.insert(0,str(s.get("opening_balance",0)))
        self.save_btn.configure(text="Update Supplier")
        self.del_btn.configure(state="normal")

    def _save(self):
        name = self.name_e.get().strip()
        if not name: messagebox.showerror("Error","Name required."); return
        try: opening = float(self.bal_e.get()) if self.bal_e.get().strip() else 0.0
        except: opening = 0.0
        suppliers = config.load("suppliers")
        if self.editing_id:
            for s in suppliers:
                if s["id"]==self.editing_id:
                    s.update({"name":name,"phone":self.phone_e.get().strip(),
                               "village":self.village_e.get().strip(),
                               "calc_mode":self.mode_c.get(),
                               "opening_balance":opening})
            self.app.set_status("Supplier updated.")
        else:
            suppliers.append({"id":config.next_id(suppliers),"name":name,
                               "phone":self.phone_e.get().strip(),
                               "village":self.village_e.get().strip(),
                               "calc_mode":self.mode_c.get(),
                               "opening_balance":opening,"active":True})
            self.app.set_status("Supplier added.")
        config.save("suppliers",suppliers)
        self._clear(); self._refresh_table()

    def _delete(self):
        if not self.editing_id: return
        if not messagebox.askyesno("Confirm","Delete supplier?"): return
        suppliers = config.load("suppliers")
        for s in suppliers:
            if s["id"]==self.editing_id: s["active"]=False
        config.save("suppliers",suppliers)
        self._clear(); self._refresh_table()
        self.app.set_status("Supplier deleted.")

    def _clear(self):
        self.editing_id=None
        for e in [self.name_e,self.phone_e,self.village_e,self.bal_e]: e.delete(0,"end")
        self.save_btn.configure(text="Add Supplier")
        self.del_btn.configure(state="disabled")
