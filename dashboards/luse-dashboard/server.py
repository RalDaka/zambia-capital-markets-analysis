import json
import os
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ROOT_DIR)
KEY_PATH = os.path.join(BASE_DIR, "kakuleta-key.json")
LUSE_URL = "https://www.luse.co.zm/trading/market-data/"
AFRICAN_FINANCIALS_URL = "https://africanfinancials.com/lusaka-securities-exchange-share-prices/"
PROJECT_ID = "kakuleta-e5256"
FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

SYMBOL_TO_DOC = {
    "AECI": "AECI",
    "ATEL": "AIRTEL",
    "BATZ": "BAT",
    "BATA": "BATA",
    "CECZ": "CEC",
    "CECA": "CEC AFRICA",
    "CHIL": "CHILANGA",
    "DCZM": "DCZM",
    "MAFS": "MADISON",
    "NATB": "NATBREW",
    "PUMA": "PUMA",
    "REIZUSD": "REIZ (US CENTS)",
    "SHOP": "SHOPRITE",
    "SCBL": "STANCHART",
    "ZFCO": "ZAFFICO",
    "ZMBF": "ZAMBEEF",
    "ZSUG": "ZAMBIA SUGAR",
    "ZMRE": "ZAMBIARE",
    "ZABR": "ZAMBREW",
    "ZMFA": "ZAMEFA",
    "ZNCO": "ZANACO",
    "ZCCM": "ZCCM",
    "KLRE": "KLRE",
}


def normalize_symbol(symbol):
    symbol = symbol.strip().replace("*", "")

    aliases = {
        "ZCCM-IH": "ZCCM",
    }

    return aliases.get(symbol, symbol)


def parse_required_float(value):
    return float(value.strip().replace(",", ""))


def parse_optional_float(value):
    clean_value = value.strip().replace(",", "")

    if clean_value in ("", "-"):
        return 0.0

    return float(clean_value)


def parse_optional_int(value):
    return int(float(parse_optional_float(value)))


def get_db():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred)

    return firestore.client()


def get_last_ingested_date():
    db = get_db()
    doc = db.collection("system_meta").document("lusePortfolio").get()

    if not doc.exists:
        return None

    return doc.to_dict().get("lastPortfolioPriceDate")


def validate_market_date(value):
    if not value:
        raise ValueError("marketDate is required.")

    datetime.strptime(value, "%Y-%m-%d")
    return value


def should_update_current_docs(market_date, last_ingested_date, allow_backfill):
    if not allow_backfill:
        return True

    if not last_ingested_date:
        return True

    return market_date >= last_ingested_date


def build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    chrome_options = Options()

    if os.environ.get("LUSE_HEADLESS") == "1":
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=chrome_options)


def parse_luse_date(raw_date):
    return datetime.strptime(raw_date.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")


def scrape_luse_page(include_rows=False):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = build_driver()

    try:
        driver.get(LUSE_URL)

        date_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="page"]//ul/li/span'))
        )
        market_date = parse_luse_date(date_element.text)
        result = {"marketDate": market_date, "companies": {}}

        if not include_rows:
            return result

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "tablepress-3"))
        )

        rows = driver.find_elements(By.XPATH, '//*[@id="tablepress-3"]/tbody/tr')

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 7:
                continue

            symbol = normalize_symbol(cells[0].text)

            if symbol not in SYMBOL_TO_DOC:
                continue

            try:
                price = parse_required_float(cells[2].text)
                volume = parse_optional_int(cells[5].text)
                value = parse_optional_float(cells[6].text)
            except ValueError:
                continue

            company_name = SYMBOL_TO_DOC[symbol]
            result["companies"][company_name] = {
                "symbol": symbol,
                "companyName": company_name,
                "price": price,
                "volume": volume,
                "value": value,
                "source": "scraped",
            }

        scraped_symbols = {
            company["symbol"]
            for company in result["companies"].values()
        }
        missing_symbols = [
            symbol
            for symbol in SYMBOL_TO_DOC
            if symbol not in scraped_symbols
        ]
        result["missingSymbols"] = missing_symbols
        result["missingCompanies"] = [
            SYMBOL_TO_DOC[symbol]
            for symbol in missing_symbols
        ]

        return result
    finally:
        driver.quit()


def scrape_luse_index_data():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = build_driver()

    try:
        driver.get(LUSE_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//h3[.//span]/span"))
        )

        elements = driver.find_elements(By.XPATH, "//h3[.//span]/span")
        extracted_data = [element.text.strip() for element in elements]
        keys = [
            "currentValue",
            "priceChange",
            "percentageChange",
            "trades",
            "volumeTraded",
            "valueTraded",
        ]
        index_data = dict(zip(keys, extracted_data))

        for key, value in index_data.items():
            clean_value = value.replace(",", "").replace("%", "").replace("ZMW", "").strip()

            if key == "trades":
                index_data[key] = int(float(clean_value))
            else:
                index_data[key] = float(clean_value)

        date_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="page"]//ul/li/span'))
        )
        index_data["dateOfUpdate"] = parse_luse_date(date_element.text)
        return index_data
    finally:
        driver.quit()


def get_ceca_sync_state():
    db = get_db()
    current_doc = db.collection("luse_listed_companies_data").document("CEC AFRICA").get()
    ceca_doc = db.collection("luseCompanyHistoricPrices").document("CECA").get()
    cecz_doc = db.collection("luseCompanyHistoricPrices").document("CECZ").get()

    current_data = current_doc.to_dict() if current_doc.exists else {}
    ceca_chart = ceca_doc.to_dict().get("chartData", []) if ceca_doc.exists else []
    cecz_chart = cecz_doc.to_dict().get("chartData", []) if cecz_doc.exists else []
    ceca_chart = sorted(ceca_chart, key=lambda entry: entry["date"])
    cecz_chart = sorted(cecz_chart, key=lambda entry: entry["date"])

    ceca_last_date = ceca_chart[-1]["date"] if ceca_chart else None
    ceca_last_price = ceca_chart[-1]["price"] if ceca_chart else current_data.get("price")
    cecz_latest_date = cecz_chart[-1]["date"] if cecz_chart else None
    next_history_date = None

    if ceca_last_date and cecz_chart:
        cecz_dates = [entry["date"] for entry in cecz_chart]

        if ceca_last_date in cecz_dates:
            idx = cecz_dates.index(ceca_last_date)

            if idx + 1 < len(cecz_dates):
                next_history_date = cecz_dates[idx + 1]

    return {
        "current": {
            "price": current_data.get("price"),
            "volume": current_data.get("today_volume"),
            "value": current_data.get("today_value"),
        },
        "cecaLastDate": ceca_last_date,
        "cecaLastPrice": ceca_last_price,
        "ceczLatestDate": cecz_latest_date,
        "nextHistoryDate": next_history_date,
        "isSynced": bool(ceca_last_date and cecz_latest_date and ceca_last_date == cecz_latest_date),
    }


def scrape_ceca_africanfinancials():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = build_driver()

    try:
        driver.get(AFRICAN_FINANCIALS_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "af21_prices"))
        )

        table = driver.find_element(By.ID, "af21_prices")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if not cells:
                continue

            company_name = cells[0].text.strip().upper()

            if "CEC AFRICA (KWACHA)" not in company_name:
                continue

            price = parse_optional_float(cells[1].text)
            value = parse_optional_float(cells[3].text)
            volume = parse_optional_int(cells[4].text)

            return {
                "price": price,
                "volume": volume,
                "value": value,
                "source": "AfricanFinancials",
            }

        raise ValueError("CEC AFRICA (KWACHA) was not found on AfricanFinancials.")
    finally:
        driver.quit()


def build_date_check():
    scraped = scrape_luse_page(include_rows=False)
    luse_date = scraped["marketDate"]
    last_ingested_date = get_last_ingested_date()
    can_scrape = last_ingested_date != luse_date

    message = (
        "LuSE has a newer date than Firestore."
        if can_scrape
        else "LuSE date already matches the last ingested date."
    )

    return {
        "luseDate": luse_date,
        "lastIngestedDate": last_ingested_date,
        "canScrape": can_scrape,
        "message": message,
    }


def load_latest_values():
    db = get_db()
    docs = db.collection("luse_listed_companies_data").stream()
    companies = {}

    for doc in docs:
        data = doc.to_dict()
        symbol = data.get("tickerSymbol") or data.get("symbol")

        if symbol:
            symbol = str(symbol).strip().replace("*", "")

        company_name = SYMBOL_TO_DOC.get(symbol) if symbol else None

        if not company_name:
            company_name = data.get("company_name") or doc.id
            symbol = next((key for key, value in SYMBOL_TO_DOC.items() if value == company_name), None)

        if not symbol:
            continue

        companies[company_name] = {
            "symbol": symbol,
            "companyName": company_name,
            "lastPrice": data.get("price"),
            "lastDate": data.get("todayDate"),
            "price": data.get("price"),
            "volume": data.get("today_volume"),
            "value": data.get("today_value"),
            "source": "latest",
        }

    for symbol, company_name in SYMBOL_TO_DOC.items():
        if company_name in companies:
            continue

        hist_doc = db.collection("luseCompanyHistoricPrices").document(symbol).get()

        if not hist_doc.exists:
            continue

        chart_data = hist_doc.to_dict().get("chartData", [])

        if not chart_data:
            continue

        latest_entry = sorted(chart_data, key=lambda entry: entry["date"])[-1]
        latest_price = latest_entry.get("price")

        companies[company_name] = {
            "symbol": symbol,
            "companyName": company_name,
            "lastPrice": latest_price,
            "lastDate": latest_entry.get("date"),
            "price": latest_price,
            "volume": None,
            "value": None,
            "source": "latest",
        }

    return {"companies": companies}


def load_latest_index_data():
    db = get_db()
    doc = db.collection("luse_index_data").document("luseIndexDataDocument").get()

    if not doc.exists:
        return {"indexData": None}

    return {"indexData": doc.to_dict()}


def get_past_index(index_data, market_date, days):
    target_date = datetime.strptime(market_date, "%Y-%m-%d") - timedelta(days=days)
    past_entries = [
        entry
        for entry in index_data
        if datetime.strptime(entry["date"], "%Y-%m-%d") <= target_date
    ]
    return past_entries[-1] if past_entries else None


def calculate_index_percentage_change(current_value, past_entry):
    if not past_entry or not past_entry.get("index"):
        return None

    past_index = past_entry["index"]

    if past_index == 0:
        return None

    return round(((current_value - past_index) / past_index) * 100, 2)


def ingest_index_payload(payload):
    db = get_db()
    market_date = validate_market_date(payload.get("marketDate"))
    index_data = payload.get("indexData") or {}
    allow_backfill = bool(payload.get("allowSpecificDateInjection"))

    required_fields = [
        "currentValue",
        "priceChange",
        "percentageChange",
        "trades",
        "volumeTraded",
        "valueTraded",
    ]

    missing_fields = [
        field
        for field in required_fields
        if index_data.get(field) is None
    ]

    if missing_fields:
        raise ValueError(f"Missing index fields: {', '.join(missing_fields)}")

    current_value = float(index_data["currentValue"])
    historic_ref = db.collection("luseHistoricIndexData").document("indexDataDocument")
    historic_doc = historic_ref.get()
    historic_data = historic_doc.to_dict().get("indexData", []) if historic_doc.exists else []

    history_added = False

    if not any(entry.get("date") == market_date for entry in historic_data):
        historic_data.append({
            "date": market_date,
            "index": current_value,
        })
        historic_data.sort(key=lambda entry: entry["date"])
        historic_ref.set({"indexData": historic_data}, merge=True)
        history_added = True

    latest_current_doc = db.collection("luse_index_data").document("luseIndexDataDocument").get()
    latest_current_date = latest_current_doc.to_dict().get("dateOfUpdate") if latest_current_doc.exists else None
    update_current = should_update_current_docs(market_date, latest_current_date, allow_backfill)

    current_updated = False

    if update_current:
        one_month = get_past_index(historic_data, market_date, 30)
        three_month = get_past_index(historic_data, market_date, 90)
        six_month = get_past_index(historic_data, market_date, 180)
        one_year = get_past_index(historic_data, market_date, 365)

        update_data = {
            "currentValue": current_value,
            "priceChange": float(index_data["priceChange"]),
            "percentageChange": float(index_data["percentageChange"]),
            "trades": int(index_data["trades"]),
            "volumeTraded": float(index_data["volumeTraded"]),
            "valueTraded": float(index_data["valueTraded"]),
            "dateOfUpdate": market_date,
            "percentageChangeOneMonth": calculate_index_percentage_change(current_value, one_month),
            "percentageChangeThreeMonths": calculate_index_percentage_change(current_value, three_month),
            "percentageChangeSixMonths": calculate_index_percentage_change(current_value, six_month),
            "percentageChangeOneYear": calculate_index_percentage_change(current_value, one_year),
        }

        db.collection("luse_index_data").document("luseIndexDataDocument").set(update_data, merge=True)
        current_updated = True

    return {
        "marketDate": market_date,
        "historyAdded": history_added,
        "currentUpdated": current_updated,
        "currentUpdateSkippedReason": None if update_current else "manual_backfill_older_than_current_index_date",
    }


def ingest_ceca_payload(payload):
    from firebase_admin import firestore

    db = get_db()
    ceca_data = payload.get("cecaData") or {}
    price = ceca_data.get("price")
    volume = ceca_data.get("volume")
    value = ceca_data.get("value")

    if price is None or volume is None or value is None:
        raise ValueError("CECA price, volume, and value are required.")

    price = float(price)
    volume = int(volume)
    value = float(value)

    db.collection("luse_listed_companies_data").document("CEC AFRICA").set({
        "price": price,
        "today_value": value,
        "today_volume": volume,
    }, merge=True)

    ceca_ref = db.collection("luseCompanyHistoricPrices").document("CECA")
    cecz_ref = db.collection("luseCompanyHistoricPrices").document("CECZ")
    ceca_doc = ceca_ref.get()
    cecz_doc = cecz_ref.get()
    ceca_chart = ceca_doc.to_dict().get("chartData", []) if ceca_doc.exists else []
    cecz_chart = cecz_doc.to_dict().get("chartData", []) if cecz_doc.exists else []
    ceca_chart = sorted(ceca_chart, key=lambda entry: entry["date"])
    cecz_chart = sorted(cecz_chart, key=lambda entry: entry["date"])

    if not ceca_chart:
        raise ValueError("CECA history is empty; cannot sync against CECZ safely.")

    if not cecz_chart:
        raise ValueError("CECZ history is empty; cannot sync CECA.")

    last_ceca_date = ceca_chart[-1]["date"]
    cecz_dates = [entry["date"] for entry in cecz_chart]

    if last_ceca_date not in cecz_dates:
        return {
            "currentUpdated": True,
            "historyAdded": False,
            "historyDate": None,
            "message": "Current CECA updated, but CECA last date does not exist in CECZ history.",
        }

    idx = cecz_dates.index(last_ceca_date)

    if idx + 1 >= len(cecz_dates):
        return {
            "currentUpdated": True,
            "historyAdded": False,
            "historyDate": None,
            "message": "Current CECA updated. CECA is already synced with CECZ.",
        }

    next_date = cecz_dates[idx + 1]

    if any(entry.get("date") == next_date for entry in ceca_chart):
        return {
            "currentUpdated": True,
            "historyAdded": False,
            "historyDate": next_date,
            "message": "Current CECA updated. CECA history already had the next sync date.",
        }

    ceca_ref.update({
        "chartData": firestore.ArrayUnion([{
            "date": next_date,
            "price": price,
        }])
    })

    return {
        "currentUpdated": True,
        "historyAdded": True,
        "historyDate": next_date,
        "message": f"CECA current data updated and history synced for {next_date}.",
    }


def calculate_mover_change(start_price, end_price, name):
    if not start_price or start_price <= 0 or end_price is None:
        return None

    change = ((end_price - start_price) / start_price) * 100

    if abs(change) < 0.001:
        return None

    return {
        "name": name,
        "change": change,
        "startPrice": start_price,
        "endPrice": end_price,
    }


def build_notification_preview():
    db = get_db()
    meta_doc = db.collection("system_meta").document("lusePortfolio").get()
    status_doc = db.collection("luse_system").document("report_status").get()
    meta_data = meta_doc.to_dict() if meta_doc.exists else {}
    status_data = status_doc.to_dict() if status_doc.exists else {}
    last_price_date = meta_data.get("lastPortfolioPriceDate")
    changes = []
    latest_date = None

    for doc in db.collection("luseCompanyHistoricPrices").stream():
        chart_data = doc.to_dict().get("chartData")

        if not chart_data or len(chart_data) < 2:
            continue

        sorted_data = sorted(chart_data, key=lambda entry: entry["date"], reverse=True)
        latest_date = sorted_data[0]["date"] if latest_date is None else max(latest_date, sorted_data[0]["date"])
        change = calculate_mover_change(
            sorted_data[1].get("price"),
            sorted_data[0].get("price"),
            doc.id,
        )

        if change:
            changes.append(change)

    changes = sorted(changes, key=lambda item: item["change"], reverse=True)
    report_date = last_price_date or latest_date
    already_sent = bool(report_date and status_data.get("last_daily_date") == report_date)
    title_day = datetime.now().strftime("%A")
    title = f"{title_day} Daily LuSE Movers"

    body_lines = [
        f"{item['name']}: {item['startPrice']:.2f} -> {item['endPrice']:.2f} ({'+' if item['change'] > 0 else ''}{item['change']:.2f}%)"
        for item in changes
    ]
    body = f"{len(changes)} movers today:\n\n" + "\n".join(body_lines) if changes else "No movers today"

    return {
        "reportDate": report_date,
        "latestHistoricDate": latest_date,
        "lastPortfolioPriceDate": last_price_date,
        "alreadySent": already_sent,
        "lastSentDate": status_data.get("last_daily_date"),
        "changes": changes,
        "title": title,
        "body": body,
    }


# =========================
# COMPANY ANALYTICS
# =========================

company_name_mapping = {
    "AECI": "AECI", "AIRTEL": "ATEL", "BAT": "BATZ", "BATA": "BATA",
    "CEC": "CECZ", "CEC AFRICA": "CECA", "CHILANGA": "CHIL", "DCZM": "DCZM",
    "MADISON": "MAFS", "NATBREW": "NATB", "PUMA": "PUMA", "REIZ (US CENTS)": "REIZUSD",
    "SHOPRITE": "SHOP", "STANCHART": "SCBL", "ZAFFICO": "ZFCO", "ZAMBEEF": "ZMBF",
    "ZAMBIA SUGAR": "ZSUG", "ZAMBIARE": "ZMRE", "ZAMBREW": "ZABR", "ZAMEFA": "ZMFA",
    "ZANACO": "ZNCO", "ZCCM": "ZCCM", "KLRE": "KLRE"
}


def get_past_entry(data, days):
    if not data:
        return None

    latest_date = datetime.strptime(data[-1]["date"], "%Y-%m-%d")
    target_date = latest_date - timedelta(days=days)

    closest_entry = None
    smallest_diff = float("inf")

    for entry in data:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")

        if entry_date <= target_date:
            diff = (target_date - entry_date).days
            if diff < smallest_diff:
                closest_entry = entry
                smallest_diff = diff

    return closest_entry


def calculate_percentage_change(old_entry, latest_price):
    if not old_entry or not latest_price:
        return None

    old_price = old_entry.get("price")

    if not old_price or old_price == 0:
        return None

    return round(((latest_price - old_price) / old_price) * 100, 2)


def run_company_analytics():
    db = get_db()

    # Early exit check
    meta_ref = db.collection("system_meta").document("lusePortfolio")
    meta_doc = meta_ref.get()

    if meta_doc.exists:
        meta_data = meta_doc.to_dict()
        last_price_date = meta_data.get("lastPortfolioPriceDate")
        last_analysis_date = meta_data.get("lastAnalysisDate")

        if last_price_date and last_analysis_date == last_price_date:
            return {
                "status": "skipped",
                "message": f"Analytics already up-to-date ({last_price_date})",
                "processedDate": last_price_date,
                "companiesUpdated": 0,
            }

    # Process data
    listed_companies_ref = db.collection("luse_listed_companies_data")
    listed_companies = listed_companies_ref.stream()

    processed_date = None
    count = 0
    errors = []

    for company_doc in listed_companies:
        company_data = company_doc.to_dict()
        company_name = company_data.get("company_name")

        if not company_name:
            continue

        historical_key = company_name_mapping.get(company_name)

        if not historical_key:
            continue

        hist_ref = db.collection("luseCompanyHistoricPrices").document(historical_key)
        hist_doc = hist_ref.get()

        if not hist_doc.exists:
            continue

        historical_data = hist_doc.to_dict().get("chartData", [])

        if not historical_data:
            continue

        historical_data = sorted(historical_data, key=lambda x: x["date"])

        latest_price = historical_data[-1]["price"]
        processed_date = historical_data[-1]["date"]

        one_m = get_past_entry(historical_data, 30)
        three_m = get_past_entry(historical_data, 90)
        six_m = get_past_entry(historical_data, 180)
        one_y = get_past_entry(historical_data, 365)

        update_data = {
            "oneMonthChange": calculate_percentage_change(one_m, latest_price),
            "threeMonthsChange": calculate_percentage_change(three_m, latest_price),
            "sixMonthsChange": calculate_percentage_change(six_m, latest_price),
            "oneYearChange": calculate_percentage_change(one_y, latest_price),
        }

        update_data = {k: v for k, v in update_data.items() if v is not None}

        if update_data:
            try:
                listed_companies_ref.document(company_doc.id).set(update_data, merge=True)
                count += 1
            except Exception as exc:
                errors.append(f"{company_name}: {exc}")

    # Finalize
    if processed_date:
        meta_ref.set({"lastAnalysisDate": processed_date}, merge=True)

    return {
        "status": "completed",
        "message": f"Analysis complete for {processed_date} ({count} companies)",
        "processedDate": processed_date,
        "companiesUpdated": count,
        "errors": errors if errors else None,
    }


def get_fcm_access_token():
    import google.auth.transport.requests
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(
        KEY_PATH,
        scopes=FCM_SCOPES,
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token


def send_notification_payload(payload=None):
    import requests

    payload = payload or {}
    preview = build_notification_preview()
    title = payload.get("title") or preview["title"]
    body = payload.get("body") or preview["body"]
    report_date = payload.get("reportDate") or preview["reportDate"]

    if preview["alreadySent"]:
        raise ValueError(f"Daily notification already sent for {preview['reportDate']}.")

    if not preview["changes"]:
        raise ValueError("No movers to send.")

    if report_date != preview["reportDate"]:
        raise ValueError("Notification report date no longer matches the latest preview. Preview again before sending.")

    if not title.strip() or not body.strip():
        raise ValueError("Notification title and body are required.")

    access_token = get_fcm_access_token()
    fcm_url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    payload = {
        "message": {
            "topic": "allTopics",
            "notification": {
                "title": title,
                "body": body,
            },
        }
    }
    response = requests.post(
        fcm_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        raise ValueError(f"FCM send failed: {response.status_code} {response.text}")

    db = get_db()
    db.collection("luse_system").document("report_status").set({
        "last_daily_date": preview["reportDate"],
    }, merge=True)

    return {
        "sent": True,
        "reportDate": preview["reportDate"],
        "changesSent": len(preview["changes"]),
        "fcmResponse": response.json(),
    }


def ingest_payload(payload):
    from firebase_admin import firestore

    db = get_db()
    market_date = validate_market_date(payload.get("marketDate"))
    companies = payload.get("companies") or {}
    allow_backfill = bool(payload.get("allowSpecificDateInjection"))
    last_ingested_date = get_last_ingested_date()
    update_current = should_update_current_docs(
        market_date,
        last_ingested_date,
        allow_backfill,
    )

    if not companies:
        raise ValueError("No complete company rows were submitted.")

    current_updated = 0
    history_added = 0
    history_skipped = 0
    invalid_rows = []
    normalized_rows = []

    for key, row in companies.items():
        symbol = row.get("symbol")
        company_name = row.get("companyName") or key
        price = row.get("price")
        volume = row.get("volume")
        value = row.get("value")

        if symbol not in SYMBOL_TO_DOC or SYMBOL_TO_DOC[symbol] != company_name:
            invalid_rows.append(key)
            continue

        if not isinstance(price, (int, float)):
            invalid_rows.append(key)
            continue

        if not isinstance(volume, (int, float)) or volume < 0:
            invalid_rows.append(key)
            continue

        if value is None:
            value = price * volume

        normalized_rows.append({
            "symbol": symbol,
            "companyName": company_name,
            "price": float(price),
            "volume": int(volume),
            "value": float(value),
        })

    if invalid_rows:
        raise ValueError(f"Invalid company rows: {', '.join(invalid_rows)}")

    for row in normalized_rows:
        symbol = row["symbol"]
        company_name = row["companyName"]
        price = row["price"]
        volume = row["volume"]
        value = row["value"]

        if update_current:
            current_ref = db.collection("luse_listed_companies_data").document(company_name)
            current_ref.set({
                "price": price,
                "today_value": value,
                "today_volume": volume,
                "todayDate": market_date,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }, merge=True)
            current_updated += 1

        hist_ref = db.collection("luseCompanyHistoricPrices").document(symbol)
        hist_doc = hist_ref.get()
        chart_data = hist_doc.to_dict().get("chartData", []) if hist_doc.exists else []

        if any(entry.get("date") == market_date for entry in chart_data):
            history_skipped += 1
            continue

        chart_data.append({
            "date": market_date,
            "price": price,
        })
        chart_data.sort(key=lambda entry: entry["date"])

        hist_ref.set({
            "companyName": symbol,
            "chartData": chart_data,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }, merge=True)
        history_added += 1

    meta_updated = False

    if update_current:
        meta_ref = db.collection("system_meta").document("lusePortfolio")
        meta_ref.set({
            "lastPortfolioPriceUpdateAt": firestore.SERVER_TIMESTAMP,
            "lastPortfolioPriceDate": market_date,
            "lastScrapeStatus": "success",
            "lastScrapeAttemptAt": firestore.SERVER_TIMESTAMP,
            "companiesUpdatedCount": current_updated,
        }, merge=True)
        meta_updated = True

    return {
        "marketDate": market_date,
        "dateMode": payload.get("dateMode"),
        "lastIngestedDateBeforeRun": last_ingested_date,
        "currentUpdatedCount": current_updated,
        "historyAddedCount": history_added,
        "historySkippedCount": history_skipped,
        "metaUpdated": meta_updated,
        "currentUpdateSkippedReason": None if update_current else "manual_backfill_older_than_current_date",
    }


def apply_manual_price_correction(payload):
    from firebase_admin import firestore

    db = get_db()
    symbol = normalize_symbol(payload.get("symbol") or "")
    company_name = payload.get("companyName") or SYMBOL_TO_DOC.get(symbol)
    date = validate_market_date(payload.get("date"))
    price = payload.get("price")
    volume = payload.get("volume")
    value = payload.get("value")

    if symbol not in SYMBOL_TO_DOC:
        raise ValueError(f"Unknown ticker symbol: {symbol}")

    if company_name != SYMBOL_TO_DOC[symbol]:
        raise ValueError(f"Company name does not match ticker symbol {symbol}.")

    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError("Price must be a positive number.")

    current_update = {
        "price": float(price),
        "todayDate": date,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }

    if isinstance(volume, int):
        current_update["today_volume"] = volume

    if isinstance(value, (int, float)):
        current_update["today_value"] = float(value)

    db.collection("luse_listed_companies_data").document(company_name).set(
        current_update,
        merge=True,
    )

    hist_ref = db.collection("luseCompanyHistoricPrices").document(symbol)
    hist_doc = hist_ref.get()
    chart_data = hist_doc.to_dict().get("chartData", []) if hist_doc.exists else []
    replaced = False

    for entry in chart_data:
        if entry.get("date") == date:
            entry["price"] = float(price)
            replaced = True
            break

    if not replaced:
        chart_data.append({
            "date": date,
            "price": float(price),
        })

    chart_data.sort(key=lambda entry: entry["date"])

    hist_ref.set({
        "companyName": symbol,
        "chartData": chart_data,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    action = "updated" if replaced else "added"

    return {
        "symbol": symbol,
        "companyName": company_name,
        "date": date,
        "price": float(price),
        "historyAction": action,
        "currentUpdated": True,
        "message": f"{company_name} {date} price {format(float(price), '.4f')} {action} in history and current company data updated.",
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def do_POST(self):
        path = urlparse(self.path).path

        if path not in ("/api/ingest", "/api/luse/index/ingest", "/api/luse/ceca/ingest", "/api/luse/notifications/send", "/api/luse/manual-price-correction"):
            self.respond_json({"error": "Unknown POST endpoint."}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body or "{}")

            if path == "/api/luse/index/ingest":
                self.respond_json(ingest_index_payload(payload))
            elif path == "/api/luse/ceca/ingest":
                self.respond_json(ingest_ceca_payload(payload))
            elif path == "/api/luse/notifications/send":
                self.respond_json(send_notification_payload(payload))
            elif path == "/api/luse/manual-price-correction":
                self.respond_json(apply_manual_price_correction(payload))
            else:
                self.respond_json(ingest_payload(payload))
        except Exception as exc:
            self.respond_json({"error": str(exc)}, status=400)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/luse/check-date":
            self.respond_json(build_date_check())
            return

        if path == "/api/luse/scrape-draft":
            date_check = build_date_check()
            scraped = scrape_luse_page(include_rows=True)
            scraped["dateCheck"] = date_check
            self.respond_json(scraped)
            return

        if path == "/api/latest-values":
            self.respond_json(load_latest_values())
            return

        if path == "/api/luse/index/latest":
            self.respond_json(load_latest_index_data())
            return

        if path == "/api/luse/index/scrape-draft":
            self.respond_json({"indexData": scrape_luse_index_data()})
            return

        if path == "/api/luse/ceca/latest":
            self.respond_json(get_ceca_sync_state())
            return

        if path == "/api/luse/ceca/scrape-draft":
            self.respond_json({
                "cecaData": scrape_ceca_africanfinancials(),
                "syncState": get_ceca_sync_state(),
            })
            return

        if path == "/api/luse/notifications/preview":
            self.respond_json(build_notification_preview())
            return

        if path == "/api/luse/analytics/run":
            self.respond_json(run_company_analytics())
            return

        super().do_GET()

    def respond_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except ConnectionError:
            pass  # Client disconnected, ignore
        except Exception as exc:
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                body = json.dumps({"error": str(exc)}).encode("utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass  # Can't recover if error handling also fails


def main():
    port = int(os.environ.get("PORT", "3004"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"LuSE dashboard running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
