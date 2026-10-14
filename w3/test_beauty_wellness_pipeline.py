"""Regression tests for the beauty and wellness product cleaning pipeline."""

import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import build_assignment_report
import beauty_wellness_pipeline as pipeline


class ParsingTests(unittest.TestCase):
    def test_size_normalizes_unit_without_converting_dimensions(self) -> None:
        self.assertEqual(pipeline.parse_size("50ml"), ("50", "mL", ""))
        self.assertEqual(pipeline.parse_size("40 g"), ("40", "g", ""))
        self.assertEqual(pipeline.parse_size("0 ml"), ("", "mL", "size_not_positive"))
        self.assertEqual(
            pipeline.parse_size("1 fl oz"),
            ("", "", "size_unparseable"),
        )

    def test_price_parses_known_currencies_and_rejects_ambiguous_commas(self) -> None:
        self.assertEqual(pipeline.parse_price("$18.00"), ("18", "USD", ""))
        self.assertEqual(pipeline.parse_price("EUR 24"), ("24", "EUR", ""))
        self.assertEqual(
            pipeline.parse_price("1,25"),
            ("", "", "price_ambiguous_or_unparseable"),
        )
        self.assertEqual(pipeline.parse_price("-3.00"), ("", "", "price_negative"))

    def test_rating_and_review_count_domain_checks(self) -> None:
        self.assertEqual(pipeline.parse_rating("4.5"), ("4.5", ""))
        self.assertEqual(pipeline.parse_rating("8.2"), ("", "rating_out_of_range"))
        self.assertEqual(pipeline.parse_review_count("1,200"), ("1200", ""))
        self.assertEqual(
            pipeline.parse_review_count("-1"),
            ("", "review_count_unparseable"),
        )

    def test_category_aliases_and_unknown_values_are_preserved(self) -> None:
        self.assertEqual(pipeline.normalize_category(" Moisturiser "), "moisturizer")
        self.assertEqual(pipeline.normalize_category("Face Oil"), "face oil")
        self.assertEqual(pipeline.normalize_category(""), "")


class CleaningTests(unittest.TestCase):
    def test_demo_row_accounting_flags_and_missingness(self) -> None:
        cleaned, quarantined, duplicates, report = pipeline.clean_records(
            [dict(row) for row in pipeline.DEMO_ROWS],
            list(pipeline.REQUIRED_COLUMNS),
        )

        self.assertEqual((len(cleaned), len(quarantined), len(duplicates)), (8, 1, 1))
        self.assertTrue(report["row_reconciliation_passed"])
        self.assertEqual(report["field_missing_counts_after_cleaning"]["ingredients_text"], 1)
        self.assertEqual(report["field_missing_rates_after_cleaning"]["ingredients_text"], 0.125)
        self.assertEqual(report["missing_ingredient_rate"], 0.125)
        self.assertEqual(report["rating_missing_or_invalid_rate"], 0.25)
        self.assertEqual(cleaned[0]["product_name_raw"], " Glow Serum ")
        self.assertEqual(cleaned[0]["product_name"], "Glow Serum")
        self.assertEqual(quarantined[0]["quarantine_reason"], "missing_product_name")
        self.assertEqual(duplicates[0]["duplicate_reason"], "exact_duplicate")

    def test_csv_loader_preserves_identifier_leading_zeroes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "products.csv"
            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=pipeline.REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "source_record_id": "000123",
                        "product_name": "Example",
                        "category": "Serum",
                        "ingredients_text": "",
                        "size": "30 ml",
                        "price": "12.50",
                        "rating": "4",
                        "review_count": "0",
                    }
                )

            records, _ = pipeline.load_csv(input_path)

        self.assertEqual(records[0]["source_record_id"], "000123")

    def test_csv_loader_rejects_missing_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "incomplete.csv"
            input_path.write_text("product_name\nExample\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                pipeline.load_csv(input_path)

    def test_demo_run_writes_reproducibility_metadata_and_matching_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "outputs"
            report = pipeline.run_pipeline(None, output_dir, use_demo=True)

            saved_report = json.loads(
                (output_dir / "quality_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["input_sha256"], saved_report["input_sha256"])
            self.assertEqual(report["pipeline_version"], pipeline.PIPELINE_VERSION)
            self.assertTrue(report["python_version"])
            self.assertEqual(
                set(report["output_sha256s"]),
                {
                    "cleaned_products.csv",
                    "quarantined_rows.csv",
                    "removed_duplicates.csv",
                },
            )
            for filename, expected_digest in report["output_sha256s"].items():
                self.assertEqual(pipeline.sha256_file(output_dir / filename), expected_digest)

    def test_report_builder_creates_readable_docx_from_demo_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "outputs"
            pipeline.run_pipeline(None, output_dir, use_demo=True)
            report_path = Path(temporary_directory) / "assignment.docx"

            build_assignment_report.write_report(
                output_dir / "quality_report.json",
                output_dir / "cleaned_products.csv",
                report_path,
            )

            self.assertTrue(zipfile.is_zipfile(report_path))
            with zipfile.ZipFile(report_path) as archive:
                document = ElementTree.fromstring(archive.read("word/document.xml"))
            text = "".join(
                node.text or ""
                for node in document.iter(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
                )
            )
            self.assertIn("Step-by-step data handling method", text)
            self.assertIn("synthetic demonstration", text)


if __name__ == "__main__":
    unittest.main()
