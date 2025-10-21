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
import yaml
import pickle
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import date
from .models import Transaction

# Global cache för TF-IDF modell
_tfidf_model = None
_tfidf_vectorizer = None
_tfidf_categories = None


def load_training_data() -> List[Dict]:
    """
    Laddar träningsdata från YAML-fil.
    
    Läser in sparad träningsdata som användaren har markerat via UI:t
    för att förbättra AI-kategorisering.
    
    Returns:
        Lista med träningsexempel (dict med 'description' och 'category')
    """
    training_data_path = Path(__file__).parent.parent / "data" / "training_data.yaml"
    
    if not training_data_path.exists():
        return []
    
    try:
        with open(training_data_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return data.get('training_examples', [])
    except Exception as e:
        print(f"Varning: Kunde inte ladda träningsdata: {e}")
        return []


def save_training_data(training_examples: List[Dict]) -> None:
    """
    Sparar träningsdata till YAML-fil.
    
    Skriver ut träningsdata som användaren har markerat via UI:t
    för att förbättra AI-kategorisering.
    
    Args:
        training_examples: Lista med träningsexempel
    """
    training_data_path = Path(__file__).parent.parent / "data" / "training_data.yaml"
    training_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(training_data_path, 'w', encoding='utf-8') as f:
        yaml.dump({'training_examples': training_examples}, f, allow_unicode=True, default_flow_style=False)


def add_training_example(description: str, category: str, confidence: float = 1.0) -> None:
    """
    Lägger till ett träningsexempel för AI-modellen.
    
    Sparar en beskrivning-kategori-mappning som används för att träna
    TF-IDF-modellen och förbättra framtida kategorisering.
    
    Args:
        description: Transaktionsbeskrivning
        category: Korrekt kategori
        confidence: Säkerhetsvärde (standard 1.0 för manuella val)
    """
    training_examples = load_training_data()
    
    # Lägg till nytt exempel
    new_example = {
        'description': description,
        'category': category,
        'date_added': date.today().isoformat(),
        'confidence': confidence
    }
    
    # Kontrollera om exempel redan finns (undvik dubbletter)
    for example in training_examples:
        if example['description'].lower() == description.lower():
            # Uppdatera befintligt exempel
            example['category'] = category
            example['date_added'] = date.today().isoformat()
            example['confidence'] = confidence
            save_training_data(training_examples)
            return
    
    # Lägg till nytt exempel
    training_examples.append(new_example)
    save_training_data(training_examples)
    
    # Invalidera cached modell så att den byggs om nästa gång
    global _tfidf_model, _tfidf_vectorizer, _tfidf_categories
    _tfidf_model = None
    _tfidf_vectorizer = None
    _tfidf_categories = None


def build_index() -> Tuple[Optional[object], Optional[object], Optional[List[str]]]:
    """
    Bygger TF-IDF-index från träningsdata.
    
    Skapar en TF-IDF vektorisering och tränar en enkel klassificerare
    baserat på sparad träningsdata. Använder scikit-learn.
    
    Returns:
        Tuple med (modell, vectorizer, kategorier) eller (None, None, None) om för lite data
    """
    training_examples = load_training_data()
    
    # Behöver minst 2 exempel och 2 kategorier för att träna
    if len(training_examples) < 2:
        return None, None, None
    
    categories = list(set(ex['category'] for ex in training_examples))
    if len(categories) < 2:
        return None, None, None
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        
        # Extrahera beskrivningar och kategorier
        descriptions = [ex['description'].lower() for ex in training_examples]
        labels = [ex['category'] for ex in training_examples]
        
        # Skapa TF-IDF vektorisering
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),  # Unigrams och bigrams
            min_df=1,
            lowercase=True
        )
        
        # Vektorisera beskrivningar
        X = vectorizer.fit_transform(descriptions)
        
        # Träna Naive Bayes klassificerare
        model = MultinomialNB()
        model.fit(X, labels)
        
        return model, vectorizer, categories
        
    except ImportError:
        print("Varning: scikit-learn inte installerat. TF-IDF-kategorisering inte tillgänglig.")
        return None, None, None
    except Exception as e:
        print(f"Varning: Kunde inte bygga TF-IDF-index: {e}")
        return None, None, None


def embedding_match(description: str) -> Tuple[str, float]:
    """
    Använder TF-IDF embedding för att hitta liknande kategorier.
    
    Använder träningsdata och TF-IDF-modell för att prediktera kategori
    baserat på semantisk likhet med tidigare kategoriserade transaktioner.
    
    Args:
        description: Transaktionsbeskrivning
        
    Returns:
        Tuple med (kategori, säkerhetsvärde)
    """
    global _tfidf_model, _tfidf_vectorizer, _tfidf_categories
    
    # Bygg eller ladda cached modell
    if _tfidf_model is None:
        _tfidf_model, _tfidf_vectorizer, _tfidf_categories = build_index()
    
    # Om ingen modell kunde byggas, returnera okategoriserad
    if _tfidf_model is None:
        return "Okategoriserad", 0.0
    
    try:
        # Vektorisera beskrivning
        X = _tfidf_vectorizer.transform([description.lower()])
        
        # Prediktera med sannolikheter
        probabilities = _tfidf_model.predict_proba(X)[0]
        
        # Hitta kategori med högst sannolikhet
        best_idx = probabilities.argmax()
        confidence = float(probabilities[best_idx])
        category = _tfidf_model.classes_[best_idx]
        
        return category, confidence
        
    except Exception as e:
        print(f"Varning: Embedding-matchning misslyckades: {e}")
        return "Okategoriserad", 0.0


def _ai_categorize_fallback(description: str) -> Tuple[str, float]:
    """
    AI-baserad kategorisering som fallback.
    
    Använder TF-IDF-baserad kategorisering med scikit-learn som fallback
    när regelbaserad matchning inte ger resultat. Tränas automatiskt från
    användarens träningsdata.
    
    Framtida förbättringar kan inkludera:
    - spaCy för text-analys och named entity recognition
    - Sentence transformers för semantisk likhet
    - Fine-tunad BERT-modell för svensk text
    
    Args:
        description: Transaktionsbeskrivning
        
    Returns:
        Tuple med (kategori, säkerhetsvärde)
    """
    # Använd TF-IDF embedding-matchning
    return embedding_match(description)


def rule_match(description: str, rules: Dict) -> Tuple[Optional[str], float]:
    """
    Matchar en beskrivning mot regelbaserade nyckelord.
    
    Går igenom alla kategorier och deras nyckelord för att hitta en match.
    Returnerar första matchningen med dess säkerhetsvärde.
    
    Args:
        description: Transaktionsbeskrivning att matcha
        rules: Dictionary med kategoriseringsregler
        
    Returns:
        Tuple med (kategori, säkerhetsvärde) eller (None, 0.0) om ingen match
    """
    desc_lower = description.lower()
    
    # Hämta kategorier från rules
    if 'categories' in rules and isinstance(rules['categories'], dict):
        categories = rules['categories']
    else:
        categories = {k: v for k, v in rules.items() if k != 'config'}
    
    # Sök efter matchningar
    for category, cat_config in categories.items():
        if 'keywords' in cat_config:
            keywords = cat_config['keywords']
            if isinstance(keywords, list):
                for keyword in keywords:
                    if keyword.lower() in desc_lower:
                        confidence = cat_config.get('confidence', 0.95)
                        return category.capitalize(), confidence
    
    return None, 0.0


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
            
        desc = str(row['description'])
        matched_category = None
        category_confidence = 0.0
        
        # Steg 1: Regelbaserad matchning
        if use_rules:
            matched_category, category_confidence = rule_match(desc, rules)
        
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
        
        desc = transaction.description
        matched_category = None
        category_confidence = 0.0
        
        # Steg 1: Regelbaserad matchning
        if use_rules:
            matched_category, category_confidence = rule_match(desc, rules)
        
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
