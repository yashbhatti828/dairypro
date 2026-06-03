import customtkinter as ctk

ACCENTS = {
    "blue":   {"btn":"#1a6faf","btn_h":"#1557a0","highlight":"#2196F3"},
    "green":  {"btn":"#2e7d32","btn_h":"#1b5e20","highlight":"#4CAF50"},
    "orange": {"btn":"#e65100","btn_h":"#bf360c","highlight":"#FF9800"},
    "purple": {"btn":"#6a1b9a","btn_h":"#4a148c","highlight":"#9C27B0"},
}

DARK = {
    "bg":         "#141414",
    "sidebar":    "#1a1a1a",
    "card":       "#1f1f1f",
    "card2":      "#252525",
    "border":     "#2d2d2d",
    "text":       "#f0f0f0",
    "text2":      "#999999",
    "text3":      "#666666",
    "row_even":   "#1f1f1f",
    "row_odd":    "#252525",
    "row_hover":  "#2d2d2d",
    "input_bg":   "#2a2a2a",
    "header_bg":  "#161616",
    "success":    "#2e7d32",
    "danger":     "#c62828",
    "warning":    "#f57f17",
}

LIGHT = {
    "bg":         "#f5f5f5",
    "sidebar":    "#ffffff",
    "card":       "#ffffff",
    "card2":      "#f9f9f9",
    "border":     "#e0e0e0",
    "text":       "#1a1a1a",
    "text2":      "#555555",
    "text3":      "#999999",
    "row_even":   "#ffffff",
    "row_odd":    "#f9f9f9",
    "row_hover":  "#f0f0f0",
    "input_bg":   "#f0f0f0",
    "header_bg":  "#eeeeee",
    "success":    "#388e3c",
    "danger":     "#d32f2f",
    "warning":    "#f9a825",
}

current_theme = "dark"
current_accent = "blue"

def get():
    t = DARK if current_theme == "dark" else LIGHT
    a = ACCENTS.get(current_accent, ACCENTS["blue"])
    return {**t, **a}

def apply(theme_name, accent_name):
    global current_theme, current_accent
    current_theme  = theme_name
    current_accent = accent_name
    ctk.set_appearance_mode(theme_name)
