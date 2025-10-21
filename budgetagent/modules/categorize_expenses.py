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
    pass


def manual_override(data: pd.DataFrame, overrides: Dict) -> pd.DataFrame:
    """
    Tillåter användaren att justera kategorier.
    
    Applicerar manuella överstyrningar på specifika transaktioner
    där den automatiska kategoriseringen behöver korrigeras.
    
    Args:
        data: DataFrame med transaktionsdata
        overrides: Dictionary med manuella kategoriseringar
        
    Returns:
        DataFrame med uppdaterade kategorier
    """
    pass


def update_category_map(new_rules: Dict) -> None:
    """
    Uppdaterar YAML-regler för framtida matchning.
    
    Sparar nya eller uppdaterade kategoriseringsregler tillbaka till
    YAML-filen för att förbättra framtida automatisk kategorisering.
    
    Args:
        new_rules: Dictionary med nya kategoriseringsregler
    """
    pass


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
    pass
