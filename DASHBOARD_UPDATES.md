# Dashboard-uppdateringar

Denna uppdatering lägger till flera nya funktioner i BudgetAgent Dashboard enligt användarens önskemål.

## Nya funktioner

### 1. Kontohantering-panel (Ny flik)

En helt ny flik "Konton" har lagts till i dashboarden som visar:

- **Kontoöversikt**: Alla registrerade bankkonton
- **Kontonummer**: Om tillgängligt
- **Import-statistik**: Antal importerade filer och transaktioner
- **Senaste import**: Datum för senaste import
- **Import-historik**: Expanderbar lista över alla importerade filer

**Användning:**
- Navigera till fliken "Konton"
- Klicka på "Uppdatera kontoöversikt" för att se senaste data
- Expandera "Visa importhistorik" för att se detaljerad information

### 2. Förbättrad CSV-import med kategorisering

CSV-importen har utökats med automatisk kategorisering:

**Vid uppladdning:**
1. Filen läses in och transaktioner extraheras
2. Transaktioner kategoriseras automatiskt med regelbaserad matchning
3. Confidence score beräknas för varje transaktion
4. Transaktioner flaggas för manuell granskning om confidence < 70%

**Visuell feedback:**
- ✅ Grön: Hög confidence (>90%)
- ⚠️ Gul: Medel confidence (70-90%)
- ❌ Röd: Låg confidence (<70%)

### 3. Granskningspanel för manuell kategorisering

Efter uppladdning visas en interaktiv granskningspanel där användaren kan:

- **Se alla transaktioner** i en tabell
- **Visa kategoriseringsstatus**: Automatisk kategori, confidence score, review-status
- **Redigera kategorier**: Dropdown-meny för att ändra kategori om nödvändigt
- **Godkänna och spara**: Knapp för att bekräfta och spara transaktioner

**Tabell-kolumner:**
1. **#**: Löpnummer
2. **Datum**: Transaktionsdatum
3. **Beskrivning**: Transaktionsbeskrivning (max 40 tecken)
4. **Belopp**: Transaktionsbelopp i SEK
5. **Kategori**: Dropdown med alla tillgängliga kategorier
6. **Säkerhet**: Confidence score i procent (färgkodad)

**Färgkodning per rad:**
- Grön bakgrund: Hög confidence
- Gul bakgrund: Medel confidence
- Röd bakgrund: Låg confidence (behöver granskning)

### 4. Utgiftsfördelning (Översikt-fliken)

En ny sektion har lagts till på översiktsfliken som visar:

- **Cirkeldiagram**: Visuell fördelning av utgifter per kategori
- **Procentandel**: Varje kategoris andel av totala utgifter
- **Absoluta belopp**: SEK-belopp per kategori
- **Interaktiv**: Hover för detaljer, klicka för att dölja/visa kategorier

**Uppdateras automatiskt:**
- När nya transaktioner importeras
- När kategorier ändras

## Tekniska detaljer

### Nya funktioner i dashboard_ui.py

1. **`accounts_panel()`**: Skapar kontohanteringspanelen
2. **`create_expense_distribution_section()`**: Skapar utgiftsfördelningssektionen
3. **`create_categorization_review_panel()`**: Skapar granskningspanelen
4. **`update_accounts_display()`**: Callback för att uppdatera kontovisning
5. **`update_expense_distribution()`**: Callback för cirkeldiagram
6. **`confirm_and_save_transactions()`**: Callback för att spara granskade transaktioner

### Uppdaterad CSV-import

Funktionen `handle_csv_upload()` har utökats med:
- Automatisk kategorisering med `categorize_expenses.categorize_transactions()`
- Confidence scoring för varje transaktion
- Temporär lagring för granskning innan final import
- Visuell feedback om kategoriseringsstatus

### Integration med account_manager

Dashboarden integrerar nu fullt med `account_manager`-modulen:
- Visa alla registrerade konton
- Import-historik per konto
- Dupliceringsskydd fungerar transparent

## Användningsexempel

### Import med kategorisering:

1. Gå till fliken "Inmatning"
2. Dra och släpp eller välj en Nordea CSV-fil
3. Vänta medan filen importeras och kategoriseras
4. Granska transaktionerna i tabellen som visas
5. Ändra kategorier vid behov genom dropdown-menyer
6. Klicka på "Godkänn och spara transaktioner"
7. Se uppdaterad data i översikten

### Visa kontoöversikt:

1. Gå till fliken "Konton"
2. Se alla registrerade konton
3. Klicka på "Uppdatera kontoöversikt" för senaste data
4. Expandera "Visa importhistorik" för detaljer

### Analysera utgiftsfördelning:

1. Gå till fliken "Översikt"
2. Scrolla ner till "Utgiftsfördelning per kategori"
3. Se cirkeldiagram med alla kategorier
4. Hover över sektioner för exakta belopp
5. Klicka på kategorier i legenden för att dölja/visa

## Fördelar

- ✅ **Transparent kategorisering**: Användaren ser direkt hur transaktioner kategoriseras
- ✅ **Manuell kontroll**: Möjlighet att granska och justera före import
- ✅ **Visuell feedback**: Färgkodning och ikoner för enkel översikt
- ✅ **Kontoöversikt**: Full kontroll över importerad data per konto
- ✅ **Utgiftsanalys**: Tydlig visualisering av hur pengarna används
- ✅ **AI-potential**: Struktur för framtida ML-baserad kategorisering

## Framtida förbättringar

Möjliga tillägg i framtiden:
- Export av kontodata till CSV/Excel
- Filtrera utgiftsfördelning per tidsperiod
- Jämför utgiftsfördelning mellan månader
- Automatisk lärning från manuella korrigeringar
- Batch-kategorisering av flera transaktioner samtidigt
- Ångra-funktion för importer
