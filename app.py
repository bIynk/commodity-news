"""
Commodity AI Dashboard
Streamlit application for monitoring commodity markets
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api.perplexity_client import PerplexityClient, TimeFrame
from src.api.commodity_queries import CommodityQueryOrchestrator
from src.processing.data_processor import DataProcessor
from src.storage.database import CommodityDatabase
from src.utils.logging_config import setup_logging, get_logger
from src.api.health import perform_full_health_check, format_health_for_display

# Page configuration
st.set_page_config(
    page_title="Steel Sector AI Dashboard - Vietnam Market",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3d59;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #ff6b6b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4ecdc4;
        margin-bottom: 1rem;
    }
    .news-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 3px solid #ff6b6b;
    }
    .source-link {
        color: #007bff;
        text-decoration: none;
        font-size: 0.9rem;
    }
    .trend-up {
        color: #28a745;
    }
    .trend-down {
        color: #dc3545;
    }
    .trend-stable {
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None
if "query_results" not in st.session_state:
    st.session_state.query_results = None
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "1 week"

@st.cache_resource
def initialize_services():
    """Initialize all services with database integration"""
    try:
        client = PerplexityClient()
        database = CommodityDatabase()
        orchestrator = CommodityQueryOrchestrator(client, database)
        processor = DataProcessor()
        return orchestrator, processor, database
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        st.info("Please make sure PERPLEXITY_API_KEY is set in your environment or .env file")
        return None, None, None

def fetch_commodity_data(orchestrator, timeframe: TimeFrame, force_refresh: bool = False):
    """
    Fetch commodity data using daily caching strategy
    
    Data Flow:
    1. Check database for today's data
    2. If not found, query Perplexity AI
    3. Save to database for future use
    4. Cache results for the day
    """
    status_text = "🔄 Checking for today's data..." if not force_refresh else "🔄 Force refreshing data from Perplexity AI..."
    with st.spinner(status_text):
        try:
            results = orchestrator.query_all_commodities(
                timeframe=timeframe,
                force_refresh=force_refresh
            )
            
            # Show source of data
            if results and results[0].get('data', {}).get('cached_from_db'):
                st.success("✅ Using today's cached data from database")
            else:
                st.success("✅ Fresh data retrieved from Perplexity AI")
            
            return results
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return []

def display_summary_table(table_data):
    """Display the commodity summary table"""
    if not table_data:
        st.warning("No data available for display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    def style_trend(val):
        if "📈" in str(val) or "bullish" in val.lower():
            return "color: green"
        elif "📉" in str(val) or "bearish" in val.lower():
            return "color: red"
        elif "➡️" in str(val) or "stable" in val.lower():
            return "color: gray"
        return ""
    
    def style_price(val):
        if "↑" in str(val):
            return "color: green; font-weight: bold"
        elif "↓" in str(val):
            return "color: red; font-weight: bold"
        return ""
    
    styled_df = df.style.applymap(
        style_trend, subset=['Trend'] if 'Trend' in df.columns else []
    ).applymap(
        style_price, subset=['Price/Change'] if 'Price/Change' in df.columns else []
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

def display_news_cards(news_cards):
    """Display news cards in a grid layout"""
    if not news_cards:
        st.info("No recent news available")
        return
    
    # Create columns for news cards
    cols = st.columns(2)
    
    for idx, card in enumerate(news_cards):
        col_idx = idx % 2
        with cols[col_idx]:
            # Format sources as clickable links
            source_links_html = []
            for source in card['sources'][:4]:  # Limit to 4 sources
                if source.startswith('http'):
                    # Extract domain name for display
                    import re
                    match = re.search(r'https?://(?:www\.)?([^/]+)', source)
                    if match:
                        domain = match.group(1).split('.')[0].capitalize()
                        source_links_html.append(f'<a href="{source}" target="_blank" style="color: #007bff; text-decoration: none;">{domain}</a>')
                    else:
                        source_links_html.append(f'<a href="{source}" target="_blank" style="color: #007bff; text-decoration: none;">Source</a>')
                else:
                    source_links_html.append(source)
            
            sources_display = ' | '.join(source_links_html) if source_links_html else 'Market data'
            
            # Create news card HTML with clickable links
            card_html = f"""
            <div class="news-card">
                <h3>{card['title']}</h3>
                <p>{card['content'][:300]}...</p>
                <p class="source-link">📰 Sources: {sources_display}</p>
                <small>Updated: {card.get('timestamp', 'Recently')}</small>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

def display_metrics(orchestrator, results):
    """Display key metrics at the top"""
    if not results:
        return
    
    # Calculate metrics
    total_commodities = len(results)
    successful_queries = sum(1 for r in results if r.get('success'))
    bullish_count = sum(1 for r in results 
                       if r.get('data', {}).get('trend') == 'bullish')
    bearish_count = sum(1 for r in results 
                       if r.get('data', {}).get('trend') == 'bearish')
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Commodities Tracked",
            total_commodities,
            f"{successful_queries} updated"
        )
    
    with col2:
        st.metric(
            "Bullish Markets",
            bullish_count,
            "📈"
        )
    
    with col3:
        st.metric(
            "Bearish Markets",
            bearish_count,
            "📉"
        )
    
    with col4:
        if st.session_state.last_refresh:
            time_diff = datetime.now() - st.session_state.last_refresh
            mins_ago = int(time_diff.total_seconds() / 60)
            st.metric(
                "Last Update",
                f"{mins_ago} mins ago",
                "🕐"
            )
        else:
            st.metric("Last Update", "Never", "🕐")

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown(
        '<h1 class="main-header">🏗️ Steel Sector AI Dashboard - Vietnam Market</h1>',
        unsafe_allow_html=True
    )
    
    # Initialize services
    orchestrator, processor, database = initialize_services()
    
    if not orchestrator:
        st.stop()
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Dashboard Controls")
        
        # Timeframe selector
        timeframe = st.radio(
            "📅 Select Timeframe",
            options=["1 week", "1 month"],
            index=0 if st.session_state.timeframe == "1 week" else 1,
            help="Choose the analysis period for price movements"
        )
        
        if timeframe != st.session_state.timeframe:
            st.session_state.timeframe = timeframe
            st.session_state.query_results = None  # Clear cache on timeframe change
        
        # Refresh buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Get Today's Data", use_container_width=True, help="Fetch today's data (uses cache if available)"):
                st.session_state.query_results = None
                st.session_state.force_refresh = False
        
        with col2:
            if st.button("🔄 Force Refresh", use_container_width=True, help="Force new query to Perplexity AI"):
                st.session_state.query_results = None
                st.session_state.force_refresh = True
        
        with col3:
            if st.button("🗑️ Clear Cache", use_container_width=True, help="Clear all caches"):
                orchestrator.daily_cache.clear()
                orchestrator.cache_date = None
                st.session_state.query_results = None
                st.success("Cache cleared!")
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Auto-refresh every 30 minutes", value=False)
        
        # Category filter
        st.header("🔍 Filters")
        categories = orchestrator.get_categories()
        selected_categories = st.multiselect(
            "Select Categories",
            options=categories,
            default=categories
        )
        
        # Export options
        st.header("📤 Export Data")
        export_format = st.selectbox(
            "Export Format",
            options=["JSON", "CSV", "Markdown"]
        )
        
        # Health check section
        st.header("🏥 System Health")
        if st.button("Check Health", use_container_width=True):
            with st.spinner("Running health checks..."):
                health_status = perform_full_health_check()
                st.markdown(format_health_for_display(health_status))
                
                # Show raw JSON if in debug mode
                if os.getenv("DEBUG", "false").lower() == "true":
                    with st.expander("Raw Health Data"):
                        st.json(health_status)
    
    # Initialize force_refresh state
    if "force_refresh" not in st.session_state:
        st.session_state.force_refresh = False
    
    # Fetch or use cached data
    if st.session_state.query_results is None:
        force_refresh = getattr(st.session_state, 'force_refresh', False)
        results = fetch_commodity_data(orchestrator, st.session_state.timeframe, force_refresh)
        if results:
            st.session_state.query_results = results
            st.session_state.last_refresh = datetime.now()
        # Reset force_refresh flag
        st.session_state.force_refresh = False
    else:
        results = st.session_state.query_results
    
    # Process results
    if results:
        table_data, news_cards = processor.process_query_results(results)
        
        # Filter by category if needed
        if selected_categories and len(selected_categories) < len(categories):
            filtered_results = [
                r for r in results 
                if r.get('data', {}).get('category') in selected_categories
            ]
            table_data, news_cards = processor.process_query_results(filtered_results)
        
        # Display metrics
        display_metrics(orchestrator, results)
        
        # Display summary table
        st.header(f"📊 Commodity Price Summary - {st.session_state.timeframe} View")
        display_summary_table(table_data)
        
        # Display news cards
        st.header("📰 Recent Market Developments")
        display_news_cards(news_cards)
        
        # Export functionality
        if st.sidebar.button("💾 Export Data", use_container_width=True):
            export_data = processor.format_for_export(
                table_data,
                news_cards,
                export_format.lower()
            )
            
            # Create download button
            st.sidebar.download_button(
                label=f"Download {export_format}",
                data=export_data,
                file_name=f"commodity_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}",
                mime=f"application/{export_format.lower()}"
            )
        
        # Database saving is now handled automatically in the orchestrator
    
    else:
        st.info("👆 Click 'Refresh Data' to fetch the latest commodity information")
    
    # Auto-refresh logic - Non-blocking implementation
    if auto_refresh:
        # Instead of blocking with sleep, use session state to track last update
        if "last_auto_refresh" not in st.session_state:
            st.session_state.last_auto_refresh = datetime.now()
        
        # Check if 30 minutes have passed
        time_since_refresh = datetime.now() - st.session_state.last_auto_refresh
        if time_since_refresh.total_seconds() > 1800:  # 30 minutes
            st.session_state.last_auto_refresh = datetime.now()
            st.session_state.query_results = None
            st.rerun()
        else:
            # Show countdown to next refresh
            remaining = 1800 - time_since_refresh.total_seconds()
            st.sidebar.info(f"⏱️ Next auto-refresh in {int(remaining/60)} minutes")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #6c757d; font-size: 0.9rem;'>
        Data powered by Perplexity AI | Sources: Reuters, Trading Economics, Mining.com, and more<br>
        Focus on Vietnamese steel market dynamics
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    # Setup centralized logging
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/commodity_dashboard.log")
    )
    logger = get_logger(__name__)
    logger.info("Starting Commodity AI Dashboard")
    
    main()