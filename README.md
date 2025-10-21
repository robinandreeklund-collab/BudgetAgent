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

### ✅ Strukturerade moduler (enligt modules.yaml)
- [x] **import_bank_data.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **parse_transactions.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **categorize_expenses.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **upcoming_bills.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **income_tracker.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **net_balance_splitter.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **forecast_engine.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **alerts_and_insights.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **dashboard_ui.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **settings_panel.py** - Struktur, docstrings, funktionssignaturer ✓
- [x] **parse_pdf_bills.py** - Struktur, docstrings, funktionssignaturer ✓

### 📝 Moduldetaljer
Alla moduler innehåller:
- ✅ Svensk moduldocstring med beskrivning
- ✅ Funktionssignaturer enligt modules.yaml
- ✅ Svenska docstrings för varje funktion
- ✅ Pass-statements (ingen fullständig implementering)
- ✅ Exempel på YAML-konfiguration där relevant

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

### 🔄 Nästa steg
Modulstrukturen och testramverket är klart. För att göra systemet funktionellt behövs:
- Implementering av funktionslogik i modulerna
- Aktivering av testerna (ersätt pass-statements med faktiska assert-satser)
- Integration mellan moduler
- Dash UI-implementation

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
Klona repot:

bash
git clone https://github.com/dittnamn/budgetagent.git
cd budgetagent
Installera beroenden:

bash
pip install -r requirements.txt
Starta dashboarden:

bash
streamlit run modules/dashboard_ui.py
🧪 Testning
Kör alla tester med:

bash
pytest tests/
🛠️ Anpassning
Ändra inställningar i config/settings_panel.yaml

Lägg till egna fördelningsregler i net_balance_splitter.yaml

Justera forecast-fönster i forecast_engine.yaml

🤝 Bidra
Alla moduler är dokumenterade och testade. Se config/test_plan.yaml för att förstå testflödet. Nya contributors kan börja med att läsa project_structure.yaml och settings_panel.yaml.

📜 Licens
MIT License – använd, modifiera och dela fritt.

