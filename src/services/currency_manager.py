"""
Currency rate management system for automated conversions.
Supports multiple data sources and fallback strategies.
"""
import requests
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os

class CurrencyRateManager:
    """Advanced currency rate management with multiple sources and caching"""
    
    def __init__(self):
        self.rates_cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        # Default rates as fallback (updated periodically)
        self.default_rates = {
            'USD': 0.84,   # 1 USD = 0.84 GBP
            'EUR': 0.92,   # 1 EUR = 0.92 GBP
            'CAD': 0.62,   # 1 CAD = 0.62 GBP
            'AUD': 0.55,   # 1 AUD = 0.55 GBP
            'CHF': 0.95,   # 1 CHF = 0.95 GBP
            'JPY': 0.0056, # 1 JPY = 0.0056 GBP
            'CNY': 0.12,   # 1 CNY = 0.12 GBP
            'SEK': 0.080,  # 1 SEK = 0.080 GBP
            'NOK': 0.078,  # 1 NOK = 0.078 GBP
            'DKK': 0.12,   # 1 DKK = 0.12 GBP
            'PLN': 0.20,   # 1 PLN = 0.20 GBP
            'CZK': 0.036,  # 1 CZK = 0.036 GBP
            'HUF': 0.0024, # 1 HUF = 0.0024 GBP
            'INR': 0.010,  # 1 INR = 0.010 GBP
            'SGD': 0.62,   # 1 SGD = 0.62 GBP
            'HKD': 0.107,  # 1 HKD = 0.107 GBP
            'NZD': 0.51,   # 1 NZD = 0.51 GBP
            'ZAR': 0.046,  # 1 ZAR = 0.046 GBP
        }
    
    def get_conversion_rate(self, from_currency: str, to_currency: str = 'GBP') -> Optional[float]:
        """
        Get conversion rate from source currency to target currency (default GBP)
        
        Args:
            from_currency: Source currency code (USD, EUR, etc.)
            to_currency: Target currency code (default GBP)
            
        Returns:
            Conversion rate or None if not available
        """
        if from_currency == to_currency:
            return 1.0
        
        # Normalize currency codes
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()
        
        # Handle currency symbols
        from_currency = self._normalize_currency_symbol(from_currency)
        to_currency = self._normalize_currency_symbol(to_currency)
        
        # Check cache first
        cache_key = f\"{from_currency}_{to_currency}\"\n        if self._is_cache_valid(cache_key):\n            return self.rates_cache[cache_key]\n        \n        # Try to get live rate\n        live_rate = self._get_live_rate(from_currency, to_currency)\n        if live_rate:\n            self._cache_rate(cache_key, live_rate)\n            return live_rate\n        \n        # Fall back to default rates\n        return self._get_default_rate(from_currency, to_currency)\n    \n    def get_all_supported_currencies(self) -> List[str]:\n        \"\"\"Get list of all supported currency codes\"\"\"\n        return list(self.default_rates.keys()) + ['GBP']\n    \n    def update_default_rate(self, currency: str, rate: float) -> None:\n        \"\"\"Update default rate for a currency\"\"\"\n        currency = currency.upper().strip()\n        currency = self._normalize_currency_symbol(currency)\n        self.default_rates[currency] = rate\n        \n        # Clear cache for this currency\n        keys_to_remove = [key for key in self.rates_cache.keys() if currency in key]\n        for key in keys_to_remove:\n            del self.rates_cache[key]\n            if key in self.cache_expiry:\n                del self.cache_expiry[key]\n    \n    def get_rate_info(self, currency: str) -> Dict[str, any]:\n        \"\"\"Get detailed information about a currency rate\"\"\"\n        currency = currency.upper().strip()\n        currency = self._normalize_currency_symbol(currency)\n        \n        rate = self.get_conversion_rate(currency)\n        cache_key = f\"{currency}_GBP\"\n        \n        return {\n            'currency': currency,\n            'rate_to_gbp': rate,\n            'is_cached': cache_key in self.rates_cache,\n            'cache_expiry': self.cache_expiry.get(cache_key),\n            'has_default': currency in self.default_rates,\n            'default_rate': self.default_rates.get(currency),\n            'last_updated': datetime.now().isoformat()\n        }\n    \n    def _normalize_currency_symbol(self, currency: str) -> str:\n        \"\"\"Convert currency symbols to standard codes\"\"\"\n        symbol_to_code = {\n            '$': 'USD',  # Default $ to USD\n            '€': 'EUR',\n            '¥': 'JPY',\n            '£': 'GBP',\n            '₹': 'INR',\n            '₽': 'RUB',\n            '₩': 'KRW',\n            '₪': 'ILS',\n            '₫': 'VND',\n            '₱': 'PHP',\n            '₡': 'CRC',\n            '₸': 'KZT'\n        }\n        return symbol_to_code.get(currency, currency)\n    \n    def _is_cache_valid(self, cache_key: str) -> bool:\n        \"\"\"Check if cached rate is still valid\"\"\"\n        if cache_key not in self.rates_cache:\n            return False\n        \n        expiry_time = self.cache_expiry.get(cache_key)\n        if not expiry_time:\n            return False\n        \n        return datetime.now() < expiry_time\n    \n    def _cache_rate(self, cache_key: str, rate: float) -> None:\n        \"\"\"Cache a rate with expiry\"\"\"\n        self.rates_cache[cache_key] = rate\n        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration\n    \n    def _get_live_rate(self, from_currency: str, to_currency: str) -> Optional[float]:\n        \"\"\"Get live exchange rate from API (with fallback strategy)\"\"\"\n        # Try multiple sources in order of preference\n        \n        # Source 1: ExchangeRate-API (free tier)\n        try:\n            rate = self._get_rate_from_exchangerate_api(from_currency, to_currency)\n            if rate:\n                return rate\n        except Exception:\n            pass\n        \n        # Source 2: Fixer.io (backup)\n        try:\n            rate = self._get_rate_from_fixer(from_currency, to_currency)\n            if rate:\n                return rate\n        except Exception:\n            pass\n        \n        # Source 3: European Central Bank (for EUR rates)\n        if from_currency == 'EUR' or to_currency == 'EUR':\n            try:\n                rate = self._get_rate_from_ecb(from_currency, to_currency)\n                if rate:\n                    return rate\n            except Exception:\n                pass\n        \n        return None\n    \n    def _get_rate_from_exchangerate_api(self, from_currency: str, to_currency: str) -> Optional[float]:\n        \"\"\"Get rate from ExchangeRate-API (free service)\"\"\"\n        url = f\"https://api.exchangerate-api.com/v4/latest/{from_currency}\"\n        \n        try:\n            response = requests.get(url, timeout=5)\n            if response.status_code == 200:\n                data = response.json()\n                rates = data.get('rates', {})\n                return rates.get(to_currency)\n        except Exception:\n            pass\n        \n        return None\n    \n    def _get_rate_from_fixer(self, from_currency: str, to_currency: str) -> Optional[float]:\n        \"\"\"Get rate from Fixer.io (requires API key)\"\"\"\n        api_key = os.getenv('FIXER_API_KEY')\n        if not api_key:\n            return None\n        \n        url = f\"http://data.fixer.io/api/latest?access_key={api_key}&base={from_currency}&symbols={to_currency}\"\n        \n        try:\n            response = requests.get(url, timeout=5)\n            if response.status_code == 200:\n                data = response.json()\n                if data.get('success'):\n                    rates = data.get('rates', {})\n                    return rates.get(to_currency)\n        except Exception:\n            pass\n        \n        return None\n    \n    def _get_rate_from_ecb(self, from_currency: str, to_currency: str) -> Optional[float]:\n        \"\"\"Get rate from European Central Bank\"\"\"\n        # ECB provides rates against EUR\n        if from_currency != 'EUR' and to_currency != 'EUR':\n            return None\n        \n        url = \"https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml\"\n        \n        try:\n            response = requests.get(url, timeout=5)\n            if response.status_code == 200:\n                # Parse XML and extract rates\n                # This would need XML parsing - simplified for now\n                pass\n        except Exception:\n            pass\n        \n        return None\n    \n    def _get_default_rate(self, from_currency: str, to_currency: str) -> Optional[float]:\n        \"\"\"Get rate from default rates table\"\"\"\n        if to_currency != 'GBP':\n            # For non-GBP conversions, convert through GBP\n            from_to_gbp = self.default_rates.get(from_currency)\n            to_to_gbp = self.default_rates.get(to_currency)\n            \n            if from_to_gbp and to_to_gbp:\n                # Convert: from -> GBP -> to\n                return from_to_gbp / to_to_gbp\n            \n            return None\n        \n        return self.default_rates.get(from_currency)\n    \n    def batch_convert(self, amounts_and_currencies: List[Dict[str, any]], \n                     to_currency: str = 'GBP') -> List[Dict[str, any]]:\n        \"\"\"Convert multiple amounts in batch\"\"\"\n        results = []\n        \n        for item in amounts_and_currencies:\n            amount = item.get('amount', 0)\n            from_currency = item.get('currency', 'GBP')\n            \n            rate = self.get_conversion_rate(from_currency, to_currency)\n            \n            if rate:\n                converted_amount = amount * rate\n                results.append({\n                    'original_amount': amount,\n                    'original_currency': from_currency,\n                    'converted_amount': round(converted_amount, 2),\n                    'converted_currency': to_currency,\n                    'conversion_rate': rate,\n                    'conversion_date': datetime.now().isoformat()\n                })\n            else:\n                results.append({\n                    'original_amount': amount,\n                    'original_currency': from_currency,\n                    'error': f\"No conversion rate available for {from_currency} to {to_currency}\"\n                })\n        \n        return results\n\n\n# Global instance\ncurrency_manager = CurrencyRateManager()\n\n\ndef get_currency_rate(from_currency: str, to_currency: str = 'GBP') -> Optional[float]:\n    \"\"\"Convenience function to get conversion rate\"\"\"\n    return currency_manager.get_conversion_rate(from_currency, to_currency)\n\n\ndef convert_amount(amount: float, from_currency: str, to_currency: str = 'GBP') -> Optional[float]:\n    \"\"\"Convenience function to convert amount between currencies\"\"\"\n    rate = get_currency_rate(from_currency, to_currency)\n    if rate:\n        return round(amount * rate, 2)\n    return None\n\n\ndef get_supported_currencies() -> List[str]:\n    \"\"\"Get list of supported currency codes\"\"\"\n    return currency_manager.get_all_supported_currencies()