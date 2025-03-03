from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/craigslist')
def craigslist_dashboard():
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT i.signal_id, c.name, i.description, i.date, i.url, i.city FROM intent_signals i JOIN companies c ON i.company_id = c.company_id ORDER BY i.date DESC")
    signals = c.fetchall()
    conn.close()
    return render_template('dashboard.html', signals=signals, signal_type='Craigslist', title='Craigslist Leads')

@app.route('/ecom')
def ecom_dashboard():
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT i.signal_id, c.name, i.description, i.date, i.url, i.source FROM ecom_signals i JOIN companies c ON i.company_id = c.company_id ORDER BY i.date DESC")
    signals = c.fetchall()
    conn.close()
    return render_template('dashboard.html', signals=signals, signal_type='Ecom', title='Ecom Businesses')

@app.route('/x')
def x_dashboard():
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT i.signal_id, c.name, i.description, i.date, i.url, i.source FROM x_signals i JOIN companies c ON i.company_id = c.company_id ORDER BY i.date DESC")
    signals = c.fetchall()
    conn.close()
    return render_template('dashboard.html', signals=signals, signal_type='X', title='X Influencers')

@app.route('/offices')
def offices_dashboard():
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT i.signal_id, c.name, i.description, i.date, i.url, i.source, i.contacted FROM office_buildings i JOIN companies c ON i.company_id = c.company_id ORDER BY i.date DESC")
    signals = c.fetchall()
    conn.close()
    return render_template('dashboard.html', signals=signals, signal_type='Offices', title='Office Buildings')

@app.route('/office-managers')
def office_managers_dashboard():
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT i.signal_id, c.name, i.description, i.date, i.url, i.source, i.contacted FROM office_manager_jobs i JOIN companies c ON i.company_id = c.company_id ORDER BY i.date DESC")
    signals = c.fetchall()
    conn.close()
    return render_template('dashboard.html', signals=signals, signal_type='OfficeManagers', title='Office Manager Jobs')

@app.route('/delete', methods=['POST'])
def delete_signals():
    signal_ids = request.form.getlist('signal_ids')
    signal_type = request.form.get('signal_type', 'Ecom')
    if signal_ids:
        conn = sqlite3.connect('data/abm_tool.db')
        c = conn.cursor()
        table = {'Craigslist': 'intent_signals', 'Ecom': 'ecom_signals', 'X': 'x_signals', 'Offices': 'office_buildings', 'OfficeManagers': 'office_manager_jobs'}[signal_type]
        c.executemany(f"DELETE FROM {table} WHERE signal_id = ?", [(int(sid),) for sid in signal_ids])
        conn.commit()
        conn.close()
    return redirect(url_for(f"{signal_type.lower()}_dashboard"))

@app.route('/toggle_contacted/<int:signal_id>', methods=['POST'])
def toggle_contacted(signal_id):
    signal_type = request.referrer.split('/')[-1]
    table = {'offices': 'office_buildings', 'office-managers': 'office_manager_jobs'}[signal_type]
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    c.execute(f"UPDATE {table} SET contacted = 1 - contacted WHERE signal_id = ?", (signal_id,))
    conn.commit()
    conn.close()
    return redirect(url_for(f"{signal_type}_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)