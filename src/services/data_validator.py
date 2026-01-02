"""
Data validation and quality checks for extracted supplier data.
Ensures data integrity and consistency across the system.
"""
import re
import datetime
from typing import Dict, List, Any, Tuple
from decimal import Decimal, InvalidOperation

class DataValidator:
    """Comprehensive data validation for supplier extraction"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_extraction(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete extraction data and return quality report
        
        Returns:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'quality_score': float,
                'cleaned_data': Dict[str, Any]
            }
        """
        self.errors = []
        self.warnings = []
        
        cleaned_data = extracted_data.copy()
        
        # Validate supplier information
        cleaned_data['supplier'] = self._validate_supplier(cleaned_data.get('supplier', {}))
        
        # Validate products
        cleaned_data['products'] = self._validate_products(cleaned_data.get('products', []))
        
        # Validate document info
        cleaned_data['document_info'] = self._validate_document_info(
            cleaned_data.get('document_info', {})
        )
        
        # Validate totals
        cleaned_data['totals'] = self._validate_totals(cleaned_data.get('totals', {}))
        
        # Validate currency consistency
        self._validate_currency_consistency(cleaned_data)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(cleaned_data)
        
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'quality_score': quality_score,
            'cleaned_data': cleaned_data
        }
    
    def _validate_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean supplier information"""
        cleaned = supplier_data.copy()
        
        # Validate company name
        name = cleaned.get('name', '').strip()
        if not name or name.lower() in ['unknown', 'n/a', 'not found']:
            self.errors.append("Missing or invalid supplier name")
        else:
            cleaned['name'] = self._clean_company_name(name)
        
        # Validate email
        email = cleaned.get('email', '').strip()
        if email and not self._is_valid_email(email):
            self.warnings.append(f"Invalid email format: {email}")
            cleaned['email'] = None
        elif email:
            cleaned['email'] = email.lower()
        
        # Validate phone number
        phone = cleaned.get('phone', '').strip()
        if phone:
            cleaned_phone = self._clean_phone_number(phone)
            if not cleaned_phone:
                self.warnings.append(f"Invalid phone format: {phone}")
            cleaned['phone'] = cleaned_phone
        
        # Validate VAT number
        vat = cleaned.get('vat_number', '').strip()
        if vat:
            cleaned_vat = self._validate_vat_number(vat)
            if not cleaned_vat:
                self.warnings.append(f"Invalid VAT number format: {vat}")
            cleaned['vat_number'] = cleaned_vat
        
        # Clean address
        address = cleaned.get('address', '').strip()
        if address:
            cleaned['address'] = self._clean_address(address)
        
        return cleaned
    
    def _validate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean product information"""
        cleaned_products = []
        
        for i, product in enumerate(products):
            cleaned_product = product.copy()
            product_errors = []
            
            # Validate product name
            name = cleaned_product.get('name', '').strip()
            if not name or name.lower() in ['unknown', 'n/a', 'not found']:
                product_errors.append(f"Product {i+1}: Missing product name")
            else:
                cleaned_product['name'] = self._clean_product_name(name)
            
            # Validate pricing
            price_validation = self._validate_product_pricing(cleaned_product, i+1)
            cleaned_product.update(price_validation['cleaned_data'])
            if price_validation['errors']:
                product_errors.extend(price_validation['errors'])
            if price_validation['warnings']:
                self.warnings.extend(price_validation['warnings'])
            
            # Validate quantity
            quantity = cleaned_product.get('quantity')
            if quantity is not None:
                try:
                    cleaned_quantity = float(quantity)
                    if cleaned_quantity <= 0:
                        self.warnings.append(f"Product {i+1}: Invalid quantity {quantity}")
                        cleaned_product['quantity'] = 1
                    else:
                        cleaned_product['quantity'] = int(cleaned_quantity) if cleaned_quantity == int(cleaned_quantity) else cleaned_quantity
                except (ValueError, TypeError):
                    self.warnings.append(f"Product {i+1}: Invalid quantity format {quantity}")
                    cleaned_product['quantity'] = 1
            
            # Clean description
            description = cleaned_product.get('description', '').strip()
            if description:
                cleaned_product['description'] = self._clean_description(description)
            
            # Add product-level errors to main errors
            if product_errors:
                self.errors.extend(product_errors)
            
            if not product_errors:  # Only add valid products
                cleaned_products.append(cleaned_product)
        
        return cleaned_products
    
    def _validate_product_pricing(self, product: Dict[str, Any], product_num: int) -> Dict[str, Any]:
        """Validate product pricing information"""
        errors = []
        warnings = []
        cleaned = {}
        
        # Validate unit price
        unit_price = product.get('unit_price')
        if unit_price is not None:
            try:
                cleaned_unit_price = float(unit_price)
                if cleaned_unit_price < 0:
                    warnings.append(f"Product {product_num}: Negative unit price {unit_price}")
                cleaned['unit_price'] = round(cleaned_unit_price, 4)
            except (ValueError, TypeError):
                errors.append(f"Product {product_num}: Invalid unit price format {unit_price}")
                cleaned['unit_price'] = 0.0
        
        # Validate total price
        price = product.get('price')
        if price is not None:
            try:
                cleaned_price = float(price)
                if cleaned_price < 0:
                    warnings.append(f"Product {product_num}: Negative total price {price}")
                cleaned['price'] = round(cleaned_price, 2)
            except (ValueError, TypeError):
                errors.append(f"Product {product_num}: Invalid price format {price}")
                cleaned['price'] = 0.0
        
        # Cross-validate pricing
        if (cleaned.get('unit_price') and cleaned.get('price') and 
            product.get('quantity') and product['quantity'] > 0):
            expected_total = cleaned['unit_price'] * product['quantity']
            actual_total = cleaned['price']
            if abs(expected_total - actual_total) > 0.01:  # Allow small rounding differences
                warnings.append(
                    f"Product {product_num}: Price mismatch - "
                    f"{cleaned['unit_price']} × {product['quantity']} = {expected_total:.2f} "
                    f"but total price is {actual_total:.2f}"
                )
        
        return {
            'cleaned_data': cleaned,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_document_info(self, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document information"""
        cleaned = doc_info.copy()
        
        # Validate dates
        for date_field in ['date', 'due_date', 'invoice_date']:
            if date_field in cleaned and cleaned[date_field]:
                parsed_date = self._parse_date(cleaned[date_field])
                if parsed_date:
                    cleaned[date_field] = parsed_date.isoformat()
                else:
                    self.warnings.append(f"Invalid date format for {date_field}: {cleaned[date_field]}")
                    cleaned[date_field] = None
        
        return cleaned
    
    def _validate_totals(self, totals: Dict[str, Any]) -> Dict[str, Any]:
        """Validate totals information"""
        cleaned = totals.copy()
        
        # Validate monetary amounts
        for amount_field in ['subtotal', 'tax', 'total_amount']:
            if amount_field in cleaned and cleaned[amount_field] is not None:
                try:
                    amount = float(cleaned[amount_field])
                    cleaned[amount_field] = round(amount, 2)
                except (ValueError, TypeError):
                    self.warnings.append(f"Invalid {amount_field} format: {cleaned[amount_field]}")
                    cleaned[amount_field] = 0.0
        
        # Cross-validate totals
        subtotal = cleaned.get('subtotal', 0)
        tax = cleaned.get('tax', 0)
        total = cleaned.get('total_amount', 0)
        
        if subtotal and tax and total:
            expected_total = subtotal + tax
            if abs(expected_total - total) > 0.01:
                self.warnings.append(
                    f"Total calculation mismatch: {subtotal} + {tax} = {expected_total:.2f} "
                    f"but total_amount is {total:.2f}"
                )
        
        return cleaned
    
    def _validate_currency_consistency(self, data: Dict[str, Any]) -> None:
        """Ensure currency consistency across the document"""
        main_currency = data.get('currency')
        
        if not main_currency:
            self.errors.append("Missing main document currency")
            return
        
        # Check product currencies
        products = data.get('products', [])
        for i, product in enumerate(products):
            product_currency = product.get('currency')
            if product_currency and product_currency != main_currency:
                self.warnings.append(
                    f"Product {i+1}: Currency mismatch - document uses {main_currency}, "
                    f"product uses {product_currency}"
                )
        
        # Check totals currency
        totals_currency = data.get('totals', {}).get('currency')
        if totals_currency and totals_currency != main_currency:
            self.warnings.append(
                f"Totals currency mismatch - document uses {main_currency}, "
                f"totals use {totals_currency}"
            )
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-100)"""
        score = 100.0
        
        # Deduct points for errors (major issues)
        score -= len(self.errors) * 15
        
        # Deduct points for warnings (minor issues)
        score -= len(self.warnings) * 5
        
        # Check completeness
        supplier = data.get('supplier', {})
        completeness_checks = [
            supplier.get('name'),
            supplier.get('email'),
            supplier.get('phone'),
            data.get('currency'),
            len(data.get('products', [])) > 0
        ]
        
        completeness_score = sum(1 for check in completeness_checks if check) / len(completeness_checks)
        score = score * completeness_score
        
        return max(0.0, min(100.0, score))
    
    # Helper methods
    def _clean_company_name(self, name: str) -> str:
        """Clean and standardize company name"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Fix common issues
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email format is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and validate phone number"""
        # Remove common formatting
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Basic validation - must have at least 7 digits
        if len(re.sub(r'[^\d]', '', cleaned)) < 7:
            return None
        
        return cleaned
    
    def _validate_vat_number(self, vat: str) -> str:
        """Validate VAT number format"""
        # Remove spaces and normalize
        vat = vat.upper().replace(' ', '')
        
        # Basic validation for common formats
        if re.match(r'^[A-Z]{2}[0-9]{8,12}$', vat):  # EU format
            return vat
        elif re.match(r'^[0-9]{8,15}$', vat):  # Numeric only
            return vat
        elif len(vat) > 5:  # Assume valid if reasonable length
            return vat
        
        return None
    
    def _clean_address(self, address: str) -> str:
        """Clean address formatting"""
        # Replace multiple spaces/newlines with single space
        cleaned = re.sub(r'\s+', ' ', address)
        return cleaned.strip()
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name"""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(name.split())
        return cleaned.strip()
    
    def _clean_description(self, description: str) -> str:
        """Clean product description"""
        # Remove extra whitespace but preserve structure
        cleaned = re.sub(r'\s+', ' ', description)
        return cleaned.strip()
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse various date formats"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d'
        ]
        
        date_str = date_str.strip()
        
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None


def validate_extraction_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate extraction data
    
    Args:
        extracted_data: Raw extraction data from AI
        
    Returns:
        Validation result with cleaned data and quality metrics
    """
    validator = DataValidator()
    return validator.validate_extraction(extracted_data)