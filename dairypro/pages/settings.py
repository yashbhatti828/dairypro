import customtkinter as ctk
from widgets import make_label, make_entry, make_btn, make_card, section_title
from theme import get as T, ACCENTS
import config, theme
from tkinter import messagebox

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        t = T()
        settings = config.load("settings")
        section_title(self,"Settings")

        # Dairy info
        info_card = make_card(self)
        info_card.pack(fill="x",padx=20,pady=(0,12))
        make_label(info_card,"Dairy Information",size=14,bold=True).pack(anchor="w",padx=16,pady=(12,8))
        form = ctk.CTkFrame(info_card,fg_color="transparent")
        form.pack(padx=16,pady=(0,12),fill="x")

        fields = [
            ("Dairy Name",   "dairy_name",  settings.get("dairy_name","Baba Nanak Dairy")),
            ("Address",      "address",     settings.get("address","")),
            ("Contact",      "contact",     settings.get("contact","")),
        ]
        self._field_entries = {}
        for i,(label_txt,key,val) in enumerate(fields):
            make_label(form,label_txt,size=12,color=t["text2"]).grid(row=i,column=0,sticky="w",padx=(0,12),pady=6)
            e = make_entry(form,width=320)
            e.insert(0,val)
            e.grid(row=i,column=1,pady=6,sticky="ew")
            self._field_entries[key] = e

        make_btn(info_card,"Save Info",self._save_info,width=130).pack(anchor="w",padx=16,pady=(0,14))

        # Theme
        theme_card = make_card(self)
        theme_card.pack(fill="x",padx=20,pady=(0,12))
        make_label(theme_card,"Appearance",size=14,bold=True).pack(anchor="w",padx=16,pady=(12,8))

        trow = ctk.CTkFrame(theme_card,fg_color="transparent")
        trow.pack(padx=16,pady=(0,8),anchor="w")
        make_label(trow,"Mode:",size=12,color=t["text2"]).pack(side="left",padx=(0,10))

        cur_theme = settings.get("theme","dark")
        for mode in ["dark","light"]:
            active = cur_theme == mode
            btn = ctk.CTkButton(trow, text=mode.capitalize(),
                width=100,
                fg_color=t["btn"] if active else "transparent",
                hover_color=t["btn_h"],
                text_color="#ffffff" if active else t["text"],
                border_width=1, border_color=t["border"],
                command=lambda m=mode: self._set_theme(m))
            btn.pack(side="left",padx=(0,8))

        arow = ctk.CTkFrame(theme_card,fg_color="transparent")
        arow.pack(padx=16,pady=(0,14),anchor="w")
        make_label(arow,"Accent:",size=12,color=t["text2"]).pack(side="left",padx=(0,10))
        cur_accent = settings.get("accent","blue")
        accent_colors = {"blue":"#2196F3","green":"#4CAF50","orange":"#FF9800","purple":"#9C27B0"}
        for acc,color in accent_colors.items():
            active = cur_accent == acc
            btn = ctk.CTkButton(arow, text=acc.capitalize(),
                width=100,
                fg_color=color if active else "transparent",
                hover_color=color,
                text_color="#ffffff",
                border_width=1, border_color=color,
                command=lambda a=acc: self._set_accent(a))
            btn.pack(side="left",padx=(0,8))

        # About
        about_card = make_card(self)
        about_card.pack(fill="x",padx=20,pady=(0,16))
        make_label(about_card,f"Baba Nanak Dairy Management System  v{config.APP_VERSION}",
                   size=12,color=t["text2"]).pack(padx=16,pady=12)

    def _save_info(self):
        settings = config.load("settings")
        for key,e in self._field_entries.items():
            settings[key] = e.get().strip()
        config.save("settings",settings)
        self.app.set_status("Dairy info saved.")

    def _set_theme(self, mode):
        settings = config.load("settings")
        settings["theme"] = mode
        config.save("settings",settings)
        theme.apply(mode, settings.get("accent","blue"))
        self.app.set_status(f"Theme changed to {mode}. Restart app to fully apply.")
        messagebox.showinfo("Theme Changed",
            "Theme saved. Please restart the application to fully apply the new theme.")

    def _set_accent(self, acc):
        settings = config.load("settings")
        settings["accent"] = acc
        config.save("settings",settings)
        theme.current_accent = acc
        self.app.set_status(f"Accent changed to {acc}. Restart to apply.")
        messagebox.showinfo("Accent Changed","Accent saved. Restart the app to apply.")
