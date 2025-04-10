import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

def plot_yield_curve(bonds: List[Dict[str, Any]], 
                    title: str = "Yield Curve",
                    show_real_yield: bool = False) -> go.Figure:
    """
    Plot yield curve from bond data
    
    Args:
        bonds: List of bond dictionaries with keys 'Laufzeit', 'YTM', and optionally 'Realzins'
        title: Title of the plot
        show_real_yield: Whether to plot real yield
        
    Returns:
        Plotly figure object
    """
    # Sort bonds by maturity
    sorted_bonds = sorted(bonds, key=lambda x: x["Laufzeit"])
    
    # Create figure
    fig = go.Figure()
    
    # Add nominal yield curve
    fig.add_trace(go.Scatter(
        x=[b["Laufzeit"] for b in sorted_bonds],
        y=[b["YTM"] for b in sorted_bonds],
        mode="lines+markers",
        name="Nominal Yield",
        line=dict(color='blue', width=3),
        marker=dict(size=10, symbol='circle')
    ))
    
    # Add real yield curve if requested
    if show_real_yield and all("Realzins" in b for b in sorted_bonds):
        fig.add_trace(go.Scatter(
            x=[b["Laufzeit"] for b in sorted_bonds],
            y=[b["Realzins"] for b in sorted_bonds],
            mode="lines+markers",
            name="Real Yield",
            line=dict(color='green', width=3, dash='dash'),
            marker=dict(size=10, symbol='square')
        ))
    
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
        height=500
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
    Plot bond price sensitivity to yield changes
    
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
    yield_changes = pd.Series(range(-200, 201, 10)) / 10000  # -2% to +2% in 0.1% steps
    
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
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Yield Change (bps)'],
        y=df['Duration + Convexity'],
        mode='lines',
        name='Quadratic (Duration + Convexity)',
        line=dict(color='red', width=3)
    ))
    
    fig.update_layout(
        title=f"{years_to_maturity}-Year Bond Price Sensitivity",
        xaxis_title="Yield Change (basis points)",
        yaxis_title="Price Change (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
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
    
    # Create labels
    labels = [f"{bond.get('Laufzeit', 'N/A')}y" for bond in bonds]
    
    # Set colors based on metric
    if metric == "YTM" or metric == "Realzins":
        colors = px.colors.sequential.Blues
    elif metric == "Duration":
        colors = px.colors.sequential.Oranges
    else:
        colors = px.colors.sequential.Greens
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=[bond[metric] for bond in bonds],
        marker_color=colors[len(colors) // 2],
        text=[f"{bond[metric]:.2f}" for bond in bonds],
        textposition='auto'
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