from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
import pandas as pd
import io, csv, os
from ga import GeneticBudgetOptimizer
from utils import load_categories
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
# For production, replace this with a random secure key, e.g. os.urandom(24) or read from env var
import os
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-fallback")

# Ensure outputs dir
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def form_to_df(form):
    names = form.getlist('name[]')
    mins = form.getlist('min[]')
    maxs = form.getlist('max[]')
    priorities = form.getlist('priority[]')
    alphas = form.getlist('alpha[]')
    rows = []
    for i, n in enumerate(names):
        if not n.strip():
            continue
        row = {
            'name': n.strip(),
            'min': float(mins[i]) if mins[i] else 0.0,
            'max': float(maxs[i]) if maxs[i] else 0.0,
            'priority': float(priorities[i]) if priorities[i] else 1.0,
            'alpha': float(alphas[i]) if alphas[i] else 0.0005
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    sample = load_categories('sample_data.csv')
    presets = {
        "Student": [
            {"name":"Rent","min":8000,"max":12000,"priority":10,"alpha":0.0003},
            {"name":"Food","min":2000,"max":6000,"priority":8,"alpha":0.0008},
            {"name":"Transport","min":500,"max":3000,"priority":4,"alpha":0.001},
            {"name":"Savings","min":500,"max":10000,"priority":9,"alpha":0.0004},
            {"name":"Entertainment","min":0,"max":3000,"priority":2,"alpha":0.0015}
        ],
        "Family": [
            {"name":"Rent","min":15000,"max":25000,"priority":10,"alpha":0.0003},
            {"name":"Food","min":4000,"max":12000,"priority":8,"alpha":0.0008},
            {"name":"Transport","min":1000,"max":5000,"priority":4,"alpha":0.001},
            {"name":"Savings","min":3000,"max":20000,"priority":9,"alpha":0.0004},
            {"name":"Kids","min":2000,"max":8000,"priority":7,"alpha":0.0006}
        ]
    }
    return render_template('create.html', sample=sample.to_dict(orient='records'), presets=presets)

# ---- ADDED about route to fix BuildError ----
@app.route('/about')
def about():
    # ensure you have templates/about.html in templates/
    return render_template('about.html')
# ------------------------------------------------

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        budget = float(request.form['budget'])
        generations = int(request.form.get('generations', 250))
        pop_size = int(request.form.get('pop', 200))
        csv_file = request.files.get('config')
        if csv_file and csv_file.filename:
            df = pd.read_csv(csv_file)
        else:
            df = form_to_df(request.form)

        optimizer = GeneticBudgetOptimizer(categories=df, budget=budget, pop_size=pop_size, random_state=42)
        result = optimizer.run(generations=generations, verbose=False)

        allocation = result['allocation']
        fitness = float(result['fitness'])
        timestamp = datetime.now().isoformat()

        history = session.get('history', [])
        entry = {
            'timestamp': timestamp,
            'budget': budget,
            'allocation': allocation,
            'fitness': fitness
        }
        history.insert(0, entry)
        history = history[:5]
        session['history'] = history
        session['last_result'] = entry

        labels = list(allocation.keys())
        values = list(allocation.values())

        return render_template('result.html',
                               allocation=allocation,
                               fitness=round(fitness,2),
                               total_budget=budget,
                               labels=labels,
                               values=values,
                               timestamp=timestamp)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/download_csv')
def download_csv():
    last = session.get('last_result')
    if not last:
        return redirect(url_for('create'))
    allocation = last['allocation']
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['category','amount'])
    for k,v in allocation.items():
        cw.writerow([k, v])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=allocation.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/download_pdf')
def download_pdf():
    last = session.get('last_result')
    if not last:
        return redirect(url_for('create'))
    allocation = last['allocation']
    budget = last['budget']
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, 750, "Smart Budget Optimizer - Allocation Report")
    p.setFont("Helvetica", 12)
    p.drawString(40, 730, f"Budget: ₹{budget:.2f}")
    p.drawString(40, 715, f"Generated: {last['timestamp']}")
    y = 690
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Category")
    p.drawString(300, y, "Amount (₹)")
    p.setFont("Helvetica", 12)
    y -= 20
    for k, v in allocation.items():
        p.drawString(40, y, str(k))
        p.drawString(300, y, f"₹{v:.2f}")
        y -= 18
        if y < 50:
            p.showPage()
            y = 750
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="allocation_report.pdf", mimetype='application/pdf')

@app.route('/history')
def history():
    history = session.get('history', [])
    return render_template('history.html', history=history)

@app.route('/predict', methods=['POST'])
def predict():
    last = session.get('last_result')
    if not last:
        return redirect(url_for('create'))
    try:
        new_budget = float(request.form['new_budget'])
        allocation = last['allocation']
        total_old = last['budget']
        factor = new_budget / total_old if total_old>0 else 1.0
        new_alloc = {k: round(v * factor,2) for k,v in allocation.items()}
        return render_template('prediction.html', new_budget=new_budget, allocation=new_alloc, old_budget=total_old)
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == "__main__":
    app.run(debug=True)
