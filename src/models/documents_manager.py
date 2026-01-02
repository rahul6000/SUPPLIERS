# Document management with Supabase integration
import uuid
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client, Client

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SUPABASE_URL, SUPABASE_KEY, TABLE_DOCUMENTS, TABLE_EXTRACTIONS, DATABASE_ENABLED

class DocumentManager:
    def __init__(self):
        if DATABASE_ENABLED and SUPABASE_URL != "https://YOUR_PROJECT.supabase.co":
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.enabled = True
        else:
            self.supabase = None
            self.enabled = False
    
    def save_document_record(self, supplier_id: str, pdf_path: str, extraction_data: Dict[str, Any]) -> str:
        """Save comprehensive document processing record"""
        filename = os.path.basename(pdf_path)
        
        if not self.enabled:
            return f"doc_{hash(filename) % 1000}"
        
        try:
            document_id = str(uuid.uuid4())
            
            # Save document record
            document_record = {
                'id': document_id,
                'supplier_id': supplier_id,
                'filename': filename,
                'file_path': pdf_path,
                'file_size': self._get_file_size(pdf_path),
                'document_type': extraction_data.get('document_info', {}).get('document_type') or extraction_data.get('document_type'),
                'document_number': extraction_data.get('document_info', {}).get('document_number') or extraction_data.get('document_number'),
                'issue_date': extraction_data.get('document_info', {}).get('issue_date'),
                'due_date': extraction_data.get('document_info', {}).get('due_date'),
                'order_number': extraction_data.get('document_info', {}).get('order_number'),
                'total_amount': extraction_data.get('totals', {}).get('total_amount') or extraction_data.get('total_amount', 0),
                'currency': extraction_data.get('totals', {}).get('currency') or 'GBP',
                'processed_at': datetime.now().isoformat(),
                'status': 'processed',
                'active': True
            }
            
            result = self.supabase.table(TABLE_DOCUMENTS).insert(document_record).execute()
            
            # Save extraction data
            extraction_id = self._save_extraction_data(document_id, extraction_data)
            
            return document_id
            
        except Exception as e:
            return f"error_{hash(filename) % 1000}"
    
    def _save_extraction_data(self, document_id: str, extraction_data: Dict[str, Any]) -> str:
        """Save raw extraction data for audit/review purposes"""
        try:
            extraction_id = str(uuid.uuid4())
            
            extraction_record = {
                'id': extraction_id,
                'document_id': document_id,
                'extraction_data': extraction_data,  # Store full JSON
                'extraction_method': 'openai_gpt4o',
                'text_length': len(extraction_data.get('original_text', '')),
                'products_count': len(extraction_data.get('products', [])),
                'created_at': datetime.now().isoformat(),
                'confidence_score': self._calculate_confidence(extraction_data)
            }
            
            result = self.supabase.table(TABLE_EXTRACTIONS).insert(extraction_record).execute()
            return extraction_id
            
        except Exception as e:
            return ""
    
    def _get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return None
    
    def _calculate_confidence(self, extraction_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        score = 0.0
        max_score = 100.0
        
        # Supplier info completeness (30 points)
        supplier_info = extraction_data.get('supplier_info', {})
        supplier_fields = ['name', 'address', 'phone', 'email', 'vat_number']
        for field in supplier_fields:
            if supplier_info.get(field) and supplier_info[field] != 'Unknown':
                score += 6
        
        # Product completeness (50 points)
        products = extraction_data.get('products', [])
        if products:
            product_score = 0
            for product in products:
                if product.get('name') and product['name'] != 'Unknown Product':
                    product_score += 10
                if product.get('price') or product.get('pricing', {}).get('unit_price'):
                    product_score += 10
            score += min(50, product_score)
        
        # Document metadata (20 points)
        if extraction_data.get('document_type') != 'Unknown':
            score += 10
        if extraction_data.get('total_amount', 0) > 0:
            score += 10
        
        return round(min(score, max_score), 2)
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if not self.enabled:
            return None
            
        try:
            result = self.supabase.table(TABLE_DOCUMENTS).select("*").eq("id", document_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    def get_documents_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a supplier"""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table(TABLE_DOCUMENTS).select("*").eq("supplier_id", supplier_id).order("processed_at", desc=True).execute()
            return result.data
        except Exception as e:
            return []
    
    def get_recent_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent documents"""
        if not self.enabled:
            return []
            
        try:
            result = self.supabase.table(TABLE_DOCUMENTS).select("*").order("processed_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            return []
    
    def update_document_status(self, document_id: str, status: str, notes: str = None):
        """Update document processing status"""
        if not self.enabled:
            return
            
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            if notes:
                update_data['notes'] = notes
                
            self.supabase.table(TABLE_DOCUMENTS).update(update_data).eq('id', document_id).execute()
            print(f"📝 Updated document {document_id} status to: {status}")
        except Exception as e:
            print(f"❌ Error updating document status: {e}")

# Global instance
document_manager = DocumentManager()

# Legacy function for backward compatibility
def save_pdf_record(supplier_id, pdf_path):
    """Legacy function - use document_manager.save_document_record instead"""
    return document_manager.save_document_record(supplier_id, pdf_path, {})
