# Beauty & Wellness Product Data Cleaning Pipeline

This Week 3 assignment demonstrates a reproducible data-quality workflow for a
beauty and personal-care product catalog. The pipeline uses only Python's
standard library. Its built-in ten-row fixture is synthetic; it is suitable for
checking transformations, not for claims about a real market or product
population.

## Run the demonstration

From this folder:

```powershell
.\.venv\Scripts\python.exe .\beauty_wellness_pipeline.py --demo
```

Or process a CSV with the required columns:

```powershell
.\.venv\Scripts\python.exe .\beauty_wellness_pipeline.py .\products.csv --output-dir .\results
```

Required CSV headers are `source_record_id`, `product_name`, `category`,
`ingredients_text`, `size`, `price`, `rating`, and `review_count`. Keep IDs
(including barcodes) as text so leading zeroes are not lost. Ratings are
assumed to use a 1–5 scale; review-count commas are treated as thousands
separators. Confirm those source conventions before using real data.

## Outputs

- `cleaned_products.csv`: identity-valid rows, original values, normalized
  fields, and field-level issue flags.
- `quarantined_rows.csv`: rows missing a source record ID or product name,
  with a reason for each quarantine.
- `removed_duplicates.csv`: rows exactly matching an earlier row across the
  input columns.
- `quality_report.json`: row reconciliation, issue counts, category counts,
  missingness counts/rates, assumptions, runtime version, input SHA-256, and
  output CSV SHA-256 checksums.

The report timestamp and absolute input path can differ between runs. With the
same input bytes, Python/pipeline version, and configuration, CSV contents
should be stable; verify them using the recorded SHA-256 checksums.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Tests cover parsing, domain rules, row accounting, preservation of leading-zero
IDs, schema rejection, and checksum metadata.

## Regenerate the assignment report

After running the synthetic demo:

```powershell
.\.venv\Scripts\python.exe .\build_assignment_report.py
```

The report builder uses only the standard library and intentionally refuses
to describe a non-demo dataset with synthetic-only conclusions.

## Assignment report

See [Week_3_Beauty_Wellness_Data_Preprocessing_Report.docx](./Week_3_Beauty_Wellness_Data_Preprocessing_Report.docx)
for the methods, step-by-step handling decisions, interpretation of the demo
results, tools, reproducibility notes, limitations, and suggested next steps
for a legally usable real dataset.
