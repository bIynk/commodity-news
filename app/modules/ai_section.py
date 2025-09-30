import streamlit as st
import pandas as pd
import re
from datetime import datetime
import logging
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from modules.ai_integration import (
    TimeFrame,
    CommodityQueryOrchestrator,
    DataProcessor as AIDataProcessor,
    AIDatabase
)
from modules.calculations import compute_frequency_aware_zscore
from modules.config import DEFAULT_TIMEFRAME, AI_ZSCORE_THRESHOLD

logger = logging.getLogger(__name__)


@st.fragment
def render_ai_intelligence_section(
    ai_orchestrator,
    ai_processor,
    ai_database,
    analysis_df,
    df_data,
    ai_timeframe,
    selected_ai_commodities,
    data_last_updated,
    force_refresh=False
):
    """
    Render the AI Intelligence section as a fragment that loads independently.
    This allows the main dashboard to render immediately while AI data loads in background.
    """

    # Calculate z-scores for commodities to pass to AI orchestrator
    commodity_zscores = {}
    # Extract filtered commodities from the analysis_df (which is now filtered_df from main)
    filtered_commodities = []
    if not analysis_df.empty and not df_data.empty:
        # Get unique commodities from the filtered dataframe
        filtered_commodities = list(analysis_df['Commodities'].dropna().unique())

        # Calculate proper z-scores using historical price data
        for commodity in filtered_commodities:
            if commodity and pd.notna(commodity):
                # Get historical price series for this commodity
                commodity_data = df_data[df_data['Commodities'] == commodity].copy()
                if not commodity_data.empty:
                    # Create price series indexed by date
                    price_series = commodity_data.set_index('Date')['Price']
                    price_series.name = commodity

                    # Use frequency-aware z-score calculation with proper volatility
                    zscore_df = compute_frequency_aware_zscore(
                        price_series,
                        lookback=90,  # 90 days lookback for frequency detection
                        window=30     # 30 periods rolling window for stats
                    )

                    if not zscore_df.empty and 'ZScore' in zscore_df.columns:
                        # Get the most recent z-score
                        latest_zscore = zscore_df['ZScore'].iloc[-1]
                        if pd.notna(latest_zscore):
                            commodity_zscores[commodity] = float(latest_zscore)

    # Get cached or fresh AI data
    ai_results = None
    ai_table_data = None
    ai_news_cards = None

    with st.spinner("🤖 Loading AI intelligence..." if force_refresh else "🤖 Checking AI cache..."):
        try:
            # Use filtered commodities from the sidebar filters instead of separate AI commodity filter
            # If selected_ai_commodities is provided and not empty, use it; otherwise use filtered commodities
            commodities_to_query = selected_ai_commodities if selected_ai_commodities else filtered_commodities

            ai_results = ai_orchestrator.query_all_commodities(
                timeframe=ai_timeframe,
                force_refresh=force_refresh,
                commodity_zscores=commodity_zscores,
                selected_commodities=commodities_to_query,
                data_last_updated=data_last_updated
            )

            if ai_results:
                # Process results with weekly aggregation already done in orchestrator
                ai_table_data, ai_news_cards = ai_processor.process_query_results(ai_results)
                st.session_state.ai_last_update = datetime.now()
                st.session_state.ai_refresh = False

                # Log statistics about API usage
                total_commodities = len(ai_results)
                skipped = sum(1 for r in ai_results if r.get('skipped'))
                if skipped > 0:
                    logger.info(f"Z-score filtering saved {skipped}/{total_commodities} API calls ({skipped*100/total_commodities:.0f}%)")
            elif ai_database and not ai_database.has_write_access:
                # Only show warning if no results AND no write access
                st.warning("""
                    ⚠️ **AI data unavailable - No cached data found and cannot query new data**

                    Database write access is required to fetch new AI intelligence.
                    Please contact your administrator to:
                    1. Grant write permissions to your database user, OR
                    2. Set DC_DB_STRING_MASTER environment variable with write-enabled connection
                """)
                return  # Exit early if no data
        except Exception as e:
            st.warning(f"AI intelligence unavailable: {str(e)}")
            return  # Exit early on error

    # --- DISPLAY AI INTELLIGENCE ---
    if ai_table_data or ai_news_cards:
        st.markdown("---")
        st.markdown("""
            <h2 style='
                color: #00816D;
                font-size: 1.5rem;
                font-weight: 600;
                text-align: center;
                margin: 2rem 0;
            '>
                🤖 AI Market Intelligence
            </h2>
        """, unsafe_allow_html=True)

        # Display AI metrics
        if ai_results:
            col1, col2, col3 = st.columns(3)

            bullish_count = sum(1 for r in ai_results
                               if r.get('data', {}).get('trend') == 'bullish')
            bearish_count = sum(1 for r in ai_results
                               if r.get('data', {}).get('trend') == 'bearish')
            stable_count = sum(1 for r in ai_results
                              if r.get('data', {}).get('trend') == 'stable')

            with col1:
                st.metric("📈 Bullish Markets", bullish_count)
            with col2:
                st.metric("📉 Bearish Markets", bearish_count)
            with col3:
                st.metric("➡️ Stable Markets", stable_count)

        # Display AI Summary Table with new implementation
        if ai_table_data:
            # Convert AI data to DataFrame for AG Grid
            ai_df = pd.DataFrame(ai_table_data)

            # Process Price/Change to extract only percentage
            if 'Price/Change' in ai_df.columns:
                def extract_percentage(price_text):
                    if pd.isna(price_text) or price_text == 'N/A':
                        return 'N/A'
                    # Extract percentage from format like "↑ $1,234 (+5.2%)"
                    import re
                    match = re.search(r'\(([-+]?\d+\.?\d*%?)\)', str(price_text))
                    if match:
                        percent = match.group(1)
                        # Add % if not present
                        if not percent.endswith('%'):
                            percent += '%'
                        # Add arrow based on direction
                        if '↑' in price_text:
                            return f"↑ {percent}"
                        elif '↓' in price_text:
                            return f"↓ {percent}"
                        else:
                            return percent
                    # If no parentheses, look for standalone percentage
                    match = re.search(r'[-+]?\d+\.?\d*%', str(price_text))
                    if match:
                        return match.group(0)
                    return price_text

                ai_df['Price change'] = ai_df['Price/Change'].apply(extract_percentage)
                ai_df = ai_df.drop(columns=['Price/Change'])

            # Select and order columns as specified
            display_columns = ['Commodity', 'Trend', 'Price change', 'Key Drivers', 'Date flagged']
            available_columns = [col for col in display_columns if col in ai_df.columns]
            ai_df = ai_df[available_columns]

            # Format Key Drivers with line breaks for better readability
            if 'Key Drivers' in ai_df.columns:
                def format_key_drivers(drivers_text):
                    if pd.isna(drivers_text) or drivers_text == 'Data pending':
                        return drivers_text

                    if not isinstance(drivers_text, str):
                        return str(drivers_text)

                    # Split into individual drivers
                    drivers_list = []

                    # Common separators in order of priority
                    if '\n' in drivers_text:
                        drivers_list = drivers_text.split('\n')
                    elif ';' in drivers_text:
                        drivers_list = drivers_text.split(';')
                    elif re.search(r'\d+\.', drivers_text):
                        drivers_list = re.split(r'\d+\.', drivers_text)
                    elif '•' in drivers_text or '·' in drivers_text:
                        drivers_list = re.split(r'[•·]', drivers_text)
                    elif drivers_text.count('. ') >= 2:
                        drivers_list = drivers_text.split('. ')
                    else:
                        return drivers_text

                    # Clean and format each driver
                    formatted_drivers = []
                    for driver in drivers_list:
                        cleaned = driver.strip()
                        # Remove leading punctuation and numbers
                        cleaned = re.sub(r'^[\d\.\-\•\·\s]+', '', cleaned)
                        cleaned = cleaned.rstrip('.')
                        if cleaned:
                            formatted_drivers.append(f"• {cleaned}")

                    # Join with line breaks for display
                    return '\n'.join(formatted_drivers) if formatted_drivers else drivers_text

                ai_df['Key Drivers'] = ai_df['Key Drivers'].apply(format_key_drivers)

            # Build AG Grid configuration matching detailed price table style
            gb = GridOptionsBuilder.from_dataframe(ai_df)

            # Default column configuration
            gb.configure_default_column(
                resizable=True,
                filter=True,
                sortable=True,
                editable=False
            )

            # Configure individual columns with flexible widths and explicit font size
            gb.configure_column(
                "Commodity",
                headerName="Commodity",
                flex=1,
                minWidth=120,
                maxWidth=180,
                pinned='left',
                cellStyle={
                    'fontWeight': '500',
                    'fontSize': '14px',
                    'fontFamily': 'Manrope, sans-serif'
                }
            )

            gb.configure_column(
                "Trend",
                headerName="Trend",
                flex=0.7,
                minWidth=80,
                maxWidth=110,
                cellStyle={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontFamily': 'Manrope, sans-serif'
                }
            )

            gb.configure_column(
                "Price change",
                headerName="Price Change",
                flex=0.8,
                minWidth=90,
                maxWidth=130,
                cellStyle={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontFamily': 'Manrope, sans-serif'
                }
            )

            gb.configure_column(
                "Key Drivers",
                headerName="Key Drivers",
                flex=3.5,  # Reduced slightly to make room for Date flagged
                minWidth=350,  # Reduced minimum width
                wrapText=True,
                autoHeight=True,
                cellStyle={
                    'whiteSpace': 'pre-line',
                    'lineHeight': '1.65',
                    'fontSize': '14px',  # Direct inline font size
                    'fontFamily': 'Manrope, sans-serif'
                }
            )

            # Configure Date flagged column if present
            if 'Date flagged' in ai_df.columns:
                gb.configure_column(
                    "Date flagged",
                    headerName="Date Flagged",
                    flex=0.8,
                    minWidth=100,
                    maxWidth=120,
                    cellStyle={
                        'textAlign': 'center',
                        'fontSize': '14px',
                        'fontFamily': 'Manrope, sans-serif'
                    }
                )

            # JavaScript for conditional formatting - matching price table style with consistent font
            trend_formatter = JsCode("""
            function(params) {
                const value = params.value ? params.value.toLowerCase() : '';
                const baseStyle = {
                    'fontSize': '14px',
                    'fontFamily': 'Manrope, sans-serif',
                    'textAlign': 'center'
                };

                if (value.includes('bullish') || value.includes('📈')) {
                    return Object.assign(baseStyle, {
                        'color': '#16a34a',
                        'fontWeight': '600'
                    });
                } else if (value.includes('bearish') || value.includes('📉')) {
                    return Object.assign(baseStyle, {
                        'color': '#dc2626',
                        'fontWeight': '600'
                    });
                } else if (value.includes('stable') || value.includes('➡️')) {
                    return Object.assign(baseStyle, {
                        'color': '#6b7280'
                    });
                }
                return baseStyle;
            }
            """)

            price_change_formatter = JsCode("""
            function(params) {
                const baseStyle = {
                    'fontSize': '14px',
                    'fontFamily': 'Manrope, sans-serif',
                    'textAlign': 'center'
                };

                if (params.value && params.value.includes('↑')) {
                    return Object.assign(baseStyle, {
                        'color': '#16a34a',
                        'fontWeight': '600'
                    });
                } else if (params.value && params.value.includes('↓')) {
                    return Object.assign(baseStyle, {
                        'color': '#dc2626',
                        'fontWeight': '600'
                    });
                }
                return baseStyle;
            }
            """)

            # Apply conditional formatting
            gb.configure_column("Trend", cellStyle=trend_formatter)
            gb.configure_column("Price change", cellStyle=price_change_formatter)

            # Grid options - normal scrollable layout with dynamic row height
            gb.configure_pagination(enabled=False)
            gb.configure_grid_options(
                domLayout='normal',  # Back to normal for scrollability
                rowHeight=None,  # Let AG Grid calculate row height
                headerHeight=45,
                suppressRowTransform=True,
                enableCellTextSelection=True,
                getRowHeight=JsCode("""
                function(params) {
                    // Calculate height based on Key Drivers content with tighter spacing
                    var keyDrivers = params.data['Key Drivers'];
                    if (keyDrivers) {
                        var lines = keyDrivers.split('\\n').length;
                        return Math.max(80, 30 + (lines * 22));  // Reduced line height multiplier
                    }
                    return 80;
                }
                """)
            )

            # Custom CSS matching detailed price table styling
            st.markdown("""
                <style>
                /* AI Analysis Table - Larger, more readable font */
                div[id*="ai_analysis_grid"] .ag-theme-streamlit {
                    font-family: 'Manrope', sans-serif;
                }

                /* Header styling */
                div[id*="ai_analysis_grid"] .ag-header {
                    background-color: #f8fafc !important;
                    font-weight: 600 !important;
                    color: #374151 !important;
                }

                div[id*="ai_analysis_grid"] .ag-header-cell-label {
                    font-size: 15px !important;
                }

                /* Cell styling - much larger font for better readability */
                div[id*="ai_analysis_grid"] .ag-cell {
                    font-weight: 400 !important;
                    border-bottom: 1px solid #f3f4f6 !important;
                    font-family: 'Manrope', sans-serif !important;
                    font-size: 16px !important;
                    padding: 12px !important;
                    display: flex !important;
                    align-items: flex-start !important;
                }

                /* Force all cell values to use larger font */
                div[id*="ai_analysis_grid"] .ag-cell-value {
                    font-size: 16px !important;
                }

                /* Key Drivers column specific - force larger font */
                div[id*="ai_analysis_grid"] .ag-cell[col-id="Key Drivers"] {
                    white-space: pre-line !important;
                    line-height: 1.9 !important;
                    padding: 14px !important;
                    font-size: 16px !important;
                }

                div[id*="ai_analysis_grid"] .ag-cell[col-id="Key Drivers"] .ag-cell-value,
                div[id*="ai_analysis_grid"] .ag-cell[col-id="Key Drivers"] span {
                    font-size: 16px !important;
                    line-height: 1.9 !important;
                }

                /* Row striping */
                div[id*="ai_analysis_grid"] .ag-row-even {
                    background-color: #ffffff !important;
                }
                div[id*="ai_analysis_grid"] .ag-row-odd {
                    background-color: #f9fafb !important;
                }

                /* Hover effect */
                div[id*="ai_analysis_grid"] .ag-row:hover {
                    background-color: #f3f4f6 !important;
                }

                /* Ensure auto height works with tighter spacing */
                div[id*="ai_analysis_grid"] .ag-row {
                    min-height: 50px !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Display the AG Grid with consistent configuration
            AgGrid(
                ai_df,
                gridOptions=gb.build(),
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,  # Auto-fit columns to screen width
                height=450,  # Fixed height for scrollability
                theme='streamlit',
                update_mode='NO_UPDATE',
                key='ai_analysis_grid'
            )

        # Display AI News Cards
        if ai_news_cards:
            st.markdown("#### 📰 Recent Market Developments (AI-Curated)")

            # Create columns for news cards
            cols = st.columns(2)

            for idx, card in enumerate(ai_news_cards):  # Show all news cards
                col_idx = idx % 2
                with cols[col_idx]:
                    # Format sources as clickable links
                    source_links_html = []
                    sources = card.get('sources', [])
                    for source in sources:  # Show all sources
                        if source.startswith('http'):
                            # Extract domain name for display
                            match = re.search(r'https?://(?:www\.)?([^/]+)', source)
                            if match:
                                domain = match.group(1).split('.')[0].capitalize()
                                source_links_html.append(f'<a href="{source}" target="_blank" style="color: #007bff; text-decoration: none;">{domain}</a>')
                            else:
                                source_links_html.append(f'<a href="{source}" target="_blank" style="color: #007bff; text-decoration: none;">Source</a>')
                        else:
                            source_links_html.append(source)

                    sources_display = ' | '.join(source_links_html) if source_links_html else 'Market data'

                    # Create news card HTML with improved styling
                    # Convert newlines to HTML line breaks for proper display
                    # Display full content without truncation
                    content_html = card.get('content', '').replace('\n', '<br>')

                    # Format timestamp to YYYY-MM-DD
                    timestamp = card.get('timestamp', '')
                    if timestamp and timestamp != '':
                        try:
                            # Parse ISO format timestamp and format to YYYY-MM-DD
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d')
                        except:
                            formatted_date = timestamp
                    else:
                        formatted_date = datetime.now().strftime('%Y-%m-%d')

                    card_html = f"""
                    <div style='
                        background: white;
                        padding: 1.5rem;
                        border-radius: 8px;
                        border-left: 3px solid #00816D;
                        margin-bottom: 1rem;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    '>
                        <h4 style='color: #1e3d59; margin-bottom: 0.5rem;'>{card.get('title', 'Market Update')}</h4>
                        <div style='color: #333; line-height: 1.8; margin-bottom: 1rem;'>{content_html}</div>
                        <p style='color: #007bff; font-size: 0.9rem; margin-top: 1rem;'>📰 Sources: {sources_display}</p>
                        <small style='color: #6c757d;'>Updated: {formatted_date}</small>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

        # Footer for AI section with dynamic source info
        # Get unique sectors from AI results
        if ai_results:
            unique_sectors = set()
            for result in ai_results:
                if result.get('data', {}).get('category'):
                    unique_sectors.add(result['data']['category'])
            sector_text = f"Covering {', '.join(sorted(unique_sectors))}" if unique_sectors else "Comprehensive market coverage"
        else:
            sector_text = "Comprehensive market coverage"

        st.markdown(f"""
            <div style='text-align: center; color: #6c757d; font-size: 0.85rem; margin-top: 2rem;'>
            Data powered by Perplexity AI | Sources include sector-specific publications<br>
            {sector_text} | Focus on Vietnamese market dynamics
            </div>
        """, unsafe_allow_html=True)