from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from datetime import datetime
import pandas as pd
import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .services.data_loader import find_instruments
from .services.trade_processor import load_and_process_trades
from .services.metrics_calculator import (
    calculate_comprehensive_stats,
    calculate_daily_instrument_stats,
    calculate_5min_window_stats,
    calculate_day_of_week_stats
)


def clean_stats_keys(stats):
    """Replace spaces and special chars in keys with underscores for Django templates."""
    if isinstance(stats, dict):
        return {k.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('%', 'Percent'): v for k, v in stats.items()}
    elif isinstance(stats, list):
        return [clean_stats_keys(item) for item in stats]
    return stats


DEVELOPER_DEFAULT_INSTRUMENTS = [
    "gc3010",
    "gc55",
    "ho305",
    "qi305",
    "qo3010",
    "rty3015",
    "si305",
    "ym305",
    "qm55",
]


def get_filtered_data(request):
    """Helper to load and filter data based on request parameters."""
    # Load instruments
    instruments_dict = find_instruments(settings.CSV_FOLDER_PATH)
    instrument_names = list(instruments_dict.keys())
    
    # Get Date Range
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except:
            start_date = settings.DEFAULT_START_DATE
    else:
        start_date = settings.DEFAULT_START_DATE
        
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except:
            end_date = settings.DEFAULT_END_DATE
    else:
        end_date = settings.DEFAULT_END_DATE
        
    # Get Selected Instruments
    selected_instruments_list = request.GET.getlist('instruments')
    # Filter out empty strings and validate against available instruments
    selected_instruments_list = [inst for inst in selected_instruments_list if inst and inst.strip()]
    # If empty list after filtering, default to developer's instruments (if available) or all
    if not selected_instruments_list:
        default_selection = [inst for inst in DEVELOPER_DEFAULT_INSTRUMENTS if inst in instrument_names]
        selected_instruments_list = default_selection or instrument_names
    # Validate selected instruments - only include instruments that actually exist
    selected_instruments_list = [name for name in selected_instruments_list if name in instrument_names]
    # If no valid instruments selected, default to developer's instruments (if available) or all
    if not selected_instruments_list:
        default_selection = [inst for inst in DEVELOPER_DEFAULT_INSTRUMENTS if inst in instrument_names]
        selected_instruments_list = default_selection or instrument_names
        
    # Get Per-Instrument Filters
    instrument_filters = {}
    instrument_contracts = {}
    for name in instrument_names:
        if name in selected_instruments_list:
            # Direction
            filter_param = request.GET.get(f'filter_{name}', 'All')
            instrument_filters[name] = filter_param
            
            # Contracts
            contract_param = request.GET.get(f'contracts_{name}', '1')
            try:
                instrument_contracts[name] = int(contract_param)
            except:
                instrument_contracts[name] = 1
                
    # Process Trades
    try:
        start_str = start_date.strftime('%d/%m/%Y')
        end_str = end_date.strftime('%d/%m/%Y')
        
        print(f"DEBUG: Selected instruments: {selected_instruments_list}")
        print(f"DEBUG: Date range: {start_str} to {end_str}")
        print(f"DEBUG: Available instruments: {list(instruments_dict.keys())}")
        
        instruments_data, combined_df = load_and_process_trades(
            instruments_dict,
            selected_instruments_list,
            instrument_filters,
            instrument_contracts,
            start_str,
            end_str
        )
        
        print(f"DEBUG: Loaded {len(combined_df)} trades from {len(instruments_data)} instruments")
    except Exception as e:
        print(f"Error processing trades: {e}")
        import traceback
        traceback.print_exc()
        instruments_data = {}
        combined_df = pd.DataFrame()
        
    return {
        'instruments_data': instruments_data,
        'combined_df': combined_df,
        'selected_instruments': selected_instruments_list,
        'start_date': start_date,
        'end_date': end_date,
        'instrument_names': instrument_names
    }


def home(request):
    """Dashboard home page."""
    data = get_filtered_data(request)
    combined_df = data['combined_df']
    
    # Calculate stats
    combined_stats = {}
    avg_weekly_profit = 0
    weeks_trading = 0
    equity_curve_json = 'null'
    
    if len(combined_df) > 0:
        stats, _, _ = calculate_comprehensive_stats(combined_df, 'ALL INSTRUMENTS')
        combined_stats = clean_stats_keys(stats)
        
        first_trade = pd.to_datetime(combined_df['Entry time']).min()
        last_trade = pd.to_datetime(combined_df['Entry time']).max()
        days_trading = (last_trade - first_trade).days
        weeks_trading = max(days_trading / 7, 1)
        avg_weekly_profit = combined_stats.get('Total_Net_Profit', 0) / weeks_trading
        
        # Prepare Equity Curve Data
        try:
            df_charts = combined_df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_charts['Exit time']):
                df_charts['Exit time'] = pd.to_datetime(df_charts['Exit time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            
            df_charts = df_charts.sort_values('Exit time')
            df_charts['Cumulative_Profit'] = df_charts['Profit'].cumsum()
            
            # Equity Curve
            equity_curve_data = {
                'x': df_charts['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'y': df_charts['Cumulative_Profit'].tolist()
            }
            equity_curve_json = json.dumps(equity_curve_data)
        except Exception as e:
            print(f"Error preparing equity curve: {e}")
        
    return render(request, 'dashboard/home.html', {
        'user': request.user,
        'combined_stats': combined_stats,
        'avg_weekly_profit': avg_weekly_profit,
        'weeks_trading': weeks_trading,
        'total_trades': len(combined_df),
        'selected_instruments': data['selected_instruments'],
        'equity_curve_json': equity_curve_json,
    })


# Base color palettes for different instrument types (Luxury Palette)
INSTRUMENT_BASE_COLORS = {
    'NQ': ['#1A5276', '#2E4053', '#154360'],    # Deep Blues (Nasdaq)
    'ES': ['#1F618D', '#21618C', '#1B4F72'],    # Dark Blues (S&P)
    'CL': ['#2C3E50', '#34495E', '#1C2833'],    # Dark Slates (Crude Oil)
    'GC': ['#D4AF37', '#B8860B', '#DAA520'],    # Golds
    'RTY': ['#7D6608', '#9A7D0A', '#6E2C00'],   # Bronzes (Russell)
    'YM': ['#1F618D', '#2874A6', '#3498DB'],    # Blues (Dow - replaced Purple)
    'HO': ['#A93226', '#922B21', '#78281F'],    # Dark Reds (Heating Oil)
    'SI': ['#E5E4E2', '#BDC3C7', '#95A5A6'],    # Silvers
    'RB': ['#922B21', '#7B241C', '#641E16'],    # Burgundies (Gasoline)
    'QI': ['#117A65', '#138D75', '#16A085'],    # Teals (replaced Violet)
    'QO': ['#117864', '#0E6655', '#0B5345'],    # Dark Teals
    'QM': ['#148F77', '#117A65', '#0E6655'],    # Sea Greens
}

def get_instrument_color(name):
    """Get unique color for each instrument+setup combination."""
    # Try to find base instrument symbol
    base_symbol = None
    for symbol in INSTRUMENT_BASE_COLORS.keys():
        if symbol in name.upper():
            base_symbol = symbol
            break
    
    if base_symbol and base_symbol in INSTRUMENT_BASE_COLORS:
        # Get the palette for this instrument
        palette = INSTRUMENT_BASE_COLORS[base_symbol]
        
        # Use hash of full name to pick a color from the palette
        # This ensures same name always gets same color
        hash_val = hash(name)
        color_index = abs(hash_val) % len(palette)
        return palette[color_index]
    
    # Fallback: generate a consistent color based on full name hash
    hash_val = hash(name)
    r = (hash_val & 0xFF0000) >> 16
    g = (hash_val & 0x00FF00) >> 8
    b = hash_val & 0x0000FF
    
    # Adjust to ensure colors are in luxury range (darker, more muted)
    r = min(max(r, 40), 180)
    g = min(max(g, 40), 180)
    b = min(max(b, 40), 180)
    
    return f"#{r:02x}{g:02x}{b:02x}"

def performance(request):
    """Performance Overview page."""
    data = get_filtered_data(request)
    combined_df = data['combined_df']
    instruments_data = data['instruments_data']
    
    combined_stats = {}
    instruments_stats = {}
    avg_weekly_profit = 0
    
    # Chart Data for Plotly (initialize as empty arrays/objects, not 'null' string)
    plotly_equity_json = '[]'
    plotly_drawdown_json = '[]'
    plotly_monthly_json = '{}'
    plotly_timeline_json = '[]'
    
    if len(combined_df) > 0:
        stats, _, _ = calculate_comprehensive_stats(combined_df, 'ALL INSTRUMENTS')
        combined_stats = clean_stats_keys(stats)
        
        # Calculate Avg Weekly Profit
        first_trade = pd.to_datetime(combined_df['Entry time']).min()
        last_trade = pd.to_datetime(combined_df['Entry time']).max()
        days_trading = (last_trade - first_trade).days
        weeks_trading = max(days_trading / 7, 1)
        avg_weekly_profit = combined_stats.get('Total_Net_Profit', 0) / weeks_trading
        
        # Calculate per-instrument stats
        for name, idata in instruments_data.items():
            df = idata['trades']
            stats, _, _ = calculate_comprehensive_stats(df, name)
            instruments_stats[name] = clean_stats_keys(stats)
            
        # --- Prepare Plotly Data ---
        try:
            # Common Date Processing
            df_charts = combined_df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_charts['Exit time']):
                df_charts['Exit time'] = pd.to_datetime(df_charts['Exit time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            df_charts = df_charts.sort_values('Exit time')
            
            # 1. Equity Curves (Per Instrument + Combined)
            equity_traces = []
            
            # Per Instrument
            for name, idata in instruments_data.items():
                idf = idata['trades'].copy()
                if not pd.api.types.is_datetime64_any_dtype(idf['Exit time']):
                    idf['Exit time'] = pd.to_datetime(idf['Exit time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                idf = idf.sort_values('Exit time')
                idf['Cumulative_Profit'] = idf['Profit'].cumsum()
                
                equity_traces.append({
                    'name': name,
                    'x': idf['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'y': idf['Cumulative_Profit'].tolist(),
                    'color': get_instrument_color(name),
                    'type': 'scatter',
                    'mode': 'lines',
                    'line': {'width': 2}
                })
                
            # Combined
            df_charts['Cumulative_Profit'] = df_charts['Profit'].cumsum()
            equity_traces.append({
                'name': 'COMBINED',
                'x': df_charts['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'y': df_charts['Cumulative_Profit'].tolist(),
                'color': '#D4AF37', # Luxury Gold
                'type': 'scatter',
                'mode': 'lines',
                'line': {'width': 3, 'dash': 'dash'}
            })
            plotly_equity_json = json.dumps(equity_traces)
            
            # 2. Drawdown Curves (Per Instrument + Combined)
            drawdown_traces = []
            
            # Per Instrument
            for name, idata in instruments_data.items():
                idf = idata['trades'].copy()
                if not pd.api.types.is_datetime64_any_dtype(idf['Exit time']):
                    idf['Exit time'] = pd.to_datetime(idf['Exit time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                idf = idf.sort_values('Exit time')
                idf['Cumulative'] = idf['Profit'].cumsum()
                idf['Running_Max'] = idf['Cumulative'].expanding().max()
                idf['Drawdown'] = idf['Cumulative'] - idf['Running_Max']
                
                drawdown_traces.append({
                    'name': name,
                    'x': idf['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'y': idf['Drawdown'].tolist(),
                    'color': get_instrument_color(name),
                    'type': 'scatter',
                    'mode': 'lines',
                    'fill': 'tozeroy',
                    'line': {'width': 1}
                })
                
            # Combined
            df_charts['Running_Max'] = df_charts['Cumulative_Profit'].expanding().max()
            df_charts['Drawdown'] = df_charts['Cumulative_Profit'] - df_charts['Running_Max']
            drawdown_traces.append({
                'name': 'COMBINED',
                'x': df_charts['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'y': df_charts['Drawdown'].tolist(),
                'color': '#C0392B', # Deep Luxury Red
                'type': 'scatter',
                'mode': 'lines',
                'fill': 'tozeroy',
                'line': {'width': 2}
            })
            plotly_drawdown_json = json.dumps(drawdown_traces)
            
            # 3. Monthly Performance (3 Panels)
            monthly_df = df_charts.set_index('Exit time').resample('ME').agg({
                'Profit': ['sum', 'count', 'mean']
            })
            monthly_df.columns = ['sum', 'count', 'mean']
            monthly_data = {
                'x': monthly_df.index.strftime('%Y-%m').tolist(),
                'profit': monthly_df['sum'].tolist(),
                'count': monthly_df['count'].tolist(),
                'avg': monthly_df['mean'].tolist()
            }
            plotly_monthly_json = json.dumps(monthly_data)
            
            # 4. Trade Timeline (Cumulative + Markers)
            timeline_traces = []
            
            # Cumulative Line
            timeline_traces.append({
                'name': 'Cumulative Profit',
                'x': df_charts['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'y': df_charts['Cumulative_Profit'].tolist(),
                'color': '#ffffff',
                'type': 'scatter',
                'mode': 'lines',
                'line': {'width': 2}
            })
            
            # Winners
            wins = df_charts[df_charts['Profit'] > 0]
            if not wins.empty:
                timeline_traces.append({
                    'name': f'Winners ({len(wins)})',
                    'x': wins['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'y': wins['Cumulative_Profit'].tolist(),
                    'customdata': wins['Profit'].tolist(),
                    'color': '#2ECC71', # Green for Wins
                    'type': 'scatter',
                    'mode': 'markers',
                    'marker': {'symbol': 'triangle-up', 'size': 12}
                })
                
            # Losers
            losses = df_charts[df_charts['Profit'] < 0]
            if not losses.empty:
                timeline_traces.append({
                    'name': f'Losers ({len(losses)})',
                    'x': losses['Exit time'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                    'y': losses['Cumulative_Profit'].tolist(),
                    'customdata': losses['Profit'].tolist(),
                    'color': '#C0392B', # Red for Losses
                    'type': 'scatter',
                    'mode': 'markers',
                    'marker': {'symbol': 'triangle-down', 'size': 12}
                })
            plotly_timeline_json = json.dumps(timeline_traces)
            
            # Advanced Stats (Time to Recover, Flat Period)
            try:
                # Calculate Drawdown Durations
                # We need the index (Exit time) to calculate durations
                dd_df = df_charts.set_index('Exit time').sort_index()
                
                # Identify peaks (where drawdown is 0)
                # Drawdown is 0 when Cumulative_Profit == Running_Max
                # Note: floating point comparison safety
                is_peak = (dd_df['Cumulative_Profit'] >= dd_df['Running_Max'] - 0.0001)
                
                # Get timestamps of peaks
                peak_times = dd_df.index[is_peak].to_series()
                
                # If we have peaks, calculate duration between them
                if len(peak_times) > 1:
                    # Calculate time differences between consecutive peaks
                    # This isn't quite right for "Time to Recover" - that's time from Peak to New Peak
                    # But if we filter for only the times we made a NEW high...
                    
                    # Actually, a better way for "Time to Recover" (Drawdown Duration):
                    # 1. Find all peaks
                    # 2. For each peak, find time to next peak
                    
                    # Let's use a simpler approach for "Flat Periods" (Time between new highs)
                    # Get only the records that are new highs
                    new_highs = dd_df[is_peak].index.to_series()
                    
                    # Calculate diff between new highs
                    flat_periods = new_highs.diff().dropna()
                    
                    if not flat_periods.empty:
                        combined_stats['Max_Time_to_Recover'] = str(flat_periods.max()).replace('0 days ', '')
                        combined_stats['Max_Flat_Period'] = str(flat_periods.max()).replace('0 days ', '')
                        combined_stats['Avg_Flat_Period'] = str(flat_periods.mean()).split('.')[0].replace('0 days ', '')
                    else:
                        combined_stats['Max_Time_to_Recover'] = "0:00:00"
                        combined_stats['Max_Flat_Period'] = "0:00:00"
                        combined_stats['Avg_Flat_Period'] = "0:00:00"
                else:
                    combined_stats['Max_Time_to_Recover'] = "N/A"
                    combined_stats['Max_Flat_Period'] = "N/A"
                    combined_stats['Avg_Flat_Period'] = "N/A"
                    
            except Exception as e:
                print(f"Error calculating advanced stats: {e}")
                combined_stats['Max_Time_to_Recover'] = "N/A"
                combined_stats['Max_Flat_Period'] = "N/A"
                combined_stats['Avg_Flat_Period'] = "N/A"
            
        except Exception as e:
            print(f"Error preparing Plotly charts: {e}")

    return render(request, 'dashboard/performance.html', {
        'user': request.user,
        'combined_stats': combined_stats,
        'instruments_stats': instruments_stats,
        'avg_weekly_profit': avg_weekly_profit,
        'total_trades': len(combined_df),
        'selected_instruments': data['selected_instruments'],
        'plotly_equity_json': plotly_equity_json,
        'plotly_drawdown_json': plotly_drawdown_json,
        'plotly_monthly_json': plotly_monthly_json,
        'plotly_timeline_json': plotly_timeline_json,
    })


def privacy(request):
    """Static Privacy Policy page."""
    return render(request, 'dashboard/privacy.html', {'user': request.user})


def terms(request):
    """Static Terms of Service page."""
    return render(request, 'dashboard/terms.html', {'user': request.user})


def purchase(request):
    """Purchase/Rental page with real performance stats."""
    print("=" * 50)
    print("PURCHASE VIEW CALLED!")
    print("=" * 50)
    
    # Load default data (all instruments, full date range)
    data = get_filtered_data(request)
    combined_df = data['combined_df']
    
    # Initialize with None so template defaults work
    total_net_profit = None
    win_rate = None
    total_trades = None
    avg_weekly_profit = None
    
    if len(combined_df) > 0:
        try:
            stats, _, _ = calculate_comprehensive_stats(combined_df, 'ALL INSTRUMENTS')
            
            # Format Total Net Profit
            if 'Total Net Profit' in stats:
                total_net_profit = f"${stats['Total Net Profit']:,.0f}"
            
            # Format Win Rate
            if 'Percent Profitable' in stats:
                win_rate = f"{stats['Percent Profitable']:.1f}"
            
            # Total Trades
            total_trades = f"{len(combined_df):,}"
            
            # Calculate Average Weekly Profit (match Performance Overview logic: use 'Entry time')
            if not combined_df.empty and 'Entry time' in combined_df.columns:
                combined_df['Entry time'] = pd.to_datetime(combined_df['Entry time'])
                date_range = (combined_df['Entry time'].max() - combined_df['Entry time'].min()).days
                weeks = max(date_range / 7, 1)
                avg_weekly = stats.get('Total Net Profit', 0) / weeks
                avg_weekly_profit = f"${avg_weekly:,.0f}"
            
            # Debug output
            print(f"Purchase page stats loaded: Profit={total_net_profit}, WinRate={win_rate}, Trades={total_trades}, Weekly={avg_weekly_profit}")
            
        except Exception as e:
            print(f"Error calculating purchase stats: {e}")
    else:
        print("No trades found for purchase page")
    
    return render(request, 'dashboard/purchase.html', {
        'user': request.user,
        'total_net_profit': total_net_profit,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'avg_weekly_profit': avg_weekly_profit,
    })


def metrics(request):
    """Summary Metrics page."""
    data = get_filtered_data(request)
    combined_df = data['combined_df']
    instruments_data = data['instruments_data']
    
    daily_stats = {}
    window_stats = {}
    instruments_stats = {}
    combined_stats = {}
    metrics_comparison_json = 'null'
    
    if len(combined_df) > 0:
        daily_stats, _ = calculate_daily_instrument_stats(combined_df)
        window_stats, _ = calculate_5min_window_stats(combined_df)
        stats, _, _ = calculate_comprehensive_stats(combined_df, 'ALL INSTRUMENTS')
        combined_stats = clean_stats_keys(stats)
        
        # Calculate per-instrument stats
        comparison_data = []
        for name, idata in instruments_data.items():
            df = idata['trades']
            stats, _, _ = calculate_comprehensive_stats(df, name)
            cleaned_stats = clean_stats_keys(stats)
            instruments_stats[name] = cleaned_stats
            
        
        # Generate Plotly Charts (matching Streamlit)
        key_metrics_chart_html = ''
        performance_comparison_chart_html = ''
        profit_chart_html = '' # No longer used, but keep for now
        drawdown_chart_html = '' # No longer used, but keep for now
        winrate_chart_html = '' # No longer used, but keep for now
        winloss_chart_html = ''
        avgtrade_chart_html = ''
        winloss_ratio_chart_html = ''
        
        try:
            # Initialize chart variables at the start
            # winloss_chart_html = '' # Redundant, already initialized above
            # winloss_ratio_chart_html = '' # Redundant, already initialized above
            
            instruments = list(instruments_stats.keys())
            
            if not instruments:
                # No instruments, create empty charts
                winloss_chart_html = '<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">No instruments available</div>'
                winloss_ratio_chart_html = '<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">No instruments available</div>'
            else:
                colors = [get_instrument_color(name) for name in instruments]
                
                # Professional chart layout template - enhanced styling
                # Note: Don't include yaxis or height here to avoid conflicts when we need to customize them
                chart_layout = dict(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(
                        color='#cbd5e1',
                        family='DM Sans, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                        size=12
                    ),
                    margin=dict(t=60, b=60, l=70, r=30),
                    xaxis=dict(
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        gridwidth=1,
                        zeroline=False,
                        showline=True,
                        linecolor='rgba(148, 163, 184, 0.2)',
                        linewidth=1,
                        tickfont=dict(color='#94a3b8', size=11, family='DM Sans, sans-serif'),
                        title=dict(font=dict(color='#e2e8f0', size=13, family='DM Sans, sans-serif')),
                        showgrid=True,
                        griddash='dot',
                        ticklen=5,
                        tickwidth=1,
                        tickcolor='rgba(148, 163, 184, 0.3)',
                        tickangle=-45
                    ),
                    hoverlabel=dict(
                        bgcolor='rgba(15, 23, 42, 0.95)',
                        bordercolor='rgba(76, 175, 80, 0.5)',
                        font=dict(family='DM Sans, sans-serif', size=12, color='#f8fafc'),
                        namelength=20
                    )
                )
                
                # Base yaxis config that can be extended (without title - each chart sets its own)
                base_yaxis = dict(
                    gridcolor='rgba(148, 163, 184, 0.15)',
                    gridwidth=1,
                    zeroline=True,
                    zerolinecolor='rgba(148, 163, 184, 0.3)',
                    zerolinewidth=1,
                    showline=True,
                    linecolor='rgba(148, 163, 184, 0.2)',
                    linewidth=1,
                    tickfont=dict(color='#94a3b8', size=11, family='DM Sans, sans-serif'),
                    showgrid=True,
                    griddash='dot',
                    ticklen=5,
                    tickwidth=1,
                    tickcolor='rgba(148, 163, 184, 0.3)'
                )
                
                # Initialize chart variables here too for safety
                # if not winloss_chart_html: # Redundant
                #     winloss_chart_html = ''
                # if not winloss_ratio_chart_html: # Redundant
                #     winloss_ratio_chart_html = ''
                
                # 1. Key Metrics Comparison (4x2 Subplots)
                metrics_keys = ['Total_Net_Profit', 'Max_Drawdown', 'Number_of_Trades', 'Percent_Profitable', 
                                'Max_Time_to_Recover', 'Max_Flat_Period', 'Avg_Flat_Period', 'Time_in_Market_Percent']
                metrics_titles = ['Total Net Profit', 'Max Drawdown', 'Number of Trades', 'Percent Profitable', 
                                  'Max Time to Recover', 'Max Flat Period', 'Avg Flat Period', 'Time in Market %']
                
                fig_key = make_subplots(
                    rows=4, cols=2,
                    subplot_titles=metrics_titles,
                    vertical_spacing=0.15,
                    horizontal_spacing=0.1
                )
                
                for idx, metric_key in enumerate(metrics_keys):
                    row = (idx // 2) + 1
                    col = (idx % 2) + 1
                    
                    values = []
                    labels = []
                    bar_colors = []
                    text_labels = []
                    
                    # Per-instrument bars
                    for name in instruments:
                        if metric_key in instruments_stats[name]:
                            val = instruments_stats[name][metric_key]
                            
                            # Handle Timedelta
                            if isinstance(val, pd.Timedelta):
                                values.append(val.total_seconds() / 86400) # Days
                                days = val.days
                                hours = val.seconds // 3600
                                text_labels.append(f"{days}d {hours}h")
                            else:
                                values.append(val)
                                if metric_key == 'Time_in_Market_Percent':
                                    text_labels.append(f"{val:.2f}%")
                                elif metric_key in ['Total_Net_Profit', 'Max_Drawdown']:
                                    text_labels.append(f"${val:,.0f}")
                                elif isinstance(val, (int, float)):
                                    text_labels.append(f"{val:,.2f}")
                                else:
                                    text_labels.append(str(val))
                                    
                            labels.append(name)
                            bar_colors.append(get_instrument_color(name))
                    
                    # Append COMBINED bar
                    if combined_stats and metric_key in combined_stats:
                        val = combined_stats[metric_key]
                        
                        if isinstance(val, pd.Timedelta):
                            values.append(val.total_seconds() / 86400)
                            days = val.days
                            hours = val.seconds // 3600
                            text_labels.append(f"{days}d {hours}h")
                        else:
                            values.append(val)
                            if metric_key == 'Time_in_Market_Percent':
                                text_labels.append(f"{val:.2f}%")
                            elif metric_key in ['Total_Net_Profit', 'Max_Drawdown']:
                                text_labels.append(f"${val:,.0f}")
                            elif isinstance(val, (int, float)):
                                text_labels.append(f"{val:,.2f}")
                            else:
                                text_labels.append(str(val))
                                
                        labels.append('COMBINED')
                        if metric_key == 'Total_Net_Profit':
                            bar_colors.append('orange' if val >= 0 else 'red')
                        elif metric_key == 'Max_Drawdown':
                            bar_colors.append('darkred' if val < 0 else 'gray')
                        else:
                            bar_colors.append('orange')
                    
                    if values:
                        fig_key.add_trace(
                            go.Bar(
                                x=labels, y=values, name=metrics_titles[idx],
                                marker_color=bar_colors,
                                text=text_labels, textposition='auto',
                                showlegend=False
                            ),
                            row=row, col=col
                        )
                        
                        # Update y-axis title for time metrics
                        if metric_key in ['Max_Time_to_Recover', 'Max_Flat_Period', 'Avg_Flat_Period']:
                            fig_key.update_yaxes(title_text="Days", row=row, col=col)

                fig_key.update_layout(**chart_layout)
                fig_key.update_layout(height=1200, title_text="Key Metrics Comparison")
                key_metrics_chart_html = fig_key.to_html(include_plotlyjs=False, div_id='keyMetricsChart')
                
                # 2. Performance Comparison (4 metrics in 2x2 grid - horizontal bars)
                comparison_metrics = ['Total_Net_Profit', 'Profit_Factor', 'Percent_Profitable', 'Number_of_Trades']
                
                fig_perf_comp = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[m.replace('_', ' ') for m in comparison_metrics],
                    vertical_spacing=0.15,
                    horizontal_spacing=0.1
                )
                
                for idx, metric in enumerate(comparison_metrics):
                    row = (idx // 2) + 1
                    col = (idx % 2) + 1
                    
                    values = []
                    labels_list = []
                    bar_colors = []
                    
                    print(f"DEBUG Performance Comparison - Processing metric: {metric}")
                    for name in instruments:
                        val = instruments_stats[name].get(metric, 0)
                        print(f"  {name}: {metric} = {val}")
                        if val is not None and val != float('inf'):
                            values.append(val)
                            labels_list.append(name)
                            bar_colors.append(colors[instruments.index(name)])
                    
                    print(f"  Collected {len(values)} values: {values}")
                    if values:
                        text_labels = [f'${v:,.0f}' if metric == 'Total_Net_Profit' else f'{v:.2f}' for v in values]
                        fig_perf_comp.add_trace(
                            go.Bar(
                                x=values, 
                                y=labels_list, 
                                orientation='h',
                                marker=dict(
                                    color=bar_colors,
                                    line=dict(color='rgba(255, 255, 255, 0.1)', width=1),
                                    opacity=0.85
                                ),
                                text=text_labels,
                                textfont=dict(color='#f8fafc', size=10, family='DM Sans, sans-serif'),
                                textposition='auto',
                                showlegend=False,
                                hovertemplate='<b>%{y}</b><br>Value: <b>%{x:,.2f}</b><extra></extra>'
                            ),
                            row=row, col=col
                        )
                
                fig_perf_comp.update_layout(
                    height=750,
                    title=dict(
                        text="Performance Comparison",
                        font=dict(family='DM Sans, sans-serif', size=22, color='#f8fafc', weight=600),
                        x=0.5,
                        xanchor='center',
                        pad=dict(t=10, b=20)
                    ),
                    showlegend=False,
                    margin=dict(t=80, b=60, l=80, r=30),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cbd5e1', family='DM Sans, sans-serif', size=12),
                    hovermode='x unified'
                )
                # Update all axes for subplots - simpler approach
                fig_perf_comp.update_xaxes(
                    tickfont=dict(color='#94a3b8', size=10, family='DM Sans, sans-serif')
                )
                fig_perf_comp.update_yaxes(
                    tickfont=dict(color='#94a3b8', size=10, family='DM Sans, sans-serif')
                )
                performance_comparison_chart_html = fig_perf_comp.to_html(include_plotlyjs=False, div_id='performanceComparisonChart')
            
                # 3. Net Profit Comparison (simple bar chart)
                profits = [instruments_stats[name].get('Total_Net_Profit', 0) for name in instruments]
                fig_profit = go.Figure(data=[
                    go.Bar(x=instruments, y=profits, marker_color=colors,
                           text=[f'${p:,.0f}' for p in profits], textposition='auto')
                ])
                fig_profit.update_layout(**chart_layout, title='Net Profit by Instrument')
                profit_chart_html = fig_profit.to_html(include_plotlyjs=False, div_id='profitChart')
                
                # 4. Max Drawdown Comparison
                drawdowns = [instruments_stats[name].get('Max_Drawdown', 0) for name in instruments]
                fig_dd = go.Figure(data=[
                    go.Bar(x=instruments, y=drawdowns, marker_color=colors,
                           text=[f'${d:,.0f}' for d in drawdowns], textposition='auto')
                ])
                fig_dd.update_layout(**chart_layout, title='Max Drawdown by Instrument')
                drawdown_chart_html = fig_dd.to_html(include_plotlyjs=False, div_id='drawdownChart')
                
                # 5. Win Rate Comparison
                winrates = [instruments_stats[name].get('Percent_Profitable', 0) for name in instruments]
                fig_wr = go.Figure(data=[
                    go.Bar(x=instruments, y=winrates, marker_color=colors,
                           text=[f'{w:.1f}%' for w in winrates], textposition='auto')
                ])
                fig_wr.update_layout(
                    **{k: v for k, v in chart_layout.items() if k != 'yaxis'}, 
                    title='Win Rate by Instrument', 
                    yaxis=dict(**base_yaxis, range=[0, 100])
                )
                winrate_chart_html = fig_wr.to_html(include_plotlyjs=False, div_id='winRateChart')
                
                # 6. Win/Loss Count (Grouped Bar - matching Streamlit exactly)
                wins = []
                losses = []
                labels = []
                
                for name in instruments:
                    try:
                        win_count = instruments_stats[name].get('Number_of_Winning_Trades', 0) or 0
                        loss_count = instruments_stats[name].get('Number_of_Losing_Trades', 0) or 0
                        # Convert to int to avoid any type issues
                        win_count = int(win_count) if win_count else 0
                        loss_count = int(loss_count) if loss_count else 0
                        wins.append(win_count)
                        losses.append(loss_count)
                        labels.append(name)
                    except (KeyError, TypeError, ValueError) as e:
                        print(f"Error processing {name} for win/loss: {e}")
                        wins.append(0)
                        losses.append(0)
                        labels.append(name)
                
                # Always generate chart, even if all values are zero
                fig_wl = go.Figure()
                if labels:  # Only add traces if we have labels
                    fig_wl.add_trace(go.Bar(
                        x=labels,
                        y=wins,
                        name='Winners',
                        marker=dict(
                            color='#4CAF50',
                            line=dict(color='#66BB6A', width=1),
                            opacity=0.85
                        ),
                        hovertemplate='<b>%{x}</b><br>Winners: <b>%{y}</b><extra></extra>'
                    ))
                    fig_wl.add_trace(go.Bar(
                        x=labels,
                        y=losses,
                        name='Losers',
                        marker=dict(
                            color='#f44336',
                            line=dict(color='#E57373', width=1),
                            opacity=0.85
                        ),
                        hovertemplate='<b>%{x}</b><br>Losers: <b>%{y}</b><extra></extra>'
                    ))
                # Create xaxis dict without title to avoid conflict
                xaxis_config = chart_layout['xaxis'].copy()
                if 'title' in xaxis_config:
                    del xaxis_config['title']
                xaxis_config['title'] = 'Instrument'
                
                # Create yaxis dict without title to avoid conflict
                yaxis_config = base_yaxis.copy()
                if 'title' in yaxis_config:
                    del yaxis_config['title']
                yaxis_config['title'] = 'Number of Trades'
                
                fig_wl.update_layout(
                    **{k: v for k, v in chart_layout.items() if k != 'xaxis'},
                    title=dict(
                        text='Win/Loss Count by Instrument',
                        font=dict(family='DM Sans, sans-serif', size=20, color='#f8fafc', weight=600),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=xaxis_config,
                    yaxis=yaxis_config,
                    barmode='group',
                    height=450,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5,
                        font=dict(color='#e2e8f0', size=12, family='DM Sans, sans-serif')
                    )
                )
                winloss_chart_html = fig_wl.to_html(include_plotlyjs=False, div_id='winLossCountChart')
                
                # 7. Avg Trade Comparison
                avg_trades = [instruments_stats[name].get('Avg_Trade', 0) for name in instruments]
                fig_avg = go.Figure(data=[
                    go.Bar(x=instruments, y=avg_trades, marker_color=colors,
                           text=[f'${a:,.0f}' for a in avg_trades], textposition='auto')
                ])
                fig_avg.update_layout(**chart_layout, title='Average Trade by Instrument')
                avgtrade_chart_html = fig_avg.to_html(include_plotlyjs=False, div_id='avgWinLossChart')
                
                # 8. Win/Loss Ratio (Average Win/Average Loss Ratio - matching Streamlit exactly)
                ratios = []
                ratio_labels = []
                ratio_colors = []
                
                for name in instruments:
                    try:
                        # Try both key formats just in case
                        avg_win = instruments_stats[name].get('Avg_Winning_Trade', 0)
                        if not avg_win:
                            avg_win = instruments_stats[name].get('Avg Winning Trade', 0)
                            
                        avg_loss = instruments_stats[name].get('Avg_Losing_Trade', 0)
                        if not avg_loss:
                            avg_loss = instruments_stats[name].get('Avg Losing Trade', 0)
                            
                        # Convert to float
                        avg_win = float(avg_win) if avg_win else 0.0
                        avg_loss = float(avg_loss) if avg_loss else 0.0
                        # Handle negative loss values
                        avg_loss_abs = abs(avg_loss) if avg_loss else 0
                        if avg_loss_abs > 0:
                            ratio = avg_win / avg_loss_abs if avg_win else 0
                            ratios.append(ratio)
                            ratio_labels.append(name)
                            ratio_colors.append(colors[instruments.index(name)])
                        elif avg_win > 0:
                            # If we have wins but no losses, ratio is infinite - skip or set to high value
                            # Skip for now to avoid division issues
                            pass
                    except (KeyError, TypeError, ValueError, ZeroDivisionError) as e:
                        print(f"Error processing {name} for ratio: {e}")
                        # Skip this instrument
                        pass
                
                # Always generate chart, even if empty (will show empty chart)
                fig_ratio = go.Figure()
                if ratios and ratio_labels:
                    fig_ratio.add_trace(go.Bar(
                        x=ratios,
                        y=ratio_labels,
                        marker=dict(
                            color=ratio_colors,
                            line=dict(color='rgba(255, 255, 255, 0.1)', width=1),
                            opacity=0.85
                        ),
                        text=[f'{r:.2f}' for r in ratios],
                        textfont=dict(color='#f8fafc', size=11, family='DM Sans, sans-serif'),
                        textposition='auto',
                        orientation='h',
                        hovertemplate='<b>%{y}</b><br>Ratio: <b>%{x:.2f}</b><extra></extra>'
                    ))
                    fig_ratio.add_vline(
                        x=1, 
                        line_dash="dash", 
                        line_color="rgba(239, 68, 68, 0.7)", 
                        line_width=2,
                        annotation_text="Break Even",
                        annotation_position="top",
                        annotation=dict(font=dict(color='#f44336', size=11, family='DM Sans, sans-serif'))
                    )
                
                # Create xaxis config without title conflict
                xaxis_ratio = chart_layout.get('xaxis', {}).copy()
                if 'title' in xaxis_ratio:
                    del xaxis_ratio['title']
                xaxis_ratio['title'] = 'Win/Loss Ratio'
                xaxis_ratio['tickangle'] = 0  # Horizontal for ratio chart
                
                # Create yaxis config without title conflict
                yaxis_ratio = base_yaxis.copy()
                # yaxis doesn't need a title for this chart
                
                fig_ratio.update_layout(
                    **{k: v for k, v in chart_layout.items() if k not in ['xaxis', 'yaxis', 'height']},
                    title=dict(
                        text='Average Win/Average Loss Ratio',
                        font=dict(family='DM Sans, sans-serif', size=20, color='#f8fafc', weight=600),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=xaxis_ratio,
                    yaxis=yaxis_ratio,
                    height=450
                )
                winloss_ratio_chart_html = fig_ratio.to_html(include_plotlyjs=False, div_id='winLossRatioChart')
            
        except Exception as e:
            print(f"Error generating Plotly charts: {e}")
            import traceback
            traceback.print_exc()
            # Ensure charts are initialized even on error
            if not winloss_chart_html:
                winloss_chart_html = f'<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">Error: {str(e)}</div>'
            if not winloss_ratio_chart_html:
                winloss_ratio_chart_html = f'<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">Error: {str(e)}</div>'
    else:
        key_metrics_chart_html = ''
        performance_comparison_chart_html = ''
        profit_chart_html = ''
        drawdown_chart_html = ''
        winrate_chart_html = ''
        winloss_chart_html = '<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">No data available</div>'
        avgtrade_chart_html = ''
        winloss_ratio_chart_html = '<div style="display: flex; align-items: center; justify-content: center; height: 400px; color: var(--text-muted);">No data available</div>'

    return render(request, 'dashboard/metrics.html', {
        'user': request.user,
        'daily_stats': daily_stats,
        'window_stats': window_stats,
        'instruments_stats': instruments_stats,
        'combined_stats': combined_stats,
        'selected_instruments': data['selected_instruments'],
        'key_metrics_chart_html': key_metrics_chart_html,
        'performance_comparison_chart_html': performance_comparison_chart_html,
        'profit_chart_html': profit_chart_html,
        'drawdown_chart_html': drawdown_chart_html,
        'winrate_chart_html': winrate_chart_html,
        'winloss_chart_html': winloss_chart_html,
        'avgtrade_chart_html': avgtrade_chart_html,
        'winloss_ratio_chart_html': winloss_ratio_chart_html,
    })


def day_of_week(request):
    """Day of Week Analysis page."""
    data = get_filtered_data(request)
    combined_df = data['combined_df']
    instruments_data = data['instruments_data']
    
    combined_dow_stats = []
    instruments_dow_stats = {}
    # Generate Plotly Charts
    profit_chart_html = ''
    trades_chart_html = ''
    winrate_chart_html = ''
    avgtrade_chart_html = ''
    profit_comparison_chart_html = ''
    trades_comparison_chart_html = ''
    winrate_comparison_chart_html = ''
    
    # Define chart_layout and base_yaxis early (used by both combined and comparison charts)
    chart_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='DM Sans, sans-serif'),
        margin=dict(t=40, b=40, l=50, r=20),
        xaxis=dict(gridcolor='rgba(51, 65, 85, 0.2)'),
    )
    base_yaxis = dict(gridcolor='rgba(51, 65, 85, 0.2)')
    
    if len(combined_df) > 0:
        df = calculate_day_of_week_stats(combined_df)
        if not df.empty:
            # Rename columns to remove spaces and special chars
            df.columns = [c.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('%', 'Percent') for c in df.columns]
            combined_dow_stats = df.to_dict('records')
            
            try:
                # Prepare data for charts
                # After cleaning, column names have underscores: 'DayName' becomes 'DayName', 'Total Net Profit' becomes 'Total_Net_Profit'
                days = [d.get('DayName', d.get('Day', '')) for d in combined_dow_stats]
                profits = [d.get('Total_Net_Profit', 0) for d in combined_dow_stats]
                trades = [d.get('Number_of_Trades', 0) for d in combined_dow_stats]
                winrates = [d.get('Percent_Profitable', 0) for d in combined_dow_stats]
                avg_trades = [d.get('Avg_Trade', 0) for d in combined_dow_stats]
                
                # Colors
                profit_colors = ['#4CAF50' if p >= 0 else '#f44336' for p in profits]
                avg_colors = ['#4CAF50' if a >= 0 else '#f44336' for a in avg_trades]
                
                # 1. Profit by Day
                fig_profit = go.Figure(data=[
                    go.Bar(x=days, y=profits, marker_color=profit_colors,
                           text=[f'${p:,.0f}' for p in profits], textposition='auto', showlegend=False)
                ])
                fig_profit.update_layout(
                    **chart_layout,
                    title='Total Net Profit by Day',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Total Net Profit ($)', tickprefix='$', tickformat=',.0f'),
                    height=400
                )
                profit_chart_html = fig_profit.to_html(include_plotlyjs=False, div_id='profitByDayChart')
                
                # 2. Trades by Day
                fig_trades = go.Figure(data=[
                    go.Bar(x=days, y=trades, marker_color='#94a3b8',
                           text=[str(t) for t in trades], textposition='auto', showlegend=False)
                ])
                fig_trades.update_layout(
                    **chart_layout,
                    title='Number of Trades by Day',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Number of Trades'),
                    height=400
                )
                trades_chart_html = fig_trades.to_html(include_plotlyjs=False, div_id='tradesByDayChart')
                
                # 3. Win Rate by Day
                fig_wr = go.Figure(data=[
                    go.Bar(x=days, y=winrates, marker_color='#4CAF50',
                           text=[f'{w:.1f}%' for w in winrates], textposition='auto', showlegend=False)
                ])
                fig_wr.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%")
                fig_wr.update_layout(
                    **chart_layout,
                    title='Win Rate % by Day',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Win Rate (%)', range=[0, 100]),
                    height=400
                )
                winrate_chart_html = fig_wr.to_html(include_plotlyjs=False, div_id='winRateByDayChart')
                
                # 4. Avg Trade by Day
                fig_avg = go.Figure(data=[
                    go.Bar(x=days, y=avg_trades, marker_color=avg_colors,
                           text=[f'${a:,.0f}' for a in avg_trades], textposition='auto', showlegend=False)
                ])
                fig_avg.update_layout(
                    **chart_layout,
                    title='Average Trade by Day',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Average Trade ($)', tickprefix='$', tickformat=',.0f'),
                    height=400
                )
                avgtrade_chart_html = fig_avg.to_html(include_plotlyjs=False, div_id='avgTradeByDayChart')
                
            except Exception as e:
                print(f"Error generating Day of Week charts: {e}")
                import traceback
                traceback.print_exc()
        
        # Calculate per-instrument stats
        for name, idata in instruments_data.items():
            df_inst = calculate_day_of_week_stats(idata['trades'])
            if not df_inst.empty:
                df_inst.columns = [c.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace('%', 'Percent') for c in df_inst.columns]
                instruments_dow_stats[name] = df_inst.to_dict('records')
        
        # Generate per-instrument comparison charts (matching Streamlit)
        try:
            if combined_dow_stats and instruments_dow_stats:
                # 1. Total Profit by Day - All Instruments (grouped bars)
                fig_profit_comp = go.Figure()
                
                for name, dow_stats in instruments_dow_stats.items():
                    if dow_stats and len(dow_stats) > 0:
                        days_inst = [d.get('Day', d.get('DayName', '')) for d in dow_stats]
                        profits_inst = [d.get('Total_Net_Profit', 0) for d in dow_stats]
                        fig_profit_comp.add_trace(go.Bar(
                            x=days_inst,
                            y=profits_inst,
                            name=name,
                            marker_color=get_instrument_color(name),
                            text=[f'${v:,.0f}' if abs(v) >= 1 else f'${v:.2f}' for v in profits_inst],
                            textposition='auto'
                        ))
                
                # Add combined
                if combined_dow_stats:
                    days_combined = [d.get('Day', d.get('DayName', '')) for d in combined_dow_stats]
                    profits_combined = [d.get('Total_Net_Profit', 0) for d in combined_dow_stats]
                    fig_profit_comp.add_trace(go.Bar(
                        x=days_combined,
                        y=profits_combined,
                        name='COMBINED',
                        marker=dict(line=dict(width=2, color='white')),
                        text=[f'${v:,.0f}' if abs(v) >= 1 else f'${v:.2f}' for v in profits_combined],
                        textposition='auto'
                    ))
                
                fig_profit_comp.update_layout(
                    **{k: v for k, v in chart_layout.items() if k != 'margin'},
                    title='Total Net Profit by Day of Week - All Instruments',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Total Net Profit ($)', tickprefix='$', tickformat=',.0f'),
                    barmode='group',
                    height=500,
                    margin=dict(t=100, b=40, l=50, r=20),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.05, 
                        xanchor="right", 
                        x=1,
                        itemclick=False,
                        itemdoubleclick=False
                    )
                )
                profit_comparison_chart_html = fig_profit_comp.to_html(include_plotlyjs=False, div_id='profitComparisonByDayChart')
                
                # 2. Number of Trades by Day - All Instruments
                fig_trades_comp = go.Figure()
                
                for name, dow_stats in instruments_dow_stats.items():
                    if dow_stats and len(dow_stats) > 0:
                        days_inst = [d.get('Day', d.get('DayName', '')) for d in dow_stats]
                        trades_inst = [d.get('Number_of_Trades', 0) for d in dow_stats]
                        fig_trades_comp.add_trace(go.Bar(
                            x=days_inst,
                            y=trades_inst,
                            name=name,
                            marker_color=get_instrument_color(name),
                            text=[str(t) for t in trades_inst],
                            textposition='auto'
                        ))
                
                # Add combined
                if combined_dow_stats:
                    days_combined = [d.get('Day', d.get('DayName', '')) for d in combined_dow_stats]
                    trades_combined = [d.get('Number_of_Trades', 0) for d in combined_dow_stats]
                    fig_trades_comp.add_trace(go.Bar(
                        x=days_combined,
                        y=trades_combined,
                        name='COMBINED',
                        marker=dict(line=dict(width=2, color='white')),
                        text=[str(t) for t in trades_combined],
                        textposition='auto'
                    ))
                
                fig_trades_comp.update_layout(
                    **{k: v for k, v in chart_layout.items() if k != 'margin'},
                    title='Number of Trades by Day of Week - All Instruments',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Number of Trades'),
                    barmode='group',
                    height=500,
                    margin=dict(t=100, b=40, l=50, r=20),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.05, 
                        xanchor="right", 
                        x=1,
                        itemclick=False,
                        itemdoubleclick=False
                    )
                )
                trades_comparison_chart_html = fig_trades_comp.to_html(include_plotlyjs=False, div_id='tradesComparisonByDayChart')
                
                # 3. Win Rate by Day - All Instruments
                fig_winrate_comp = go.Figure()
                
                for name, dow_stats in instruments_dow_stats.items():
                    if dow_stats and len(dow_stats) > 0:
                        days_inst = [d.get('Day', d.get('DayName', '')) for d in dow_stats]
                        winrates_inst = [d.get('Percent_Profitable', 0) for d in dow_stats]
                        fig_winrate_comp.add_trace(go.Bar(
                            x=days_inst,
                            y=winrates_inst,
                            name=name,
                            marker_color=get_instrument_color(name),
                            text=[f'{v:.1f}%' for v in winrates_inst],
                            textposition='auto'
                        ))
                
                # Add combined
                if combined_dow_stats:
                    days_combined = [d.get('Day', d.get('DayName', '')) for d in combined_dow_stats]
                    winrates_combined = [d.get('Percent_Profitable', 0) for d in combined_dow_stats]
                    fig_winrate_comp.add_trace(go.Bar(
                        x=days_combined,
                        y=winrates_combined,
                        name='COMBINED',
                        marker=dict(line=dict(width=2, color='white')),
                        text=[f'{v:.1f}%' for v in winrates_combined],
                        textposition='auto'
                    ))
                
                fig_winrate_comp.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%")
                fig_winrate_comp.update_layout(
                    **{k: v for k, v in chart_layout.items() if k != 'margin'},
                    title='Win Rate by Day of Week - All Instruments',
                    xaxis_title='Day of Week',
                    yaxis=dict(**base_yaxis, title='Win Rate (%)', range=[0, 100]),
                    barmode='group',
                    height=500,
                    margin=dict(t=100, b=40, l=50, r=20),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.05, 
                        xanchor="right", 
                        x=1,
                        itemclick=False,
                        itemdoubleclick=False
                    )
                )
                winrate_comparison_chart_html = fig_winrate_comp.to_html(include_plotlyjs=False, div_id='winRateComparisonByDayChart')
                
        except Exception as e:
            print(f"Error generating Day of Week comparison charts: {e}")
            import traceback
            traceback.print_exc()

    return render(request, 'dashboard/day_of_week.html', {
        'user': request.user,
        'combined_dow_stats': combined_dow_stats,
        'instruments_dow_stats': instruments_dow_stats,
        'selected_instruments': data['selected_instruments'],
        'profit_chart_html': profit_chart_html,
        'trades_chart_html': trades_chart_html,
        'winrate_chart_html': winrate_chart_html,
        'avgtrade_chart_html': avgtrade_chart_html,
        'profit_comparison_chart_html': profit_comparison_chart_html,
        'trades_comparison_chart_html': trades_comparison_chart_html,
        'winrate_comparison_chart_html': winrate_comparison_chart_html,
    })


def strategy_images(request):
    """Strategy Images gallery."""
    return render(request, 'dashboard/strategy_images.html', {
        'user': request.user,
    })


def news(request):
    """News page."""
    return render(request, 'dashboard/news.html', {
        'user': request.user,
    })


@login_required
def checkout(request):
    """
    Simple checkout / confirmation page before starting the free trial.

    - Shows the instruments currently selected in the filters.
    - Summarizes basic stats (trades, profit, win rate).
    - From here the user can click a final button to start the trial.
    """
    user = request.user

    # Make sure user has a machine ID before proceeding to confirmation
    if not getattr(user, "has_machine_id", False):
        return redirect("users:set_machine_id")

    data = get_filtered_data(request)
    combined_df = data["combined_df"]
    selected_instruments = data["selected_instruments"]

    total_trades = len(combined_df)
    total_net_profit = None
    win_rate = None

    if len(combined_df) > 0:
        stats, _, _ = calculate_comprehensive_stats(combined_df, "ALL INSTRUMENTS")
        total_net_profit = stats.get("Total Net Profit")
        win_rate = stats.get("Percent Profitable")

    # NOTE: adjust this to match the Strategy.name you create in the DB.
    strategy_name = "ROA305_MULTI"

    return render(
        request,
        "dashboard/checkout.html",
        {
            "user": user,
            "selected_instruments": selected_instruments,
            "total_trades": total_trades,
            "total_net_profit": total_net_profit,
            "win_rate": win_rate,
            "strategy_name": strategy_name,
        },
    )


@login_required
def download_trial(request, strategy_name: str):
    """
    Start a free trial for the given strategy and return/download the files.

    This view is intentionally simple for now:
    - Requires authenticated user with a machine ID set.
    - Uses payments.utils.start_trial(...) to create the Trial.
    - Records a StrategyDownload row for analytics.
    - Returns a basic HTTP response placeholder where you can later
      hook in real file delivery (e.g. NinjaTrader .zip download).
    """
    from payments.utils import start_trial  # local import to avoid circulars
    from .models import Strategy, StrategyDownload

    user = request.user

    # Enforce machine ID requirement (trials are machine-locked)
    if not getattr(user, "has_machine_id", False):
        # Guide user to machine ID registration first
        return redirect("users:set_machine_id")

    # Look up (or lazily create) the strategy being trialed.
    # This avoids 403s if the record was not pre-created in the admin.
    strategy, _created = Strategy.objects.get_or_create(
        name=strategy_name,
        defaults={
            "display_name": "ROA305 Multi-Instrument Strategy",
            "description": "Automatically created strategy record for the ROA305 multi-instrument free trial.",
            "is_active": True,
        },
    )

    # Create / validate the trial (raises ValueError if not allowed)
    try:
        trial, _created = start_trial(user, strategy_name=strategy.name)
    except ValueError as e:
        # User has already had a trial or other rule violation
        return HttpResponseForbidden(str(e))

    # Record the download event for analytics / reporting
    StrategyDownload.objects.create(
        user=user,
        strategy=strategy,
        access_type="trial",
        machine_id_hash=user.machine_id_hash,
        trial_triggered=True,
    )

    # Render a proper download/confirmation page instead of plain text.
    # The template can show:
    # - trial status
    # - strategy name
    # - download button for the NinjaTrader files
    # - basic setup instructions and trial expiry date
    return render(
        request,
        "dashboard/download_trial.html",
        {
            "user": user,
            "strategy": strategy,
            "trial": trial,
        },
    )