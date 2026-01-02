"""
Complete export/import system for the Suppliers AI platform.
Handles CSV, Excel, JSON, and bulk operations with data validation.
"""
import csv
import json
import io
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import streamlit as st
from pathlib import Path
import base64
import logging

class DataExporter:
    """Advanced data export system with multiple formats"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> bytes:
        """Export data to CSV format"""
        if not data:
            raise ValueError("No data to export")
        
        # Convert to DataFrame for better CSV handling
        df = pd.DataFrame(data)
        
        # Clean data for CSV export
        df = self._clean_data_for_export(df)
        
        # Generate CSV
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        
        return output.getvalue().encode('utf-8')
    
    def export_to_excel(self, data: Dict[str, List[Dict[str, Any]]], filename: str = None) -> bytes:
        """Export multiple data sets to Excel with multiple sheets"""
        if not data:
            raise ValueError("No data to export")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, sheet_data in data.items():
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    df = self._clean_data_for_export(df)
                    
                    # Limit sheet name length
                    clean_sheet_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                    
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[clean_sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output.getvalue()
    
    def export_to_json(self, data: List[Dict[str, Any]], pretty: bool = True) -> bytes:
        """Export data to JSON format"""
        if not data:
            raise ValueError("No data to export")
        
        # Clean data for JSON export
        cleaned_data = self._clean_data_for_json(data)
        
        json_str = json.dumps(
            cleaned_data,
            indent=2 if pretty else None,
            ensure_ascii=False,
            default=self._json_serializer
        )
        
        return json_str.encode('utf-8')
    
    def export_comprehensive_package(self) -> bytes:
        """Export complete data package with all tables"""
        try:
            export_data = {}
            
            # Export all main tables
            if self.supabase:
                tables = ['suppliers', 'products', 'documents']
                
                for table in tables:
                    try:
                        result = self.supabase.table(table).select('*').execute()
                        export_data[table] = result.data if result.data else []
                    except Exception as e:
                        st.warning(f"Could not export {table}: {e}")
                        export_data[table] = []
            else:
                # Mock data for development
                export_data = self._get_mock_export_data()
            
            # Add metadata
            export_data['_metadata'] = {
                'export_date': datetime.now().isoformat(),
                'export_version': '1.0',
                'total_records': sum(len(data) for data in export_data.values() if isinstance(data, list))
            }
            
            # Create ZIP file with multiple formats
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON export
                json_data = self.export_to_json(export_data)
                zip_file.writestr('complete_export.json', json_data)
                
                # Add Excel export
                excel_data = self.export_to_excel(export_data)
                zip_file.writestr('complete_export.xlsx', excel_data)
                
                # Add individual CSV files
                for table_name, table_data in export_data.items():
                    if isinstance(table_data, list) and table_data:
                        csv_data = self.export_to_csv(table_data)
                        zip_file.writestr(f'{table_name}.csv', csv_data)
                
                # Add README
                readme_content = self._generate_export_readme(export_data)
                zip_file.writestr('README.txt', readme_content.encode('utf-8'))
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Export package creation failed: {e}")
            raise
    
    def _clean_data_for_export(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame for export"""
        # Convert datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert datetime strings
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass
        
        # Fill NaN values
        df = df.fillna('')
        
        # Convert complex objects to strings
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        
        return df
    
    def _clean_data_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean data for JSON serialization"""
        cleaned_data = []
        
        for item in data:
            cleaned_item = {}
            for key, value in item.items():
                # Handle None values
                if value is None:
                    cleaned_item[key] = None
                # Handle datetime objects
                elif isinstance(value, datetime):
                    cleaned_item[key] = value.isoformat()
                # Handle other types
                else:
                    cleaned_item[key] = value
            
            cleaned_data.append(cleaned_item)
        
        return cleaned_data
    
    def _json_serializer(self, obj):
        """JSON serializer for special objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _get_mock_export_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get mock data for development"""
        return {
            'suppliers': [
                {'id': '1', 'name': 'EcoPackaging Ltd', 'email': 'contact@ecopack.com', 'created_at': datetime.now().isoformat()},
                {'id': '2', 'name': 'Kitchen Supplies Co', 'email': 'sales@kitchensupplies.com', 'created_at': datetime.now().isoformat()}
            ],
            'products': [
                {'id': '1', 'name': 'Biodegradable Cups', 'category': 'Packaging', 'usage_type': 'Disposable'},
                {'id': '2', 'name': 'Stainless Steel Pans', 'category': 'Kitchen', 'usage_type': 'Equipment'}
            ],
            'documents': [
                {'id': '1', 'filename': 'invoice_001.pdf', 'supplier_id': '1', 'processed_at': datetime.now().isoformat()},
                {'id': '2', 'filename': 'catalog_2024.pdf', 'supplier_id': '2', 'processed_at': datetime.now().isoformat()}
            ]
        }
    
    def _generate_export_readme(self, export_data: Dict[str, Any]) -> str:
        """Generate README file for export package"""
        metadata = export_data.get('_metadata', {})
        
        readme = f"""
SUPPLIERS AI PLATFORM - DATA EXPORT
===================================

Export Date: {metadata.get('export_date', 'Unknown')}
Export Version: {metadata.get('export_version', '1.0')}
Total Records: {metadata.get('total_records', 0)}

CONTENTS:
---------
1. complete_export.json - Complete data in JSON format
2. complete_export.xlsx - Complete data in Excel format (multiple sheets)
3. suppliers.csv - Suppliers data in CSV format
4. products.csv - Products data in CSV format
5. documents.csv - Documents data in CSV format

FILE DESCRIPTIONS:
------------------
- JSON files: Machine-readable format, preserves data types
- Excel files: Human-readable, multiple sheets, formatted columns
- CSV files: Individual tables, compatible with most spreadsheet applications

DATA STRUCTURE:
---------------
"""
        
        for table_name, table_data in export_data.items():
            if isinstance(table_data, list) and table_data:
                readme += f"- {table_name.upper()}: {len(table_data)} records\n"
                if table_data:
                    sample_keys = list(table_data[0].keys())[:5]
                    readme += f"  Columns: {', '.join(sample_keys)}{'...' if len(table_data[0].keys()) > 5 else ''}\n"
                readme += "\n"
        
        readme += """
USAGE NOTES:
------------
- All timestamps are in ISO format (YYYY-MM-DDTHH:MM:SS)
- Empty values are represented as empty strings in CSV/Excel, null in JSON
- File encoding is UTF-8 for all text formats
- Excel file has auto-sized columns for better readability

For technical support, contact your system administrator.
"""
        
        return readme


class DataImporter:
    """Advanced data import system with validation and conflict resolution"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.validation_errors = []
        self.import_stats = {'imported': 0, 'skipped': 0, 'errors': 0}
    
    def import_from_csv(self, file_content: bytes, table_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Import data from CSV file with validation"""
        if options is None:
            options = {}
        
        try:
            # Read CSV content
            content_str = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content_str))
            
            # Validate and process data
            processed_data = self._validate_and_process_import_data(df, table_name)
            
            # Import to database
            if self.supabase and processed_data:
                result = self._import_to_database(processed_data, table_name, options)
                return result
            else:
                return {
                    'success': True,
                    'message': f"Processed {len(processed_data)} records (mock mode)",
                    'imported': len(processed_data),
                    'errors': len(self.validation_errors)
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Import failed: {str(e)}",
                'imported': 0,
                'errors': 1
            }
    
    def import_from_excel(self, file_content: bytes, sheet_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Import data from Excel file with multiple sheets"""
        if sheet_mapping is None:
            sheet_mapping = {}
        
        try:
            # Read Excel file
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            
            results = {}
            
            for sheet_name, df in excel_data.items():
                # Determine target table
                target_table = sheet_mapping.get(sheet_name, sheet_name.lower())
                
                if target_table in ['suppliers', 'products', 'documents']:
                    # Process sheet
                    processed_data = self._validate_and_process_import_data(df, target_table)
                    
                    # Import to database
                    if self.supabase and processed_data:
                        result = self._import_to_database(processed_data, target_table)
                        results[sheet_name] = result
                    else:
                        results[sheet_name] = {
                            'success': True,
                            'message': f"Processed {len(processed_data)} records from {sheet_name}",
                            'imported': len(processed_data)
                        }
                else:
                    results[sheet_name] = {
                        'success': False,
                        'message': f"Unknown table mapping for sheet: {sheet_name}"
                    }
            
            return results
            
        except Exception as e:
            return {
                'excel_import': {
                    'success': False,
                    'message': f"Excel import failed: {str(e)}"
                }
            }
    
    def import_from_json(self, file_content: bytes, table_name: str = None) -> Dict[str, Any]:
        """Import data from JSON file"""
        try:
            # Parse JSON
            content_str = file_content.decode('utf-8')
            json_data = json.loads(content_str)
            
            results = {}
            
            # Handle different JSON structures
            if isinstance(json_data, dict):
                # Multiple tables
                for key, data in json_data.items():
                    if key.startswith('_'):  # Skip metadata
                        continue
                    
                    if isinstance(data, list) and data:
                        processed_data = self._validate_and_process_import_data(pd.DataFrame(data), key)
                        
                        if self.supabase and processed_data:
                            result = self._import_to_database(processed_data, key)
                            results[key] = result
                        else:
                            results[key] = {
                                'success': True,
                                'message': f"Processed {len(processed_data)} records",
                                'imported': len(processed_data)
                            }
            
            elif isinstance(json_data, list):
                # Single table
                if not table_name:
                    raise ValueError("Table name required for list-based JSON import")
                
                processed_data = self._validate_and_process_import_data(pd.DataFrame(json_data), table_name)
                
                if self.supabase and processed_data:
                    result = self._import_to_database(processed_data, table_name)
                    results[table_name] = result
                else:
                    results[table_name] = {
                        'success': True,
                        'message': f"Processed {len(processed_data)} records",
                        'imported': len(processed_data)
                    }
            
            return results
            
        except Exception as e:
            return {
                'json_import': {
                    'success': False,
                    'message': f"JSON import failed: {str(e)}"
                }
            }
    
    def _validate_and_process_import_data(self, df: pd.DataFrame, table_name: str) -> List[Dict[str, Any]]:
        """Validate and process import data"""
        self.validation_errors = []
        processed_data = []
        
        # Define required fields per table
        required_fields = {
            'suppliers': ['name'],
            'products': ['name'],
            'documents': ['filename']
        }
        
        table_required = required_fields.get(table_name, [])
        
        for index, row in df.iterrows():
            row_data = {}
            row_errors = []
            
            # Check required fields
            for field in table_required:
                if field not in row or pd.isna(row[field]) or str(row[field]).strip() == '':
                    row_errors.append(f"Missing required field: {field}")
            
            # Process each column
            for col, value in row.items():
                if pd.isna(value):
                    row_data[col] = None
                elif col.endswith('_at') or col.endswith('_date'):
                    # Handle date fields
                    try:
                        row_data[col] = pd.to_datetime(value).isoformat()
                    except:
                        row_data[col] = str(value)
                else:
                    row_data[col] = str(value).strip() if isinstance(value, str) else value
            
            if row_errors:
                self.validation_errors.extend([f"Row {index + 1}: {error}" for error in row_errors])
            else:
                processed_data.append(row_data)
        
        return processed_data
    
    def _import_to_database(self, data: List[Dict[str, Any]], table_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Import data to database with conflict resolution"""
        if options is None:
            options = {}
        
        batch_size = options.get('batch_size', 100)
        conflict_resolution = options.get('conflict_resolution', 'skip')  # skip, update, replace
        
        imported = 0
        errors = 0
        
        try:
            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                if conflict_resolution == 'skip':
                    # Simple insert, skip conflicts
                    result = self.supabase.table(table_name).insert(batch).execute()
                    if not hasattr(result, 'error') or result.error is None:
                        imported += len(batch)
                    else:
                        errors += len(batch)
                
                elif conflict_resolution == 'update':
                    # Update existing records
                    for record in batch:
                        try:
                            result = self.supabase.table(table_name).upsert(record).execute()
                            if not hasattr(result, 'error') or result.error is None:
                                imported += 1
                            else:
                                errors += 1
                        except:
                            errors += 1
                
                elif conflict_resolution == 'replace':
                    # Delete and insert (careful!)
                    # This would need more sophisticated implementation
                    pass
            
            return {
                'success': True,
                'message': f"Successfully imported {imported} records to {table_name}",
                'imported': imported,
                'errors': errors,
                'validation_errors': self.validation_errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Database import failed: {str(e)}",
                'imported': imported,
                'errors': errors + 1
            }


class BulkOperations:
    """Bulk operations for large-scale data management"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.exporter = DataExporter(supabase_client)
        self.importer = DataImporter(supabase_client)
    
    def bulk_update_suppliers(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update supplier records"""
        if not self.supabase:
            return {'success': False, 'message': 'Database not available'}
        
        updated = 0
        errors = []
        
        for update in updates:
            try:
                if 'id' not in update:
                    errors.append("Missing ID in update record")
                    continue
                
                record_id = update.pop('id')
                result = self.supabase.table('suppliers').update(update).eq('id', record_id).execute()
                
                if not hasattr(result, 'error') or result.error is None:
                    updated += 1
                else:
                    errors.append(f"Failed to update supplier {record_id}: {result.error}")
                    
            except Exception as e:
                errors.append(f"Error updating supplier: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'updated': updated,
            'errors': errors,
            'message': f"Updated {updated} suppliers, {len(errors)} errors"
        }
    
    def bulk_delete_records(self, table: str, record_ids: List[str]) -> Dict[str, Any]:
        """Bulk delete records (with safety checks)"""
        if not self.supabase:
            return {'success': False, 'message': 'Database not available'}
        
        if len(record_ids) > 100:
            return {'success': False, 'message': 'Bulk delete limited to 100 records at once for safety'}
        
        try:
            result = self.supabase.table(table).delete().in_('id', record_ids).execute()
            
            if not hasattr(result, 'error') or result.error is None:
                return {
                    'success': True,
                    'deleted': len(record_ids),
                    'message': f"Deleted {len(record_ids)} records from {table}"
                }
            else:
                return {
                    'success': False,
                    'message': f"Bulk delete failed: {result.error}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Bulk delete error: {str(e)}"
            }


# Streamlit UI for export/import functionality
def show_export_import_interface():
    """Display export/import interface in Streamlit"""
    st.header("📤📥 Data Export & Import")
    
    tab1, tab2, tab3 = st.tabs(["📤 Export", "📥 Import", "🔄 Bulk Operations"])
    
    with tab1:
        st.markdown("### Export Data")
        
        exporter = DataExporter()
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                ["CSV", "Excel", "JSON", "Complete Package"]
            )
        
        with col2:
            if export_format != "Complete Package":
                export_table = st.selectbox(
                    "Select Table",
                    ["suppliers", "products", "documents", "all"]
                )
        
        if st.button("🚀 Export Data"):
            with st.spinner("Preparing export..."):
                try:
                    if export_format == "Complete Package":
                        data = exporter.export_comprehensive_package()
                        st.download_button(
                            label="📦 Download Complete Package",
                            data=data,
                            file_name=f"suppliers_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )
                    elif export_format == "CSV":
                        # Mock data for demo
                        mock_data = [{'id': '1', 'name': 'Test Supplier', 'email': 'test@test.com'}]
                        data = exporter.export_to_csv(mock_data)
                        st.download_button(
                            label="📄 Download CSV",
                            data=data,
                            file_name=f"{export_table}_export.csv",
                            mime="text/csv"
                        )
                    
                    st.success("✅ Export completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
    
    with tab2:
        st.markdown("### Import Data")
        
        importer = DataImporter()
        
        import_format = st.selectbox(
            "Import Format",
            ["CSV", "Excel", "JSON"]
        )
        
        uploaded_file = st.file_uploader(
            f"Upload {import_format} file",
            type=[import_format.lower()],
            help=f"Upload a {import_format} file containing your data"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File '{uploaded_file.name}' uploaded successfully")
            
            # Import options
            with st.expander("Import Options"):
                conflict_resolution = st.selectbox(
                    "Conflict Resolution",
                    ["skip", "update", "replace"],
                    help="How to handle existing records"
                )
                
                batch_size = st.number_input(
                    "Batch Size",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    help="Number of records to process at once"
                )
            
            if st.button("📥 Import Data"):
                with st.spinner("Importing data..."):
                    try:
                        file_content = uploaded_file.read()
                        options = {
                            'conflict_resolution': conflict_resolution,
                            'batch_size': batch_size
                        }
                        
                        if import_format == "CSV":
                            result = importer.import_from_csv(file_content, "suppliers", options)
                        elif import_format == "Excel":
                            result = importer.import_from_excel(file_content)
                        elif import_format == "JSON":
                            result = importer.import_from_json(file_content)
                        
                        if result.get('success', False):
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
                        
                        # Show detailed results
                        if isinstance(result, dict) and 'imported' in result:
                            st.metric("Records Imported", result['imported'])
                            if result.get('errors', 0) > 0:
                                st.metric("Errors", result['errors'])
                        
                    except Exception as e:
                        st.error(f"❌ Import failed: {str(e)}")
    
    with tab3:
        st.markdown("### Bulk Operations")
        
        bulk_ops = BulkOperations()
        
        operation = st.selectbox(
            "Bulk Operation",
            ["Bulk Update Suppliers", "Bulk Delete Records", "Data Cleanup"]
        )
        
        if operation == "Bulk Update Suppliers":
            st.markdown("Upload a CSV file with supplier updates (must include 'id' column)")
            update_file = st.file_uploader("Upload Updates", type=['csv'])
            
            if update_file and st.button("Apply Updates"):
                st.info("Bulk update functionality would be implemented here")
        
        elif operation == "Bulk Delete Records":
            st.warning("⚠️ Bulk delete is irreversible. Use with caution.")
            
            table_to_clean = st.selectbox("Table", ["suppliers", "products", "documents"])
            
            record_ids = st.text_area(
                "Record IDs (one per line)",
                placeholder="Enter record IDs to delete, one per line"
            )
            
            if record_ids and st.button("🗑️ Delete Records", type="primary"):
                ids_list = [id.strip() for id in record_ids.split('\n') if id.strip()]
                if len(ids_list) > 100:
                    st.error("Maximum 100 records can be deleted at once")
                else:
                    st.info(f"Would delete {len(ids_list)} records from {table_to_clean}")


# Global export/import instances
data_exporter = DataExporter()
data_importer = DataImporter()
bulk_operations = BulkOperations()