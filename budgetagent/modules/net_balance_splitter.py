"""
Modul för fördelning av kvarvarande pengar efter utgifter enligt valda regler.

Denna modul hanterar rättvis fördelning av kvarvarande saldo mellan personer
i hushållet. Den stödjer olika fördelningsregler som 50/50-delning,
inkomstbaserad fördelning eller anpassade kvoter.

Exempel på YAML-konfiguration (net_balance_splitter.yaml):
    net_balance_splitter:
      split_rule: "income_weighted"
      custom_ratio:
        Robin: 0.60
        Partner: 0.40
      shared_expense_categories: ["Boende", "Mat", "Hem"]
"""

import pandas as pd
from typing import Dict


def split_balance(total_income: Dict, total_expenses: Dict, rule: str) -> Dict:
    """
    Returnerar fördelning per person.
    
    Beräknar hur kvarvarande saldo ska fördelas mellan personer
    baserat på vald regel.
    
    Args:
        total_income: Dictionary med total inkomst per person
        total_expenses: Dictionary med totala utgifter per person
        rule: Fördelningsregel, t.ex. "equal_split", "income_weighted", "custom_ratio"
        
    Returns:
        Dictionary med fördelat saldo per person
    """
    pass


def apply_custom_ratio(ratio: Dict) -> None:
    """
    Tillämpar anpassad kvot, t.ex. 60/40 mellan Robin och Partner.
    
    Sparar en anpassad fördelningskvot i YAML-konfigurationen
    som kan användas för framtida fördelningar.
    
    Args:
        ratio: Dictionary med fördelningskvoter per person (ska summera till 1.0)
    """
    pass


def calculate_shared_vs_individual(expenses: pd.DataFrame) -> Dict:
    """
    Separerar gemensamma och individuella utgifter.
    
    Analyserar utgifter och klassificerar dem som antingen gemensamma
    (ska delas) eller individuella (belastar bara en person).
    
    Args:
        expenses: DataFrame med utgiftsdata och kategorier
        
    Returns:
        Dictionary med separerade gemensamma och individuella utgifter
    """
    pass
