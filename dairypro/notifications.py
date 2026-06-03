"""
Notification system — persistent alerts, sidebar badge count, launch popup.
"""
import customtkinter as ctk
import tkinter as tk
from theme import get as T
import config

def get_alerts():
    missing_c, missing_s = config.get_missing_today()
    alerts = []
    for c in missing_c:
        alerts.append({
            "type": "customer",
            "id":   c["id"],
            "name": c["name"],
            "msg":  f"{c['name']} — no supply entry today (expected {c.get('expected_qty',0)} L)",
            "color": "warning",
        })
    for s in missing_s:
        alerts.append({
            "type": "supplier",
            "id":   s["id"],
            "name": s["name"],
            "msg":  f"Supplier {s['name']} — no delivery recorded today",
            "color": "danger",
        })
    return alerts

def badge_count():
    a, b = config.get_missing_today()
    return len(a) + len(b)

class NotificationPanel(ctk.CTkFrame):
    """Persistent panel shown on dashboard — never forces close."""
    def __init__(self, parent):
        t = T()
        super().__init__(parent, fg_color=t["card"],
                         border_color=t["border"], border_width=1, corner_radius=10)
        self.refresh()

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t    = T()
        alerts = get_alerts()

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10,4))
        ctk.CTkLabel(hdr, text="🔔  Alerts",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=t["text"]).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{len(alerts)} pending",
                     font=ctk.CTkFont(size=11),
                     text_color=t["text2"]).pack(side="right")

        if not alerts:
            ctk.CTkLabel(self, text="✓  All customers and suppliers covered today",
                         font=ctk.CTkFont(size=11),
                         text_color=t["success"]).pack(padx=12, pady=(4,10))
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=120)
        scroll.pack(fill="x", padx=8, pady=(0,8))

        for a in alerts:
            color = t["warning"] if a["color"] == "warning" else t["danger"]
            row = ctk.CTkFrame(scroll, fg_color=t["card2"],
                               corner_radius=6, border_width=1, border_color=color)
            row.pack(fill="x", pady=2)
            ctk.CTkFrame(row, fg_color=color, width=3, corner_radius=0).pack(
                side="left", fill="y")
            icon = "👤" if a["type"] == "customer" else "🚚"
            ctk.CTkLabel(row, text=f"{icon}  {a['msg']}",
                         font=ctk.CTkFont(size=11),
                         text_color=t["text"], anchor="w").pack(
                side="left", padx=10, pady=6)


class LaunchPopup(ctk.CTkToplevel):
    """Shows once on app launch if there are alerts."""
    def __init__(self, parent):
        super().__init__(parent)
        t = T()
        alerts = get_alerts()
        if not alerts:
            self.destroy()
            return

        self.title("Daily Alerts")
        self.geometry("480x360")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=t["bg"])

        ctk.CTkLabel(self, text="🔔  Today's Pending Alerts",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=t["text"]).pack(pady=(20,4), padx=20, anchor="w")
        ctk.CTkLabel(self, text="These customers/suppliers have no entry for today.",
                     font=ctk.CTkFont(size=11),
                     text_color=t["text2"]).pack(padx=20, anchor="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color=t["card"],
                                         corner_radius=10, height=220)
        scroll.pack(fill="x", padx=20, pady=12)

        for a in alerts:
            color = t["warning"] if a["color"] == "warning" else t["danger"]
            row = ctk.CTkFrame(scroll, fg_color=t["card2"],
                               corner_radius=6, border_width=1, border_color=color)
            row.pack(fill="x", pady=3)
            ctk.CTkFrame(row, fg_color=color, width=4).pack(side="left", fill="y")
            icon = "👤" if a["type"] == "customer" else "🚚"
            ctk.CTkLabel(row, text=f"{icon}  {a['msg']}",
                         font=ctk.CTkFont(size=12),
                         text_color=t["text"], anchor="w").pack(
                side="left", padx=12, pady=8)

        ctk.CTkLabel(self,
                     text="This window will not appear again until you reopen the app.",
                     font=ctk.CTkFont(size=10), text_color=t["text3"]).pack(pady=(0,4))
        ctk.CTkButton(self, text="OK, I'll handle it",
                      command=self.destroy,
                      fg_color=t["btn"], hover_color=t["btn_h"],
                      width=160).pack(pady=(0,16))
