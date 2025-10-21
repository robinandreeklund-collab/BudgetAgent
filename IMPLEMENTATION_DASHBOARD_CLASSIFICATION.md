# Dashboard Classification Feature - Implementation Summary

## Översikt

Detta är en implementation av "Förslag A: Dashboard-flöde för att granska transaktioner" enligt specifikationen. Implementationen tillhandahåller ett komplett Flask-baserat REST API för transaktionskategorisering med hybrid-klassificering (regelbaserad + AI).

## Implementerade Komponenter

### 1. category_schema.yaml
**Plats:** `/category_schema.yaml` (rotkatalog)

Utökad YAML-struktur som innehåller:
- **accounts**: Kontostruktur (fylls automatiskt vid import)
- **categories**: 9 fördefinierade kategorier (mat, boende, transport, nöje, kläder, hälsa, försäkring, inkomst, övrigt)
  - Varje kategori har: display_name, keywords, color, icon
- **model_metadata**: Metadata om AI-modellen (typ, träningsstatus, accuracy metrics)
- **training_examples**: Sparade träningsexempel för AI
- **preview_sessions**: Temporära förhandsgranskningssessioner
- **persisted_settings**: Konfigurerbara inställningar
  - MIN_EXAMPLES_PER_CATEGORY: 2 (konfigurerbart)
  - Hybrid-klassificeringsinställningar
  - Träningsinställningar
  - UI-inställningar

### 2. backend/api/classification.py
**Plats:** `/backend/api/classification.py`

Flask-baserat REST API med 7 endpoints:

#### GET /api/accounts
Hämtar alla registrerade bankkonton.

#### GET /api/accounts/{accountId}/transactions
Hämtar transaktioner för ett specifikt konto med paginering (limit, offset).

#### POST /api/transactions/{transactionId}/label
Sparar träningsexempel för AI-modellen.
- Request body: `{description, category}`
- Returnerar: träningsexempel, total_examples, can_train status

#### POST /api/transactions/{transactionId}/assign
Persisterar kategorilldelning för en transaktion.
- Request body: `{category}`

#### POST /api/preview
Förhandsgranskar klassificering för flera transaktioner.
- Request body: `{transactions: [{description}]}`
- Använder hybrid-klassificering (rules -> model fallback)
- Returnerar: predicted_category, confidence, needs_review per transaktion

#### POST /api/train
Triggar asynkron träning av AI-modellen.
- Query param: `async=true/false`
- Kräver minst MIN_EXAMPLES_PER_CATEGORY (default: 2) exempel per kategori
- Kräver minst 2 kategorier

#### GET /api/model/status
Hämtar modellstatus och träningsmetadata.

**Tekniska detaljer:**
- In-memory store för demonstration (kan ersättas med databas)
- JSON-baserad kommunikation
- Felhantering för 400, 404, 500
- Integrerad med account_manager för kontoinformation

### 3. backend/service/classifier.py
**Plats:** `/backend/service/classifier.py`

Hybrid-klassificerare som kombinerar:
1. **Regelbaserad matchning** (keywords) - snabb, hög precision (confidence 0.95)
2. **TF-IDF + Naive Bayes** - fallback för okända transaktioner

**Huvudfunktioner:**
- `predict(description)` - Förutsäger kategori med confidence
- `train(training_examples, async_mode)` - Tränar modellen (synkront eller asynkront)
- `can_train()` - Kontrollerar om tillräckligt med data finns
- `get_training_status()` - Returnerar träningsstatus och metadata
- `get_category_stats()` - Statistik per kategori

**Tekniska detaljer:**
- Använder scikit-learn (TfidfVectorizer, MultinomialNB)
- Threading för asynkron träning
- Persistent lagring i category_schema.yaml
- Konfigurerbar MIN_EXAMPLES_PER_CATEGORY

### 4. tests/test_classification_api.py
**Plats:** `/tests/test_classification_api.py`

Komplett testsvit med 16 tester:
- **TestGetAccounts** (1 test)
- **TestGetAccountTransactions** (2 tester)
- **TestLabelTransaction** (3 tester)
- **TestAssignCategory** (2 tester)
- **TestPreviewClassification** (3 tester)
- **TestTriggerTraining** (2 tester)
- **TestModelStatus** (1 test)
- **TestErrorHandling** (1 test)
- **TestIntegrationFlow** (1 test) - testar hela arbetsflödet

**Testfixtures:**
- Flask test client
- Mock för att förhindra YAML-skrivning under tester
- Automatisk cleanup efter varje test

### 5. README.md uppdaterad
**Sektion tillagd:** "🔌 Classification API"

Omfattande dokumentation med:
- Hur man startar API-servern
- Detaljerad beskrivning av varje endpoint
- Exempel på curl-kommandon
- Request/response-format för alla endpoints
- Konfigurationsinstruktioner
- Integrationsbeskrivning för dashboard

### 6. CI uppdaterad
**.github/workflows/ci.yml** uppdaterad för att:
- Köra tester i både `budgetagent/tests/` och `tests/`
- Validera både `budgetagent/config/*.yaml` och `category_schema.yaml`

## Teststatus

✅ **314 tester passerar** (298 befintliga + 16 nya)
✅ **yamllint validering passerar**
✅ **Python 3.10, 3.11, 3.12 support**

## Användningsexempel

### Starta API:t
```bash
python backend/api/classification.py
# API startar på http://localhost:5000
```

### Dashboard-integration

1. **Hämta transaktioner:**
```javascript
fetch('http://localhost:5000/api/accounts/PERSONKONTO_1709/transactions?limit=50')
```

2. **Användaren väljer kategori i dropdown**

3. **"Lär AI" - Spara träningsexempel:**
```javascript
fetch('http://localhost:5000/api/transactions/abc123/label', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({description: 'ICA Maxi', category: 'mat'})
})
```

4. **Förhandsgranska klassificering:**
```javascript
fetch('http://localhost:5000/api/preview', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    transactions: [
      {description: 'ICA Supermarket'},
      {description: 'Circle K bensin'}
    ]
  })
})
```

5. **Autoträning när minst 2 exempel per kategori:**
```javascript
fetch('http://localhost:5000/api/train?async=true', {method: 'POST'})
```

## Arkitektur

```
BudgetAgent/
├── backend/
│   ├── api/
│   │   └── classification.py    # Flask REST API
│   └── service/
│       └── classifier.py         # Hybrid classifier (rules + TF-IDF)
├── tests/
│   └── test_classification_api.py  # API tester
├── category_schema.yaml           # Utökad YAML-struktur
└── README.md                      # Uppdaterad dokumentation
```

## Konfiguration

**category_schema.yaml → persisted_settings → training:**
```yaml
min_examples_per_category: 2  # Minsta antal exempel per kategori
auto_train_enabled: true      # Automatisk träning
auto_train_threshold: 2       # Minsta totalt antal exempel
```

## Vidareutveckling

Följande kan enkelt läggas till:
1. **Persistent transaktionslagring** - SQLite eller YAML-struktur
2. **Sentence-transformers** - Ersätt TF-IDF med bättre embeddings
3. **Bulk-operations** - Kategorisera många transaktioner samtidigt
4. **Träningsvisualisering** - Confusion matrix, accuracy över tid
5. **Dashboard-callbacks** - Koppla API till Dash-dashboard

## Säkerhetsnoteringar

För produktionsanvändning:
- Lägg till autentisering (t.ex. JWT tokens)
- Rate limiting på endpoints
- Input validation och sanitering
- CORS-konfiguration
- HTTPS-only i produktion
- Flytta från in-memory store till databas

## Dependencies

Alla dependencies finns redan i `requirements.txt`:
- Flask >= 3.1.2
- scikit-learn >= 1.0.0
- pyyaml >= 6.0
- numpy (via scikit-learn)

## Sammanfattning

✅ **Alla deliverables från specifikationen är implementerade:**
1. ✅ category_schema.yaml med utökad struktur
2. ✅ backend/api/classification.py med 7 endpoints
3. ✅ backend/service/classifier.py med hybrid classifier
4. ✅ README.md uppdaterad med instruktioner
5. ✅ tests/test_classification_api.py med 16 tester
6. ✅ CI uppdaterad för nya tester
7. ✅ MIN_EXAMPLES_PER_CATEGORY = 2 (konfigurerbart)

**Status: Fungerande, reviewbart initial implementation redo för dashboard-integration och vidareutveckling.**
