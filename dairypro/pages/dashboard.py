import customtkinter as ctk
import tkinter as tk
from widgets import StatCard, Table, make_label, section_title
from theme import get as T
import config, notifications
from datetime import date

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        section_title(self, "Dashboard")

        today = date.today().isoformat()
        month = today[:7]
        entries   = config.load("entries")
        payments  = config.load("payments")
        customers = config.load("customers")

        today_e   = [e for e in entries if e["date"] == today]
        month_e   = [e for e in entries if e["date"].startswith(month)]
        today_pay = sum(p["amount"] for p in payments if p["date"] == today)
        month_pay = sum(p["amount"] for p in payments if p["date"].startswith(month))
        today_amt = sum(e.get("total",0) for e in today_e)
        month_amt = sum(e.get("total",0) for e in month_e)
        total_pending = sum(
            c.get("opening_balance",0) +
            sum(e.get("total",0) for e in entries if e["cust_id"]==c["id"]) -
            sum(p["amount"] for p in payments if p["cust_id"]==c["id"])
            for c in customers if c.get("active",True)
        )

        # ── Stat cards ───────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0,10))
        cards = [
            ("Customers",     str(sum(1 for c in customers if c.get("active",True))), "", None),
            ("Today's Sales", f"₹{today_amt:,.0f}", f"Paid: ₹{today_pay:,.0f}", t["btn"]),
            ("Month Sales",   f"₹{month_amt:,.0f}", f"Paid: ₹{month_pay:,.0f}", t["btn"]),
            ("Total Pending", f"₹{total_pending:,.0f}", "All customers", t["danger"]),
        ]
        for title, val, sub, color in cards:
            StatCard(stats_frame, title, val, sub, color).pack(
                side="left", padx=(0,10), pady=4, ipadx=4)

        # ── Two column layout: alerts + recent ───────────────────────────────
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=20, pady=(0,16))

        # Left — notification panel
        left = ctk.CTkFrame(cols, fg_color="transparent", width=340)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)
        make_label(left,"Today's Alerts",size=14,bold=True).pack(anchor="w",pady=(0,6))
        self.notif_panel = notifications.NotificationPanel(left)
        self.notif_panel.pack(fill="x")

        # Refresh button
        ctk.CTkButton(left, text="↻  Refresh Alerts",
                      command=self.notif_panel.refresh,
                      fg_color="transparent",
                      border_width=1, border_color=t["border"],
                      text_color=t["text2"],
                      hover_color=t["card2"],
                      width=160, height=28,
                      font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(6,0))

        # Right — recent entries
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        make_label(right,"Recent Supply Entries",size=14,bold=True).pack(anchor="w",pady=(0,6))

        prods       = config.load("products")
        active_prods= [p for p in prods if p["active"]]
        cust_map    = {c["id"]:c["name"] for c in customers}

        tcard = ctk.CTkFrame(right, fg_color=t["card"],
                             border_color=t["border"], border_width=1, corner_radius=10)
        tcard.pack(fill="both", expand=True)
        cols_h  = ["Date","Customer"] + [p["name"] for p in active_prods] + ["Total"]
        widths  = [110,160] + [75]*len(active_prods) + [110]
        tbl = Table(tcard, cols_h, widths, height=300)
        tbl.pack(fill="both", expand=True, padx=8, pady=8)

        recent = sorted(entries, key=lambda e: e["date"], reverse=True)[:15]
        if not recent:
            tbl.empty_state("No entries yet.")
        for e in recent:
            row_vals = [e["date"], cust_map.get(e["cust_id"],"?")]
            for p in active_prods:
                qty = e.get("items",{}).get(str(p["id"]),0)
                row_vals.append(str(qty) if qty else "-")
            row_vals.append(f"₹{e.get('total',0):,.2f}")
            tbl.add_row(row_vals)
