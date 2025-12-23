import pandas as pd
import requests
from io import StringIO
from datetime import timedelta

class CNBRateProvider:
    def __init__(self):
        self._cache = {}

    def get_rate(self, date_val) -> float:
        """Handles the 'Weekend Problem' by looking back to the last available working day."""
        # Ensure date is a normalized pandas timestamp for consistent comparison
        ts = pd.to_datetime(date_val).normalize()
        year = ts.year
        
        if year not in self._cache:
            self._load_year(year)
        
        rates = self._cache[year]
        # Look back up to 5 days to find the last business day rate
        for i in range(6):
            lookup_date = ts - timedelta(days=i)
            if lookup_date in rates.index:
                return rates.loc[lookup_date]
        return 0.0

    def _load_year(self, year: int):
        """Solves Performance: Fetches the whole year's TXT once and caches it."""
        url = f"https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/year.txt?year={year}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # CNB TXT format uses '|' as a separator
                df = pd.read_csv(StringIO(response.text), sep='|')
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
                df.set_index('Date', inplace=True)
                # Find the EUR column (e.g., '1 EUR')
                eur_col = [c for c in df.columns if 'EUR' in c][0]
                self._cache[year] = df[eur_col].apply(lambda x: float(str(x).replace(',', '.')))
        except Exception as e:
            print(f"Error fetching CNB data: {e}")
            self._cache[year] = pd.Series()

# Global instance to be used across all 30 token sheets
cnb = CNBRateProvider()