import pandas as pd
import sqlite3

def load_year_data(year, conn):
    df = pd.read_sql("SELECT * FROM purchase_orders", conn)
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    return df[df['Order_Date'].dt.year == year]

def compute_metrics(current_year, prior_year, db_path="db/procurement.db"):
    conn = sqlite3.connect(db_path)
    curr = load_year_data(current_year, conn)
    prior = load_year_data(prior_year, conn)

    # --- Spend ---
    curr_spend = (curr["Quantity"] * curr["Negotiated_Price"]).sum()
    prior_spend = (prior["Quantity"] * prior["Negotiated_Price"]).sum()
    spend_change_pct = round(((curr_spend - prior_spend) / prior_spend) * 100, 1)

    # --- Non-compliant spend (reuses Part 1's exact logic) ---
    noncompliant_curr = (curr["Compliance"] == "No").sum()
    noncompliant_prior = (prior["Compliance"] == "No").sum()
    noncompliant_change = int(noncompliant_curr - noncompliant_prior)

    # --- Price variance (reuses Part 1's exact logic, >30% above category avg) ---
    def count_price_variance(d):
        cat_avg = d.groupby("Item_Category")["Unit_Price"].transform("mean")
        return (d["Unit_Price"] > cat_avg * 1.3).sum()
    variance_curr = count_price_variance(curr)
    variance_prior = count_price_variance(prior)
    variance_change = int(variance_curr - variance_prior)

    # --- Defect rate (reuses Part 3's exact logic) ---
    defect_rate_curr = round(100 * curr["Defective_Units"].sum() / curr["Quantity"].sum(), 2)
    defect_rate_prior = round(100 * prior["Defective_Units"].sum() / prior["Quantity"].sum(), 2)

    # --- Top mover: supplier with biggest spend increase ---
    curr_by_supplier = (curr.groupby("Supplier").apply(lambda d: (d["Quantity"] * d["Negotiated_Price"]).sum()))
    prior_by_supplier = (prior.groupby("Supplier").apply(lambda d: (d["Quantity"] * d["Negotiated_Price"]).sum()))
    delta = (curr_by_supplier - prior_by_supplier.reindex(curr_by_supplier.index).fillna(0))
    top_mover = delta.idxmax()
    top_mover_change = round(delta.max(), 2)

    conn.close()
    return {
        "current_year": current_year,
        "prior_year": prior_year,
        "total_spend_current": float(curr_spend),
        "spend_change_pct": spend_change_pct,
        "noncompliant_current": int(noncompliant_curr),
        "noncompliant_change": noncompliant_change,
        "price_variance_current": int(variance_curr),
        "price_variance_change": variance_change,
        "defect_rate_current": defect_rate_curr,
        "defect_rate_change": round(defect_rate_curr - defect_rate_prior, 2),
        "top_mover_supplier": top_mover,
        "top_mover_spend_increase": top_mover_change,
    }

if __name__ == "__main__":
    metrics = compute_metrics(current_year=2023, prior_year=2022)
    for k, v in metrics.items():
        print(f"{k}: {v}")
