import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from scipy.interpolate import make_interp_spline, PchipInterpolator

def plot_yield_curve(bonds: List[Dict[str, Any]], 
                    title: str = "Yield Curve",
                    show_real_yield: bool = False) -> go.Figure:
    """
    Plot yield curve from bond data with smooth curves
    
    Args:
        bonds: List of bond dictionaries with keys 'Laufzeit', 'YTM', and optionally 'Realzins'
        title: Title of the plot
        show_real_yield: Whether to plot real yield
        
    Returns:
        Plotly figure object
    """
    # Sort bonds by maturity
    sorted_bonds = sorted(bonds, key=lambda x: x["Laufzeit"])
    
    # Extract x and y values
    x_years = [b["Laufzeit"] for b in sorted_bonds]
    y_ytm = [b["YTM"] for b in sorted_bonds]
    
    # Create figure
    fig = go.Figure()
    
    # If we have enough points, generate a smooth curve
    if len(sorted_bonds) >= 3:
        # Generate smooth curve with more points for interpolation
        x_smooth = np.linspace(min(x_years), max(x_years), 100)
        
        # Use PCHIP interpolation which preserves monotonicity and is better for economic data
        pch = PchipInterpolator(x_years, y_ytm)
        y_smooth = pch(x_smooth)
        
        # Add smooth nominal yield curve
        fig.add_trace(go.Scatter(
            x=x_smooth,
            y=y_smooth,
            mode="lines",
            name="Nominal Yield",
            line=dict(color='blue', width=3, shape='spline', smoothing=1.3),
        ))
        
        # Add original data points
        fig.add_trace(go.Scatter(
            x=x_years,
            y=y_ytm,
            mode="markers",
            name="Actual Yields",
            marker=dict(size=10, color='blue', symbol='circle'),
            showlegend=False
        ))
    else:
        # If we don't have enough points, just use the original data
        fig.add_trace(go.Scatter(
            x=x_years,
            y=y_ytm,
            mode="lines+markers",
            name="Nominal Yield",
            line=dict(color='blue', width=3),
            marker=dict(size=10, symbol='circle')
        ))
    
    # Add real yield curve if requested
    if show_real_yield and all("Realzins" in b for b in sorted_bonds):
        y_real = [b["Realzins"] for b in sorted_bonds]
        
        if len(sorted_bonds) >= 3:
            # Generate smooth curve for real yield
            pch_real = PchipInterpolator(x_years, y_real)
            y_real_smooth = pch_real(x_smooth)
            
            # Add smooth real yield curve
            fig.add_trace(go.Scatter(
                x=x_smooth,
                y=y_real_smooth,
                mode="lines",
                name="Real Yield",
                line=dict(color='green', width=3, dash='dash', shape='spline', smoothing=1.3),
            ))
            
            # Add original data points
            fig.add_trace(go.Scatter(
                x=x_years,
                y=y_real,
                mode="markers",
                name="Actual Real Yields",
                marker=dict(size=10, color='green', symbol='square'),
                showlegend=False
            ))
        else:
            fig.add_trace(go.Scatter(
                x=x_years,
                y=y_real,
                mode="lines+markers",
                name="Real Yield",
                line=dict(color='green', width=3, dash='dash'),
                marker=dict(size=10, symbol='square')
            ))
    
    # Add shaded area for recession indicator (illustration only)
    fig.add_vrect(
        x0=0, x1=2,
        fillcolor="lightcoral", opacity=0.2,
        layer="below", line_width=0,
        annotation_text="Recession Risk Zone",
        annotation_position="top right"
    )
    
    # Customize layout
    fig.update_layout(
        title=title,
        xaxis_title="Laufzeit (Jahre)",
        yaxis_title="Yield (%)",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        template="plotly_white",
        height=500,
        hovermode="x unified"
    )
    
    # Add grid lines
    fig.update_xaxes(
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='lightgray'
    )
    fig.update_yaxes(
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='lightgray'
    )
    
    return fig

def plot_price_sensitivity(bond_data: Dict[str, Any]) -> go.Figure:
    """
    Plot bond price sensitivity to yield changes with enhanced visuals
    
    Args:
        bond_data: Dictionary with bond information
        
    Returns:
        Plotly figure object
    """
    # Extract bond info
    years_to_maturity = bond_data.get("Laufzeit", 10)
    ytm = bond_data.get("YTM", 5) / 100
    duration = bond_data.get("Duration", 8)
    convexity = bond_data.get("Convexity", 80)
    
    # Create yield change range
    yield_changes = np.linspace(-0.02, 0.02, 200)  # -2% to +2% in smaller steps for smoother curves
    
    # Calculate price changes
    price_changes_duration = -duration * yield_changes * 100
    price_changes_with_convexity = (-duration * yield_changes + 0.5 * convexity * yield_changes**2) * 100
    
    # Create data frame
    df = pd.DataFrame({
        'Yield Change (bps)': yield_changes * 10000,
        'Duration Only': price_changes_duration,
        'Duration + Convexity': price_changes_with_convexity
    })
    
    # Create plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Yield Change (bps)'],
        y=df['Duration Only'],
        mode='lines',
        name='Linear (Duration)',
        line=dict(color='blue', width=2, shape='spline', smoothing=1.3)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Yield Change (bps)'],
        y=df['Duration + Convexity'],
        mode='lines',
        name='Quadratic (Duration + Convexity)',
        line=dict(color='red', width=3, shape='spline', smoothing=1.3)
    ))
    
    # Add shaded areas to highlight potential profit/loss zones
    fig.add_hrect(
        y0=0, y1=max(df['Duration + Convexity'].max(), df['Duration Only'].max()) + 1,
        fillcolor="lightgreen", opacity=0.2,
        layer="below", line_width=0,
        annotation_text="Profit Zone",
        annotation_position="top right"
    )
    
    fig.add_hrect(
        y0=min(df['Duration + Convexity'].min(), df['Duration Only'].min()) - 1, y1=0,
        fillcolor="lightcoral", opacity=0.2,
        layer="below", line_width=0,
        annotation_text="Loss Zone",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        title=f"{years_to_maturity}-Year Bond Price Sensitivity",
        xaxis_title="Yield Change (basis points)",
        yaxis_title="Price Change (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white"
    )
    
    # Add zero lines
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
    
    return fig

def plot_comparison_chart(bonds: List[Dict[str, Any]], 
                         metric: str = "YTM",
                         title: Optional[str] = None) -> go.Figure:
    """
    Create a bar chart comparing different bonds by a specific metric
    
    Args:
        bonds: List of bond dictionaries
        metric: Metric to compare ('YTM', 'Realzins', 'Duration', 'Convexity')
        title: Custom title for the chart
        
    Returns:
        Plotly figure object
    """
    # Ensure all bonds have the metric
    if not all(metric in bond for bond in bonds):
        raise ValueError(f"Not all bonds have the metric '{metric}'")
    
    # Sort bonds by maturity for consistent presentation
    sorted_bonds = sorted(bonds, key=lambda x: x.get("Laufzeit", 0))
    
    # Create labels
    labels = [f"{bond.get('Name', f'{bond.get('Laufzeit', 'N/A')}y')}" for bond in sorted_bonds]
    
    # Set colors based on metric
    if metric == "YTM" or metric == "Realzins":
        colors = px.colors.sequential.Blues
        color_scale = [colors[min(len(colors)-1, int(i * len(colors) / len(sorted_bonds)))] for i in range(len(sorted_bonds))]
    elif metric == "Duration":
        colors = px.colors.sequential.Oranges
        color_scale = [colors[min(len(colors)-1, int(i * len(colors) / len(sorted_bonds)))] for i in range(len(sorted_bonds))]
    else:
        colors = px.colors.sequential.Greens
        color_scale = [colors[min(len(colors)-1, int(i * len(colors) / len(sorted_bonds)))] for i in range(len(sorted_bonds))]
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=[bond[metric] for bond in sorted_bonds],
        marker_color=color_scale,
        text=[f"{bond[metric]:.2f}" for bond in sorted_bonds],
        textposition='auto',
        hovertemplate="%{x}: %{y:.2f}"
    ))
    
    # Set title
    if title is None:
        title = f"Bond Comparison - {metric}"
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Bond",
        yaxis_title=metric,
        template="plotly_white"
    )
    
    return fig

def plot_yield_curve_3d(bonds_over_time: List[Dict[str, List[Dict[str, Any]]]],
                       metric: str = "YTM",
                       title: str = "3D Yield Curve Evolution") -> go.Figure:
    """
    Create a 3D visualization of yield curve evolution over time
    
    Args:
        bonds_over_time: List of bond dictionaries for different time periods
                        (each entry should have 'date' and 'bonds' keys)
        metric: Metric to visualize ('YTM' or 'Realzins')
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Colors for the different times
    colors = px.colors.sequential.Viridis
    
    for i, period_data in enumerate(bonds_over_time):
        date = period_data.get('date', f'Period {i+1}')
        bonds = period_data.get('bonds', [])
        
        if not bonds:
            continue
            
        # Sort bonds by maturity
        sorted_bonds = sorted(bonds, key=lambda x: x.get("Laufzeit", 0))
        
        # Extract maturities and yields
        maturities = [bond.get("Laufzeit", 0) for bond in sorted_bonds]
        yields = [bond.get(metric, 0) for bond in sorted_bonds]
        
        # Generate smooth curve for nicer visualization
        if len(sorted_bonds) >= 3:
            # More points for a smoother curve
            maturities_smooth = np.linspace(min(maturities), max(maturities), 50)
            
            # Use PCHIP interpolation for yield curve
            pch = PchipInterpolator(maturities, yields)
            yields_smooth = pch(maturities_smooth)
            
            # Plot the smooth curve
            color_idx = min(len(colors)-1, int(i * len(colors) / len(bonds_over_time)))
            
            fig.add_trace(go.Scatter3d(
                x=[date] * len(maturities_smooth),
                y=maturities_smooth,
                z=yields_smooth,
                mode='lines',
                line=dict(color=colors[color_idx], width=5),
                name=date
            ))
        
        # Always plot the actual data points
        fig.add_trace(go.Scatter3d(
            x=[date] * len(maturities),
            y=maturities,
            z=yields,
            mode='markers',
            marker=dict(size=5, color=colors[min(len(colors)-1, int(i * len(colors) / len(bonds_over_time)))]),
            name=f"{date} (actual)",
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='Date',
            yaxis_title='Maturity (Years)',
            zaxis_title=f'{metric} (%)',
            xaxis=dict(gridcolor='lightgray'),
            yaxis=dict(gridcolor='lightgray'),
            zaxis=dict(gridcolor='lightgray')
        ),
        height=700,
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    
    return fig

def plot_historical_yields(historical_data: Dict[str, List[Dict[str, Any]]],
                          bond_type: str = "10-Year",
                          title: Optional[str] = None) -> go.Figure:
    """
    Plot historical yield trends for a specific bond type
    
    Args:
        historical_data: Dictionary with country codes as keys and lists of historical yield data
        bond_type: Bond type to plot (e.g., '10-Year')
        title: Custom title
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Define colors and symbols for different countries
    country_styles = {
        "US": {"color": "blue", "symbol": "circle", "name": "US Treasury"},
        "DE": {"color": "red", "symbol": "square", "name": "German Bund"},
        "UK": {"color": "green", "symbol": "diamond", "name": "UK Gilt"},
        "JP": {"color": "purple", "symbol": "cross", "name": "Japan JGB"}
    }
    
    for country, data_points in historical_data.items():
        if country not in country_styles:
            continue
            
        # Filter data for the specified bond type
        filtered_data = [d for d in data_points if d.get("name", "").startswith(bond_type)]
        
        if not filtered_data:
            continue
            
        # Sort by date
        sorted_data = sorted(filtered_data, key=lambda x: x.get("date"))
        
        # Extract dates and yields
        dates = [d.get("date") for d in sorted_data]
        yields = [d.get("yield", 0) for d in sorted_data]
        
        # Add trace for this country
        fig.add_trace(go.Scatter(
            x=dates,
            y=yields,
            mode='lines+markers',
            name=country_styles[country]["name"],
            line=dict(color=country_styles[country]["color"], width=2, shape='spline', smoothing=1.3),
            marker=dict(symbol=country_styles[country]["symbol"], size=8)
        ))
    
    # Customize layout
    if title is None:
        title = f"Historical {bond_type} Bond Yields"
        
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Yield (%)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def plot_yield_vs_inflation(bonds: List[Dict[str, Any]], 
                           country_name: str = "",
                           title: Optional[str] = None) -> go.Figure:
    """
    Plot yield vs inflation for bonds of different maturities
    
    Args:
        bonds: List of bond dictionaries
        country_name: Name of the country for the title
        title: Custom title
        
    Returns:
        Plotly figure object
    """
    # Extract data
    maturities = []
    yields = []
    real_yields = []
    inflation_rates = []
    
    for bond in bonds:
        if "Laufzeit" in bond and "YTM" in bond and "Inflation" in bond:
            maturities.append(bond["Laufzeit"])
            yields.append(bond["YTM"])
            inflation_rates.append(bond["Inflation"])
            
            # Calculate real yield if not provided
            if "Realzins" in bond:
                real_yields.append(bond["Realzins"])
            else:
                nominal = bond["YTM"] / 100
                inflation = bond["Inflation"] / 100
                real = ((1 + nominal) / (1 + inflation) - 1) * 100
                real_yields.append(real)
    
    # Create figure
    fig = go.Figure()
    
    # Add yield bar
    fig.add_trace(go.Bar(
        x=maturities,
        y=yields,
        name="Nominal Yield",
        marker_color="royalblue",
        opacity=0.7
    ))
    
    # Add inflation bar
    fig.add_trace(go.Bar(
        x=maturities,
        y=inflation_rates,
        name="Inflation",
        marker_color="red",
        opacity=0.7
    ))
    
    # Add real yield line
    fig.add_trace(go.Scatter(
        x=maturities,
        y=real_yields,
        mode="lines+markers",
        name="Real Yield",
        line=dict(color="green", width=3),
        marker=dict(size=10)
    ))
    
    # Set title
    if title is None:
        if country_name:
            title = f"Yield vs Inflation: {country_name}"
        else:
            title = "Yield vs Inflation Analysis"
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Maturity (Years)",
        yaxis_title="Rate (%)",
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    return fig

def plot_bond_risk_return(bonds: List[Dict[str, Any]], 
                         title: str = "Bond Risk-Return Profile") -> go.Figure:
    """
    Create a risk-return scatter plot for bonds
    
    Args:
        bonds: List of bond dictionaries
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Extract data
    names = []
    yields = []
    durations = []
    maturities = []
    real_yields = []
    
    for bond in bonds:
        if "Name" in bond and "YTM" in bond and "Mod. Duration" in bond:
            names.append(bond["Name"])
            yields.append(bond["YTM"])
            durations.append(bond["Mod. Duration"])
            maturities.append(bond.get("Laufzeit", 0))
            real_yields.append(bond.get("Realzins", 0))
    
    # Create bubble chart
    fig = go.Figure()
    
    # Bubble size based on maturity
    sizes = [max(10, m * 5) for m in maturities]
    
    # Color based on real yield
    colorscale = [[0, 'red'], [0.5, 'yellow'], [1.0, 'green']]
    
    fig.add_trace(go.Scatter(
        x=durations,
        y=yields,
        mode='markers',
        text=names,
        marker=dict(
            size=sizes,
            sizemode='area',
            sizeref=2.*max(sizes)/(40.**2),
            color=real_yields,
            colorscale=colorscale,
            colorbar=dict(title="Real Yield (%)"),
            line=dict(width=1, color='black')
        ),
        hovertemplate="<b>%{text}</b><br>YTM: %{y:.2f}%<br>Duration: %{x:.2f}<br>Maturity: %{marker.size:.1f} years<br>Real Yield: %{marker.color:.2f}%<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Modified Duration (Risk)",
        yaxis_title="Yield to Maturity (%)",
        template="plotly_white",
        height=600
    )
    
    # Add trend line
    if len(yields) >= 2:
        z = np.polyfit(durations, yields, 1)
        p = np.poly1d(z)
        
        x_trend = np.linspace(min(durations), max(durations), 100)
        y_trend = p(x_trend)
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            name='Trend',
            line=dict(color='rgba(0,0,0,0.3)', width=2, dash='dash')
        ))
    
    return fig 