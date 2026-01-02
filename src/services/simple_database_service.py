# Updated database service that works with your existing tables
import os
from typing import Dict, Any
from supabase import create_client
from datetime import datetime
import uuid

class SimpleSupplierManager:
    """Simplified supplier manager for existing table structure: id, name, contact_email, notes, created_at"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
    
    def get_or_create_supplier(self, extraction_data: Dict[str, Any]) -> str:
        """Get existing supplier or create new one"""
        supplier_name = extraction_data.get('supplier_name', 'Unknown Supplier')
        supplier_info = extraction_data.get('supplier_info', {})
        supplier_email = supplier_info.get('email', '')
        
        try:
            # Check if supplier exists by name first
            existing = self.supabase.table('suppliers').select("id, name, contact_email").eq("name", supplier_name).execute()
            
            if existing.data:
                supplier_id = existing.data[0]['id']
                return supplier_id
            
            # Check by email if provided
            if supplier_email and supplier_email.strip():
                existing = self.supabase.table('suppliers').select("id, name, contact_email").eq("contact_email", supplier_email).execute()
                if existing.data:
                    supplier_id = existing.data[0]['id']
                    return supplier_id
            
            # Create new supplier
            supplier_record = {
                'name': supplier_name,
                'contact_email': supplier_info.get('email'),
                'notes': f"Address: {supplier_info.get('address', 'Unknown')}\\nPhone: {supplier_info.get('phone', 'Unknown')}\\nVAT: {supplier_info.get('vat_number', 'Unknown')}"
            }
            
            result = self.supabase.table('suppliers').insert(supplier_record).execute()
            supplier_id = result.data[0]['id']
            return supplier_id
            
        except Exception as e:
            return f"supplier_error_{hash(supplier_name) % 1000}"

class SimpleDocumentManager:
    """Simplified document manager for existing table structure: id, supplier_id, file_name, upload_date, parsed, raw_text"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
    
    def save_document_record(self, supplier_id: str, pdf_path: str, extraction_data: Dict[str, Any]) -> str:
        """Save document record to your existing documents table"""
        try:
            # Check if document already exists for this supplier
            filename = os.path.basename(pdf_path)
            existing = self.supabase.table('documents').select("id").eq("supplier_id", supplier_id).eq("file_name", filename).execute()
            
            if existing.data:
                doc_id = existing.data[0]['id']
                return doc_id
            
            document_record = {
                'supplier_id': supplier_id,
                'file_name': filename,
                'upload_date': datetime.now().isoformat(),
                'parsed': True,
                'raw_text': str(extraction_data)[:2000]  # Truncate for storage
            }
            
            result = self.supabase.table('documents').insert(document_record).execute()
            doc_id = result.data[0]['id']
            return doc_id
            
        except Exception as e:
            return f"doc_error_{hash(pdf_path) % 1000}"

class SimpleProductManager:
    """Simplified product manager for existing table structure: id, category, product_name, size, material, usage_type, created_at"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
    
    def find_existing_product(self, product_name: str, size: str = None, material: str = None) -> dict:
        """Find existing product with exact matching to prevent duplicates"""
        try:
            # Clean the product name
            clean_name = product_name.strip()
            
            # Try exact match first (case-insensitive)
            products = self.supabase.table('products').select("*").ilike('product_name', clean_name).execute()
            
            if products.data:
                # If we have size/material criteria, try to find best match
                if size or material:
                    for product in products.data:
                        existing_size = (product.get('size', '') or '').lower()
                        existing_material = (product.get('material', '') or '').lower()
                        
                        # Only match if size and material are very similar
                        size_match = not size or existing_size == size.lower() or 'unknown' in existing_size
                        material_match = not material or existing_material == material.lower() or 'unknown' in existing_material
                        
                        if size_match and material_match:
                            return product
                
                # Return first exact name match
                return products.data[0]
            
            return None
        except Exception as e:
            return None
    
    def get_product_with_pricing(self, product_name: str) -> list:
        """Get products with complete price history from database"""
        try:
            # Search for products 
            products = self.supabase.table('products').select("*").ilike('product_name', f'%{product_name}%').execute()
            
            results = []
            for product in products.data:
                # Debug: Let's see what's in the database
                
                # Parse price history from usage_type field
                price_history = []
                usage_type_data = product.get('usage_type', '')
                
                if '£' in str(usage_type_data) and '|' in str(usage_type_data):
                    # Parse price history entries: "£26.00|2025-12-22T12:30:00|supplier_id;£28.00|2025-12-23T10:15:00|supplier_id2"
                    entries = str(usage_type_data).split(';')
                    for entry in entries:
                        if '|' in entry and '£' in entry:
                            try:
                                parts = entry.split('|')
                                if len(parts) >= 3:
                                    price_str = parts[0].replace('£', '')
                                    price = float(price_str)
                                    timestamp = parts[1]
                                    supplier_id = parts[2]
                                    
                                    # Get supplier name
                                    supplier_name = 'Unknown Supplier'
                                    try:
                                        supplier_result = self.supabase.table('suppliers').select('name').eq('id', supplier_id).execute()
                                        if supplier_result.data:
                                            supplier_name = supplier_result.data[0]['name']
                                    except:
                                        pass
                                    
                                    price_history.append({
                                        'price': price,
                                        'date': timestamp,
                                        'supplier_id': supplier_id,
                                        'supplier_name': supplier_name
                                    })
                            except Exception as parse_error:
                                continue
                else:
                    # No price history found, return empty list
                    pass
                
                # Sort by date (newest first)
                price_history.sort(key=lambda x: x['date'], reverse=True)
                
                # Add price history to product
                product['price_history'] = price_history
                product['current_price'] = price_history[0]['price'] if price_history else 0
                product['supplier_name'] = price_history[0]['supplier_name'] if price_history else 'Unknown'
                product['last_updated'] = price_history[0]['date'] if price_history else product.get('created_at', '')
                
                results.append(product)
            
            return results
            
        except Exception as e:
            # Fallback to basic search
            return self.supabase.table('products').select("*").ilike('product_name', f'%{product_name}%').execute().data or []
    
    def save_products_comprehensive(self, supplier_id: str, products_data: list, document_filename: str = None) -> list:
        """Smart product saving with duplicate checking, comprehensive price history tracking, and document source tracking"""
        
        saved_products = []
        new_products = 0
        existing_products = 0
        price_updates = 0
        
        try:
            for product in products_data:
                # Handle both string and dict product data
                if isinstance(product, str):
                    product_name = product
                    product_details = {
                        'category': 'General',
                        'size': 'Unknown',
                        'material': 'Unknown',
                        'usage_type': 'General',
                        'price': 0,
                        'unit_price': 0
                    }
                elif isinstance(product, dict):
                    product_name = product.get('name', 'Unknown Product')
                    product_details = {
                        'category': product.get('category', 'General'),
                        'size': product.get('size', 'Unknown'),
                        'material': product.get('material', 'Unknown'), 
                        'usage_type': product.get('usage_type', 'General'),
                        'price': product.get('price', 0),
                        'unit_price': product.get('unit_price', 0),
                        'quantity': product.get('quantity', 1),
                        'specifications': product.get('specifications', '')
                    }
                else:
                    continue  # Skip invalid product data
                
                # Extract pricing info
                unit_price = product_details.get('unit_price', 0) or product_details.get('price', 0)
                quantity = product_details.get('quantity', 1)
                specs = product_details.get('specifications', '')
                
                # Check if product already exists
                existing_product = self.find_existing_product(
                    product_name, 
                    product_details.get('size'),
                    product_details.get('material')
                )
                
                if existing_product:
                    # Product exists - add price history entry
                    existing_products += 1
                    
                    # Store price history in the usage_type field
                    current_timestamp = datetime.now().isoformat()
                    price_entry = f"£{unit_price:.2f}|{current_timestamp}|{supplier_id}"
                    
                    # Get existing usage_type and preserve document source
                    current_usage_type = existing_product.get('usage_type', '')
                    
                    # Extract existing document source if present
                    existing_doc_source = ''
                    if '|DOC:' in current_usage_type:
                        existing_doc_source = '|DOC:' + current_usage_type.split('|DOC:')[-1]
                    elif document_filename:
                        existing_doc_source = f"|DOC:{document_filename}"
                    
                    # If usage_type already contains price history, append; otherwise start new
                    if '£' in str(current_usage_type) and '|' in str(current_usage_type):
                        # Get base price history without document source
                        base_history = current_usage_type.split('|DOC:')[0] if '|DOC:' in current_usage_type else current_usage_type
                        # Append new entry and preserve document source
                        updated_notes = f"{base_history};{price_entry}{existing_doc_source}"
                    else:
                        # First price entry
                        updated_notes = f"{price_entry}{existing_doc_source}"
                    
                    # Update the product with new price history
                    try:
                        self.supabase.table('products').update({
                            'usage_type': updated_notes[:500]  # Limit to avoid field size issues
                        }).eq('id', existing_product['id']).execute()
                    except:
                        pass  # Continue even if update fails
                    
                    # Add to response with current pricing
                    existing_product['current_price'] = unit_price
                    existing_product['price_updated'] = current_timestamp
                    existing_product['specifications'] = specs
                    existing_product['supplier_id'] = supplier_id
                    
                    saved_products.append(existing_product)
                    price_updates += 1
                    
                else:
                    # Product doesn't exist - create new with initial price
                    current_timestamp = datetime.now().isoformat()
                    price_entry = f"£{unit_price:.2f}|{current_timestamp}|{supplier_id}"
                    
                    # Store document source with price history in usage_type field
                    document_source = document_filename if document_filename else 'Unknown Document'
                    price_entry_with_doc = f"{price_entry}|DOC:{document_source}"
                    
                    product_record = {
                        'category': product_details['category'],
                        'product_name': product_name,
                        'size': product_details['size'],
                        'material': product_details['material'],
                        'usage_type': price_entry_with_doc,  # Store price history and document source
                        'unit_price': unit_price,
                        'currency': product.get('currency', 'GBP'),
                        'original_price': product.get('original_price'),
                        'original_currency': product.get('original_currency'),
                        'original_currency_symbol': product.get('original_currency_symbol'),
                        'conversion_rate': product.get('conversion_rate', 1.0)
                    }
                    
                    # Save to database
                    result = self.supabase.table('products').insert(product_record).execute()
                    
                    if result.data:
                        new_product = result.data[0]
                        # Add pricing info for tracking
                        new_product['current_price'] = unit_price
                        new_product['specifications'] = specs
                        new_product['supplier_id'] = supplier_id
                        new_product['created_in_session'] = True
                        
                        saved_products.append(new_product)
                        new_products += 1
        
        except Exception as e:
            print(f"Error saving products: {str(e)}")
        
        return saved_products

class SimpleDatabaseService:
    """Simplified database service for your existing table structure"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supplier_manager = SimpleSupplierManager(supabase_url, supabase_key)
        self.document_manager = SimpleDocumentManager(supabase_url, supabase_key)
        self.product_manager = SimpleProductManager(supabase_url, supabase_key)
    
    def get_product_with_pricing(self, product_name: str) -> list:
        """Wrapper method for product manager"""
        return self.product_manager.get_product_with_pricing(product_name)
    
    def search_suppliers(self, search_term: str) -> list:
        """Search suppliers by name"""
        try:
            return self.supplier_manager.supabase.table('suppliers').select("*").ilike('name', f'%{search_term}%').execute().data or []
        except:
            return []
    
    def find_product_document_source(self, product_name: str) -> str:
        """Find which document a product came from"""
        try:
            result = self.product_manager.supabase.table('products').select("usage_type, product_name").ilike('product_name', f'%{product_name}%').execute()
            if result.data:
                product = result.data[0]
                usage_type = product.get('usage_type', '')
                
                # Extract document source from usage_type field (format: price|timestamp|supplier|DOC:filename)
                document_source = 'Unknown Document'
                if '|DOC:' in usage_type:
                    doc_part = usage_type.split('|DOC:')[-1]
                    document_source = doc_part if doc_part else 'Unknown Document'
                
                return f"Product '{product['product_name']}' came from document: {document_source}"
            else:
                return f"Product '{product_name}' not found in database"
        except Exception as e:
            return f"Error searching for product: {str(e)}"
    
    def save_complete_extraction(self, pdf_path: str, extraction_data: Dict[str, Any]) -> Dict[str, str]:
        """Save complete extraction data using your existing table structure"""
        try:
            # 1. Get or create supplier
            supplier_id = self.supplier_manager.get_or_create_supplier(extraction_data)
            
            # 2. Save document record
            document_id = self.document_manager.save_document_record(
                supplier_id, pdf_path, extraction_data
            )
            
            # 3. Save products with smart duplicate handling and document tracking
            products = extraction_data.get('products', [])
            document_filename = pdf_path.split('/')[-1] if pdf_path else 'Unknown Document'
            saved_products = self.product_manager.save_products_comprehensive(supplier_id, products, document_filename)
            
            return {
                'status': 'success',
                'supplier_id': supplier_id,
                'document_id': document_id,
                'saved_products': len(saved_products),
                'message': f'Smart save: {len(saved_products)} products processed with duplicate detection'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to save to existing tables'
            }