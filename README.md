# Bond Yield Curve Simulator

Ein interaktiver Simulator für Anleihen und Zinsstrukturkurven mit grafischer Benutzeroberfläche in Streamlit.

![Bond Simulator Screenshot](https://img.icons8.com/fluency/96/bonds.png)

## Funktionen

- Interaktive Benutzeroberfläche mit Streamlit
- Vordefinierte Staatsanleihen für verschiedene Länder (USA, Deutschland, Großbritannien, Japan)
- Eigene Anleihen konfigurieren und analysieren
- Zinsstrukturkurve visualisieren (Yield Curve)
- Realzins (inflationsbereinigt) anzeigen
- Erweiterte Metriken: Duration, Modified Duration, Convexity
- Preissensitivitätsanalyse für Zinsänderungen
- Yield Spread Berechnung
- Verschiedene Visualisierungen und Analysen

## Installation

1. Stellen Sie sicher, dass Python 3.8+ installiert ist
2. Klonen Sie das Repository
3. Installieren Sie die erforderlichen Pakete:

```
pip install -r requirements.txt
```

## Ausführung

Wechseln Sie in das Verzeichnis `bond_simulator` und führen Sie den folgenden Befehl aus:

```
streamlit run app.py
```

Der Browser sollte sich automatisch öffnen und die Anwendung anzeigen.

## Verwendung

1. **Yield Curve Tab**:
   - Wählen Sie ein Land im Sidebar
   - Laden Sie vordefinierte Anleihen oder erstellen Sie eigene
   - Passen Sie Parameter wie Laufzeit, Kupon, Preis und Inflation an
   - Sehen Sie die berechnete Yield Curve und weitere Metriken

2. **Bond-Rechner Tab**:
   - Berechnen Sie detaillierte Metriken für eine einzelne Anleihe
   - Analysieren Sie die Preissensitivität bei Zinsänderungen

3. **Analyse Tab**:
   - Sehen Sie detaillierte Metriken für alle Anleihen
   - Analysieren Sie Yield Spreads zwischen verschiedenen Laufzeiten
   - Verschiedene Visualisierungen für YTM, Duration und Convexity

## Technologien

- Python 3.8+
- Streamlit für die Benutzeroberfläche
- Plotly für interaktive Visualisierungen
- NumPy und SciPy für mathematische Berechnungen
- Pandas für Datenmanipulation

## Lizenz

MIT 