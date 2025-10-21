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
    import yaml
    from pathlib import Path
    from decimal import Decimal
    
    # Beräkna total inkomst och utgifter
    total_in = sum(Decimal(str(v)) for v in total_income.values())
    total_exp = sum(Decimal(str(v)) for v in total_expenses.values())
    remaining = total_in - total_exp
    
    # Hämta personer
    people = set(list(total_income.keys()) + list(total_expenses.keys()))
    
    distribution = {}
    
    if rule == "equal_split":
        # Dela lika mellan alla personer
        per_person = remaining / len(people) if people else Decimal(0)
        for person in people:
            distribution[person] = float(per_person)
    
    elif rule == "income_weighted":
        # Dela baserat på inkomstandel
        if total_in > 0:
            for person in people:
                person_income = Decimal(str(total_income.get(person, 0)))
                income_ratio = person_income / total_in
                distribution[person] = float(remaining * income_ratio)
        else:
            # Fallback till lika fördelning
            per_person = remaining / len(people) if people else Decimal(0)
            for person in people:
                distribution[person] = float(per_person)
    
    elif rule == "custom_ratio":
        # Använd anpassad kvot från YAML
        config_path = Path(__file__).parent.parent / "config" / "net_balance_splitter.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            if 'net_balance_splitter' in config and 'custom_ratio' in config['net_balance_splitter']:
                ratios = config['net_balance_splitter']['custom_ratio']
                for person in people:
                    ratio = Decimal(str(ratios.get(person, 0)))
                    distribution[person] = float(remaining * ratio)
            else:
                # Fallback
                per_person = remaining / len(people) if people else Decimal(0)
                for person in people:
                    distribution[person] = float(per_person)
        else:
            # Fallback
            per_person = remaining / len(people) if people else Decimal(0)
            for person in people:
                distribution[person] = float(per_person)
    
    elif rule == "needs_based":
        # Behovsbaserad fördelning (förenklad: efter utgifter)
        if total_exp > 0:
            for person in people:
                person_expenses = Decimal(str(total_expenses.get(person, 0)))
                expense_ratio = person_expenses / total_exp
                distribution[person] = float(remaining * expense_ratio)
        else:
            # Fallback
            per_person = remaining / len(people) if people else Decimal(0)
            for person in people:
                distribution[person] = float(per_person)
    
    else:
        # Default: lika fördelning
        per_person = remaining / len(people) if people else Decimal(0)
        for person in people:
            distribution[person] = float(per_person)
    
    return distribution


def apply_custom_ratio(ratio: Dict) -> None:
    """
    Tillämpar anpassad kvot, t.ex. 60/40 mellan Robin och Partner.
    
    Sparar en anpassad fördelningskvot i YAML-konfigurationen
    som kan användas för framtida fördelningar.
    
    Args:
        ratio: Dictionary med fördelningskvoter per person (ska summera till 1.0)
    """
    import yaml
    from pathlib import Path
    
    # Validera att summan är 1.0
    total_ratio = sum(ratio.values())
    if abs(total_ratio - 1.0) > 0.01:
        raise ValueError(f"Summan av kvoter måste vara 1.0, fick {total_ratio}")
    
    config_path = Path(__file__).parent.parent / "config" / "net_balance_splitter.yaml"
    
    # Ladda befintlig konfiguration
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Uppdatera custom_ratio
    if 'net_balance_splitter' not in config:
        config['net_balance_splitter'] = {}
    
    config['net_balance_splitter']['custom_ratio'] = ratio
    
    # Spara tillbaka
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


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
    import yaml
    from pathlib import Path
    
    if expenses.empty or 'category' not in expenses.columns or 'amount' not in expenses.columns:
        return {'shared': 0.0, 'individual': 0.0}
    
    # Ladda konfiguration för gemensamma kategorier
    config_path = Path(__file__).parent.parent / "config" / "net_balance_splitter.yaml"
    shared_categories = ["Boende", "Mat", "Hem"]  # Default
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        if 'net_balance_splitter' in config and 'shared_expense_categories' in config['net_balance_splitter']:
            shared_categories = config['net_balance_splitter']['shared_expense_categories']
    
    # Konvertera till absoluta värden
    expenses_copy = expenses.copy()
    expenses_copy['abs_amount'] = expenses_copy['amount'].abs()
    
    # Klassificera utgifter
    shared_mask = expenses_copy['category'].isin(shared_categories)
    shared_total = expenses_copy[shared_mask]['abs_amount'].sum()
    individual_total = expenses_copy[~shared_mask]['abs_amount'].sum()
    
    return {
        'shared': float(shared_total),
        'individual': float(individual_total),
        'shared_categories': shared_categories,
        'breakdown': {
            'shared_by_category': expenses_copy[shared_mask].groupby('category')['abs_amount'].sum().to_dict(),
            'individual_by_category': expenses_copy[~shared_mask].groupby('category')['abs_amount'].sum().to_dict()
        }
    }
