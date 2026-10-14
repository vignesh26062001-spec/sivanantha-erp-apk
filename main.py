import os
import csv
import shutil
import sqlite3
import urllib.parse
from datetime import datetime
import flet as ft

DB_NAME = "sivanantha_erp_pro.db"


class ERPDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_schema()

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_schema(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS designs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_code TEXT UNIQUE NOT NULL,
                    quality_name TEXT NOT NULL,
                    hsn_code TEXT DEFAULT '5208',
                    warp_count TEXT,
                    weft_count TEXT,
                    reed INTEGER DEFAULT 0,
                    pick INTEGER DEFAULT 0,
                    width_inch REAL DEFAULT 0.0,
                    glm REAL DEFAULT 0.0,
                    coolie_rate REAL DEFAULT 0.0,
                    sale_rate REAL DEFAULT 0.0,
                    fabric_stock_mtrs REAL DEFAULT 0.0
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT UNIQUE NOT NULL,
                    party_type TEXT NOT NULL,
                    gstin TEXT,
                    state_name TEXT DEFAULT '33-Tamil Nadu',
                    phone TEXT,
                    address TEXT,
                    balance REAL DEFAULT 0.0
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS weavers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    looms INTEGER DEFAULT 1,
                    loom_type TEXT DEFAULT 'Powerloom',
                    yarn_balance_kg REAL DEFAULT 0.0,
                    advance_balance REAL DEFAULT 0.0,
                    coolie_payable REAL DEFAULT 0.0
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pur_date TEXT NOT NULL,
                    bill_no TEXT NOT NULL,
                    supplier_name TEXT NOT NULL,
                    supplier_gstin TEXT,
                    item_desc TEXT NOT NULL,
                    hsn_code TEXT DEFAULT '5205',
                    lot_no TEXT,
                    bags INTEGER DEFAULT 1,
                    weight_kg REAL NOT NULL,
                    rate_kg REAL NOT NULL,
                    taxable_amt REAL NOT NULL,
                    gst_type TEXT NOT NULL,
                    gst_rate REAL DEFAULT 5.0,
                    cgst_amt REAL DEFAULT 0.0,
                    sgst_amt REAL DEFAULT 0.0,
                    igst_amt REAL DEFAULT 0.0,
                    net_amt REAL NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS godown_stock (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    yarn_stock_kg REAL DEFAULT 0.0
                )
            """)
            c.execute("INSERT OR IGNORE INTO godown_stock (id, yarn_stock_kg) VALUES (1, 0.0)")
            c.execute("""
                CREATE TABLE IF NOT EXISTS yarn_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_date TEXT NOT NULL,
                    challan_no TEXT,
                    weaver_name TEXT NOT NULL,
                    design_code TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    ref_no TEXT,
                    weight_kg REAL NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS grey_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_date TEXT NOT NULL,
                    weaver_name TEXT NOT NULL,
                    design_code TEXT NOT NULL,
                    taka_count INTEGER DEFAULT 1,
                    meters REAL NOT NULL,
                    cloth_weight_kg REAL NOT NULL,
                    wastage_kg REAL DEFAULT 0.0,
                    coolie_rate REAL NOT NULL,
                    gross_coolie REAL NOT NULL,
                    advance_deducted REAL DEFAULT 0.0,
                    net_coolie REAL NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS sales_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inv_date TEXT NOT NULL,
                    inv_no TEXT UNIQUE NOT NULL,
                    buyer_name TEXT NOT NULL,
                    buyer_gstin TEXT,
                    design_code TEXT NOT NULL,
                    hsn_code TEXT DEFAULT '5208',
                    taka INTEGER DEFAULT 1,
                    meters REAL NOT NULL,
                    rate REAL NOT NULL,
                    discount_amt REAL DEFAULT 0.0,
                    taxable_amt REAL NOT NULL,
                    gst_type TEXT NOT NULL,
                    gst_rate REAL DEFAULT 5.0,
                    cgst_amt REAL DEFAULT 0.0,
                    sgst_amt REAL DEFAULT 0.0,
                    igst_amt REAL DEFAULT 0.0,
                    net_amt REAL NOT NULL,
                    transport_name TEXT,
                    lr_no TEXT,
                    eway_bill TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    v_date TEXT NOT NULL,
                    v_type TEXT NOT NULL,
                    account_head TEXT NOT NULL,
                    payment_mode TEXT NOT NULL,
                    ref_no TEXT,
                    credit_in REAL DEFAULT 0.0,
                    debit_out REAL DEFAULT 0.0,
                    narration TEXT
                )
            """)
            conn.commit()


def main(page: ft.Page):
    page.title = "Sivanantha Export Fabs - ERP Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f1f5f9"
    page.padding = 0

    # Resolve writable local storage directory for Android & Windows
    storage_dir = os.environ.get("FLET_APP_STORAGE_DATA") or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(storage_dir, exist_ok=True)
    db_path = os.path.join(storage_dir, DB_NAME)
    db = ERPDatabase(db_path)

    def notify(msg: str, err: bool = False):
        sb = ft.SnackBar(
            content=ft.Text(msg, color="#ffffff", weight=ft.FontWeight.BOLD),
            bgcolor="#dc2626" if err else "#059669",
            duration=2500,
        )
        page.snack_bar = sb
        sb.open = True
        page.update()

    def show_modal_slip(title: str, body_text: str, wa_text: str):
        def close_dlg(e):
            dlg.open = False
            page.update()

        def share_wa(e):
            encoded = urllib.parse.quote(wa_text)
            page.launch_url(f"https://wa.me/?text={encoded}")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD, size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(body_text, font_family="monospace", size=12, selectable=True),
                ], scroll=ft.ScrollMode.AUTO, tight=True),
                padding=10,
                bgcolor="#f8fafc",
                border_radius=8,
                border=ft.border.all(1, "#cbd5e1"),
            ),
            actions=[
                ft.ElevatedButton("Share on WhatsApp", bgcolor="#16a34a", color="#ffffff", on_click=share_wa),
                ft.TextButton("Close", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def card_box(controls_list):
        return ft.Container(
            content=ft.Column(controls_list, spacing=8),
            bgcolor="#ffffff",
            padding=12,
            border_radius=10,
            border=ft.border.all(1, "#cbd5e1"),
        )

    def kpi_tile(label: str, value_text: ft.Text):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=11, color="#64748b", weight=ft.FontWeight.BOLD),
                value_text,
            ], spacing=2),
            bgcolor="#ffffff",
            padding=10,
            border_radius=9,
            border=ft.border.all(1, "#cbd5e1"),
            col={"xs": 6, "sm": 6, "md": 3},
        )

    # =========================================================================
    # MODULE 1: EXECUTIVE DASHBOARD
    # =========================================================================
    kv_gyarn = ft.Text("0.00 kg", size=15, weight=ft.FontWeight.BOLD, color="#0284c7")
    kv_wyarn = ft.Text("0.00 kg", size=15, weight=ft.FontWeight.BOLD, color="#d97706")
    kv_fstock = ft.Text("0.00 m", size=15, weight=ft.FontWeight.BOLD, color="#059669")
    kv_coolie = ft.Text("₹ 0.00", size=15, weight=ft.FontWeight.BOLD, color="#dc2626")
    kv_sales = ft.Text("₹ 0.00", size=15, weight=ft.FontWeight.BOLD, color="#4f46e5")
    kv_pur = ft.Text("₹ 0.00", size=15, weight=ft.FontWeight.BOLD, color="#7c3aed")
    kv_rec = ft.Text("₹ 0.00", size=15, weight=ft.FontWeight.BOLD, color="#16a34a")
    kv_pay = ft.Text("₹ 0.00", size=15, weight=ft.FontWeight.BOLD, color="#e11d48")

    dash_design_col = ft.Column(spacing=6)
    dash_weaver_col = ft.Column(spacing=6)

    def load_dashboard(e=None):
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT yarn_stock_kg FROM godown_stock WHERE id=1")
            g_yarn = c.fetchone()[0] or 0.0
            c.execute("SELECT IFNULL(SUM(yarn_balance_kg),0), IFNULL(SUM(coolie_payable),0) FROM weavers")
            w_yarn, w_coolie = c.fetchone()
            c.execute("SELECT IFNULL(SUM(fabric_stock_mtrs),0) FROM designs")
            f_stock = c.fetchone()[0]
            c.execute("SELECT IFNULL(SUM(net_amt),0) FROM sales_invoices")
            t_sales = c.fetchone()[0]
            c.execute("SELECT IFNULL(SUM(net_amt),0) FROM purchases")
            t_pur = c.fetchone()[0]
            c.execute("SELECT IFNULL(SUM(balance),0) FROM parties WHERE balance > 0")
            rec = c.fetchone()[0]
            c.execute("SELECT IFNULL(SUM(ABS(balance)),0) FROM parties WHERE balance < 0")
            pay = c.fetchone()[0]

            kv_gyarn.value = f"{g_yarn:,.2f} kg"
            kv_wyarn.value = f"{w_yarn:,.2f} kg"
            kv_fstock.value = f"{f_stock:,.2f} m"
            kv_coolie.value = f"₹ {w_coolie:,.2f}"
            kv_sales.value = f"₹ {t_sales:,.2f}"
            kv_pur.value = f"₹ {t_pur:,.2f}"
            kv_rec.value = f"₹ {rec:,.2f}"
            kv_pay.value = f"₹ {pay:,.2f}"

            dash_design_col.controls.clear()
            c.execute("SELECT design_code, quality_name, glm, coolie_rate, sale_rate, fabric_stock_mtrs FROM designs ORDER BY design_code")
            for r in c.fetchall():
                stock_val = r[5] * r[4]
                dash_design_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{r[0]} - {r[1]}", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"GLM: {r[2]:.1f}g | Coolie: ₹{r[3]:.2f} | Sale: ₹{r[4]:.2f}/m", size=11, color="#475569"),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"{r[5]:,.2f} m", weight=ft.FontWeight.BOLD, size=13, color="#059669"),
                                ft.Text(f"Val: ₹{stock_val:,.0f}", size=10, color="#64748b"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            dash_weaver_col.controls.clear()
            c.execute("SELECT name, looms, loom_type, yarn_balance_kg, advance_balance, coolie_payable FROM weavers ORDER BY name")
            for r in c.fetchall():
                dash_weaver_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"{r[0]} ({r[1]} {r[2]})", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"Coolie Due: ₹ {r[5]:,.2f}", weight=ft.FontWeight.BOLD, size=13, color="#dc2626"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"Yarn with Weaver: {r[3]:.2f} kg  |  Advance Pending: ₹ {r[4]:,.2f}", size=11, color="#475569"),
                        ], spacing=3),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )
        page.update()

    view_dashboard = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Executive Mill & Stock Dashboard", size=16, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Refresh", on_click=load_dashboard, bgcolor="#2563eb", color="#ffffff"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ResponsiveRow([
                kpi_tile("Godown Yarn Stock", kv_gyarn),
                kpi_tile("Yarn With Weavers", kv_wyarn),
                kpi_tile("Ready Fabric Stock", kv_fstock),
                kpi_tile("Weaver Coolie Due", kv_coolie),
                kpi_tile("Total GST Sales", kv_sales),
                kpi_tile("Yarn Purchases", kv_pur),
                kpi_tile("Buyer Receivables", kv_rec),
                kpi_tile("Supplier Payables", kv_pay),
            ]),
            ft.Divider(),
            ft.Text("Design-Wise Ready Fabric Stock & Valuation", size=14, weight=ft.FontWeight.BOLD),
            dash_design_col,
            ft.Divider(),
            ft.Text("Weaver Live Production & Ledger Status", size=14, weight=ft.FontWeight.BOLD),
            dash_weaver_col,
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 2: MASTERS (DESIGN MASTER & PARTY MASTER WITH DELETE/EDIT)
    # =========================================================================
    dm_code = ft.TextField(label="Design Code *", dense=True, col=6)
    dm_name = ft.TextField(label="Quality Name *", dense=True, col=6)
    dm_hsn = ft.TextField(label="HSN Code", value="5208", dense=True, col=4)
    dm_warp = ft.TextField(label="Warp Count", dense=True, col=4)
    dm_weft = ft.TextField(label="Weft Count", dense=True, col=4)
    dm_reed = ft.TextField(label="Reed", dense=True, col=4)
    dm_pick = ft.TextField(label="Pick", dense=True, col=4)
    dm_width = ft.TextField(label="Width (In)", dense=True, col=4)
    dm_glm = ft.TextField(label="GLM (g/m)", dense=True, col=4)
    dm_coolie = ft.TextField(label="Coolie/m (₹) *", dense=True, col=4)
    dm_srate = ft.TextField(label="Sale Rate/m (₹)", dense=True, col=4)
    dm_ostock = ft.TextField(label="Opening Stock (Meters)", value="0.0", dense=True, col=12)
    dm_calc_lbl = ft.Text("Enter Warp, Weft, Reed, Pick & Width to calculate GLM & 100m Yarn.", size=11, color="#2563eb")
    dm_list_col = ft.Column(spacing=6)

    def calc_glm_action(e):
        try:
            wc = float(dm_warp.value)
            fc = float(dm_weft.value)
            rd = float(dm_reed.value)
            pk = float(dm_pick.value)
            wd = float(dm_width.value)
            w_glm = ((rd * wd) / (wc * 1693.3)) * 1000 * 1.08
            f_glm = ((pk * wd) / (fc * 1693.3)) * 1000 * 1.08
            tot = w_glm + f_glm
            dm_glm.value = f"{tot:.1f}"
            dm_calc_lbl.value = f"100m Consumption -> Warp: {w_glm/10:.2f} kg | Weft: {f_glm/10:.2f} kg | Total: {tot/10:.2f} kg"
            page.update()
        except ValueError:
            notify("Enter numeric Warp, Weft, Reed, Pick & Width", True)

    def save_design_action(e):
        if not dm_code.value or not dm_name.value:
            notify("Design Code & Quality Name are mandatory", True)
            return
        try:
            with db.connect() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO designs
                    (design_code, quality_name, hsn_code, warp_count, weft_count, reed, pick, width_inch, glm, coolie_rate, sale_rate, fabric_stock_mtrs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dm_code.value.strip().upper(), dm_name.value.strip(), dm_hsn.value.strip() or "5208",
                    dm_warp.value.strip(), dm_weft.value.strip(),
                    int(dm_reed.value or 0), int(dm_pick.value or 0),
                    float(dm_width.value or 0.0), float(dm_glm.value or 0.0),
                    float(dm_coolie.value or 0.0), float(dm_srate.value or 0.0),
                    float(dm_ostock.value or 0.0)
                ))
                conn.commit()
            dm_code.value = ""
            dm_name.value = ""
            sync_all_views()
            notify("Design Saved Successfully!")
        except ValueError:
            notify("Invalid numeric fields in Design form", True)

    def delete_design_record(did: int):
        with db.connect() as conn:
            conn.execute("DELETE FROM designs WHERE id=?", (did,))
            conn.commit()
        sync_all_views()
        notify("Design deleted")

    pm_name = ft.TextField(label="Party / Mill Name *", dense=True, col=12)
    pm_type = ft.Dropdown(
        label="Category *", dense=True, col=6, value="Buyer (Fabric Customer)",
        options=[
            ft.dropdown.Option("Buyer (Fabric Customer)"),
            ft.dropdown.Option("Yarn Supplier / Mill"),
            ft.dropdown.Option("Sizing / Warping Mill"),
            ft.dropdown.Option("Process / Dyeing House"),
        ]
    )
    pm_gstin = ft.TextField(label="15-Digit GSTIN", dense=True, col=6)
    pm_state = ft.Dropdown(
        label="State Code", dense=True, col=6, value="33-Tamil Nadu",
        options=[
            ft.dropdown.Option("33-Tamil Nadu"),
            ft.dropdown.Option("29-Karnataka"),
            ft.dropdown.Option("27-Maharashtra"),
            ft.dropdown.Option("24-Gujarat"),
            ft.dropdown.Option("32-Kerala"),
            ft.dropdown.Option("07-Delhi"),
            ft.dropdown.Option("19-West Bengal"),
        ]
    )
    pm_phone = ft.TextField(label="Phone / Mobile", dense=True, col=6)
    pm_addr = ft.TextField(label="City / Address", dense=True, col=6)
    pm_bal = ft.TextField(label="Opening Bal (₹) [+Rec / -Pay]", value="0.0", dense=True, col=6)
    pm_list_col = ft.Column(spacing=6)

    def save_party_action(e):
        if not pm_name.value:
            notify("Party Name is required", True)
            return
        try:
            with db.connect() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO parties (party_name, party_type, gstin, state_name, phone, address, balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pm_name.value.strip(), pm_type.value, (pm_gstin.value or "").strip().upper(),
                    pm_state.value, (pm_phone.value or "").strip(), (pm_addr.value or "").strip(),
                    float(pm_bal.value or 0.0)
                ))
                conn.commit()
            pm_name.value = ""
            pm_gstin.value = ""
            sync_all_views()
            notify("Party Saved to Master!")
        except ValueError:
            notify("Opening Balance must be numeric", True)

    def delete_party_record(pid: int):
        with db.connect() as conn:
            conn.execute("DELETE FROM parties WHERE id=?", (pid,))
            conn.commit()
        sync_all_views()
        notify("Party removed")

    view_masters = ft.Container(
        content=ft.Column([
            ft.Text("1. Fabric Design & Quality Master", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([dm_code, dm_name, dm_hsn, dm_warp, dm_weft, dm_reed, dm_pick, dm_width, dm_glm, dm_coolie, dm_srate, dm_ostock]),
                dm_calc_lbl,
                ft.Row([
                    ft.ElevatedButton("Calculate GLM & Yarn", on_click=calc_glm_action, bgcolor="#7c3aed", color="#ffffff"),
                    ft.ElevatedButton("Save / Update Design", on_click=save_design_action, bgcolor="#2563eb", color="#ffffff"),
                ]),
            ]),
            ft.Text("Saved Designs (Tap Delete to Remove)", size=13, weight=ft.FontWeight.BOLD),
            dm_list_col,
            ft.Divider(),
            ft.Text("2. Buyer & Yarn Supplier Party Master", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([pm_name, pm_type, pm_gstin, pm_state, pm_phone, pm_addr, pm_bal]),
                ft.ElevatedButton("Save / Update Party", on_click=save_party_action, bgcolor="#059669", color="#ffffff"),
            ]),
            ft.Text("Registered Parties & Closing Balances", size=13, weight=ft.FontWeight.BOLD),
            pm_list_col,
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 3: PURCHASE MANAGEMENT (YARN & BEAM INWARD + ITC)
    # =========================================================================
    pu_bill = ft.TextField(label="Supplier Bill No *", dense=True, col=6)
    pu_supp = ft.Dropdown(label="Select Supplier *", dense=True, col=6)
    pu_gstin = ft.TextField(label="Supplier GSTIN", dense=True, col=6)
    pu_item = ft.TextField(label="Yarn Count / Item Desc *", value="40s Combed Cotton Yarn", dense=True, col=6)
    pu_hsn = ft.TextField(label="HSN Code", value="5205", dense=True, col=4)
    pu_lot = ft.TextField(label="Mill Lot No", dense=True, col=4)
    pu_bags = ft.TextField(label="Bags / Beams", value="10", dense=True, col=4)
    pu_wt = ft.TextField(label="Net Weight (kg) *", dense=True, col=6)
    pu_rate = ft.TextField(label="Rate / kg (₹) *", dense=True, col=6)
    pu_ttype = ft.Dropdown(
        label="Tax Type", dense=True, col=6, value="Intra-State (CGST + SGST)",
        options=[
            ft.dropdown.Option("Intra-State (CGST + SGST)"),
            ft.dropdown.Option("Inter-State (IGST)"),
        ]
    )
    pu_grate = ft.Dropdown(
        label="GST %", dense=True, col=6, value="5.0",
        options=[ft.dropdown.Option("5.0"), ft.dropdown.Option("12.0"), ft.dropdown.Option("18.0")]
    )
    pu_list_col = ft.Column(spacing=6)

    def on_pu_supp_change(e):
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT gstin, state_name FROM parties WHERE party_name=?", (pu_supp.value,))
            r = c.fetchone()
            if r:
                pu_gstin.value = r[0] or ""
                pu_ttype.value = "Inter-State (IGST)" if (r[1] and not r[1].startswith("33")) else "Intra-State (CGST + SGST)"
                page.update()

    pu_supp.on_change = on_pu_supp_change

    def save_purchase_action(e):
        try:
            bags = int(pu_bags.value or 1)
            wt = float(pu_wt.value)
            rate = float(pu_rate.value)
            grate = float(pu_grate.value)
            if not pu_bill.value or not pu_supp.value or wt <= 0:
                raise ValueError
        except (ValueError, TypeError):
            notify("Fill Bill No, Supplier, Weight (kg) & Rate", True)
            return

        taxable = wt * rate
        tot_gst = taxable * (grate / 100.0)
        cgst = tot_gst / 2.0 if "Intra" in pu_ttype.value else 0.0
        sgst = tot_gst / 2.0 if "Intra" in pu_ttype.value else 0.0
        igst = tot_gst if "Inter" in pu_ttype.value else 0.0
        net = round(taxable + tot_gst, 2)
        dt = datetime.now().strftime("%Y-%m-%d")

        with db.connect() as conn:
            conn.execute("""
                INSERT INTO purchases
                (pur_date, bill_no, supplier_name, supplier_gstin, item_desc, hsn_code, lot_no, bags, weight_kg, rate_kg, taxable_amt, gst_type, gst_rate, cgst_amt, sgst_amt, igst_amt, net_amt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dt, pu_bill.value.strip(), pu_supp.value, (pu_gstin.value or "").strip().upper(),
                pu_item.value.strip(), pu_hsn.value.strip() or "5205", (pu_lot.value or "").strip(),
                bags, wt, rate, taxable, pu_ttype.value, grate, cgst, sgst, igst, net
            ))
            conn.execute("UPDATE godown_stock SET yarn_stock_kg = yarn_stock_kg + ? WHERE id = 1", (wt,))
            conn.execute("UPDATE parties SET balance = balance - ? WHERE party_name = ?", (net, pu_supp.value))
            conn.commit()

        pu_bill.value = ""
        pu_wt.value = ""
        sync_all_views()
        notify(f"Purchase Saved! +{wt:.2f} kg added to Godown Stock.")

    view_purchases = ft.Container(
        content=ft.Column([
            ft.Text("Spinning Mill Yarn & Sized Beam Purchase (Inward + ITC)", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([pu_bill, pu_supp, pu_gstin, pu_item, pu_hsn, pu_lot, pu_bags, pu_wt, pu_rate, pu_ttype, pu_grate]),
                ft.ElevatedButton("Record Purchase & Add Godown Yarn Stock", on_click=save_purchase_action, bgcolor="#7c3aed", color="#ffffff"),
            ]),
            ft.Text("Purchase ITC Register (Recent Bills)", size=14, weight=ft.FontWeight.BOLD),
            pu_list_col,
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 4: WEAVER'S MANAGEMENT (GREY INWARD, YARN ISSUE & WEAVER MASTER)
    # =========================================================================
    gr_weaver = ft.Dropdown(label="Select Weaver *", dense=True, col=6)
    gr_design = ft.Dropdown(label="Design Code *", dense=True, col=6)
    gr_taka = ft.TextField(label="Taka / Rolls", value="1", dense=True, col=4)
    gr_mtrs = ft.TextField(label="Meters Recd *", dense=True, col=4)
    gr_wt = ft.TextField(label="Cloth Wt (kg) *", dense=True, col=4)
    gr_waste = ft.TextField(label="Wastage (kg)", value="0.0", dense=True, col=4)
    gr_rate = ft.TextField(label="Coolie/m (₹) *", dense=True, col=4)
    gr_adv = ft.TextField(label="Adv Deduct (₹)", value="0.0", dense=True, col=4)
    gr_expected_lbl = ft.Text("Expected Weight check will appear when Design & Meters are entered.", size=11, color="#0284c7")
    gr_list_col = ft.Column(spacing=6)

    def update_grey_helper(e=None):
        if not gr_design.value:
            return
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT coolie_rate, glm FROM designs WHERE design_code=?", (gr_design.value,))
            r = c.fetchone()
            if r:
                if not gr_rate.value:
                    gr_rate.value = str(r[0])
                try:
                    m = float(gr_mtrs.value or 0)
                    exp_kg = (m * r[1]) / 1000.0
                    gr_expected_lbl.value = f"Design GLM: {r[1]:.1f}g/m -> Expected Cloth Weight for {m:.1f}m = {exp_kg:.2f} kg"
                except ValueError:
                    pass
                page.update()

    gr_design.on_change = update_grey_helper
    gr_mtrs.on_change = update_grey_helper

    def save_grey_inward_action(e):
        try:
            taka = int(gr_taka.value or 1)
            mtrs = float(gr_mtrs.value)
            wt = float(gr_wt.value)
            waste = float(gr_waste.value or 0.0)
            rate = float(gr_rate.value)
            adv = float(gr_adv.value or 0.0)
            if not gr_weaver.value or not gr_design.value or mtrs <= 0:
                raise ValueError
        except (ValueError, TypeError):
            notify("Fill Weaver, Design, Meters, Weight & Coolie Rate", True)
            return

        gross = round(mtrs * rate, 2)
        net = round(gross - adv, 2)
        dt = datetime.now().strftime("%Y-%m-%d")

        with db.connect() as conn:
            conn.execute("""
                INSERT INTO grey_receipts
                (receipt_date, weaver_name, design_code, taka_count, meters, cloth_weight_kg, wastage_kg, coolie_rate, gross_coolie, advance_deducted, net_coolie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dt, gr_weaver.value, gr_design.value, taka, mtrs, wt, waste, rate, gross, adv, net))
            conn.execute("""
                UPDATE weavers
                SET yarn_balance_kg = yarn_balance_kg - ?,
                    advance_balance = advance_balance - ?,
                    coolie_payable = coolie_payable + ?
                WHERE name = ?
            """, (wt + waste, adv, net, gr_weaver.value))
            conn.execute("UPDATE designs SET fabric_stock_mtrs = fabric_stock_mtrs + ? WHERE design_code = ?", (mtrs, gr_design.value))
            conn.commit()

        gr_mtrs.value = ""
        gr_wt.value = ""
        sync_all_views()
        notify(f"Grey Received! +{mtrs:.1f}m Stock | Net Coolie: ₹{net:,.2f}")

    # Yarn / Beam Issue Controls
    yi_challan = ft.TextField(label="Challan No *", value="DC-101", dense=True, col=4)
    yi_weaver = ft.Dropdown(label="Select Weaver *", dense=True, col=8)
    yi_design = ft.Dropdown(label="Design Code *", dense=True, col=6)
    yi_type = ft.Dropdown(
        label="Issue Type", dense=True, col=6, value="Sized Warp Beam",
        options=[
            ft.dropdown.Option("Sized Warp Beam"),
            ft.dropdown.Option("Weft Yarn Cones"),
            ft.dropdown.Option("Selvedge Yarn"),
        ]
    )
    yi_ref = ft.TextField(label="Beam / Bag Ref No", dense=True, col=6)
    yi_wt = ft.TextField(label="Net Weight (kg) *", dense=True, col=6)
    yi_list_col = ft.Column(spacing=6)

    def save_yarn_issue_action(e):
        try:
            wt = float(yi_wt.value)
            if not yi_weaver.value or not yi_design.value or wt <= 0:
                raise ValueError
        except (ValueError, TypeError):
            notify("Select Weaver, Design & positive Weight (kg)", True)
            return

        dt = datetime.now().strftime("%Y-%m-%d")
        with db.connect() as conn:
            conn.execute("""
                INSERT INTO yarn_issues (issue_date, challan_no, weaver_name, design_code, issue_type, ref_no, weight_kg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dt, yi_challan.value.strip(), yi_weaver.value, yi_design.value, yi_type.value, (yi_ref.value or "").strip(), wt))
            conn.execute("UPDATE godown_stock SET yarn_stock_kg = yarn_stock_kg - ? WHERE id = 1", (wt,))
            conn.execute("UPDATE weavers SET yarn_balance_kg = yarn_balance_kg + ? WHERE name = ?", (wt, yi_weaver.value))
            conn.commit()

        yi_wt.value = ""
        sync_all_views()
        notify(f"Issued {wt:.2f} kg to {yi_weaver.value}")

    # Weaver Master Controls
    wm_name = ft.TextField(label="Weaver Name *", dense=True, col=6)
    wm_phone = ft.TextField(label="Mobile No", dense=True, col=6)
    wm_looms = ft.TextField(label="No. of Looms", value="4", dense=True, col=6)
    wm_type = ft.Dropdown(
        label="Loom Type", dense=True, col=6, value="Powerloom",
        options=[
            ft.dropdown.Option("Powerloom"),
            ft.dropdown.Option("Auto Loom"),
            ft.dropdown.Option("Rapier"),
            ft.dropdown.Option("Airjet"),
        ]
    )
    wm_yarn = ft.TextField(label="Opening Yarn (kg)", value="0.0", dense=True, col=6)
    wm_adv = ft.TextField(label="Opening Advance (₹)", value="0.0", dense=True, col=6)

    def save_weaver_action(e):
        if not wm_name.value:
            notify("Weaver Name is mandatory", True)
            return
        try:
            with db.connect() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO weavers (name, phone, looms, loom_type, yarn_balance_kg, advance_balance)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    wm_name.value.strip(), (wm_phone.value or "").strip(),
                    int(wm_looms.value or 1), wm_type.value,
                    float(wm_yarn.value or 0.0), float(wm_adv.value or 0.0)
                ))
                conn.commit()
            wm_name.value = ""
            sync_all_views()
            notify("Weaver Saved to Master!")
        except ValueError:
            notify("Check numeric fields in Weaver form", True)

    view_weavers = ft.Container(
        content=ft.Column([
            ft.Text("1. Grey Cloth Inward & Coolie Calculation", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([gr_weaver, gr_design, gr_taka, gr_mtrs, gr_wt, gr_waste, gr_rate, gr_adv]),
                gr_expected_lbl,
                ft.ElevatedButton("Save Grey Inward & Generate Coolie Slip", on_click=save_grey_inward_action, bgcolor="#059669", color="#ffffff"),
            ]),
            ft.Text("Recent Grey Cloth Slips (Tap 'Slip / WA' to View & Share)", size=13, weight=ft.FontWeight.BOLD),
            gr_list_col,
            ft.Divider(),
            ft.Text("2. Yarn / Sized Beam Outward Challan", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([yi_challan, yi_weaver, yi_design, yi_type, yi_ref, yi_wt]),
                ft.ElevatedButton("Issue Yarn / Beam (Deducts Godown Stock)", on_click=save_yarn_issue_action, bgcolor="#2563eb", color="#ffffff"),
            ]),
            ft.Text("Recent Yarn Issue Challans", size=13, weight=ft.FontWeight.BOLD),
            yi_list_col,
            ft.Divider(),
            ft.Text("3. Add / Update Weaver Master", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([wm_name, wm_phone, wm_looms, wm_type, wm_yarn, wm_adv]),
                ft.ElevatedButton("Save Weaver", on_click=save_weaver_action, bgcolor="#0f172a", color="#ffffff"),
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 5: GST SALES & DISPATCH (TAX INVOICE, E-WAY BILL, LR NO)
    # =========================================================================
    sl_inv = ft.TextField(label="Invoice No *", value="SEF/26-27/001", dense=True, col=6)
    sl_buyer = ft.Dropdown(label="Select Buyer *", dense=True, col=6)
    sl_gstin = ft.TextField(label="Buyer GSTIN", dense=True, col=6)
    sl_design = ft.Dropdown(label="Design Code *", dense=True, col=6)
    sl_hsn = ft.TextField(label="HSN", value="5208", dense=True, col=4)
    sl_taka = ft.TextField(label="Bales / Taka", value="5", dense=True, col=4)
    sl_mtrs = ft.TextField(label="Total Meters *", dense=True, col=4)
    sl_rate = ft.TextField(label="Sale Rate/m (₹) *", dense=True, col=4)
    sl_disc = ft.TextField(label="Discount (₹)", value="0.0", dense=True, col=4)
    sl_grate = ft.Dropdown(
        label="GST %", dense=True, col=4, value="5.0",
        options=[ft.dropdown.Option("5.0"), ft.dropdown.Option("12.0"), ft.dropdown.Option("18.0")]
    )
    sl_ttype = ft.Dropdown(
        label="GST Type", dense=True, col=6, value="Intra-State (CGST + SGST)",
        options=[
            ft.dropdown.Option("Intra-State (CGST + SGST)"),
            ft.dropdown.Option("Inter-State (IGST)"),
        ]
    )
    sl_trans = ft.TextField(label="Transport Name", dense=True, col=6)
    sl_lr = ft.TextField(label="LR Number", dense=True, col=6)
    sl_eway = ft.TextField(label="E-Way Bill No", dense=True, col=6)
    sl_stock_hint = ft.Text("Select Design to see available fabric stock.", size=11, color="#059669")
    sl_list_col = ft.Column(spacing=6)

    def on_sl_buyer_change(e):
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT gstin, state_name FROM parties WHERE party_name=?", (sl_buyer.value,))
            r = c.fetchone()
            if r:
                sl_gstin.value = r[0] or ""
                sl_ttype.value = "Inter-State (IGST)" if (r[1] and not r[1].startswith("33")) else "Intra-State (CGST + SGST)"
                page.update()

    def on_sl_design_change(e):
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT hsn_code, sale_rate, fabric_stock_mtrs FROM designs WHERE design_code=?", (sl_design.value,))
            r = c.fetchone()
            if r:
                sl_hsn.value = r[0] or "5208"
                sl_rate.value = str(r[1] or 0.0)
                sl_stock_hint.value = f"Available Ready Stock for {sl_design.value}: {r[2]:,.2f} Meters"
                page.update()

    sl_buyer.on_change = on_sl_buyer_change
    sl_design.on_change = on_sl_design_change

    def save_sales_action(e):
        try:
            taka = int(sl_taka.value or 1)
            mtrs = float(sl_mtrs.value)
            rate = float(sl_rate.value)
            disc = float(sl_disc.value or 0.0)
            grate = float(sl_grate.value)
            if not sl_inv.value or not sl_buyer.value or not sl_design.value or mtrs <= 0:
                raise ValueError
        except (ValueError, TypeError):
            notify("Fill Invoice No, Buyer, Design, Meters & Rate", True)
            return

        taxable = round((mtrs * rate) - disc, 2)
        tot_gst = round(taxable * (grate / 100.0), 2)
        cgst = round(tot_gst / 2.0, 2) if "Intra" in sl_ttype.value else 0.0
        sgst = round(tot_gst / 2.0, 2) if "Intra" in sl_ttype.value else 0.0
        igst = tot_gst if "Inter" in sl_ttype.value else 0.0
        net = round(taxable + tot_gst, 2)
        dt = datetime.now().strftime("%Y-%m-%d")

        try:
            with db.connect() as conn:
                conn.execute("""
                    INSERT INTO sales_invoices
                    (inv_date, inv_no, buyer_name, buyer_gstin, design_code, hsn_code, taka, meters, rate, discount_amt, taxable_amt, gst_type, gst_rate, cgst_amt, sgst_amt, igst_amt, net_amt, transport_name, lr_no, eway_bill)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dt, sl_inv.value.strip(), sl_buyer.value, (sl_gstin.value or "").strip().upper(),
                    sl_design.value, sl_hsn.value.strip() or "5208", taka, mtrs, rate, disc, taxable,
                    sl_ttype.value, grate, cgst, sgst, igst, net,
                    (sl_trans.value or "").strip(), (sl_lr.value or "").strip(), (sl_eway.value or "").strip()
                ))
                conn.execute("UPDATE designs SET fabric_stock_mtrs = fabric_stock_mtrs - ? WHERE design_code = ?", (mtrs, sl_design.value))
                conn.execute("UPDATE parties SET balance = balance + ? WHERE party_name = ?", (net, sl_buyer.value))
                conn.commit()
            sl_mtrs.value = ""
            sync_all_views()
            notify(f"GST Invoice {sl_inv.value} Saved! Total: ₹{net:,.2f}")
        except sqlite3.IntegrityError:
            notify(f"Invoice No '{sl_inv.value}' already exists!", True)

    view_sales = ft.Container(
        content=ft.Column([
            ft.Text("GST Sales Tax Invoice & Dispatch Entry", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([sl_inv, sl_buyer, sl_gstin, sl_design, sl_hsn, sl_taka, sl_mtrs, sl_rate, sl_disc, sl_grate, sl_ttype, sl_trans, sl_lr, sl_eway]),
                sl_stock_hint,
                ft.ElevatedButton("Generate GST Invoice & Deduct Fabric Stock", on_click=save_sales_action, bgcolor="#2563eb", color="#ffffff"),
            ]),
            ft.Text("Issued GST Invoices (Tap 'Invoice / WA' to View & Share)", size=13, weight=ft.FontWeight.BOLD),
            sl_list_col,
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 6: ACCOUNTS, VOUCHERS & INDIVIDUAL PARTY/WEAVER LEDGER VIEWER
    # =========================================================================
    ac_vtype = ft.Dropdown(
        label="Voucher Type *", dense=True, col=12, value="Buyer Payment Received (In)",
        options=[
            ft.dropdown.Option("Buyer Payment Received (In)"),
            ft.dropdown.Option("Supplier Payment Made (Out)"),
            ft.dropdown.Option("Weaver Coolie Paid (Out)"),
            ft.dropdown.Option("Weaver Advance Given (Out)"),
            ft.dropdown.Option("Mill / Sizing Expense (Out)"),
        ]
    )
    ac_party = ft.Dropdown(label="Select Party / Weaver *", dense=True, col=6)
    ac_mode = ft.Dropdown(
        label="Payment Mode", dense=True, col=6, value="NEFT / RTGS / IMPS",
        options=[
            ft.dropdown.Option("NEFT / RTGS / IMPS"),
            ft.dropdown.Option("UPI / GPay"),
            ft.dropdown.Option("Cheque"),
            ft.dropdown.Option("Cash"),
        ]
    )
    ac_amt = ft.TextField(label="Amount (₹) *", dense=True, col=6)
    ac_ref = ft.TextField(label="UTR / Cheque / Ref No", dense=True, col=6)
    ac_narr = ft.TextField(label="Narration / Notes", dense=True, col=12)

    def save_voucher_action(e):
        try:
            amt = float(ac_amt.value)
            if not ac_party.value or amt <= 0:
                raise ValueError
        except (ValueError, TypeError):
            notify("Select Account/Party and enter positive Amount", True)
            return

        vt = ac_vtype.value
        c_in = amt if "(In)" in vt else 0.0
        d_out = amt if "(Out)" in vt else 0.0
        dt = datetime.now().strftime("%Y-%m-%d")

        with db.connect() as conn:
            conn.execute("""
                INSERT INTO vouchers (v_date, v_type, account_head, payment_mode, ref_no, credit_in, debit_out, narration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (dt, vt, ac_party.value, ac_mode.value, (ac_ref.value or "").strip(), c_in, d_out, (ac_narr.value or "").strip()))

            if vt == "Buyer Payment Received (In)":
                conn.execute("UPDATE parties SET balance = balance - ? WHERE party_name = ?", (amt, ac_party.value))
            elif vt == "Supplier Payment Made (Out)":
                conn.execute("UPDATE parties SET balance = balance + ? WHERE party_name = ?", (amt, ac_party.value))
            elif vt == "Weaver Coolie Paid (Out)":
                conn.execute("UPDATE weavers SET coolie_payable = coolie_payable - ? WHERE name = ?", (amt, ac_party.value))
            elif vt == "Weaver Advance Given (Out)":
                conn.execute("UPDATE weavers SET advance_balance = advance_balance + ? WHERE name = ?", (amt, ac_party.value))
            conn.commit()

        ac_amt.value = ""
        ac_ref.value = ""
        ac_narr.value = ""
        sync_all_views()
        notify(f"Voucher Posted: ₹{amt:,.2f} for {ac_party.value}")

    # Individual Statement Viewer
    st_select = ft.Dropdown(label="Select Weaver or Party to View Full Ledger Statement", dense=True, col=12)
    st_summary_txt = ft.Text("Select an account above to load statement.", weight=ft.FontWeight.BOLD, size=13, color="#1e3a8a")
    st_history_col = ft.Column(spacing=5)

    def load_individual_statement(e=None):
        name = st_select.value
        if not name:
            return
        st_history_col.controls.clear()
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT yarn_balance_kg, advance_balance, coolie_payable FROM weavers WHERE name=?", (name,))
            w = c.fetchone()
            c.execute("SELECT party_type, balance FROM parties WHERE party_name=?", (name,))
            p = c.fetchone()

            if w:
                st_summary_txt.value = f"Weaver: {name} | Yarn Stock: {w[0]:.2f} kg | Advance: ₹{w[1]:,.2f} | Coolie Due: ₹{w[2]:,.2f}"
                c.execute("SELECT issue_date, challan_no, design_code, issue_type, weight_kg FROM yarn_issues WHERE weaver_name=? ORDER BY id DESC", (name,))
                for r in c.fetchall():
                    st_history_col.controls.append(ft.Text(f"[YARN ISSUE] {r[0]} | {r[1]} | {r[2]} ({r[3]}): +{r[4]:.2f} kg", size=12, color="#d97706"))
                c.execute("SELECT receipt_date, design_code, meters, cloth_weight_kg, net_coolie FROM grey_receipts WHERE weaver_name=? ORDER BY id DESC", (name,))
                for r in c.fetchall():
                    st_history_col.controls.append(ft.Text(f"[GREY INWARD] {r[0]} | {r[1]} | {r[2]:.1f}m (-{r[3]:.2f}kg) | Net Coolie: +₹{r[4]:,.2f}", size=12, color="#059669"))
            elif p:
                lbl = "Receivable" if p[1] >= 0 else "Payable"
                st_summary_txt.value = f"{p[0]}: {name} | Closing Balance: ₹{abs(p[1]):,.2f} ({lbl})"
                c.execute("SELECT inv_date, inv_no, design_code, meters, net_amt FROM sales_invoices WHERE buyer_name=? ORDER BY id DESC", (name,))
                for r in c.fetchall():
                    st_history_col.controls.append(ft.Text(f"[SALE INVOICE] {r[0]} | {r[1]} | {r[2]} ({r[3]:.1f}m) -> ₹{r[4]:,.2f}", size=12, color="#2563eb"))
                c.execute("SELECT pur_date, bill_no, item_desc, weight_kg, net_amt FROM purchases WHERE supplier_name=? ORDER BY id DESC", (name,))
                for r in c.fetchall():
                    st_history_col.controls.append(ft.Text(f"[PURCHASE BILL] {r[0]} | Bill {r[1]} | {r[2]} ({r[3]:.1f}kg) -> ₹{r[4]:,.2f}", size=12, color="#7c3aed"))

            c.execute("SELECT v_date, v_type, payment_mode, credit_in, debit_out, ref_no FROM vouchers WHERE account_head=? ORDER BY id DESC", (name,))
            for r in c.fetchall():
                amt = r[3] if r[3] > 0 else r[4]
                st_history_col.controls.append(ft.Text(f"[VOUCHER] {r[0]} | {r[1]} ({r[2]} {r[5] or ''}) -> ₹{amt:,.2f}", size=12, color="#dc2626"))
        page.update()

    st_select.on_change = load_individual_statement

    view_accounts = ft.Container(
        content=ft.Column([
            ft.Text("1. Daybook Payment / Receipt Voucher Entry", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([ac_vtype, ac_party, ac_mode, ac_amt, ac_ref, ac_narr]),
                ft.ElevatedButton("Post Voucher & Auto-Update Ledger", on_click=save_voucher_action, bgcolor="#059669", color="#ffffff"),
            ]),
            ft.Divider(),
            ft.Text("2. Individual Weaver & Party Ledger Statement", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                st_select,
                st_summary_txt,
                ft.Divider(),
                st_history_col,
            ]),
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MODULE 7: DATE-RANGE GSTR-1 / ITC REPORTS, CSV EXPORTS & DB BACKUP
    # =========================================================================
    rep_from = ft.TextField(label="From Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-01"), dense=True, col=6)
    rep_to = ft.TextField(label="To Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"), dense=True, col=6)
    rep_cards_col = ft.Column(spacing=8)
    export_status_txt = ft.Text(f"Storage Folder: {storage_dir}", size=11, color="#475569", selectable=True)

    def load_gstr_reports(e=None):
        df = rep_from.value.strip()
        dt = rep_to.value.strip()
        rep_cards_col.controls.clear()
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*), IFNULL(SUM(meters),0), IFNULL(SUM(taxable_amt),0),
                       IFNULL(SUM(cgst_amt),0), IFNULL(SUM(sgst_amt),0), IFNULL(SUM(igst_amt),0), IFNULL(SUM(net_amt),0)
                FROM sales_invoices WHERE inv_date BETWEEN ? AND ?
            """, (df, dt))
            s = c.fetchone()

            c.execute("""
                SELECT COUNT(*), IFNULL(SUM(weight_kg),0), IFNULL(SUM(taxable_amt),0),
                       IFNULL(SUM(cgst_amt),0), IFNULL(SUM(sgst_amt),0), IFNULL(SUM(igst_amt),0), IFNULL(SUM(net_amt),0)
                FROM purchases WHERE pur_date BETWEEN ? AND ?
            """, (df, dt))
            p = c.fetchone()

            out_tax = s[3] + s[4] + s[5]
            in_tax = p[3] + p[4] + p[5]
            net_gst = out_tax - in_tax

            rep_cards_col.controls.extend([
                card_box([
                    ft.Text(f"GSTR-1 Outward Sales ({s[0]} Invoices | {s[1]:,.2f} m)", weight=ft.FontWeight.BOLD, size=14, color="#2563eb"),
                    ft.Text(f"Taxable Value: ₹ {s[2]:,.2f}  |  Total Invoice Value: ₹ {s[6]:,.2f}", size=12),
                    ft.Text(f"Output CGST: ₹{s[3]:,.2f} | SGST: ₹{s[4]:,.2f} | IGST: ₹{s[5]:,.2f}", size=12, weight=ft.FontWeight.BOLD),
                ]),
                card_box([
                    ft.Text(f"GSTR-2 Inward Purchases ITC ({p[0]} Bills | {p[1]:,.2f} kg)", weight=ft.FontWeight.BOLD, size=14, color="#7c3aed"),
                    ft.Text(f"Taxable Value: ₹ {p[2]:,.2f}  |  Total Purchase Value: ₹ {p[6]:,.2f}", size=12),
                    ft.Text(f"Input CGST: ₹{p[3]:,.2f} | SGST: ₹{p[4]:,.2f} | IGST: ₹{p[5]:,.2f}", size=12, weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(
                    content=ft.Column([
                        ft.Text("NET GST LIABILITY (Output Tax minus Input ITC)", weight=ft.FontWeight.BOLD, size=13, color="#991b1b"),
                        ft.Text(f"Output GST (₹{out_tax:,.2f}) - Input ITC (₹{in_tax:,.2f}) = ₹ {net_gst:,.2f}", weight=ft.FontWeight.BOLD, size=15, color="#dc2626"),
                    ]),
                    bgcolor="#fef2f2", padding=12, border_radius=10, border=ft.border.all(1, "#fecaca")
                ),
            ])
        page.update()

    def export_gstr1_action(e):
        df, dt = rep_from.value.strip(), rep_to.value.strip()
        out_path = os.path.join(storage_dir, f"GSTR1_Sales_{df}_to_{dt}.csv")
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT buyer_gstin, buyer_name, inv_no, inv_date, net_amt, hsn_code, gst_rate, meters, taxable_amt, cgst_amt, sgst_amt, igst_amt, eway_bill
                FROM sales_invoices WHERE inv_date BETWEEN ? AND ? ORDER BY inv_date ASC
            """, (df, dt))
            rows = c.fetchall()
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Buyer GSTIN", "Buyer Name", "Invoice No", "Date", "Invoice Value", "HSN", "GST %", "Meters", "Taxable", "CGST", "SGST", "IGST", "E-Way Bill"])
            w.writerows(rows)
        export_status_txt.value = f"Exported GSTR-1 CSV: {out_path}"
        notify(f"Saved {len(rows)} GSTR-1 invoices!")

    def export_gstr2_action(e):
        df, dt = rep_from.value.strip(), rep_to.value.strip()
        out_path = os.path.join(storage_dir, f"GSTR2_ITC_{df}_to_{dt}.csv")
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT supplier_gstin, supplier_name, bill_no, pur_date, item_desc, hsn_code, weight_kg, taxable_amt, gst_rate, cgst_amt, sgst_amt, igst_amt, net_amt
                FROM purchases WHERE pur_date BETWEEN ? AND ? ORDER BY pur_date ASC
            """, (df, dt))
            rows = c.fetchall()
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Supplier GSTIN", "Supplier", "Bill No", "Date", "Yarn Desc", "HSN", "Weight(kg)", "Taxable", "GST %", "CGST", "SGST", "IGST", "Total Bill"])
            w.writerows(rows)
        export_status_txt.value = f"Exported GSTR-2 CSV: {out_path}"
        notify(f"Saved {len(rows)} Purchase ITC bills!")

    def backup_db_action(e):
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        b_path = os.path.join(storage_dir, f"Sivanantha_Backup_{stamp}.db")
        shutil.copy2(db_path, b_path)
        export_status_txt.value = f"Database Backup Saved: {b_path}"
        notify("SQLite Database Backed Up!")

    view_reports = ft.Container(
        content=ft.Column([
            ft.Text("Auditor GST Reports, CSV Exports & DB Backup", size=15, weight=ft.FontWeight.BOLD),
            card_box([
                ft.ResponsiveRow([rep_from, rep_to]),
                ft.ElevatedButton("Filter Date-Range GST Summary", on_click=load_gstr_reports, bgcolor="#0f172a", color="#ffffff"),
            ]),
            rep_cards_col,
            ft.Row([
                ft.ElevatedButton("Export GSTR-1 CSV", on_click=export_gstr1_action, bgcolor="#2563eb", color="#ffffff", expand=True),
                ft.ElevatedButton("Export GSTR-2 ITC", on_click=export_gstr2_action, bgcolor="#7c3aed", color="#ffffff", expand=True),
            ]),
            ft.ElevatedButton("Backup Full SQLite Database (.db)", on_click=backup_db_action, bgcolor="#dc2626", color="#ffffff"),
            export_status_txt,
        ], scroll=ft.ScrollMode.AUTO, spacing=10),
        padding=12, expand=True
    )

    # =========================================================================
    # MASTER SYNCHRONIZATION ACROSS ALL 7 MODULES
    # =========================================================================
    def sync_all_views():
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM weavers ORDER BY name")
            w_opts = [ft.dropdown.Option(r[0]) for r in c.fetchall()]
            gr_weaver.options = w_opts
            yi_weaver.options = w_opts

            c.execute("SELECT design_code FROM designs ORDER BY design_code")
            d_opts = [ft.dropdown.Option(r[0]) for r in c.fetchall()]
            gr_design.options = d_opts
            yi_design.options = d_opts
            sl_design.options = d_opts

            c.execute("SELECT party_name FROM parties ORDER BY party_name")
            p_opts = [ft.dropdown.Option(r[0]) for r in c.fetchall()]
            pu_supp.options = p_opts
            sl_buyer.options = p_opts

            c.execute("SELECT party_name FROM parties UNION SELECT name FROM weavers ORDER BY 1")
            all_opts = [ft.dropdown.Option(r[0]) for r in c.fetchall()]
            ac_party.options = all_opts
            st_select.options = all_opts

            # Design list in Masters
            dm_list_col.controls.clear()
            c.execute("SELECT id, design_code, quality_name, glm, coolie_rate, sale_rate, fabric_stock_mtrs FROM designs ORDER BY design_code")
            for r in c.fetchall():
                did = r[0]
                dm_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{r[1]} - {r[2]}", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"GLM: {r[3]:.1f}g | Coolie: ₹{r[4]:.2f} | Sale: ₹{r[5]:.2f} | Stock: {r[6]:.1f}m", size=11, color="#475569"),
                            ], expand=True),
                            ft.TextButton("Delete", on_click=lambda e, x=did: delete_design_record(x)),
                        ]),
                        bgcolor="#ffffff", padding=8, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            # Party list in Masters
            pm_list_col.controls.clear()
            c.execute("SELECT id, party_name, party_type, gstin, balance FROM parties ORDER BY party_name")
            for r in c.fetchall():
                pid = r[0]
                tag = "Rec" if r[4] >= 0 else "Pay"
                pm_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(r[1], weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{r[2]} | GSTIN: {r[3] or 'N/A'} | Bal: ₹{abs(r[4]):,.2f} ({tag})", size=11, color="#475569"),
                            ], expand=True),
                            ft.TextButton("Delete", on_click=lambda e, x=pid: delete_party_record(x)),
                        ]),
                        bgcolor="#ffffff", padding=8, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            # Purchase list
            pu_list_col.controls.clear()
            c.execute("SELECT pur_date, bill_no, supplier_name, item_desc, weight_kg, net_amt FROM purchases ORDER BY id DESC LIMIT 10")
            for r in c.fetchall():
                pu_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"Bill {r[1]} - {r[2]}", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{r[0]} | {r[3]} ({r[4]:.2f} kg)", size=11, color="#475569"),
                            ], expand=True),
                            ft.Text(f"₹ {r[5]:,.2f}", weight=ft.FontWeight.BOLD, color="#7c3aed"),
                        ]),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            # Grey Cloth list with Native Coolie Slip Modal & WhatsApp Share
            gr_list_col.controls.clear()
            c.execute("SELECT id, receipt_date, weaver_name, design_code, taka_count, meters, cloth_weight_kg, coolie_rate, gross_coolie, advance_deducted, net_coolie FROM grey_receipts ORDER BY id DESC LIMIT 10")
            for r in c.fetchall():
                slip_txt = (
                    f"SIVANANTHA EXPORT FABS - COOLIE SLIP\n"
                    f"Slip No: GR-{r[0]} | Date: {r[1]}\n"
                    f"Weaver: {r[2]}\n"
                    f"Design: {r[3]} | Taka: {r[4]}\n"
                    f"Meters Recd: {r[5]:.2f} m | Cloth Wt: {r[6]:.2f} kg\n"
                    f"Coolie Rate: Rs.{r[7]:.2f}/m\n"
                    f"Gross Coolie: Rs.{r[8]:,.2f}\n"
                    f"Advance Deducted: -Rs.{r[9]:,.2f}\n"
                    f"NET PAYABLE COOLIE: Rs.{r[10]:,.2f}"
                )
                gr_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"GR-{r[0]}: {r[2]} ({r[3]})", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{r[1]} | {r[5]:.2f} m ({r[6]:.2f} kg) | Net: ₹{r[10]:,.2f}", size=11, color="#475569"),
                            ], expand=True),
                            ft.ElevatedButton(
                                "Slip / WA", bgcolor="#059669", color="#ffffff",
                                on_click=lambda e, t=slip_txt: show_modal_slip("Weaver Coolie Slip", t, t)
                            ),
                        ]),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            # Yarn Issue list
            yi_list_col.controls.clear()
            c.execute("SELECT issue_date, challan_no, weaver_name, design_code, issue_type, weight_kg FROM yarn_issues ORDER BY id DESC LIMIT 8")
            for r in c.fetchall():
                yi_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{r[1]} - {r[2]} ({r[3]})", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{r[0]} | {r[4]}", size=11, color="#475569"),
                            ], expand=True),
                            ft.Text(f"{r[5]:.2f} kg", weight=ft.FontWeight.BOLD, color="#d97706"),
                        ]),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

            # Sales Invoices list with Native Invoice Modal & WhatsApp Share
            sl_list_col.controls.clear()
            c.execute("""
                SELECT inv_date, inv_no, buyer_name, buyer_gstin, design_code, hsn_code, taka, meters, rate, taxable_amt, cgst_amt, sgst_amt, igst_amt, net_amt, lr_no, eway_bill
                FROM sales_invoices ORDER BY id DESC LIMIT 10
            """)
            for r in c.fetchall():
                inv_txt = (
                    f"SIVANANTHA EXPORT FABS - TAX INVOICE\n"
                    f"Invoice No: {r[1]} | Date: {r[0]}\n"
                    f"Buyer: {r[2]} (GSTIN: {r[3] or 'Unregistered'})\n"
                    f"Design: {r[4]} (HSN: {r[5]}) | Bales/Taka: {r[6]}\n"
                    f"Quantity: {r[7]:,.2f} m @ Rs.{r[8]:.2f}/m\n"
                    f"Taxable Value: Rs.{r[9]:,.2f}\n"
                    f"CGST: Rs.{r[10]:,.2f} | SGST: Rs.{r[11]:,.2f} | IGST: Rs.{r[12]:,.2f}\n"
                    f"LR No: {r[14] or '-'} | E-Way Bill: {r[15] or '-'}\n"
                    f"GRAND TOTAL: Rs.{r[13]:,.2f}"
                )
                sl_list_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{r[1]} - {r[2]}", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{r[0]} | {r[4]} ({r[7]:.2f} m) | Total: ₹{r[13]:,.2f}", size=11, color="#475569"),
                            ], expand=True),
                            ft.ElevatedButton(
                                "Invoice / WA", bgcolor="#2563eb", color="#ffffff",
                                on_click=lambda e, t=inv_txt: show_modal_slip(f"Tax Invoice {r[1]}", t, t)
                            ),
                        ]),
                        bgcolor="#ffffff", padding=10, border_radius=8, border=ft.border.all(1, "#e2e8f0")
                    )
                )

        load_dashboard()
        load_gstr_reports()

    header_bar = ft.Container(
        content=ft.Column([
            ft.Text("SIVANANTHA EXPORT FABS", color="#38bdf8", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Full-Fledged Native Android ERP & GST Suite", color="#cbd5e1", size=11),
        ], spacing=1),
        bgcolor="#0f172a",
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        width=float("inf"),
    )

    nav_tabs = ft.Tabs(
        selected_index=0,
        scrollable=True,
        animation_duration=200,
        tabs=[
            ft.Tab(text="1. Dashboard", content=view_dashboard),
            ft.Tab(text="2. Weavers", content=view_weavers),
            ft.Tab(text="3. GST Sales", content=view_sales),
            ft.Tab(text="4. Yarn Purchase", content=view_purchases),
            ft.Tab(text="5. Accounts & Ledgers", content=view_accounts),
            ft.Tab(text="6. Masters", content=view_masters),
            ft.Tab(text="7. GSTR & Backup", content=view_reports),
        ],
        expand=True,
    )

    page.add(ft.Column([header_bar, nav_tabs], spacing=0, expand=True))
    sync_all_views()


if __name__ == "__main__":
    ft.app(target=main)