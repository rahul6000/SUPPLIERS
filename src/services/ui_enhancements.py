"""
Enhanced UI/UX system for the Suppliers AI platform.
Provides modern, responsive design with improved user experience.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime

class UIThemeManager:
    """Advanced theme and styling manager"""
    
    THEMES = {
        'professional': {
            'primary_color': '#1f77b4',
            'background_color': '#ffffff',
            'secondary_background': '#f0f2f6',
            'text_color': '#262730',
            'font_family': 'Inter, sans-serif',
            'border_color': '#e0e0e0'
        },
        'dark': {
            'primary_color': '#4fc3f7',
            'background_color': '#0e1117',
            'secondary_background': '#262730',
            'text_color': '#fafafa',
            'font_family': 'Inter, sans-serif',
            'border_color': '#404040'
        },
        'corporate': {
            'primary_color': '#2e7d32',
            'background_color': '#ffffff',
            'secondary_background': '#f8f9fa',
            'text_color': '#212529',
            'font_family': 'Roboto, sans-serif',
            'border_color': '#dee2e6'
        }
    }
    
    @staticmethod
    def apply_theme(theme_name: str = 'professional'):
        """Apply selected theme with custom CSS"""
        theme = UIThemeManager.THEMES.get(theme_name, UIThemeManager.THEMES['professional'])
        
        css = f"""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap');
        
        /* Global theme variables */
        :root {{
            --primary-color: {theme['primary_color']};
            --background-color: {theme['background_color']};
            --secondary-background: {theme['secondary_background']};
            --text-color: {theme['text_color']};
            --font-family: {theme['font_family']};
            --border-color: {theme['border_color']};
        }}
        
        /* Main app styling */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            font-family: var(--font-family);
        }}
        
        /* Header styling */
        .app-header {{
            background: linear-gradient(90deg, var(--primary-color), rgba(31, 119, 180, 0.8));
            padding: 1.5rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .app-header h1 {{
            color: white;
            margin: 0;
            font-weight: 600;
            font-size: 2.5rem;
        }}
        
        .app-header p {{
            color: rgba(255,255,255,0.9);
            margin: 0;
            font-size: 1.1rem;
        }}
        
        /* Card styling */
        .metric-card {{
            background: var(--secondary-background);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: #6c757d;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-delta {{
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }}
        
        .metric-delta.positive {{
            color: #28a745;
        }}
        
        .metric-delta.negative {{
            color: #dc3545;
        }}
        
        /* Button styling */
        .stButton > button {{
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            font-family: var(--font-family);
        }}
        
        .stButton > button:hover {{
            background: rgba(31, 119, 180, 0.9);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        /* Enhanced sidebar */
        .css-1d391kg {{
            background: var(--secondary-background);
            border-right: 1px solid var(--border-color);
        }}
        
        .sidebar-section {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid var(--border-color);
        }}
        
        .sidebar-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-color);
        }}
        
        /* Status indicators */
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status-error {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .status-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        /* Table enhancements */
        .dataframe {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .dataframe th {{
            background: var(--secondary-background);
            font-weight: 600;
            padding: 1rem 0.5rem;
        }}
        
        .dataframe td {{
            padding: 0.75rem 0.5rem;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        /* Progress bars */
        .custom-progress {{
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            height: 8px;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, var(--primary-color), rgba(31, 119, 180, 0.8));
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        /* Notification styling */
        .notification {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid;
        }}
        
        .notification.success {{
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }}
        
        .notification.info {{
            background: #d1ecf1;
            border-left-color: #17a2b8;
            color: #0c5460;
        }}
        
        .notification.warning {{
            background: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }}
        
        .notification.error {{
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }}
        
        /* Loading animations */
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .loading-pulse {{
            animation: pulse 2s infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .loading-spinner {{
            animation: spin 1s linear infinite;
            display: inline-block;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            
            .app-header h1 {{
                font-size: 2rem;
            }}
            
            .metric-card {{
                padding: 1rem;
            }}
            
            .metric-value {{
                font-size: 2rem;
            }}
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def create_app_header(title: str, subtitle: str = ""):
        """Create styled application header"""
        header_html = f"""
        <div class="app-header">
            <h1>🤖 {title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)


class ComponentLibrary:
    """Library of reusable UI components"""
    
    @staticmethod
    def metric_card(label: str, value: str, delta: Optional[str] = None, delta_type: str = "positive"):
        """Create enhanced metric card"""
        delta_class = f"metric-delta {delta_type}" if delta else ""
        delta_html = f'<p class="{delta_class}">{delta}</p>' if delta else ""
        
        card_html = f"""
        <div class="metric-card">
            <p class="metric-label">{label}</p>
            <p class="metric-value">{value}</p>
            {delta_html}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    @staticmethod
    def status_badge(text: str, status: str = "info"):
        """Create status badge"""
        badge_html = f"""
        <span class="status-indicator status-{status}">
            {text}
        </span>
        """
        st.markdown(badge_html, unsafe_allow_html=True)
    
    @staticmethod
    def progress_bar(value: float, label: str = ""):
        """Create custom progress bar"""
        progress_html = f"""
        <div>
            {f'<p style="margin-bottom: 0.5rem; font-weight: 500;">{label}</p>' if label else ''}
            <div class="custom-progress">
                <div class="progress-fill" style="width: {value}%"></div>
            </div>
            <p style="text-align: right; margin-top: 0.25rem; font-size: 0.8rem; color: #6c757d;">
                {value:.1f}%
            </p>
        </div>
        """
        st.markdown(progress_html, unsafe_allow_html=True)
    
    @staticmethod
    def notification(message: str, type: str = "info", title: Optional[str] = None):
        """Create notification"""
        title_html = f"<strong>{title}</strong><br>" if title else ""
        notification_html = f"""
        <div class="notification {type}">
            {title_html}{message}
        </div>
        """
        st.markdown(notification_html, unsafe_allow_html=True)
    
    @staticmethod
    def action_button_row(buttons: List[Dict[str, Any]]):
        """Create row of action buttons"""
        cols = st.columns(len(buttons))
        
        for i, button in enumerate(buttons):
            with cols[i]:
                if st.button(
                    button['text'],
                    key=button.get('key', f"btn_{i}"),
                    help=button.get('help', ''),
                    type=button.get('type', 'secondary')
                ):
                    if 'callback' in button:
                        button['callback']()
    
    @staticmethod
    def data_table_enhanced(data: List[Dict[str, Any]], title: str = "", searchable: bool = True):
        """Create enhanced data table"""
        if not data:
            st.warning("No data to display")
            return
        
        if title:
            st.markdown(f"### {title}")
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Search functionality
        if searchable and len(df) > 5:
            search_term = st.text_input("🔍 Search", placeholder="Type to search...")
            if search_term:
                # Simple text search across all columns
                mask = df.astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                df = df[mask]
        
        # Display table with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        return df


class InteractiveComponents:
    """Advanced interactive components"""
    
    @staticmethod
    def multi_filter_sidebar(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive filter sidebar"""
        st.sidebar.markdown("## 🔧 Filters")
        
        applied_filters = {}
        
        for filter_name, filter_config in filters.items():
            with st.sidebar.container():
                st.markdown(f"### {filter_config.get('title', filter_name)}")
                
                if filter_config['type'] == 'select':
                    applied_filters[filter_name] = st.selectbox(
                        filter_config.get('label', filter_name),
                        options=filter_config['options'],
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_config['type'] == 'multiselect':
                    applied_filters[filter_name] = st.multiselect(
                        filter_config.get('label', filter_name),
                        options=filter_config['options'],
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_config['type'] == 'range':
                    applied_filters[filter_name] = st.slider(
                        filter_config.get('label', filter_name),
                        min_value=filter_config['min'],
                        max_value=filter_config['max'],
                        value=(filter_config['min'], filter_config['max']),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_config['type'] == 'date':
                    applied_filters[filter_name] = st.date_input(
                        filter_config.get('label', filter_name),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_config['type'] == 'text':
                    applied_filters[filter_name] = st.text_input(
                        filter_config.get('label', filter_name),
                        placeholder=filter_config.get('placeholder', ''),
                        key=f"filter_{filter_name}"
                    )
        
        # Filter controls
        st.sidebar.markdown("---")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Reset", key="reset_filters"):
                st.experimental_rerun()
        
        with col2:
            if st.button("✅ Apply", key="apply_filters"):
                st.success("Filters applied!")
        
        return applied_filters
    
    @staticmethod
    def dashboard_tabs(tabs: Dict[str, callable]):
        """Create dashboard with multiple tabs"""
        tab_names = list(tabs.keys())
        tab_objects = st.tabs([f"📊 {name}" for name in tab_names])
        
        for i, (tab_name, tab_function) in enumerate(tabs.items()):
            with tab_objects[i]:
                try:
                    tab_function()
                except Exception as e:
                    st.error(f"Error in {tab_name} tab: {str(e)}")
    
    @staticmethod
    def file_uploader_enhanced(
        label: str,
        accepted_types: List[str],
        multiple: bool = False,
        help_text: str = ""
    ):
        """Enhanced file uploader with drag-and-drop styling"""
        uploader_html = f"""
        <div style="
            border: 2px dashed #cccccc;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background: #fafafa;
            margin: 1rem 0;
        ">
            <h3 style="margin: 0; color: #666;">📁 {label}</h3>
            <p style="margin: 0.5rem 0; color: #888;">{help_text}</p>
            <small style="color: #aaa;">Supported: {', '.join(accepted_types)}</small>
        </div>
        """
        st.markdown(uploader_html, unsafe_allow_html=True)
        
        return st.file_uploader(
            label=f"Upload {label}",
            type=accepted_types,
            accept_multiple_files=multiple,
            label_visibility="collapsed"
        )


class MobileResponsive:
    """Mobile-responsive design utilities"""
    
    @staticmethod
    def detect_mobile() -> bool:
        """Detect if user is on mobile device (simplified)"""
        # In a real implementation, this would check user agent
        # For now, we'll use viewport width as proxy
        return False  # Mock implementation
    
    @staticmethod
    def responsive_columns(desktop_cols: int, mobile_cols: int = 1):
        """Create responsive columns"""
        if MobileResponsive.detect_mobile():
            return st.columns(mobile_cols)
        return st.columns(desktop_cols)
    
    @staticmethod
    def mobile_friendly_table(df, max_cols: int = 3):
        """Create mobile-friendly table display"""
        if MobileResponsive.detect_mobile() and len(df.columns) > max_cols:
            # Show key columns only on mobile
            key_cols = df.columns[:max_cols].tolist()
            st.dataframe(df[key_cols])
            
            with st.expander("View all columns"):
                st.dataframe(df)
        else:
            st.dataframe(df)


class UIEnhancements:
    """Main UI enhancement coordinator"""
    
    def __init__(self, theme: str = 'professional'):
        self.theme_manager = UIThemeManager()
        self.components = ComponentLibrary()
        self.interactive = InteractiveComponents()
        self.mobile = MobileResponsive()
        
        # Apply theme
        self.theme_manager.apply_theme(theme)
    
    def setup_page_config(self, title: str, icon: str = "🤖", layout: str = "wide"):
        """Setup enhanced page configuration"""
        st.set_page_config(
            page_title=title,
            page_icon=icon,
            layout=layout,
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo/issues',
                'Report a bug': 'https://github.com/your-repo/issues',
                'About': f"# {title}\nPowered by Streamlit and AI"
            }
        )
    
    def create_loading_state(self, message: str = "Loading..."):
        """Create loading state with spinner"""
        return st.spinner(f"⏳ {message}")
    
    def show_welcome_message(self):
        """Show welcome message for new users"""
        if 'welcome_shown' not in st.session_state:
            self.components.notification(
                "Welcome to the Suppliers AI Platform! 🎉 Start by uploading a document or exploring existing data.",
                type="info",
                title="Welcome!"
            )
            st.session_state.welcome_shown = True


# Global UI enhancements instance
ui_enhancements = UIEnhancements()