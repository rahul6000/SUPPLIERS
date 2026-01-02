# Database service layer - orchestrates all database operations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import sys
import os

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.supplier_manager import supplier_manager
from models.product_manager import product_manager  
from models.documents_manager import document_manager
from config import DATABASE_ENABLED

class DatabaseService:
    """Orchestrates all database operations for the AI Supplier Agent"""
    
    def __init__(self):
        self.supplier_manager = supplier_manager
        self.product_manager = product_manager
        self.document_manager = document_manager
        self.enabled = DATABASE_ENABLED
    
    def save_complete_extraction(self, pdf_path: str, extraction_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Save complete extraction data - supplier, products, and document record
        Returns IDs for tracking: {'supplier_id': '...', 'document_id': '...', 'status': 'success/error'}
        """
        try:
            # 1. Save/get supplier
            supplier_id = self.supplier_manager.get_or_create_supplier(extraction_data)
            
            # Ensure supplier_id is valid before proceeding
            if not supplier_id or not isinstance(supplier_id, str):
                supplier_id = "error_fallback"
            
            # 2. Save document record
            document_id = self.document_manager.save_document_record(
                supplier_id, pdf_path, extraction_data
            )
            
            # 3. Save products with supplier name for tracking
            products = extraction_data.get('products', [])
            if products and isinstance(products, list):
                # Add supplier name to each product for tracking
                supplier_name = extraction_data.get('supplier_name', 'Unknown')
                for product in products:
                    if isinstance(product, dict):
                        product['supplier_name'] = supplier_name
                
                success = self.product_manager.save_products_comprehensive(
                    supplier_id, products, document_id
                )
                if not success:
                    return {
                        'supplier_id': supplier_id,
                        'document_id': document_id,
                        'status': 'error',
                        'message': 'Failed to save products',
                        'timestamp': datetime.now().isoformat()
                    }
            
            
            return {
                'supplier_id': supplier_id,
                'document_id': document_id,
                'status': 'success',
                'products_count': len(products) if isinstance(products, list) else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'supplier_id': None,
                'document_id': None,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_supplier_summary(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive supplier summary with stats"""
        if not self.enabled:
            return None
            
        try:
            # Get supplier info
            supplier = self.supplier_manager.get_supplier_by_id(supplier_id)
            if not supplier:
                return None
            
            # Get related data
            documents = self.document_manager.get_documents_by_supplier(supplier_id)
            products = self.product_manager.get_products_by_supplier(supplier_id)
            
            # Calculate stats
            total_value = sum(doc.get('total_amount', 0) for doc in documents)
            unique_products = len(set(p.get('name') for p in products))
            
            return {
                'supplier': supplier,
                'stats': {
                    'total_documents': len(documents),
                    'total_products': len(products),
                    'unique_products': unique_products,
                    'total_value': total_value,
                    'currency': documents[0].get('currency', 'GBP') if documents else 'GBP',
                    'last_processed': max((doc.get('processed_at') for doc in documents), default=None)
                },
                'recent_documents': documents[:5],  # Last 5 documents
                'top_products': sorted(products, key=lambda p: p.get('unit_price', 0), reverse=True)[:10]
            }
            
        except Exception as e:
            return None
    
    def search_everything(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search across suppliers, products, and documents"""
        if not self.enabled:
            return {'suppliers': [], 'products': [], 'documents': []}
            
        try:
            suppliers = self.supplier_manager.search_suppliers(query)
            products = self.product_manager.search_products(query)
            # Note: Add document search when needed
            
            return {
                'suppliers': suppliers,
                'products': products,
                'documents': [],  # Placeholder
                'query': query,
                'total_results': len(suppliers) + len(products)
            }
            
        except Exception as e:
            return {'suppliers': [], 'products': [], 'documents': []}
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Database not configured'
            }
            
        try:
            # Get recent data for stats
            suppliers = self.supplier_manager.get_all_suppliers(limit=1000)
            recent_docs = self.document_manager.get_recent_documents(limit=1000)
            
            # Calculate stats
            total_suppliers = len(suppliers)
            total_documents = len(recent_docs)
            total_value = sum(doc.get('total_amount', 0) for doc in recent_docs)
            
            # Recent activity (last 7 days)
            from datetime import timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_activity = [doc for doc in recent_docs if doc.get('processed_at', '') > week_ago]
            
            return {
                'enabled': True,
                'totals': {
                    'suppliers': total_suppliers,
                    'documents': total_documents,
                    'total_value': total_value,
                    'currency': 'GBP'
                },
                'recent': {
                    'documents_this_week': len(recent_activity),
                    'latest_supplier': suppliers[0].get('name') if suppliers else None,
                    'latest_document': recent_docs[0].get('filename') if recent_docs else None
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'enabled': True,
                'error': str(e)
            }
    
    def approve_document(self, document_id: str, notes: str = None) -> bool:
        """Mark document as approved"""
        try:
            self.document_manager.update_document_status(document_id, 'approved', notes)
            return True
        except Exception as e:
            return False
    
    def reject_document(self, document_id: str, reason: str = None) -> bool:
        """Mark document as rejected"""
        try:
            self.document_manager.update_document_status(document_id, 'rejected', reason)
            return True
        except Exception as e:
            return False
    
    def export_supplier_data(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """Export all data for a supplier"""
        try:
            summary = self.get_supplier_summary(supplier_id)
            if not summary:
                return None
            
            # Get all products and documents
            all_products = self.product_manager.get_products_by_supplier(supplier_id)
            all_documents = self.document_manager.get_documents_by_supplier(supplier_id)
            
            return {
                'export_timestamp': datetime.now().isoformat(),
                'supplier': summary['supplier'],
                'statistics': summary['stats'],
                'products': all_products,
                'documents': all_documents
            }
            
        except Exception as e:
            return None

# Global service instance
database_service = DatabaseService()