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
FOREX_DIR = os.path.join(BASE_DIR, "forex")
KEY_PATH = os.path.join(BASE_DIR, "kakuleta-key.json")
BOZ_FOREX_URL = "https://www.boz.zm/markets-securities/average-exchange-rates"

EXCHANGE_RATES_COLLECTION = "boz_exchange_rates"
EXCHANGE_RATES_DOCUMENT = "average_exchange_rates"

FOREX_MAPPING = {
    "EUR": "EURZMW",
    "GBP": "GBPZMW",
    "USD": "USDZMW",
    "ZAR": "ZARZMW",
}

ANALYTICS_SCRIPT = "Daily7_ForexHistoricPricesAnalysis.py"

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
    return {
        "mode": "review-first",
        "port": 3005,
        "activeStage": stage_state["activeStage"],
        "lastActionResult": stage_state["lastActionResult"],
        "lastActionTime": stage_state["lastActionTime"],
        "running": stage_state["running"],
    }


def clean_firestore_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: clean_firestore_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [clean_firestore_value(item) for item in value]

    return value


def get_db():
    from google.cloud import firestore

    return firestore.Client.from_service_account_json(KEY_PATH)


def get_current_exchange_rates():
    doc = (
        get_db()
        .collection(EXCHANGE_RATES_COLLECTION)
        .document(EXCHANGE_RATES_DOCUMENT)
        .get()
    )

    if not doc.exists:
        return {}

    return clean_firestore_value(doc.to_dict())


def build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()

    if os.environ.get("FOREX_HEADLESS", "1") != "0":
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=chrome_options)


def scrape_exchange_rates_draft():
    """Scrape-only version of Daily6. Returns draft data WITHOUT writing to Firestore."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    current = get_current_exchange_rates()
    driver = build_driver()

    try:
        driver.get(BOZ_FOREX_URL)
        wait = WebDriverWait(driver, 30)

        # 1. Scrape date
        print("⏳ Checking date chip...")
        date_chip = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "last-updated-chip"))
        )

        raw_date_text = date_chip.text.replace("Last updated:", "").strip()
        from datetime import datetime

        formatted_date = datetime.strptime(raw_date_text, "%d-%m-%Y").strftime(
            "%d-%b-%y"
        )

        # 2. Check idempotency
        stored_date = current.get("date") if current else None
        is_new_data = stored_date != formatted_date

        # 3. Scrape table
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        exchange_rates = []

        for row in rows:
            try:
                currency_raw = row.find_element(
                    By.CLASS_NAME, "currency-code"
                ).text.strip()
                currency_code = currency_raw.split("/")[-1].strip()

                buying_rate = float(
                    row.find_element(By.XPATH, "./td[2]")
                    .text.replace(",", "")
                    .strip()
                )
                selling_rate = float(
                    row.find_element(By.XPATH, "./td[3]")
                    .text.replace(",", "")
                    .strip()
                )

                exchange_rates.append(
                    {
                        "currency_name": currency_code,
                        "buying_rate": buying_rate,
                        "selling_rate": selling_rate,
                    }
                )
            except Exception:
                continue

        return {
            "current": current if current else None,
            "draft": {
                "date": formatted_date,
                "exchange_rates": exchange_rates,
            },
            "isNewData": is_new_data,
            "decision": (
                f"New exchange rates for {formatted_date}."
                if is_new_data
                else f"Exchange rates for {formatted_date} are already up to date."
            ),
        }
    finally:
        driver.quit()


def validate_exchange_rates_payload(payload):
    """Validate the exchange rates payload before writing."""
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else payload

    date = str(draft.get("date", "")).strip()
    exchange_rates = draft.get("exchange_rates", [])

    if not date:
        raise ValueError("Date is required.")

    if not isinstance(exchange_rates, list) or len(exchange_rates) == 0:
        raise ValueError("At least one exchange rate entry is required.")

    validated_rates = []
    for rate in exchange_rates:
        currency_name = str(rate.get("currency_name", "")).strip()
        try:
            buying_rate = float(rate.get("buying_rate", 0))
            selling_rate = float(rate.get("selling_rate", 0))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid numeric value in exchange rate: {rate}")

        if not currency_name:
            raise ValueError("Currency name is required.")

        validated_rates.append(
            {
                "currency_name": currency_name,
                "buying_rate": buying_rate,
                "selling_rate": selling_rate,
            }
        )

    return {
        "date": date,
        "exchange_rates": validated_rates,
    }


def ingest_exchange_rates(payload):
    """Write exchange rates to Firestore (only called after Inject/Confirm).
    Mirrors the write logic from Daily6_boz_exchange_rates.py."""
    from google.cloud import firestore

    data = validate_exchange_rates_payload(payload)
    date = data["date"]
    exchange_rates = data["exchange_rates"]

    db = get_db()

    # 1. Write snapshot to boz_exchange_rates/average_exchange_rates
    snap_ref = db.collection(EXCHANGE_RATES_COLLECTION).document(
        EXCHANGE_RATES_DOCUMENT
    )
    snap_ref.set(
        {
            "date": date,
            "exchange_rates": exchange_rates,
        }
    )
    add_log(f"✅ Snapshot updated: {date}")

    # 2. Build forex_data for history update
    forex_data = {}
    for rate in exchange_rates:
        code = rate["currency_name"]
        forex_data[code] = {
            "date": date,
            "buyRate": rate["buying_rate"],
            "sellRate": rate["selling_rate"],
        }

    # 3. Update forexHistoricPrices using same logic as Daily6
    for code, doc_id in FOREX_MAPPING.items():
        if code in forex_data:
            doc_ref = db.collection("forexHistoricPrices").document(doc_id)
            doc_ref.set(
                {
                    "currencyData": firestore.ArrayUnion([forex_data[code]])
                },
                merge=True,
            )
            add_log(f"📈 History updated for {doc_id}")

    add_log("🎉 All Forex updates finished safely!")
    return clean_firestore_value(data)


def run_analytics_script():
    """Run Daily7_ForexHistoricPricesAnalysis.py via subprocess and capture output."""
    script_path = os.path.join(ROOT_DIR, ANALYTICS_SCRIPT)

    if not os.path.exists(script_path):
        return {"error": f"Script not found: {ANALYTICS_SCRIPT}"}

    add_log(f"Starting {ANALYTICS_SCRIPT}...")

    try:
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT_DIR,
        )
        stdout, _ = proc.communicate(input="y\n", timeout=300)

        returncode = proc.returncode

        # Log each line of output
        for line in stdout.splitlines():
            if line.strip():
                add_log(line.strip())

        if returncode == 0:
            add_log(f"{ANALYTICS_SCRIPT} completed successfully.")
        else:
            add_log(f"{ANALYTICS_SCRIPT} exited with code {returncode}.")

        return {
            "stdout": stdout,
            "returncode": returncode,
            "success": returncode == 0,
        }

    except subprocess.TimeoutExpired:
        proc.kill()
        add_log(f"{ANALYTICS_SCRIPT} timed out after 300 seconds.")
        return {"error": "Script timed out after 300 seconds.", "stdout": "", "success": False}
    except Exception as e:
        add_log(f"Error running {ANALYTICS_SCRIPT}: {str(e)}")
        return {"error": str(e), "stdout": "", "success": False}


class ForexDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def _is_api_path(self, path):
        return path.startswith("/api/")

    def _handle_api_error(self, error_message, status=500):
        add_log(f"Error: {error_message}")
        stage_state["lastActionResult"] = f"Error: {error_message}"
        stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
        stage_state["running"] = False
        try:
            self.respond_json({"error": error_message}, status=status)
        except Exception:
            pass

    def do_GET(self):
        path = urlparse(self.path).path

        try:
            if path == "/api/overview":
                self.respond_json(build_overview())
                return

            if path == "/api/stage/status":
                self.respond_json(stage_state)
                return

            if path == "/api/forex/exchange-rates/scrape-draft":
                add_log("Stage 1: Scraping BoZ website for exchange rates...")
                stage_state["activeStage"] = "Stage 1"
                stage_state["running"] = True
                try:
                    result = scrape_exchange_rates_draft()
                    if result.get("draft") and result["draft"].get("exchange_rates"):
                        add_log("Draft exchange rates ready for inspection.")
                    else:
                        add_log(result.get("decision", "No exchange rate data available."))
                    stage_state["lastActionResult"] = "Scrape complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    self._handle_api_error(str(e))
                finally:
                    stage_state["running"] = False
                return

            if path == "/api/forex/exchange-rates/firebase":
                add_log("Stage 1: Loading current exchange rates from Firebase...")
                stage_state["activeStage"] = "Stage 1"
                try:
                    data = get_current_exchange_rates()
                    self.respond_json(
                        {
                            "source": "firebase",
                            "draft": data if data else None,
                            "decision": "Loaded from Firebase."
                            if data
                            else "No exchange rate data found in Firebase.",
                        }
                    )
                except Exception as e:
                    self._handle_api_error(str(e))
                return

            super().do_GET()
        except Exception as e:
            if self._is_api_path(path):
                self._handle_api_error(f"Unhandled server error: {str(e)}")
            else:
                raise

    def do_POST(self):
        path = urlparse(self.path).path

        try:
            if path == "/api/forex/exchange-rates/ingest":
                try:
                    add_log("Stage 1: Injecting exchange rates to Firestore...")
                    stage_state["activeStage"] = "Stage 1"
                    result = ingest_exchange_rates(self.read_json_body())
                    add_log("Inject complete.")
                    stage_state["lastActionResult"] = "Inject complete"
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json({"saved": result})
                except ValueError as error:
                    add_log(f"Validation error: {str(error)}")
                    self.respond_json({"error": str(error)}, status=400)
                return

            if path == "/api/forex/analytics/run":
                add_log("Stage 2: Running Forex Analytics script...")
                stage_state["activeStage"] = "Stage 2"
                stage_state["running"] = True
                try:
                    result = run_analytics_script()
                    if result.get("success"):
                        stage_state["lastActionResult"] = "Stage 2 completed"
                    elif "error" in result:
                        stage_state["lastActionResult"] = f"Stage 2 error: {result['error']}"
                    else:
                        stage_state["lastActionResult"] = (
                            f"Stage 2 exited with code {result.get('returncode')}"
                        )
                    stage_state["lastActionTime"] = time.strftime("%H:%M:%S")
                    self.respond_json(result)
                except Exception as e:
                    add_log(f"Error running Stage 2: {str(e)}")
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
    port = int(os.environ.get("PORT", "3005"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ForexDashboardHandler)
    print(f"Forex dashboard running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
