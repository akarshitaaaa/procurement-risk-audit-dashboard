# Procurement Risk & Internal Audit Dashboard

A 3-page Power BI dashboard that detects classic internal-audit red flags in real procurement data, paired with a small agentic AI layer that automatically writes its own year-over-year executive summary.

## Dashboard Preview

### Page 1 — Executive Overview
(<img width="1303" height="737" alt="page 1" src="https://github.com/user-attachments/assets/b687b667-3d97-4e04-87d2-a4c6cb5a14f2" />
)

### Page 2 — Risk Deep-Dive
(<img width="1310" height="737" alt="page 2" src="https://github.com/user-attachments/assets/5410ad49-7d70-46c3-9d5d-7149247a28e0" />
)

### Page 3 — Quality & Delivery Risk
(<img width="1312" height="736" alt="page 3" src="https://github.com/user-attachments/assets/2f623a10-5ff9-45ca-a52b-df618c6c47b5" />
)

## Objective
Simulate an internal audit of an enterprise procurement process to identify control weaknesses, quantify financial risk exposure, and produce audit-style findings and recommendations — the same core workflow performed by a risk/audit analyst.

## Scope
- **Dataset:** Procurement KPI Analysis Dataset (public, Kaggle — real-world supplier performance, cost, and compliance data)
- **Size:** 777 purchase orders across 5 suppliers and 5 item categories
- **Period covered:** 2022–2024 (2024 is partial, through January 1 only)
- **Fields used:** PO_ID, Supplier, Order_Date, Delivery_Date, Item_Category, Order_Status, Quantity, Unit_Price, Negotiated_Price, Defective_Units, Compliance
- **Dashboard structure:** 3 pages — Executive Overview, Risk Deep-Dive, and Quality & Delivery Risk

## Data Source & Limitations
This is real (not synthetic) procurement data sourced from Kaggle. As with most public procurement datasets, it does **not** include internal HR/approval fields such as a requester or approver ID. As a result, a **Segregation of Duties (SoD)** check — one of the standard six audit risk flags — could not be built against this dataset and has been intentionally excluded rather than simulated. This is disclosed here rather than worked around, since a real audit engagement would document a data limitation the same way.

## Risk Criteria Tested
1. **Vendor Concentration Risk** — flags over-reliance on any single supplier
2. **Price Variance** — flags purchase orders priced significantly above the category average unit price
3. **Maverick / Non-Compliant Spend** — flags purchases marked non-compliant in the source data
4. **Duplicate Purchase Orders** — flags near-identical POs (same supplier, category, quantity, and price within a 7-day window), used as a proxy for duplicate-payment risk since no separate invoice/payment table exists in this dataset
5. **Split PO Pattern** — flags supplier+category clusters with 3 or more orders in a short window, a softer signal than a true requester-based split-PO check (since no requester field is available)

## Findings Summary

### Page 1 — Executive Overview
- **Total spend analyzed:** ₹45.37M across all purchase orders
- **Vendor concentration:** Spend is fairly evenly distributed across the 5 suppliers (17.3%–21.7% each) — no single vendor shows over-reliance risk
- **Price variance:** 238 purchase orders (30.6% of all POs) were priced more than 30% above their category average, concentrated heavily in the Packaging category
- **Non-compliant spend:** 137 purchase orders (17.6% of all POs) were flagged as non-compliant in the source data, representing significant unmitigated risk exposure
- **Duplicate POs:** 0 exact/near-duplicate orders detected — a clean result on this specific control

### Page 2 — Risk Deep-Dive
- **Total risk findings across all categories:** 384 (137 non-compliant + 238 price variance + 9 split PO clusters + 0 duplicates)
- **Split PO pattern:** 9 supplier+category clusters showed 3+ orders within a single week, the largest cluster (Beta_Supplies, Electronics) totaling ₹5.4L combined value
- **Monthly spend trend (2022–2024):** Spend trended around ₹20-24M/month through most of the period. **Note:** the dataset's date range ends 2024-01-01, so 2024 contains only partial-year data — the visible decline at the end of the trend line reflects incomplete data for that period, not an actual drop in spend

### Page 3 — Quality & Delivery Risk
- **Average defect rate across suppliers:** 6.79%
- **Highest defect rate:** Delta_Logistics at 14.4% — more than 6x the rate of the best-performing supplier (Alpha_Inc, 2.25%)
- **Delivery performance:** Fairly consistent across suppliers, averaging 10.2–11.3 days; Delta_Logistics is both a quality and delivery-speed laggard, making it the clearest candidate for vendor review
- **Order status:** 72% Delivered, 10% Pending, 9% Partially Delivered, 8% Cancelled

## Recommendations
- Investigate the root cause of the high price-variance rate in the Packaging category — could indicate weak negotiated pricing enforcement or vendor overcharging
- Review the 137 non-compliant purchase orders individually to determine root cause (policy exception vs. control failure) and remediate recurring patterns
- Monitor the 9 flagged split-PO clusters for intentional threshold avoidance, even though a true requester-level check wasn't possible with this dataset
- **Prioritize a formal vendor review of Delta_Logistics** — it shows both the highest defect rate (14.4%, vs. an average of 6.79%) and among the slower delivery times, making it the single clearest vendor-risk signal in the dataset
- Maintain current vendor diversification — concentration risk is currently low and should be preserved as the supplier base evolves

## Limitations
- Segregation of Duties could not be tested due to missing requester/approver fields in the source data (see Data Source & Limitations above)
- Duplicate PO and Split PO checks are proxy signals built on available fields (supplier, category, quantity, price, date), not true payment-level or requester-level detection — a production audit would need the underlying ERP's payment and approval tables for full coverage
- Price variance thresholds (30% above category average) are illustrative and not derived from a formal cost-benchmarking study

## Tools Used
Python (pandas), SQL (SQLite), Power BI, DAX, Groq API (LLM), ReportLab (PDF generation)

## AI Executive Summary Agent (Agentic AI Layer)

On top of the dashboard, this project includes a small agentic AI pipeline that automatically writes a year-over-year executive summary — the kind of narrative a business analyst would otherwise write by hand each reporting period.

### Architecture
Three specialized steps, chained together, each with a single clear responsibility:

| Agent | Role | Uses an LLM? |
|---|---|---|
| **Metrics Agent** | Computes 2023 vs. 2022 changes — spend, non-compliance, price variance, defect rate, top spend mover — by reusing the exact same detection logic as the SQL queries above | No — pure Python/pandas |
| **Narrative Agent** | Converts the computed metrics into a 4-5 sentence executive summary in business language | Yes — this is the only step in the entire project that calls an LLM |
| **Output Agent** | Formats the summary into a PDF briefing and a CSV that feeds directly into the Power BI dashboard | No |

**Design principle:** the AI is used only where it adds real value — turning numbers into readable prose. Every number the AI receives is pre-computed by deterministic code; the model is explicitly instructed not to invent figures beyond what it's given. This keeps every output fully explainable and traceable back to the underlying data.

**Model used:** `openai/gpt-oss-120b` via the Groq API.

### Real output (generated from this project's actual data)
> *"The 2023 procurement risk dashboard shows a total spend of INR 23,743,036, representing a 10.6% change versus 2022. Non-compliant purchase orders rose modestly to 70, up by three, while price-variance alerts fell slightly to 119, a decrease of four flags. The defect rate increased to 5.83%, up 0.41 percentage points from the prior year, indicating a marginal rise in quality concerns. The most significant spend shift came from Beta_Supplies, which added INR 1,334,997 to the portfolio, emerging as the top mover in 2023."*

This narrative is displayed directly on Page 1 of the dashboard (Executive Overview), above the KPI cards.

### Files
- `summary_agent/metrics_agent.py` — deterministic year-over-year metrics calculation
- `summary_agent/narrative_agent.py` — the LLM call that generates the narrative
- `summary_agent/output_agent.py` — builds the PDF briefing and the Power BI card CSV
- `Annual_Risk_Briefing.pdf` — generated one-page executive briefing
- `powerbi_summary_card.csv` — the narrative, formatted for import into Power BI



## Files in This Repository
```
procurement-risk-audit-dashboard/
├── README.md
├── Procurement KPI Analysis Dataset.csv       # source data (Kaggle)
├── risk_queries.sql                           # all 10 SQL queries
├── procurement_risk_analysis_dashboard.pbix   # Power BI dashboard (3 pages)
├── Annual_Risk_Briefing.pdf                   # AI-generated executive briefing
├── screenshots/
│   ├── page1_executive_overview.png
│   ├── page2_risk_deep_dive.png
│   └── page3_quality_delivery_risk.png
├── query_outputs/
│   ├── 1_vendor_concentration.csv
│   ├── 2_price_variance.csv
│   ├── 3_maverick_noncompliant.csv
│   ├── 4_duplicate_pos.csv
│   ├── 5_split_po_pattern.csv
│   ├── 6_monthly_spend_trend.csv
│   ├── 7_risk_breakdown.csv
│   ├── 8_defect_rate_by_supplier.csv
│   ├── 9_order_status_breakdown.csv
│   ├── 10_delivery_delay_by_supplier.csv
│   └── powerbi_summary_card.csv
└── summary_agent/
    ├── metrics_agent.py
    ├── narrative_agent.py
    └── output_agent.py
```
