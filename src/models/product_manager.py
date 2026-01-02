# Product management with Supabase integration
import uuid
import sys
import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SUPABASE_URL, SUPABASE_KEY, TABLE_PRODUCTS, DATABASE_ENABLED

class ProductManager:
    def __init__(self):
        if DATABASE_ENABLED and SUPABASE_URL != "https://YOUR_PROJECT.supabase.co":
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.enabled = True
        else:
            self.supabase = None
            self.enabled = False
    
    def save_products_comprehensive(self, supplier_id: str, products: List[Dict[str, Any]], document_id: str = None) -> List[Dict[str, Any]]:
        """Save comprehensive product data with duplicate detection and currency conversion"""
        
        if not self.enabled:
            for product in products:
                name = product.get('name', 'Unknown')
                price = product.get('price') or product.get('pricing', {}).get('unit_price', 0)
                print(f"   • {name} - £{price}")
            return products
        
        try:
            # Ensure supplier_id is a string
            if not isinstance(supplier_id, str):
                print(f"❌ PRODUCT DEBUG: Invalid supplier_id type: {type(supplier_id)}")
                return []
                
            saved_products = []
            new_products = []
            updated_products = []
            
            print(f"🔍 PRODUCT DEBUG: Processing {len(products)} products for supplier_id: {supplier_id}")
            
            # Debug: Show what products we're trying to save
            print(f"📦 PRODUCTS TO PROCESS:")
            for i, product in enumerate(products):
                name = product.get('name', 'Unknown')
                supplier = product.get('supplier_name', 'Unknown')
                price = product.get('price', 0)
                print(f"   {i+1}. '{name}' from supplier '{supplier}' - £{price:.2f}")
            
            # Get existing products for this supplier for duplicate checking
            existing_products = self._get_existing_products_for_supplier(supplier_id)
            
            print(f"🔍 DUPLICATE CHECK: Found {len(existing_products)} existing products to check against")
            
            for i, product in enumerate(products):
                # Ensure product is a dictionary
                if not isinstance(product, dict):
                    print(f"❌ PRODUCT DEBUG: Product {i} is not a dict: {type(product)}")
                    continue
                
                print(f"\n🔍 PROCESSING PRODUCT {i+1}: '{product.get('name', 'Unknown')}'")
                
                # Check if this product already exists
                existing_product = self._find_existing_product(product, existing_products)
                
                if existing_product:
                    # Product exists - check if we should update it
                    print(f"📋 PRODUCT EXISTS: Checking if update needed...")
                    if self._should_update_product(product, existing_product):
                        updated_product = self._update_existing_product(existing_product['id'], product)
                        updated_products.append(updated_product)
                        print(f"🔄 PRODUCT DEBUG: Updated existing product: {product.get('name', 'No name')}")
                    else:
                        print(f"ℹ️ PRODUCT DEBUG: Product unchanged, skipping: {product.get('name', 'No name')}")
                        saved_products.append(existing_product)
                else:
                    # New product - create it
                    print(f"➕ PRODUCT DEBUG: Creating new product: {product.get('name', 'No name')}")
                    product_record = self._build_product_record(supplier_id, product, document_id)
                    new_products.append(product_record)
                    print(f"✅ PRODUCT DEBUG: New product record built")
            
            # Batch insert new products
            if new_products:
                print(f"💾 PRODUCT DEBUG: Saving {len(new_products)} new products to database")
                result = self.supabase.table(TABLE_PRODUCTS).insert(new_products).execute()
                saved_products.extend(result.data if result.data else [])
                print(f"✅ PRODUCT DEBUG: Created {len(result.data) if result.data else 0} new products")
            
            # Add updated products to the result
            saved_products.extend(updated_products)
            
            # Log summary
            print(f"📊 PRODUCT SUMMARY: {len(new_products)} new, {len(updated_products)} updated, {len(saved_products) - len(new_products) - len(updated_products)} unchanged")
            
            return saved_products
            
        except Exception as e:
            print(f"❌ PRODUCT DEBUG: Error saving products: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    def _build_product_record(self, supplier_id: str, product: Dict[str, Any], document_id: str = None) -> Dict[str, Any]:
        """Build product record with both original and converted prices"""
        product_id = str(uuid.uuid4())
        
        # Extract pricing and currency information
        pricing = product.get('pricing', {})
        original_price = self._safe_float(pricing.get('unit_price') or product.get('price') or product.get('original_price'))
        original_currency = pricing.get('currency') or product.get('currency') or product.get('original_currency') or 'GBP'
        
        # Get conversion rate and calculate GBP price
        conversion_rate = self._safe_float(product.get('conversion_rate'), 1.0)
        gbp_price = original_price
        
        # If currency is not GBP and we have a conversion rate, convert to GBP
        if original_currency != 'GBP' and conversion_rate != 1.0:
            gbp_price = original_price * conversion_rate
            print(f"💱 CURRENCY: {original_currency} {original_price} -> GBP {gbp_price:.2f} (rate: {conversion_rate})")
        
        # Build record with enhanced price fields
        record = {
            'id': product_id,
            'product_name': product.get('name', 'Unknown Product'),
            'unit_price': gbp_price,  # Always store GBP price in unit_price for consistency
            'currency': 'GBP',  # Main currency field is always GBP
            'category': product.get('category', 'Unknown'),
            # Store original price information
            'original_price': original_price,
            'original_currency': original_currency,
            'conversion_rate': conversion_rate if conversion_rate != 1.0 else None
        }
        
        # Add supplier info in usage_type as a temporary solution
        supplier_name = product.get('supplier_name', 'Unknown')
        if supplier_name != 'Unknown':
            record['usage_type'] = f"Supplier: {supplier_name}"
        elif product.get('usage_type'):
            record['usage_type'] = product.get('usage_type')
        
        # Add other optional fields
        optional_fields = {
            'size': product.get('size'),
            'material': product.get('material'),
            'original_currency_symbol': self._get_currency_symbol(original_currency)
        }
        
        # Only include non-empty optional fields
        for key, value in optional_fields.items():
            if value is not None and value != '' and value != 0.0:
                record[key] = value
        
        return record
    
    def _get_existing_products_for_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get all existing products to check for duplicates (since usage_type format is inconsistent)"""
        try:
            # Since the usage_type format is inconsistent between old and new data,
            # we'll get all products and do more sophisticated matching
            print(f"🔍 DUPLICATE CHECK: Getting all products for duplicate detection (supplier_id: {supplier_id})")
            
            result = self.supabase.table(TABLE_PRODUCTS).select("*").execute()
            
            existing_count = len(result.data) if result.data else 0
            print(f"🔍 DUPLICATE CHECK: Found {existing_count} total products in database")
            
            if result.data and existing_count > 0:
                print(f"📊 EXISTING PRODUCTS (showing first 5):")
                for i, product in enumerate(result.data[:5]):
                    try:
                        usage = product.get('usage_type', 'No usage_type') or 'No usage_type'
                        category = product.get('category', 'No category') or 'No category'
                        unit_price = product.get('unit_price') or 0
                        product_name = product.get('product_name', 'Unknown') or 'Unknown'
                        print(f"   {i+1}. '{product_name}' - £{float(unit_price):.2f}")
                        print(f"      Category: {category}")
                        print(f"      Usage: {usage[:100]}{'...' if len(usage) > 100 else ''}")
                    except Exception as e:
                        print(f"   {i+1}. Error displaying product: {e}")
                if len(result.data) > 5:
                    print(f"   ... and {len(result.data) - 5} more")
            else:
                print(f"📊 No existing products found")
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error fetching existing products: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_existing_product(self, new_product: Dict[str, Any], existing_products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find if a product already exists using robust matching (name + category + size)"""
        new_name = new_product.get('name', '').lower().strip()
        new_category = new_product.get('category', 'unknown').lower().strip()
        new_size = new_product.get('size', '').lower().strip()
        new_supplier = new_product.get('supplier_name', '')
        
        print(f"🔍 DUPLICATE CHECK: Looking for existing product:")
        print(f"   Name: '{new_name}'")
        print(f"   Category: '{new_category}'")
        print(f"   Size: '{new_size}'")
        print(f"   Supplier: '{new_supplier}'")
        print(f"🔍 DUPLICATE CHECK: Checking against {len(existing_products)} existing products")
        
        best_match = None
        best_score = 0
        
        for i, existing in enumerate(existing_products):
            existing_name = existing.get('product_name', '').lower().strip()
            existing_category = existing.get('category', '').lower().strip()
            existing_size = existing.get('size', '').lower().strip()
            existing_usage = existing.get('usage_type', '')
            existing_id = existing.get('id', 'no-id')
            
            print(f"\n   📋 #{i+1}: '{existing_name}' (ID: {existing_id[:8]}...)")
            print(f"      Category: '{existing_category}'")
            print(f"      Size: '{existing_size}'")
            print(f"      Usage: {existing_usage[:50]}{'...' if len(existing_usage) > 50 else ''}")
            
            # Calculate match score based on multiple criteria
            match_score = 0
            
            # 1. Check product name similarity (most important - 50 points)
            if self._products_are_similar(new_name, existing_name):
                match_score += 50
                print(f"      ✅ Name match (+50): '{new_name}' ~ '{existing_name}'")
            else:
                print(f"      ❌ Name no match: '{new_name}' != '{existing_name}'")
                continue  # If names don't match, skip this product
            
            # 2. Check category similarity (20 points)
            if new_category != 'unknown' and existing_category:
                if new_category == existing_category or new_category in existing_category or existing_category in new_category:
                    match_score += 20
                    print(f"      ✅ Category match (+20): '{new_category}' ~ '{existing_category}'")
                else:
                    print(f"      ❌ Category mismatch: '{new_category}' != '{existing_category}'")
            
            # 3. Check size similarity (15 points)
            if new_size and existing_size:
                # Clean sizes for comparison
                clean_new_size = self._clean_size(new_size)
                clean_existing_size = self._clean_size(existing_size)
                if clean_new_size == clean_existing_size or clean_new_size in clean_existing_size or clean_existing_size in clean_new_size:
                    match_score += 15
                    print(f"      ✅ Size match (+15): '{new_size}' ~ '{existing_size}'")
                else:
                    print(f"      ❌ Size mismatch: '{new_size}' != '{existing_size}'")
            
            # 4. Check supplier context (15 points) - handle both old and new usage_type formats
            if new_supplier:
                supplier_match = False
                if f"Supplier: {new_supplier}" in existing_usage:  # New format
                    supplier_match = True
                elif new_supplier.lower() in existing_usage.lower():  # Partial match
                    supplier_match = True
                # For old format, we can't reliably match supplier, so don't penalize
                
                if supplier_match:
                    match_score += 15
                    print(f"      ✅ Supplier context match (+15)")
                else:
                    print(f"      ℹ️ No supplier context match (old format?)")
            
            print(f"      📊 Total match score: {match_score}/100")
            
            # If this is a better match than previous best
            if match_score > best_score:
                best_match = existing
                best_score = match_score
        
        # Consider it a match if score is 50+ (at least name + some other criteria)
        if best_match and best_score >= 50:
            print(f"\n✅ DUPLICATE FOUND: Best match with score {best_score}/100")
            print(f"   Existing: '{best_match.get('product_name', 'Unknown')}' (ID: {best_match.get('id', 'no-id')[:8]}...)")
            return best_match
        else:
            print(f"\n➕ NEW PRODUCT: No sufficient match found (best score: {best_score}/100)")
            return None
    
    def _products_are_similar(self, name1: str, name2: str) -> bool:
        """Check if two product names are similar enough to be the same product"""
        if not name1 or not name2:
            return False
        
        # Check for size/volume conflicts first (critical!)
        if self._has_conflicting_sizes(name1, name2):
            return False
        
        # Exact match (case insensitive)
        if name1.lower() == name2.lower():
            return True
        
        # Remove common variations and check again
        clean1 = self._clean_product_name(name1)
        clean2 = self._clean_product_name(name2)
        
        if clean1 == clean2 and len(clean1) > 2:  # Avoid matching very short cleaned names
            return True
        
        # Check if one contains the other (for longer names only)
        if len(clean1) >= 8 and len(clean2) >= 8:  # Increase minimum length
            if clean1 in clean2 or clean2 in clean1:
                return True
        
        # Check for very similar names (allow small differences)
        if len(clean1) > 5 and len(clean2) > 5:
            # Calculate similarity ratio
            common_chars = len(set(clean1.lower()) & set(clean2.lower()))
            total_chars = len(set(clean1.lower()) | set(clean2.lower()))
            similarity = common_chars / total_chars if total_chars > 0 else 0
            
            if similarity > 0.8:  # 80% character overlap
                return True
        
        return False
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name for better comparison"""
        import re
        
        # Convert to lowercase and strip whitespace
        clean = name.lower().strip()
        
        # Remove extra spaces and normalize
        clean = re.sub(r'\s+', ' ', clean)
        
        # Remove common packaging indicators but keep the core product info
        clean = re.sub(r'\b(pack of|box of|case of|carton of|set of)\s*\d+\b', '', clean)
        clean = re.sub(r'\b\d+\s*(pack|box|case|carton|set)\b', '', clean)
        
        # Remove extra punctuation but keep important ones like sizes
        clean = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', clean)
        
        # Remove common filler words
        filler_words = ['the', 'a', 'an', 'with', 'for', 'in', 'on', 'at', 'by']
        words = clean.split()
        words = [word for word in words if word not in filler_words]
        
        clean = ' '.join(words).strip()
        
        print(f"         🧽 Cleaned '{name}' -> '{clean}'")
        return clean
    
    def _clean_size(self, size: str) -> str:
        """Clean size/packaging info for better comparison"""
        import re
        clean = size.lower().strip()
        
        # Normalize common variations
        clean = re.sub(r'pieces?|pcs?', 'pcs', clean)
        clean = re.sub(r'boxes?|box', 'box', clean)
        clean = re.sub(r'packs?|pack', 'pack', clean)
        
        # Remove extra spacing and punctuation
        clean = re.sub(r'[^\w\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    def _should_update_product(self, new_product: Dict[str, Any], existing_product: Dict[str, Any]) -> bool:
        """Check if we should update an existing product with new information"""
        # Check if price has changed significantly
        new_price = self._safe_float(new_product.get('price') or new_product.get('pricing', {}).get('unit_price', 0))
        existing_price = self._safe_float(existing_product.get('unit_price', 0))
        
        # Update if price difference is more than 1%
        if abs(new_price - existing_price) / max(existing_price, 0.01) > 0.01:
            return True
        
        # Check if we have more complete information
        new_fields = ['size', 'material', 'category']
        for field in new_fields:
            if (new_product.get(field) and 
                new_product.get(field) != 'Unknown' and
                (not existing_product.get(field) or existing_product.get(field) == 'Unknown')):
                return True
        
        return False
    
    def _update_existing_product(self, product_id: str, new_product: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product with new information"""
        try:
            # Build update data
            pricing = new_product.get('pricing', {})
            original_price = self._safe_float(pricing.get('unit_price') or new_product.get('price'))
            original_currency = pricing.get('currency') or new_product.get('currency') or 'GBP'
            conversion_rate = self._safe_float(new_product.get('conversion_rate'), 1.0)
            
            gbp_price = original_price
            if original_currency != 'GBP' and conversion_rate != 1.0:
                gbp_price = original_price * conversion_rate
            
            update_data = {
                'unit_price': gbp_price,
                'original_price': original_price,
                'original_currency': original_currency,
                'conversion_rate': conversion_rate if conversion_rate != 1.0 else None
            }
            
            # Add other fields if they have meaningful values
            optional_updates = {
                'size': new_product.get('size'),
                'material': new_product.get('material'),
                'category': new_product.get('category')
            }
            
            for key, value in optional_updates.items():
                if value and value != 'Unknown':
                    update_data[key] = value
            
            # Perform update
            result = self.supabase.table(TABLE_PRODUCTS).update(update_data).eq('id', product_id).execute()
            
            if result.data:
                print(f"✅ Updated product {product_id} with new price: {original_currency} {original_price} -> GBP {gbp_price:.2f}")
                return result.data[0]
            else:
                print(f"❌ Failed to update product {product_id}")
                return {}
                
        except Exception as e:
            print(f"❌ Error updating product {product_id}: {e}")
            return {}
    
    def _get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol for a currency code"""
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'Fr', 'CNY': '¥',
            'INR': '₹', 'KRW': '₩', 'BRL': 'R$', 'RUB': '₽'
        }
        return symbols.get(currency_code, currency_code)

    def _extract_price(self, product: Dict[str, Any]) -> float:
        """Extract price from various possible locations in product data"""
        pricing = product.get('pricing', {})
        return (self._safe_float(pricing.get('unit_price')) or 
                self._safe_float(product.get('price')) or 
                0.0)
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            if value is None or value == 'Unknown' or value == '':
                return default
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def get_products_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get all products for a supplier"""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table(TABLE_PRODUCTS).select("*").eq("supplier_id", supplier_id).execute()
            return result.data
        except Exception as e:
            return []
    
    def search_products(self, query: str, supplier_id: str = None) -> List[Dict[str, Any]]:
        """Search products by name or description"""
        if not self.enabled:
            return []
            
        try:
            query_builder = self.supabase.table(TABLE_PRODUCTS).select("*")
            
            # Add supplier filter if provided
            if supplier_id:
                query_builder = query_builder.eq("supplier_id", supplier_id)
            
            # Search in name and description
            result = query_builder.or_(f"name.ilike.%{query}%,full_description.ilike.%{query}%").execute()
            return result.data
        except Exception as e:
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        if not self.enabled:
            return None
            
        try:
            result = self.supabase.table(TABLE_PRODUCTS).select("*").eq("id", product_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    def _has_conflicting_sizes(self, name1: str, name2: str) -> bool:
        """Check if two product names have conflicting size/volume specifications"""
        import re
        
        # Patterns for volume/size specifications
        size_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(oz|ounce|ounces)\b',  # 8 oz, 12 oz, etc.
            r'\b(\d+(?:\.\d+)?)\s*(ml|milliliter|milliliters)\b',  # 250 ml, etc.
            r'\b(\d+(?:\.\d+)?)\s*(cl|centiliter|centiliters)\b',  # 33 cl, etc.
            r'\b(\d+(?:\.\d+)?)\s*(l|liter|liters|litre|litres)\b',  # 1 l, etc.
            r'\b(\d+(?:\.\d+)?)\s*(inch|inches|in)\b',  # 6 inch, etc.
            r'\b(\d+(?:\.\d+)?)\s*(cm|centimeter|centimeters)\b',  # 15 cm, etc.
            r'\b(\d+(?:\.\d+)?)\s*(mm|millimeter|millimeters)\b',  # 100 mm, etc.
            r'\b(\d+(?:\.\d+)?)\s*["\']',  # 6", 12', etc.
        ]
        
        for pattern in size_patterns:
            # Find all size specs in both names
            sizes1 = re.findall(pattern, name1.lower())
            sizes2 = re.findall(pattern, name2.lower())
            
            if sizes1 and sizes2:
                # Extract numeric values
                values1 = set(float(match[0]) for match in sizes1)
                values2 = set(float(match[0]) for match in sizes2)
                
                # If they have different size values, they're not duplicates
                if values1 != values2:
                    return True
        
        return False

# Global instance
product_manager = ProductManager()

# Legacy function for backward compatibility  
def save_products_prices(supplier_id, products):
    """Legacy function - use product_manager.save_products_comprehensive instead"""
    return product_manager.save_products_comprehensive(supplier_id, products)
