"""
Currency conversion utilities for multi-currency support
"""
import re
from typing import Dict, Tuple, Optional

# Common currency mappings
CURRENCY_SYMBOLS = {
    '£': 'GBP',
    '$': 'USD', 
    '€': 'EUR',
    '¥': 'JPY',
    '₹': 'INR',
    '¢': 'USD',  # Cents
    '₽': 'RUB',
    '₴': 'UAH',
    '₦': 'NGN',
    '₨': 'INR',
    '₩': 'KRW',
    '₪': 'ILS',
    '₫': 'VND',
    '₱': 'PHP',
    '₡': 'CRC',
    '₸': 'KZT',
    'R$': 'BRL',
    'C$': 'CAD',
    'A$': 'AUD',
    'CHF': 'CHF',
    'SEK': 'SEK',
    'NOK': 'NOK',
    'DKK': 'DKK',
    'PLN': 'PLN',
    'HUF': 'HUF',
    'CZK': 'CZK',
    'RMB': 'CNY',
    '¤': 'UNKNOWN'  # Generic currency symbol
}

CURRENCY_CODES = {
    'GBP': '£',
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'INR': '₹',
    'RUB': '₽',
    'UAH': '₴',
    'NGN': '₦',
    'KRW': '₩',
    'ILS': '₪',
    'VND': '₫',
    'PHP': '₱',
    'CRC': '₡',
    'KZT': '₸',
    'BRL': 'R$',
    'CAD': 'C$',
    'AUD': 'A$',
    'CHF': 'CHF',
    'SEK': 'SEK',
    'NOK': 'NOK',
    'DKK': 'DKK',
    'PLN': 'PLN',
    'HUF': 'HUF',
    'CZK': 'CZK',
    'CNY': '¥',
    'RMB': '¥'
}

def detect_currency(text: str) -> Tuple[str, str]:
    """
    Detect currency from text
    Returns: (currency_code, currency_symbol)
    """
    text = text.upper()
    
    # Check for explicit currency codes first
    for code in CURRENCY_CODES.keys():
        if code in text:
            symbol = CURRENCY_CODES.get(code, code)
            return code, symbol
    
    # Check for currency symbols
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code, symbol
    
    # Default to GBP if no currency detected
    return 'GBP', '£'

def normalize_currency(currency_input: str) -> Tuple[str, str]:
    """
    Normalize currency input to standard code and symbol
    Returns: (currency_code, currency_symbol)
    """
    if not currency_input:
        return 'GBP', '£'
    
    currency_input = currency_input.strip().upper()
    
    # Direct code match
    if currency_input in CURRENCY_CODES:
        return currency_input, CURRENCY_CODES[currency_input]
    
    # Symbol match
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in currency_input or currency_input == symbol:
            return code, symbol
    
    # Special cases
    if currency_input in ['DOLLAR', 'DOLLARS']:
        return 'USD', '$'
    elif currency_input in ['POUND', 'POUNDS']:
        return 'GBP', '£'
    elif currency_input in ['EURO', 'EUROS']:
        return 'EUR', '€'
    elif currency_input in ['YEN']:
        return 'JPY', '¥'
    elif currency_input in ['RUPEE', 'RUPEES']:
        return 'INR', '₹'
    
    # Default to input as-is if unknown
    return currency_input, currency_input

def convert_price(amount: float, from_currency: str, to_currency: str, conversion_rate: float) -> float:
    """
    Convert price from one currency to another
    """
    if from_currency.upper() == to_currency.upper():
        return amount
    
    return round(amount * conversion_rate, 2)

def format_price(amount: float, currency_code: str, currency_symbol: str) -> str:
    """
    Format price with appropriate currency symbol
    """
    return f"{currency_symbol}{amount:.2f}"

def get_currency_name(currency_code: str) -> str:
    """
    Get full currency name from code
    """
    currency_names = {
        'GBP': 'British Pound',
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'JPY': 'Japanese Yen',
        'INR': 'Indian Rupee',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar',
        'CHF': 'Swiss Franc',
        'RUB': 'Russian Ruble',
        'CNY': 'Chinese Yuan',
        'RMB': 'Chinese Yuan',
        'SEK': 'Swedish Krona',
        'NOK': 'Norwegian Krone',
        'DKK': 'Danish Krone',
        'PLN': 'Polish Zloty',
        'HUF': 'Hungarian Forint',
        'CZK': 'Czech Koruna',
        'KRW': 'South Korean Won',
        'SGD': 'Singapore Dollar',
        'HKD': 'Hong Kong Dollar',
        'NZD': 'New Zealand Dollar',
        'ZAR': 'South African Rand',
        'BRL': 'Brazilian Real',
        'MXN': 'Mexican Peso'
    }
    
    return currency_names.get(currency_code.upper(), currency_code)

def is_gbp_currency(currency: str) -> bool:
    """
    Check if currency is GBP/Pound
    """
    currency = currency.upper().strip()
    return currency in ['GBP', '£', 'POUND', 'POUNDS', 'STERLING']