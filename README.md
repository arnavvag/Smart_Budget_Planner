# 💰 Smart Budget Optimizer — Genetic Algorithm

A web-based personal budget optimizer that uses a **Genetic Algorithm (GA)** to intelligently allocate a monthly budget across spending categories. Instead of guessing how to split your money, the algorithm evolves the best allocation over hundreds of generations — balancing your priorities, minimum needs, and maximum limits.

---

## ✨ Features

- **GA-powered optimization** — runs up to 250 generations with elitism, tournament selection, adaptive mutation, and BLX crossover
- **Interactive category builder** — add/remove categories directly in the UI (no CSV required)
- **Preset profiles** — one-click Student and Family budget templates
- **CSV upload** — supply your own category config file
- **Results chart** — pie chart breakdown of the optimized allocation
- **Download reports** — export allocation as CSV or PDF
- **Session history** — keeps the last 5 optimization runs
- **Budget prediction** — scale an existing allocation proportionally to a new budget total

---

## 🗂️ Project Structure

```
smart_budget_ga_web_enhanced/
├── app.py                  # Flask app — routes and controllers
├── ga.py                   # Genetic Algorithm optimizer core
├── utils.py                # CSV loading and allocation saving helpers
├── requirements.txt        # Python dependencies
├── sample_data.csv         # Example category config (7 categories)
├── outputs/                # Generated output files (auto-created)
├── static/
│   ├── money.svg           # App icon/logo
│   ├── script.js           # Frontend JS
│   └── style.css           # Custom styles
└── templates/
    ├── base.html           # Shared layout
    ├── index.html          # Landing page
    ├── create.html         # Budget creation form
    ├── result.html         # Optimization results + chart
    ├── history.html        # Past optimization runs
    ├── prediction.html     # Scaled budget prediction
    ├── about.html          # About page
    └── error.html          # Error display
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

**1. Clone or unzip the project**
```bash
unzip Smart_Budget_GA_Project.zip
cd Smart_Budget_GA_Project/smart_budget_ga_web_enhanced
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
python app.py
```

**5. Open in your browser**
```
http://127.0.0.1:5000
```

---

## 📋 How to Use

1. **Go to Create** — enter your total monthly budget amount (in ₹)
2. **Define categories** — use the form to add spending categories, or pick a preset (Student / Family), or upload a CSV
3. **Set constraints per category:**
   - `min` — the minimum amount that must be allocated
   - `max` — the maximum amount that can be allocated
   - `priority` — importance weight (higher = more critical, e.g. Rent = 10)
   - `alpha` — sensitivity of utility to spending (lower = large spend needed to feel impact)
4. **Click Optimize** — the GA runs and returns the best allocation
5. **Download** the result as CSV or PDF, or use **Predict** to rescale it to a different budget

---

## 📄 CSV Format

You can upload a custom category config. The CSV must have these columns:

```csv
name,min,max,priority,alpha
Rent,8000,12000,10,0.0003
Food,2000,8000,8,0.0008
Transport,500,5000,4,0.001
Savings,1000,15000,9,0.0004
Entertainment,0,5000,2,0.0015
```

See `sample_data.csv` for a working example with 7 categories.

---

## 🧬 How the Genetic Algorithm Works

The core optimizer lives in `ga.py` and follows a standard GA loop:

1. **Initialization** — random population of budget allocations (as fractions), each satisfying minimum constraints
2. **Fitness** — each individual is scored using a utility function:
   - Utility = Σ `priority × (1 − e^(−alpha × amount))` — diminishing returns per category
   - Penalty subtracted for violating min/max bounds or budget total
3. **Selection** — tournament selection (k=3) picks parents
4. **Crossover** — BLX (blend crossover) with probability 0.9
5. **Mutation** — Gaussian noise with adaptive probability (stronger early, weaker late)
6. **Elitism** — top individuals are always carried forward
7. **Repeat** for N generations; return the best allocation found

---

## 📦 Dependencies

| Package      | Purpose                          |
|-------------|----------------------------------|
| Flask       | Web framework                    |
| NumPy       | GA numerical operations          |
| Pandas      | Data loading and manipulation    |
| Matplotlib  | Chart generation                 |
| ReportLab   | PDF report generation            |

Install all with:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

The app uses Flask sessions to store history and results. Before deploying to production, replace the placeholder secret key in `app.py`:

```python
# Development (current)
app.secret_key = "replace_with_a_random_secret_key_please_change"

# Production — use a random key or load from environment
import os
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
```

---

## 🔮 Possible Extensions

- Add user authentication and persistent DB storage (SQLite / PostgreSQL)
- Replace session history with a proper database-backed history page
- Add a REST API endpoint for programmatic optimization
- Export results to Excel
- Deploy to a cloud platform (Render, Railway, Heroku)

---

## 📃 License

This project is for personal/educational use.
