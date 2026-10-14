"""Build the assignment DOCX report from the pipeline's machine-readable output."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
EP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
W = f"{{{WORD_NS}}}"

ET.register_namespace("w", WORD_NS)
ET.register_namespace("r", REL_NS)
ET.register_namespace("cp", CORE_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("ep", EP_NS)
ET.register_namespace("vt", VT_NS)
ET.register_namespace("", PKG_REL_NS)


def element(parent: ET.Element, tag: str, attributes: dict[str, str] | None = None) -> ET.Element:
    return ET.SubElement(parent, W + tag, attributes or {})


def add_run(paragraph: ET.Element, text: str, *, bold: bool = False, color: str | None = None) -> None:
    run = element(paragraph, "r")
    if bold or color:
        properties = element(run, "rPr")
        if bold:
            element(properties, "b")
        if color:
            element(properties, "color", {W + "val": color})
    text_node = element(run, "t")
    text_node.text = text
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def add_paragraph(
    body: ET.Element,
    text: str = "",
    *,
    style: str | None = None,
    bold: bool = False,
    page_break: bool = False,
) -> ET.Element:
    paragraph = element(body, "p")
    if style or page_break:
        properties = element(paragraph, "pPr")
        if style:
            element(properties, "pStyle", {W + "val": style})
    if page_break:
        run = element(paragraph, "r")
        element(run, "br", {W + "type": "page"})
    if text:
        add_run(paragraph, text, bold=bold)
    return paragraph


def add_table(body: ET.Element, headers: list[str], rows: list[list[str]]) -> None:
    table = element(body, "tbl")
    properties = element(table, "tblPr")
    element(properties, "tblStyle", {W + "val": "TableGrid"})
    element(properties, "tblW", {W + "w": "9360", W + "type": "dxa"})
    element(properties, "tblLayout", {W + "type": "autofit"})
    margins = element(properties, "tblCellMar")
    for edge in ("top", "start", "bottom", "end"):
        element(margins, edge, {W + "w": "100", W + "type": "dxa"})

    def add_row(values: list[str], header: bool = False) -> None:
        row = element(table, "tr")
        for value in values:
            cell = element(row, "tc")
            if header:
                cell_properties = element(cell, "tcPr")
                element(cell_properties, "shd", {W + "fill": "1F4E78", W + "val": "clear"})
            paragraph = element(cell, "p")
            run = element(paragraph, "r")
            run_properties = element(run, "rPr")
            if header:
                element(run_properties, "b")
                element(run_properties, "color", {W + "val": "FFFFFF"})
            text_node = element(run, "t")
            text_node.text = value

    add_row(headers, header=True)
    for values in rows:
        add_row(values)


def add_bullets(body: ET.Element, items: list[str]) -> None:
    for item in items:
        add_paragraph(body, f"- {item}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def report_body(report: dict[str, object], cleaned_rows: list[dict[str, str]]) -> ET.Element:
    document = ET.Element(W + "document")
    body = element(document, "body")

    add_paragraph(body, "WEEK 3 PROJECT REPORT", style="Title")
    add_paragraph(body, "Beauty & Wellness Product Data Cleaning and Preprocessing", style="Subtitle")
    add_paragraph(
        body,
        "A traceable walkthrough of the implemented pipeline, its synthetic demonstration, and its limits",
    )
    add_table(
        body,
        ["Report item", "Verified project detail"],
        [
            ["Purpose", "Assess and clean catalog-style beauty and personal-care product records"],
            ["Implementation", f"Python {report['python_version']}; pipeline {report['pipeline_version']}"],
            ["Data used for reported results", "Built-in synthetic 10-row demonstration; no external dataset was supplied or downloaded"],
            ["Run timestamp (UTC)", str(report["run_timestamp_utc"])],
            ["Dependency policy", "Pipeline and report builder use the Python standard library only"],
        ],
    )
    add_paragraph(
        body,
        "Evidence boundary: all numeric results in this report describe only the invented demonstration rows. "
        "They are not estimates about actual products, brands, markets, consumers, safety, or efficacy.",
    )
    add_paragraph(body, page_break=True)

    add_paragraph(body, "Contents", style="Heading1")
    add_bullets(
        body,
        [
            "1. Executive summary and objectives",
            "2. Data, schema, and analytical questions",
            "3. Step-by-step data handling method",
            "4. Demonstration results and interpretation",
            "5. Tools used and why",
            "6. Testing and reproducibility",
            "7. Limitations, risks, and next steps for real data",
            "8. Conclusion and references",
        ],
    )

    add_paragraph(body, "1. Executive summary and objectives", style="Heading1")
    add_paragraph(
        body,
        "The assignment implements a small, auditable CSV cleaning pipeline. It keeps raw field values available, "
        "standardizes selected fields, validates numeric values against explicit rules, and routes identity-incomplete "
        "records to a quarantine file instead of silently dropping them. Exact duplicate rows are recorded separately. "
        "The pipeline reconciles every input row into exactly one of three outcomes: cleaned, quarantined, or duplicate.",
    )
    add_paragraph(
        body,
        f"In the included synthetic run, {report['input_rows']} input rows resulted in "
        f"{report['exact_duplicates_removed']} exact duplicate, {report['quarantined_rows']} quarantined row(s), "
        f"and {report['cleaned_rows']} retained row(s). Reconciliation passed. The workflow is a cleaning "
        "demonstration, not a statistical study of a real catalog.",
    )
    add_paragraph(body, "Project objectives", style="Heading2")
    add_bullets(
        body,
        [
            "Preserve source values and make every normalization or issue visible.",
            "Reject missing identity rather than guessing product identity.",
            "Use explicit parsers and domain checks for size, price, rating, and review count.",
            "Produce separate cleaned, exception, duplicate, and machine-readable audit outputs.",
            "Make the result repeatable and verifiable with input/output checksums and regression tests.",
        ],
    )

    add_paragraph(body, "2. Data, schema, and analytical questions", style="Heading1")
    add_paragraph(
        body,
        "The pipeline requires eight CSV fields. One input row represents one source record, not necessarily one "
        "globally unique product: distinct variants or repeated source IDs are not merged unless every input value "
        "matches exactly.",
    )
    add_table(
        body,
        ["Field", "Expected meaning / handling"],
        [
            ["source_record_id", "Text identifier; required for retention; preserve leading zeroes."],
            ["product_name", "Display name; surrounding whitespace is trimmed; required for retention."],
            ["category", "Text category; known aliases map to canonical labels; unknown labels remain visible."],
            ["ingredients_text", "Source ingredient string; raw text retained; blank is reported as missing, not ingredient-free."],
            ["size", "Positive magnitude plus mL/L/g/kg unit; no mass-to-volume conversion."],
            ["price", "Non-negative decimal; only recognized currency markers and conventional comma grouping are parsed."],
            ["rating", "Numeric value validated against the documented-in-code 1–5 assumption."],
            ["review_count", "Non-negative integer; comma treated as thousands separator."],
        ],
    )
    add_paragraph(body, "Questions a future real-data analysis could address", style="Heading2")
    add_bullets(
        body,
        [
            "How complete are ingredient lists by category and data source?",
            "How are ratings and review counts distributed among records with valid observations?",
            "How do listed prices compare after currency, date, package size, and compatible units are verified?",
        ],
    )
    add_paragraph(
        body,
        "These questions remain proposed: the ten synthetic records are far too few and are not a probability sample. "
        "No population inference, hypothesis test, model, or causal conclusion is supported by this demonstration.",
    )

    add_paragraph(body, "3. Step-by-step data handling method", style="Heading1")
    steps = [
        ["1. Load and check schema", "Read CSV as text with UTF-8-with-BOM support; require all eight named columns; reject missing headers/required fields."],
        ["2. Establish row identity", "Assign the original CSV line number (header is line 1); compute an exact row signature across input columns."],
        ["3. Remove exact repeats with an audit trail", "Keep the first exact row; write each later identical row and its line number/reason to removed_duplicates.csv."],
        ["4. Gate critical identity", "Trim product name and source ID; quarantine rows missing either value and record a specific reason."],
        ["5. Preserve source text", "Write raw name/category/ingredient fields beside cleaned/normalized fields so representation changes remain auditable."],
        ["6. Normalize category labels", "Trim, collapse repeated whitespace, case-fold, and apply the explicit alias map; retain unmapped category text."],
        ["7. Parse and validate size", "Accept positive numeric magnitudes with mL, L, g, or kg; normalize unit spelling; flag missing, unparseable, or non-positive values."],
        ["8. Parse and validate price", "Recognize USD/EUR/GBP markers; accept a simple decimal and valid three-digit comma groups; reject negatives and ambiguous commas."],
        ["9. Validate rating and review count", "Assume a 1–5 rating scale; keep invalid/missing values blank with issue codes. Convert comma-grouped counts to non-negative integer strings."],
        ["10. Reconcile and publish", "Check cleaned constraints and row accounting; write three CSV outputs plus JSON metrics, assumptions, versions, and SHA-256 hashes."],
    ]
    add_table(body, ["Stage", "Implemented handling and decision"], steps)
    add_paragraph(
        body,
        "The pipeline does not impute missing values, infer product details, tokenize ingredients, convert currencies, "
        "convert mass to volume, or automatically delete statistical outliers. Those steps require source semantics "
        "or an explicit analytical objective and are intentionally not guessed.",
    )

    add_paragraph(body, "4. Demonstration results and interpretation", style="Heading1")
    add_paragraph(body, "Row-level accounting", style="Heading2")
    add_table(
        body,
        ["Outcome", "Observed count", "Meaning"],
        [
            ["Input rows", str(report["input_rows"]), "Ten invented CSV-like records."],
            ["Exact duplicates removed", str(report["exact_duplicates_removed"]), "One repeat of S001 across every input column."],
            ["Quarantined", str(report["quarantined_rows"]), "One row lacks a product name; source row retained with a reason."],
            ["Cleaned rows", str(report["cleaned_rows"]), "Eight identity-valid candidates retained; field issues remain flagged."],
            ["Reconciliation", "PASS" if report["row_reconciliation_passed"] else "FAIL", "10 = 1 duplicate + 1 quarantined + 8 cleaned."],
        ],
    )
    add_paragraph(body, "Issue and missingness summary", style="Heading2")
    issue_counts = report["issue_counts"]
    issue_rows = [[str(name), str(count)] for name, count in sorted(issue_counts.items())]
    add_table(body, ["Issue code", "Observed count"], issue_rows)
    field_counts = report["field_missing_counts_after_cleaning"]
    field_rates = report["field_missing_rates_after_cleaning"]
    missing_rows = [
        [str(name), str(count), f"{100 * float(field_rates[name]):.1f}%"]
        for name, count in field_counts.items()
    ]
    add_table(body, ["Input field", "Blank after cleaning", "Rate among cleaned rows"], missing_rows)
    add_paragraph(
        body,
        f"Among the {report['cleaned_rows']} retained rows, ingredient text is missing for "
        f"{100 * float(report['missing_ingredient_rate']):.1f}% (1/8). Ratings are missing or invalid for "
        f"{100 * float(report['rating_missing_or_invalid_rate']):.1f}% (2/8): one blank value and one value of 8.2, "
        "outside the assumed 1–5 range. One negative price is retained as a raw value and flagged, with the parsed "
        "price left blank. The string “1,200” is parsed as 1200 under the stated thousands-separator assumption.",
    )
    category_counts = report["category_counts_after_cleaning"]
    category_rows = [
        [str(category), str(count), f"{100 * int(count) / int(report['cleaned_rows']):.1f}%"]
        for category, count in category_counts.items()
    ]
    valid_ratings = [
        float(row["rating_value"]) for row in cleaned_rows if row.get("rating_value")
    ]
    valid_usd_prices = [
        float(row["price_value"])
        for row in cleaned_rows
        if row.get("price_value") and row.get("currency") == "USD"
    ]
    add_paragraph(body, "Descriptive numeric checks", style="Heading2")
    add_table(
        body,
        ["Measure", "Valid n", "Mean", "Median", "Interpretation"],
        [
            [
                "Rating (assumed 1–5 scale)",
                str(len(valid_ratings)),
                f"{statistics.mean(valid_ratings):.2f}" if valid_ratings else "N/A",
                f"{statistics.median(valid_ratings):.2f}" if valid_ratings else "N/A",
                "Describes only valid ratings in the synthetic fixture.",
            ],
            [
                "USD listed price",
                str(len(valid_usd_prices)),
                f"{statistics.mean(valid_usd_prices):.2f}" if valid_usd_prices else "N/A",
                f"{statistics.median(valid_usd_prices):.2f}" if valid_usd_prices else "N/A",
                "Not adjusted for package size, promotion, date, or market.",
            ],
        ],
    )
    add_paragraph(body, "Normalized categories", style="Heading2")
    add_table(body, ["Category", "Rows", "Share of 8 cleaned rows"], category_rows)
    add_paragraph(
        body,
        "Category counts are a check that the alias rules worked, not evidence of category market share. The small "
        "synthetic fixture also intentionally includes an unmapped “face oil” value to show that unknown labels are "
        "kept rather than discarded.",
    )

    add_paragraph(body, "5. Tools used and why", style="Heading1")
    add_table(
        body,
        ["Tool / module", "Actual use in this submission"],
        [
            ["Python 3.13.15", "Language/runtime used for pipeline and regression tests."],
            ["csv", "DictReader/DictWriter parse and write quoted CSV records while preserving identifiers as strings."],
            ["argparse", "Exposes input path, --demo mode, and --output-dir through a reproducible command-line interface."],
            ["re", "Constrains supported size, price, and count formats rather than relying on permissive coercion."],
            ["json", "Stores machine-readable quality metrics, assumptions, and provenance/checksum metadata."],
            ["hashlib", "Computes SHA-256 digests of inputs and produced CSV outputs for integrity comparison."],
            ["pathlib, datetime, collections, platform", "Portable paths, UTC timestamp, issue/category counters, and runtime version."],
            ["unittest, tempfile", "Runs deterministic parser, schema, row-accounting, identifier, and output-hash tests."],
            ["PowerShell / VS Code", "Used to run the CLI/tests and inspect the workspace outputs."],
            ["No pandas, NumPy, scikit-learn, matplotlib, or seaborn", "These packages are not installed or used by this standard-library implementation; no charts or ML model are claimed."],
        ],
    )
    add_paragraph(
        body,
        "The prior report draft listed third-party analytics libraries as primary tools and included a separate pandas "
        "implementation template. That did not match the submitted code. This revised report describes only the tools "
        "actually used and lists future analytical options as recommendations, not completed work.",
    )

    add_paragraph(body, "6. Testing and reproducibility", style="Heading1")
    add_paragraph(
        body,
        "The regression suite contains nine standard-library tests. It checks size/unit behavior; price currencies, "
        "negative and ambiguous values; rating/count boundaries; known and unknown categories; the 10→1→1→8 demo "
        "accounting; preservation of leading-zero IDs; required-column rejection; and consistency of saved output hashes.",
    )
    add_paragraph(body, "Repeatable execution", style="Heading2")
    add_paragraph(body, "Demo: .\\.venv\\Scripts\\python.exe .\\beauty_wellness_pipeline.py --demo")
    add_paragraph(body, "Tests: .\\.venv\\Scripts\\python.exe -m unittest -v")
    add_paragraph(
        body,
        "For a CSV: .\\.venv\\Scripts\\python.exe .\\beauty_wellness_pipeline.py .\\products.csv --output-dir .\\results",
    )
    add_paragraph(body, f"Input SHA-256: {report['input_sha256']}")
    add_paragraph(body, "Output CSV SHA-256 values", style="Heading2")
    hash_rows = [[str(name), str(digest)] for name, digest in report["output_sha256s"].items()]
    add_table(body, ["Output file", "SHA-256"], hash_rows)
    add_paragraph(
        body,
        "The JSON run report includes a UTC timestamp, Python and pipeline versions, and the hashes above. The timestamp "
        "and absolute source path are expected to differ between executions. Compare input and output hashes—not the "
        "entire JSON file—to verify equivalent bytes. Hashes support integrity checking; they do not prove source accuracy, "
        "license compliance, or that the file is an immutable archive.",
    )
    add_paragraph(
        body,
        "For stronger production reproducibility, archive the exact original source bytes and extraction query, record "
        "source/license/version and retrieval time, pin a runtime, preserve configuration and mapping tables, and retain "
        "a decision log. A hash alone cannot recreate a source file that was not retained.",
    )

    add_paragraph(body, "7. Limitations, risks, and next steps for real data", style="Heading1")
    add_bullets(
        body,
        [
            "No real source snapshot or assignment-specific external dataset is present in the workspace; therefore there are no real-data EDA findings.",
            "The 1–5 rating scale and comma-as-thousands convention must be verified against a real source before parsing.",
            "Deduplication removes exact row repeats only. Near-duplicates, repeated IDs with conflicting product variants, and barcode conflicts need a separate review policy.",
            "Prices without recognized currency markers are parsed with an empty currency field; currency conversion and date alignment are not implemented.",
            "Only the listed size formats are supported; package counts, fluid ounces, locale-specific decimals, dates, and Unicode normalization need source-specific rules.",
            "The pipeline reports selected field missingness and issue counts, but it does not produce distribution plots, robust outlier diagnostics, source coverage analysis, or modeling features.",
            "Synthetic findings must not be presented as product-market facts or as evidence of safety, efficacy, consumer preference, or sales.",
        ],
    )
    add_paragraph(body, "Before a real-data resubmission", style="Heading2")
    add_bullets(
        body,
        [
            "Obtain the exact task brief/rubric and identify the required dataset, geography, time period, question, and expected deliverables.",
            "Use a legally permitted, documented source; save an immutable dated snapshot, schema, extraction details, attribution/license, and checksum.",
            "Profile the real snapshot before cleaning: shape, dtypes, missingness by field, duplicate and conflicting keys, category frequencies, parse failures, and numeric distributions.",
            "Review quarantine and ambiguous currency/unit/identity cases with evidence; document decisions and denominators.",
            "Add source-specific tests, rerun the full pipeline, regenerate this report from the resulting JSON, and verify the report against actual output files.",
        ],
    )

    add_paragraph(body, "8. Conclusion and references", style="Heading1")
    add_paragraph(
        body,
        "The revised deliverable connects the implementation to its data-handling choices, observed synthetic counts, "
        "tests, and reproducibility evidence. It is a transparent preprocessing prototype. To make substantive claims "
        "or earn credit for empirical analysis, it must be paired with the dataset and exact evaluation criteria required "
        "by the internship assignment; no score can be guaranteed from code/report formatting alone.",
    )
    add_paragraph(body, "References and further reading", style="Heading2")
    add_bullets(
        body,
        [
            "Python Software Foundation. csv — CSV File Reading and Writing. https://docs.python.org/3/library/csv.html",
            "Python Software Foundation. argparse — Parser for Command-Line Options. https://docs.python.org/3/library/argparse.html",
            "Python Software Foundation. hashlib — Secure Hashes and Message Digests. https://docs.python.org/3/library/hashlib.html",
            "Python Software Foundation. unittest — Unit Testing Framework. https://docs.python.org/3/library/unittest.html",
        ],
    )
    add_paragraph(
        body,
        "The references describe standard-library behavior used by this implementation. No external product dataset "
        "or third-party statistical method was used for the numerical results in this report.",
    )

    section = element(body, "sectPr")
    element(section, "pgSz", {W + "w": "12240", W + "h": "15840"})
    element(
        section,
        "pgMar",
        {
            W + "top": "900",
            W + "right": "900",
            W + "bottom": "900",
            W + "left": "900",
            W + "header": "450",
            W + "footer": "450",
            W + "gutter": "0",
        },
    )
    return document


def make_styles() -> ET.Element:
    styles = ET.Element(W + "styles")
    defaults = element(styles, "docDefaults")
    run_defaults = element(defaults, "rPrDefault")
    run_properties = element(run_defaults, "rPr")
    element(run_properties, "rFonts", {W + "ascii": "Aptos", W + "hAnsi": "Aptos"})
    element(run_properties, "sz", {W + "val": "20"})
    paragraph_defaults = element(defaults, "pPrDefault")
    paragraph_properties = element(paragraph_defaults, "pPr")
    element(paragraph_properties, "spacing", {W + "after": "120", W + "line": "276", W + "lineRule": "auto"})

    definitions = [
        ("Normal", "paragraph", None, "222222", "20"),
        ("Title", "paragraph", "Title", "1F4E78", "36"),
        ("Subtitle", "paragraph", "Subtitle", "5B6573", "24"),
        ("Heading1", "paragraph", "Heading 1", "1F4E78", "28"),
        ("Heading2", "paragraph", "Heading 2", "2F75B5", "22"),
    ]
    for style_id, style_type, name, color, size in definitions:
        style = element(styles, "style", {W + "type": style_type, W + "styleId": style_id})
        if style_id != "Normal":
            element(style, "name", {W + "val": name or style_id})
        if style_id.startswith("Heading"):
            element(style, "basedOn", {W + "val": "Normal"})
            element(style, "next", {W + "val": "Normal"})
            element(style, "uiPriority", {W + "val": "9"})
            element(style, "keepNext")
        ppr = element(style, "pPr")
        if style_id in ("Title", "Subtitle"):
            element(ppr, "spacing", {W + "before": "180", W + "after": "240"})
        elif style_id.startswith("Heading"):
            element(ppr, "spacing", {W + "before": "240", W + "after": "100"})
        rpr = element(style, "rPr")
        element(rpr, "rFonts", {W + "ascii": "Aptos", W + "hAnsi": "Aptos"})
        element(rpr, "color", {W + "val": color})
        element(rpr, "sz", {W + "val": size})
        if style_id != "Normal":
            element(rpr, "b")
    table_style = element(styles, "style", {W + "type": "table", W + "styleId": "TableGrid"})
    element(table_style, "name", {W + "val": "Table Grid"})
    return styles


def make_content_types() -> ET.Element:
    root = ET.Element(f"{{{CONTENT_NS}}}Types")
    ET.SubElement(root, f"{{{CONTENT_NS}}}Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(root, f"{{{CONTENT_NS}}}Default", {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(root, f"{{{CONTENT_NS}}}Override", {"PartName": "/word/document.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"})
    ET.SubElement(root, f"{{{CONTENT_NS}}}Override", {"PartName": "/word/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"})
    ET.SubElement(root, f"{{{CONTENT_NS}}}Override", {"PartName": "/docProps/core.xml", "ContentType": "application/vnd.openxmlformats-package.core-properties+xml"})
    ET.SubElement(root, f"{{{CONTENT_NS}}}Override", {"PartName": "/docProps/app.xml", "ContentType": "application/vnd.openxmlformats-officedocument.extended-properties+xml"})
    return root


def make_relationships() -> ET.Element:
    root = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    ET.SubElement(
        root,
        f"{{{PKG_REL_NS}}}Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "word/document.xml",
        },
    )
    return root


def make_document_relationships() -> ET.Element:
    root = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    ET.SubElement(
        root,
        f"{{{PKG_REL_NS}}}Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            "Target": "styles.xml",
        },
    )
    return root


def make_core_properties() -> ET.Element:
    root = ET.Element(f"{{{CORE_NS}}}coreProperties")
    ET.SubElement(root, f"{{{DC_NS}}}title").text = "Week 3 Beauty & Wellness Data Preprocessing Report"
    ET.SubElement(root, f"{{{DC_NS}}}subject").text = "Data quality, cleaning, and reproducibility"
    ET.SubElement(root, f"{{{DC_NS}}}creator").text = "Beauty & Wellness Data Preprocessing Assignment"
    ET.SubElement(root, f"{{{CORE_NS}}}revision").text = "2"
    return root


def make_app_properties() -> ET.Element:
    root = ET.Element(f"{{{EP_NS}}}Properties")
    ET.SubElement(root, f"{{{EP_NS}}}Application").text = "Python standard-library DOCX builder"
    return root


def write_report(report_path: Path, cleaned_path: Path, output_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("source") != "built-in synthetic demonstration":
        raise ValueError(
            "This assignment report template is specific to the built-in synthetic demonstration."
        )
    cleaned_rows = read_csv_rows(cleaned_path)
    document = report_body(report, cleaned_rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", ET.tostring(make_content_types(), encoding="utf-8", xml_declaration=True))
        archive.writestr("_rels/.rels", ET.tostring(make_relationships(), encoding="utf-8", xml_declaration=True))
        archive.writestr("word/document.xml", ET.tostring(document, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/styles.xml", ET.tostring(make_styles(), encoding="utf-8", xml_declaration=True))
        archive.writestr("word/_rels/document.xml.rels", ET.tostring(make_document_relationships(), encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/core.xml", ET.tostring(make_core_properties(), encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/app.xml", ET.tostring(make_app_properties(), encoding="utf-8", xml_declaration=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("beauty_wellness_output/quality_report.json"))
    parser.add_argument("--cleaned", type=Path, default=Path("beauty_wellness_output/cleaned_products.csv"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Week_3_Beauty_Wellness_Data_Preprocessing_Report.docx"),
    )
    args = parser.parse_args()
    if not args.report.is_file():
        parser.error(f"quality report not found: {args.report}")
    if not args.cleaned.is_file():
        parser.error(f"cleaned CSV not found: {args.cleaned}")
    write_report(args.report, args.cleaned, args.output)
    print(f"Report written: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
