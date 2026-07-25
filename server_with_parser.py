from __future__ import annotations

import os
import io
import json
import re
import time
import logging
from collections import Counter
from pathlib import Path
from typing import Any, BinaryIO, Callable
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import pypdf

PORT = 8899
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')
DB_FILE = os.path.join(os.path.dirname(__file__), 'results_db.json')

# Silence pypdf verbose warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

SUBJECT_CODES: dict[str, dict[str, str]] = {
    "21011": {"name": "Engineering Drawing", "semester": "Curriculum dependent"},
    "25711": {"name": "Bangla-I", "semester": "Semester 1"},
    "25712": {"name": "English-I", "semester": "Semester 1"},
    "25721": {"name": "Bangla-II", "semester": "Semester 2"},
    "25722": {"name": "English-II", "semester": "Semester 2"},
    "25811": {"name": "Social Science", "semester": "Semester 1"},
    "25812": {"name": "Physical Education & Life Skills Development", "semester": "Semester 2"},
    "25831": {"name": "Business Communication", "semester": "Other / carried subject"},
    "25911": {"name": "Mathematics-I", "semester": "Semester 1"},
    "25912": {"name": "Physics-I", "semester": "Semester 1"},
    "25913": {"name": "Chemistry", "semester": "Semester 1"},
    "25921": {"name": "Mathematics-II", "semester": "Semester 2"},
    "25922": {"name": "Physics-II", "semester": "Semester 2"},
    "26111": {"name": "Creativity and Concept Development", "semester": "Curriculum dependent"},
    "26121": {"name": "Architectural Design-I", "semester": "Curriculum dependent"},
    "26211": {"name": "Automobile Fundamentals", "semester": "Curriculum dependent"},
    "26221": {"name": "Automotive Engine System-I", "semester": "Curriculum dependent"},
    "26311": {"name": "Chemical Engineering Fundamentals", "semester": "Curriculum dependent"},
    "26312": {"name": "Safety in Chemical Industry", "semester": "Curriculum dependent"},
    "26321": {"name": "Basic Stoichiometry", "semester": "Curriculum dependent"},
    "26322": {"name": "Chemical Engineering Drawing", "semester": "Curriculum dependent"},
    "26411": {"name": "Civil Engineering Materials", "semester": "Curriculum dependent"},
    "26421": {"name": "Civil Engineering Drawing", "semester": "Curriculum dependent"},
    "26521": {"name": "Wood Workshop Practice", "semester": "Curriculum dependent"},
    "26711": {"name": "Basic Electricity", "semester": "Curriculum dependent"},
    "26712": {"name": "Electrical Engineering Materials", "semester": "Curriculum dependent"},
    "26721": {"name": "Electrical Circuit-I", "semester": "Curriculum dependent"},
    "26722": {"name": "Electrical Engineering Drawing", "semester": "Curriculum dependent"},
    "26811": {"name": "Basic Electronics", "semester": "Curriculum dependent"},
    "26821": {"name": "Electronic Devices and Circuits", "semester": "Curriculum dependent"},
    "26911": {"name": "Food Engineering Fundamentals", "semester": "Curriculum dependent"},
    "26912": {"name": "Food Safety & Hygiene Management", "semester": "Curriculum dependent"},
    "26921": {"name": "Food Science & Nutrition", "semester": "Curriculum dependent"},
    "26922": {"name": "Food Plant Layout & Design", "semester": "Curriculum dependent"},
    "27011": {"name": "Basic Workshop Practice", "semester": "Curriculum dependent"},
    "27012": {"name": "Machine Shop Practice-I", "semester": "Curriculum dependent"},
    "27021": {"name": "Mechanical Engineering Drawing", "semester": "Curriculum dependent"},
    "27031": {"name": "Mechanical Engineering Materials", "semester": "Curriculum dependent"},
    "27111": {"name": "Power Engineering Fundamentals", "semester": "Curriculum dependent"},
    "27121": {"name": "Power Equipment Management & Safety", "semester": "Curriculum dependent"},
    "27211": {"name": "RAC Fundamentals", "semester": "Curriculum dependent"},
    "27611": {"name": "Geological Engineering", "semester": "Curriculum dependent"},
    "27621": {"name": "Ceramic Model Making", "semester": "Curriculum dependent"},
    "27622": {"name": "Ceramic Engineering Materials-I", "semester": "Curriculum dependent"},
    "27711": {"name": "Glass Engineering Materials-I", "semester": "Curriculum dependent"},
    "27721": {"name": "Glass Engineering Materials-II", "semester": "Curriculum dependent"},
    "27821": {"name": "Basic Surveying", "semester": "Curriculum dependent"},
    "28021": {"name": "General Ship Knowledge", "semester": "Curriculum dependent"},
    "28221": {"name": "Aircraft Structure and Repair", "semester": "Curriculum dependent"},
    "28511": {"name": "Computer Office Application", "semester": "Curriculum dependent"},
    "28521": {"name": "Python Programming", "semester": "Curriculum dependent"},
    "28522": {"name": "Computer Graphics Design-I", "semester": "Curriculum dependent"},
    "28611": {"name": "Human Anatomy and Physiology", "semester": "Curriculum dependent"},
    "28621": {"name": "Basic Biomedical Engineering", "semester": "Curriculum dependent"},
    "29011": {"name": "Basic Environmental Engineering", "semester": "Curriculum dependent"},
    "29411": {"name": "Basics of Telecommunication", "semester": "Curriculum dependent"},
    "29511": {"name": "Printing Basics", "semester": "Curriculum dependent"},
    "29521": {"name": "Offset Machine Operation", "semester": "Curriculum dependent"},
}

INSTITUTE_FIND_RE = re.compile(r"(?m)^\s*(\d{5})\s*-\s*(.+?)\s*$")
RECORD_START_RE = re.compile(r"(?<!\d)(\d{6})\s*(?=[({])")
GPA_RE = re.compile(r"gpa([12])\s*:\s*(ref|\d+(?:\.\d+)?)", re.IGNORECASE)
SUBJECT_RE = re.compile(r"\b(\d{5})\s*\((T(?:\s*,\s*P)?|P(?:\s*,\s*T)?)\)", re.IGNORECASE)
PAGE_NUMBER_RE = re.compile(r"Page\s+\d+\s+of\s+\d+", re.IGNORECASE)

# Global Parsing State for Progress Bar API
parsing_progress = {
    "status": "idle",
    "completed_pages": 0,
    "total_pages": 0,
    "percentage": 0,
    "message": "Ready"
}

def normalize_gpa(value: str | None) -> float | str | None:
    if value is None:
        return None
    value = value.strip().lower()
    if value == "ref":
        return "ref"
    try:
        return round(float(value), 2)
    except ValueError:
        return None

def component_label(components: list[str]) -> str:
    component_names = {"T": "Theory", "P": "Practical"}
    return " + ".join(component_names.get(c, c) for c in components)

def get_subject_information(code: str) -> dict[str, str]:
    information = SUBJECT_CODES.get(code)
    if information:
        return {"name": information["name"], "semester": information["semester"]}
    return {"name": f"Subject ({code})", "semester": "Curriculum"}

def parse_record(block: str, institute_code: str | None, institute_name: str | None, page_number: int) -> dict[str, Any] | None:
    block = PAGE_NUMBER_RE.sub(" ", block)
    block = " ".join(block.replace("\n", " ").split())
    record_match = re.match(r"^(\d{6})\s*(.*)$", block)
    if not record_match:
        return None

    roll = record_match.group(1)
    result_text = record_match.group(2).strip()

    extracted_gpas = {
        f"gpa{semester_number}": value.lower()
        for semester_number, value in GPA_RE.findall(result_text)
    }

    subjects: list[dict[str, Any]] = []
    seen_subjects: set[tuple[str, tuple[str, ...]]] = set()

    for subject_code, component_text in SUBJECT_RE.findall(result_text):
        components = component_text.upper().replace(" ", "").split(",")
        unique_key = (subject_code, tuple(components))
        if unique_key in seen_subjects:
            continue
        seen_subjects.add(unique_key)
        subject_info = get_subject_information(subject_code)

        subjects.append({
            "code": subject_code,
            "name": subject_info["name"],
            "semester": subject_info["semester"],
            "components": components,
            "componentLabel": component_label(components),
        })

    if result_text.startswith("("):
        status = "pass"
    elif extracted_gpas:
        status = "referred"
    else:
        status = "failed"

    gpa1 = normalize_gpa(extracted_gpas.get("gpa1"))
    gpa2 = normalize_gpa(extracted_gpas.get("gpa2"))

    return {
        "roll": roll,
        "instituteCode": institute_code,
        "instituteName": institute_name,
        "status": status,
        "statusLabel": {
            "pass": "Passed",
            "referred": "Referred",
            "failed": "Failed in Four or More Subjects",
        }[status],
        "gpa1": gpa1,
        "gpa2": gpa2,
        "semesterResults": {
            "semester1": {
                "gpa": gpa1,
                "result": "Referred" if gpa1 == "ref" else "Published" if gpa1 is not None else "Not Available",
            },
            "semester2": {
                "gpa": gpa2,
                "result": "Referred" if gpa2 == "ref" else "Published" if gpa2 is not None else "Not Available",
            },
        },
        "failedSubjects": subjects,
        "failedSubjectCount": len(subjects),
        "sourcePage": page_number,
        "rawResult": result_text,
    }

def record_is_complete(block: str) -> bool:
    start_match = re.match(r"^\s*\d{6}\s*([({])", block)
    if not start_match:
        return False
    opening_character = start_match.group(1)
    if opening_character == "(":
        return ")" in block
    return "}" in block

def institute_for_position(position: int, institute_matches: list[re.Match[str]], fallback_code: str | None, fallback_name: str | None) -> tuple[str | None, str | None]:
    institute_code = fallback_code
    institute_name = fallback_name
    for match in institute_matches:
        if match.start() > position:
            break
        institute_code = match.group(1)
        institute_name = match.group(2).strip()
    return institute_code, institute_name

def extract_records_from_page(text: str, page_number: int, current_institute_code: str | None, current_institute_name: str | None, pending_block: str | None = None, pending_institute_code: str | None = None, pending_institute_name: str | None = None, pending_page_number: int | None = None):
    institute_matches = list(INSTITUTE_FIND_RE.finditer(text))
    record_matches = list(RECORD_START_RE.finditer(text))
    parsed_records: list[dict[str, Any]] = []

    first_record_position = record_matches[0].start() if record_matches else len(text)
    page_prefix = text[:first_record_position]

    if pending_block:
        pending_block += " " + page_prefix
        if record_is_complete(pending_block) or record_matches:
            parsed_record = parse_record(pending_block, pending_institute_code, pending_institute_name, pending_page_number or page_number)
            if parsed_record:
                parsed_records.append(parsed_record)
            pending_block = None
            pending_institute_code = None
            pending_institute_name = None
            pending_page_number = None

    for index, record_match in enumerate(record_matches):
        record_start = record_match.start()
        record_end = record_matches[index + 1].start() if index + 1 < len(record_matches) else len(text)

        for institute_match in institute_matches:
            if record_start < institute_match.start() < record_end:
                record_end = institute_match.start()
                break

        institute_code, institute_name = institute_for_position(record_start, institute_matches, current_institute_code, current_institute_name)
        record_block = text[record_start:record_end]

        is_last_record = (index == len(record_matches) - 1)
        if is_last_record and not record_is_complete(record_block):
            pending_block = record_block
            pending_institute_code = institute_code
            pending_institute_name = institute_name
            pending_page_number = page_number
            continue

        parsed_record = parse_record(record_block, institute_code, institute_name, page_number)
        if parsed_record:
            parsed_records.append(parsed_record)

    if institute_matches:
        last_institute = institute_matches[-1]
        current_institute_code = last_institute.group(1)
        current_institute_name = last_institute.group(2).strip()

    return (parsed_records, current_institute_code, current_institute_name, pending_block, pending_institute_code, pending_institute_name, pending_page_number)

def is_cngpi_institute(code: str | None, name: str | None) -> bool:
    if code and str(code).strip() in {"20015", "13143"}:
        return True
    if name and any(kw in str(name).lower() for kw in ["chapainawabganj", "cngpi"]):
        return True
    return False

def parse_pdf_bytes(pdf_bytes: bytes, source_name: str = "result.pdf", progress_callback: Callable[[int, int], None] | None = None) -> dict[str, Any]:
    if not pdf_bytes:
        raise RuntimeError("The PDF file is empty.")
    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("The selected file is not a valid PDF.")

    parsing_started_at = time.time()
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes), strict=False)
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise RuntimeError("The PDF contains no pages.")

    current_institute_code = None
    current_institute_name = None
    pending_block = None
    pending_institute_code = None
    pending_institute_name = None
    pending_page_number = None

    all_raw_results: dict[str, dict[str, Any]] = {}
    cngpi_filtered_results: dict[str, dict[str, Any]] = {}
    pdf_has_cngpi_keyword = False

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if "20015" in page_text or "13143" in page_text or "chapainawabganj" in page_text.lower():
            pdf_has_cngpi_keyword = True

        (page_records, current_institute_code, current_institute_name, pending_block, pending_institute_code, pending_institute_name, pending_page_number) = extract_records_from_page(
            text=page_text, page_number=page_number, current_institute_code=current_institute_code, current_institute_name=current_institute_name,
            pending_block=pending_block, pending_institute_code=pending_institute_code, pending_institute_name=pending_institute_name, pending_page_number=pending_page_number
        )

        for result in page_records:
            roll = result["roll"]
            all_raw_results[roll] = result

            rec_code = result.get("instituteCode")
            rec_name = result.get("instituteName")

            if is_cngpi_institute(rec_code, rec_name):
                cngpi_filtered_results[roll] = result

        if progress_callback:
            progress_callback(page_number, total_pages)

    if pending_block:
        parsed_record = parse_record(pending_block, pending_institute_code, pending_institute_name, pending_page_number or total_pages)
        if parsed_record:
            roll = parsed_record["roll"]
            all_raw_results[roll] = parsed_record
            if is_cngpi_institute(parsed_record.get("instituteCode"), parsed_record.get("instituteName")):
                cngpi_filtered_results[roll] = parsed_record

    # Fallback: If section detection found zero CNGPI-specific records but document text contains CNGPI keyword (20015),
    # treat all extracted roll records from this PDF as Chapainawabganj Polytechnic records!
    if not cngpi_filtered_results and pdf_has_cngpi_keyword:
        for roll, result in all_raw_results.items():
            result["instituteCode"] = "20015"
            result["instituteName"] = "Chapainawabganj Polytechnic Institute"
            cngpi_filtered_results[roll] = result

    # Final results set to return (ONLY Chapainawabganj Polytechnic Institute records)
    final_results = cngpi_filtered_results

    status_counts = Counter(result["status"] for result in final_results.values())
    institutes = {(r.get("instituteCode"), r.get("instituteName")) for r in final_results.values() if r.get("instituteCode")}
    used_subject_codes = sorted({s["code"] for r in final_results.values() for s in r.get("failedSubjects", [])})
    result_list = sorted(final_results.values(), key=lambda item: int(item["roll"]))

    return {
        "success": True,
        "meta": {
            "sourceFile": Path(source_name).name,
            "pdfEngine": "pypdf",
            "totalPages": total_pages,
            "totalResults": len(final_results),
            "rawTotalResultsFound": len(all_raw_results),
            "instituteFilter": "Chapainawabganj Polytechnic Institute (20015)",
            "statusCounts": {
                "pass": status_counts.get("pass", 0),
                "referred": status_counts.get("referred", 0),
                "failed": status_counts.get("failed", 0),
            },
            "usedSubjectCodeCount": len(used_subject_codes),
            "usedSubjectCodes": used_subject_codes,
            "parsingSeconds": round(time.time() - parsing_started_at, 3),
        },
        "resultsByRoll": final_results,
        "results": result_list,
    }

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print("Error loading DB file:", e)
    return {}

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error saving DB file:", e)

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/result':
            query = urllib.parse.parse_qs(parsed_url.query)
            roll = query.get('roll', [''])[0].strip()
            
            db_data = load_db()
            records_map = db_data.get("resultsByRoll", db_data)
            
            if roll in records_map:
                res_data = records_map[roll]
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "result": res_data}).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": f"No result found for Roll {roll}"}).encode('utf-8'))
            return
        
        elif parsed_url.path == '/api/parse-progress':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(parsing_progress).encode('utf-8'))
            return

        return super().do_GET()

    def do_POST(self):
        global parsing_progress
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/parse-pdf-upload':
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            filename = "Uploaded_Result.pdf"
            pdf_bytes = b""

            if "multipart/form-data" in content_type:
                boundary = content_type.split("boundary=")[1].encode()
                parts = body.split(b"--" + boundary)
                for part in parts:
                    if b'filename="' in part:
                        header_and_body = part.split(b"\r\n\r\n", 1)
                        if len(header_and_body) == 2:
                            pdf_bytes = header_and_body[1].rsplit(b"\r\n", 1)[0]
                            match = re.search(r'filename="([^"]+)"', header_and_body[0].decode('utf-8', errors='ignore'))
                            if match:
                                filename = match.group(1)
            else:
                try:
                    payload = json.loads(body.decode('utf-8'))
                    if 'pdfBase64' in payload:
                        import base64
                        pdf_bytes = base64.b64decode(payload['pdfBase64'].split(',')[-1])
                        filename = payload.get('filename', 'Result.pdf')
                except Exception:
                    pdf_bytes = body

            if not pdf_bytes:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "No PDF data received."}).encode('utf-8'))
                return

            parsing_progress = {
                "status": "parsing",
                "completed_pages": 0,
                "total_pages": 1,
                "percentage": 0,
                "message": "Initializing PDF Reader..."
            }

            def update_progress(current: int, total: int):
                global parsing_progress
                pct = round((current / total) * 100, 1)
                parsing_progress = {
                    "status": "parsing",
                    "completed_pages": current,
                    "total_pages": total,
                    "percentage": pct,
                    "message": f"Parsing Page {current} of {total} ({pct}%)"
                }

            try:
                # Save PDF to public/uploads directory
                uploads_dir = os.path.join(PUBLIC_DIR, 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
                if not safe_filename.endswith('.pdf'):
                    safe_filename += '.pdf'
                
                pdf_save_path = os.path.join(uploads_dir, safe_filename)
                with open(pdf_save_path, 'wb') as f:
                    f.write(pdf_bytes)

                file_url = f"/uploads/{safe_filename}"

                parsed_output = parse_pdf_bytes(pdf_bytes, source_name=filename, progress_callback=update_progress)
                parsed_output["fileUrl"] = file_url
                
                # Merge into database
                existing_db = load_db()
                if "resultsByRoll" not in existing_db:
                    existing_db = {"meta": parsed_output["meta"], "resultsByRoll": existing_db}
                
                existing_db["meta"] = parsed_output["meta"]
                existing_db["resultsByRoll"].update(parsed_output["resultsByRoll"])
                save_db(existing_db)

                parsing_progress = {
                    "status": "completed",
                    "completed_pages": parsed_output["meta"]["totalPages"],
                    "total_pages": parsed_output["meta"]["totalPages"],
                    "percentage": 100,
                    "message": f"Complete! Parsed {parsed_output['meta']['totalResults']} student results."
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(parsed_output).encode('utf-8'))

            except Exception as e:
                parsing_progress = {
                    "status": "error",
                    "completed_pages": 0,
                    "total_pages": 0,
                    "percentage": 0,
                    "message": str(e)
                }
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
            return

        return super().do_POST()

if __name__ == '__main__':
    # Initialize DB with mock demo data if empty
    db = load_db()
    if not db:
        db = {
          "meta": { "totalResults": 2, "totalPages": 1 },
          "resultsByRoll": {
            "654321": {
              "roll": "654321",
              "instituteCode": "13143",
              "instituteName": "Chapainawabganj Polytechnic Institute",
              "status": "pass",
              "statusLabel": "Passed",
              "gpa1": 3.85,
              "gpa2": 3.90,
              "semesterResults": {
                "semester1": { "gpa": 3.85, "result": "Published" },
                "semester2": { "gpa": 3.90, "result": "Published" }
              },
              "failedSubjects": [],
              "failedSubjectCount": 0
            },
            "654322": {
              "roll": "654322",
              "instituteCode": "13143",
              "instituteName": "Chapainawabganj Polytechnic Institute",
              "status": "referred",
              "statusLabel": "Referred",
              "gpa1": "ref",
              "gpa2": 3.50,
              "semesterResults": {
                "semester1": { "gpa": "ref", "result": "Referred" },
                "semester2": { "gpa": 3.50, "result": "Published" }
              },
              "failedSubjects": [
                { "code": "28511", "name": "Computer Office Application", "semester": "Semester 1", "components": ["T"], "componentLabel": "Theory" }
              ],
              "failedSubjectCount": 1
            }
          }
        }
        save_db(db)

    server = HTTPServer(('0.0.0.0', PORT), CustomHandler)
    print(f"BTEB Parser Server running on port {PORT}...")
    server.serve_forever()
