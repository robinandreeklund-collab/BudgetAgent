# Modulintegration i BudgetAgent

Detta dokument beskriver hur modulerna i BudgetAgent samarbetar och integreras med varandra.

## Datamodeller (models.py)

Alla moduler använder gemensamma Pydantic-modeller för att säkerställa konsistent datatyper:

- **Transaction**: Representerar banktransaktioner
- **Bill**: Representerar fakturor och betalningar
- **Income**: Representerar inkomster
- **ForecastData**: Representerar prognosdata
- **AlertConfig**: Konfiguration för varningar
- **Scenario**: Hypotetiska scenarier för analys

## Modulflöden

### 1. Import och Kategorisering av Transaktioner

```
import_bank_data.py → parse_transactions.py → categorize_expenses.py
```

**Steg:**
1. `import_bank_data.load_file()` - Läser bankfil
2. `import_bank_data.detect_format()` - Identifierar bankformat
3. `import_bank_data.normalize_columns()` - Standardiserar kolumnnamn
4. `parse_transactions.parse_dates()` - Konverterar datum
5. `parse_transactions.clean_descriptions()` - Rensar beskrivningar
6. `categorize_expenses.categorize_transactions()` - Tilldelar kategorier

**Resultat:** Lista med `Transaction`-objekt

### 2. Hantering av Fakturor från PDF

```
parse_pdf_bills.py → upcoming_bills.py → forecast_engine.py
```

**Steg:**
1. `parse_pdf_bills.extract_text_from_pdf()` - Extraherar text från PDF
2. `parse_pdf_bills.extract_bills_from_text()` - Skapar `Bill`-objekt
3. `parse_pdf_bills.validate_bill_structure()` - Validerar struktur
4. `upcoming_bills.add_bill()` - Registrerar i systemet
5. `forecast_engine.inject_future_income_and_bills()` - Inkluderar i prognos

**Resultat:** Fakturor registrerade och inkluderade i prognos

### 3. Inkomsthantering och Prognos

```
income_tracker.py → forecast_engine.py → dashboard_ui.py
```

**Steg:**
1. `income_tracker.add_income()` - Registrerar inkomst
2. `income_tracker.forecast_income()` - Prognostiserar framtida inkomster
3. `forecast_engine.inject_future_income_and_bills()` - Kombinerar med fakturor
4. `forecast_engine.simulate_monthly_balance()` - Simulerar saldo
5. `dashboard_ui.update_forecast_graph()` - Visualiserar i dashboard

**Resultat:** Lista med `ForecastData`-objekt, visas grafiskt

### 4. Ekonomisk Analys och Varningar

```
[Transaction-lista] → alerts_and_insights.py → dashboard_ui.py
```

**Steg:**
1. Samla historiska `Transaction`-objekt
2. `alerts_and_insights.check_budget_thresholds()` - Kontrollerar trösklar
3. `alerts_and_insights.generate_insights()` - Genererar insikter
4. `alerts_and_insights.recommend_actions()` - Ger rekommendationer
5. Visa i dashboard

**Resultat:** Varningar och rekommendationer

### 5. Agentfrågor

```
dashboard_ui.py → query_parser.py → [relevanta moduler] → dashboard_ui.py
```

**Steg:**
1. Användare skriver fråga i `dashboard_ui.agent_query_interface()`
2. `query_parser.parse_query()` - Identifierar intent och parametrar
3. `query_parser.execute_query()` - Anropar rätt handler
4. Handler anropar relevanta moduler (t.ex. `upcoming_bills.get_upcoming_bills()`)
5. Svar returneras till dashboard

**Exempel:**
- "Visa alla fakturor i december" → `upcoming_bills.get_upcoming_bills("2025-12")`
- "Hur mycket har vi kvar i januari?" → `forecast_engine.simulate_monthly_balance()`
- "Vad händer om vi får 5000 kr extra?" → `forecast_engine.compare_scenarios()`

### 6. Komplett Månadsuppdatering (workflow.py)

```
workflow.full_monthly_update()
```

**Orkestrerar:**
1. Import av nya transaktioner
2. Automatisk kategorisering
3. Uppdatering av prognoser
4. Kontroll av varningar
5. Generering av månadsrapport

## Funktionssignaturer och Dataflöde

### Import och Parse
```python
# Input: Filsökväg
file_path: str

# Output: Transaction-lista
transactions: List[Transaction]
```

### Kategorisering
```python
# Input: Transaktioner och regler
transactions: List[Transaction]
rules: Dict

# Output: Kategoriserade transaktioner
categorized: List[Transaction]
```

### Fakturhantering
```python
# Input: Bill-objekt
bill: Bill

# Output: Registrerad i system
upcoming_bills.add_bill(bill)

# Query: Hämta fakturor för månad
bills: List[Bill] = upcoming_bills.get_upcoming_bills(month="2025-12")
```

### Inkomstspårning
```python
# Input: Income-objekt
income: Income

# Output: Registrerad i system
income_tracker.add_income(income)

# Query: Prognostisera framtida inkomster
future_income: List[Income] = income_tracker.forecast_income(months=6)
```

### Prognostisering
```python
# Input: Inkomster och fakturor
income: List[Income]
bills: List[Bill]

# Process: Simulera framtida saldo
forecast: List[ForecastData] = forecast_engine.simulate_monthly_balance(months=6)

# Compare: Jämför scenarier
scenarios: List[Scenario]
results: Dict[str, List[ForecastData]] = forecast_engine.compare_scenarios(scenarios)
```

### Analys och Varningar
```python
# Input: Transaktionsdata och konfiguration
data: pd.DataFrame
alert_config: AlertConfig

# Output: Varningar och insikter
alerts: List[str] = alerts_and_insights.check_budget_thresholds(data, alert_config)
insights: List[str] = alerts_and_insights.generate_insights(data)
```

### Dashboard och Agentfrågor
```python
# Dash layout
app.layout = dashboard_ui.create_app_layout()

# Agentfråga
query: str = "Visa alla fakturor i december"
answer: str = query_parser.answer_query(query)
```

## Exempel på Komplett Integration

### Scenario: Ny månad, importera transaktioner och visa prognos

```python
from budgetagent.modules import workflow

# 1. Importera och kategorisera nya transaktioner
transactions = workflow.import_and_categorize_transactions(
    file_path="data/bank_export.csv"
)

# 2. Generera komplett prognos
forecast = workflow.generate_complete_forecast(months=6)

# 3. Analysera och generera varningar
alert_config = workflow.load_alert_config()
analysis = workflow.analyze_and_alert(transactions, alert_config)

# 4. Visa i dashboard
# dashboard_ui.render_dashboard()
```

### Scenario: Användare ställer fråga

```python
from budgetagent.modules import query_parser

# Användaren skriver: "Hur mycket spenderar vi på mat per månad?"
query = "Hur mycket spenderar vi på mat per månad?"

# Systemet tolkar och besvarar
answer = query_parser.answer_query(query)
# Output: "Utgifter för Mat: 4500 kr/månad (genomsnitt senaste 6 månaderna)"
```

### Scenario: Jämför budgetscenarier

```python
from budgetagent.modules import forecast_engine, workflow
from budgetagent.modules.models import Scenario
from decimal import Decimal

# Basscenario
base = Scenario(
    name="Nuläge",
    description="Aktuell budget utan ändringar"
)

# Alternativt scenario
with_bonus = Scenario(
    name="Med bonus",
    description="Om vi får 5000 kr extra i januari",
    income_adjustments={"Robin": Decimal(5000)}
)

# Jämför
results = workflow.compare_budget_scenarios(base, [with_bonus])
```

## Testning av Integration

Alla moduler har tester i `budgetagent/tests/`. För att köra:

```bash
pytest budgetagent/tests/
```

## Nästa Steg för Implementation

För att göra systemet fullt funktionellt:

1. **Implementera funktionskroppar** - Ersätt `pass` med faktisk logik
2. **Lägg till YAML-läsning/skrivning** - Implementera faktisk persistence
3. **Koppla Dash-callbacks** - Gör UI interaktivt
4. **Utöka query_parser** - Lägg till fler intent och bättre NLP
5. **Lägg till databas** - För långsiktig datalagring
6. **Implementera PDF-parsing** - Med pdfplumber eller pytesseract

## Arkitekturprinciper

1. **Loose Coupling**: Moduler kommunicerar via definierade gränssnitt
2. **Type Safety**: Pydantic-modeller säkerställer datavalidering
3. **Single Responsibility**: Varje modul har en tydlig uppgift
4. **Composability**: workflow.py kan kombinera moduler på olika sätt
5. **Testability**: Alla moduler kan testas isolerat
