# Documentation claim auditor

This offline static auditor compares documented claims about the checked capability with Python source patterns. It examines the root README and Markdown under docs, excluding fenced code; inline code counts. It reports unsupported affirmative claims and denials contradicted by production evidence. Tests are reported separately.

```sh
pdf-extraction-claim-audit audit . --json --fail-on medium --ignore vendor/
python3 -m pdf_extraction_claim_audit --version
```

Exit status 0 means PASS, 2 means a finding meets the threshold, and 1 indicates an input or usage error. The default threshold is high; use medium to include test-only evidence. Ignore prefixes may be repeated. Source is parsed, never executed; symlinks, examples, fixtures, and documentation are excluded from source evidence.

Findings use these identifiers:

```
documented-pdf-extraction-claim-false
documented-no-pdf-extraction-claim-false
```

## Differentiation

This tool checks a distinct file-access capability. Other auditors cover spreadsheet, Word document and presentation reading; file generation; table extraction; OCR; and document field extraction. Invoice, receipt, identity, bank check, bank statement, tax form, pay stub, health insurance card, business card, credit card, contract, mortgage, resume, bill of lading, delivery note, carte grise, energy bill, marriage certificate, bank account details, nutrition facts label, material certificate, US mail, invoice splitting, multiple receipt detection, French health card, Indian passport, driver license, and vaccination card extraction are outside the phrase lists, as are document cropping, electronic signatures and payment processing.

## Limitations

Exact phrases can describe unrelated capabilities, an application, a job title, or a wrapper. A file object may already have been opened elsewhere. Static matching is not semantic judgment: dead code counts, alias chains may be missed, denial handling depends on the listed phrases, and each route must occur in one module. A listed opener with an argument counts even if only metadata is accessed. Empty constructors and an argument-free opener do not count; those in PyMuPDF create empty documents for writing. A bare page text method is too generic to count without a listed opener in the same module.

The following are not detected: writing via pypdf, PyMuPDF or reportlab; table operations via pdfplumber, Camelot or tabula; OCR via pytesseract; page rendering via pdf2image or PyMuPDF; low-level pdfminer operations; unstructured partitioning; external commands such as pdftotext, pdfinfo and LibreOffice; hand-written object-stream parsing; access to text, HTML, Markdown, images, Word documents, spreadsheets or presentations. External converters can therefore lead to findings. Scanned or image-only files need OCR first: the listed libraries access the text layer, which may be empty. The auditor cannot distinguish these files.

Mindee and Veryfi extract fields rather than the checked capability. Azure Document Intelligence, including prebuilt-read and prebuilt-layout, and Google Document AI use opaque model or processor identifiers. Eden AI has no documented model for the checked operation; Textract has no fixed fingerprint for it. LlamaParse provides general document parsing. Nanonets, Docsumo, ABBYY Vantage, Rossum, Klippa, Parseur and Extend use opaque identifiers or configure document type outside a generic upload call. None of these service calls count as evidence.
