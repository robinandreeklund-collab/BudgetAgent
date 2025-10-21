# Implementering: settings_panel.py och parse_pdf_bills.py

## Översikt

Denna implementering tillhandahåller två nya moduler för BudgetAgent-systemet:

1. **settings_panel.py** - Fullständig UI-hantering för systeminställningar
2. **parse_pdf_bills.py** - Automatisk parsing av PDF-fakturor

## settings_panel.py

### Funktionalitet

Modulen hanterar läsning, visning och uppdatering av alla systeminställningar som lagras i YAML-filer. Den genererar Dash-komponenter dynamiskt baserat på konfiguration.

### Funktioner

#### `load_settings(yaml_path: str) -> Dict`
Läser in alla inställningar från YAML-fil.

**Exempel:**
```python
from budgetagent.modules import settings_panel as sp

settings = sp.load_settings('budgetagent/config/settings_panel.yaml')
```

#### `render_controls(settings: Dict) -> List`
Skapar Dash-komponenter dynamiskt baserat på inställningsdefinitioner.

**Stödda kontrolltyper:**
- `dropdown` - Dropdown-meny med flera alternativ
- `slider` - Slider för numeriska värden
- `toggle` - Checkbox för på/av-inställningar

**Exempel:**
```python
components = sp.render_controls(settings)
# Returnerar lista med Dash-komponenter
```

#### `update_settings(yaml_path: str, new_values: Dict) -> None`
Sparar ändringar till YAML-fil.

**Exempel:**
```python
new_values = {
    'forecast_window': 9,
    'alert_threshold': 85
}
sp.update_settings('budgetagent/config/settings_panel.yaml', new_values)
```

#### `get_current_values(yaml_path: str) -> Dict`
Hämtar aktuella inställningsvärden från YAML.

**Exempel:**
```python
current = sp.get_current_values('budgetagent/config/settings_panel.yaml')
# {'forecast_window': 6, 'alert_threshold': 80, ...}
```

### YAML-konfiguration

Inställningar definieras i `budgetagent/config/settings_panel.yaml`:

```yaml
settings_panel:
  import_format:
    type: dropdown
    options: ["Swedbank CSV", "SEB Excel", "Revolut JSON"]
    default: "Swedbank CSV"
  
  forecast_window:
    type: slider
    min: 1
    max: 12
    default: 6
    unit: "months"
  
  alert_threshold:
    type: slider
    min: 0
    max: 100
    default: 80
    unit: "%"
  
  show_debug_panel:
    type: toggle
    default: true
```

### Integration med Dashboard

Modulen är integrerad med `dashboard_ui.py` och genererar automatiskt inställningspanelen baserat på YAML-konfiguration.

```python
def settings_panel() -> html.Div:
    """Skapar inställningspanel baserad på settings_panel.yaml."""
    from . import settings_panel as sp
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "settings_panel.yaml"
    settings = sp.load_settings(str(config_path))
    components = sp.render_controls(settings)
    
    return html.Div(components, style={'padding': '20px'})
```

## parse_pdf_bills.py

### Funktionalitet

Modulen hanterar automatisk extraktion av fakturadata från PDF-filer. Den stödjer både textbaserade PDF:er och bildbaserade fakturor via OCR.

### Funktioner

#### `extract_text_from_pdf(file_path: str) -> str`
Läser text från PDF-sidor med pdfplumber.

**Exempel:**
```python
from budgetagent.modules import parse_pdf_bills as ppb

text = ppb.extract_text_from_pdf('faktura.pdf')
```

#### `extract_bills_from_text(raw_text: str, default_category: str = "Boende") -> List[Bill]`
Identifierar fakturor i texten via regex och heuristik.

**Stödda mönster:**
- Belopp: `900 kr`, `1234.56 SEK`, `Belopp: 500 kronor`
- Datum: `2025-11-30`, `30-11-2025`, `30/11/2025`
- Fakturans namn: `Faktura: Elräkning`, `Leverantör: Vattenfall AB`

**Automatisk kategorisering:**
- Försäkring: innehåller "försäkring", "insurance"
- Boende: innehåller "el", "vatten", "hyra", "internet"

**Exempel:**
```python
text = """
Elräkning från Vattenfall
Belopp: 900 kr
Förfallodatum: 2025-11-30
"""

bills = ppb.extract_bills_from_text(text, "Boende")
# [Bill(name='Elräkning', amount=900, due_date='2025-11-30', category='Boende')]
```

#### `validate_bill_structure(bill: Bill) -> bool`
Validerar att faktura har korrekt format.

**Valideringsregler:**
- Namn får inte vara tomt
- Belopp måste vara positivt
- Kategori måste finnas
- Återkommande fakturor måste ha frekvens
- Betalda fakturor måste ha betalningsdatum

**Exempel:**
```python
from budgetagent.modules.models import Bill
from decimal import Decimal
from datetime import date

bill = Bill(
    name="Elräkning",
    amount=Decimal('900'),
    due_date=date(2025, 11, 30),
    category="Boende"
)

is_valid = ppb.validate_bill_structure(bill)  # True
```

#### `write_bills_to_yaml(bills: List[Bill], yaml_path: str) -> None`
Lägger till extraherade fakturor i `upcoming_bills.yaml`.

**Funktioner:**
- Läser befintliga fakturor
- Lägger till nya fakturor
- Undviker dubbletter (jämför namn, belopp, datum)
- Validerar alla fakturor innan sparning

**Exempel:**
```python
bills = [...]  # Lista med Bill-objekt
ppb.write_bills_to_yaml(bills, 'budgetagent/config/upcoming_bills.yaml')
```

#### `extract_text_with_ocr(file_path: str) -> str`
Använder OCR för bildbaserade PDF:er (valfri funktion).

**Krav:**
- `pytesseract`
- `pdf2image`
- Tesseract OCR installerat på systemet

**Exempel:**
```python
# Installera beroenden först:
# pip install pytesseract pdf2image
# sudo apt-get install tesseract-ocr tesseract-ocr-swe

text = ppb.extract_text_with_ocr('bildbaserad_faktura.pdf')
```

#### `parse_pdf_to_bills(file_path: str, default_category: str = "Boende", ocr_enabled: bool = False) -> List[Bill]`
Huvudfunktion för att parsa PDF och extrahera fakturor.

**Exempel:**
```python
# Enkel textbaserad PDF
bills = ppb.parse_pdf_to_bills('faktura.pdf', "Boende")

# Med OCR för bildbaserade PDF:er
bills = ppb.parse_pdf_to_bills('faktura.pdf', "Boende", ocr_enabled=True)

# Spara till YAML
ppb.write_bills_to_yaml(bills, 'budgetagent/config/upcoming_bills.yaml')
```

### YAML-konfiguration

Inställningar för PDF-parsing finns i `budgetagent/config/parse_pdf_bills.yaml`:

```yaml
parse_pdf_bills:
  ocr_enabled:
    type: toggle
    default: false
  
  default_category:
    type: dropdown
    options: ["Boende", "Mat", "Transport", "Nöje", "Övrigt"]
    default: "Boende"
  
  date_format:
    type: dropdown
    options: ["YYYY-MM-DD", "DD-MM-YYYY", "YYYY/MM/DD"]
    default: "YYYY-MM-DD"
```

### Fullständigt exempel

```python
from budgetagent.modules import parse_pdf_bills as ppb
from pathlib import Path

# Konfigurera sökvägar
pdf_file = Path('fakturor/elrakning_november.pdf')
output_yaml = Path('budgetagent/config/upcoming_bills.yaml')

# Parse PDF
bills = ppb.parse_pdf_to_bills(
    str(pdf_file),
    default_category="Boende",
    ocr_enabled=False
)

# Validera och visa resultat
for bill in bills:
    if ppb.validate_bill_structure(bill):
        print(f"✅ {bill.name}: {bill.amount} SEK (förfaller {bill.due_date})")
    else:
        print(f"❌ Ogiltig faktura: {bill.name}")

# Spara till YAML
if bills:
    ppb.write_bills_to_yaml(bills, str(output_yaml))
    print(f"Sparade {len(bills)} fakturor till {output_yaml}")
```

## Tester

Båda modulerna har omfattande testsuitear:

### Köra alla tester
```bash
pytest budgetagent/tests/test_settings_panel.py -v
pytest budgetagent/tests/test_parse_pdf_bills.py -v
```

### Teststatistik
- `test_settings_panel.py`: 15 tester
- `test_parse_pdf_bills.py`: 20 tester
- Total testtäckning: 272 tester passerar

## Beroenden

### Kärn-beroenden (installerade)
- `pyyaml>=6.0` - YAML-hantering
- `pydantic>=2.0.0` - Datavalidering
- `dash>=2.0.0` - UI-komponenter
- `pdfplumber>=0.10.0` - PDF-textextraktion

### Valfria beroenden (för OCR)
```bash
pip install pytesseract pdf2image
sudo apt-get install tesseract-ocr tesseract-ocr-swe
```

## Användning i praktiken

### Scenario 1: Uppdatera systeminställningar

```python
from budgetagent.modules import settings_panel as sp

# Ladda nuvarande inställningar
config_path = 'budgetagent/config/settings_panel.yaml'
current = sp.get_current_values(config_path)
print(f"Aktuellt prognosfönster: {current['forecast_window']} månader")

# Uppdatera inställningar
new_values = {
    'forecast_window': 12,
    'alert_threshold': 90
}
sp.update_settings(config_path, new_values)
print("✅ Inställningar uppdaterade!")
```

### Scenario 2: Importera fakturor från PDF

```python
from budgetagent.modules import parse_pdf_bills as ppb
from pathlib import Path

# Hitta alla PDF:er i fakturamapp
pdf_folder = Path('fakturor/')
output_yaml = Path('budgetagent/config/upcoming_bills.yaml')

all_bills = []
for pdf_file in pdf_folder.glob('*.pdf'):
    print(f"Läser {pdf_file.name}...")
    bills = ppb.parse_pdf_to_bills(str(pdf_file), "Boende")
    all_bills.extend(bills)
    print(f"  Hittade {len(bills)} fakturor")

# Spara alla fakturor
if all_bills:
    ppb.write_bills_to_yaml(all_bills, str(output_yaml))
    print(f"\n✅ Totalt {len(all_bills)} fakturor importerade!")
```

## Felsökning

### Problem: "YAML-fil hittades inte"
**Lösning:** Kontrollera att sökvägen är korrekt och att filen existerar.

### Problem: "Inga fakturor hittades i PDF"
**Lösning:** 
- Kontrollera att PDF:en innehåller text (inte bara bild)
- Prova med `ocr_enabled=True` för bildbaserade PDF:er
- Verifiera att PDF:en innehåller belopp och datum i stödt format

### Problem: "OCR fungerar inte"
**Lösning:**
```bash
# Installera Tesseract
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-swe

# Installera Python-paket
pip install pytesseract pdf2image

# Verifiera installation
tesseract --version
```

## Framtida förbättringar

- [ ] Stöd för fler datumformat
- [ ] Bättre kategorisering med ML-modell
- [ ] Stöd för flera fakturor i samma PDF
- [ ] Export till andra format (CSV, JSON)
- [ ] Bulk-import från mapp med PDF:er via UI

## Dokumentation

- **API-dokumentation:** Se docstrings i respektive modul
- **YAML-specifikation:** Se konfigurationsfiler i `budgetagent/config/`
- **Testfall:** Se `budgetagent/tests/test_settings_panel.py` och `test_parse_pdf_bills.py`
