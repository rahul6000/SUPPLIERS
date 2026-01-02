# Supplier management with Supabase integration
import uuid
import sys
import os
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SUPABASE_URL, SUPABASE_KEY, TABLE_SUPPLIERS, DATABASE_ENABLED

class SupplierManager:
    def __init__(self):
        if DATABASE_ENABLED and SUPABASE_URL != "https://YOUR_PROJECT.supabase.co":
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.enabled = True
        else:
            self.supabase = None
            self.enabled = False
    
    def get_or_create_supplier(self, supplier_data: Dict[str, Any]) -> str:
        """Create or get supplier ID with smart duplicate detection using multiple criteria"""
        supplier_name = supplier_data.get('supplier_name', 'Unknown Supplier')
        supplier_info = supplier_data.get('supplier_info', {})
        
        if not self.enabled:
            return f"supplier_{hash(supplier_name) % 1000}"
        
        try:
            # Check for existing supplier using multiple criteria
            existing_supplier_id = self._find_existing_supplier(supplier_name, supplier_info)
            
            if existing_supplier_id:
                print(f"✅ Found existing supplier: {supplier_name} (ID: {existing_supplier_id})")
                # Update supplier info if more complete
                self._update_supplier_info(existing_supplier_id, supplier_data)
                return existing_supplier_id
            
            # Create new supplier
            print(f"➕ Creating new supplier: {supplier_name}")
            supplier_id = str(uuid.uuid4())
            supplier_record = self._build_supplier_record(supplier_id, supplier_data)
            
            result = self.supabase.table(TABLE_SUPPLIERS).insert(supplier_record).execute()
            return supplier_id
            
        except Exception as e:
            print(f"❌ Error in get_or_create_supplier: {e}")
            return f"error_{hash(supplier_name) % 1000}"
    
    def _find_existing_supplier(self, supplier_name: str, supplier_info: Dict[str, Any]) -> Optional[str]:
        """Find existing supplier using multiple matching criteria"""
        try:
            # First check by exact name match
            result = self.supabase.table(TABLE_SUPPLIERS).select("id, name").eq("name", supplier_name).execute()
            if result.data:
                return result.data[0]['id']
            
            # Check by similar name (fuzzy match) - remove common business suffixes
            clean_name = self._clean_company_name(supplier_name)
            if clean_name != supplier_name:
                result = self.supabase.table(TABLE_SUPPLIERS).select("id, name").ilike("name", f"%{clean_name}%").execute()
                if result.data:
                    for supplier in result.data:
                        if self._names_are_similar(supplier_name, supplier['name']):
                            print(f"📝 Found similar supplier: '{supplier_name}' matches '{supplier['name']}'")
                            return supplier['id']
            
            # TODO: Could add email/phone matching here when those fields are added to DB
            # For now, we only match by company name
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding existing supplier: {e}")
            return None
    
    def _clean_company_name(self, name: str) -> str:
        """Clean company name by removing common suffixes for better matching"""
        suffixes = ['ltd', 'limited', 'inc', 'corp', 'corporation', 'llc', 'co', 'company']
        clean_name = name.lower().strip()
        
        for suffix in suffixes:
            if clean_name.endswith(f' {suffix}'):
                clean_name = clean_name[:-len(f' {suffix}')].strip()
            elif clean_name.endswith(f'.{suffix}'):
                clean_name = clean_name[:-len(f'.{suffix}')].strip()
        
        return clean_name
    
    def _names_are_similar(self, name1: str, name2: str) -> bool:
        """Check if two company names are similar enough to be the same company"""
        clean1 = self._clean_company_name(name1)
        clean2 = self._clean_company_name(name2)
        
        # If cleaned names match exactly
        if clean1 == clean2:
            return True
        
        # If one is contained in the other (with reasonable length)
        if len(clean1) > 3 and len(clean2) > 3:
            if clean1 in clean2 or clean2 in clean1:
                return True
        
        return False

    def _build_supplier_record(self, supplier_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build basic supplier record with only fields that exist in DB"""
        return {
            'id': supplier_id,
            'name': data.get('supplier_name', 'Unknown Supplier')
        }
    
    def _update_supplier_info(self, supplier_id: str, data: Dict[str, Any]):
        """Update supplier information - only use columns that exist in DB"""
        try:
            supplier_info = data.get('supplier_info', {})
            update_data = {}
            
            # Only update the name field since other columns don't exist in DB
            supplier_name = supplier_info.get('name')
            if supplier_name and supplier_name != 'Unknown' and supplier_name != 'Manual review required':
                update_data['name'] = supplier_name
            
            if update_data:  # Only update if there's something to update
                self.supabase.table(TABLE_SUPPLIERS).update(update_data).eq('id', supplier_id).execute()
                print(f"📝 Updated supplier info for ID: {supplier_id}")
                
        except Exception as e:
            print(f"❌ Error updating supplier: {e}")
    
    def get_supplier_by_id(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """Get supplier by ID"""
        if not self.enabled:
            return None
            
        try:
            result = self.supabase.table(TABLE_SUPPLIERS).select("*").eq("id", supplier_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    def search_suppliers(self, query: str) -> List[Dict[str, Any]]:
        """Search suppliers by name"""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table(TABLE_SUPPLIERS).select("*").ilike("name", f"%{query}%").execute()
            return result.data
        except Exception as e:
            return []
    
    def get_all_suppliers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all suppliers with limit"""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table(TABLE_SUPPLIERS).select("*").limit(limit).execute()
            return result.data
        except Exception as e:
            return []

# Global instance
supplier_manager = SupplierManager()

# Legacy function for backward compatibility
def get_or_create_supplier(supplier_name):
    """Legacy function - use supplier_manager.get_or_create_supplier instead"""
    supplier_data = {'supplier_name': supplier_name}
    return supplier_manager.get_or_create_supplier(supplier_data)
