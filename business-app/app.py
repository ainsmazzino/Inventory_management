
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import calendar
from sqlalchemy import extract
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///business.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50), nullable=False)
    serial = db.Column(db.String(50), nullable=False)
    control_unit = db.Column(db.String(50), nullable=False)
    control_unit_serial = db.Column(db.String(50), nullable=False)
    print_head = db.Column(db.String(50), nullable=False)
    print_head_serial = db.Column(db.String(50), nullable=False)
    items = db.relationship('Item', backref='printer_obj')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    pincode = db.Column(db.String(10))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    gst = db.Column(db.String(15))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial = db.Column(db.String(50))
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'))
    description = db.Column(db.String(200))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = db.relationship('Customer', backref='transactions')
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'))
    printer = db.relationship('Printer')
    installation_date = db.Column(db.Date)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('TransactionItem', backref='transaction', cascade="all, delete-orphan")

class TransactionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship('Item')
    quantity = db.Column(db.Integer)
    serviced = db.Column(db.String(3))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('base.html')

# ---- Master → Printer ----
@app.route('/master/printer', methods=['GET','POST'])
def master_printer():
    if request.method == 'POST':
        p = Printer(
            model=request.form['model'],
            serial=request.form['serial'],
            control_unit=request.form['control_unit'],
            control_unit_serial=request.form['control_unit_serial'],
            print_head=request.form['print_head'],
            print_head_serial=request.form['print_head_serial']
        )
        db.session.add(p); db.session.commit()
        return redirect(url_for('master_printer'))
    printers = Printer.query.all()
    return render_template('master/printer.html', printers=printers)

@app.route('/master/printer/edit/<int:id>', methods=['GET','POST'])
def master_printer_edit(id):
    printer = Printer.query.get_or_404(id)
    if request.method == 'POST':
        printer.model = request.form['model']
        printer.serial = request.form['serial']
        printer.control_unit = request.form['control_unit']
        printer.control_unit_serial = request.form['control_unit_serial']
        printer.print_head = request.form['print_head']
        printer.print_head_serial = request.form['print_head_serial']
        db.session.commit()
        return redirect(url_for('master_printer'))
    printers = Printer.query.all()
    return render_template('master/printer.html', printers=printers, edit_printer=printer)

# ---- Master → Customer ----
@app.route('/master/customer', methods=['GET','POST'])
def master_customer():
    if request.method == 'POST':
        c = Customer(
            name=request.form['name'],
            address_line1=request.form['address_line1'],
            address_line2=request.form['address_line2'],
            pincode=request.form['pincode'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            gst=request.form['gst']
        )
        db.session.add(c); db.session.commit()
        return redirect(url_for('master_customer'))
    customers = Customer.query.all()
    return render_template('master/customer.html', customers=customers)

@app.route('/master/customer/edit/<int:id>', methods=['GET','POST'])
def master_customer_edit(id):
    cust = Customer.query.get_or_404(id)
    if request.method == 'POST':
        cust.name = request.form['name']
        cust.address_line1 = request.form['address_line1']
        cust.address_line2 = request.form['address_line2']
        cust.pincode = request.form['pincode']
        cust.city = request.form['city']
        cust.state = request.form['state']
        cust.phone = request.form['phone']
        cust.gst = request.form['gst']
        db.session.commit()
        return redirect(url_for('master_customer'))
    customers = Customer.query.all()
    return render_template('master/customer.html', customers=customers, edit_customer=cust)

# ---- Master → Item ----
@app.route('/master/item', methods=['GET','POST'])
def master_item():
    if request.method == 'POST':
        i = Item(
            name=request.form['name'],
            serial=request.form['serial'],
            printer_id=request.form['printer'],
            description=request.form['description']
        )
        db.session.add(i); db.session.commit()
        return redirect(url_for('master_item'))
    items = Item.query.all()
    printers = Printer.query.all()
    return render_template('master/item.html', items=items, printers=printers)

@app.route('/master/item/edit/<int:id>', methods=['GET','POST'])
def master_item_edit(id):
    it = Item.query.get_or_404(id)
    if request.method == 'POST':
        it.name = request.form['name']
        it.serial = request.form['serial']
        it.printer_id = request.form['printer']
        it.description = request.form['description']
        db.session.commit()
        return redirect(url_for('master_item'))
    items = Item.query.all()
    printers = Printer.query.all()
    return render_template('master/item.html', items=items, printers=printers, edit_item=it)

# ---- Transaction → New & Edit ----
@app.route('/transaction/new', methods=['GET','POST'])
def transaction_new():
    if request.method == 'POST':
        install_date = date.fromisoformat(request.form['installation_date'])
        tx = Transaction(
            customer_id=request.form['customer_id'],
            printer_id=request.form['printer_id'],
            installation_date=install_date
        )
        db.session.add(tx); db.session.commit()
        for item_id, qty, serv in zip(
            request.form.getlist('item_id'),
            request.form.getlist('quantity'),
            request.form.getlist('serviced')
        ):
            db.session.add(TransactionItem(
                transaction_id=tx.id,
                item_id=item_id,
                quantity=qty,
                serviced=serv
            ))
        db.session.commit()
        return redirect(url_for('transaction_new'))

    customers    = Customer.query.all()
    printers     = Printer.query.all()
    transactions = Transaction.query.options(
        joinedload(Transaction.items).joinedload(TransactionItem.item),
        joinedload(Transaction.customer),
        joinedload(Transaction.printer)
    ).all()
    return render_template('transaction/new.html',
                           customers=customers,
                           printers=printers,
                           transactions=transactions)

@app.route('/transaction/edit/<int:id>', methods=['GET','POST'])
def transaction_edit(id):
    tx = Transaction.query.get_or_404(id)
    if request.method == 'POST':
        tx.customer_id = request.form['customer_id']
        tx.printer_id = request.form['printer_id']
        tx.installation_date = date.fromisoformat(request.form['installation_date'])
        TransactionItem.query.filter_by(transaction_id=tx.id).delete()
        db.session.commit()
        for item_id, qty, serv in zip(
            request.form.getlist('item_id'),
            request.form.getlist('quantity'),
            request.form.getlist('serviced')
        ):
            db.session.add(TransactionItem(
                transaction_id=tx.id,
                item_id=item_id,
                quantity=qty,
                serviced=serv
            ))
        db.session.commit()
        return redirect(url_for('transaction_new'))

    customers    = Customer.query.all()
    printers     = Printer.query.all()
    initial_items = [{'id': ti.item_id, 'quantity': ti.quantity, 'serviced': ti.serviced}
                     for ti in tx.items]
    transactions = Transaction.query.options(
        joinedload(Transaction.items).joinedload(TransactionItem.item),
        joinedload(Transaction.customer),
        joinedload(Transaction.printer)
    ).all()
    return render_template('transaction/new.html',
                           customers=customers,
                           printers=printers,
                           transactions=transactions,
                           edit_tx=tx,
                           edit_items=initial_items)

# ---- API → Items by Printer ----
@app.route('/api/items/<int:printer_id>')
def items_by_printer(printer_id):
    items = Item.query.filter_by(printer_id=printer_id).all()
    return jsonify(items=[{'id': i.id, 'name': f"{i.name} ({i.serial})"} for i in items])

# ---- Report → Customer Wise ----
@app.route('/report/customer-wise', methods=['GET','POST'])
def report_customer_wise():
    customers = Customer.query.all()
    results, selected = [], None
    if request.method=='POST':
        cid = request.form['customer_id']
        selected = Customer.query.get(cid)
        txs = Transaction.query.filter_by(customer_id=cid).options(
            joinedload(Transaction.items).joinedload(TransactionItem.item)
        ).all()
        for tx in txs:
            for it in tx.items:
                results.append({
                    'date': tx.transaction_date,
                    'item_name': it.item.name,
                    'serial': it.item.serial,
                    'printer': it.item.printer_obj.model,
                    'quantity': it.quantity,
                    'serviced': it.serviced
                })
    return render_template('report/customer_wise.html',
                           customers=customers,
                           results=results,
                           selected_customer=selected)

# ---- Report → Monthly (RANGE) ----
@app.route('/report/monthly', methods=['GET','POST'])
def report_monthly():
    months = list(range(1, 13))
    years = list(range(2020, datetime.now().year + 1))
    results = []
    selected_range = None

    if request.method == 'POST':
        fm = int(request.form['from_month'])
        fy = int(request.form['from_year'])
        tm = int(request.form['to_month'])
        ty = int(request.form['to_year'])

        start_date = date(fy, fm, 1)
        last_day = calendar.monthrange(ty, tm)[1]
        end_date = date(ty, tm, last_day)

        selected_range = (start_date, end_date)

        txs = Transaction.query.filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).options(
            joinedload(Transaction.customer),
            joinedload(Transaction.items).joinedload(TransactionItem.item),
            joinedload(Transaction.printer)
        ).all()

        for tx in txs:
            for it in tx.items:
                results.append({
                    'date': tx.transaction_date,
                    'customer': tx.customer.name,
                    'item_name': it.item.name,
                    'serial': it.item.serial,
                    'printer': tx.printer.model,
                    'quantity': it.quantity,
                    'serviced': it.serviced
                })

    return render_template('report/monthly.html',
                           months=months,
                           years=years,
                           results=results,
                           selected_range=selected_range)

# ---- Report → Item Wise ----
@app.route('/report/item-wise', methods=['GET','POST'])
def report_item_wise():
    items = Item.query.all()
    results, selected = [], None
    if request.method=='POST':
        iid = request.form['item_id']
        selected = Item.query.get(iid)
        tis = TransactionItem.query.filter_by(item_id=iid).options(
            joinedload(TransactionItem.transaction).joinedload(Transaction.customer)
        ).all()
        for ti in tis:
            results.append({
                'date': ti.transaction.transaction_date,
                'customer': ti.transaction.customer.name,
                'quantity': ti.quantity,
                'serviced': ti.serviced
            })
    return render_template('report/item_wise.html',
                           items=items,
                           results=results,
                           selected_item=selected)

# ---- Report → Printer Summary ----
@app.route('/report/printer-summary', methods=['GET','POST'])
def report_printer_summary():
    models = [m[0] for m in db.session.query(Printer.model).distinct().all()]
    results = []
    selected_model = None
    if request.method=='POST':
        selected_model = request.form['model']
        printers = Printer.query.filter_by(model=selected_model).all()
        for p in printers:
            txs = Transaction.query.filter_by(printer_id=p.id).options(
                joinedload(Transaction.customer),
                joinedload(Transaction.items).joinedload(TransactionItem.item)
            ).all()
            for tx in txs:
                for it in tx.items:
                    results.append({
                        'customer': tx.customer.name,
                        'printer_serial': p.serial,
                        'item_name': it.item.name,
                        'item_serial': it.item.serial,
                        'installation_date': tx.installation_date
                    })
    return render_template('report/printer_summary.html',
                           models=models,
                           results=results,
                           selected_model=selected_model)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
# if __name__ == '__main__':
#     app.run(debug=True)

