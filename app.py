import streamlit as st
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import plotly.graph_objects as go
import datetime

import logging
logging.basicConfig(level=logging.DEBUG)

# Import our modules
from bonds import (
    calculate_ytm, 
    real_yield, 
    calculate_duration, 
    calculate_modified_duration,
    calculate_convexity,
    get_price_impact
)
from plots import (
    plot_yield_curve, 
    plot_price_sensitivity, 
    plot_comparison_chart,
    plot_yield_curve_3d,
    plot_historical_yields,
    plot_yield_vs_inflation,
    plot_bond_risk_return
)
from market_data import fetch_market_data, update_predefined_bonds_with_market_data

# Set page config
st.set_page_config(
    page_title="Bond Yield Curve Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load predefined bonds
@st.cache_data
def load_predefined_bonds():
    data_path = Path(__file__).parent / "data" / "predefined_bonds.json"
    with open(data_path, "r") as f:
        return json.load(f)

def format_percentage(value, decimals=2):
    """Format a number as a percentage with specified decimals."""
    return f"{value:.{decimals}f}%"

def format_currency(value, currency="€", decimals=2):
    """Format a number as currency with specified decimals."""
    return f"{currency} {value:.{decimals}f}"

def main():
    # Add custom CSS
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2 {
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0e0ef;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Bond Yield Curve Simulator")
        st.write("Interaktiver Simulator für Anleihen und Zinsstrukturkurven")
    
    with col2:
        st.image("https://img.icons8.com/fluency/96/bonds.png", width=80)
    
    # Sidebar
    with st.sidebar:
        st.header("Einstellungen")
        
        # Country selection
        predefined_bonds = load_predefined_bonds()
        countries = {
            "US": "🇺🇸 USA",
            "DE": "🇩🇪 Deutschland",
            "UK": "🇬🇧 Großbritannien",
            "JP": "🇯🇵 Japan"
        }
        
        selected_country = st.selectbox(
            "Land auswählen", 
            list(countries.keys()),
            format_func=lambda x: countries.get(x, x)
        )
        
        # Add the sync button for fetching live data
        sync_col1, sync_col2 = st.columns([3, 1])
        with sync_col1:
            st.write("Echtzeit-Marktdaten:")
        with sync_col2:
            if st.button("🔄 Sync", help="Lädt aktuelle Marktdaten für die ausgewählten Anleihen"):
                with st.spinner("Lade Marktdaten..."):
                    try:
                        # Fetch live market data
                        market_data = fetch_market_data(selected_country)
                        
                        if market_data and "bonds" in market_data:
                            # Update predefined bonds with fetched data
                            update_predefined_bonds_with_market_data()
                            
                            # Clear cache to load new data
                            st.cache_data.clear()
                            
                            # Reload predefined bonds
                            predefined_bonds = load_predefined_bonds()
                            
                            # Show success message
                            st.success(f"Marktdaten für {countries[selected_country]} aktualisiert! ({datetime.datetime.now().strftime('%H:%M:%S')})")
                        else:
                            st.error("Keine Daten verfügbar.")
                    except Exception as e:
                        st.error(f"Fehler beim Abrufen der Daten: {str(e)}")
        
        st.divider()
        
        # Load mode
        load_mode = st.radio(
            "Datenquelle",
            ["Vordefinierte Anleihen", "Eigene Anleihen"]
        )
        
        if load_mode == "Vordefinierte Anleihen":
            st.info(f"Lädt Standard-Staatsanleihen für {countries[selected_country]}.")
            
        st.divider()
        
        # Display options
        st.subheader("Anzeigeoptionen")
        show_real_yield = st.checkbox("Realzins anzeigen", value=True)
        show_additional_metrics = st.checkbox("Erweiterte Metriken", value=False)
        
        # Add visualization options
        st.subheader("Visualisierung")
        smooth_curves = st.checkbox("Glatte Kurven", value=True)
        show_advanced_charts = st.checkbox("Erweiterte Graphen", value=True)
        
        # Add a reset button 
        if st.button("Zurücksetzen", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Initialize session state for bonds if not exists
    if "bonds" not in st.session_state:
        st.session_state.bonds = []
    
    # Main area - Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Yield Curve", "🧮 Bond-Rechner", "📋 Analyse"])
    
    with tab1:
        # Bond input section
        st.header("Anleihen-Parameter")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if load_mode == "Vordefinierte Anleihen":
                if st.button("Vordefinierte Anleihen laden", use_container_width=True):
                    # Load predefined bonds for the selected country
                    country_data = predefined_bonds.get(selected_country, {})
                    st.session_state.bonds = []
                    
                    for bond in country_data.get("bonds", []):
                        # Calculate metrics
                        ytm = calculate_ytm(
                            bond["price"], 
                            bond["face_value"], 
                            bond["coupon_rate"] / 100, 
                            bond["years_to_maturity"]
                        )
                        
                        real = real_yield(ytm, bond["inflation"] / 100)
                        
                        duration = calculate_duration(
                            bond["price"],
                            bond["face_value"],
                            bond["coupon_rate"] / 100,
                            ytm,
                            bond["years_to_maturity"]
                        )
                        
                        mod_duration = calculate_modified_duration(duration, ytm)
                        
                        convexity = calculate_convexity(
                            bond["price"],
                            bond["face_value"],
                            bond["coupon_rate"] / 100,
                            ytm,
                            bond["years_to_maturity"]
                        )
                        
                        st.session_state.bonds.append({
                            "Name": bond["name"],
                            "Laufzeit": bond["years_to_maturity"],
                            "Kupon": bond["coupon_rate"],
                            "Preis": bond["price"],
                            "Inflation": bond["inflation"],
                            "YTM": ytm * 100,
                            "Realzins": real * 100,
                            "Duration": duration,
                            "Mod. Duration": mod_duration,
                            "Convexity": convexity
                        })
            
            num_custom_bonds = st.number_input(
                "Anzahl eigener Anleihen", 
                min_value=0, 
                max_value=10, 
                value=0 if st.session_state.bonds else 4,
                step=1,
                help="Füge bis zu 10 eigene Anleihen hinzu"
            )
        
        # Show the bonds table with editable fields
        if len(st.session_state.bonds) > 0 or num_custom_bonds > 0:
            # Create a DataFrame from existing bonds
            if st.session_state.bonds:
                df = pd.DataFrame(st.session_state.bonds)
            else:
                # Create default bonds if none exist
                df = pd.DataFrame([
                    {"Name": "2-Jahr", "Laufzeit": 2, "Kupon": 3.0, "Preis": 995, "Inflation": 2.0},
                    {"Name": "5-Jahr", "Laufzeit": 5, "Kupon": 3.2, "Preis": 990, "Inflation": 2.0},
                    {"Name": "10-Jahr", "Laufzeit": 10, "Kupon": 3.5, "Preis": 980, "Inflation": 2.0},
                    {"Name": "30-Jahr", "Laufzeit": 30, "Kupon": 4.0, "Preis": 950, "Inflation": 2.0},
                ][:num_custom_bonds])
            
            # Create a form for editing bonds
            with st.form("bond_form"):
                edited_df = st.data_editor(
                    df,
                    num_rows="fixed" if st.session_state.bonds else num_custom_bonds,
                    column_config={
                        "Name": st.column_config.TextColumn("Name", width="medium"),
                        "Laufzeit": st.column_config.NumberColumn("Laufzeit (Jahre)", min_value=0.25, max_value=100, step=0.25, width="small"),
                        "Kupon": st.column_config.NumberColumn("Kupon (%)", min_value=0.0, max_value=20.0, step=0.1, format="%.2f %%", width="small"),
                        "Preis": st.column_config.NumberColumn("Preis", min_value=500, max_value=1500, step=0.1, format="%.2f", width="small"),
                        "Inflation": st.column_config.NumberColumn("Inflation (%)", min_value=-5.0, max_value=20.0, step=0.1, format="%.2f %%", width="small"),
                    },
                    hide_index=True,
                )
                
                calculate_button = st.form_submit_button("Berechnen", use_container_width=True)
                
                if calculate_button:
                    # Calculate all metrics for each bond
                    updated_bonds = []
                    for _, row in edited_df.iterrows():
                        # Calculate YTM
                        ytm = calculate_ytm(
                            row["Preis"], 
                            1000, 
                            row["Kupon"] / 100, 
                            row["Laufzeit"]
                        )
                        
                        # Calculate real yield
                        real = real_yield(ytm, row["Inflation"] / 100)
                        
                        # Calculate duration
                        duration = calculate_duration(
                            row["Preis"],
                            1000,
                            row["Kupon"] / 100,
                            ytm,
                            row["Laufzeit"]
                        )
                        
                        # Calculate modified duration
                        mod_duration = calculate_modified_duration(duration, ytm)
                        
                        # Calculate convexity
                        convexity = calculate_convexity(
                            row["Preis"],
                            1000,
                            row["Kupon"] / 100,
                            ytm,
                            row["Laufzeit"]
                        )
                        
                        # Append to updated bonds
                        updated_bonds.append({
                            "Name": row["Name"],
                            "Laufzeit": row["Laufzeit"],
                            "Kupon": row["Kupon"],
                            "Preis": row["Preis"],
                            "Inflation": row["Inflation"],
                            "YTM": ytm * 100,
                            "Realzins": real * 100,
                            "Duration": duration,
                            "Mod. Duration": mod_duration,
                            "Convexity": convexity
                        })
                    
                    # Update session state
                    st.session_state.bonds = updated_bonds
                    st.rerun()
            
            # After form submission, show results
            if st.session_state.bonds:
                # Sort bonds by maturity
                sorted_bonds = sorted(st.session_state.bonds, key=lambda x: x["Laufzeit"])
                
                # Create a metrics table
                metrics_df = pd.DataFrame([
                    {
                        "Name": bond["Name"],
                        "Laufzeit (Jahre)": bond["Laufzeit"],
                        "YTM (%)": f"{bond['YTM']:.2f}",
                        "Realzins (%)": f"{bond['Realzins']:.2f}",
                        "Duration": f"{bond['Duration']:.2f}",
                        "Mod. Duration": f"{bond['Mod. Duration']:.2f}"
                    }
                    for bond in sorted_bonds
                ])
                
                with st.expander("Bond-Metriken", expanded=True):
                    st.dataframe(
                        metrics_df,
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Plot yield curve
                st.header("Zinsstrukturkurve")
                fig = plot_yield_curve(
                    sorted_bonds, 
                    title=f"Yield Curve - {countries.get(selected_country, 'Custom')}",
                    show_real_yield=show_real_yield
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Additional visualization
                if show_additional_metrics:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # YTM comparison chart
                        fig_ytm = plot_comparison_chart(
                            sorted_bonds, 
                            metric="YTM", 
                            title="Vergleich der Renditen (YTM)"
                        )
                        st.plotly_chart(fig_ytm, use_container_width=True)
                    
                    with col2:
                        # Duration comparison chart
                        fig_duration = plot_comparison_chart(
                            sorted_bonds, 
                            metric="Duration", 
                            title="Vergleich der Duration"
                        )
                        st.plotly_chart(fig_duration, use_container_width=True)
                
                # Add advanced visualizations with smooth curves and complex charts
                if smooth_curves and show_advanced_charts:
                    st.subheader("Erweiterte Visualisierungen")
                    
                    # Create tabs for different advanced visualizations
                    adv_tab1, adv_tab2, adv_tab3 = st.tabs(["Inflation vs Yield", "Risk/Return", "Marktanalyse"])
                    
                    with adv_tab1:
                        # Get country name for the title
                        country_name = countries.get(selected_country, "Custom")
                        
                        # Plot yield vs inflation
                        fig_inflation = plot_yield_vs_inflation(
                            sorted_bonds,
                            country_name=country_name.split(" ", 1)[1] if " " in country_name else country_name,
                            title=f"Yield vs Inflation: {country_name}"
                        )
                        
                        st.plotly_chart(fig_inflation, use_container_width=True)
                        
                        st.markdown("""
                        ### Interpretation:
                        - **Nominal Yield**: Die erwartete Rendite ohne Berücksichtigung der Inflation
                        - **Inflation**: Die erwartete Inflationsrate
                        - **Real Yield**: Inflationsbereinigte Rendite (Nominal Yield - Inflation)
                        
                        Ein positiver Realzins bedeutet, dass die Anleihe die Kaufkraft über die Zeit erhält.
                        """)
                    
                    with adv_tab2:
                        # Plot risk/return bubble chart
                        fig_risk = plot_bond_risk_return(
                            sorted_bonds,
                            title=f"Bond Risk-Return Profile - {country_name}"
                        )
                        
                        st.plotly_chart(fig_risk, use_container_width=True)
                        
                        st.markdown("""
                        ### Interpretation:
                        - **X-Achse**: Modified Duration (Risikomaß - höhere Werte bedeuten mehr Zinsrisiko)
                        - **Y-Achse**: Yield to Maturity (Rendite)
                        - **Blasengröße**: Laufzeit der Anleihe
                        - **Farbe**: Realzins (grün = höher, rot = niedriger)
                        
                        Die Trendlinie zeigt die typische Beziehung zwischen Risiko und Rendite.
                        """)
                    
                    with adv_tab3:
                        # Price sensitivity for a selected bond
                        selected_bond_name = st.selectbox(
                            "Anleihe für Preissensitivitätsanalyse:",
                            options=[bond["Name"] for bond in sorted_bonds],
                            index=0
                        )
                        
                        # Find the selected bond
                        selected_bond = next(
                            (bond for bond in sorted_bonds if bond["Name"] == selected_bond_name),
                            sorted_bonds[0]
                        )
                        
                        # Plot price sensitivity with enhanced visuals
                        fig_sensitivity = plot_price_sensitivity(selected_bond)
                        st.plotly_chart(fig_sensitivity, use_container_width=True)
                        
                        # Add some explanatory text
                        st.markdown(f"""
                        ### Preissensitivität für {selected_bond_name}:
                        - **Duration**: {selected_bond.get("Duration", 0):.2f} Jahre
                        - **Modified Duration**: {selected_bond.get("Mod. Duration", 0):.2f}
                        - **Convexity**: {selected_bond.get("Convexity", 0):.2f}
                        
                        Die Grafik zeigt, wie der Preis auf Zinsänderungen reagiert. Die rote Kurve (mit Convexity) 
                        ist präziser für größere Zinsänderungen als die blaue Kurve (nur Duration).
                        """)
        else:
            st.info("Bitte wähle vordefinierte Anleihen oder füge eigene hinzu.")
    
    with tab2:
        st.header("Bond-Rechner")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Parameter")
            
            face_value = st.number_input(
                "Nennwert (Face Value)", 
                min_value=500, 
                max_value=10000, 
                value=1000,
                step=100
            )
            
            price = st.number_input(
                "Marktpreis", 
                min_value=500.0, 
                max_value=1500.0, 
                value=980.0,
                step=0.1
            )
            
            coupon_rate = st.number_input(
                "Kuponzins (%)", 
                min_value=0.0, 
                max_value=20.0, 
                value=3.5,
                step=0.1
            )
            
            years = st.number_input(
                "Laufzeit (Jahre)", 
                min_value=0.25, 
                max_value=100.0, 
                value=10.0,
                step=0.25
            )
            
            frequency = st.selectbox(
                "Zahlungsfrequenz", 
                [("Jährlich", 1), ("Halbjährlich", 2), ("Vierteljährlich", 4)],
                format_func=lambda x: x[0]
            )[1]
            
            inflation_rate = st.number_input(
                "Inflationsrate (%)", 
                min_value=-5.0, 
                max_value=20.0, 
                value=2.0,
                step=0.1
            )
            
            if st.button("Berechnen", use_container_width=True):
                # Calculate YTM
                ytm = calculate_ytm(
                    price, 
                    face_value, 
                    coupon_rate / 100, 
                    years,
                    frequency
                )
                
                # Calculate other metrics
                real_rate = real_yield(ytm, inflation_rate / 100)
                duration = calculate_duration(
                    price, 
                    face_value, 
                    coupon_rate / 100, 
                    ytm, 
                    years, 
                    frequency
                )
                mod_duration = calculate_modified_duration(
                    duration, 
                    ytm, 
                    frequency
                )
                convexity = calculate_convexity(
                    price, 
                    face_value, 
                    coupon_rate / 100, 
                    ytm, 
                    years, 
                    frequency
                )
                
                # Store in session state
                st.session_state.single_bond_result = {
                    "YTM": ytm * 100,
                    "Realzins": real_rate * 100,
                    "Duration": duration,
                    "Mod. Duration": mod_duration,
                    "Convexity": convexity,
                    "Laufzeit": years,
                    "Kupon": coupon_rate
                }
        
        with col2:
            st.subheader("Ergebnisse")
            
            if "single_bond_result" in st.session_state:
                result = st.session_state.single_bond_result
                
                # Display metrics in a nice format
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Yield to Maturity (YTM)", 
                        format_percentage(result["YTM"])
                    )
                    st.metric(
                        "Kuponzins", 
                        format_percentage(coupon_rate)
                    )
                
                with col2:
                    st.metric(
                        "Realzins", 
                        format_percentage(result["Realzins"])
                    )
                    st.metric(
                        "Macaulay Duration", 
                        f"{result['Duration']:.2f} Jahre"
                    )
                
                with col3:
                    st.metric(
                        "Modified Duration", 
                        f"{result['Mod. Duration']:.2f}"
                    )
                    st.metric(
                        "Convexity", 
                        f"{result['Convexity']:.2f}"
                    )
                
                # Price sensitivity analysis
                st.subheader("Preissensitivität")
                
                fig_sensitivity = plot_price_sensitivity(result)
                st.plotly_chart(fig_sensitivity, use_container_width=True)
                
                # What if analysis for yield changes
                st.subheader("Rendite-Änderung Szenario")
                
                yield_change_bps = st.slider(
                    "Änderung der Rendite (Basispunkte)", 
                    min_value=-200, 
                    max_value=200, 
                    value=0,
                    step=10
                )
                
                yield_change = yield_change_bps / 10000
                price_impact = get_price_impact(
                    result["Mod. Duration"], 
                    result["Convexity"], 
                    yield_change
                )
                
                new_price = price * (1 + price_impact / 100)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Preisänderung", 
                        format_percentage(price_impact),
                        delta=f"{price_impact:.2f}%"
                    )
                
                with col2:
                    st.metric(
                        "Neuer Preis", 
                        format_currency(new_price, "€"),
                        delta=f"{new_price - price:.2f}"
                    )
            else:
                st.info("Gib die Parameter ein und klicke auf 'Berechnen'.")
    
    with tab3:
        st.header("Anleihen-Analyse")
        
        if not st.session_state.bonds:
            st.warning("Bitte füge zuerst Anleihen im 'Yield Curve' Tab hinzu.")
        else:
            # Sort bonds by maturity
            sorted_bonds = sorted(st.session_state.bonds, key=lambda x: x["Laufzeit"])
            
            st.subheader("Übersicht")
            
            # Create a detailed table of all bonds and all metrics
            detailed_df = pd.DataFrame([
                {
                    "Name": bond["Name"],
                    "Laufzeit (Jahre)": bond["Laufzeit"],
                    "Kupon (%)": bond["Kupon"],
                    "Preis": bond["Preis"],
                    "Inflation (%)": bond["Inflation"],
                    "YTM (%)": bond["YTM"],
                    "Realzins (%)": bond["Realzins"],
                    "Duration": bond["Duration"],
                    "Mod. Duration": bond["Mod. Duration"],
                    "Convexity": bond["Convexity"]
                }
                for bond in sorted_bonds
            ])
            
            st.dataframe(detailed_df, hide_index=True, use_container_width=True)
            
            # Yield spreads
            st.subheader("Yield Spreads")
            
            if len(sorted_bonds) > 1:
                spreads = []
                for i in range(len(sorted_bonds) - 1):
                    for j in range(i + 1, len(sorted_bonds)):
                        bond_i = sorted_bonds[i]
                        bond_j = sorted_bonds[j]
                        spread = bond_j["YTM"] - bond_i["YTM"]
                        spreads.append({
                            "Von": bond_i["Name"],
                            "Zu": bond_j["Name"],
                            "Spread (bps)": spread * 100,
                            "Laufzeitdifferenz (Jahre)": bond_j["Laufzeit"] - bond_i["Laufzeit"]
                        })
                
                spreads_df = pd.DataFrame(spreads)
                st.dataframe(spreads_df, hide_index=True, use_container_width=True)
            
            # Analysis plots
            st.subheader("Visualisierungen")
            
            tab_ytm, tab_duration, tab_convexity = st.tabs(["Yield", "Duration", "Convexity"])
            
            with tab_ytm:
                # Plot YTM vs Maturity
                fig_ytm = go.Figure()
                
                fig_ytm.add_trace(go.Scatter(
                    x=[b["Laufzeit"] for b in sorted_bonds],
                    y=[b["YTM"] for b in sorted_bonds],
                    mode="lines+markers+text",
                    name="YTM",
                    text=[b["Name"] for b in sorted_bonds],
                    textposition="top center",
                    line=dict(color='blue', width=3),
                    marker=dict(size=12)
                ))
                
                fig_ytm.update_layout(
                    title="Yield to Maturity vs. Laufzeit",
                    xaxis_title="Laufzeit (Jahre)",
                    yaxis_title="YTM (%)",
                    template="plotly_white",
                    height=500
                )
                
                st.plotly_chart(fig_ytm, use_container_width=True)
            
            with tab_duration:
                # Plot Duration vs YTM
                fig_dur = go.Figure()
                
                fig_dur.add_trace(go.Scatter(
                    x=[b["YTM"] for b in sorted_bonds],
                    y=[b["Duration"] for b in sorted_bonds],
                    mode="markers+text",
                    name="Duration",
                    text=[b["Name"] for b in sorted_bonds],
                    textposition="top center",
                    marker=dict(
                        size=[b["Laufzeit"] * 2 for b in sorted_bonds],
                        color=[b["Laufzeit"] for b in sorted_bonds],
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title="Laufzeit (Jahre)")
                    )
                ))
                
                fig_dur.update_layout(
                    title="Duration vs. YTM",
                    xaxis_title="YTM (%)",
                    yaxis_title="Duration (Jahre)",
                    template="plotly_white",
                    height=500
                )
                
                st.plotly_chart(fig_dur, use_container_width=True)
            
            with tab_convexity:
                # Plot Convexity vs Duration
                fig_conv = go.Figure()
                
                fig_conv.add_trace(go.Scatter(
                    x=[b["Duration"] for b in sorted_bonds],
                    y=[b["Convexity"] for b in sorted_bonds],
                    mode="markers+text",
                    name="Convexity",
                    text=[b["Name"] for b in sorted_bonds],
                    textposition="top center",
                    marker=dict(
                        size=[b["YTM"] * 3 for b in sorted_bonds],
                        color=[b["YTM"] for b in sorted_bonds],
                        colorscale="Plasma",
                        showscale=True,
                        colorbar=dict(title="YTM (%)")
                    )
                ))
                
                fig_conv.update_layout(
                    title="Convexity vs. Duration",
                    xaxis_title="Duration (Jahre)",
                    yaxis_title="Convexity",
                    template="plotly_white",
                    height=500
                )
                
                st.plotly_chart(fig_conv, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption("Bond Yield Curve Simulator | Erstellt mit Streamlit")

if __name__ == "__main__":
    main() 