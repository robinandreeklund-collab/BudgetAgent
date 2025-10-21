# Kontohantering - Ta bort filer och konton

Denna uppdatering lägger till möjlighet att ta bort importerade filer och hela konton från systemet.

## Nya funktioner

### 1. Ta bort importerade filer

Du kan nu ta bort enskilda importerade filer från ett konto utan att ta bort hela kontot.

**I dashboarden:**
- Gå till fliken "Konton"
- Expandera "Visa importhistorik" för ett konto
- Klicka på 🗑️-knappen bredvid filen du vill ta bort

**Programmatiskt:**
```python
from budgetagent.modules import account_manager

# Ta bort en fil från ett konto
success = account_manager.delete_imported_file(
    account_name="PERSONKONTO 1709 20 72840",
    filename="PERSONKONTO 1709 20 72840 - 2025-10-21.csv"
)

if success:
    print("Filen togs bort från kontots historik")
```

**Notera:** Detta tar endast bort filreferensen från kontots historik. De transaktioner som importerades från filen finns kvar i systemet.

### 2. Ta bort hela konton

Du kan ta bort hela konton inklusive all importhistorik och transaktions-hasher.

**I dashboarden:**
- Gå till fliken "Konton"
- Klicka på "Ta bort konto"-knappen i övre högra hörnet av kontorkortet

**Programmatiskt:**
```python
from budgetagent.modules import account_manager

# Ta bort ett helt konto
success = account_manager.delete_account("PERSONKONTO 1709 20 72840")

if success:
    print("Kontot togs bort helt")
```

**VARNING:** Detta tar bort all historik om importerade filer och transaktions-hasher för kontot. Transaktioner som redan sparats i systemet påverkas inte, men du kan importera samma filer igen eftersom dupliceringsskyddet är borttaget.

### 3. Rensa alla konton

För test- och demo-syften kan du rensa alla konton samtidigt.

**I dashboarden:**
- Gå till fliken "Konton"
- Klicka på den röda knappen "Rensa alla konton"

**Programmatiskt:**
```python
from budgetagent.modules import account_manager

# Rensa alla konton
account_manager.clear_all_accounts()
```

**VARNING:** Detta tar bort ALL kontohistorik. Använd endast för test/demo-syften eller när du vill börja om från scratch.

## Tekniska förbättringar

### Callback-fel åtgärdat

Tidigare fick användare ett felmeddelande om att `confirm-import-button` inte hittades i layouten. Detta har åtgärdats genom att sätta `suppress_callback_exceptions=True` i Dash-applikationen.

### Nya funktioner i account_manager.py

1. **`delete_imported_file(account_name, filename)`** - Ta bort en fil från importhistorik
2. **`delete_account(account_name)`** - Ta bort ett helt konto
3. **`clear_all_accounts()`** - Rensa alla konton

### Nya tester

6 nya tester har lagts till i `test_account_manager.py`:
- Test för att ta bort filer (lyckad, fil ej funnen, konto ej funnet)
- Test för att ta bort konton (lyckat, konto ej funnet)
- Test för att rensa alla konton

## Användningsexempel

### Scenario 1: Ta bort en felaktig import

Om du råkat importera fel fil:
```python
from budgetagent.modules import account_manager

# Lista alla konton
accounts = account_manager.load_accounts()
for name, account in accounts.items():
    print(f"Konto: {name}")
    for file in account.imported_files:
        print(f"  - {file['filename']}")

# Ta bort den felaktiga filen
account_manager.delete_imported_file(
    "PERSONKONTO 1709 20 72840",
    "PERSONKONTO 1709 20 72840 - 2025-10-21-FEL.csv"
)

# Nu kan du importera rätt fil
```

### Scenario 2: Starta om från scratch

För test- eller demo-syften:
```python
from budgetagent.modules import account_manager

# Rensa alla konton
account_manager.clear_all_accounts()

# Nu kan du importera filer igen utan dupliceringsskydd
```

### Scenario 3: Ta bort gammalt konto

Om du inte längre använder ett konto:
```python
from budgetagent.modules import account_manager

# Ta bort gamla konton
account_manager.delete_account("GAMMALT_KONTO_2023")
```

## Säkerhet och datahantering

- **Filborttagning**: Tar endast bort filreferensen, inte de transaktioner som importerades
- **Kontoborttagning**: Tar bort all import-historik och dupliceringsskydd för kontot
- **Transaktioner**: Sparade transaktioner i systemet påverkas INTE av någon av dessa operationer
- **Återställning**: Det finns ingen ångra-funktion, så var försiktig med borttagningar

## UI-förändringar

### Konton-fliken

Varje kontokort har nu:
- **"Ta bort konto"-knapp** (röd) i övre högra hörnet
- **🗑️-knappar** bredvid varje fil i importhistoriken
- **"Rensa alla konton"-knapp** (röd) överst på sidan

### Visuell feedback

Efter borttagning visas:
- ✅ Grön meddelande vid lyckad borttagning
- ❌ Röd meddelande vid fel
- Kontolistan uppdateras automatiskt

## Framtida förbättringar

Möjliga tillägg:
- Bekräftelsedialog innan borttagning
- Ångra-funktion för senaste borttagning
- Backup av konton före borttagning
- Batch-borttagning av flera filer samtidigt
- Export av kontodata före borttagning
