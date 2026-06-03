import customtkinter as ctk
from widgets import Table, make_label, make_entry, make_btn, make_combo, make_card, section_title
from theme import get as T
import config
from tkinter import messagebox

class ProductsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.editing_id = None

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Products & Rates")

        card = make_card(self)
        card.pack(fill="x",padx=20,pady=(0,10))
        form = ctk.CTkFrame(card,fg_color="transparent")
        form.pack(padx=16,pady=14,fill="x")

        make_label(form,"Product Name",size=12,color=t["text2"]).grid(row=0,column=0,sticky="w",padx=(0,8),pady=6)
        self.name_e = make_entry(form,"e.g. Milk",width=180)
        self.name_e.grid(row=0,column=1,pady=6,padx=(0,20))

        make_label(form,"Unit",size=12,color=t["text2"]).grid(row=0,column=2,sticky="w",padx=(0,8))
        self.unit_c = make_combo(form,["L","kg","pcs","g"],width=100)
        self.unit_c.grid(row=0,column=3,pady=6,padx=(0,20))

        make_label(form,"Rate (₹)",size=12,color=t["text2"]).grid(row=0,column=4,sticky="w",padx=(0,8))
        self.rate_e = make_entry(form,"0.00",width=120)
        self.rate_e.grid(row=0,column=5,pady=6,padx=(0,20))

        btn_row = ctk.CTkFrame(card,fg_color="transparent")
        btn_row.pack(padx=16,pady=(0,14),anchor="w")
        self.save_btn = make_btn(btn_row,"Add Product",self._save,width=140)
        self.save_btn.pack(side="left",padx=(0,8))
        self.toggle_btn = make_btn(btn_row,"Disable",self._toggle,style="ghost",width=100)
        self.toggle_btn.pack(side="left",padx=(0,8))
        self.toggle_btn.configure(state="disabled")
        make_btn(btn_row,"Clear",self._clear,style="ghost",width=80).pack(side="left")

        tcard = make_card(self)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))
        self.table = Table(tcard,
            ["ID","Product","Unit","Rate (₹)","Status"],
            [60,180,80,120,100], height=320,
            on_select=self._select)
        self.table.pack(fill="both",expand=True,padx=8,pady=8)
        self._refresh_table()

    def _refresh_table(self):
        self.table.clear()
        products = config.load("products")
        for p in products:
            status = "Active" if p.get("active",True) else "Disabled"
            self.table.add_row([p["id"],p["name"],p["unit"],f"₹{p['rate']:.2f}",status],tag=p["id"])

    def _select(self, pid):
        products = config.load("products")
        p = next((x for x in products if x["id"]==pid),None)
        if not p: return
        self.editing_id = pid
        self.name_e.delete(0,"end"); self.name_e.insert(0,p["name"])
        self.unit_c.set(p["unit"])
        self.rate_e.delete(0,"end"); self.rate_e.insert(0,str(p["rate"]))
        self.save_btn.configure(text="Update Product")
        self.toggle_btn.configure(state="normal",
            text="Enable" if not p.get("active",True) else "Disable")

    def _save(self):
        name = self.name_e.get().strip()
        if not name: messagebox.showerror("Error","Name required."); return
        try: rate = float(self.rate_e.get())
        except: messagebox.showerror("Error","Enter valid rate."); return
        unit = self.unit_c.get()
        products = config.load("products")
        if self.editing_id:
            for p in products:
                if p["id"]==self.editing_id:
                    p.update({"name":name,"unit":unit,"rate":rate})
            self.app.set_status("Product updated.")
        else:
            products.append({"id":config.next_id(products),"name":name,
                              "unit":unit,"rate":rate,"active":True})
            self.app.set_status("Product added.")
        config.save("products",products)
        self._clear(); self._refresh_table()

    def _toggle(self):
        if not self.editing_id: return
        products = config.load("products")
        for p in products:
            if p["id"]==self.editing_id:
                p["active"] = not p.get("active",True)
        config.save("products",products)
        self._clear(); self._refresh_table()
        self.app.set_status("Product status changed.")

    def _clear(self):
        self.editing_id = None
        self.name_e.delete(0,"end"); self.rate_e.delete(0,"end")
        self.unit_c.set("L")
        self.save_btn.configure(text="Add Product")
        self.toggle_btn.configure(state="disabled")
