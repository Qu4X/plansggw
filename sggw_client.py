"""
Klient pobierania planów zajęć SGGW z SharePoint / stron wydziałowych.
"""
import os
import re
import logging
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("sggw_client")

# Domyślny katalog planów WMW SGGW (semestry zimowe 2026/2027)
WMW_SCHEDULE_URL = "https://wmw.sggw.edu.pl/strefa-studenta/plan-zajec-i-programy-studiow/"

DEFAULT_WMW_PLANS = {
    "wmw_sem_7": {
        "id": "wmw_sem_7",
        "name": "Weterynaria sem. 7 (IV rok)",
        "sharepoint_url": "https://sggwpl-my.sharepoint.com/:x:/g/personal/p104180_sggw_edu_pl/IQB6QFz3yl8FRYXMqAhlLpVoAYNgS1MCPw5p2CDIc8PdADU?e=zhzcON",
        "faculty": "WMW",
        "semester": 7
    }
}


def to_direct_download_url(sharepoint_url: str) -> str:
    """Konwertuje publiczny link SharePoint do bezpośredniego linku pobierania binarnego."""
    if not sharepoint_url:
        return ""
    sep = "&" if "?" in sharepoint_url else "?"
    if "download=1" not in sharepoint_url:
        return f"{sharepoint_url}{sep}download=1"
    return sharepoint_url


def download_plan_file(sharepoint_url: str, output_path: str, session: Optional[requests.Session] = None) -> bool:
    """Pobiera arkusz XLSX z SharePoint i zapisuje go lokalnie."""
    dl_url = to_direct_download_url(sharepoint_url)
    s = session or requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = s.get(dl_url, headers=headers, allow_redirects=True, timeout=30)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        logger.info(f"Pobrano plan do {output_path} ({len(resp.content)} bajtów)")
        return True
    except Exception as e:
        logger.error(f"Błąd pobierania z SharePoint ({sharepoint_url}): {e}")
        return False


def discover_wmw_plans(page_url: str = WMW_SCHEDULE_URL) -> Dict[str, Dict[str, str]]:
    """Przeszukuje stronę wydziału WMW w poszukiwaniu linków do planów na SharePoint."""
    discovered = {}
    try:
        resp = requests.get(page_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if "sharepoint.com" in href and "semestr" in text.lower():
                m_sem = re.search(r'semestr\s*(\d+)', text, re.IGNORECASE)
                sem_num = int(m_sem.group(1)) if m_sem else 0
                plan_id = f"wmw_sem_{sem_num}"
                discovered[plan_id] = {
                    "id": plan_id,
                    "name": f"Weterynaria sem. {sem_num}",
                    "sharepoint_url": href,
                    "faculty": "WMW",
                    "semester": sem_num
                }
    except Exception as e:
        logger.warning(f"Nie udało się pobrać listy ze strony WMW ({page_url}): {e}")
    return discovered or DEFAULT_WMW_PLANS
