from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import pandas as pd

def build_pdf_brief(metrics, narrative, output_path="../outputs/Annual_Risk_Briefing.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = [
        Paragraph("Procurement Risk - Annual Executive Briefing", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Period: {metrics['current_year']} vs {metrics['prior_year']}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(narrative, styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Key Metrics", styles["Heading2"]),
        Paragraph(f"Total Spend: INR {metrics['total_spend_current']:,.0f} "
                  f"({metrics['spend_change_pct']}% vs {metrics['prior_year']})", styles["Normal"]),
        Paragraph(f"Non-Compliant POs: {metrics['noncompliant_current']} "
                  f"(change of {metrics['noncompliant_change']})", styles["Normal"]),
        Paragraph(f"Price Variance Flags: {metrics['price_variance_current']} "
                  f"(change of {metrics['price_variance_change']})", styles["Normal"]),
        Paragraph(f"Defect Rate: {metrics['defect_rate_current']}% "
                  f"(change of {metrics['defect_rate_change']} pts)", styles["Normal"]),
        Paragraph(f"Top Spend Mover: {metrics['top_mover_supplier']} "
                  f"(+INR {metrics['top_mover_spend_increase']:,.0f})", styles["Normal"]),
    ]
    doc.build(story)
    print(f"PDF brief saved to {output_path}")

def write_powerbi_card(narrative, output_path="../outputs/powerbi_summary_card.csv"):
    pd.DataFrame([{"summary_text": narrative}]).to_csv(output_path, index=False)
    print(f"Power BI card CSV saved to {output_path}")

if __name__ == "__main__":
    from metrics_agent import compute_metrics
    metrics = compute_metrics(current_year=2023, prior_year=2022, db_path="../db/procurement.db")

    # Using the demonstration narrative generated earlier
    narrative = (
        "Total procurement spend rose 10.6% in 2023 compared to 2022, reaching INR 23.74M, "
        "with Beta_Supplies accounting for the largest increase in spend at approximately "
        "INR 13.3 lakh. Non-compliant purchase orders increased slightly, a modest but "
        "noteworthy uptick given the existing non-compliance rate flagged in the executive "
        "overview. Price variance flags declined, a small improvement in pricing discipline. "
        "The overall defect rate rose marginally, continuing a trend that warrants attention "
        "given Delta_Logistics' persistently elevated defect rate identified in the Quality "
        "and Delivery Risk analysis."
    )

    build_pdf_brief(metrics, narrative)
    write_powerbi_card(narrative)
