import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pages"))

import customtkinter as ctk
import tkinter as tk
import config, theme, notifications
from theme import get as T

from pages.dashboard      import DashboardPage
from pages.customers      import CustomersPage
from pages.entry          import EntryPage
from pages.ledger         import LedgerPage
from pages.payments       import PaymentsPage
from pages.billing        import BillingPage
from pages.formulas       import FormulasPage
from pages.products       import ProductsPage
from pages.settings       import SettingsPage
from pages.suppliers      import SuppliersPage
from pages.supplier_entry import SupplierEntryPage

_settings = config.load("settings")
theme.apply(_settings.get("theme","dark"), _settings.get("accent","blue"))
ctk.set_appearance_mode(_settings.get("theme","dark"))
ctk.set_default_color_theme("blue")

NAV_ITEMS = [
    ("📊","Dashboard",      DashboardPage),
    ("👥","Customers",      CustomersPage),
    ("🥛","Customer Entry", EntryPage),
    ("📒","Ledger",         LedgerPage),
    ("💰","Payments",       PaymentsPage),
    ("🧾","Billing",        BillingPage),
    ("─────────────","",   None),
    ("🚚","Suppliers",      SuppliersPage),
    ("🧪","Supplier Entry", SupplierEntryPage),
    ("─────────────","",   None),
    ("🔢","Formulas",       FormulasPage),
    ("📦","Products",       ProductsPage),
    ("⚙️","Settings",       SettingsPage),
]

class DairyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        t = T()
        self.title("Baba Nanak Dairy — Management System")
        self.geometry("1240x760")
        self.minsize(1000,640)
        self.configure(fg_color=t["bg"])
        self._pages    = {}
        self._nav_btns = {}
        self._current  = None
        self._build()
        self.after(900, self._show_launch_popup)

    def _build(self):
        t = T()
        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0,
                                    fg_color=t["sidebar"],
                                    border_color=t["border"], border_width=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x")
        ctk.CTkFrame(logo, fg_color=t["btn"], height=3).pack(fill="x")
        ctk.CTkLabel(logo, text="🥛  Baba Nanak Dairy",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=t["text"]).pack(padx=16, pady=(14,2), anchor="w")
        ctk.CTkLabel(logo, text="Management System  v"+config.APP_VERSION,
                     font=ctk.CTkFont(size=10),
                     text_color=t["text2"]).pack(padx=16, pady=(0,10), anchor="w")
        ctk.CTkFrame(self.sidebar, fg_color=t["border"], height=1).pack(fill="x")

        # Nav
        nav_wrap = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_wrap.pack(fill="both", expand=True, pady=8)

        for icon, name, PageClass in NAV_ITEMS:
            # Separator
            if PageClass is None and name == "":
                ctk.CTkFrame(nav_wrap, fg_color=t["border"], height=1).pack(
                    fill="x", padx=12, pady=4)
                continue

            frm = ctk.CTkFrame(nav_wrap, fg_color="transparent")
            frm.pack(fill="x", padx=10, pady=1)
            btn = ctk.CTkButton(frm,
                text=f"  {icon}   {name}",
                anchor="w", height=38, corner_radius=8,
                fg_color="transparent", hover_color=t["card2"],
                text_color=t["text2"], font=ctk.CTkFont(size=12),
                command=lambda n=name: self._nav(n))
            btn.pack(side="left", fill="x", expand=True)

            # Alert badge
            badge = tk.Label(frm, text="", bg=t["danger"], fg="#fff",
                             font=("Segoe UI",8,"bold"),
                             width=2, bd=0, relief="flat")
            badge.pack(side="right", padx=(0,4))
            badge.pack_forget()

            self._nav_btns[name] = (btn, badge)
            self._pages[name]    = None

        # Version at bottom
        ctk.CTkFrame(self.sidebar, fg_color=t["border"], height=1).pack(
            fill="x", side="bottom")
        ctk.CTkLabel(self.sidebar, text="Agondh, Haryana",
                     font=ctk.CTkFont(size=9),
                     text_color=t["text3"]).pack(side="bottom", pady=4)

        # ── Main content ─────────────────────────────────────────────────────
        right = ctk.CTkFrame(self, corner_radius=0, fg_color=t["bg"])
        right.pack(side="left", fill="both", expand=True)

        self.content = ctk.CTkScrollableFrame(right, corner_radius=0,
                                               fg_color=t["bg"],
                                               scrollbar_button_color=t["border"])
        self.content.pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="  Ready  |  Baba Nanak Dairy Management System")
        sb = tk.Frame(right, bg=t["header_bg"], height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var,
                 bg=t["header_bg"], fg=t["text2"],
                 font=("Segoe UI",10), anchor="w").pack(fill="x", padx=8)

        self._nav("Dashboard")
        self.update_badge()

    def _nav(self, name):
        if not name: return
        t = T()
        for page in self._pages.values():
            if page: page.pack_forget()

        for n,(btn,badge) in self._nav_btns.items():
            active = n == name
            btn.configure(
                fg_color=t["card2"] if active else "transparent",
                text_color=t["text"] if active else t["text2"],
                font=ctk.CTkFont(size=12, weight="bold" if active else "normal"))

        if self._pages.get(name) is None:
            PageClass = next((pc for ic,n,pc in NAV_ITEMS if n==name and pc), None)
            if not PageClass: return
            self._pages[name] = PageClass(self.content, self)

        page = self._pages[name]
        page.pack(fill="both", expand=True)
        page.refresh()
        self._current = name

    def update_badge(self):
        t     = T()
        count = notifications.badge_count()
        for name,(btn,badge) in self._nav_btns.items():
            if name in ("Dashboard","Customer Entry","Supplier Entry","Ledger"):
                if count > 0:
                    badge.configure(text=str(count))
                    badge.pack(side="right", padx=(0,6))
                else:
                    badge.pack_forget()

    def _show_launch_popup(self):
        notifications.LaunchPopup(self)

    def open_ledger(self, cust_name):
        self._nav("Ledger")
        ledger = self._pages.get("Ledger")
        if ledger and hasattr(ledger,"cust_c"):
            ledger.cust_c.set(cust_name)

    def set_status(self, msg):
        self.status_var.set(f"  {msg}")
        self.after(5000, lambda: self.status_var.set(
            "  Ready  |  Baba Nanak Dairy Management System"))

    def refresh_combos(self):
        if self._current:
            page = self._pages.get(self._current)
            if page and hasattr(page,"refresh"):
                page.refresh()

if __name__ == "__main__":
    app = DairyApp()
    app.mainloop()
