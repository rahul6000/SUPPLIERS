#!/usr/bin/env python3
"""
Simple Supplier Invoice Processing System with AI Chat
- Upload invoices
- AI extract data
- Convert currencies to GBP
- AI chatbot for natural language queries
"""

import streamlit as st

# Configure page FIRST - must be the very first Streamlit command
st.set_page_config(
    page_title="Invoice Processing System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import sys
import tempfile
from datetime import datetime
import openai
import pandas as pd

# Add src to path
sys.path.append('src')

# Import required modules
from src.config import DATABASE_ENABLED, SUPABASE_URL, SUPABASE_KEY
from src.services.database_service import DatabaseService
from src.services.ai_extractor import extract_data_and_supplier
from src.services.pdf_reader import extract_text_from_pdf
from src.currency_utils import normalize_currency, is_gbp_currency, get_currency_name, convert_price

# Initialize OpenAI for chatbot
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize database service
database_service = None
if DATABASE_ENABLED:
    try:
        database_service = DatabaseService()
        # Database connection success will be shown later in the UI
    except Exception as e:
        # Database connection error will be shown later in the UI
        database_service = None

# Initialize session state first
if 'current_extraction' not in st.session_state:
    st.session_state.current_extraction = None
if 'buttons_hidden' not in st.session_state:
    st.session_state.buttons_hidden = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'manual_exchange_rate' not in st.session_state:
    st.session_state.manual_exchange_rate = None
if 'source_currency' not in st.session_state:
    st.session_state.source_currency = None
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'light'
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'show_shortcuts' not in st.session_state:
    st.session_state.show_shortcuts = False
if 'notifications' not in st.session_state:
    st.session_state.notifications = []

# Initialize session state first
if 'current_extraction' not in st.session_state:
    st.session_state.current_extraction = None
if 'buttons_hidden' not in st.session_state:
    st.session_state.buttons_hidden = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'manual_exchange_rate' not in st.session_state:
    st.session_state.manual_exchange_rate = None
if 'source_currency' not in st.session_state:
    st.session_state.source_currency = None
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'light'
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'show_shortcuts' not in st.session_state:
    st.session_state.show_shortcuts = False
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'bulk_mode' not in st.session_state:
    st.session_state.bulk_mode = False
if 'bulk_extractions' not in st.session_state:
    st.session_state.bulk_extractions = []
if 'bulk_processing_status' not in st.session_state:
    st.session_state.bulk_processing_status = 'idle'  # idle, processing, completed
if 'show_analytics' not in st.session_state:
    st.session_state.show_analytics = False
if 'pending_query' not in st.session_state:
    st.session_state.pending_query = None
if 'ai_response_cache' not in st.session_state:
    st.session_state.ai_response_cache = {}

st.title("📄 Supplier Invoice Processing System")

# Main Navigation
col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    if st.button("📄 Invoice Processing", 
                 use_container_width=True, 
                 type="primary" if not st.session_state.show_analytics else "secondary"):
        if st.session_state.show_analytics:  # Only rerun if actually changing
            st.session_state.show_analytics = False
            st.rerun()

with col2:
    if st.button("📊 Analytics Dashboard", 
                 use_container_width=True, 
                 type="primary" if st.session_state.show_analytics else "secondary"):
        if not st.session_state.show_analytics:  # Only rerun if actually changing
            st.session_state.show_analytics = True
            st.rerun()

# Status indicator
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    theme_icon = "🌙" if st.session_state.theme_mode == 'dark' else "☀️"
    st.caption(f"{theme_icon} {st.session_state.theme_mode.title()} Mode")
with col2:
    if database_service and database_service.enabled:
        st.caption("🟢 Database Online")
    else:
        st.caption("🔴 Database Offline")
with col3:
    shortcuts_status = "🟢 Enabled" if st.session_state.show_shortcuts else "⚫ Disabled"
    st.caption(f"⌨️ Shortcuts: {shortcuts_status}")

st.markdown("Upload invoices → AI extraction → Currency conversion → AI chat queries")

# Display notifications
if st.session_state.notifications:
    for notification in st.session_state.notifications[-3:]:  # Show last 3 notifications
        if notification["type"] == "success":
            st.success(notification["msg"])
        elif notification["type"] == "info":
            st.info(notification["msg"])
        elif notification["type"] == "warning":
            st.warning(notification["msg"])
        else:
            st.error(notification["msg"])
    # Clear notifications after showing them
    st.session_state.notifications = []

# Apply theme-based styling
if st.session_state.theme_mode == 'dark':
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stSidebar {
        background-color: #262730;
    }
    .stSidebar .stMarkdown h1, 
    .stSidebar .stMarkdown h2, 
    .stSidebar .stMarkdown h3,
    .stSidebar .stMarkdown h4,
    .stSidebar .stMarkdown h5,
    .stSidebar .stMarkdown h6,
    .stSidebar .stMarkdown p,
    .stSidebar .stMarkdown div {
        color: #fafafa !important;
    }
    .stButton > button {
        background-color: #262730;
        color: #fafafa;
        border: 1px solid #404040;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #fafafa;
        border: 1px solid #404040;
    }
    .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: #fafafa !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #fafafa !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #262730;
    }
    .stSidebar {
        background-color: #f0f2f6;
    }
    .stSidebar .stMarkdown h1, 
    .stSidebar .stMarkdown h2, 
    .stSidebar .stMarkdown h3,
    .stSidebar .stMarkdown h4,
    .stSidebar .stMarkdown h5,
    .stSidebar .stMarkdown h6,
    .stSidebar .stMarkdown p,
    .stSidebar .stMarkdown div {
        color: #262730 !important;
    }
    .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: #262730 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #262730 !important;
    }
    .stButton > button {
        background-color: #ffffff;
        color: #262730;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# Keyboard shortcuts functionality
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    // Ctrl+1: Focus upload area
    if (e.ctrlKey && e.key === '1') {
        e.preventDefault();
        const uploadBtn = document.querySelector('button:contains("Browse files")');
        if (uploadBtn) uploadBtn.focus();
    }
    // Ctrl+2: Focus chat input
    if (e.ctrlKey && e.key === '2') {
        e.preventDefault();
        const chatInput = document.querySelector('textarea[placeholder*="chat"]');
        if (chatInput) chatInput.focus();
    }
    // Ctrl+Enter: Submit chat (if in chat input)
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        const submitBtn = document.querySelector('button[kind="primary"]');
        if (submitBtn && document.activeElement.tagName === 'TEXTAREA') {
            submitBtn.click();
        }
    }
    // Esc: Clear current extraction
    if (e.key === 'Escape') {
        const clearBtn = document.querySelector('button:contains("Process New Invoice")');
        if (clearBtn) clearBtn.click();
    }
});
</script>
""", unsafe_allow_html=True)

# Processed Documents sidebar
with st.sidebar:
    # Theme and UX Controls
    st.markdown("## ⚙️ Settings")
    
    # Theme Toggle
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🌙 Dark" if st.session_state.theme_mode == 'light' else "☀️ Light", key="theme_toggle"):
            st.session_state.theme_mode = 'dark' if st.session_state.theme_mode == 'light' else 'light'
            st.rerun()
    
    with col2:
        if st.button("⌨️ Shortcuts", key="shortcuts_toggle"):
            st.session_state.show_shortcuts = not st.session_state.show_shortcuts
            st.rerun()
    
    # Show different sidebar content based on current view
    if st.session_state.show_analytics:
        # Analytics Dashboard Sidebar
        st.markdown("### 📊 Analytics Controls")
        
        # Analytics-specific quick actions
        if st.button("🔄 Refresh Data", key="refresh_analytics", help="Refresh analytics data"):
            st.session_state.notifications.append({"msg": "🔄 Analytics data refreshed!", "type": "success"})
            st.rerun()
        
        if st.button("📤 Export Analytics", key="export_analytics", help="Export analytics to CSV"):
            st.session_state.notifications.append({"msg": "📤 Analytics export coming soon!", "type": "info"})
        
        # Analytics info
        st.markdown("### 📈 Analytics Info")
        st.info("💡 **Tip**: Use the tabs above to explore different analytics views.")
        st.info("🔍 **Filter**: Analytics automatically update with your latest data.")
        
    else:
        # Invoice Processing Sidebar
        # Quick Actions Toolbar
        st.markdown("### 🚀 Quick Actions")
        qa_col1, qa_col2 = st.columns(2)
        with qa_col1:
            if st.button("📊 Analytics", key="quick_analytics", help="View database analytics"):
                st.session_state.show_analytics = True
                st.session_state.notifications.append({"msg": "📊 Opening analytics dashboard...", "type": "success"})
            if st.button("📤 Export", key="quick_export", help="Export data to CSV"):
                st.session_state.notifications.append({"msg": "📤 Export feature coming soon!", "type": "info"})
        
        with qa_col2:
            if st.button("🔍 Advanced Search", key="quick_search", help="Advanced search options"):
                st.session_state.notifications.append({"msg": "🔍 Advanced search feature coming soon!", "type": "info"})
            if st.button("⚡ Clear Cache", key="quick_clear", help="Clear search history"):
                st.session_state.recent_searches = []
                st.session_state.notifications.append({"msg": "🗑️ Search history cleared!", "type": "success"})
        
        # Recent Searches History
        if st.session_state.recent_searches:
            st.markdown("### 🕐 Recent Searches")
            for i, search in enumerate(reversed(st.session_state.recent_searches[-5:])):
                if st.button(f"🔍 {search[:25]}...", key=f"recent_search_{i}", help=f"Search: {search}"):
                    # Simulate clicking on the search
                    st.session_state.messages.append({
                        "role": "user",
                        "content": search,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    # Get AI response for the search
                    ai_response = ai_chat_response(search)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ai_response,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()
        
        # Show keyboard shortcuts if toggled (only in invoice processing mode)
        if st.session_state.show_shortcuts:
            st.markdown("### ⌨️ Keyboard Shortcuts")
            st.markdown("""
            - **Ctrl+1**: Focus upload area
            - **Ctrl+2**: Focus chat input
            - **Ctrl+Enter**: Send message
            - **Esc**: Clear current extraction
            """)
        
        # Processed Documents (only in invoice processing mode)
        st.markdown("---")
        st.markdown("## 📁 Processed Documents")
        if st.session_state.processed_documents:
            for i, doc in enumerate(reversed(st.session_state.processed_documents)):
                with st.expander(f"📄 {doc['filename'][:20]}..."):
                    st.write(f"**Supplier:** {doc['supplier']}")
                    st.write(f"**Products:** {doc['products_count']}")
                    st.write(f"**Currency:** {doc['currency_conversion']}")
                    st.write(f"**Processed:** {doc['processed_at']}")
                    st.write(f"**Saved:** {doc['saved_products']} products")
                    if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                        st.session_state.processed_documents.remove(doc)
                        st.rerun()
        else:
            st.info("No processed documents yet")
        
        if st.session_state.processed_documents:
            if st.button("🗑️ Clear All"):
                st.session_state.processed_documents = []
                st.rerun()

def process_document(uploaded_file):
    """Process uploaded document with improved AI extraction"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_path = tmp_file.name
        
        # Extract text from PDF
        with st.spinner("📄 Reading PDF document..."):
            pdf_text = extract_text_from_pdf(temp_path)
        
        if not pdf_text:
            st.error("❌ Could not extract text from PDF")
            return
            
        st.info(f"📄 Extracted {len(pdf_text)} characters from PDF")
        
        # Extract data using AI with improved prompts
        with st.spinner("🤖 AI is analyzing your invoice for supplier and product details..."):
            extracted_data = extract_data_and_supplier(pdf_text)
        
        if extracted_data and extracted_data.get('status') != 'error':
            # Debug: Show what AI extracted
            st.write("**🔍 AI Extraction Results:**")
            # Get supplier name from correct field structure
            supplier_name = extracted_data.get('supplier_name', 'Not found')
            st.write(f"- Supplier found: {supplier_name}")
            st.write(f"- Products found: {len(extracted_data.get('products', []))}")
            st.write(f"- Currency detected: {extracted_data.get('currency', 'Not found')}")
            
            st.session_state.current_extraction = {
                'filename': uploaded_file.name,
                'extracted': extracted_data,
                'pdf_path': temp_path,
                'pdf_text': pdf_text,  # Save original text for debugging
                'is_approved': None
            }
            st.session_state.buttons_hidden = False
            st.success("✅ Data extracted successfully!")
        else:
            st.error("❌ Failed to extract data from document")
            if extracted_data.get('error'):
                st.error(f"Error details: {extracted_data['error']}")
            
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
            
    except Exception as e:
        st.error(f"❌ Error processing document: {e}")
        import traceback
        st.code(traceback.format_exc())

def process_bulk_documents(uploaded_files):
    """Process multiple documents with progress tracking"""
    try:
        st.session_state.bulk_processing_status = 'processing'
        st.session_state.bulk_extractions = []
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Update progress
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
            
            # Process individual file
            result = process_single_file_bulk(uploaded_file)
            if result:
                st.session_state.bulk_extractions.append(result)
        
        st.session_state.bulk_processing_status = 'completed'
        progress_bar.progress(1.0)
        status_text.text(f"✅ Completed! Processed {len(st.session_state.bulk_extractions)}/{len(uploaded_files)} files successfully")
        st.success(f"🎉 Bulk processing completed! {len(st.session_state.bulk_extractions)} files ready for review")
        
    except Exception as e:
        st.session_state.bulk_processing_status = 'idle'
        st.error(f"❌ Bulk processing failed: {e}")

def process_single_file_bulk(uploaded_file):
    """Process a single file for bulk processing (non-interactive)"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_path = tmp_file.name
        
        # Read PDF
        pdf_text = extract_text_from_pdf(temp_path)
        
        if not pdf_text or len(pdf_text.strip()) < 100:
            return None
            
        # Extract data using AI
        extracted_data = extract_data_and_supplier(pdf_text)
        
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
        
        if extracted_data and extracted_data.get('status') != 'error':
            return {
                'filename': uploaded_file.name,
                'extracted': extracted_data,
                'pdf_text': pdf_text,
                'is_approved': None,
                'processing_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        return None
        
    except Exception as e:
        return None

def handle_bulk_approval():
    """Handle bulk approval of all extracted documents"""
    if not st.session_state.bulk_extractions:
        st.error("❌ No documents to approve")
        return
        
    try:
        approved_count = 0
        failed_count = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, extraction in enumerate(st.session_state.bulk_extractions):
            if extraction.get('is_approved') != False:  # Skip rejected ones
                # Update progress
                progress = (i + 1) / len(st.session_state.bulk_extractions)
                progress_bar.progress(progress)
                status_text.text(f"Approving {i+1}/{len(st.session_state.bulk_extractions)}: {extraction['filename']}")
                
                # Set as current extraction temporarily for approval logic
                st.session_state.current_extraction = extraction
                
                # Handle individual approval (reuse existing logic)
                try:
                    handle_approval()
                    approved_count += 1
                    extraction['is_approved'] = True
                except:
                    failed_count += 1
                    extraction['is_approved'] = False
        
        # Clear current extraction
        st.session_state.current_extraction = None
        
        # Show final results
        progress_bar.progress(1.0)
        status_text.text(f"✅ Bulk approval completed!")
        
        if approved_count > 0:
            st.success(f"🎉 {approved_count} documents approved and saved!")
        if failed_count > 0:
            st.warning(f"⚠️ {failed_count} documents failed to save")
            
        # Reset bulk processing
        st.session_state.bulk_extractions = []
        st.session_state.bulk_processing_status = 'idle'
        st.session_state.uploader_key += 1
        
    except Exception as e:
        st.error(f"❌ Bulk approval failed: {e}")

def display_bulk_extractions():
    """Display bulk extraction results for review"""
    if not st.session_state.bulk_extractions:
        return
        
    st.subheader(f"📋 Bulk Processing Results ({len(st.session_state.bulk_extractions)} files)")
    
    # Bulk action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve All", key="bulk_approve"):
            handle_bulk_approval()
    with col2:
        if st.button("❌ Reject All", key="bulk_reject"):
            for extraction in st.session_state.bulk_extractions:
                extraction['is_approved'] = False
            st.info("All documents rejected")
    with col3:
        if st.button("🗑️ Clear All", key="bulk_clear"):
            st.session_state.bulk_extractions = []
            st.session_state.bulk_processing_status = 'idle'
            st.rerun()
    
    # Display individual extractions
    for i, extraction in enumerate(st.session_state.bulk_extractions):
        with st.expander(f"📄 {extraction['filename']}", expanded=False):
            data = extraction['extracted']
            
            # Show supplier info
            supplier_name = data.get('supplier_name', 'Unknown')
            currency = data.get('currency', 'Unknown')
            products = data.get('products', [])
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Supplier:** {supplier_name}")
                st.write(f"**Currency:** {currency}")
            with col2:
                st.write(f"**Products:** {len(products)}")
                st.write(f"**Status:** {extraction.get('is_approved', 'Pending')}")
            
            # Individual action buttons
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("✅ Approve", key=f"approve_{i}"):
                    st.session_state.current_extraction = extraction
                    handle_approval()
                    st.session_state.current_extraction = None
                    extraction['is_approved'] = True
                    st.rerun()
            with btn_col2:
                if st.button("❌ Reject", key=f"reject_{i}"):
                    extraction['is_approved'] = False
                    st.rerun()

# Analytics Functions
def get_supplier_cost_analysis():
    """Get cost analysis data across suppliers"""
    try:
        if not database_service or not database_service.enabled:
            return None
            
        # Get all products
        products_result = database_service.supplier_manager.supabase.table('products').select(
            'product_name, size, unit_price, currency, original_price, category, created_at, usage_type'
        ).execute()
        
        # Get documents with supplier info
        documents_result = database_service.supplier_manager.supabase.table('documents').select(
            'id, supplier_id'
        ).execute()
        
        suppliers_result = database_service.supplier_manager.supabase.table('suppliers').select(
            'id, name'
        ).execute()
        
        if not products_result.data:
            return []
            
        # Create lookups
        suppliers = {s['id']: s['name'] for s in suppliers_result.data} if suppliers_result.data else {}
        documents = {d['id']: d['supplier_id'] for d in documents_result.data} if documents_result.data else {}
        
        # Combine data
        result = []
        for p in products_result.data:
            # Extract supplier info and price from usage_type
            supplier_id = None
            supplier_name = 'Unknown'
            extracted_price = 0
            
            if p.get('usage_type'):
                try:
                    usage_type = str(p['usage_type'])
                    
                    # Handle semicolon-separated format first
                    if ';' in usage_type:
                        # Take the first part: £38.00|2025-12-23T18:57:43.221610|supplier_id
                        usage_type = usage_type.split(';')[0]
                    
                    if '|' in usage_type:
                        # Format: £13.00|2025-12-23T18:57:42.238572|supplier_id or with |DOC:filename
                        parts = usage_type.split('|')
                        if len(parts) >= 3:
                            # Extract price from first part
                            price_str = parts[0].replace('£', '').replace(',', '').strip()
                            try:
                                extracted_price = float(price_str)
                            except:
                                extracted_price = 0
                            
                            # Extract supplier_id from third part
                            supplier_id = parts[2].strip()
                    elif 'Supplier:' in usage_type:
                        # Old format: Supplier: MAC Global Ventures Ltd
                        supplier_name = usage_type.replace('Supplier:', '').strip()
                except Exception as e:
                    print(f"Error parsing usage_type: {e}")
            
            # Get supplier name if we have supplier_id
            if supplier_id and supplier_id in suppliers:
                supplier_name = suppliers[supplier_id]
            
            # Use extracted price if unit_price is None
            unit_price = p.get('unit_price')
            if unit_price is None:
                unit_price = extracted_price
            else:
                try:
                    unit_price = float(unit_price)
                except (ValueError, TypeError):
                    unit_price = extracted_price
            
            # Handle original price
            original_price = p.get('original_price', 0)
            if original_price is None:
                original_price = 0
            try:
                original_price = float(original_price)
            except (ValueError, TypeError):
                original_price = 0
            
            result.append({
                'supplier_name': supplier_name,
                'product_name': p.get('product_name', 'Unknown'),
                'size': p.get('size', 'Unknown'),
                'price_gbp': round(unit_price, 2),
                'currency': p.get('currency', 'GBP'),
                'original_price': round(original_price, 2),
                'category': p.get('category', 'Uncategorized'),
                'created_at': p.get('created_at', '')
            })
            
        return result
    except Exception as e:
        st.error(f"Error fetching cost analysis data: {e}")
        return []

def get_price_comparison_data():
    """Get price comparison data for products across suppliers"""
    try:
        if not database_service or not database_service.enabled:
            return None
            
        # Get all products
        products_result = database_service.supplier_manager.supabase.table('products').select(
            'product_name, size, unit_price, currency, original_price, usage_type'
        ).execute()
        
        # Get documents with supplier info
        documents_result = database_service.supplier_manager.supabase.table('documents').select(
            'id, supplier_id'
        ).execute()
        
        suppliers_result = database_service.supplier_manager.supabase.table('suppliers').select(
            'id, name'
        ).execute()
        
        if not products_result.data:
            return []
            
        # Create lookups
        suppliers = {s['id']: s['name'] for s in suppliers_result.data} if suppliers_result.data else {}
        documents = {d['id']: d['supplier_id'] for d in documents_result.data} if documents_result.data else {}
        
        # Group products by name and size to find duplicates
        product_groups = {}
        for p in products_result.data:
            # Extract supplier info and price from usage_type
            supplier_id = None
            supplier_name = 'Unknown'
            extracted_price = 0
            
            if p.get('usage_type'):
                try:
                    usage_type = str(p['usage_type'])
                    
                    # Handle semicolon-separated format first
                    if ';' in usage_type:
                        usage_type = usage_type.split(';')[0]
                    
                    if '|' in usage_type:
                        parts = usage_type.split('|')
                        if len(parts) >= 3:
                            # Extract price
                            price_str = parts[0].replace('£', '').replace(',', '').strip()
                            try:
                                extracted_price = float(price_str)
                            except:
                                extracted_price = 0
                            
                            # Extract supplier_id
                            supplier_id = parts[2].strip()
                    elif 'Supplier:' in usage_type:
                        supplier_name = usage_type.replace('Supplier:', '').strip()
                except:
                    pass
            
            # Get supplier name if we have supplier_id
            if supplier_id and supplier_id in suppliers:
                supplier_name = suppliers[supplier_id]
            
            # Use extracted price if unit_price is None
            unit_price = p.get('unit_price')
            if unit_price is None:
                unit_price = extracted_price
            else:
                try:
                    unit_price = float(unit_price)
                except (ValueError, TypeError):
                    unit_price = extracted_price
                
            original_price = p.get('original_price', 0)
            if original_price is None:
                original_price = 0
            try:
                original_price = float(original_price)
            except (ValueError, TypeError):
                original_price = 0
            
            key = f"{p.get('product_name', 'Unknown')}_{p.get('size', 'Unknown')}"
            if key not in product_groups:
                product_groups[key] = []
            product_groups[key].append({
                'product_name': p.get('product_name', 'Unknown'),
                'size': p.get('size', 'Unknown'),
                'supplier_name': supplier_name,
                'price_gbp': round(unit_price, 2),
                'currency': p.get('currency', 'GBP'),
                'original_price': round(original_price, 2)
            })
        
        # Filter for products with multiple suppliers
        result = []
        for group in product_groups.values():
            if len(group) > 1:
                for item in group:
                    item['supplier_count'] = len(group)
                    result.append(item)
                    
        return result
    except Exception as e:
        st.error(f"Error fetching price comparison data: {e}")
        return []

def get_category_breakdown():
    """Get product category breakdown data"""
    try:
        if not database_service or not database_service.enabled:
            return None
            
        # Get all products
        products_result = database_service.supplier_manager.supabase.table('products').select(
            'category, unit_price, usage_type'
        ).execute()
        
        # Get documents with supplier info
        documents_result = database_service.supplier_manager.supabase.table('documents').select(
            'id, supplier_id'
        ).execute()
        
        if not products_result.data:
            return []
            
        # Create document lookup
        documents = {d['id']: d['supplier_id'] for d in documents_result.data} if documents_result.data else {}
        
        # Group by category
        categories = {}
        for p in products_result.data:
            # Extract supplier info and price from usage_type
            supplier_id = None
            extracted_price = 0
            
            if p.get('usage_type'):
                try:
                    usage_type = str(p['usage_type'])
                    
                    # Handle semicolon-separated format first
                    if ';' in usage_type:
                        usage_type = usage_type.split(';')[0]
                    
                    if '|' in usage_type:
                        parts = usage_type.split('|')
                        if len(parts) >= 3:
                            # Extract price
                            price_str = parts[0].replace('£', '').replace(',', '').strip()
                            try:
                                extracted_price = float(price_str)
                            except:
                                extracted_price = 0
                            
                            # Extract supplier_id
                            supplier_id = parts[2].strip()
                except:
                    pass
            
            # Use extracted price if unit_price is None
            unit_price = p.get('unit_price')
            if unit_price is None:
                unit_price = extracted_price
            else:
                try:
                    unit_price = float(unit_price)
                except (ValueError, TypeError):
                    unit_price = extracted_price
            
            cat = p.get('category') or 'Uncategorized'
            if cat not in categories:
                categories[cat] = {
                    'category': cat,
                    'products': [],
                    'suppliers': set()
                }
            categories[cat]['products'].append(unit_price)
            
            if supplier_id:
                categories[cat]['suppliers'].add(supplier_id)
        
        # Calculate statistics
        result = []
        for cat_data in categories.values():
            prices = cat_data['products']
            result.append({
                'category': cat_data['category'],
                'product_count': len(prices),
                'supplier_count': len(cat_data['suppliers']),
                'avg_price_gbp': sum(prices) / len(prices) if prices else 0,
                'min_price_gbp': min(prices) if prices else 0,
                'max_price_gbp': max(prices) if prices else 0,
                'total_value_gbp': sum(prices)
            })
            
        return sorted(result, key=lambda x: x['product_count'], reverse=True)
    except Exception as e:
        st.error(f"Error fetching category breakdown: {e}")
        return []

def get_supplier_performance_data():
    """Get supplier performance and statistics"""
    try:
        if not database_service or not database_service.enabled:
            return None
            
        # Get suppliers and products
        suppliers_result = database_service.supplier_manager.supabase.table('suppliers').select(
            'id, name, created_at'
        ).execute()
        
        # Get all products
        products_result = database_service.supplier_manager.supabase.table('products').select(
            'unit_price, category, usage_type'
        ).execute()
        
        # Get documents with supplier info
        documents_result = database_service.supplier_manager.supabase.table('documents').select(
            'id, supplier_id'
        ).execute()
        
        if not suppliers_result.data:
            return []
            
        # Create lookups
        documents = {d['id']: d['supplier_id'] for d in documents_result.data} if documents_result.data else {}
        
        # Group products by supplier
        supplier_products = {}
        for s in suppliers_result.data:
            supplier_products[s['id']] = {
                'supplier_name': s['name'],
                'created_at': s['created_at'],
                'products': [],
                'categories': set()
            }
            
        for p in products_result.data if products_result.data else []:
            # Extract supplier info and price from usage_type
            supplier_id = None
            extracted_price = 0
            
            if p.get('usage_type'):
                try:
                    usage_type = str(p['usage_type'])
                    
                    # Handle semicolon-separated format first
                    if ';' in usage_type:
                        usage_type = usage_type.split(';')[0]
                    
                    if '|' in usage_type:
                        parts = usage_type.split('|')
                        if len(parts) >= 3:
                            # Extract price
                            price_str = parts[0].replace('£', '').replace(',', '').strip()
                            try:
                                extracted_price = float(price_str)
                            except:
                                extracted_price = 0
                            
                            # Extract supplier_id
                            supplier_id = parts[2].strip()
                except:
                    pass
            
            # Use extracted price if unit_price is None
            unit_price = p.get('unit_price')
            if unit_price is None:
                unit_price = extracted_price
            else:
                try:
                    unit_price = float(unit_price)
                except (ValueError, TypeError):
                    unit_price = extracted_price
            
            if supplier_id and supplier_id in supplier_products:
                supplier_products[supplier_id]['products'].append(unit_price)
                if p['category']:
                    supplier_products[supplier_id]['categories'].add(p['category'])
        
        # Calculate statistics
        result = []
        for data in supplier_products.values():
            prices = data['products']
            result.append({
                'supplier_name': data['supplier_name'],
                'total_products': len(prices),
                'avg_price_gbp': sum(prices) / len(prices) if prices else 0,
                'min_price_gbp': min(prices) if prices else 0,
                'max_price_gbp': max(prices) if prices else 0,
                'category_diversity': len(data['categories']),
                'created_at': data['created_at']
            })
            
        return sorted(result, key=lambda x: x['total_products'], reverse=True)
    except Exception as e:
        st.error(f"Error fetching supplier performance data: {e}")
        return []

def display_analytics_dashboard():
    """Display the complete analytics dashboard"""
    st.header("📊 Analytics & Reporting Dashboard")
    
    if not database_service or not database_service.enabled:
        st.warning("📊 Analytics requires database connection. Please check your database configuration.")
        return
    
    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Cost Analysis", "🔄 Price Comparison", "📦 Category Breakdown", "🏢 Supplier Performance"])
    
    with tab1:
        display_cost_analysis()
    
    with tab2:
        display_price_comparison()
    
    with tab3:
        display_category_breakdown()
    
    with tab4:
        display_supplier_performance()

def display_cost_analysis():
    """Display cost analysis charts and data"""
    st.subheader("💰 Cost Analysis Across Suppliers")
    
    cost_data = get_supplier_cost_analysis()
    if not cost_data:
        st.info("📊 No cost data available. Upload some invoices to see analytics.")
        return
    
    # Convert to DataFrame for easier processing
    import pandas as pd
    df = pd.DataFrame(cost_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = len(df)
        st.metric("Total Products", total_products)
    
    with col2:
        total_suppliers = df['supplier_name'].nunique()
        st.metric("Total Suppliers", total_suppliers)
    
    with col3:
        avg_price = df['price_gbp'].mean()
        st.metric("Average Price (GBP)", f"£{avg_price:.2f}")
    
    with col4:
        total_value = df['price_gbp'].sum()
        st.metric("Total Value (GBP)", f"£{total_value:.2f}")
    
    # Charts
    st.subheader("📈 Price Distribution by Supplier")
    
    # Box plot for price distribution
    supplier_prices = df.groupby('supplier_name')['price_gbp'].apply(list).to_dict()
    
    if len(supplier_prices) > 0:
        # Create a simple bar chart showing average prices by supplier
        avg_by_supplier = df.groupby('supplier_name')['price_gbp'].mean().sort_values(ascending=True)
        st.bar_chart(avg_by_supplier)
        
        # Show detailed table
        st.subheader("📋 Detailed Cost Data")
        display_df = df[['supplier_name', 'product_name', 'size', 'price_gbp', 'currency', 'category']].copy()
        # Format price_gbp to 2 decimal places in display
        display_df['price_gbp'] = display_df['price_gbp'].apply(lambda x: f"£{x:.2f}")
        st.dataframe(display_df, use_container_width=True)

def display_price_comparison():
    """Display price comparison for products across suppliers"""
    st.subheader("🔄 Price Comparison Across Suppliers")
    
    comparison_data = get_price_comparison_data()
    if not comparison_data:
        st.info("📊 No comparable products found. Need products from multiple suppliers to show comparisons.")
        return
    
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    
    # Group by product and show price differences
    st.subheader("💸 Products with Multiple Suppliers")
    
    for product_name in df['product_name'].unique():
        product_df = df[df['product_name'] == product_name]
        
        if len(product_df) > 1:
            st.write(f"**{product_name}**")
            
            # Show price comparison for this product
            price_comparison = product_df[['supplier_name', 'size', 'price_gbp', 'currency']].copy()
            price_comparison['price_gbp'] = price_comparison['price_gbp'].round(2)
            price_comparison = price_comparison.sort_values('price_gbp')
            
            # Highlight best price
            min_price = price_comparison['price_gbp'].min()
            max_price = price_comparison['price_gbp'].max()
            savings = max_price - min_price
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(price_comparison, use_container_width=True)
            with col2:
                st.metric("Best Price", f"£{min_price:.2f}")
                st.metric("Potential Savings", f"£{savings:.2f}")
                if savings > 0:
                    savings_percent = (savings / max_price) * 100
                    st.metric("Savings %", f"{savings_percent:.1f}%")
            
            st.markdown("---")

def display_category_breakdown():
    """Display product category breakdown and analysis"""
    st.subheader("📦 Product Category Breakdown")
    
    category_data = get_category_breakdown()
    if not category_data:
        st.info("📊 No category data available. Upload some invoices to see category breakdown.")
        return
    
    import pandas as pd
    df = pd.DataFrame(category_data)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_categories = len(df)
        st.metric("Total Categories", total_categories)
    
    with col2:
        largest_category = df.loc[df['product_count'].idxmax()]
        st.metric("Largest Category", f"{largest_category['category']} ({largest_category['product_count']} products)")
    
    with col3:
        highest_value_cat = df.loc[df['total_value_gbp'].idxmax()]
        st.metric("Highest Value Category", f"{highest_value_cat['category']} (£{highest_value_cat['total_value_gbp']:.2f})")
    
    # Charts
    st.subheader("📊 Category Distribution")
    
    # Product count by category
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Products per Category**")
        product_counts = df.set_index('category')['product_count']
        st.bar_chart(product_counts)
    
    with col2:
        st.write("**Value per Category (GBP)**")
        category_values = df.set_index('category')['total_value_gbp']
        st.bar_chart(category_values)
    
    # Detailed breakdown table
    st.subheader("📋 Detailed Category Analysis")
    display_df = df.copy()
    display_df['avg_price_gbp'] = display_df['avg_price_gbp'].round(2)
    display_df['min_price_gbp'] = display_df['min_price_gbp'].round(2)
    display_df['max_price_gbp'] = display_df['max_price_gbp'].round(2)
    display_df['total_value_gbp'] = display_df['total_value_gbp'].round(2)
    
    st.dataframe(display_df, use_container_width=True)

def display_supplier_performance():
    """Display supplier performance metrics and analysis"""
    st.subheader("🏢 Supplier Performance Analysis")
    
    supplier_data = get_supplier_performance_data()
    if not supplier_data:
        st.info("📊 No supplier data available. Upload some invoices to see supplier analysis.")
        return
    
    import pandas as pd
    df = pd.DataFrame(supplier_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_suppliers = len(df)
        st.metric("Total Suppliers", total_suppliers)
    
    with col2:
        most_products_supplier = df.loc[df['total_products'].idxmax()]
        st.metric("Most Products", f"{most_products_supplier['supplier_name']} ({most_products_supplier['total_products']} items)")
    
    with col3:
        highest_avg_price = df.loc[df['avg_price_gbp'].idxmax()]
        st.metric("Highest Avg Price", f"{highest_avg_price['supplier_name']} (£{highest_avg_price['avg_price_gbp']:.2f})")
    
    with col4:
        most_diverse = df.loc[df['category_diversity'].idxmax()]
        st.metric("Most Diverse", f"{most_diverse['supplier_name']} ({most_diverse['category_diversity']} categories)")
    
    # Charts
    st.subheader("📈 Supplier Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Products per Supplier**")
        products_per_supplier = df.set_index('supplier_name')['total_products'].sort_values(ascending=True)
        st.bar_chart(products_per_supplier)
    
    with col2:
        st.write("**Average Price per Supplier (GBP)**")
        avg_prices = df.set_index('supplier_name')['avg_price_gbp'].sort_values(ascending=True)
        st.bar_chart(avg_prices)
    
    # Detailed supplier table
    st.subheader("📋 Detailed Supplier Analysis")
    display_df = df.copy()
    display_df['avg_price_gbp'] = display_df['avg_price_gbp'].round(2)
    display_df['min_price_gbp'] = display_df['min_price_gbp'].round(2)
    display_df['max_price_gbp'] = display_df['max_price_gbp'].round(2)
    
    st.dataframe(display_df, use_container_width=True)

def ai_chat_response(user_query):
    """Generate AI response for user queries about products and suppliers"""
    if not database_service:
        return "❌ Database not available. Please check your database connection."
    
    # Check cache first to improve performance
    cache_key = user_query.lower().strip()
    if cache_key in st.session_state.ai_response_cache:
        return st.session_state.ai_response_cache[cache_key]
    
    try:
        # Get recent products and suppliers for context
        supabase = database_service.supplier_manager.supabase
        products_result = supabase.table('products').select('*').limit(50).execute()
        suppliers_result = supabase.table('suppliers').select('*').limit(20).execute()
        documents_result = supabase.table('documents').select('id, supplier_id, file_name, upload_date').limit(30).execute()
        
        products_data = products_result.data if products_result.data else []
        suppliers_data = suppliers_result.data if suppliers_result.data else []
        documents_data = documents_result.data if documents_result.data else []
        
        # Create supplier lookup
        supplier_lookup = {s['id']: s['name'] for s in suppliers_data}
        
        # Build enhanced product list with supplier info and correct prices
        enhanced_products = []
        for p in products_data:
            # Extract price from multiple possible columns with better logic
            price = None
            if p.get('unit_price'):
                price = float(p['unit_price'])
            elif p.get('original_price'):
                price = float(p['original_price'])  
            elif p.get('usage_type'):
                # Handle old format: "£8.50|timestamp|supplier_id" or just a number
                usage_value = str(p['usage_type'])
                if '|' in usage_value:
                    # Extract price from pipe-separated format
                    price_part = usage_value.split('|')[0]
                    if price_part.startswith('£'):
                        try:
                            price = float(price_part[1:])  # Remove £ symbol and convert
                        except:
                            pass
                elif usage_value.replace('.', '').replace('£', '').isdigit():
                    # Simple number or £number format
                    try:
                        clean_price = usage_value.replace('£', '')
                        price = float(clean_price)
                    except:
                        pass
            
            # Try to find supplier through recent documents (best effort)
            supplier_name = "Unknown Supplier"
            
            # First try to extract from usage_type if it has supplier info
            usage_value = str(p.get('usage_type', ''))
            
            # Check for new format: "Supplier: Supplier Name"
            if usage_value.startswith('Supplier: '):
                potential_supplier = usage_value.replace('Supplier: ', '').strip()
                # Check if this supplier name exists in our supplier lookup
                for supplier_id, name in supplier_lookup.items():
                    if name == potential_supplier:
                        supplier_name = name
                        break
                # If not found by exact match, just use the name from usage_type
                if supplier_name == "Unknown Supplier":
                    supplier_name = potential_supplier
            
            # Check for old pipe-separated format: "price|timestamp|supplier_id"
            elif '|' in usage_value:
                parts = usage_value.split('|')
                if len(parts) >= 3:
                    supplier_id = parts[2]
                    if supplier_id in supplier_lookup:
                        supplier_name = supplier_lookup[supplier_id]
            
            # If still not found, try matching by date
            if supplier_name == "Unknown Supplier":
                product_date = p.get('created_at', '')
                if product_date:
                    for doc in documents_data:
                        if doc.get('upload_date', '')[:10] == product_date[:10]:  # Same date
                            supplier_id = doc.get('supplier_id')
                            if supplier_id in supplier_lookup:
                                supplier_name = supplier_lookup[supplier_id]
                                break
            
            enhanced_products.append({
                'name': p.get('product_name', 'Unknown'),
                'price': price or 0,
                'supplier': supplier_name,
                'category': p.get('category', 'Unknown'),
                'currency': p.get('currency') or 'GBP',  # Ensure currency is never None
                'original_price': p.get('original_price'),
                'original_currency': p.get('original_currency') or 'GBP',  # Ensure never None
                'size': p.get('size', ''),  # Pack size information
                'material': p.get('material', '')
            })
        
        # Build context for AI
        context = f"""
You are an AI assistant for a supplier invoice processing system. Here's the current database:

SUPPLIERS ({len(suppliers_data)}):
{chr(10).join([f"- {s.get('name', 'Unknown')}" for s in suppliers_data[:10]])}

PRODUCTS WITH SUPPLIERS ({len(enhanced_products)}):
{chr(10).join([f"- {p['name']}{' (' + p['size'] + ')' if p.get('size') else ''} (£{p['price']:.2f}) from {p['supplier']}" + (f" [Original: {p.get('original_price', 'N/A')} {p.get('original_currency', '')}]" if p.get('original_price') else "") for p in enhanced_products])}

User Query: {user_query}

Instructions:
1. STRICT EXACT MATCHING ONLY - If user searches for "8oz", show ONLY products that contain "8oz" or "8 oz" in the name. Do NOT show 7oz, 9oz, 10oz, or any other sizes.
2. Check if the user query contains words like "original price", "original prices", "buying price", "original currency", or "original cost"
3. If the user asks for "all products", "show all products", "list all products", "how many products", "show products", or "list products" - show ALL {len(enhanced_products)} products regardless of pricing
4. If original prices ARE requested:
   - Show: "Product Name (Pack Size) (£GBP_Price | Original: $USD_Price) from Supplier" 
   - Example: "8 OZ RIPPLE WALL PAPER CUPS (500 pcs) (£10.99 | Original: $13.08 USD) from Greenpack India Private Limited"
5. If original prices are NOT requested:
   - Show: "Product Name (Pack Size) (£GBP_Price) from Supplier"
   - For products with £0.00 price, show: "Product Name (Pack Size) (No pricing) from Supplier"
6. Always include pack size information when available (from the size field)
7. If multiple suppliers have the same product, list all suppliers with their prices
8. Be concise and only answer what was asked
9. Use emojis sparingly
10. ONLY suggest alternatives if NO exact matches are found

CRITICAL MATCHING RULES:
- "8oz" query = ONLY show products with "8oz", "8 oz", or "8OZ" in the name
- "7oz" query = ONLY show products with "7oz", "7 oz", or "7OZ" in the name  
- "ripple" query = ONLY show products with "ripple" in the name
- Do NOT include products that are "close" or "similar" unless NO exact matches exist

IMPORTANT FORMATTING:
- Show each product on a SEPARATE LINE with actual line breaks
- Use bullet points (•) for multiple products
- Do NOT put multiple products on the same line
- Use this EXACT format for multiple products:

• Product 1 (Pack Size) (£Price or No pricing) from Supplier 1

• Product 2 (Pack Size) (£Price or No pricing) from Supplier 2

CRITICAL: Put each product on its own line. Use \\n or actual line breaks between products.

IMPORTANT: The user query "{user_query}" contains original price request: {"original" in user_query.lower()}

Provide a precise response based ONLY on what the user requested.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise AI assistant for a supplier database. Be concise and only show exactly what the user asks for. Only show original prices if specifically requested. CRITICAL: When showing multiple products, put each product on a separate line with a bullet point. Use actual line breaks between products."},
                {"role": "user", "content": context}
            ],
            max_tokens=800,
            temperature=0.3  # Lower temperature for more precise responses
        )
        
        ai_response = response.choices[0].message.content
        
        # Cache the response to improve performance (limit cache size)
        if len(st.session_state.ai_response_cache) > 20:  # Limit cache size
            # Remove oldest entry
            oldest_key = next(iter(st.session_state.ai_response_cache))
            del st.session_state.ai_response_cache[oldest_key]
        
        st.session_state.ai_response_cache[cache_key] = ai_response
        
        return ai_response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"AI Chat Error: {e}")
        print(f"Traceback: {error_details}")
        return f"❌ Sorry, I encountered an error: {e}"

def display_extracted_data(data):
    """Display extracted data for review in clean text format"""
    
    # Supplier Information - Try multiple data paths
    st.subheader("🏢 Supplier Information")
    
    # Try different ways to get supplier info
    supplier = data.get('supplier', {})
    supplier_info = data.get('supplier_info', {})
    
    # Get supplier name from multiple possible locations
    supplier_name = (
        supplier.get('name') or 
        supplier_info.get('name') or 
        data.get('supplier_name') or 
        data.get('company_name') or 
        'Unknown Supplier'
    )
    
    # Get other supplier details
    address = (
        supplier.get('address') or 
        supplier_info.get('address') or 
        data.get('supplier_address') or 
        'Not provided'
    )
    
    email = (
        supplier.get('email') or 
        supplier_info.get('email') or 
        data.get('supplier_email') or 
        'Not provided'
    )
    
    phone = (
        supplier.get('phone') or 
        supplier_info.get('phone') or 
        data.get('supplier_phone') or 
        'Not provided'
    )
    
    vat_number = (
        supplier.get('vat_number') or 
        supplier_info.get('vat_number') or 
        data.get('vat_number') or 
        'Not provided'
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Company:** {supplier_name}")
        st.write(f"**Address:** {address}")
        st.write(f"**Email:** {email}")
    with col2:
        st.write(f"**Phone:** {phone}")
        st.write(f"**VAT Number:** {vat_number}")
        
        # Show currency info
        currency = data.get('currency', 'GBP')
        try:
            currency_code, currency_symbol = normalize_currency(currency)
        except:
            currency_code, currency_symbol = currency, currency
        st.write(f"**Document Currency:** {currency_symbol} ({currency_code})")
        
        # Currency Conversion Interface for non-GBP currencies  
        if currency_code != 'GBP' and not is_gbp_currency(currency):
            st.warning(f"⚠️ Foreign currency detected: {currency_code}")
            st.subheader("💱 Currency Conversion Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                exchange_rate = st.number_input(
                    f"Exchange Rate ({currency_code} to GBP)",
                    min_value=0.001,
                    max_value=100.0,
                    value=0.79 if currency_code == 'USD' else 1.0,  # Default rates
                    step=0.01,
                    key=f"exchange_rate_{currency_code}",  # Unique key to prevent duplicate ID error
                    help=f"Enter the current exchange rate to convert {currency_code} prices to GBP"
                )
            with col2:
                st.info(f"💡 Example: If 1 {currency_code} = 0.79 GBP, enter 0.79")
                st.write(f"**Current setting:** 1 {currency_code} = {exchange_rate:.3f} GBP")
            
            # Store exchange rate in session state for use during approval
            st.session_state.manual_exchange_rate = exchange_rate
            st.session_state.source_currency = currency_code
            st.success(f"✅ Conversion rate set: 1 {currency_code} = {exchange_rate:.3f} GBP")
        else:
            # Currency is already GBP, no conversion needed
            st.session_state.manual_exchange_rate = 1.0
            st.session_state.source_currency = 'GBP'
            st.success("✅ Document currency is GBP - no conversion needed")

    # Products Information - Improved data access
    st.subheader("📦 Products")
    products = data.get('products', [])
    
    st.write(f"**Found {len(products)} product(s)**")
    
    if products:
        for i, product in enumerate(products, 1):
            # Get product name from multiple possible locations
            product_name = (
                product.get('product_name') or 
                product.get('name') or 
                product.get('description') or 
                f'Product {i}'
            )
            
            with st.expander(f"Product {i}: {product_name}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Name:** {product_name}")
                    st.write(f"**Category:** {product.get('category', 'Unknown')}")
                    st.write(f"**Size:** {product.get('size', 'Unknown')}")
                
                with col2:
                    st.write(f"**Quantity:** {product.get('quantity', 'Unknown')}")
                    st.write(f"**Material:** {product.get('material', 'Unknown')}")
                
                with col3:
                    # Show pack pricing info
                    pack_price = product.get('pack_price', 0)
                    pack_quantity = product.get('pack_quantity', 1)
                    unit_price = product.get('unit_price', 0)
                    
                    if pack_price > 0 and pack_quantity > 1:
                        st.write(f"**Pack Price:** {currency_symbol}{pack_price:.2f}")
                        st.write(f"**Pack Size:** {pack_quantity} pcs")
                        per_item = pack_price / pack_quantity if pack_quantity > 0 else 0
                        st.write(f"**Per Item:** {currency_symbol}{per_item:.4f}")
                    else:
                        # Fallback to regular price display
                        price = product.get('price', 0)
                        st.write(f"**Price:** {currency_symbol}{unit_price:.2f}")
                        if pack_quantity > 1:
                            st.write(f"**Pack Size:** {pack_quantity} pcs")
    else:
        st.write("No products found")
    
    # Currency conversion notice
    if currency_code != 'GBP':
        st.info(f"💱 **Currency Conversion Required:** Prices are in {currency_code}. You'll be asked for the GBP conversion rate when approving.")

def handle_approval():
    """Handle document approval with currency conversion and duplicate detection"""
    if not st.session_state.current_extraction:
        st.error("❌ No document to approve")
        return
        
    if not database_service:
        st.error("❌ Database not available")
        return
    
    try:
        st.write("🔄 **Step 1: Getting extraction data...**")
        extracted_data = st.session_state.current_extraction['extracted']
        st.write(f"✅ Extracted data keys: {list(extracted_data.keys())}")
        
        st.write("🔄 **Step 2: Applying currency conversion...**")
        
        # Get currency conversion info from session state
        manual_exchange_rate = st.session_state.get('manual_exchange_rate', 1.0)
        source_currency = st.session_state.get('source_currency', 'GBP')
        st.write(f"✅ Exchange rate: {manual_exchange_rate}, Source currency: {source_currency}")
        
        # Get supplier info
        supplier_name = (
            extracted_data.get('supplier_name') or
            extracted_data.get('supplier', {}).get('name') or
            'Unknown Supplier'
        )
        st.write(f"✅ Supplier name: {supplier_name}")
        
        # Process products with currency conversion
        products = extracted_data.get('products', [])
        st.write(f"✅ Found {len(products)} products to process")
        if not products:
            st.error("❌ No products found in extraction")
            return
        
        converted_products = []
        for product in products:
            # Get original price and currency
            original_price = product.get('price', 0) or product.get('unit_price', 0)
            product_currency = product.get('currency', source_currency)
            
            # Apply conversion if needed
            if product_currency != 'GBP' and manual_exchange_rate != 1.0:
                gbp_price = original_price * manual_exchange_rate
                conversion_rate = manual_exchange_rate
            else:
                gbp_price = original_price
                conversion_rate = 1.0
            
            # Enhanced product record with both original and converted prices
            converted_product = {
                'name': product.get('name', 'Unknown Product'),
                'supplier_name': supplier_name,
                'price': gbp_price,  # Converted GBP price
                'unit_price': gbp_price,  # Converted GBP price
                'original_price': original_price,  # Original price
                'currency': 'GBP',  # Final currency is always GBP
                'original_currency': product_currency,  # Original currency
                'conversion_rate': conversion_rate,  # Conversion rate used
                'category': product.get('category', 'Unknown'),
                'size': product.get('size', 'Unknown'),
                'material': product.get('material'),
                'quantity': product.get('quantity', 1),
                'pricing': {
                    'unit_price': gbp_price,
                    'currency': 'GBP'
                }
            }
            converted_products.append(converted_product)
        
        st.write(f"✅ **Supplier:** {supplier_name}")
        st.write(f"✅ **Products:** {len(converted_products)} items")
        if source_currency != 'GBP':
            st.write(f"✅ **Currency conversion:** {source_currency} → GBP (rate: {manual_exchange_rate})")
        
        # Enhanced data structure with currency conversion info
        enhanced_data = {
            'supplier_name': supplier_name,
            'supplier_info': extracted_data.get('supplier_info', {'name': supplier_name}),
            'products': converted_products,
            'currency_info': {
                'final_currency': 'GBP',
                'original_currency': source_currency,
                'conversion_rate': manual_exchange_rate
            }
        }
        
        st.write("🔄 **Step 3: Testing database connection...**")
        
        # Test database connection
        try:
            supabase = database_service.supplier_manager.supabase
            test_query = supabase.table('suppliers').select('*').limit(1).execute()
            st.success("✅ Database connection working")
        except Exception as db_error:
            st.error(f"❌ Database connection failed: {db_error}")
            return
        
        st.write("🔄 **Step 4: Saving with duplicate detection...**")
        
        pdf_path = st.session_state.current_extraction.get('pdf_path', 'test.pdf')
        
        # Try to save with enhanced duplicate detection
        try:
            result = database_service.save_complete_extraction(pdf_path, enhanced_data)
            
            if result.get('status') == 'success':
                st.session_state.current_extraction['is_approved'] = True
                st.session_state.buttons_hidden = True
                
                # Add to processed documents list
                processed_doc = {
                    'filename': st.session_state.current_extraction.get('filename', 'Unknown'),
                    'supplier': supplier_name,
                    'products_count': len(converted_products),
                    'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'currency_conversion': f"{source_currency} → GBP" if source_currency != 'GBP' else 'GBP',
                    'saved_products': result.get('saved_products', 0)
                }
                st.session_state.processed_documents.append(processed_doc)
                
                st.success("✅ Invoice approved and saved to database!")
                
                # Show save summary
                saved_products = result.get('saved_products', 0)
                supplier_id = result.get('supplier_id', 'Unknown')
                st.info(f"📊 **Save Summary:** {saved_products} products processed for supplier {supplier_id}")
                
                # Clear current extraction to remove from upload area
                st.session_state.current_extraction = None
                st.session_state.buttons_hidden = False
                st.session_state.uploader_key += 1  # Force file uploader to reset
                
                st.balloons()
            else:
                error_msg = result.get('error', result.get('message', 'Unknown error'))
                st.error(f"❌ Failed to save: {error_msg}")
                
                # Show detailed error analysis
                if 'error' in result:
                    st.write("**Error Details:**")
                    st.code(result['error'])
                    
        except Exception as save_error:
            st.error(f"❌ Save function crashed: {save_error}")
            import traceback
            st.code(traceback.format_exc())
            
    except Exception as e:
        st.error(f"❌ Approval failed: {e}")
        import traceback
        st.code(traceback.format_exc())

def handle_rejection():
    """Handle document rejection"""
    st.session_state.current_extraction['is_approved'] = False
    st.session_state.buttons_hidden = True
    st.info("❌ Invoice rejected and not saved to database")

def search_products(query):
    """Search for products with enhanced price display"""
    if not database_service:
        return "❌ Database not available"
    
    def _get_currency_symbol_helper(currency_code: str) -> str:
        """Helper function to get currency symbol"""
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'Fr', 'CNY': '¥',
            'INR': '₹', 'KRW': '₩', 'BRL': 'R$', 'RUB': '₽'
        }
        return symbols.get(currency_code, currency_code)
    
    try:
        # Check if user wants original prices
        show_original = any(keyword in query.lower() for keyword in ['original', 'buying', 'usd', 'eur', 'purchase'])
        
        # Extract search terms
        terms = query.lower().split()
        search_terms = [term for term in terms if term not in ['price', 'buying', 'original', 'show', 'me', 'the', 'of']]
        
        if not search_terms:
            return "Please specify what product you're looking for"
        
        # Search products  
        supabase = database_service.supplier_manager.supabase
        result = supabase.table('products').select(
            'id, product_name, size, category, unit_price, currency, original_price, original_currency, original_currency_symbol, conversion_rate, usage_type'
        ).execute()
        
        if not result.data:
            return "No products found in database"
        
        # Filter products that match ALL search terms
        matching_products = []
        for product in result.data:
            product_text = f"{product.get('product_name', '')} {product.get('size', '')} {product.get('category', '')}".lower()
            if all(term in product_text for term in search_terms):
                matching_products.append(product)
        
        if not matching_products:
            return f"No products found matching '{' '.join(search_terms)}'"
        
        # Get supplier info for each product
        response = f"🔍 **Found {len(matching_products)} product(s) matching '{' '.join(search_terms)}':**\n\n"
        
        # Group by product name to show multiple suppliers
        product_groups = {}
        for product in matching_products:
            name = product.get('product_name', 'Unknown')
            if name not in product_groups:
                product_groups[name] = []
            product_groups[name].append(product)
        
        for product_name, products in product_groups.items():
            response += f"**📦 {product_name}**\n"
            
            for i, product in enumerate(products, 1):
                # Extract supplier info from usage_type (since no supplier_id column)
                supplier_name = 'Unknown Supplier'
                usage_type = product.get('usage_type', '')
                if 'Supplier:' in usage_type:
                    supplier_name = usage_type.replace('Supplier:', '').strip()
                
                if show_original and product.get('original_price') and product.get('original_price') != product.get('unit_price'):
                    # Show original prices when different from GBP price
                    original_price = product.get('original_price', 0)
                    original_currency = product.get('original_currency', 'USD')
                    original_symbol = product.get('original_currency_symbol') or _get_currency_symbol_helper(original_currency)
                    gbp_price = product.get('unit_price', 0)
                    conversion_rate = product.get('conversion_rate', 1.0)
                    
                    if conversion_rate and conversion_rate != 1.0:
                        response += f"  {i}. **{supplier_name}** - {original_symbol}{original_price:.2f} ({original_currency}) → £{gbp_price:.2f} (rate: {conversion_rate:.3f})\n"
                    else:
                        response += f"  {i}. **{supplier_name}** - {original_symbol}{original_price:.2f} ({original_currency})\n"
                else:
                    # Show GBP prices
                    gbp_price = product.get('unit_price', 0)
                    response += f"  {i}. **{supplier_name}** - £{gbp_price:.2f}"
                    
                    # Show original price if different and available
                    if (product.get('original_price') and 
                        product.get('original_currency') != 'GBP' and
                        abs(product.get('original_price', 0) - gbp_price) > 0.01):
                        orig_currency = product.get('original_currency', 'USD')
                        orig_symbol = product.get('original_currency_symbol') or _get_currency_symbol_helper(orig_currency)
                        response += f" (originally {orig_symbol}{product.get('original_price', 0):.2f} {orig_currency})"
                    
                    response += "\n"
            
            response += "\n"
        
        if show_original:
            response += "💡 *Showing original invoice prices with conversion rates*"
        else:
            response += "💡 *Showing GBP converted prices. Add 'original price' to see invoice prices.*"
            
        return response
        
    except Exception as e:
        return f"❌ Search failed: {e}"

# Main Content Area
if st.session_state.show_analytics:
    # Show Analytics Dashboard
    display_analytics_dashboard()
else:
    # Show Invoice Processing Interface
    # Main UI
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Upload Invoice(s)")
    
    # Toggle between single and bulk mode
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button("📄 Single Mode", disabled=not st.session_state.bulk_mode):
            st.session_state.bulk_mode = False
            st.session_state.bulk_extractions = []
            st.rerun()
    with mode_col2:
        if st.button("📦 Bulk Mode", disabled=st.session_state.bulk_mode):
            st.session_state.bulk_mode = True
            st.session_state.current_extraction = None
            st.rerun()
    
    # Show current mode
    mode_icon = "📦" if st.session_state.bulk_mode else "📄"
    st.info(f"{mode_icon} **{('Bulk' if st.session_state.bulk_mode else 'Single')} Upload Mode**")
    
    if st.session_state.bulk_mode:
        # Bulk upload interface
        uploaded_files = st.file_uploader(
            "Upload multiple PDF invoices", 
            type=['pdf'], 
            accept_multiple_files=True,
            key=f"bulk_uploader_{st.session_state.uploader_key}"
        )
        
        if uploaded_files:
            st.write(f"📁 **{len(uploaded_files)} files selected**")
            for i, file in enumerate(uploaded_files[:5]):  # Show first 5
                st.write(f"{i+1}. {file.name}")
            if len(uploaded_files) > 5:
                st.write(f"... and {len(uploaded_files) - 5} more")
            
            if st.button("🚀 Process All Invoices", key="process_bulk"):
                process_bulk_documents(uploaded_files)
    else:
        # Single upload interface (existing)
        uploaded_file = st.file_uploader("Upload PDF invoice", type=['pdf'], key=f"uploader_{st.session_state.uploader_key}")
        
        if uploaded_file:
            if st.button("🔄 Process Invoice"):
                process_document(uploaded_file)

    with col2:
        st.subheader("🤖 AI Chat Assistant")
        
        # Chat interface with improved UX
        st.markdown("### 🤖 AI Assistant")
        
        # Example queries for new users
        if not st.session_state.messages:
            st.markdown("💭 *Ask me about products, prices, suppliers, or search for specific items...*")
            st.markdown("**Try these examples:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Show me 7oz cups", key="example1"):
                    st.session_state.pending_query = "7oz cups"
                    st.rerun()
                if st.button("💰 8oz ripple wall original prices", key="example2"):
                    st.session_state.pending_query = "8oz ripple wall original prices"
                    st.rerun()
            with col2:
                if st.button("📦 All paper cup sizes", key="example3"):
                    st.session_state.pending_query = "all paper cup sizes"
                    st.rerun()
                if st.button("🏢 Products from MAC Global", key="example4"):
                    st.session_state.pending_query = "products from MAC Global"
                    st.rerun()
        
        # Show chat history in a more visually appealing way with timestamps
        if st.session_state.messages:
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.messages[-10:]:  # Show last 10 messages
                    timestamp = message.get("timestamp", "")
                    if message["role"] == "user":
                        st.markdown(f'<div style="text-align: right; margin: 10px 0;"><div style="background: linear-gradient(90deg, #1f77b4, #87ceeb); color: white; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%;"><b>You:</b> {message["content"]}<br><small style="opacity: 0.8;">{timestamp}</small></div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="text-align: left; margin: 10px 0;"><div style="background: #f0f2f6; color: #333; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%;">{message["content"]}<br><small style="opacity: 0.6;">{timestamp}</small></div></div>', unsafe_allow_html=True)

    # Show bulk extractions if any
    if st.session_state.bulk_extractions:
        st.markdown("---")
        display_bulk_extractions()

    # Show extraction results
    if st.session_state.current_extraction:
        st.markdown("---")
        st.subheader("📋 Extracted Data Review")
        
        current = st.session_state.current_extraction
        
        if not st.session_state.buttons_hidden:
            # Show extracted data
            display_extracted_data(current['extracted'])
            
            # Decision buttons
            st.markdown("### 🔵 Decision Time")
            col1, col2 = st.columns(2)
            
            with col1:
                approve_clicked = st.button("✅ APPROVE & SAVE", type="primary", key="approve_btn")
                if approve_clicked:
                    st.write("✅ **Approve button clicked!**")
                    with st.spinner("Processing approval..."):
                        handle_approval()
                    st.rerun()
            
            with col2:
                reject_clicked = st.button("❌ REJECT", key="reject_btn")
                if reject_clicked:
                    st.write("❌ **Reject button clicked!**")
                    with st.spinner("Processing rejection..."):
                        handle_rejection()
                    st.rerun()
        
        else:
            # Show result
            if current.get('is_approved'):
                st.success("✅ **Invoice APPROVED and saved to database!**")
                st.info("You can now ask the AI chatbot about these products and their prices.")
            else:
                st.info("❌ **Invoice REJECTED and not saved.**")
            
            if st.button("🔄 Process New Invoice"):
                st.session_state.current_extraction = None
                st.session_state.buttons_hidden = False
                st.session_state.uploader_key += 1  # Reset file uploader
                st.rerun()

# Chat input outside of any containers (must be at top level)
if not st.session_state.show_analytics:
    # Enhanced chat input - submits on Enter  
    user_input = st.chat_input("💬 Ask me about products and suppliers... (Press Enter to send)")
    
    # Check for pending query from example buttons
    pending_query = st.session_state.get('pending_query', None)
    if pending_query:
        st.session_state.pending_query = None  # Clear it immediately
        user_input = pending_query  # Process it as if it was typed
    
    # Process chat input (avoid rerun loops)
    if user_input and user_input.strip():
        query_to_process = user_input.strip()
        
        try:
            # Prevent duplicate processing
            last_message = st.session_state.messages[-1] if st.session_state.messages else {}
            if last_message.get('role') == 'user' and last_message.get('content') == query_to_process:
                pass  # Skip duplicate
            else:
                # Add to recent searches (avoid duplicates and limit to 10)
                if query_to_process not in st.session_state.recent_searches:
                    st.session_state.recent_searches.append(query_to_process)
                    # Keep only last 10 searches
                    if len(st.session_state.recent_searches) > 10:
                        st.session_state.recent_searches = st.session_state.recent_searches[-10:]
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": query_to_process, "timestamp": datetime.now().strftime("%H:%M:%S")})
                
                # Get AI response with error handling
                try:
                    with st.spinner("🤖 AI is thinking..."):
                        ai_response = ai_chat_response(query_to_process)
                    
                    # Add AI response
                    st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().strftime("%H:%M:%S")})
                    
                    # Use experimental_rerun to avoid infinite loops
                    st.rerun()
                except Exception as ai_error:
                    st.error(f"🤖 AI Error: {ai_error}")
                    # Add error message to chat
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Sorry, I encountered an error: {ai_error}", "timestamp": datetime.now().strftime("%H:%M:%S")})
                    
        except Exception as general_error:
            st.error(f"💥 Chat Error: {general_error}")
            # Reset pending query to prevent stuck state
            if 'pending_query' in st.session_state:
                st.session_state.pending_query = None

    # Footer
    st.markdown("---")
    st.markdown("💡 **How to use:** Upload invoices → Review extracted data → Approve to save → Chat with AI about products and prices")