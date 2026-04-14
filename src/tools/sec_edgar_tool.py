import requests
import re
from bs4 import BeautifulSoup # <--- NEW IMPORT
from src.memory.redis_cache import cache_result
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Replace with your actual email!
HEADERS = {'User-Agent': 'AutoQuant_Agent_Project (your_email@domain.com)'}

@cache_result(ttl_seconds=86400)
def get_sec_filing_sections(ticker: str) -> dict:
    logger.info(f"Fetching latest SEC filing for {ticker}...")
    ticker = ticker.upper()
    
    try:
        # 1. Map Ticker to CIK
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(tickers_url, headers=HEADERS)
        response.raise_for_status()
        
        # Check if ticker exists
        ticker_map = response.json()
        cik = next((str(data['cik_str']).zfill(10) for data in ticker_map.values() if data['ticker'] == ticker), None)
                
        if not cik:
            logger.warning(f"Ticker {ticker} not found in SEC database.")
            return {}

        # 2. Get filing history
        sub_response = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS)
        sub_response.raise_for_status()
        filings = sub_response.json()['filings']['recent']

        # 3. Find the most recent 10-Q or 10-K
        try:
            doc_index = next(i for i, form in enumerate(filings['form']) if form in ['10-Q', '10-K'])
        except StopIteration:
            logger.warning(f"No recent 10-Q or 10-K found for {ticker}.")
            return {}

        # 4. Download document
        accession_no = filings['accessionNumber'][doc_index].replace('-', '')
        primary_doc = filings['primaryDocument'][doc_index]
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no}/{primary_doc}"
        
        logger.info(f"Downloading filing from: {doc_url}")
        doc_response = requests.get(doc_url, headers=HEADERS)
        doc_response.raise_for_status()
        
        # 5. --- THE FIX: Clean HTML with BeautifulSoup BEFORE searching ---
        soup = BeautifulSoup(doc_response.text, 'html.parser')
        clean_text = soup.get_text(separator=' ', strip=True)
        
        # Normalize spaces
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        extracted = {}
        
        # 6. Extract MD&A
        # Look for "Item X. Management's Discussion..."
        mda_match = re.search(r'Item\s+[27]\.\s+Management[’\'s]*\s+Discussion', clean_text, re.IGNORECASE)
        if mda_match:
            # Skip the Table of Contents mention by finding the LAST occurrence (usually the actual section)
            all_matches = list(re.finditer(r'Item\s+[27]\.\s+Management[’\'s]*\s+Discussion', clean_text, re.IGNORECASE))
            if len(all_matches) > 1:
                best_match = all_matches[-1] # Use the last match (skips TOC)
            else:
                best_match = mda_match
                
            start_idx = best_match.end()
            extracted['mda_snippet'] = clean_text[start_idx : start_idx + 30000]
            logger.info("Successfully extracted MD&A snippet.")
            
        # 7. Extract Risk Factors
        risk_match = re.search(r'Item\s+1A\.\s+Risk\s+Factors', clean_text, re.IGNORECASE)
        if risk_match:
            all_matches = list(re.finditer(r'Item\s+1A\.\s+Risk\s+Factors', clean_text, re.IGNORECASE))
            best_match = all_matches[-1] if len(all_matches) > 1 else risk_match
            
            start_idx = best_match.end()
            extracted['risk_factors_snippet'] = clean_text[start_idx : start_idx + 20000]
            logger.info("Successfully extracted Risk Factors snippet.")

        return extracted

    except Exception as e:
        logger.error(f"Failed to fetch or parse SEC EDGAR data for {ticker}: {str(e)}")
        return {}