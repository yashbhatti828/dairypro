"""
Excel-style ledger — tight grid, no spacing, skip rows, delete payments.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from widgets import make_label, make_btn, make_combo, make_card, section_title, date_range_bar
from theme import get as T
import config
from datetime import date, datetime

SKIP_BG  = "#7f1d1d"
SKIP_FG  = "#fca5a5"
ENTRY_FG = "#86efac"

class LedgerPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app      = app
        self.cust_id  = None
        self.cell_vars= {}
        self.pay_vars = {}
        self.row_data = {}  # date -> {frame, is_skip, bg}

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Customer Ledger")

        # Controls
        ctrl = make_card(self)
        ctrl.pack(fill="x",padx=20,pady=(0,8))
        top = ctk.CTkFrame(ctrl,fg_color="transparent")
        top.pack(padx=16,pady=10,fill="x")

        make_label(top,"Customer",size=12,color=t["text2"]).pack(side="left",padx=(0,6))
        customers = config.load("customers")
        names = [c["name"] for c in customers if c.get("active",True)]
        self.cust_c = make_combo(top,names if names else ["No customers"],width=200)
        self.cust_c.pack(side="left",padx=(0,16))

        # Date range bar
        rbar, self.from_var, self.to_var = date_range_bar(top, lambda: None)
        rbar.pack(side="left",padx=(0,12))
        make_btn(top,"Load",self._load,width=80).pack(side="left")

        # Legend
        leg = ctk.CTkFrame(ctrl,fg_color="transparent")
        leg.pack(padx=16,pady=(0,10),anchor="w")
        for color,lbl in [(t["warning"],"Skipped"),(ENTRY_FG,"Has entry"),(t["text3"],"Empty")]:
            tk.Label(leg,text="■",bg=t["card"],fg=color,font=("Segoe UI",12)).pack(side="left",padx=(0,2))
            make_label(leg,lbl,size=11,color=t["text2"]).pack(side="left",padx=(0,12))

        # Grid container
        self.grid_outer = ctk.CTkFrame(self,fg_color=t["card"],
                                        border_color=t["border"],border_width=1,corner_radius=10)
        self.grid_outer.pack(fill="both",expand=True,padx=20,pady=(0,16))

        canvas = tk.Canvas(self.grid_outer,bg=t["card"],highlightthickness=0)
        h_sb = tk.Scrollbar(self.grid_outer,orient="horizontal",command=canvas.xview)
        v_sb = tk.Scrollbar(self.grid_outer,orient="vertical",command=canvas.yview)
        canvas.configure(xscrollcommand=h_sb.set,yscrollcommand=v_sb.set)
        h_sb.pack(side="bottom",fill="x")
        v_sb.pack(side="right",fill="y")
        canvas.pack(fill="both",expand=True)
        self.grid_frame = tk.Frame(canvas,bg=t["card"])
        cw = canvas.create_window((0,0),window=self.grid_frame,anchor="nw")
        self.grid_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e: canvas.itemconfig(cw,width=e.width))
        canvas.bind("<MouseWheel>",lambda e: canvas.yview_scroll(-1 if e.delta>0 else 1,"units"))
        self.canvas = canvas

        make_label(self.grid_frame,"← Select a customer and click Load",
                   size=12,color=t["text3"]).pack(padx=20,pady=30)

        if self.cust_id is not None:
            customers_data = config.load("customers")
            c = next((x for x in customers_data if x["id"]==self.cust_id),None)
            if c: self.cust_c.set(c["name"]); self._load()

    def _load(self):
        t = T()
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.cell_vars={}; self.pay_vars={}; self.row_data={}

        cust_name = self.cust_c.get().strip()
        customers = config.load("customers")
        cust = next((c for c in customers if c["name"]==cust_name),None)
        if not cust: return
        self.cust_id = cust["id"]

        from_d = self.from_var.get().strip()
        to_d   = self.to_var.get().strip()
        try: dates = config.date_range(from_d,to_d)
        except: messagebox.showerror("Error","Invalid dates."); return

        products = config.load("products")
        self.active_prods = [p for p in products if p["active"]]
        entries  = config.load("entries")
        payments = config.load("payments")
        skips    = config.load("skips")

        entry_map = {e["date"]:e for e in entries if e["cust_id"]==self.cust_id}
        pay_map   = {}
        for p in payments:
            if p["cust_id"]==self.cust_id:
                pay_map.setdefault(p["date"],[]).append(p)
        skip_set  = {s["date"] for s in skips
                     if s.get("cust_id")==self.cust_id and s.get("type","customer")=="customer"}

        # ── TIGHT Excel header ────────────────────────────────────────────────
        CELL_W = 7   # char width per cell
        COL_DATE = 9
        COL_SKIP = 3
        COL_PROD = 7
        COL_PAY  = 11
        COL_TOT  = 9
        COL_DEL  = 4

        hdr = tk.Frame(self.grid_frame, bg=t["header_bg"])
        hdr.pack(fill="x")
        for txt,w in ([("Date",COL_DATE),("Sk",COL_SKIP)] +
                      [(p["name"][:6],COL_PROD) for p in self.active_prods] +
                      [("Payment ₹",COL_PAY),("Total ₹",COL_TOT),("Del",COL_DEL)]):
            tk.Label(hdr,text=txt,width=w,bg=t["header_bg"],fg=t["text2"],
                     font=("Courier New",9,"bold"),anchor="w",padx=2,
                     relief="flat",bd=0).pack(side="left")

        # ── Data rows ─────────────────────────────────────────────────────────
        for i,d in enumerate(dates):
            is_skip   = d in skip_set
            has_entry = d in entry_map
            bg  = SKIP_BG if is_skip else (t["row_even"] if i%2==0 else t["row_odd"])
            cfg = SKIP_FG if is_skip else (ENTRY_FG if has_entry else t["text"])

            row = tk.Frame(self.grid_frame,bg=bg)
            row.pack(fill="x",pady=0)
            self.row_data[d] = {"frame":row,"is_skip":is_skip,"bg":bg}

            # Date
            dt_str = datetime.strptime(d,"%Y-%m-%d").strftime("%b %d")
            tk.Label(row,text=dt_str,width=COL_DATE,bg=bg,fg=cfg,
                     font=("Courier New",9,"bold"),anchor="w",padx=2,bd=0,relief="flat").pack(side="left")

            # Skip toggle
            skip_txt = "✓" if is_skip else "·"
            sk_btn = tk.Button(row,text=skip_txt,width=COL_SKIP,
                               bg=SKIP_BG if is_skip else bg,
                               fg=SKIP_FG if is_skip else t["text3"],
                               relief="flat",bd=0,cursor="hand2",
                               font=("Courier New",9),highlightthickness=0,
                               command=lambda dd=d,r=row: self._toggle_skip(dd,r))
            sk_btn.pack(side="left")

            # Product cells
            e_data = entry_map.get(d)
            for p in self.active_prods:
                qty = e_data["items"].get(str(p["id"]),0) if e_data else 0
                var = tk.StringVar(value=str(qty) if qty else "")
                self.cell_vars[(d,p["id"])] = var
                cell = tk.Entry(row,textvariable=var,width=COL_PROD,
                                bg=bg,fg=cfg,
                                insertbackground=t["text"],
                                relief="flat",bd=1,
                                font=("Courier New",9),
                                highlightthickness=1,
                                highlightbackground=t["border"],
                                highlightcolor=t["btn"],
                                state="disabled" if is_skip else "normal",
                                disabledbackground=SKIP_BG,disabledforeground=SKIP_FG)
                cell.pack(side="left",padx=0,pady=1)
                cell.bind("<FocusOut>",lambda ev,dd=d: self._autosave(dd))
                cell.bind("<Return>",  lambda ev,dd=d: self._autosave(dd))
                cell.bind("<Tab>",     lambda ev,dd=d: self._autosave(dd))

            # Payment cell + delete button
            pmt_total = sum(p["amount"] for p in pay_map.get(d,[]))
            pmt_var   = tk.StringVar(value=str(int(pmt_total)) if pmt_total else "")
            self.pay_vars[d] = pmt_var
            pmt_cell = tk.Entry(row,textvariable=pmt_var,width=COL_PAY,
                                bg=bg,fg="#fbbf24",
                                insertbackground=t["text"],
                                relief="flat",bd=1,
                                font=("Courier New",9,"bold"),
                                highlightthickness=1,
                                highlightbackground=t["border"],
                                highlightcolor=t["btn"],
                                state="disabled" if is_skip else "normal",
                                disabledbackground=SKIP_BG)
            pmt_cell.pack(side="left",padx=0,pady=1)
            pmt_cell.bind("<FocusOut>",lambda ev,dd=d: self._autosave_pay(dd))
            pmt_cell.bind("<Return>",  lambda ev,dd=d: self._autosave_pay(dd))

            # Total
            total = e_data.get("total",0) if e_data else 0
            tot_var = tk.StringVar(value=f"{total:,.0f}" if total else "")
            tot_lbl = tk.Label(row,textvariable=tot_var,width=COL_TOT,bg=bg,fg=cfg,
                                font=("Courier New",9),anchor="e",padx=2,bd=0,relief="flat")
            tot_lbl.pack(side="left")
            self.row_data[d]["tot_var"] = tot_var

            # Delete payment button
            del_btn = tk.Button(row,text="✕",width=COL_DEL,
                                bg=bg,fg=t["danger"],relief="flat",bd=0,
                                font=("Courier New",9),highlightthickness=0,
                                cursor="hand2",
                                command=lambda dd=d: self._delete_payment(dd))
            del_btn.pack(side="left")

    def _autosave(self,d):
        products = config.load("products")
        prod_map = {p["id"]:p for p in products}
        entries  = config.load("entries")
        items,total,has = {},0.0,False
        for p in self.active_prods:
            val = self.cell_vars.get((d,p["id"]),tk.StringVar()).get().strip()
            try: qty = float(val) if val else 0.0
            except: qty=0.0
            if qty>0:
                items[str(p["id"])]=qty; total+=qty*prod_map[p["id"]]["rate"]; has=True
        existing = next((e for e in entries if e["cust_id"]==self.cust_id and e["date"]==d),None)
        if has:
            if existing: existing["items"]=items; existing["total"]=round(total,2)
            else: entries.append({"id":config.next_id(entries),"cust_id":self.cust_id,
                                   "date":d,"session":"Full Day","items":items,"total":round(total,2)})
        else:
            entries=[e for e in entries if not (e["cust_id"]==self.cust_id and e["date"]==d)]
        config.save("entries",entries)
        if d in self.row_data and "tot_var" in self.row_data[d]:
            self.row_data[d]["tot_var"].set(f"{total:,.0f}" if has else "")
        self.app.set_status(f"Saved {d} — ₹{total:,.2f}" if has else f"Cleared {d}")

    def _autosave_pay(self,d):
        val = self.pay_vars.get(d,tk.StringVar()).get().strip()
        try: amt = float(val) if val else 0.0
        except: amt=0.0
        if amt<=0: return
        payments = config.load("payments")
        payments=[p for p in payments if not (p["cust_id"]==self.cust_id
                  and p["date"]==d and p.get("from_ledger"))]
        payments.append({"id":config.next_id(payments),"cust_id":self.cust_id,
                          "date":d,"amount":amt,"note":"Ledger","from_ledger":True})
        config.save("payments",payments)
        self.app.set_status(f"Payment ₹{amt:,.0f} saved for {d}")

    def _delete_payment(self,d):
        payments = config.load("payments")
        day_pmts = [p for p in payments if p["cust_id"]==self.cust_id and p["date"]==d]
        if not day_pmts: return
        if not messagebox.askyesno("Delete Payment",
            f"Delete payment(s) for {d}?\n"+"\n".join(f"₹{p['amount']:,.0f} — {p.get('note','')}" for p in day_pmts)):
            return
        payments=[p for p in payments if not (p["cust_id"]==self.cust_id and p["date"]==d)]
        config.save("payments",payments)
        if d in self.pay_vars: self.pay_vars[d].set("")
        self.app.set_status(f"Payment deleted for {d}")

    def _toggle_skip(self,d,row_frame):
        t     = T()
        skips = config.load("skips")
        existing = next((s for s in skips if s.get("cust_id")==self.cust_id
                         and s["date"]==d and s.get("type","customer")=="customer"),None)
        if existing:
            skips=[s for s in skips if not (s.get("cust_id")==self.cust_id
                   and s["date"]==d and s.get("type","customer")=="customer")]
            new_bg = self.row_data[d]["bg"]
        else:
            skips.append({"id":config.next_id(skips),"cust_id":self.cust_id,
                           "date":d,"type":"customer"})
            new_bg = SKIP_BG
        config.save("skips",skips)
        row_frame.configure(bg=new_bg)
        for child in row_frame.winfo_children():
            try: child.configure(bg=new_bg)
            except: pass
        self.app.update_badge()
