Beauty & Wellness Demand Planner

A Python application for the Week 2 internship task Data
Identification, Sourcing Strategy & Initial Analysis Planning. It
generates a Word report describing a beauty and wellness data-sourcing
strategy. If you provide a monthly demand CSV, it can also validate and
aggregate the data, perform exploratory summaries, evaluate baseline
forecasting models, and include results in the report.

Features

Desktop interface built with tkinter.

Command-line interface for generating a Week 2 .docx report.

Generates a report without an input dataset.

Optional CSV analysis for monthly demand or sales.

Optional exact-match filtering by product category and
region/country.

Validates dates and demand values; records accepted, rejected, and
filtered rows.

Aggregates demand by month and summarizes optional search-interest,
promotion, and price fields.

Handles missing months using error, zero, or interpolate
policies.

Evaluates baseline forecasting approaches and can produce forecasts
for 1--24 months when the data and missing-month policy permit.

Includes candidate data sources, collection steps, quality
considerations, and analysis planning in the generated report.

Uses Python standard-library modules; no third-party packages are
required by the application itself.

Requirements

Python 3.10 or later is recommended.

tkinter is needed for the desktop interface and is included with
many Python installations. If it is unavailable, use command-line
mode.

A CSV dataset is optional. Without one, the application generates
the sourcing-strategy report only.

Files

Save the Python code from this project as:

week2_app.py

The repository can be organized like this:

beauty-wellness-demand-planner/
├── week2_app.py
├── README.md
├── monthly_demand.csv                 # optional input dataset
└── week2_data_sourcing_strategy.docx   # generated report

Run the application

Open Command Prompt or a terminal in the folder containing
week2_app.py.

Open the desktop application

python week2_app.py

In the app, enter a category and region, choose an output .docx path,
and optionally select a CSV file. Then click Generate Week 2 DOCX.

Generate a report from the command line

python week2_app.py --output week2_data_sourcing_strategy.docx

Choose a category, region, and forecast horizon:

python week2_app.py --category skincare --region India --horizon 3 --output week2_report.docx

Analyze a CSV and generate the report:

python week2_app.py --input monthly_demand.csv --category skincare --region India --horizon 3 --output week2_report.docx

Choose how missing months are handled:

python week2_app.py --input monthly_demand.csv --missing-policy error --output week2_report.docx

Available policies are:

error --- default; withholds forecasting when months are missing.

zero --- fills absent months with zero demand. Use only if a
missing month truly represents zero demand.

interpolate --- estimates values for missing months by
interpolation. Treat these values as estimates, not observed sales.

The forecast horizon must be between 1 and 24 months. Use the built-in
end-to-end self-test with:

python week2_app.py --self-test

View all command-line options:

python week2_app.py --help

CSV input format

The CSV must have a header row and include:

A date column named date or month.

A demand column named demand, sales, or units_sold.

Optional columns:

category --- exact-match category filter.

region or country --- exact-match region/country filter.

search_interest --- numeric relative index from 0 to 100.

promotion --- numeric value or a yes/no-style value.

price --- non-negative numeric price.

Header matching is case-insensitive. Date values can use formats such as
YYYY-MM-DD or YYYY-MM; additional supported formats are checked by
the application. Demand values must be numeric and non-negative. Rows
outside the selected category/region are filtered out; rows with invalid
dates or demand values are rejected.

Example CSV:

date,demand,search_interest,promotion,price,category,region
2025-01-01,120,45,0,250,skincare,India
2025-02-01,135,52,1,240,skincare,India
2025-03-01,128,49,0,250,skincare,India
2025-04-01,150,61,1,230,skincare,India
2025-05-01,142,58,0,250,skincare,India
2025-06-01,160,67,1,225,skincare,India

These values are illustrative sample data, not real market observations.
The example is too short for a reliable business forecast; use a longer,
continuous history where possible. The program defines a minimum
training history for forecasting, and results should be treated as
exploratory baselines.

Data sources discussed in the report

The report includes candidate sources and explains their possible use
and limitations:

Google
Trends
--- relative search interest, not search counts or sales.

Open Government Data Platform India ---
discovery of relevant public datasets.

MoSPI eSankhyiki --- official
statistical and price context.

UN Comtrade API --- international
trade data, not direct retail demand.

World Bank Indicators
API
--- macroeconomic indicators, often at a coarser frequency than
monthly sales.

Amazon Reviews 2023 ---
review and product information, subject to dataset and platform
terms.

Open Beauty Facts ---
product and ingredient metadata.

Meta Ad Library ---
advertising context, not sales or conversion data.

These are discovery starting points. The application does not
automatically download data from these websites. Before using a source,
verify that the exact dataset exists, covers the required dates and
geography, has suitable fields, and can legally be accessed and reused.

Recommended data strategy

For actual demand forecasting, prioritize an authorized point-of-sale,
retailer, or commerce export as the target dataset. Define the demand
measure (for example, net units sold), product/category mapping, region,
time period, and treatment of returns and stock-outs before analysis.
Use public search, review, trade, price, or advertising information only
as optional supporting signals when their definitions and dates align
with the sales data.

Limitations

The tool generates a report and analyzes a supplied CSV; it is not a
live data collection service.

Public indicators and review/ad activity are proxies or context, not
substitutes for actual sales.

Forecasts depend on data quality, history length, missing-month
handling, and model assumptions. They are not guaranteed sales or
inventory recommendations.

Confirm the data source's license, access permissions, definitions,
and update frequency before using it in an internship submission or
business decision.

Project purpose

This project supports a beauty and wellness data-science workflow by
documenting possible data sources, assessing their relevance and
limitations, and planning initial analysis of monthly demand.

