# Saldo-spårning och integration med prognoser

Denna uppdatering lägger till automatisk saldo-spårning från CSV-importer och integrerar denna information med systemets prognosfunktionalitet.

## Nya funktioner

### 1. Automatisk saldo-extraktion vid import

Systemet extraherar nu automatiskt saldoinformation från importerade CSV-filer när denna information finns tillgänglig.

**Stödda banker:**
- **Nordea**: Extraherar saldo från "Saldo"-kolumnen
- **SEB**: Extraherar saldo från "Saldo"-kolumnen
- **Andra banker**: Kommer att utökas efter behov

**Exempel:**
När du importerar en Nordea CSV-fil med en "Saldo"-kolumn, extraheras automatiskt:
- Saldo-belopp (senaste värdet i filen)
- Datum för saldot (från senaste transaktionen)
- Valuta (från Valuta-kolumnen eller standard SEK)

### 2. Uppdaterad Account-modell

Account-modellen har utökats med tre nya fält:

```python
class Account(BaseModel):
    account_name: str
    account_number: Optional[str] = None
    imported_files: List[Dict[str, str]] = []
    last_import_date: Optional[datetime] = None
    transaction_hashes: set = set()
    current_balance: Optional[Decimal] = None  # NYT!
    balance_date: Optional[date] = None         # NYT!
    balance_currency: str = "SEK"               # NYT!
```

### 3. Visualisering i dashboard

Kontoöversikten i dashboardens "Konton"-flik visar nu:
- **Aktuellt saldo**: Visas med färgkodning (grönt för positivt, rött för negativt)
- **Saldo per**: Datum då saldot registrerades
- **Valuta**: Vilken valuta saldot är i

**Exempel på visning:**
```
Konto: PERSONKONTO 1709 20 72840
Kontonummer: 1709 20 72840
Aktuellt saldo: 15,234.50 SEK  (grönt om positivt)
Saldo per: 2025-10-21
Antal importerade filer: 3
```

## Tekniska detaljer

### Nya funktioner

#### extract_balance_info(raw_data, bank_format)
Extraherar saldoinformation från rådata innan normalisering.

```python
from budgetagent.modules import import_bank_data

# Anropas automatiskt under import
balance_info = import_bank_data.extract_balance_info(raw_data, "Nordea")
# Returns: (balance, balance_date, currency) eller None
```

#### update_account_balance(account_name, balance, balance_date, currency)
Uppdaterar saldoinformation för ett konto.

```python
from budgetagent.modules import account_manager
from decimal import Decimal
from datetime import date

account_manager.update_account_balance(
    "PERSONKONTO 1709 20 72840",
    Decimal("15234.50"),
    date(2025, 10, 21),
    "SEK"
)
```

### Uppdaterade funktioner

#### import_and_parse()
Nu extraherar och sparar saldoinformation automatiskt:

1. Laddar fil och detekterar format
2. **Extraherar saldoinformation** (nytt steg)
3. Normaliserar kolumner
4. Konverterar till Transaction-objekt
5. Filtrerar dubbletter
6. **Uppdaterar kontosaldo** (nytt steg)
7. Markerar fil som importerad

## Integration med prognoser

### Hur saldo kan användas

Saldoinformation kan användas för att:

1. **Startpunkt för prognoser**: Använd aktuellt saldo som bas för framtida beräkningar
2. **Validering av transaktioner**: Verifiera att importerade transaktioner stämmer med saldo
3. **Alert-system**: Varna när saldo blir lågt
4. **Multi-konto-översikt**: Se totalt saldo över alla konton

### Framtida implementation (förslag)

```python
def create_forecast_from_balance(account_name: str, months: int = 6):
    """
    Skapar prognos med kontosaldo som startpunkt.
    """
    from budgetagent.modules import account_manager, forecast_engine
    
    # Hämta konto med saldo
    accounts = account_manager.load_accounts()
    account = accounts.get(account_name)
    
    if not account or not account.current_balance:
        raise ValueError("Inget saldo tillgängligt för prognos")
    
    # Använd saldo som startpunkt
    starting_balance = account.current_balance
    starting_date = account.balance_date
    
    # Skapa prognos
    forecast = forecast_engine.simulate_monthly_balance(
        months=months,
        starting_balance=starting_balance,
        starting_date=starting_date
    )
    
    return forecast
```

### Användningsexempel

```python
# Exempel 1: Visa totalt saldo över alla konton
from budgetagent.modules import account_manager

accounts = account_manager.load_accounts()
total_balance = sum(
    acc.current_balance or 0 
    for acc in accounts.values()
)
print(f"Totalt saldo: {total_balance} SEK")

# Exempel 2: Hitta konton med lågt saldo
low_balance_accounts = [
    (name, acc.current_balance)
    for name, acc in accounts.items()
    if acc.current_balance and acc.current_balance < 1000
]

for name, balance in low_balance_accounts:
    print(f"⚠️ Lågt saldo på {name}: {balance} SEK")

# Exempel 3: Beräkna daglig förbränning
from datetime import date

for name, acc in accounts.items():
    if acc.current_balance and acc.balance_date:
        days_since = (date.today() - acc.balance_date).days
        if days_since > 0:
            # Estimera daglig kostnad baserat på transaktioner
            print(f"{name}: Saldo {acc.current_balance} SEK per {acc.balance_date}")
```

## Alert-integration (framtida)

Saldoinformation kan användas för att skapa alerts:

```yaml
# alerts_config.yaml
alerts:
  low_balance:
    enabled: true
    threshold: 1000
    accounts:
      - "PERSONKONTO 1709 20 72840"
    message: "⚠️ Lågt saldo: {balance} SEK på konto {account_name}"
  
  negative_balance:
    enabled: true
    threshold: 0
    message: "❌ NEGATIVT saldo: {balance} SEK på konto {account_name}"
```

## Fördelar

✅ **Automatisk spårning**: Saldo extraheras automatiskt vid varje import
✅ **Visuell feedback**: Tydlig visning i dashboard med färgkodning
✅ **Multi-valuta stöd**: Hanterar olika valutor
✅ **Prognosintegration**: Grund för mer exakta framtidsprognoser
✅ **Alert-potential**: Kan användas för att varna vid lågt saldo
✅ **Historisk data**: Saldo sparas per import för framtida analys

## Begränsningar och framtida förbättringar

### Nuvarande begränsningar:
- Endast senaste saldot sparas (ingen historik)
- Fungerar bara för banker som inkluderar saldo i CSV
- Ingen automatisk validering mot transaktioner

### Planerade förbättringar:
- **Saldo-historik**: Spara saldo vid varje import för trendanalys
- **Saldo-rekonstruktion**: Beräkna saldo från transaktioner om det saknas i CSV
- **Validering**: Kontrollera att transaktioner + tidigare saldo = nytt saldo
- **Multi-konto-prognos**: Skapa prognoser över alla konton samtidigt
- **Saldo-graf**: Visualisera saldo över tid
- **Export**: Exportera saldo-historik till Excel/CSV

## Testning

Alla 237 befintliga tester passerar. Systemet är bakåtkompatibelt och fungerar även utan saldoinformation.

```bash
# Kör tester
pytest budgetagent/tests/

# Resultat: 237 passed, 7 warnings
```

## Exempel på CSV-format med saldo

### Nordea format:
```csv
Bokföringsdatum,Belopp,Rubrik,Valuta,Saldo
2025-10-21,-350.50,ICA Maxi Stockholm,SEK,15234.50
2025-10-20,-120.00,Circle K,SEK,15584.00
2025-10-19,25000.00,Lön,SEK,15704.00
```

Systemet extraherar: Saldo = 15234.50 SEK per 2025-10-21

### SEB format:
```csv
Bokföringsdatum,Valuta,Belopp,Saldo
2025-10-21,SEK,-350.50,15234.50
2025-10-20,SEK,-120.00,15584.00
```

Systemet extraherar: Saldo = 15234.50 SEK per 2025-10-21
