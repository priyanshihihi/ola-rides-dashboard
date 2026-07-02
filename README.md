#  Ola Rides Analytics Dashboard

An end-to-end **Power BI analytics dashboard** built on synthetic Ola ride-hailing data, featuring an **AI-powered review trust scoring system** that classifies customer reviews as Genuine, Suspicious, or Spam using a hybrid LLM + rule-based approach.

> Built as a portfolio project to demonstrate Data Analyst skills: data generation, Python scripting, AI integration, data modelling, DAX, and interactive dashboard design.

---

## Dashboard Pages

| Page | What it shows |
|------|--------------|
| **Overview** | Total bookings, revenue, completion rate, cancellation rate, avg fare — with city and month slicers |
| **Cancellation Analysis** | Cancellation reasons breakdown, cancellation rate by city, booking status distribution |
| **Vehicle & Revenue** | Revenue by vehicle type, revenue by payment method, avg fare by vehicle type |
| **Driver Analysis** | Top 10 drivers by revenue, driver rating distribution, bookings by vehicle type per city |
| **AI Review Trust** | Genuine/Suspicious/Spam review counts, trust distribution donut, flagged reviews table with AI reasoning |

---

## AI Feature: Review Trust Scoring

The standout feature of this project is a **hybrid AI pipeline** that scores every customer review for authenticity:

### How it works
1. **LLM Layer (Google Gemini API):** Each review is sent to Gemini with a structured prompt asking it to classify the review as Genuine/Suspicious/Spam, assign a trust score (0–100), and provide a one-line reason
2. **Rule-based Fallback Layer:** For reviews where the LLM hits rate limits or returns uncertain results, a keyword/pattern-based scorer takes over — checking for spam signals (URLs, phone numbers), generic/repetitive language, sentiment-rating mismatches, and short/vague text
3. **Result:** Every review gets a label, trust score, and reason — surfaced in the Power BI dashboard

### Why this matters
This mirrors real-world production systems where LLMs handle nuanced cases and rule-based logic provides reliable, explainable fallback coverage. The dashboard surfaces actionable insights: which drivers have disproportionately high suspicious review rates, and which reviews contain outright spam.

### Results
| Label | Count | % |
|-------|-------|---|
| Genuine | 3,124 | 91.4% |
| Suspicious | 238 | 7.0% |
| Spam | 55 | 1.6% |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python (pandas, Faker) | Synthetic data generation |
| Google Gemini API | LLM-based review classification |
| Custom rule-based scorer | Fallback classifier for unscored reviews |
| Power BI Desktop | Dashboard and data visualisation |
| DAX | KPI measures (Completion Rate, Cancellation Rate, Revenue per KM etc.) |
| Git + GitHub | Version control and portfolio hosting |

---

## Project Structure

```
ola_dashboard_project/
│
├── ola_dashboard.pbix          ← Power BI dashboard file
├── score_reviews_gemini.py     ← LLM review scoring script (Gemini API)
├── fix_unknown_reviews.py      ← Rule-based fallback scorer
├── generate_data.py            ← Synthetic dataset generator
│
└── ola_data/
    ├── bookings.csv            ← 8,000 ride bookings
    ├── customers.csv           ← 1,800 customers
    ├── drivers.csv             ← 350 drivers
    ├── reviews.csv             ← 3,417 raw reviews
    └── reviews_scored.csv      ← Reviews with AI trust labels
```

---

##  Dataset Overview

All data is **synthetically generated** using Python's Faker library (Indian locale) to simulate realistic Ola ride patterns:

- **8,000 bookings** across 6 cities: Bengaluru, Mumbai, Delhi, Hyderabad, Pune, Chennai
- **5 vehicle types:** Mini, Sedan, Auto, Bike, Prime SUV
- **Realistic booking statuses:** 78% Completed, 12% Cancelled by Customer, 7% Cancelled by Driver, 3% No Driver Found
- **3,417 reviews** with deliberately seeded suspicious/spam text to validate the AI trust-scoring feature

---

##  How to Run

### 1. Generate the dataset
```bash
pip install pandas faker
python generate_data.py
```

### 2. Run AI review scoring
```bash
pip install google-generativeai
set GOOGLE_API_KEY=your-key-here       # Windows
export GOOGLE_API_KEY="your-key-here"  # Mac/Linux
python score_reviews_gemini.py
```

### 3. Fix any unscored reviews
```bash
python fix_unknown_reviews.py
```

### 4. Open the dashboard
Open `ola_dashboard.pbix` in Power BI Desktop and refresh the data source paths if prompted.

---

##  Key Insights from the Dashboard

- **Hyderabad** leads in total bookings among all 6 cities
- **Prime SUV** generates the highest revenue per ride despite lower booking volume
- **UPI** is the dominant payment method — consistent with India's digital payment trends
- **June** shows the sharpest revenue dip, suggesting seasonal demand patterns
- **8% of drivers** flagged as "problem drivers" had significantly higher suspicious review rates — suggesting possible review manipulation

---

##  Author

**Priyanshi** — B.Tech Computer Science (Blockchain), Presidency University Bangalore  
GitHub: [@priyanshihihi](https://github.com/priyanshihihi)
