import os, json
from datetime import date, timedelta, datetime

APP_NAME    = "Baba Nanak Dairy"
APP_VERSION = "3.0"
DATA_DIR    = "dairy_data"

PATHS = {
    "customers":    os.path.join(DATA_DIR, "customers.json"),
    "products":     os.path.join(DATA_DIR, "products.json"),
    "entries":      os.path.join(DATA_DIR, "entries.json"),
    "payments":     os.path.join(DATA_DIR, "payments.json"),
    "formulas":     os.path.join(DATA_DIR, "formulas.json"),
    "settings":     os.path.join(DATA_DIR, "settings.json"),
    "skips":        os.path.join(DATA_DIR, "skips.json"),
    "suppliers":    os.path.join(DATA_DIR, "suppliers.json"),
    "sup_entries":  os.path.join(DATA_DIR, "sup_entries.json"),
    "bill_schedule":os.path.join(DATA_DIR, "bill_schedule.json"),
}

DEFAULTS = {
    "products": [
        {"id":1,"name":"Milk",   "unit":"L",  "rate":60.0,  "active":True},
        {"id":2,"name":"Dahi",   "unit":"kg", "rate":50.0,  "active":True},
        {"id":3,"name":"Paneer", "unit":"kg", "rate":230.0, "active":True},
        {"id":4,"name":"Cream",  "unit":"kg", "rate":350.0, "active":True},
        {"id":5,"name":"Ghee",   "unit":"kg", "rate":750.0, "active":True},
        {"id":6,"name":"Makhan", "unit":"kg", "rate":500.0, "active":True},
    ],
    "settings": {
        "theme":"dark","accent":"blue",
        "dairy_name":"Baba Nanak Dairy",
        "address":"Agondh, next to Bus Stop",
        "contact":"9896086466",
        "global_fatrate": 5850.0,
        "bill_schedule_day": 1,
    },
    "formulas":[],"skips":[],"suppliers":[],"sup_entries":[],"bill_schedule":[],
}

os.makedirs(DATA_DIR, exist_ok=True)

def load(key):
    path = PATHS[key]
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    return DEFAULTS.get(key, [])

def save(key, data):
    with open(PATHS[key],"w",encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def next_id(lst):
    return max((x["id"] for x in lst), default=0) + 1

# ── Calculation modes ────────────────────────────────────────────────────────
import math

def calc_full(qty, fat, meter, fatrate):
    directrate = fatrate / 650
    gheeQty    = fat * qty / 100
    SNF        = (25 * meter + fat * 20 + 14) / 100
    powderQty  = math.floor(SNF * qty) / 100
    gheeRate   = directrate * 60
    powderRate = directrate * 30.69
    total      = gheeQty * gheeRate + powderQty * powderRate
    return {"SNF": round(SNF,2), "amount": round(total,2)}

def calc_direct(qty, fat, fatrate):
    directrate = fatrate / 650
    milkrate   = directrate * fat
    total      = milkrate * qty
    return {"SNF": None, "amount": round(total,2)}

def calc_fixed(qty, rate):
    return {"SNF": None, "amount": round(qty * rate, 2)}

# ── Date helpers ─────────────────────────────────────────────────────────────
def this_month_range():
    today = date.today()
    first = today.replace(day=1)
    return first.isoformat(), today.isoformat()

def last_n_days(n):
    today = date.today()
    start = today - timedelta(days=n-1)
    return start.isoformat(), today.isoformat()

def date_range(from_d, to_d):
    d1, d2 = datetime.strptime(from_d,"%Y-%m-%d").date(), datetime.strptime(to_d,"%Y-%m-%d").date()
    out, cur = [], d1
    while cur <= d2:
        out.append(cur.isoformat()); cur += timedelta(days=1)
    return out

# ── Missing today ────────────────────────────────────────────────────────────
def get_missing_today():
    today     = date.today().isoformat()
    customers = load("customers")
    entries   = load("entries")
    skips     = load("skips")
    suppliers = load("suppliers")
    sup_entries = load("sup_entries")

    today_cust_ids = {e["cust_id"] for e in entries if e["date"]==today}
    skip_cust_ids  = {s["cust_id"] for s in skips
                      if s["date"]==today and s.get("type","customer")=="customer"}
    missing_custs  = [c for c in customers
                      if c.get("active",True) and c.get("expected_qty",0)>0
                      and c["id"] not in today_cust_ids
                      and c["id"] not in skip_cust_ids]

    today_sup_ids  = {e["sup_id"] for e in sup_entries if e["date"]==today}
    skip_sup_ids   = {s["cust_id"] for s in skips
                      if s["date"]==today and s.get("type")=="supplier"}
    missing_sups   = [s for s in suppliers
                      if s.get("active",True)
                      and s["id"] not in today_sup_ids
                      and s["id"] not in skip_sup_ids]
    return missing_custs, missing_sups
