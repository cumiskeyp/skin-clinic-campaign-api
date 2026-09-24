"""
Skin Clinic Campaign Analysis API
=================================
FastAPI application that analyses a customer marketing campaign and
serves the response-rate breakdowns as HTML tables and JSON.

Endpoints
---------
GET  /                        Landing page with links
GET  /campaign-analysis       The four analysis tables, rendered as HTML
GET  /campaign-analysis/json  The same results as JSON (for Excel / VBA / Power Query)
GET  /health                  Health check

Run locally:  uvicorn main:app --reload
"""

from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# -------------------------------------------------
# Create FastAPI app
# -------------------------------------------------
app = FastAPI(
    title="Skin Clinic Campaign Analysis API",
    description="Response-rate analysis  for customer marketing campaign.",
    version="1.0.0",
)

DATA_FILE = Path(__file__).parent / "skin_clinic_campaign.csv"

AGE_ORDER = ["<30", "30-50", ">50"]
PURCHASE_ORDER = ["Yes", "No"]
USAGE_ORDER = ["1-4", "5-8", ">8"]


# -------------------------------------------------
# Data loading
# -------------------------------------------------
def usage_band(n: int) -> str:
    """Count of unique products purchased in the last year."""
    if n <= 4:
        return "1-4"
    if n <= 8:
        return "5-8"
    return ">8"


def load_data() -> pd.DataFrame:
    """Read the campaign CSV and add the two derived columns """
    df = pd.read_csv(DATA_FILE)
    df["Responded"] = (df["Response_to_Campaign"] == "Yes").astype(int)
    df["Usage_Band"] = df["Unique_Products_Purchased"].apply(usage_band)
    return df


# Loaded once at startup. 

DF = load_data()


# -------------------------------------------------
# Analysis
# -------------------------------------------------
def response_rate_table(df: pd.DataFrame, column: str, order=None) -> pd.DataFrame:
    """Customers, responders and response rate (%) for each value of `column`."""
    grouped = df.groupby(column, observed=True).agg(
        Customers=("Responded", "size"),
        Responders=("Responded", "sum"),
    )
    grouped["Response_Rate_%"] = (
        grouped["Responders"] / grouped["Customers"] * 100
    ).round(2)

    if order:
        grouped = grouped.reindex(order)

    return grouped.reset_index().rename(columns={column: "Segment"})


def build_all_tables(df: pd.DataFrame) -> dict:
    """The four tables the campaign analysis calls for."""
    return {
        "Gender vs Campaign Response": response_rate_table(df, "Gender"),
        "Age Group vs Campaign Response": response_rate_table(df, "AgeGroup", AGE_ORDER),
        "Purchase in Last Quarter vs Campaign Response": response_rate_table(
            df, "Purchase_Last_Quarter", PURCHASE_ORDER
        ),
        "Product Usage vs Campaign Response": response_rate_table(
            df, "Usage_Band", USAGE_ORDER
        ),
    }


def overall_stats(df: pd.DataFrame) -> dict:
    responders = int(df["Responded"].sum())
    total = int(len(df))
    return {
        "total_customers": total,
        "total_responders": responders,
        "overall_response_rate_%": round(responders / total * 100, 2),
    }


# -------------------------------------------------
# Health check endpoint
# -------------------------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Skin Clinic Campaign Analysis API is running",
        "rows_loaded": int(len(DF)),
    }


# -------------------------------------------------
# JSON endpoint (Excel / VBA / Power Query friendly)
# -------------------------------------------------
@app.get("/campaign-analysis/json")
def campaign_analysis_json():
    tables = build_all_tables(DF)
    return {
        "overall": overall_stats(DF),
        "tables": {
            name: table.to_dict(orient="records") for name, table in tables.items()
        },
    }


# -------------------------------------------------
# HTML endpoint 
# -------------------------------------------------
def table_to_html(title: str, table: pd.DataFrame) -> str:
    rows = "".join(
        "<tr>"
        f"<td class='seg'>{segment}</td>"
        f"<td>{customers:,}</td>"
        f"<td>{responders:,}</td>"
        f"<td class='rate'>{rate:.2f}%</td>"
        "</tr>"
        for segment, customers, responders, rate in zip(
            table["Segment"],
            table["Customers"],
            table["Responders"],
            table["Response_Rate_%"],
        )
    )
    return f"""
    <section>
      <h2>{title}</h2>
      <table>
        <thead>
          <tr>
            <th>Segment</th>
            <th>Customers</th>
            <th>Responders</th>
            <th>Response Rate (%)</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    """


@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis():
    tables = build_all_tables(DF)
    stats = overall_stats(DF)

    sections = "".join(table_to_html(name, t) for name, t in tables.items())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Skin Clinic Campaign Analysis</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      margin: 0;
      padding: 40px 16px;
      background: #f7f8fa;
      color: #1c1f23;
    }}
    .wrap {{ max-width: 880px; margin: 0 auto; }}
    h1 {{ font-size: 1.6rem; margin: 0 0 8px; }}
    .sub {{ color: #5b6470; margin: 0 0 28px; }}
    .headline {{
      background: #fff;
      border: 1px solid #e3e6ea;
      border-radius: 10px;
      padding: 18px 20px;
      margin-bottom: 28px;
    }}
    .headline strong {{ font-size: 1.5rem; }}
    section {{
      background: #fff;
      border: 1px solid #e3e6ea;
      border-radius: 10px;
      padding: 18px 20px;
      margin-bottom: 20px;
    }}
    h2 {{ font-size: 1.05rem; margin: 0 0 12px; color: #2c3440; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{
      border-bottom: 1px solid #eceef1;
      padding: 9px 10px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    th {{
      background: #f2f4f7;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: #5b6470;
    }}
    th:first-child, td.seg {{ text-align: left; }}
    td.rate {{ font-weight: 600; }}
    footer {{ color: #7b838f; font-size: 0.85rem; margin-top: 24px; }}
    footer a {{ color: #3f6ad8; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Skin Clinic Campaign Analysis</h1>
    <p class="sub">Response rates by customer segment</p>

    <div class="headline">
      Overall response rate:
      <strong>{stats["overall_response_rate_%"]:.2f}%</strong><br>
      {stats["total_responders"]:,} responders out of
      {stats["total_customers"]:,} customers targeted.
    </div>

    {sections}

    <footer>
      Machine-readable version: <a href="/campaign-analysis/json">/campaign-analysis/json</a>
    </footer>
  </div>
</body>
</html>"""


# -------------------------------------------------
# Landing page
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Skin Clinic Campaign Analysis API</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 60px auto; max-width: 620px; }
    li { margin: 8px 0; }
  </style>
</head>
<body>
  <h1>Skin Clinic Campaign Analysis API</h1>
  <p>Available endpoints:</p>
  <ul>
    <li><a href="/campaign-analysis">/campaign-analysis</a> &mdash; analysis tables (HTML)</li>
    <li><a href="/campaign-analysis/json">/campaign-analysis/json</a> &mdash; same results as JSON</li>
    <li><a href="/health">/health</a> &mdash; health check</li>
    <li><a href="/docs">/docs</a> &mdash; interactive API documentation</li>
  </ul>
</body>
</html>"""
