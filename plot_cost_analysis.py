import plotly.graph_objects as go
import numpy as np

# Data from the provided image
# Cost per frame: 0.06 USD
# 1 training data unit:
#   - 1 min (10 Hz, 600 frames) = 36 USD
#   - 1 min (50 Hz, 3000 frames) = 180 USD
# Table Data:
# 1 min (10 Hz): 1000 units = 36k, 10k units = 360k
# 1 min (50 Hz): 1000 units = 180k, 10k units = 1.8 millions
# Price (67% Profit Margin):
# 1 min (10 Hz): 1000 units = 108k, 10k units = 1.08 millions
# 1 min (50 Hz): 1000 units = 540k, 10k units = 5.4 millions

# Constants
COST_PER_FRAME = 0.06
HZ_10 = 10
HZ_50 = 50
PROFIT_MARGIN = 0.67
# Price = Cost / (1 - Margin)
PRICE_MULTIPLIER = 1 / (1 - PROFIT_MARGIN) # approximately 3x for 67% margin

cost_1min_10hz_rate = 60 * HZ_10 * COST_PER_FRAME  # 36 USD per unit
cost_1min_50hz_rate = 60 * HZ_50 * COST_PER_FRAME  # 180 USD per unit

price_1min_10hz_rate = cost_1min_10hz_rate * PRICE_MULTIPLIER # ~108 USD per unit
price_1min_50hz_rate = cost_1min_50hz_rate * PRICE_MULTIPLIER # ~540 USD per unit

# Units (x-axis) for plotting: 1k to 100k
units_extended = np.logspace(3, 5, 100)

# Extrapolate to full range
cost_1min_10hz_extended = units_extended * cost_1min_10hz_rate
cost_1min_50hz_extended = units_extended * cost_1min_50hz_rate
price_1min_10hz_extended = units_extended * price_1min_10hz_rate
price_1min_50hz_extended = units_extended * price_1min_50hz_rate

# Create figure
fig = go.Figure()

# Add Filling/Shadow between Cost and Price for 1 min (10 Hz)
fig.add_trace(go.Scatter(
    x=np.concatenate([units_extended, units_extended[::-1]]),
    y=np.concatenate([cost_1min_10hz_extended, price_1min_10hz_extended[::-1]]),
    fill='toself',
    fillcolor='rgba(59, 130, 246, 0.1)',
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo='skip',
    showlegend=False,
    name='1 min (10 Hz) Profit Area'
))

# Add Filling/Shadow between Cost and Price for 1 min (50 Hz)
fig.add_trace(go.Scatter(
    x=np.concatenate([units_extended, units_extended[::-1]]),
    y=np.concatenate([cost_1min_50hz_extended, price_1min_50hz_extended[::-1]]),
    fill='toself',
    fillcolor='rgba(239, 68, 68, 0.1)',
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo='skip',
    showlegend=False,
    name='1 min (50 Hz) Profit Area'
))

# Add cost lines
fig.add_trace(go.Scatter(
    x=units_extended,
    y=cost_1min_10hz_extended,
    mode='lines',
    name='1 min (10 Hz) Cost',
    line=dict(color='#3B82F6', width=3),
    hovertemplate='<b>1 min (10 Hz) Cost</b><br>Units: %{x:,.0f}<br>Cost: $%{y:,.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=units_extended,
    y=cost_1min_50hz_extended,
    mode='lines',
    name='1 min (50 Hz) Cost',
    line=dict(color='#EF4444', width=3),
    hovertemplate='<b>1 min (50 Hz) Cost</b><br>Units: %{x:,.0f}<br>Cost: $%{y:,.0f}<extra></extra>'
))

# Add price lines
fig.add_trace(go.Scatter(
    x=units_extended,
    y=price_1min_10hz_extended,
    mode='lines',
    name='1 min (10 Hz) Price (67% Margin)',
    line=dict(color='#3B82F6', width=3, dash='dash'),
    hovertemplate='<b>1 min (10 Hz) Price</b><br>Units: %{x:,.0f}<br>Price: $%{y:,.0f}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=units_extended,
    y=price_1min_50hz_extended,
    mode='lines',
    name='1 min (50 Hz) Price (67% Margin)',
    line=dict(color='#EF4444', width=3, dash='dash'),
    hovertemplate='<b>1 min (50 Hz) Price</b><br>Units: %{x:,.0f}<br>Price: $%{y:,.0f}<extra></extra>'
))

# Update layout
fig.update_layout(
    title={
        'text': '<b>Training Data Cost & Price Analysis (10 Hz vs 50 Hz)</b><br><span style="font-size: 14px; color: #6B7280;">67% Profit Margin | Log Scale Units</span>',
        'font': {'size': 24, 'family': 'Inter, sans-serif', 'color': '#1F2937'},
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis=dict(
        title='<b>Total Units</b>',
        type='log',
        showgrid=True,
        gridcolor='#E5E7EB',
        gridwidth=1,
        title_font=dict(size=18, family='Inter, sans-serif', color='#1F2937'),
        tickfont=dict(size=14, family='Inter, sans-serif', color='#374151'),
        tickmode='array',
        tickvals=[1000, 2000, 3000, 5000, 10000, 20000, 30000, 50000, 100000],
        ticktext=['1k', '2k', '3k', '5k', '10k', '20k', '30k', '50k', '100k'],
        range=[3, 5]  # 10^3 = 1000 to 10^5 = 100000
    ),
    yaxis=dict(
        title='<b>Value (USD)</b>',
        type='linear',
        showgrid=True,
        gridcolor='#E5E7EB',
        gridwidth=1,
        title_font=dict(size=18, family='Inter, sans-serif', color='#1F2937'),
        tickfont=dict(size=14, family='Inter, sans-serif', color='#374151'),
        tickformat='$.2s',  # Format as $1k, $10M, etc.
        tickmode='linear',
        tick0=0,
        dtick=5000000  # Grid every $5,000,000
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    hovermode='x unified',
    legend=dict(
        font=dict(size=12, family='Inter, sans-serif', color='#374151'),
        bgcolor='rgba(255, 255, 255, 0.9)',
        bordercolor='#D1D5DB',
        borderwidth=1,
        x=0.02,
        y=0.98,
        xanchor='left',
        yanchor='top'
    ),
    width=1200,
    height=750,
    margin=dict(l=80, r=40, t=100, b=80),
    annotations=[
        dict(
            x=1000, y=price_1min_50hz_rate * 1000,
            xref="x", yref="y",
            text="Price (1 min @ 50 Hz, 1k units): $540k",
            showarrow=True, arrowhead=2, ax=70, ay=-30,
            font=dict(size=12, color="#EF4444")
        ),
        dict(
            x=10000, y=price_1min_10hz_rate * 10000,
            xref="x", yref="y",
            text="Price (1 min @ 10 Hz, 10k units): $1.08M",
            showarrow=True, arrowhead=2, ax=-70, ay=-30,
            font=dict(size=12, color="#3B82F6")
        )
    ]
)

# Show the figure
fig.show()

# # Optionally save as HTML
# output_file = '/Users/shamangary/codeDemo/vibephysics/cost_analysis_log_linear.html'
# fig.write_html(output_file)
# print(f"Plot saved to: {output_file}")
