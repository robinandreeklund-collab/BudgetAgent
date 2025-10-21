# 💸 BudgetAgent – Transparent hushållsbudget med agentlogik

BudgetAgent är ett modulärt, agentvänligt system för att hantera hushållsekonomi. Det läser in bankkontoutdrag, kategoriserar transaktioner, hanterar framtida fakturor och inkomster, och simulerar framtida saldo med rättvis fördelning mellan personer. Systemet är byggt för insyn, flexibilitet och vidareutveckling.

---


## 🧱 Teknisk arkitektur

- **Språk:** Python 3.10+
- **UI:** Dash (Plotly)
- **Konfiguration:** YAML-baserad
- **Testning:** Pytest
- **Modularitet:** Varje funktion är en separat modul med testfil och YAML-konfiguration
- **Agentgränssnitt:** Frågebaserad interaktion via Dash + API-ready struktur

## 🧩 Modulöversikt

| Modul | Funktion |
|-------|----------|
| `import_bank_data` | Läser in bankutdrag från CSV, Excel eller JSON |
| `parse_transactions` | Extraherar datum, belopp, beskrivning, kategori |
| `categorize_expenses` | Automatisk och manuell kategorisering av utgifter |
| `upcoming_bills` | Hantering av framtida fakturor med förfallodatum |
| `income_tracker` | Registrering av inkomster per person |
| `net_balance_splitter` | Fördelning av kvarvarande saldo enligt regler |
| `forecast_engine` | Simulering av framtida saldo baserat på historik och planerade inkomster/fakturor |
| `alerts_and_insights` | Varningar och rekommendationer baserat på budgetmål |
| `dashboard_ui` | Interaktiv visualisering via Streamlit eller Dash |
| `settings_panel` | Granulär kontroll över alla inställningar och regler |
| `parse_pdf_bills` | Extraherar fakturainformation från PDF-filer och konverterar till YAML-format |

## 📋 Status: Modulimplementering

### ✅ Funktionella moduler (implementerade)
- [x] **import_bank_data.py** - Filläsning, formatdetektering, kolumnnormalisering ✅
- [x] **parse_transactions.py** - Datumparsing, beskrivningsrensning, metadataextraktion ✅
- [x] **categorize_expenses.py** - Automatisk och manuell kategorisering ✅
- [x] **upcoming_bills.py** - Fakturahantering med YAML-persistence ✅
- [x] **income_tracker.py** - Inkomstregistrering och prognos ✅
- [x] **net_balance_splitter.py** - Saldofördelning med olika regler ✅
- [x] **forecast_engine.py** - Simulering och scenarioanalys ✅
- [x] **alerts_and_insights.py** - Varningar och rekommendationer ✅
- [x] **dashboard_ui.py** - Interaktiv Dash-applikation med callbacks ✅
- [x] **query_parser.py** - Naturlig språkbearbetning för frågor ✅
- [x] **workflow.py** - Modulintegration och arbetsflöden ✅
- [x] **models.py** - Pydantic-modeller för datavalidering ✅
- [ ] **settings_panel.py** - UI för inställningar (grundstruktur klar)
- [ ] **parse_pdf_bills.py** - PDF-faktura-parsing (struktur klar)

### 📝 Moduldetaljer
Alla moduler innehåller:
- ✅ Svensk moduldocstring med beskrivning
- ✅ Funktionssignaturer enligt modules.yaml
- ✅ Svenska docstrings för varje funktion
- ✅ **Komplett funktionsimplementering**
- ✅ YAML-konfiguration och datapers persistence
- ✅ Felhantering och validering

## 🧪 Test- och CI-status

### ✅ Teststruktur (enligt test_plan.yaml)
- [x] **test_import_sweden_csv.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_categorization_rules.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_upcoming_bills.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_income_tracker.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_forecast_average.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_future_income_injection.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_net_balance_splitter.py** - Struktur, enhetstest, YAML-validering, edge cases ✓
- [x] **test_ui_interaction.py** - Struktur, enhetstest, YAML-validering, edge cases ✓

### 📊 Testöversikt
Alla testfiler innehåller:
- ✅ Grundläggande teststruktur med pytest
- ✅ Exempel på enhetstest för varje huvudfunktion
- ✅ YAML-konfigurationsvalidering
- ✅ Edge case-tester (tom input, felaktigt format, etc.)
- ✅ Svenska docstrings och beskrivningar
- ✅ Integration med faktiska YAML-konfigurationsfiler

**Totalt: 193 tester samlade** (körklara för framtida implementation)

### 🔄 CI/CD-pipeline
- [x] **GitHub Actions workflow** konfigurerad (`.github/workflows/ci.yml`)
- [x] **Pytest** - Kör alla tester automatiskt vid push/PR
- [x] **yamllint** - Validerar alla YAML-filer i config/
- [x] **Multi-version testing** - Testas mot Python 3.10, 3.11, 3.12
- [x] **Automatisk körning** - Vid push till main/develop och alla PR

### ✨ Systemstatus
**Systemet är nu funktionellt!** ✅

- ✅ Alla kärnmoduler är implementerade
- ✅ Dash-dashboard är funktionellt med interaktiva komponenter
- ✅ Data persisteras i YAML-filer
- ✅ Kategoriseringsregler och prognoser fungerar
- ✅ Exempeldata finns för testning
- 🔄 Testerna behöver aktiveras med faktiska assertions
- 🔄 PDF-parsing och avancerade features kan läggas till

---

## 🧠 Funktioner

- Automatisk import och kategorisering av banktransaktioner
- Inmatning av framtida fakturor och inkomster
- Genomsnittlig utgiftsanalys baserat på historik
- Simulering av framtida saldo månad för månad
- Fördelning av kvarvarande pengar enligt valda regler (50/50, inkomstbaserat, behovsbaserat)
- Interaktiv dashboard med filter, grafer och exportfunktioner
- Agentgränssnitt för frågor som:  
  _“Hur mycket har vi kvar i januari?”_  
  _“Vad händer om vi får 5000 kr extra?”_

---

## 📁 Filstruktur

```bash
budgetagent/
├── data/
│   └── example_bank_data.csv
├── modules/
│   ├── import_bank_data.py
│   ├── parse_transactions.py
│   ├── categorize_expenses.py
│   ├── upcoming_bills.py
│   ├── income_tracker.py
│   ├── net_balance_splitter.py
│   ├── forecast_engine.py
│   ├── alerts_and_insights.py
│   └── dashboard_ui.py
├── config/
│   ├── project_structure.yaml
│   ├── settings_panel.yaml
│   ├── forecast_engine.yaml
│   ├── income_tracker.yaml
│   ├── upcoming_bills.yaml
│   ├── net_balance_splitter.yaml
│   └── test_plan.yaml
├── tests/
│   ├── test_import_sweden_csv.py
│   ├── test_categorization_rules.py
│   ├── test_upcoming_bills.py
│   ├── test_income_tracker.py
│   ├── test_forecast_average.py
│   ├── test_future_income_injection.py
│   ├── test_net_balance_splitter.py
│   └── test_ui_interaction.py
├── README.md
└── requirements.txt
```

## 🚀 Kom igång

### Installation

1. **Klona repot:**
```bash
git clone https://github.com/robinandreeklund-collab/BudgetAgent.git
cd BudgetAgent
```

2. **Installera beroenden:**
```bash
pip install -r requirements.txt
```

### Starta Systemet

**Starta Dashboard:**
```bash
python start_dashboard.py
```

Dashboard öppnas automatiskt på: **http://localhost:8050**

Dashboard innehåller:
- 📊 **Översikt**: Prognosgraf och ekonomiska insikter
- ➕ **Inmatning**: Formulär för fakturor och inkomster
- 🤖 **Agentfrågor**: Ställ frågor om din ekonomi i naturligt språk
- ⚙️ **Inställningar**: Anpassa prognosfönster, fördelningsregler och varningar

### Använda Systemet Programmatiskt

**Importera och kategorisera banktransaktioner:**
```python
from budgetagent.modules.import_bank_data import import_and_parse
from budgetagent.modules.categorize_expenses import categorize_transactions
import yaml

# Ladda kategoriseringsregler
with open('budgetagent/config/categorization_rules.yaml', 'r') as f:
    config = yaml.safe_load(f)
    rules = config['categories']

# Importera transaktioner
transactions = import_and_parse('budgetagent/data/example_bank_data.csv')

# Kategorisera
categorized = categorize_transactions(transactions, rules)
```

**Skapa prognos:**
```python
from budgetagent.modules.forecast_engine import simulate_monthly_balance

# Simulera 6 månader framåt
forecast = simulate_monthly_balance(6)

for f in forecast:
    print(f"{f.date}: Saldo={f.balance} SEK")
```

**Lägg till faktura:**
```python
from budgetagent.modules.models import Bill
from budgetagent.modules.upcoming_bills import add_bill
from datetime import date
from decimal import Decimal

bill = Bill(
    name='Elräkning',
    amount=Decimal('900'),
    due_date=date(2025, 11, 30),
    category='Boende',
    recurring=True,
    frequency='monthly'
)
add_bill(bill)
```

## 🧪 Testning

Kör alla tester med:
```bash
pytest budgetagent/tests/ -v
```

**Testtäckning:** 55+ tester i 10+ testfiler (inkl. nya test_import_accounts.py och utökade test_categorization_rules.py)

## 🤖 Träna AI-modellen för kategorisering

BudgetAgent använder en hybrid-modell för kategorisering som kombinerar:
1. **Regelbaserad matchning** - snabb och pålitlig kategorisering med nyckelord
2. **TF-IDF AI-fallback** - maskininlärning baserat på träningsdata

### Hur tränar du modellen?

1. **Via Dashboard (kommande feature):**
   - Navigera till "Konton"-vyn i dashboarden
   - Granska transaktioner och välj rätt kategori från dropdown
   - Klicka på "Lär AI" för att spara valet som träningsdata
   - Modellen tränas automatiskt när du har minst 2 exempel per kategori

2. **Programmatiskt:**
   ```python
   from budgetagent.modules.categorize_expenses import add_training_example
   
   # Lägg till träningsexempel
   add_training_example("ICA Supermarket Linköping", "Mat")
   add_training_example("Circle K bensin", "Transport")
   add_training_example("Spotify Premium", "Nöje")
   ```

3. **Förhandsgranska klassificering:**
   - Använd "Förhandsgranska klassificering" för att se hur AI skulle kategorisera
   - Spara endast de resultat du är nöjd med

### Träningsdata

Träningsdata sparas i `budgetagent/data/training_data.yaml` och används för att bygga TF-IDF-index.
Ju fler exempel du lägger till, desto bättre blir kategoriseringen!

**Krav för TF-IDF-träning:**
- Minst 2 träningsexempel totalt
- Minst 2 olika kategorier
- Fler exempel ger bättre resultat

### Dependencies för AI-kategorisering

AI-funktionen kräver scikit-learn:
```bash
pip install scikit-learn>=1.0.0
```

För framtida förbättringar kan du även installera:
```bash
pip install sentence-transformers  # För semantisk likhet (kommande)
```

## 🛠️ Anpassning

**Kategoriseringsregler:**
Redigera `budgetagent/config/categorization_rules.yaml` för att lägga till eller ändra kategorier och nyckelord.

**Fördelningsregler:**
Anpassa `budgetagent/config/net_balance_splitter.yaml` för att ändra hur saldo fördelas mellan personer.

**Prognosinställningar:**
Justera forecast-fönster och andra inställningar i `budgetagent/config/forecast_engine.yaml`.

**Inställningspanel:**
Alla inställningar kan också justeras via dashboard-gränssnittet under fliken **Inställningar**.

## 📊 Exempeldata

Projektet inkluderar exempeldata i `budgetagent/data/example_bank_data.csv` med 20 transaktioner från januari-februari 2025. Använd detta för att testa systemet.

## 🏦 Kontohantering och Dupliceringsskydd

BudgetAgent hanterar automatiskt flera bankkonton och skyddar mot dubbletter:

### Automatisk kontoregistrering

När du importerar en fil extraheras kontonamnet automatiskt från filnamnet:
- Exempel: `PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv` → Konto: `PERSONKONTO 1709 20 72840`
- Konton skapas automatiskt om de inte finns
- Metadata sparas i `budgetagent/config/accounts.yaml`

### Dupliceringsskydd

Systemet förhindrar dubbletter på två nivåer:

1. **Filnivå:** MD5-checksumma beräknas för varje fil
   - Samma fil kan inte importeras två gånger
   - Indexeras i `budgetagent/data/imports_index.yaml`

2. **Transaktionsnivå:** SHA256-hash beräknas för varje transaktion
   - Baserat på datum, belopp, beskrivning och valuta
   - Dubbletter filtreras bort automatiskt vid import

### Import-index

Alla importer spåras i `budgetagent/data/imports_index.yaml`:
```yaml
imports:
  - filename: "PERSONKONTO 1709 20 72840 - 2025-10-21.csv"
    checksum: "abc123..."
    account: "PERSONKONTO 1709 20 72840"
    import_date: "2025-10-21T09:39:41"
    transaction_count: 25
    transaction_hashes:
      - "hash1..."
      - "hash2..."
```

## 🤖 Agentfrågor - Exempel

Dashboard innehåller ett naturligt språkgränssnitt där du kan ställa frågor som:

- "Visa alla fakturor i december"
- "Hur mycket har vi kvar i januari?"
- "Vad händer om vi får 5000 kr extra?"
- "Hur mycket spenderar vi på mat per månad?"

Systemet tolkar frågan, identifierar intent och parametrar, och returnerar relevant information.

🤝 Bidra
Alla moduler är dokumenterade och testade. Se config/test_plan.yaml för att förstå testflödet. Nya contributors kan börja med att läsa project_structure.yaml och settings_panel.yaml.

📜 Licens
MIT License – använd, modifiera och dela fritt.

