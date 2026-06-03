"""
Billing — PDF-style rendered view inside app + multi-customer PDF export.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from widgets import make_label, make_entry, make_btn, make_combo, make_card, section_title, date_range_bar, Table
from theme import get as T
import config, pdf_export
from datetime import date, datetime, timedelta
import os

class BillingPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._last_bill = None

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self,"Billing & Reports")

        # ── Tabs: Single | Multi ─────────────────────────────────────────────
        tab_row = ctk.CTkFrame(self,fg_color="transparent")
        tab_row.pack(fill="x",padx=20,pady=(0,8))
        self.mode = tk.StringVar(value="single")
        for lbl,val in [("Single Customer","single"),("Multi-Customer Export","multi")]:
            ctk.CTkRadioButton(tab_row,text=lbl,variable=self.mode,value=val,
                               command=self._switch_mode,
                               text_color=t["text"],fg_color=t["btn"],
                               border_color=t["border"]).pack(side="left",padx=(0,20))

        self.single_frame = ctk.CTkFrame(self,fg_color="transparent")
        self.multi_frame  = ctk.CTkFrame(self,fg_color="transparent")
        self._build_single()
        self._build_multi()
        self._switch_mode()

    def _switch_mode(self):
        if self.mode.get()=="single":
            self.multi_frame.pack_forget()
            self.single_frame.pack(fill="both",expand=True)
        else:
            self.single_frame.pack_forget()
            self.multi_frame.pack(fill="both",expand=True)

    # ── Single customer ───────────────────────────────────────────────────────
    def _build_single(self):
        t = T()
        card = make_card(self.single_frame)
        card.pack(fill="x",padx=20,pady=(0,8))
        top = ctk.CTkFrame(card,fg_color="transparent")
        top.pack(padx=16,pady=10,fill="x")

        make_label(top,"Customer",size=12,color=t["text2"]).pack(side="left",padx=(0,6))
        customers = config.load("customers")
        names = [c["name"] for c in customers if c.get("active",True)]
        self.cust_c = make_combo(top,names if names else ["No customers"],width=200)
        self.cust_c.pack(side="left",padx=(0,16))

        rbar,self.from_var,self.to_var = date_range_bar(top, lambda: None)
        rbar.pack(side="left",padx=(0,12))

        make_btn(top,"Generate",self._generate,width=100).pack(side="left",padx=(0,8))
        make_btn(top,"Export PDF",self._export_pdf,style="ghost",width=110).pack(side="left",padx=(0,8))
        make_btn(top,"Save Text",self._save_txt,style="ghost",width=100).pack(side="left")

        # Summary strip
        self.summary_frame = ctk.CTkFrame(self.single_frame,fg_color="transparent")
        self.summary_frame.pack(fill="x",padx=20,pady=(0,8))

        # PDF-style bill canvas
        bill_card = make_card(self.single_frame)
        bill_card.pack(fill="both",expand=True,padx=20,pady=(0,16))

        # Inner canvas for PDF-style rendering
        self.bill_canvas = tk.Canvas(bill_card,bg="#ffffff",highlightthickness=0)
        h_sb = tk.Scrollbar(bill_card,orient="horizontal",command=self.bill_canvas.xview)
        v_sb = tk.Scrollbar(bill_card,orient="vertical",command=self.bill_canvas.yview)
        self.bill_canvas.configure(xscrollcommand=h_sb.set,yscrollcommand=v_sb.set)
        h_sb.pack(side="bottom",fill="x")
        v_sb.pack(side="right",fill="y")
        self.bill_canvas.pack(fill="both",expand=True,padx=4,pady=4)
        self.bill_frame = tk.Frame(self.bill_canvas,bg="#ffffff")
        self._bill_win  = self.bill_canvas.create_window((0,0),window=self.bill_frame,anchor="nw")
        self.bill_frame.bind("<Configure>",
            lambda e: self.bill_canvas.configure(scrollregion=self.bill_canvas.bbox("all")))
        self.bill_canvas.bind("<Configure>",
            lambda e: self.bill_canvas.itemconfig(self._bill_win,width=max(e.width,800)))
        self.bill_canvas.bind("<MouseWheel>",
            lambda e: self.bill_canvas.yview_scroll(-1 if e.delta>0 else 1,"units"))

        tk.Label(self.bill_frame,text="Generate a bill to see it here.",
                 bg="#ffffff",fg="#aaaaaa",font=("Segoe UI",12),pady=40).pack()

    def _generate(self):
        t = T()
        cust_name = self.cust_c.get().strip()
        if not cust_name or cust_name=="No customers":
            messagebox.showerror("Error","Select a customer."); return
        customers = config.load("customers")
        cust = next((c for c in customers if c["name"]==cust_name),None)
        if not cust: return

        from_d = self.from_var.get().strip()
        to_d   = self.to_var.get().strip()
        entries  = config.load("entries")
        payments = config.load("payments")
        products = config.load("products")
        active_prods = [p for p in products if p["active"]]

        all_e   = [e for e in entries  if e["cust_id"]==cust["id"]]
        all_p   = [p for p in payments if p["cust_id"]==cust["id"]]
        prev_amt  = sum(e.get("total",0) for e in all_e if e["date"]<from_d)
        prev_paid = sum(p["amount"] for p in all_p      if p["date"]<from_d)
        pending   = cust.get("opening_balance",0)+prev_amt-prev_paid

        period_e = sorted([e for e in all_e if from_d<=e["date"]<=to_d],key=lambda x:x["date"])
        period_p = [p for p in all_p if from_d<=p["date"]<=to_d]

        # Only products customer actually took
        used_pids = set()
        for e in period_e:
            for pid_str,qty in e.get("items",{}).items():
                if qty and float(qty)>0: used_pids.add(int(pid_str))
        disp_prods = [p for p in active_prods if p["id"] in used_pids]

        totals      = {p["id"]:0.0 for p in disp_prods}
        total_pay   = sum(p["amount"] for p in period_p)
        total_supply= 0.0
        for e in period_e:
            for pid_str,qty in e.get("items",{}).items():
                pid=int(pid_str)
                if pid in totals: totals[pid]+=float(qty)
            total_supply+=e.get("total",0)
        amounts     = {p["id"]:round(totals[p["id"]]*p["rate"],2) for p in disp_prods}
        net_pending = pending+total_supply-total_pay

        self._last_bill=(cust,entries,payments,products,from_d,to_d)

        # Summary
        for w in self.summary_frame.winfo_children(): w.destroy()
        for lbl,val,color in [
            ("Previous Pending",f"₹{pending:,.2f}",t["warning"]),
            ("Period Supply",f"₹{total_supply:,.2f}",t["btn"]),
            ("Payments",f"₹{total_pay:,.2f}",t["success"]),
            ("Net Pending",f"₹{net_pending:,.2f}",t["danger"]),
        ]:
            box=ctk.CTkFrame(self.summary_frame,fg_color=t["card"],
                             border_color=t["border"],border_width=1,corner_radius=8)
            box.pack(side="left",padx=(0,10),pady=4)
            ctk.CTkLabel(box,text=val,font=ctk.CTkFont(size=16,weight="bold"),
                         text_color=color).pack(padx=16,pady=(8,2))
            ctk.CTkLabel(box,text=lbl,font=ctk.CTkFont(size=10),
                         text_color=t["text2"]).pack(padx=16,pady=(0,8))

        # ── Render PDF-style bill in canvas ───────────────────────────────────
        for w in self.bill_frame.winfo_children(): w.destroy()
        settings = config.load("settings")
        bg,fg,hdr_bg = "#ffffff","#111111","#1a1a2e"
        hdr_fg = "#ffffff"
        row_a,row_b = "#f9f9f9","#ffffff"
        acc = "#1a6faf"

        # Header
        header_f = tk.Frame(self.bill_frame,bg=hdr_bg)
        header_f.pack(fill="x")
        tk.Label(header_f,text=settings.get("dairy_name","Baba Nanak Dairy"),
                 bg=hdr_bg,fg=hdr_fg,font=("Segoe UI",16,"bold"),pady=8).pack()
        tk.Label(header_f,text=f"{settings.get('address','')}   |   {settings.get('contact','')}",
                 bg=hdr_bg,fg="#aaaacc",font=("Segoe UI",10)).pack(pady=(0,8))

        # Customer + period info
        info_f = tk.Frame(self.bill_frame,bg="#f0f4ff")
        info_f.pack(fill="x")
        left_i  = tk.Frame(info_f,bg="#f0f4ff")
        right_i = tk.Frame(info_f,bg="#f0f4ff")
        left_i.pack(side="left",padx=20,pady=10)
        right_i.pack(side="right",padx=20,pady=10)
        tk.Label(left_i,text=f"Customer:  {cust['name']}",bg="#f0f4ff",fg=fg,
                 font=("Segoe UI",12,"bold"),anchor="w").pack(anchor="w")
        tk.Label(left_i,text=f"Phone:  {cust.get('phone','—')}",bg="#f0f4ff",fg="#555",
                 font=("Segoe UI",10),anchor="w").pack(anchor="w")
        tk.Label(left_i,text=f"Period:  {from_d}  to  {to_d}",bg="#f0f4ff",fg="#555",
                 font=("Segoe UI",10),anchor="w").pack(anchor="w")
        tk.Label(right_i,text=f"Pending: ₹{pending:,.2f}",bg="#f0f4ff",fg="#c0392b",
                 font=("Segoe UI",12,"bold")).pack()

        # Table
        pay_by_date = {}
        for p in period_p: pay_by_date.setdefault(p["date"],[]).append(p)
        entry_by_date = {e["date"]:e for e in period_e}

        try: dates = config.date_range(from_d,to_d)
        except: dates=[]

        tbl_f = tk.Frame(self.bill_frame,bg=bg)
        tbl_f.pack(fill="x",padx=8,pady=8)

        COL_DATE=11; COL_PROD=9; COL_PAY=14; COL_TOT=10

        # Header row
        hrow = tk.Frame(tbl_f,bg=hdr_bg)
        hrow.pack(fill="x")
        tk.Label(hrow,text="Date",width=COL_DATE,bg=hdr_bg,fg=hdr_fg,
                 font=("Courier New",9,"bold"),anchor="w",padx=4).pack(side="left")
        for p in disp_prods:
            tk.Label(hrow,text=p["name"],width=COL_PROD,bg=hdr_bg,fg=hdr_fg,
                     font=("Courier New",9,"bold"),anchor="center").pack(side="left")
        tk.Label(hrow,text="Payments",width=COL_PAY,bg=hdr_bg,fg=hdr_fg,
                 font=("Courier New",9,"bold"),anchor="center").pack(side="left")
        tk.Label(hrow,text="Total",width=COL_TOT,bg=hdr_bg,fg=hdr_fg,
                 font=("Courier New",9,"bold"),anchor="e",padx=4).pack(side="left")

        # Data rows
        for i,d in enumerate(dates):
            e    = entry_by_date.get(d)
            pmts = pay_by_date.get(d,[])
            rbg  = row_a if i%2==0 else row_b
            rfg  = "#1a7a3c" if e else "#999999"
            drow = tk.Frame(tbl_f,bg=rbg)
            drow.pack(fill="x")
            dt_str = datetime.strptime(d,"%Y-%m-%d").strftime("%b %d")
            tk.Label(drow,text=dt_str,width=COL_DATE,bg=rbg,fg=fg,
                     font=("Courier New",9,"bold" if e else "normal"),anchor="w",padx=4).pack(side="left")
            for p in disp_prods:
                qty = e["items"].get(str(p["id"]),0) if e else 0
                tk.Label(drow,text=str(qty) if qty else "—",width=COL_PROD,bg=rbg,
                          fg=rfg,font=("Courier New",9),anchor="center").pack(side="left")
            pmt_str = "  ".join(f"₹{p['amount']:,.0f}" for p in pmts) if pmts else "—"
            tk.Label(drow,text=pmt_str,width=COL_PAY,bg=rbg,fg="#d97706" if pmts else "#999",
                     font=("Courier New",9),anchor="center").pack(side="left")
            total = e.get("total",0) if e else 0
            tk.Label(drow,text=f"₹{total:,.0f}" if total else "—",width=COL_TOT,bg=rbg,
                     fg=rfg,font=("Courier New",9),anchor="e",padx=4).pack(side="left")

        # Totals / Rate / Amounts footer rows
        for row_data,rbg,rfw in [
            (["Totals"]+[str(round(totals[p["id"]],1)) if totals[p["id"]] else "—"
                         for p in disp_prods]+[f"₹{total_pay:,.0f}",f"₹{total_supply:,.0f}"],
             "#e8f5e9","bold"),
            (["Rate"]+[f"₹{p['rate']:.0f}" for p in disp_prods]+["",""],"#fff8e1","normal"),
            (["Amounts"]+[f"₹{amounts[p['id']]:,.0f}" if amounts[p["id"]] else "—"
                          for p in disp_prods]+["",f"₹{total_supply:,.0f}"],"#e3f2fd","bold"),
        ]:
            srow = tk.Frame(tbl_f,bg=rbg)
            srow.pack(fill="x")
            cols = [COL_DATE]+[COL_PROD]*len(disp_prods)+[COL_PAY,COL_TOT]
            for val,w in zip(row_data,cols):
                tk.Label(srow,text=str(val),width=w,bg=rbg,fg=fg,
                         font=("Courier New",9,rfw),anchor="center").pack(side="left")

        # Total amount bar
        tot_bar = tk.Frame(self.bill_frame,bg="#1a1a2e")
        tot_bar.pack(fill="x",padx=8,pady=(0,4))
        tk.Label(tot_bar,text=f"Total Amount: ₹{total_supply:,.2f}",bg="#1a1a2e",fg="#ffffff",
                 font=("Segoe UI",13,"bold"),pady=6).pack(side="left",padx=16)
        tk.Label(tot_bar,text=f"Paid: ₹{total_pay:,.2f}",bg="#1a1a2e",fg="#86efac",
                 font=("Segoe UI",12,"bold")).pack(side="left",padx=16)
        tk.Label(tot_bar,text=f"Net Pending: ₹{net_pending:,.2f}",bg="#1a1a2e",fg="#fca5a5",
                 font=("Segoe UI",13,"bold")).pack(side="right",padx=16)

        # Footer
        tk.Label(self.bill_frame,
                 text=f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}  |  {settings.get('dairy_name','')}",
                 bg="#f0f0f0",fg="#888888",font=("Segoe UI",9),pady=6).pack(fill="x")

        self.app.set_status(f"Bill: ₹{total_supply:,.2f} supply, ₹{net_pending:,.2f} pending")

    def _export_pdf(self):
        if not self._last_bill:
            messagebox.showinfo("Info","Generate a bill first."); return
        cust,entries,payments,products,from_d,to_d=self._last_bill
        path=filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"bill_{cust['name']}_{from_d}.pdf")
        if path:
            try:
                pdf_export.export_customer_bill(cust,entries,payments,products,from_d,to_d,path)
                self.app.set_status("PDF saved.")
                messagebox.showinfo("Done","PDF saved successfully!")
            except Exception as ex:
                messagebox.showerror("Error",str(ex))

    def _save_txt(self):
        if not self._last_bill:
            messagebox.showinfo("Info","Generate a bill first."); return
        # Quick text export
        cust,entries,payments,products,from_d,to_d = self._last_bill
        path=filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text","*.txt")],initialfile="bill.txt")
        if path:
            with open(path,"w",encoding="utf-8") as f:
                f.write(f"Bill: {cust['name']} | {from_d} to {to_d}\n")
            self.app.set_status("Text saved.")

    # ── Multi-customer export ─────────────────────────────────────────────────
    def _build_multi(self):
        t = T()
        card = make_card(self.multi_frame)
        card.pack(fill="x",padx=20,pady=(0,10))

        make_label(card,"Multi-Customer PDF Export",size=14,bold=True).pack(anchor="w",padx=16,pady=(12,4))
        make_label(card,"Select customers → set date range → export all bills as separate PDFs.",
                   size=11,color=t["text2"]).pack(anchor="w",padx=16,pady=(0,8))

        # Date range
        drow = ctk.CTkFrame(card,fg_color="transparent")
        drow.pack(padx=16,pady=(0,8),fill="x")
        rbar,self.m_from_var,self.m_to_var = date_range_bar(drow,lambda: None)
        rbar.pack(fill="x")

        # Schedule info
        sched_row = ctk.CTkFrame(card,fg_color="transparent")
        sched_row.pack(padx=16,pady=(0,8),anchor="w")
        make_label(sched_row,"Auto-schedule: generate bills on day",size=12,color=t["text2"]).pack(side="left",padx=(0,8))
        settings = config.load("settings")
        self.sched_day_e = make_entry(sched_row,str(settings.get("bill_schedule_day",1)),width=60)
        self.sched_day_e.pack(side="left",padx=(0,8))
        make_label(sched_row,"of every month",size=12,color=t["text2"]).pack(side="left",padx=(0,12))
        make_btn(sched_row,"Save Schedule",self._save_schedule,style="ghost",width=140).pack(side="left")

        btn_row = ctk.CTkFrame(card,fg_color="transparent")
        btn_row.pack(padx=16,pady=(0,14),fill="x")
        make_btn(btn_row,"Select All",self._select_all_custs,style="ghost",width=110).pack(side="left",padx=(0,8))
        make_btn(btn_row,"Deselect All",self._deselect_all_custs,style="ghost",width=110).pack(side="left",padx=(0,16))
        make_btn(btn_row,"Export Selected as PDFs",self._export_multi,width=200).pack(side="left")

        self.m_result_lbl = make_label(card,"",size=12,color=t["success"])
        self.m_result_lbl.pack(anchor="w",padx=16,pady=(0,8))

        # Customer checklist
        make_label(self.multi_frame,"Select Customers:",size=13,bold=True).pack(anchor="w",padx=20,pady=(8,4))
        tcard = make_card(self.multi_frame)
        tcard.pack(fill="both",expand=True,padx=20,pady=(0,16))

        scroll = ctk.CTkScrollableFrame(tcard,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=8,pady=8)

        self.cust_check_vars = {}
        customers = config.load("customers")
        entries   = config.load("entries")
        payments  = config.load("payments")
        for c in customers:
            if not c.get("active",True): continue
            supply  = sum(e.get("total",0) for e in entries if e["cust_id"]==c["id"])
            paid    = sum(p["amount"] for p in payments if p["cust_id"]==c["id"])
            pending = c.get("opening_balance",0)+supply-paid
            var = tk.BooleanVar(value=True)
            self.cust_check_vars[c["id"]] = (var,c)
            row = ctk.CTkFrame(scroll,fg_color="transparent")
            row.pack(fill="x",pady=2)
            ctk.CTkCheckBox(row,text=f"  {c['name']}",variable=var,
                             text_color=t["text"],fg_color=t["btn"],
                             border_color=t["border"]).pack(side="left")
            make_label(row,f"Pending: ₹{pending:,.0f}",size=11,color=t["text2"]).pack(side="right",padx=8)

    def _select_all_custs(self):
        for var,_ in self.cust_check_vars.values(): var.set(True)

    def _deselect_all_custs(self):
        for var,_ in self.cust_check_vars.values(): var.set(False)

    def _save_schedule(self):
        try: day = int(self.sched_day_e.get())
        except: messagebox.showerror("Error","Enter valid day (1-31)."); return
        settings = config.load("settings")
        settings["bill_schedule_day"] = day
        config.save("settings",settings)
        self.app.set_status(f"Bill schedule set to day {day} of every month.")

    def _export_multi(self):
        selected = [c for vid,(var,c) in self.cust_check_vars.items() if var.get()]
        if not selected:
            messagebox.showinfo("Info","Select at least one customer."); return
        folder = filedialog.askdirectory(title="Select folder to save PDFs")
        if not folder: return

        from_d = self.m_from_var.get().strip()
        to_d   = self.m_to_var.get().strip()
        entries  = config.load("entries")
        payments = config.load("payments")
        products = config.load("products")

        done,failed = 0,0
        for cust in selected:
            try:
                path = os.path.join(folder,f"bill_{cust['name'].replace(' ','_')}_{from_d}.pdf")
                pdf_export.export_customer_bill(cust,entries,payments,products,from_d,to_d,path)
                done+=1
            except Exception as ex:
                failed+=1

        msg = f"Exported {done} PDFs to {folder}"
        if failed: msg+=f" ({failed} failed)"
        self.m_result_lbl.configure(text=msg)
        self.app.set_status(msg)
        messagebox.showinfo("Done",msg)
