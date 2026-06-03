from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import config, os
from datetime import datetime, timedelta

def export_customer_bill(customer, entries, payments, products, from_date, to_date, filepath):
    settings = config.load("settings")
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    title_style = ParagraphStyle("t", fontSize=16, fontName="Helvetica-Bold",
                                  alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle("s", fontSize=9,  fontName="Helvetica",
                                  alignment=TA_CENTER, textColor=colors.grey)
    cust_style  = ParagraphStyle("c", fontSize=13, fontName="Helvetica-Bold",
                                  alignment=TA_RIGHT)

    story.append(Paragraph(settings.get("dairy_name","Baba Nanak Dairy"), title_style))
    story.append(Paragraph(
        f"{settings.get('address','')}  |  {settings.get('contact','')}", sub_style))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(customer["name"], cust_style))
    story.append(Spacer(1,0.2*cm))

    all_e   = [e for e in entries  if e["cust_id"]==customer["id"]]
    all_p   = [p for p in payments if p["cust_id"]==customer["id"]]
    prev_amt  = sum(e.get("total",0) for e in all_e if e["date"] < from_date)
    prev_paid = sum(p["amount"] for p in all_p    if p["date"] < from_date)
    pending   = customer.get("opening_balance",0) + prev_amt - prev_paid

    info_data = [["Month", f"{from_date}  ↔  {to_date}", "", f"Pending  ₹{pending:,.2f}"],
                 ["", "", "", customer["name"]]]
    info_tbl = Table(info_data, colWidths=[2*cm,6*cm,4*cm,5*cm])
    info_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),10),
        ("FONTNAME",(3,0),(3,0),"Helvetica-Bold"),
        ("ALIGN",(3,0),(3,-1),"RIGHT"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1,0.3*cm))

    # ── Find only products this customer actually took in this period ─────────
    period_e = [e for e in all_e if from_date <= e["date"] <= to_date]
    used_prod_ids = set()
    for e in period_e:
        for pid_str, qty in e.get("items",{}).items():
            if qty and float(qty) > 0:
                used_prod_ids.add(int(pid_str))

    active_prods = [p for p in products if p["active"] and p["id"] in used_prod_ids]

    if not active_prods:
        story.append(Paragraph("No supply entries found for this period.", sub_style))
        doc.build(story)
        return filepath

    # ── Build date range ──────────────────────────────────────────────────────
    d1 = datetime.strptime(from_date,"%Y-%m-%d").date()
    d2 = datetime.strptime(to_date,  "%Y-%m-%d").date()
    date_range = []
    cur = d1
    while cur <= d2:
        date_range.append(cur.isoformat())
        cur += timedelta(days=1)

    entry_by_date = {e["date"]:e for e in period_e}
    pay_by_date   = {}
    for p in all_p:
        if from_date <= p["date"] <= to_date:
            pay_by_date.setdefault(p["date"],[]).append(p)

    totals        = {p["id"]:0.0 for p in active_prods}
    total_payment = 0.0

    headers = ["Date"] + [p["name"] for p in active_prods] + ["Payments"]
    col_w   = [2.2*cm] + [2*cm]*len(active_prods) + [3*cm]

    table_data = [headers]
    for d in date_range:
        e   = entry_by_date.get(d)
        pmt = pay_by_date.get(d,[])
        pmt_str = ", ".join(
            "₹"+f"{p['amount']:,.0f}"+(f"({p['note']})" if p.get("note") else "")
            for p in pmt) if pmt else "-"
        row = [datetime.strptime(d,"%Y-%m-%d").strftime("%b %d")]
        for prod in active_prods:
            qty = e["items"].get(str(prod["id"]),0) if e else 0
            row.append(str(qty) if qty else "-")
            totals[prod["id"]] += float(qty) if qty else 0
        row.append(pmt_str)
        total_payment += sum(p["amount"] for p in pmt)
        table_data.append(row)

    tot_row  = ["Totals"] + [str(round(totals[p["id"]],2)) if totals[p["id"]] else "-"
                              for p in active_prods] + [f"₹{total_payment:,.2f}"]
    rate_row = ["Rate"]   + [f"₹{p['rate']:.0f}" for p in active_prods] + [""]
    amounts  = {p["id"]:round(totals[p["id"]]*p["rate"],2) for p in active_prods}
    total_amt= sum(amounts.values())
    amt_row  = ["Amounts"]+ [f"₹{amounts[p['id']]:,.0f}" if amounts[p["id"]] else "-"
                              for p in active_prods] + [""]
    table_data += [tot_row, rate_row, amt_row,
                   ["Total Amount", f"₹{total_amt:,.2f}"] + [""]*(len(active_prods)-1) + [""]]

    tbl = Table(table_data, colWidths=col_w, repeatRows=1)
    n   = len(table_data)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),      colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",(0,0),(-1,0),       colors.white),
        ("FONTNAME",(0,0),(-1,0),        "Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),       9),
        ("ALIGN",(0,0),(-1,-1),          "CENTER"),
        ("ALIGN",(0,0),(0,-1),           "LEFT"),
        ("GRID",(0,0),(-1,-1),           0.4,colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0,1),(-1,n-5),[colors.white,colors.HexColor("#f9f9f9")]),
        ("BACKGROUND",(0,n-4),(-1,n-4),  colors.HexColor("#e8f5e9")),
        ("BACKGROUND",(0,n-3),(-1,n-3),  colors.HexColor("#fff8e1")),
        ("BACKGROUND",(0,n-2),(-1,n-2),  colors.HexColor("#e3f2fd")),
        ("BACKGROUND",(0,n-1),(-1,n-1),  colors.HexColor("#fce4ec")),
        ("FONTNAME",(0,n-4),(-1,n-1),    "Helvetica-Bold"),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(tbl)
    story.append(Spacer(1,0.4*cm))

    net_pending = pending + total_amt - total_payment
    s_data = [["Previous Pending",f"₹{pending:,.2f}"],
               ["Period Amount",  f"₹{total_amt:,.2f}"],
               ["Payments",       f"₹{total_payment:,.2f}"],
               ["Net Pending",    f"₹{net_pending:,.2f}"]]
    s_tbl = Table(s_data, colWidths=[6*cm,4*cm], hAlign="RIGHT")
    s_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(0,3),(1,3),"Helvetica-Bold"),
        ("FONTSIZE",(0,3),(1,3),11),
        ("BACKGROUND",(0,3),(1,3),colors.HexColor("#fce4ec")),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1,0.3*cm))

    foot = ParagraphStyle("f",fontSize=8,textColor=colors.grey,alignment=TA_CENTER)
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}  |  {settings.get('dairy_name','')}",
        foot))
    doc.build(story)
    return filepath
