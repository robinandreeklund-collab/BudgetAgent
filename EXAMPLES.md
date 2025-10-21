# BudgetAgent - Användningsexempel

Detta dokument visar exempel på hur man använder BudgetAgent-systemet.

## Grundläggande Användning

### 1. Importera Bankdata

```python
from budgetagent.modules import import_bank_data
from budgetagent.modules.models import Transaction

# Ladda bankfil
file_path = "data/swedbank_export.csv"
raw_data = import_bank_data.load_file(file_path)

# Detektera bankformat
bank_format = import_bank_data.detect_format(raw_data)
print(f"Detekterat format: {bank_format}")

# Normalisera kolumner
normalized_data = import_bank_data.normalize_columns(raw_data, bank_format)

# Komplett import och konvertering till Transaction-objekt
transactions = import_bank_data.import_and_parse(file_path)
```

### 2. Lägg till Fakturor

```python
from budgetagent.modules import upcoming_bills
from budgetagent.modules.models import Bill
from datetime import date
from decimal import Decimal

# Skapa en faktura
elrakning = Bill(
    name="Elräkning",
    amount=Decimal("900.00"),
    due_date=date(2025, 11, 30),
    category="Boende",
    recurring=True,
    frequency="monthly"
)

# Lägg till i systemet
upcoming_bills.add_bill(elrakning)

# Hämta fakturor för en månad
december_bills = upcoming_bills.get_upcoming_bills("2025-12")
for bill in december_bills:
    print(f"{bill.name}: {bill.amount} kr, förfaller {bill.due_date}")
```

### 3. Registrera Inkomster

```python
from budgetagent.modules import income_tracker
from budgetagent.modules.models import Income
from datetime import date
from decimal import Decimal

# Lägg till månadslön
lon = Income(
    person="Robin",
    source="Lön",
    amount=Decimal("28000.00"),
    date=date(2025, 11, 25),
    recurring=True,
    frequency="monthly"
)

income_tracker.add_income(lon)

# Lägg till en engångsinkomst
frilans = Income(
    person="Robin",
    source="Frilansuppdrag",
    amount=Decimal("5000.00"),
    date=date(2025, 12, 10),
    recurring=False
)

income_tracker.add_income(frilans)

# Hämta total inkomst för en månad
monthly_income = income_tracker.get_monthly_income("Robin", "2025-12")
print(f"Total inkomst december: {monthly_income} kr")
```

### 4. Generera Prognos

```python
from budgetagent.modules import forecast_engine
from budgetagent.modules.models import ForecastData

# Simulera saldo 6 månader framåt
forecast = forecast_engine.simulate_monthly_balance(months=6)

for month_data in forecast:
    print(f"{month_data.date}: Saldo {month_data.balance} kr")
    print(f"  Inkomst: {month_data.income} kr")
    print(f"  Utgifter: {month_data.expenses} kr")
    print(f"  Konfidens: {month_data.confidence * 100}%")
```

### 5. Jämför Scenarier

```python
from budgetagent.modules import forecast_engine
from budgetagent.modules.models import Scenario
from decimal import Decimal

# Basscenario
base = Scenario(
    name="Nuvarande budget",
    description="Ingen förändring"
)

# Scenario med extra inkomst
bonus_scenario = Scenario(
    name="Med julbonus",
    description="5000 kr extra i december",
    income_adjustments={"Robin": Decimal(5000)}
)

# Scenario med minskade utgifter
savings_scenario = Scenario(
    name="Spara på mat",
    description="Minska matkostnader med 1000 kr/månad",
    expense_adjustments={"Mat": Decimal(-1000)}
)

# Jämför alla scenarier
scenarios = [base, bonus_scenario, savings_scenario]
results = forecast_engine.compare_scenarios(scenarios)

for scenario_name, forecast_data in results.items():
    print(f"\n{scenario_name}:")
    for month in forecast_data:
        print(f"  {month.date}: {month.balance} kr")
```

### 6. Kontrollera Varningar

```python
from budgetagent.modules import alerts_and_insights
from budgetagent.modules.models import AlertConfig
from decimal import Decimal
import pandas as pd

# Konfigurera varningar
alert_config = AlertConfig(
    threshold_percentage=80,
    category_limits={
        "Mat": Decimal(5000),
        "Nöje": Decimal(2000),
        "Transport": Decimal(1500)
    },
    alert_days_before_due=7,
    min_balance_warning=Decimal(1000)
)

# Skapa exempel-data
transaction_data = pd.DataFrame({
    'category': ['Mat', 'Mat', 'Nöje', 'Transport'],
    'amount': [-3500, -2000, -2500, -1200],
    'date': ['2025-11-01', '2025-11-15', '2025-11-10', '2025-11-05']
})

# Kontrollera trösklar
alerts = alerts_and_insights.check_budget_thresholds(transaction_data, alert_config)
for alert in alerts:
    print(f"⚠️ {alert}")

# Generera insikter
insights = alerts_and_insights.generate_insights(transaction_data)
for insight in insights:
    print(f"💡 {insight}")
```

## Agentfrågor

### 7. Ställ Frågor till BudgetAgent

```python
from budgetagent.modules import query_parser

# Exempel på olika typer av frågor

# Fakturafrågor
answer = query_parser.answer_query("Visa alla fakturor i december")
print(answer)

answer = query_parser.answer_query("Vilka räkningar ska betalas nästa månad?")
print(answer)

# Saldofrågor
answer = query_parser.answer_query("Hur mycket har vi kvar i januari?")
print(answer)

answer = query_parser.answer_query("Vad är vårt saldo i slutet av året?")
print(answer)

# Scenariofrågor
answer = query_parser.answer_query("Vad händer om vi får 5000 kr extra i december?")
print(answer)

answer = query_parser.answer_query("Kan vi köpa en ny TV för 8000 kr?")
print(answer)

# Utgiftsfrågor
answer = query_parser.answer_query("Hur mycket spenderar vi på mat per månad?")
print(answer)

answer = query_parser.answer_query("Vad kostar transport i genomsnitt?")
print(answer)
```

### 8. Tolka och Analysera Frågor

```python
from budgetagent.modules import query_parser

# Parsa en fråga för att se hur systemet tolkar den
query = "Visa alla fakturor i december"
parsed = query_parser.parse_query(query)

print(f"Intent: {parsed['intent']}")
print(f"Parametrar: {parsed['params']}")
print(f"Original fråga: {parsed['original_query']}")

# Output:
# Intent: show_bills
# Parametrar: {'month': '2025-12'}
# Original fråga: Visa alla fakturor i december
```

## Dashboard och UI

### 9. Starta Dashboard

```python
from budgetagent.modules import dashboard_ui

# Starta Dash-applikationen
dashboard_ui.render_dashboard()

# Öppna webbläsare på http://localhost:8050
```

### 10. Visa Prognosgraf

```python
from budgetagent.modules import dashboard_ui, forecast_engine

# Generera prognosdata
forecast_data = forecast_engine.simulate_monthly_balance(months=6)

# Skapa graf
figure = dashboard_ui.update_forecast_graph(forecast_data)

# Visa i Dash eller spara som bild
# figure.show()  # Om du kör lokalt
# figure.write_html("forecast.html")  # Spara som HTML
```

## Komplett Arbetsflöde

### 11. Månatlig Uppdatering

```python
from budgetagent.modules import workflow

# Kör komplett månadsuppdatering
summary = workflow.full_monthly_update()

print(f"Nya transaktioner: {summary['new_transactions']}")
print(f"Nya fakturor: {summary['new_bills']}")
print(f"Varningar: {len(summary['alerts'])}")
print(f"Insikter: {len(summary['insights'])}")
print(f"Prognos uppdaterad: {summary['forecast_updated']}")

# Visa varningar
for alert in summary['alerts']:
    print(f"⚠️ {alert}")

# Visa insikter
for insight in summary['insights']:
    print(f"💡 {insight}")
```

### 12. Importera och Kategorisera

```python
from budgetagent.modules import workflow

# Komplett import och kategorisering
transactions = workflow.import_and_categorize_transactions(
    file_path="data/bank_november_2025.csv",
    rules_path="config/categorization_rules.yaml"
)

# Visa resultat
print(f"Importerade {len(transactions)} transaktioner")

# Gruppera per kategori
from collections import defaultdict
by_category = defaultdict(list)

for t in transactions:
    by_category[t.category or "Okategoriserad"].append(t)

for category, trans in by_category.items():
    total = sum(t.amount for t in trans)
    print(f"{category}: {total} kr ({len(trans)} transaktioner)")
```

### 13. Process PDF-fakturor

```python
from budgetagent.modules import workflow

# Extrahera fakturor från PDF
pdf_path = "data/elrakning_november_2025.pdf"
bills = workflow.process_pdf_bills(pdf_path)

print(f"Extraherade {len(bills)} fakturor från PDF")

for bill in bills:
    print(f"{bill.name}: {bill.amount} kr, förfaller {bill.due_date}")
```

### 14. Generera Komplett Prognos med Analys

```python
from budgetagent.modules import workflow

# Generera prognos
forecast = workflow.generate_complete_forecast(months=6)

# Ladda varningskonfiguration
alert_config = workflow.load_alert_config()

# Hämta historiska transaktioner för analys
historical_data = workflow.get_historical_transactions()

# Analysera
from budgetagent.modules import alerts_and_insights
alerts = alerts_and_insights.check_budget_thresholds(
    historical_data, 
    alert_config
)

# Visa resultat
print("=== EKONOMISK PROGNOS ===\n")

for month_data in forecast:
    print(f"{month_data.date.strftime('%Y-%m')}")
    print(f"  Prognostiserat saldo: {month_data.balance} kr")
    print(f"  Inkomster: +{month_data.income} kr")
    print(f"  Utgifter: -{month_data.expenses} kr")
    print(f"  Konfidens: {month_data.confidence * 100:.0f}%")
    
    if month_data.category_breakdown:
        print("  Utgifter per kategori:")
        for category, amount in month_data.category_breakdown.items():
            print(f"    {category}: {amount} kr")
    print()

print("\n=== VARNINGAR ===\n")
for alert in alerts:
    print(f"⚠️ {alert}")
```

## Pydantic-modeller i Praktiken

### 15. Validering av Indata

```python
from budgetagent.modules.models import Transaction, Bill
from decimal import Decimal
from datetime import date

# Pydantic validerar automatiskt
try:
    # Detta fungerar
    valid_transaction = Transaction(
        date=date(2025, 11, 15),
        amount=Decimal("-350.50"),
        description="ICA Maxi",
        category="Mat"
    )
    print("✓ Transaktion skapad")
    
    # Detta failar - belopp får inte vara 0
    invalid_transaction = Transaction(
        date=date(2025, 11, 15),
        amount=Decimal("0"),
        description="Test"
    )
except ValueError as e:
    print(f"✗ Fel: {e}")

# Validering av fakturor
try:
    # Detta fungerar
    valid_bill = Bill(
        name="Elräkning",
        amount=Decimal("900"),
        due_date=date(2025, 12, 31),
        category="Boende"
    )
    print("✓ Faktura skapad")
    
    # Detta failar - belopp måste vara positivt
    invalid_bill = Bill(
        name="Test",
        amount=Decimal("-100"),
        due_date=date(2025, 12, 31),
        category="Test"
    )
except ValueError as e:
    print(f"✗ Fel: {e}")
```

### 16. Serialisering och Deserialisering

```python
from budgetagent.modules.models import Bill
from decimal import Decimal
from datetime import date
import json

# Skapa objekt
bill = Bill(
    name="Internet",
    amount=Decimal("399"),
    due_date=date(2025, 12, 15),
    category="Boende",
    recurring=True,
    frequency="monthly"
)

# Serialisera till dict
bill_dict = bill.model_dump()
print(bill_dict)

# Serialisera till JSON
bill_json = bill.model_dump_json()
print(bill_json)

# Deserialisera från dict
restored_bill = Bill(**bill_dict)
print(f"Återställd: {restored_bill.name}")

# Deserialisera från JSON
restored_from_json = Bill.model_validate_json(bill_json)
print(f"Från JSON: {restored_from_json.name}")
```

## Tips och Best Practices

1. **Använd alltid Pydantic-modeller** för datavalidering
2. **Definiera tydliga kategorier** i categorization_rules.yaml
3. **Uppdatera prognoser regelbundet** med nya transaktioner
4. **Använd scenarier** för att planera stora köp eller inkomster
5. **Sätt upp varningar** för kategorier du vill hålla koll på
6. **Testa agentfrågor** för att hitta rätt formuleringar
7. **Exportera data** regelbundet för backup
8. **Validera YAML-filer** med yamllint
9. **Kör tester** efter ändringar: `pytest budgetagent/tests/`
10. **Dokumentera anpassningar** i egen README

## Felsökning

### Problem: Import misslyckas
```python
# Kontrollera filformat
import pandas as pd
df = pd.read_csv("data/export.csv", encoding='utf-8')
print(df.head())
print(df.columns)
```

### Problem: Kategorisering fungerar inte
```python
# Testa kategoriseringsregler
from budgetagent.modules import categorize_expenses
import yaml

with open("config/categorization_rules.yaml") as f:
    rules = yaml.safe_load(f)
    
print("Tillgängliga kategorier:", list(rules['categories'].keys()))
```

### Problem: Dashboard startar inte
```python
# Verifiera att alla dependencies är installerade
import dash
import plotly
import pandas
import pydantic
print("Alla dependencies installerade ✓")
```

## Nästa Steg

1. Läs [INTEGRATION.md](budgetagent/INTEGRATION.md) för detaljerad modulintegration
2. Utforska [modules.yaml](modules.yaml) för modulspecifikationer
3. Studera [test_plan.yaml](budgetagent/config/test_plan.yaml) för testning
4. Anpassa [settings_panel.yaml](budgetagent/config/settings_panel.yaml) för dina behov
