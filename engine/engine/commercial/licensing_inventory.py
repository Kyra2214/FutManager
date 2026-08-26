from datetime import date
import sqlite3
from engine.core.state_store import assert_mutable_state_path
from engine.world.time_and_finance import FinanceLedger, WorldTickContext

SCHEMA = '''
CREATE TABLE IF NOT EXISTS licensing_contracts(contract_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,partner TEXT NOT NULL,total_value INTEGER NOT NULL,periodic_value INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS licensed_products(product_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,name TEXT NOT NULL,segment TEXT NOT NULL,unit_price INTEGER NOT NULL,low_stock_threshold INTEGER NOT NULL DEFAULT 0,UNIQUE(club_id,name));
CREATE TABLE IF NOT EXISTS product_lots(lot_id INTEGER PRIMARY KEY AUTOINCREMENT,product_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity >= 0),unit_cost INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS product_sales(sale_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,product_id INTEGER NOT NULL,lot_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity > 0),unit_price INTEGER NOT NULL,segment TEXT NOT NULL,reference TEXT UNIQUE,status TEXT NOT NULL DEFAULT 'SOLD',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS product_refunds(refund_id INTEGER PRIMARY KEY AUTOINCREMENT,sale_id INTEGER NOT NULL UNIQUE,amount INTEGER NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
'''

class LicensingInventoryService:
    def __init__(self, db):
        if not isinstance(db, sqlite3.Connection): assert_mutable_state_path(db)
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self.ledger = FinanceLedger(self.connection)
        self.connection.commit()

    def preview_contract(self, club_id, partner, total_value, periodic_value, start_date, end_date, reference):
        if min(int(total_value), int(periodic_value)) < 0 or start_date >= end_date or not str(reference).strip(): raise ValueError('LICENSING_CONTRACT_INVALID')
        duplicate = self.connection.execute('SELECT contract_id FROM licensing_contracts WHERE reference=?', (str(reference).strip(),)).fetchone()
        return {'club_id': int(club_id), 'partner': str(partner), 'total_value': int(total_value), 'periodic_value': int(periodic_value), 'duplicate': duplicate is not None, 'persisted': False}

    def approve_contract(self, club_id, partner, total_value, periodic_value, start_date, end_date, reference):
        preview = self.preview_contract(club_id, partner, total_value, periodic_value, start_date, end_date, reference)
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO licensing_contracts(club_id,partner,total_value,periodic_value,start_date,end_date,status,reference) VALUES(?,?,?,?,?,?,?,?)', (club_id, partner, total_value, periodic_value, start_date, end_date, 'APPROVED', str(reference).strip()))
            row = self.connection.execute('SELECT * FROM licensing_contracts WHERE reference=?', (str(reference).strip(),)).fetchone()
        return {'contract_id': int(row['contract_id']), 'status': row['status'], 'preview': preview}

    def add_product(self, club_id, name, segment, unit_price, low_stock_threshold=0):
        if int(unit_price) < 0 or int(low_stock_threshold) < 0: raise ValueError('PRODUCT_INVALID')
        with self.connection:
            self.connection.execute('INSERT INTO licensed_products(club_id,name,segment,unit_price,low_stock_threshold) VALUES(?,?,?,?,?) ON CONFLICT(club_id,name) DO UPDATE SET segment=excluded.segment,unit_price=excluded.unit_price,low_stock_threshold=excluded.low_stock_threshold', (club_id, name, segment, unit_price, low_stock_threshold))
        return dict(self.connection.execute('SELECT * FROM licensed_products WHERE club_id=? AND name=?', (club_id, name)).fetchone())

    def add_lot(self, product_id, quantity, unit_cost=0):
        if int(quantity) < 0 or int(unit_cost) < 0: raise ValueError('PRODUCT_LOT_INVALID')
        with self.connection:
            cur = self.connection.execute('INSERT INTO product_lots(product_id,quantity,unit_cost,created_at) VALUES(?,?,?,?)', (product_id, quantity, unit_cost, date.today().isoformat()))
        return int(cur.lastrowid)

    def sell_lot(self, club_id, product_id, quantity, segment, reference, unit_price=None):
        product = self.connection.execute('SELECT * FROM licensed_products WHERE product_id=? AND club_id=?', (product_id, club_id)).fetchone()
        if not product or int(quantity) <= 0: raise ValueError('PRODUCT_NOT_AVAILABLE')
        lot = self.connection.execute('SELECT * FROM product_lots WHERE product_id=? AND quantity>=? ORDER BY lot_id LIMIT 1', (product_id, quantity)).fetchone()
        if not lot: raise ValueError('STOCK_UNAVAILABLE')
        price = int(product['unit_price'] if unit_price is None else unit_price)
        with self.connection:
            self.connection.execute('UPDATE product_lots SET quantity=quantity-? WHERE lot_id=?', (quantity, lot['lot_id']))
            cur = self.connection.execute('INSERT INTO product_sales(club_id,product_id,lot_id,quantity,unit_price,segment,reference,created_at) VALUES(?,?,?,?,?,?,?,?)', (club_id, product_id, lot['lot_id'], quantity, price, segment, str(reference), date.today().isoformat()))
        return {'sale_id': int(cur.lastrowid), 'quantity': int(quantity), 'revenue': int(quantity) * price, 'persisted': True}

    def refund_sale(self, sale_id, reason):
        sale = self.connection.execute("SELECT * FROM product_sales WHERE sale_id=? AND status='SOLD'", (sale_id,)).fetchone()
        if not sale: raise KeyError(sale_id)
        amount = int(sale['quantity']) * int(sale['unit_price'])
        with self.connection:
            self.connection.execute("UPDATE product_sales SET status='REFUNDED' WHERE sale_id=?", (sale_id,))
            self.connection.execute('UPDATE product_lots SET quantity=quantity+? WHERE lot_id=?', (sale['quantity'], sale['lot_id']))
            self.connection.execute('INSERT INTO product_refunds(sale_id,amount,reason,created_at) VALUES(?,?,?,?)', (sale_id, amount, reason, date.today().isoformat()))
        return {'sale_id': int(sale_id), 'refund': amount, 'persisted': True}

    def stock_alerts(self, club_id):
        rows = self.connection.execute('SELECT p.product_id,p.name,p.low_stock_threshold,COALESCE(SUM(l.quantity),0) AS stock FROM licensed_products p LEFT JOIN product_lots l ON l.product_id=p.product_id WHERE p.club_id=? GROUP BY p.product_id ORDER BY p.product_id', (club_id,)).fetchall()
        return [{'product_id': int(r['product_id']), 'name': r['name'], 'stock': int(r['stock']), 'threshold': int(r['low_stock_threshold']), 'low': int(r['stock']) <= int(r['low_stock_threshold'])} for r in rows]

    def sales_by_segment(self, club_id):
        rows = self.connection.execute("SELECT segment,SUM(quantity) quantity,SUM(quantity*unit_price) revenue FROM product_sales WHERE club_id=? AND status='SOLD' GROUP BY segment ORDER BY segment", (club_id,)).fetchall()
        return [dict(r) for r in rows]

    def close(self): self.connection.close()
