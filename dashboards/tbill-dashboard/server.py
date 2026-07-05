import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlparse


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ROOT_DIR)
TBILL_DIR = ROOT_DIR
KEY_PATH = os.path.join(BASE_DIR, "kakuleta-key.json")
BOZ_TBILLS_URL = "https://www.boz.zm/markets-securities/treasury-bills"
INVITATION_COLLECTION = "grzSecuritiesInvitations"
INVITATION_DOCUMENT = "treasuryBillInvitations"
YIELD_COLLECTION = "boz_tbill_yield_rates"
YIELD_DOCUMENT = "yieldUpdates"

STAGE_FILES = [
    "Monthly_Stage1_Boz_Tbill_Invitations.py",
    "Monthly_Stage1a_Boz_Tbill_Notifications.py",
    "Monthly_Stage2_Boz_Tbill_yield_rates.py",
    "Monthly_Stage2a_Boz_Tbill_Yield_Notifications.py",
    "Monthly_Stage3_Boz_Tbill_add_new_yieldRates_to_Historic_Yields.py",
    "Monthly_Stage4_Boz_Tbill_AmountBidAllocated.py",
    "Monthly_Stage5_Boz_Tbill_Analysis.py",
]

# In-memory stage state (session-only)
stage_state = {
    "activeStage": None,
    "lastActionResult": None,
    "lastActionTime": None,
    "logs": [],
    "running": False,
    "currentScriptOutput": None,
}


def add_log(message):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "message": message}
    stage_state["logs"].append(entry)
    # Keep last 200 logs
    if len(stage_state["logs"]) > 200:
        stage_state["logs"] = stage_state["logs"][-200:]
    return entry


def build_overview():
    found = [
        name
        for name in STAGE_FILES
        if os.path.exists(os.path.join(TBILL_DIR, name))
    ]

    return {
        "scriptsFound": len(found),
        "scriptsExpected": len(STAGE_FILES),
        "found": found,
        "missing": [name for name in STAGE_FILES if name not in found],
        "mode": "review-first",
        "port": 3003,
        "activeStage": stage_state["activeStage"],
        "lastActionResult": stage_state["lastActionResult"],
        "lastActionTime": stage_state["lastActionTime"],
        "running": stage_state["running"],
    }


def clean_firestore_value(value):
    # Handle Firestore Sentinel objects (e.g., SERVER_TIMESTAMP)
    if hasattr(value, "value"):
        return str(value)

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: clean_firestore_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [clean_firestore_value(item) for item in value]

    return value


def get_db():
    from google.cloud import firestore

    return firestore.Client.from_service_account_json(KEY_PATH)


def get_current_invitation():
    doc = get_db().collection(INVITATION_COLLECTION).document(INVITATION_DOCUMENT).get()

    if not doc.exists:
        return {}

    return clean_firestore_value(doc.to_dict())


def get_current_yields():
    doc = get_db().collection(YIELD_COLLECTION).document(YIELD_DOCUMENT).get()

    if not doc.exists:
        return {}

    return clean_firestore_value(doc.to_dict())


def parse_tender_key(tender_number):
    if not tender_number:
        return (0, 0)

    parts = str(tender_number).split("/")

    try:
        tender_no = int(parts[0])
        tender_year = int(parts[1][:4])
        return (tender_year, tender_no)
    except (IndexError, TypeError, ValueError):
        return (0, 0)


def build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()

    if os.environ.get("TBILL_HEADLESS", "1") != "0":
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_pdf_data(pdf_url):
    import fitz
    import requests

    response = requests.get(
        pdf_url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()

    with fitz.open(stream=response.content, filetype="pdf") as pdf:
        text = " ".join(page.get_text() for page in pdf)

    text = re.sub(r"\s+", " ", text)
    data = {
        "name": "treasuryBill",
        "tenderNumber": "",
        "bidSubmissionDeadlineString": "",
        "settlementDate": "",
        "pdfUrl": pdf_url,
    }

    tender_match = re.search(
        r"(?:Issue|Tender|Auction)\s+Number\s+([\d/A-Z-]+)", text, re.IGNORECASE
    )
    if tender_match:
        data["tenderNumber"] = tender_match.group(1).strip()

    deadline_match = re.search(
        r"submitted\s+by\s+(.*?)\.\s+Settlement",
        text,
        re.IGNORECASE,
    )
    if deadline_match:
        data["bidSubmissionDeadlineString"] = deadline_match.group(1).strip()

    settlement_match = re.search(
        r"Settlement\s+will\s+be\s+on\s+(.*?)\.", text, re.IGNORECASE
    )
    if settlement_match:
        data["settlementDate"] = settlement_match.group(1).strip()

    return data


def scrape_invitation_draft():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    current = get_current_invitation()
    current_key = parse_tender_key(current.get("tenderNumber"))
    driver = build_driver()

    try:
        driver.get(BOZ_TBILLS_URL)
        wait = WebDriverWait(driver, 25)

        invitation_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'treasury bill invitations')]")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", invitation_button)
        time.sleep(0.5)
        invitation_button.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.documents-table")))
        rows = driver.find_elements(By.CSS_SELECTOR, "table.documents-table tbody tr")

        candidates = []
        latest = None

        for row in rows:
            try:
                title = row.find_element(By.CSS_SELECTOR, "span.doc-title").text.strip()
                tender_match = re.search(r"(\d+)/(\d{4})", title)

                if not tender_match:
                    continue

                tender_number = f"{int(tender_match.group(1)):02d}/{tender_match.group(2)}"
                tender_key = parse_tender_key(tender_number)
                href = row.find_element(By.CSS_SELECTOR, "a.download-btn").get_attribute("href")
                pdf_url = urljoin(BOZ_TBILLS_URL, href)

                candidate = {
                    "title": title,
                    "tenderNumber": tender_number,
                    "pdfUrl": pdf_url,
                    "isNewerThanFirestore": tender_key > current_key,
                }
                candidates.append(candidate)

                if latest is None or tender_key > parse_tender_key(latest["tenderNumber"]):
                    latest = candidate
            except Exception:
                continue

        if not latest:
            return {
                "current": current,
                "candidates": candidates,
                "draft": None,
                "decision": "No T-Bill invitation documents were found on the BoZ page.",
            }

        draft = extract_pdf_data(latest["pdfUrl"])

        return {
            "current": current,
            "candidates": candidates,
            "draft": draft,
            "latest": latest,
            "isNewData": parse_tender_key(draft.get("tenderNumber")) > current_key,
            "decision": (
                "New invitation available."
                if parse_tender_key(draft.get("tenderNumber")) > current_key
                else "Website tender is not newer than Firestore. You can still inspect the draft."
            ),
        }
    finally:
        driver.quit()


def scrape_yield_draft():
    """Scrape-only version of Stage 2. Returns draft data WITHOUT writing to Firestore.
    Duplicates only the scraping logic from Monthly_Stage2_Boz_Tbill_yield_rates.py."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = build_driver()

    try:
        driver.get(BOZ_TBILLS_URL)
        wait = WebDriverWait(driver, 15)

        # 1. Scrape tender number
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.card-subtitle")))
        subtitle_text = driver.find_element(By.CSS_SELECTOR, "p.card-subtitle").text
        tender_match = re.search(r"Tender No\.\s*([\w/]+)", subtitle_text)
        web_tender_no = tender_match.group(1) if tender_match else "Unknown"

        # 2. Check if already in Firestore
        current = get_current_yields()
        existing_tender_no = current.get("tender_no")
        is_new_data = existing_tender_no != web_tender_no

        # 3. Scrape the yield table
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "app-treasury-bills-result-invitation table")
            )
        )

        rows = driver.find_elements(
            By.CSS_SELECTOR, "app-treasury-bills-result-invitation tbody tr"
        )
        tbill_data = []

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                tenure = cols[0].text.strip()
                isin = cols[1].text.strip()

                try:
                    discount_rate = float(cols[2].text.replace(",", "").strip())
                    yield_val = float(cols[3].text.replace(",", "").strip())

                    # Calculate change from Firestore data if available
                    previous_yield = 0.0
                    if current and "tbill_data" in current:
                        for item in current["tbill_data"]:
                            if item.get("tenure") == tenure:
                                previous_yield = item.get("yield", 0.0)
                                break

                    yield_change = round(yield_val - previous_yield, 4)

                    tbill_data.append({
                        "tenure": tenure,
                        "isin": isin,
                        "discount_rate": discount_rate,
                        "yield": yield_val,
                        "change": yield_change,
                    })
                except ValueError:
                    continue

        return {
            "current": current if current else None,
            "draft": {
                "tender_no": web_tender_no,
                "tbill_data": tbill_data,
            },
            "isNewData": is_new_data,
            "decision": (
                f"New yield data for Tender {web_tender_no}."
                if is_new_data
                else f"Yield data for Tender {web_tender_no} is already up to date."
            ),
        }
    finally:
        driver.quit()


def validate_invitation_payload(payload):
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else payload

    tender_number = str(draft.get("tenderNumber", "")).strip()
    deadline = str(draft.get("bidSubmissionDeadlineString", "")).strip()
    settlement_date = str(draft.get("settlementDate", "")).strip()
    pdf_url = str(draft.get("pdfUrl", "")).strip()

    if not tender_number:
        raise ValueError("Tender number is required.")

    if not deadline:
        raise ValueError("Bid submission deadline is required.")

    if not settlement_date:
        raise ValueError("Settlement date is required.")

    data = {
        "name": "treasuryBill",
        "tenderNumber": tender_number,
        "bidSubmissionDeadlineString": deadline,
        "settlementDate": settlement_date,
    }

    if pdf_url:
        data["pdfUrl"] = pdf_url

    return data


def ingest_invitation(payload):
    from google.cloud import firestore

    data = validate_invitation_payload(payload)
    data["updatedAt"] = firestore.SERVER_TIMESTAMP
    get_db().collection(INVITATION_COLLECTION).document(INVITATION_DOCUMENT).set(data, merge=True)
    return clean_firestore_value(data)


def validate_yield_payload(payload):
    """Validate and normalize yield payload for Firestore write."""
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else payload

    tender_no = str(draft.get("tender_no", "")).strip()
    tbill_data = draft.get("tbill_data", [])

    if not tender_no:
        raise ValueError("Tender number is required.")

    if not isinstance(tbill_data, list) or len(tbill_data) == 0:
        raise ValueError("At least one yield data entry is required.")

    # Clean each entry
    cleaned_data = []
    for item in tbill_data:
        entry = {
            "tenure": str(item.get("tenure", "")).strip(),
            "isin": str(item.get("isin", "")).strip(),
            "discount_rate": float(item.get("discount_rate", 0)),
            "yield": float(item.get("yield", 0)),
            "change": float(item.get("change", 0)),
        }
        if not entry["tenure"]:
            raise ValueError("Each yield entry must have a tenure.")
        cleaned_data.append(entry)

    return {
        "tender_no": tender_no,
        "tbill_data": cleaned_data,
    }


def ingest_yields(payload):
    from google.cloud import firestore

    data = validate_yield_payload(payload)
    data["updatedAt"] = firestore.SERVER_TIMESTAMP
    get_db().collection(YIELD_COLLECTION).document(YIELD_DOCUMENT).set(data, merge=True)
    return clean_firestore_value(data)


def run_script(script_name, confirm=False):
    """Run an existing stage script via subprocess and capture output.
    For scripts that use input() for confirmation, pipe 'y\\n' or 'n\\n'.
    When confirm=False (preview mode), pipe 'n\\n' to auto-cancel any prompts
    so the script runs through without hanging on input()."""
    script_path = os.path.join(TBILL_DIR, script_name)

    if not os.path.exists(script_path):
        return {"error": f"Script not found: {script_name}"}

    add_log(f"Starting {script_name}...")

    try:
        # Always pipe stdin so scripts with input() don't hang or crash
        # confirm=True  -> pipe "y\n" to approve
        # confirm=False -> pipe "n\n" to auto-cancel (preview mode)
        input_data = "y\n" if confirm else "n\n"

        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=TBILL_DIR,
        )
        stdout, _ = proc.communicate(input=input_data, timeout=300)

        returncode = proc.returncode

        # Log each line of output
        for line in stdout.splitlines():
            if line.strip():
                add_log(line.strip())

        if returncode == 0:
            add_log(f"{script_name} completed successfully.")
        else:
            add_log(f"{script_name} exited with code {returncode}.")

        return {
            "stdout": stdout,
            "returncode": returncode,
            "success": returncode == 0,
        }

    except subprocess.TimeoutExpired:
        proc.kill()
        add_log(f"{script_name} timed out after 300 seconds.")
        return {"error": "Script timed out after 300 seconds.", "stdout": "", "success": False}
    except Exception as e:
        add_log(f"Error running {script_name}: {str(e)}")
        return {"error": str(e), "stdout": "", "success": False}


class TbillDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def _is_api_path(self, path):
        """Check if the path is an API route."""
        return path.startswith("/api/")

    def _handle_api_error(self, error_message, status=500):
        """Safely return a JSON error response, even if the error happened mid-request."""
        add_log(f"Error: {error_message}")
        stage_state["lastActionResult"] = f"Error: {error_message}"
        stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
        stage_state["running"] = False
        try:
            self.respond_json({"error": error_message}, status=status)
        except Exception:
            # If we can't even send a response, the connection is dead
            pass

    def do_GET(self):
        path = urlparse(self.path).path

        try:
            if path == "/api/overview":
                self.respond_json(build_overview())
                return

            if path == "/api/tbill/invitations/latest":
                self.respond_json({"invitation": get_current_invitation()})
                return

            if path == "/api/tbill/invitations/scrape-draft":
                add_log("Running Stage 1 scrape...")
                stage_state["activeStage"] = "Stage 1"
                stage_state["running"] = True
                try:
                    result = scrape_invitation_draft()
                    if result.get("draft"):
                        add_log("Draft ready for inspection.")
                    else:
                        add_log(result.get("decision", "No draft data available."))
                    stage_state["lastActionResult"] = "Scrape complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    self._handle_api_error(str(e))
                finally:
                    stage_state["running"] = False
                return

            if path == "/api/tbill/yields/scrape-draft":
                add_log("Running Stage 2 scrape (preview only)...")
                stage_state["activeStage"] = "Stage 2"
                stage_state["running"] = True
                try:
                    result = scrape_yield_draft()
                    if result.get("draft"):
                        add_log("Yield draft ready for inspection.")
                    else:
                        add_log(result.get("decision", "No yield data available."))
                    stage_state["lastActionResult"] = "Yield scrape complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    self._handle_api_error(str(e))
                finally:
                    stage_state["running"] = False
                return

            if path == "/api/tbill/yields/latest":
                self.respond_json({"yields": get_current_yields()})
                return

            if path == "/api/tbill/invitations/firebase-source":
                add_log("Loading current invitation data from Firebase...")
                stage_state["activeStage"] = "Stage 1"
                try:
                    current = get_current_invitation()
                    if current and current.get("tenderNumber"):
                        result = {
                            "source": "firebase",
                            "draft": {
                                "tenderNumber": current.get("tenderNumber", ""),
                                "bidSubmissionDeadlineString": current.get("bidSubmissionDeadlineString", ""),
                                "settlementDate": current.get("settlementDate", ""),
                                "pdfUrl": current.get("pdfUrl", ""),
                            },
                            "decision": "Loaded current invitation data from Firebase.",
                        }
                        add_log("Firebase invitation data loaded.")
                    else:
                        result = {
                            "source": "firebase",
                            "draft": None,
                            "decision": "No invitation data found in Firebase.",
                        }
                        add_log("No invitation data in Firebase.")
                    stage_state["lastActionResult"] = "Firebase source loaded"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    self._handle_api_error(str(e))
                return

            if path == "/api/tbill/yields/firebase-source":
                add_log("Loading current yield data from Firebase...")
                stage_state["activeStage"] = "Stage 2"
                try:
                    current = get_current_yields()
                    if current and current.get("tender_no"):
                        result = {
                            "source": "firebase",
                            "draft": {
                                "tender_no": current.get("tender_no", ""),
                                "tbill_data": current.get("tbill_data", []),
                            },
                            "decision": "Loaded current yield data from Firebase.",
                        }
                        add_log("Firebase yield data loaded.")
                    else:
                        result = {
                            "source": "firebase",
                            "draft": None,
                            "decision": "No yield data found in Firebase.",
                        }
                        add_log("No yield data in Firebase.")
                    stage_state["lastActionResult"] = "Firebase source loaded"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    self._handle_api_error(str(e))
                return

            if path == "/api/stage/status":

                self.respond_json(stage_state)
                return

            super().do_GET()
        except Exception as e:
            # Global catch-all for any unhandled errors in API routes
            if self._is_api_path(path):
                self._handle_api_error(f"Unhandled server error: {str(e)}")
            else:
                raise

    def do_POST(self):
        path = urlparse(self.path).path

        try:
            if path == "/api/tbill/invitations/ingest":
                try:
                    add_log("Injecting invitation data to Firestore...")
                    stage_state["activeStage"] = "Stage 1"
                    result = ingest_invitation(self.read_json_body())
                    add_log("Inject complete.")
                    stage_state["lastActionResult"] = "Inject complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json({"saved": result})
                except ValueError as error:
                    add_log(f"Validation error: {str(error)}")
                    self.respond_json({"error": str(error)}, status=400)
                return

            if path == "/api/tbill/yields/ingest":
                try:
                    add_log("Injecting yield data to Firestore...")
                    stage_state["activeStage"] = "Stage 2"
                    result = ingest_yields(self.read_json_body())
                    add_log("Yield inject complete.")
                    stage_state["lastActionResult"] = "Yield inject complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json({"saved": result})
                except ValueError as error:
                    add_log(f"Validation error: {str(error)}")
                    self.respond_json({"error": str(error)}, status=400)
                return

            if path == "/api/stage/run":

                body = self.read_json_body()
                stage_key = body.get("stage", "")
                confirm = body.get("confirm", False)

                script_map = {
                    "stage1a": "Monthly_Stage1a_Boz_Tbill_Notifications.py",
                    "stage2": "Monthly_Stage2_Boz_Tbill_yield_rates.py",
                    "stage2a": "Monthly_Stage2a_Boz_Tbill_Yield_Notifications.py",
                    "stage3": "Monthly_Stage3_Boz_Tbill_add_new_yieldRates_to_Historic_Yields.py",
                    "stage4": "Monthly_Stage4_Boz_Tbill_AmountBidAllocated.py",
                    "stage5": "Monthly_Stage5_Boz_Tbill_Analysis.py",
                }

                stage_label_map = {
                    "stage1a": "Stage 1a",
                    "stage2": "Stage 2",
                    "stage2a": "Stage 2a",
                    "stage3": "Stage 3",
                    "stage4": "Stage 4",
                    "stage5": "Stage 5",
                }

                script_name = script_map.get(stage_key)
                if not script_name:
                    self.respond_json({"error": f"Unknown stage: {stage_key}"}, status=400)
                    return

                stage_label = stage_label_map.get(stage_key, stage_key)
                stage_state["activeStage"] = stage_label
                stage_state["running"] = True

                try:
                    add_log(f"Running {stage_label} ({script_name})...")
                    result = run_script(script_name, confirm=confirm)

                    if result.get("success"):
                        stage_state["lastActionResult"] = f"{stage_label} completed"
                    elif "error" in result:
                        stage_state["lastActionResult"] = f"{stage_label} error: {result['error']}"
                    else:
                        stage_state["lastActionResult"] = f"{stage_label} exited with code {result.get('returncode')}"

                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    add_log(f"Error running {stage_label}: {str(e)}")
                    stage_state["lastActionResult"] = f"Error: {str(e)}"
                    self.respond_json({"error": str(e)}, status=500)
                finally:
                    stage_state["running"] = False
                return

            self.respond_json({"error": "Endpoint not found."}, status=404)
        except Exception as e:
            if self._is_api_path(path):
                self._handle_api_error(f"Unhandled server error: {str(e)}")
            else:
                raise

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}

        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def respond_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = int(os.environ.get("PORT", "3003"))
    server = ThreadingHTTPServer(("127.0.0.1", port), TbillDashboardHandler)
    print(f"T-Bill dashboard running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
