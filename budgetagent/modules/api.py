"""
API-modul för BudgetAgent med endpoints för kontohantering och kategorisering.

Detta är en enkel API-struktur som kan användas med Dash callbacks eller
utökas till en full REST API med Flask/FastAPI.

Endpoints:
- list_accounts: Lista alla konton
- get_account_transactions: Hämta transaktioner för ett konto (paginerat)
- bulk_label: Kategorisera flera transaktioner samtidigt
- create_category: Skapa ny kategori
- train_model: Lägg till träningsexempel och träna AI-modell
- preview_categorization: Förhandsgranska kategorisering utan att spara
"""

from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import date
from decimal import Decimal
from pathlib import Path
import yaml

from . import account_manager
from .models import Transaction, Account
from .categorize_expenses import (
    add_training_example,
    auto_categorize,
    build_index
)


def list_accounts() -> List[Dict]:
    """
    Listar alla konton i systemet.
    
    Returns:
        Lista med konto-dictionaries med metadata
    """
    accounts = account_manager.load_accounts()
    
    result = []
    for account_name, account in accounts.items():
        result.append({
            'account_name': account.account_name,
            'account_number': account.account_number,
            'imported_files_count': len(account.imported_files),
            'transaction_count': len(account.transaction_hashes),
            'last_import_date': account.last_import_date.isoformat() if account.last_import_date else None,
            'current_balance': str(account.current_balance) if account.current_balance else None,
            'balance_date': account.balance_date.isoformat() if account.balance_date else None,
            'balance_currency': account.balance_currency
        })
    
    return result


def get_account_transactions(
    account_name: str,
    page: int = 1,
    per_page: int = 50,
    include_categorized: bool = True
) -> Dict:
    """
    Hämtar transaktioner för ett konto med paginering.
    
    Args:
        account_name: Namn på kontot
        page: Sidnummer (1-indexerat)
        per_page: Antal transaktioner per sida (max 100)
        include_categorized: Om True, inkludera redan kategoriserade transaktioner
        
    Returns:
        Dictionary med transaktioner och paginerings-metadata
    """
    # Begränsa per_page till max 100
    per_page = min(per_page, 100)
    
    # Ladda alla transaktioner från kontot
    # I praktiken skulle detta läsa från en databas eller CSV-fil
    # För nu returnerar vi en mock-respons med struktur
    
    # TODO: Implementera faktisk transaktionshämtning från databas/fil
    # Detta skulle kräva att transaktioner sparas persistent med konto-referens
    
    return {
        'account_name': account_name,
        'page': page,
        'per_page': per_page,
        'total_count': 0,
        'total_pages': 0,
        'transactions': []
    }


def bulk_label(
    transactions: List[Dict],
    labels: Dict[int, str]
) -> Dict:
    """
    Kategoriserar flera transaktioner samtidigt.
    
    Args:
        transactions: Lista med transaction-dictionaries
        labels: Dictionary med index -> kategori-mappningar
        
    Returns:
        Dictionary med resultat och statistik
    """
    updated_count = 0
    errors = []
    
    for idx, category in labels.items():
        if idx >= len(transactions):
            errors.append(f"Index {idx} utanför intervall")
            continue
        
        try:
            transactions[idx]['category'] = category
            updated_count += 1
        except Exception as e:
            errors.append(f"Fel vid uppdatering av index {idx}: {str(e)}")
    
    return {
        'success': len(errors) == 0,
        'updated_count': updated_count,
        'errors': errors
    }


def create_category(
    category_name: str,
    keywords: List[str],
    confidence: float = 0.95,
    parent_category: Optional[str] = None
) -> Dict:
    """
    Skapar en ny kategori i kategoriseringsreglerna.
    
    Args:
        category_name: Namn på kategorin
        keywords: Lista med nyckelord för kategorin
        confidence: Säkerhetsvärde för regelbaserad matchning (0-1)
        parent_category: Valfri huvudkategori
        
    Returns:
        Dictionary med resultat
    """
    try:
        # Ladda befintliga regler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f) or {}
        
        # Skapa ny kategori
        new_category = {
            'keywords': keywords,
            'confidence': confidence
        }
        
        if parent_category:
            new_category['parent'] = parent_category
        
        # Lägg till i regler
        if 'categories' not in rules:
            rules['categories'] = {}
        
        rules['categories'][category_name.lower()] = new_category
        
        # Spara tillbaka
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, allow_unicode=True, default_flow_style=False)
        
        return {
            'success': True,
            'category_name': category_name,
            'message': f"Kategori '{category_name}' skapad"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def train_model(
    description: str,
    category: str,
    confidence: float = 1.0
) -> Dict:
    """
    Lägger till träningsexempel och tränar AI-modellen.
    
    Args:
        description: Transaktionsbeskrivning
        category: Korrekt kategori
        confidence: Säkerhetsvärde (1.0 för manuella val)
        
    Returns:
        Dictionary med resultat
    """
    try:
        # Lägg till träningsexempel
        add_training_example(description, category, confidence)
        
        # Bygg om index (triggas automatiskt i add_training_example via cache invalidation)
        model, vectorizer, categories = build_index()
        
        return {
            'success': True,
            'message': f"Träningsexempel tillagt: '{description}' -> '{category}'",
            'model_status': 'trained' if model is not None else 'not_enough_data',
            'categories_count': len(categories) if categories else 0
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def preview_categorization(
    transactions: List[Dict],
    use_rules: bool = True,
    use_ai_fallback: bool = True
) -> List[Dict]:
    """
    Förhandsgranskar kategorisering utan att spara.
    
    Args:
        transactions: Lista med transaction-dictionaries
        use_rules: Om regelbaserad matchning ska användas
        use_ai_fallback: Om AI-fallback ska användas
        
    Returns:
        Lista med transaktioner inkl. föreslagen kategori och confidence
    """
    try:
        # Konvertera till DataFrame
        df = pd.DataFrame(transactions)
        
        # Ladda kategoriseringsregler
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f) or {}
        
        # Kör kategorisering
        result_df = auto_categorize(
            df, 
            rules, 
            config={
                'use_rules': use_rules,
                'use_ai_fallback': use_ai_fallback,
                'confidence_threshold': 0.7,
                'ai_min_confidence': 0.5
            }
        )
        
        # Konvertera tillbaka till dictionaries
        return result_df.to_dict('records')
        
    except Exception as e:
        print(f"Fel vid förhandsgranskning: {e}")
        return transactions


def get_training_data_stats() -> Dict:
    """
    Hämtar statistik om träningsdata.
    
    Returns:
        Dictionary med statistik
    """
    from .categorize_expenses import load_training_data
    
    training_data = load_training_data()
    
    # Räkna kategorier
    categories = {}
    for example in training_data:
        category = example.get('category', 'Unknown')
        categories[category] = categories.get(category, 0) + 1
    
    return {
        'total_examples': len(training_data),
        'categories': categories,
        'unique_categories': len(categories)
    }


def list_categories() -> List[Dict]:
    """
    Listar alla tillgängliga kategorier.
    
    Returns:
        Lista med kategori-dictionaries
    """
    try:
        config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f) or {}
        
        categories = []
        for category_name, category_data in rules.get('categories', {}).items():
            categories.append({
                'name': category_name.capitalize(),
                'keywords_count': len(category_data.get('keywords', [])),
                'confidence': category_data.get('confidence', 0.95),
                'subcategories': category_data.get('subcategories', [])
            })
        
        return categories
        
    except Exception as e:
        print(f"Fel vid hämtning av kategorier: {e}")
        return []
