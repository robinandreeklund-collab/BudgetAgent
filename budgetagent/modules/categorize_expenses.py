"""
Modul för kategorisering av transaktioner automatiskt eller manuellt.

Denna modul hanterar kategorisering av utgifter baserat på nyckelord
och regler. Den stödjer både automatisk kategorisering via
regelbaserad matchning och manuell överstyring av användaren.

Stöd för hybridkategorisering:
- Regelbaserad matchning med högt säkerhetsvärde
- AI-baserad fallback vid okända transaktioner (stub för framtida ML-modell)
- Flaggning för manuell granskning vid låg säkerhet

Exempel på YAML-konfiguration kan laddas från categorization_rules.yaml:
    config:
      use_rules: true
      use_ai_fallback: true
      confidence_threshold: 0.7
    categories:
      mat:
        keywords: ["ica", "coop", "willys", "hemköp"]
        confidence: 0.95
      transport:
        keywords: ["sl", "uber", "bensin"]
        confidence: 0.95
"""

import pandas as pd
from typing import Dict, Optional, List, Tuple
from .models import Transaction


def _ai_categorize_fallback(description: str) -> Tuple[str, float]:
    """
    AI-baserad kategorisering som fallback.
    
    Detta är en stub-implementation för framtida AI-baserad kategorisering
    med scikit-learn, spaCy eller embedding-modeller. För närvarande returnerar
    den "Okategoriserad" med låg säkerhet för att signalera att AI-modellen
    inte är tränad än.
    
    Framtida implementation kan inkludera:
    - TF-IDF vektorisering med scikit-learn classifier
    - spaCy för text-analys och named entity recognition
    - Sentence transformers för semantisk likhet
    - Fine-tunad BERT-modell för svensk text
    
    Args:
        description: Transaktionsbeskrivning
        
    Returns:
        Tuple med (kategori, säkerhetsvärde)
    """
    # TODO: Implementera riktig AI-baserad kategorisering
    # Exempel på framtida implementation:
    # 
    # from sklearn.feature_extraction.text import TfidfVectorizer
    # from sklearn.naive_bayes import MultinomialNB
    # 
    # # Ladda tränad modell
    # model = load_trained_model()
    # vectorizer = load_vectorizer()
    # 
    # # Vektorisera beskrivning
    # features = vectorizer.transform([description])
    # 
    # # Prediktera kategori
    # probabilities = model.predict_proba(features)[0]
    # category_idx = probabilities.argmax()
    # confidence = probabilities[category_idx]
    # category = model.classes_[category_idx]
    # 
    # return category, confidence
    
    # Stub-implementation: returnera okategoriserad med låg säkerhet
    return "Okategoriserad", 0.3


def auto_categorize(data: pd.DataFrame, rules: Dict, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Matchar transaktioner mot nyckelord i beskrivning med hybridmodell.
    
    Använder regelbaserad matchning först, med AI-baserad fallback och
    flaggning för manuell granskning vid låg säkerhet.
    
    Process:
    1. Regelbaserad matchning med högt säkerhetsvärde
    2. AI-baserad kategorisering vid ingen match (om aktiverat)
    3. Flaggning för manuell granskning vid låg säkerhet
    4. "Okategoriserad" vid mycket låg säkerhet
    
    Args:
        data: DataFrame med transaktionsdata
        rules: Dictionary med kategoriseringsregler från YAML
        config: Valfri konfiguration för hybrid-modell
        
    Returns:
        DataFrame med kategoriserade transaktioner, inkl. confidence och needs_review
    """
    df = data.copy()
    
    # Ladda config från rules om det inte ges separat
    if config is None:
        config = rules.get('config', {})
    
    # Default-konfiguration
    use_rules = config.get('use_rules', True)
    use_ai_fallback = config.get('use_ai_fallback', True)
    confidence_threshold = config.get('confidence_threshold', 0.7)
    ai_min_confidence = config.get('ai_min_confidence', 0.5)
    flag_low_confidence = config.get('flag_low_confidence', True)
    
    # Hämta kategorier - hantera både platt struktur och nested struktur
    if 'categories' in rules and isinstance(rules['categories'], dict):
        # Ny struktur med nested categories
        categories = rules['categories']
    else:
        # Gammal struktur (platt) - skippa config-nyckeln
        categories = {k: v for k, v in rules.items() if k != 'config'}
    
    # Initiera kolumner om de inte finns
    if 'category' not in df.columns:
        df['category'] = None
    if 'confidence' not in df.columns:
        df['confidence'] = 0.0
    if 'needs_review' not in df.columns:
        df['needs_review'] = False
    
    if 'description' not in df.columns:
        return df
    
    # Gå igenom varje transaktion
    for idx, row in df.iterrows():
        if pd.notna(row.get('category')) and row.get('category') != '':
            # Skippa om kategori redan är satt
            continue
            
        desc = str(row['description']).lower()
        matched_category = None
        category_confidence = 0.0
        
        # Steg 1: Regelbaserad matchning
        if use_rules:
            for category, cat_config in categories.items():
                if 'keywords' in cat_config:
                    keywords = cat_config['keywords']
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            if keyword.lower() in desc:
                                matched_category = category.capitalize()
                                # Hämta säkerhetsvärde från kategori-config eller använd standard
                                category_confidence = cat_config.get('confidence', 0.95)
                                break
                if matched_category:
                    break
        
        # Steg 2: AI-baserad fallback om ingen match
        if not matched_category and use_ai_fallback:
            ai_category, ai_confidence = _ai_categorize_fallback(desc)
            
            # Använd AI-resultat endast om säkerheten är över minimum
            if ai_confidence >= ai_min_confidence:
                matched_category = ai_category
                category_confidence = ai_confidence
        
        # Steg 3: Sätt kategori och säkerhetsvärde
        if matched_category:
            df.at[idx, 'category'] = matched_category
            df.at[idx, 'confidence'] = category_confidence
        else:
            df.at[idx, 'category'] = "Okategoriserad"
            df.at[idx, 'confidence'] = 0.0
        
        # Steg 4: Flagga för manuell granskning vid låg säkerhet
        if flag_low_confidence and df.at[idx, 'confidence'] < confidence_threshold:
            df.at[idx, 'needs_review'] = True
    
    return df


def manual_override(data: pd.DataFrame, overrides: Dict) -> pd.DataFrame:
    """
    Tillåter användaren att justera kategorier.
    
    Applicerar manuella överstyrningar på specifika transaktioner
    där den automatiska kategoriseringen behöver korrigeras.
    
    Args:
        data: DataFrame med transaktionsdata
        overrides: Dictionary med manuella kategoriseringar
                   Format: {index: "Kategori"} eller {"description_pattern": "Kategori"}
        
    Returns:
        DataFrame med uppdaterade kategorier
    """
    df = data.copy()
    
    if 'category' not in df.columns:
        df['category'] = None
    
    # Applicera överstyrningar
    for key, category in overrides.items():
        if isinstance(key, int):
            # Index-baserad överstyring
            if key < len(df):
                df.at[key, 'category'] = category
        elif isinstance(key, str):
            # Beskrivnings-baserad överstyring
            mask = df['description'].str.contains(key, case=False, na=False)
            df.loc[mask, 'category'] = category
    
    return df


def get_transactions_needing_review(data: pd.DataFrame) -> pd.DataFrame:
    """
    Returnerar transaktioner som behöver manuell granskning.
    
    Filtrerar ut transaktioner där needs_review är True, dvs. transaktioner
    där kategoriseringen har låg säkerhet och bör granskas manuellt.
    
    Args:
        data: DataFrame med transaktionsdata
        
    Returns:
        DataFrame med endast transaktioner som behöver granskning
    """
    if 'needs_review' not in data.columns:
        return pd.DataFrame()
    
    return data[data['needs_review'] == True].copy()


def get_uncategorized_transactions(data: pd.DataFrame) -> pd.DataFrame:
    """
    Returnerar okategoriserade transaktioner.
    
    Filtrerar ut transaktioner som kategoriserats som "Okategoriserad"
    och därför kan behöva ytterligare granskning.
    
    Args:
        data: DataFrame med transaktionsdata
        
    Returns:
        DataFrame med endast okategoriserade transaktioner
    """
    if 'category' not in data.columns:
        return pd.DataFrame()
    
    return data[data['category'] == 'Okategoriserad'].copy()


def update_category_map(new_rules: Dict) -> None:
    """
    Uppdaterar YAML-regler för framtida matchning.
    
    Sparar nya eller uppdaterade kategoriseringsregler tillbaka till
    YAML-filen för att förbättra framtida automatisk kategorisering.
    
    Args:
        new_rules: Dictionary med nya kategoriseringsregler
    """
    import yaml
    from pathlib import Path
    
    # Sökväg till kategoriseringsregler
    config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
    
    # Ladda befintliga regler om de finns
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            existing_rules = yaml.safe_load(f) or {}
    else:
        existing_rules = {}
    
    # Uppdatera med nya regler
    if 'categories' not in existing_rules:
        existing_rules['categories'] = {}
    
    existing_rules['categories'].update(new_rules)
    
    # Spara tillbaka
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(existing_rules, f, allow_unicode=True, default_flow_style=False)


def categorize_transactions(transactions: List[Transaction], rules: Dict) -> List[Transaction]:
    """
    Kategoriserar en lista av Transaction-objekt med hybridmodell.
    
    Huvudfunktion för att kategorisera transaktioner från andra moduler.
    Används av import_bank_data och parse_transactions för att tilldela
    kategorier till importerade transaktioner.
    
    Använder regelbaserad matchning först, med AI-baserad fallback och
    flaggning för manuell granskning vid låg säkerhet.
    
    Args:
        transactions: Lista med Transaction-objekt
        rules: Dictionary med kategoriseringsregler från YAML
        
    Returns:
        Lista med kategoriserade Transaction-objekt
    """
    # Ladda config
    config = rules.get('config', {})
    use_rules = config.get('use_rules', True)
    use_ai_fallback = config.get('use_ai_fallback', True)
    confidence_threshold = config.get('confidence_threshold', 0.7)
    ai_min_confidence = config.get('ai_min_confidence', 0.5)
    flag_low_confidence = config.get('flag_low_confidence', True)
    
    # Hämta kategorier - hantera både platt struktur och nested struktur
    if 'categories' in rules and isinstance(rules['categories'], dict):
        # Ny struktur med nested categories
        categories = rules['categories']
    else:
        # Gammal struktur (platt) - skippa config-nyckeln
        categories = {k: v for k, v in rules.items() if k != 'config'}
    
    categorized_transactions = []
    
    for transaction in transactions:
        # Om transaktionen redan har en kategori, behåll den
        if transaction.category:
            categorized_transactions.append(transaction)
            continue
        
        desc = transaction.description.lower()
        matched_category = None
        category_confidence = 0.0
        
        # Steg 1: Regelbaserad matchning
        if use_rules:
            for category, cat_config in categories.items():
                if 'keywords' in cat_config:
                    keywords = cat_config['keywords']
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            if keyword.lower() in desc:
                                matched_category = category.capitalize()
                                category_confidence = cat_config.get('confidence', 0.95)
                                break
                if matched_category:
                    break
        
        # Steg 2: AI-baserad fallback om ingen match
        if not matched_category and use_ai_fallback:
            ai_category, ai_confidence = _ai_categorize_fallback(desc)
            
            if ai_confidence >= ai_min_confidence:
                matched_category = ai_category
                category_confidence = ai_confidence
        
        # Steg 3: Sätt kategori
        final_category = matched_category or "Okategoriserad"
        if not matched_category:
            category_confidence = 0.0
        
        # Lägg till metadata om säkerhet och manuell granskning
        metadata = transaction.metadata.copy() if transaction.metadata else {}
        metadata['confidence'] = str(category_confidence)
        
        if flag_low_confidence and category_confidence < confidence_threshold:
            metadata['needs_review'] = 'true'
        
        # Skapa ny transaktion med kategori
        categorized_transaction = Transaction(
            date=transaction.date,
            amount=transaction.amount,
            description=transaction.description,
            category=final_category,
            currency=transaction.currency,
            metadata=metadata
        )
        categorized_transactions.append(categorized_transaction)
    
    return categorized_transactions
