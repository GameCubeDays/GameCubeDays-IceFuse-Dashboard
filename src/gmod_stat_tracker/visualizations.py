import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# Import configuration (Absolute Import)
from gmod_stat_tracker import config


def ensure_graphs_directory():
    """Create graphs directory if it doesn't exist."""
    if not os.path.exists(config.GRAPHS_DIR):
        os.makedirs(config.GRAPHS_DIR)
        print(f"Created directory: {config.GRAPHS_DIR}")

def format_date_range_short(date_range_str):
    """(Unchanged logic)"""
    try:
        parts = date_range_str.split(' - ')
        if len(parts) == 2:
            start_date = datetime.strptime(parts[0], '%Y-%m-%d %H:%M')
            end_date = datetime.strptime(parts[1], '%Y-%m-%d %H:%M')
            return f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}"
    except:
        pass
    return date_range_str


def analyze_data_quality(branch_pivots_df, subbranch_pivots_df):
    """(Unchanged logic)"""
    print("\n" + "="*60)
    print("DATA QUALITY ANALYSIS")
    print("="*60)
    
    issues_found = []
    
    if not branch_pivots_df.empty:
        print("\n[BRANCH DATA ANALYSIS]")
        for _, row in branch_pivots_df.iterrows():
            branch = row['Branch']
            
            if 'Avg_HS_Percent' in row and pd.notna(row['Avg_HS_Percent']):
                hs_pct = row['Avg_HS_Percent']
                if hs_pct > 100:
                    issue = f"⚠️ {branch}: Headshot % is {hs_pct:.2f}% (over 100%!)"
                    print(issue)
                    issues_found.append(issue)
            
            if 'Avg_KD_Ratio' in row and pd.notna(row['Avg_KD_Ratio']):
                kd = row['Avg_KD_Ratio']
                if kd > 10:
                    issue = f"⚠️ {branch}: K/D Ratio is {kd:.2f} (suspiciously high)"
                    print(issue)
                    issues_found.append(issue)
            
            for col in ['Avg_Kills', 'Avg_Deaths', 'Avg_Money', 'Avg_Level']:
                if col in row and pd.notna(row[col]):
                    if row[col] < 0:
                        issue = f"⚠️ {branch}: {col} is negative ({row[col]})"
                        print(issue)
                        issues_found.append(issue)
    
    if not subbranch_pivots_df.empty:
        print("\n[SUB-BRANCH DATA ANALYSIS]")
        for _, row in subbranch_pivots_df.iterrows():
            subbranch = row['SubBranch']
            
            if 'Avg_HS_Percent' in row and pd.notna(row['Avg_HS_Percent']):
                hs_pct = row['Avg_HS_Percent']
                if hs_pct > 100:
                    issue = f"⚠️ {subbranch}: Headshot % is {hs_pct:.2f}% (over 100%!)"
                    print(issue)
                    issues_found.append(issue)
    
    if not issues_found:
        print("\n✅ No data quality issues detected!")
    else:
        print(f"\n⚠️ Found {len(issues_found)} potential data issues")
        print("\nRECOMMENDATION: Check the source data (GMod API) for these anomalies.")
        print("The HS_Percent field in the API might be formatted incorrectly (e.g., 60.74 vs 0.6074)")
    
    print("="*60)


def create_branch_hours_graph(branch_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING BRANCH HOURS GRAPH]")
    
    if branch_pivots_df.empty:
        print("⚠️ No data available for branch hours graph")
        return None
    
    week_columns = [col for col in branch_pivots_df.columns 
                    if ' - ' in str(col) and col not in ['Branch']]
    
    if not week_columns:
        print("⚠️ No week columns found")
        return None
    
    week_labels = [format_date_range_short(col) for col in week_columns]
    
    fig = go.Figure()
    
    branch_colors = {
        'Army': '#2E7D32',
        'USAF': '#17A2B8',  # Teal
        'USMC': '#C62828',
        'NAVY': '#0277BD'
    }
    
    all_hours_per_week = []
    for week_col in week_columns:
        week_values = branch_pivots_df[week_col].dropna()
        if len(week_values) > 0:
            all_hours_per_week.append(week_values.mean())
        else:
            all_hours_per_week.append(0)
    
    fig.add_trace(go.Scatter(
        x=week_labels,
        y=all_hours_per_week,
        mode='lines',
        name='Overall Average',
        line=dict(width=2, color='#757575', dash='dot'),
        hovertemplate='<b>Overall Average</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
    ))
    
    for _, row in branch_pivots_df.iterrows():
        branch = row['Branch']
        hours = [row[col] if pd.notna(row[col]) else 0 for col in week_columns]
        
        fig.add_trace(go.Scatter(
            x=week_labels,
            y=hours,
            mode='lines+markers',
            name=branch,
            line=dict(width=3, color=branch_colors.get(branch, '#666666')),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Average Playtime Hours by Branch (Weekly)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2C3E50'}
        },
        xaxis_title='Week',
        yaxis_title='Average Hours',
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14)
        ),
        width=1200,
        height=600
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0', rangemode='tozero')
    
    html_path = os.path.join(config.GRAPHS_DIR, 'branch_hours_over_time.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'branch_hours_over_time.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path)
    
    print(f"✅ Branch hours graph saved: {html_path}")
    
    return png_path


def create_subbranch_hours_graph(subbranch_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING SUB-BRANCH HOURS GRAPH]")
    
    if subbranch_pivots_df.empty:
        print("⚠️ No data available for sub-branch hours graph")
        return None
    
    week_columns = [col for col in subbranch_pivots_df.columns 
                    if ' - ' in str(col) and col not in ['SubBranch']]
    
    if not week_columns:
        print("⚠️ No week columns found")
        return None
    
    week_labels = [format_date_range_short(col) for col in week_columns]
    
    fig = go.Figure()
    
    subbranch_colors = {
        '75th': '#388E3C',
        '89th': '#7CB342',
        'FORECON': '#D32F2F',
        'MARSOC': '#F57C00',
        'SEALS': '#17A2B8',  # Teal
        'DEVGRU': '#0288D1',
        'DELTA': '#512DA8'
    }
    
    all_hours_per_week = []
    for week_col in week_columns:
        week_values = subbranch_pivots_df[week_col].dropna()
        if len(week_values) > 0:
            all_hours_per_week.append(week_values.mean())
        else:
            all_hours_per_week.append(0)
    
    fig.add_trace(go.Scatter(
        x=week_labels,
        y=all_hours_per_week,
        mode='lines',
        name='Overall Average',
        line=dict(width=2, color='#757575', dash='dot'),
        hovertemplate='<b>Overall Average</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
    ))
    
    for _, row in subbranch_pivots_df.iterrows():
        subbranch = row['SubBranch']
        hours = [row[col] if pd.notna(row[col]) else 0 for col in week_columns]
        
        fig.add_trace(go.Scatter(
            x=week_labels,
            y=hours,
            mode='lines+markers',
            name=subbranch,
            line=dict(width=3, color=subbranch_colors.get(subbranch, '#666666')),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Average Playtime Hours by Sub-Branch (Weekly)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2C3E50'}
        },
        xaxis_title='Week',
        yaxis_title='Average Hours',
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14)
        ),
        width=1200,
        height=600
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0', rangemode='tozero')
    
    html_path = os.path.join(config.GRAPHS_DIR, 'subbranch_hours_over_time.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'subbranch_hours_over_time.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path)
    
    print(f"✅ Sub-branch hours graph saved: {html_path}")
    
    return png_path


def create_branch_stats_ranking(branch_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING BRANCH STATS RANKINGS]")
    
    if branch_pivots_df.empty:
        print("⚠️ No data available for rankings")
        return None
    
    stats_to_rank = {
        'Avg_KD_Ratio': ('K/D Ratio', 2),
        'Avg_HS_Percent': ('Headshot %', 2),
        'Avg_Kills': ('Average Kills', 0),
        'Avg_Deaths': ('Average Deaths', 0),
        'Avg_Level': ('Average Level', 0),
        'Avg_Money': ('Average Money', 0),
        'Avg_Damage': ('Average Damage', 0)
    }
    
    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=[stats_to_rank[stat][0] for stat in stats_to_rank.keys()] + [''],
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]],
        vertical_spacing=0.2,
        horizontal_spacing=0.1
    )
    
    branch_colors = {
        'Army': '#2E7D32',
        'USAF': '#17A2B8',  # Teal
        'USMC': '#C62828',
        'NAVY': '#0277BD'
    }
    
    positions = [(1,1), (1,2), (1,3), (1,4), (2,1), (2,2), (2,3)]
    
    for idx, (stat_col, (stat_name, decimals)) in enumerate(stats_to_rank.items()):
        if stat_col not in branch_pivots_df.columns:
            continue
            
        avg_val = branch_pivots_df[stat_col].mean()
        
        row, col = positions[idx]
        sorted_df = branch_pivots_df.sort_values(by=stat_col, ascending=True)
        colors = [branch_colors.get(branch, '#666666') for branch in sorted_df['Branch']]
        
        text_values = sorted_df[stat_col].round(decimals).apply(
            lambda x: f'{x:.{decimals}f}' if decimals > 0 else f'{int(x):,}'
        )
        
        fig.add_trace(
            go.Bar(
                y=sorted_df['Branch'],
                x=sorted_df[stat_col],
                orientation='h',
                marker=dict(color=colors),
                text=text_values,
                textposition='inside',
                textfont=dict(size=12, color='white'),
                insidetextanchor='middle',
                hovertemplate=f'<b>%{{y}}</b><br>Value: %{{x:.{decimals}f}}<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )
        
        fig.add_vline(
            x=avg_val, 
            line_width=2, 
            line_dash="dot", 
            line_color="grey",
            row=row, col=col,
            annotation_text="Avg",
            annotation_position="top right"
        )
        
        max_val = sorted_df[stat_col].max()
        axis_max = max(max_val, avg_val) 
        fig.update_xaxes(range=[0, axis_max * 1.15], row=row, col=col)
    
    fig.update_layout(
        title_text="Branch Statistics Rankings",
        title_x=0.5,
        title_font=dict(size=24, color='#2C3E50'),
        showlegend=False,
        height=800,
        width=1600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=50, t=100, b=50)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=False)
    
    html_path = os.path.join(config.GRAPHS_DIR, 'branch_stats_rankings.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'branch_stats_rankings.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path, width=1600, height=800)
    
    print(f"✅ Branch rankings graph saved: {html_path}")
    
    return png_path


def create_subbranch_stats_ranking(subbranch_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING SUB-BRANCH STATS RANKINGS]")
    
    if subbranch_pivots_df.empty:
        print("⚠️ No data available for sub-branch rankings")
        return None
    
    stats_to_rank = {
        'Avg_KD_Ratio': ('K/D Ratio', 2),
        'Avg_HS_Percent': ('Headshot %', 2),
        'Avg_Kills': ('Average Kills', 0),
        'Avg_Deaths': ('Average Deaths', 0),
        'Avg_Level': ('Average Level', 0),
        'Avg_Money': ('Average Money', 0),
        'Avg_Damage': ('Average Damage', 0)
    }
    
    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=[stats_to_rank[stat][0] for stat in stats_to_rank.keys()] + [''],
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]],
        vertical_spacing=0.2,
        horizontal_spacing=0.1
    )
    
    subbranch_colors = {
        '75th': '#388E3C',
        '89th': '#7CB342',
        'FORECON': '#D32F2F',
        'MARSOC': '#F57C00',
        'SEALS': '#17A2B8',  # Teal
        'DEVGRU': '#0288D1',
        'DELTA': '#512DA8'
    }
    
    positions = [(1,1), (1,2), (1,3), (1,4), (2,1), (2,2), (2,3)]
    
    for idx, (stat_col, (stat_name, decimals)) in enumerate(stats_to_rank.items()):
        if stat_col not in subbranch_pivots_df.columns:
            continue
            
        avg_val = subbranch_pivots_df[stat_col].mean()
        
        row, col = positions[idx]
        sorted_df = subbranch_pivots_df.sort_values(by=stat_col, ascending=True)
        colors = [subbranch_colors.get(sb, '#666666') for sb in sorted_df['SubBranch']]
        
        text_values = sorted_df[stat_col].round(decimals).apply(
            lambda x: f'{x:.{decimals}f}' if decimals > 0 else f'{int(x):,}'
        )
        
        fig.add_trace(
            go.Bar(
                y=sorted_df['SubBranch'],
                x=sorted_df[stat_col],
                orientation='h',
                marker=dict(color=colors),
                text=text_values,
                textposition='inside',
                textfont=dict(size=12, color='white'),
                insidetextanchor='middle',
                hovertemplate=f'<b>%{{y}}</b><br>Value: %{{x:.{decimals}f}}<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )
        
        fig.add_vline(
            x=avg_val, 
            line_width=2, 
            line_dash="dot", 
            line_color="grey",
            row=row, col=col,
            annotation_text="Avg",
            annotation_position="top right"
        )
        
        max_val = sorted_df[stat_col].max()
        axis_max = max(max_val, avg_val)
        fig.update_xaxes(range=[0, axis_max * 1.15], row=row, col=col)
    
    fig.update_layout(
        title_text="Sub-Branch Statistics Rankings",
        title_x=0.5,
        title_font=dict(size=24, color='#2C3E50'),
        showlegend=False,
        height=900,
        width=1600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=50, t=100, b=50)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=False)
    
    html_path = os.path.join(config.GRAPHS_DIR, 'subbranch_stats_rankings.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'subbranch_stats_rankings.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path, width=1600, height=900)
    
    print(f"✅ Sub-branch rankings graph saved: {html_path}")
    
    return png_path


def create_us_hours_graph(us_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING US HOURS GRAPH]")
    
    if us_pivots_df.empty:
        print("⚠️ No data available for US hours graph")
        return None
    
    week_columns = [col for col in us_pivots_df.columns 
                    if ' - ' in str(col) and col not in ['Group']]
    
    if not week_columns:
        print("⚠️ No week columns found")
        return None
    
    week_labels = [format_date_range_short(col) for col in week_columns]
    
    fig = go.Figure()
    
    org_colors = {
        'US Military': '#1976D2',  # Blue
        'US SOCOM': '#C62828'   # Red
    }
    
    all_hours_per_week = []
    for week_col in week_columns:
        week_values = us_pivots_df[week_col].dropna()
        if len(week_values) > 0:
            all_hours_per_week.append(week_values.mean())
        else:
            all_hours_per_week.append(0)
    
    fig.add_trace(go.Scatter(
        x=week_labels,
        y=all_hours_per_week,
        mode='lines',
        name='Overall Average',
        line=dict(width=2, color='#757575', dash='dot'),
        hovertemplate='<b>Overall Average</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
    ))
    
    for _, row in us_pivots_df.iterrows():
        org = row['Group']
        hours = [row[col] if pd.notna(row[col]) else 0 for col in week_columns]
        
        fig.add_trace(go.Scatter(
            x=week_labels,
            y=hours,
            mode='lines+markers',
            name=org,
            line=dict(width=4, color=org_colors.get(org, '#666666')),
            marker=dict(size=10),
            hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Avg Hours: %{y:.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Average Playtime Hours: US vs SOCOM (Weekly)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2C3E50'}
        },
        xaxis_title='Week',
        yaxis_title='Average Hours',
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14)
        ),
        width=1200,
        height=600
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0', rangemode='tozero')
    
    html_path = os.path.join(config.GRAPHS_DIR, 'us_hours_over_time.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'us_hours_over_time.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path)
    
    print(f"✅ US hours graph saved: {html_path}")
    
    return png_path


def create_us_stats_ranking(us_pivots_df):
    """(Unchanged logic, uses config.GRAPHS_DIR)"""
    print("\n[CREATING US STATS RANKINGS]")
    
    if us_pivots_df.empty:
        print("⚠️ No data available for US rankings")
        return None
    
    stats_to_rank = {
        'Avg_KD_Ratio': ('K/D Ratio', 2),
        'Avg_HS_Percent': ('Headshot %', 2),
        'Avg_Kills': ('Average Kills', 0),
        'Avg_Deaths': ('Average Deaths', 0),
        'Avg_Level': ('Average Level', 0),
        'Avg_Money': ('Average Money', 0),
        'Avg_Damage': ('Average Damage', 0)
    }
    
    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=[stats_to_rank[stat][0] for stat in stats_to_rank.keys()] + [''],
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]],
        vertical_spacing=0.2,
        horizontal_spacing=0.1
    )
    
    org_colors = {
        'US Military': '#1976D2',
        'US SOCOM': '#C62828'
    }
    
    positions = [(1,1), (1,2), (1,3), (1,4), (2,1), (2,2), (2,3)]
    
    for idx, (stat_col, (stat_name, decimals)) in enumerate(stats_to_rank.items()):
        if stat_col not in us_pivots_df.columns:
            continue
        
        row, col = positions[idx]
        sorted_df = us_pivots_df.sort_values(by=stat_col, ascending=True)
        colors = [org_colors.get(org, '#666666') for org in sorted_df['Group']]
        
        text_values = sorted_df[stat_col].round(decimals).apply(
            lambda x: f'{x:.{decimals}f}' if decimals > 0 else f'{int(x):,}'
        )
        
        fig.add_trace(
            go.Bar(
                y=sorted_df['Group'],
                x=sorted_df[stat_col],
                orientation='h',
                marker=dict(color=colors),
                text=text_values,
                textposition='inside',
                textfont=dict(size=12, color='white'),
                insidetextanchor='middle',
                hovertemplate=f'<b>%{{y}}</b><br>Value: %{{x:.{decimals}f}}<extra></extra>',
                showlegend=False
            ),
            row=row, col=col
        )
        
        max_val = sorted_df[stat_col].max()
        fig.update_xaxes(range=[0, max_val * 1.15], row=row, col=col)
    
    fig.update_layout(
        title_text="US vs SOCOM Statistics Rankings",
        title_x=0.5,
        title_font=dict(size=24, color='#2C3E50'),
        showlegend=False,
        height=600,
        width=1600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=50, t=100, b=50)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    fig.update_yaxes(showgrid=False)
    
    html_path = os.path.join(config.GRAPHS_DIR, 'us_stats_rankings.html')
    png_path = os.path.join(config.GRAPHS_DIR, 'us_stats_rankings.png')
    
    fig.write_html(html_path)
    fig.write_image(png_path, width=1600, height=600)
    
    print(f"✅ US rankings graph saved: {html_path}")
    
    return png_path

# --- MAIN FUNCTION ---

def generate_all_graphs(branch_pivots_csv, subbranch_pivots_csv, us_pivots_csv):
    """
    Main function to generate all graphs from CSV files.
    (Now takes CSV paths as arguments)
    """
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)
    
    ensure_graphs_directory()
    
    try:
        branch_df = pd.read_csv(branch_pivots_csv)
        print(f"✅ Loaded branch pivots: {len(branch_df)} rows")
    except FileNotFoundError:
        print(f"⚠️ Branch pivots file not found: {branch_pivots_csv}")
        branch_df = pd.DataFrame()
    
    try:
        subbranch_df = pd.read_csv(subbranch_pivots_csv)
        print(f"✅ Loaded sub-branch pivots: {len(subbranch_df)} rows")
    except FileNotFoundError:
        print(f"⚠️ Sub-branch pivots file not found: {subbranch_pivots_csv}")
        subbranch_df = pd.DataFrame()

    try:
        us_df = pd.read_csv(us_pivots_csv)
        print(f"✅ Loaded US pivots: {len(us_df)} rows")
    except FileNotFoundError:
        print(f"⚠️ US pivots file not found: {us_pivots_csv}")
        us_df = pd.DataFrame()
    
    # Analyze data quality first
    analyze_data_quality(branch_df, subbranch_df)
    
    # Generate graphs
    if not branch_df.empty:
        create_branch_hours_graph(branch_df)
        create_branch_stats_ranking(branch_df)
    
    if not subbranch_df.empty:
        create_subbranch_hours_graph(subbranch_df)
        create_subbranch_stats_ranking(subbranch_df)
        
    if not us_df.empty:
        create_us_hours_graph(us_df)
        create_us_stats_ranking(us_df)
    
    print("\n" + "="*60)
    print("✅ ALL GRAPHS GENERATED!")
    print(f"   Location: ./{config.GRAPHS_DIR}/")
    print("   - HTML files: Open in browser for interactive graphs")
    print("   - PNG files: Use in reports/presentations")
    print("="*60)


if __name__ == "__main__":
    # Test block now uses config paths
    print("Running visualizations.py as a script...")
    generate_all_graphs(
        branch_pivots_csv=config.BRANCH_PIVOT_OUTPUT_PATH,
        subbranch_pivots_csv=config.SUBBRANCH_PIVOT_OUTPUT_PATH,
        us_pivots_csv=config.US_PIVOT_OUTPUT_PATH
    )