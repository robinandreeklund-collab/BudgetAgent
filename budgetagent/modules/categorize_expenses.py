"""
Modul för kategorisering av transaktioner automatiskt eller manuellt.

Denna modul hanterar kategorisering av utgifter baserat på nyckelord
och regler. Den stödjer både automatisk kategorisering via
regelbaserad matchning och manuell överstyring av användaren.

Exempel på YAML-konfiguration kan laddas från categorization_rules.yaml:
    categories:
      mat:
        keywords: ["ica", "coop", "willys", "hemköp"]
      transport:
        keywords: ["sl", "uber", "bensin"]
"""

import pandas as pd
from typing import Dict, Optional, List
from .models import Transaction


def auto_categorize(data: pd.DataFrame, rules: Dict) -> pd.DataFrame:
    """
    Matchar transaktioner mot nyckelord i beskrivning.
    
    Använder regelbaserad matchning för att automatiskt kategorisera
    transaktioner baserat på text i beskrivningsfältet.
    
    Args:
        data: DataFrame med transaktionsdata
        rules: Dictionary med kategoriseringsregler från YAML
        
    Returns:
        DataFrame med kategoriserade transaktioner
    """
    df = data.copy()
    
    # Initiera kategorikolumn om den inte finns
    if 'category' not in df.columns:
        df['category'] = None
    
    if 'description' not in df.columns:
        return df
    
    # Gå igenom varje transaktion
    for idx, row in df.iterrows():
        if pd.notna(row.get('category')):
            # Skippa om kategori redan är satt
            continue
            
        desc = str(row['description']).lower()
        
        # Matcha mot regler
        for category, config in rules.items():
            if 'keywords' in config:
                keywords = config['keywords']
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword.lower() in desc:
                            df.at[idx, 'category'] = category.capitalize()
                            break
            if pd.notna(df.at[idx, 'category']):
                break
        
        # Sätt "Okategoriserad" om ingen match
        if pd.isna(df.at[idx, 'category']):
            df.at[idx, 'category'] = "Okategoriserad"
    
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
    Kategoriserar en lista av Transaction-objekt.
    
    Huvudfunktion för att kategorisera transaktioner från andra moduler.
    Används av import_bank_data och parse_transactions för att tilldela
    kategorier till importerade transaktioner.
    
    Args:
        transactions: Lista med Transaction-objekt
        rules: Dictionary med kategoriseringsregler från YAML
        
    Returns:
        Lista med kategoriserade Transaction-objekt
    """
    categorized_transactions = []
    
    for transaction in transactions:
        # Om transaktionen redan har en kategori, behåll den
        if transaction.category:
            categorized_transactions.append(transaction)
            continue
        
        # Matcha mot regler
        desc = transaction.description.lower()
        matched_category = None
        
        for category, config in rules.items():
            if 'keywords' in config:
                keywords = config['keywords']
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword.lower() in desc:
                            matched_category = category.capitalize()
                            break
            if matched_category:
                break
        
        # Skapa ny transaktion med kategori
        categorized_transaction = Transaction(
            date=transaction.date,
            amount=transaction.amount,
            description=transaction.description,
            category=matched_category or "Okategoriserad",
            currency=transaction.currency,
            metadata=transaction.metadata
        )
        categorized_transactions.append(categorized_transaction)
    
    return categorized_transactions
