import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pdf_extraction_claim_audit.audit import audit, evidence
from pdf_extraction_claim_audit.phrases import PDFEXTRACTION, NOPDFEXTRACTION, GENERIC_NAMES
from pdf_extraction_claim_audit.__main__ import main

YES = ('pdf extraction', 'extract pdf', 'extracts pdf', 'extracting pdf', 'extract pdf text', 'extracts pdf text', 'extracting pdf text', 'extract text from pdf', 'extracts text from pdf', 'extract pdf content', 'extract pdf files', 'extract pdf file', 'extract pdf document', 'extract pdf documents', 'read pdf', 'reads pdf', 'reading pdf', 'read pdf file', 'reads pdf file', 'reading pdf file', 'read pdf document', 'load pdf', 'loads pdf', 'loading pdf', 'load pdf file', 'loads pdf file', 'loading pdf file', 'load pdf document', 'open pdf', 'opens pdf', 'opening pdf', 'open pdf file', 'opens pdf file', 'opening pdf file', 'parse pdf', 'parses pdf', 'parsing pdf', 'parse pdf file', 'parses pdf file', 'parsing pdf file', 'pdf text extraction', 'pdf reader', 'pdf parser', 'pdf extractor', 'pdf text extractor', 'pdf content extraction', 'pdf file reading', 'pdf document reading', 'pdf loading', 'extract text from pdf file')
NO = ('no pdf extraction', 'does not extract pdf', 'does not extract pdf text', 'does not support pdf extraction', 'without pdf extraction', 'no pdf reader', 'does not read pdf', 'does not read pdf file', 'does not load pdf', 'does not load pdf file', 'does not open pdf', 'does not open pdf file', 'does not parse pdf', 'does not parse pdf file', 'does not extract text from pdf', 'no pdf parser', 'does not read pdf document', 'does not extract pdf file', 'does not extract pdf document', 'no pdf extractor', 'does not extract pdf content', 'pdf extraction not supported', 'no pdf extraction support', 'no pdf text extraction')
GENERIC = ('read_pdf', 'read_pdf_file', 'load_pdf', 'load_pdf_file', 'open_pdf', 'open_pdf_file', 'parse_pdf', 'parse_pdf_file', 'extract_pdf', 'extract_pdf_text', 'extract_text_from_pdf', 'extract_pdf_content', 'extract_pdf_file', 'extract_pdf_document', 'read_pdf_document', 'load_pdf_document', 'pdf_reader', 'pdf_parser', 'pdf_extractor', 'read_pdfs', 'load_pdfs', 'extract_pdfs', 'pdf_text_extractor', 'extract_pdf_text_from_file')

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'pdf_extraction_claim_audit', *args], capture_output=True, text=True)
    def test_oracle(self):
        self.assertEqual((PDFEXTRACTION, NOPDFEXTRACTION, GENERIC_NAMES), (YES, NO, GENERIC))
    def test_findings(self):
        self.write('README.md', 'read pdf')
        self.assertEqual(audit(self.root)['findings'][0]['rule'], 'documented-pdf-extraction-claim-false')
        self.assertEqual(self.cli('audit', str(self.root)).returncode, 2)
        self.write('tests/test_a.py', 'import pypdf\npypdf.PdfReader("x")')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.assertEqual(self.cli('audit', str(self.root)).returncode, 0)
        self.assertEqual(self.cli('audit', str(self.root), '--fail-on', 'medium').returncode, 2)
        self.write('app.py', 'import pypdf\npypdf.PdfReader("x")')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.write('README.md', 'does not read pdf')
        self.assertEqual(audit(self.root)['findings'][0]['rule'], 'documented-no-pdf-extraction-claim-false')
        self.assertEqual(self.cli('audit', str(self.root)).returncode, 2)
        self.write('README.md', 'unrelated')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_docs(self):
        self.write('README.md', 'does not read pdf')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.write('README.md', '```\nread pdf\n```')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.write('README.md', '`read pdf`')
        self.assertEqual(audit(self.root)['verdict'], 'FAIL')
        self.write('README.md', 'unrelated')
        self.write('docs/a.md', 'read pdf')
        self.assertEqual(audit(self.root, ['docs/'])['verdict'], 'PASS')
    def test_routes(self):
        cases = ['from pypdf import PdfReader as P\nP("x")', 'import pypdf\npypdf.PdfReader("x")', 'import pypdf as p\np.PdfReader("x")', 'from pypdf import PdfReader\nPdfReader(stream="x")', 'from PyPDF2 import PdfReader\nPdfReader("x")', 'import PyPDF2\nPyPDF2.PdfReader("x")', 'from PyPDF2 import PdfFileReader\nPdfFileReader("x")', 'import PyPDF2\nPyPDF2.PdfFileReader("x")', 'from pdfplumber import open as op\nop("x")', 'import pdfplumber\npdfplumber.open("x")', 'import pdfplumber\npdfplumber.open(path="x")', 'from fitz import open as op\nop("x")', 'import fitz\nfitz.open("x")', 'from fitz import Document\nDocument("x")', 'import fitz\nfitz.Document("x")', 'import pymupdf\npymupdf.open("x")', 'import pymupdf\npymupdf.Document("x")', 'from pdfminer.high_level import extract_text\nextract_text()', 'import pdfminer.high_level\npdfminer.high_level.extract_text()', 'from pdfminer.high_level import extract_pages\nextract_pages()', 'import pdfminer.high_level\npdfminer.high_level.extract_pages()', 'from pkg import read_pdf as f\nf()']
        cases += ['x.' + name + '()' for name in GENERIC]
        for source in cases:
            with self.subTest(source=source): self.assertTrue(evidence(source))
    def test_non_routes(self):
        cases = ['import ' + n for n in ('pypdf', 'PyPDF2', 'pdfplumber', 'fitz', 'pymupdf', 'pdfminer', 'camelot', 'tabula')]
        cases += ['import pypdf\npypdf.PdfReader()', 'import PyPDF2\nPyPDF2.PdfFileReader()', 'import pdfplumber\npdfplumber.open()', 'import fitz\nfitz.open()', 'import fitz\nfitz.Document()', 'import pypdf\npypdf.PdfWriter().write("x")', 'import fitz\nfitz.open().insert_text()\nfitz.open().save("x")', 'from reportlab.pdfgen import canvas\ncanvas.Canvas("x").save()', 'pdfplumber.extract_tables()', 'import camelot\ncamelot.read_pdf("x")', 'import tabula\ntabula.read_pdf("x")', 'import tabula\ntabula.convert_into("x")', 'page.extract_text()', 'page.get_text()', 'extract_text()', 'extract_pages()', 'pytesseract.image_to_string(x)', 'pdf2image.convert_from_path(x)', 'fitz.get_pixmap()', 'PDFPage.get_pages(x)\ninterpreter.process_page(x)', 'unstructured.partition_pdf(x)', 'subprocess.run(["pdftotext"])', 'subprocess.run(["pdfinfo"])', 'from docx import Document\nDocument("x")', 'openpyxl.load_workbook("x")', 'pandas.read_excel("x")', 'pptx.Presentation("x")', 'open("x.txt").read()', 'Path("x").read_text()', 'Image.open("x")', '"pdf"', 'mindee.parse(InvoiceV4)', 'azure.begin_analyze_document("prebuilt-read")', 'azure.begin_analyze_document("prebuilt-layout")', 'veryfi.Client()', 'documentai.process_document()', 'textract.analyze_document()', 'eden.universal_ai()', 'llamaparse.parse()', 'nanonets.ocr(model_id="opaque")', 'docsumo.upload()', 'import pypdf\npypdf = object()\npypdf.PdfReader("x")', 'from pypdf import PdfReader\ndef PdfReader(x): pass\nPdfReader("x")', 'def read_pdf(): pass\nx.read_pdf()', 'from pypdf import PdfReader\nwith ctx() as PdfReader: pass\nPdfReader("x")', 'from pypdf import PdfReader\nPdfReader', 'from pypdf import PdfReader\ninvalid !']
        for source in cases:
            with self.subTest(source=source): self.assertFalse(evidence(source))
    def test_exclusions_json(self):
        self.write('README.md', 'read pdf')
        self.write('part.py', 'import pypdf')
        self.write('other.py', 'pypdf.PdfReader("x")')
        self.write('examples/e.py', 'import pypdf\npypdf.PdfReader("x")')
        self.write('fixtures/f.py', 'import pypdf\npypdf.PdfReader("x")')
        (self.root / 'link.py').symlink_to(self.root / 'examples/e.py')
        result = json.loads(self.cli('audit', str(self.root), '--json').stdout)
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertIn('message', result['findings'][0])
        self.assertEqual(self.cli('audit', str(self.root / 'missing')).returncode, 1)
        self.assertEqual(self.cli('bad').returncode, 1)
    def test_entrypoints(self):
        self.assertEqual(self.cli('--version').stdout.strip(), '0.1.0')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['audit', str(self.root)]), 0)
        self.assertIn('PASS', output.getvalue())

if __name__ == '__main__': unittest.main()
