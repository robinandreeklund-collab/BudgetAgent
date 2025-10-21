"""
Modul för hantering av framtida fakturor med belopp, förfallodatum och kategori.

Denna modul hanterar registrering och spårning av kommande fakturor
och betalningar. Den använder YAML för persistent lagring av fakturor.

Exempel på YAML-konfiguration (upcoming_bills.yaml):
    upcoming_bills:
      bills:
        - name: "Elräkning"
          amount: 900
          due_date: "2025-11-30"
          category: "Boende"
        - name: "Internet"
          amount: 399
          due_date: "2025-11-15"
          category: "Boende"
"""

from typing import List, Dict
from .models import Bill


def add_bill(bill: Bill) -> None:
    """
    Lägger till ny faktura i YAML.
    
    Registrerar en ny kommande faktura med alla nödvändiga detaljer
    och sparar den i YAML-konfigurationsfilen.
    
    Args:
        bill: Bill-objekt med fakturainformation
    """
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    # Ladda befintliga fakturor
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    
    if 'upcoming_bills' not in data:
        data['upcoming_bills'] = {'bills': []}
    elif 'bills' not in data['upcoming_bills']:
        data['upcoming_bills']['bills'] = []
    
    # Konvertera Bill till dictionary
    bill_dict = {
        'name': bill.name,
        'amount': float(bill.amount),
        'due_date': bill.due_date.isoformat(),
        'category': bill.category,
        'account': bill.account,
        'recurring': bill.recurring,
        'frequency': bill.frequency,
        'paid': bill.paid
    }
    
    if bill.payment_date:
        bill_dict['payment_date'] = bill.payment_date.isoformat()
    
    # Lägg till fakturan om den inte redan finns (baserat på name, amount, due_date)
    duplicate = any(
        b.get('name') == bill_dict['name'] and
        float(b.get('amount', 0)) == bill_dict['amount'] and
        b.get('due_date') == bill_dict['due_date']
        for b in data['upcoming_bills']['bills']
    )
    if not duplicate:
        data['upcoming_bills']['bills'].append(bill_dict)
    
    # Spara tillbaka
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def get_upcoming_bills(month: str) -> List[Bill]:
    """
    Returnerar alla fakturor för vald månad.
    
    Hämtar och filtrerar fakturor som förfaller under den angivna månaden.
    
    Args:
        month: Månad i format YYYY-MM
        
    Returns:
        Lista med Bill-objekt
    """
    import yaml
    from pathlib import Path
    from datetime import datetime
    from decimal import Decimal
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'upcoming_bills' not in data or 'bills' not in data['upcoming_bills']:
        return []
    
    bills = []
    for bill_dict in data['upcoming_bills']['bills']:
        try:
            # Parsa due_date
            due_date = datetime.fromisoformat(bill_dict['due_date']).date()
            
            # Filtrera på månad om specificerat
            if month:
                bill_month = due_date.strftime('%Y-%m')
                if bill_month != month:
                    continue
            
            # Konvertera till Bill-objekt
            payment_date = None
            if 'payment_date' in bill_dict and bill_dict['payment_date']:
                payment_date = datetime.fromisoformat(bill_dict['payment_date']).date()
            
            bill = Bill(
                name=bill_dict['name'],
                amount=Decimal(str(bill_dict['amount'])),
                due_date=due_date,
                category=bill_dict['category'],
                account=bill_dict.get('account'),
                recurring=bill_dict.get('recurring', False),
                frequency=bill_dict.get('frequency'),
                paid=bill_dict.get('paid', False),
                payment_date=payment_date
            )
            bills.append(bill)
        except Exception as e:
            print(f"Kunde inte parsa faktura: {e}")
            continue
    
    return bills


def get_all_bills() -> List[Bill]:
    """
    Returnerar alla fakturor oavsett månad.
    
    Returns:
        Lista med alla Bill-objekt
    """
    import yaml
    from pathlib import Path
    from datetime import datetime
    from decimal import Decimal
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'upcoming_bills' not in data or 'bills' not in data['upcoming_bills']:
        return []
    
    bills = []
    for bill_dict in data['upcoming_bills']['bills']:
        try:
            # Parsa due_date
            due_date = datetime.fromisoformat(bill_dict['due_date']).date()
            
            # Konvertera till Bill-objekt
            payment_date = None
            if 'payment_date' in bill_dict and bill_dict['payment_date']:
                payment_date = datetime.fromisoformat(bill_dict['payment_date']).date()
            
            bill = Bill(
                name=bill_dict['name'],
                amount=Decimal(str(bill_dict['amount'])),
                due_date=due_date,
                category=bill_dict['category'],
                account=bill_dict.get('account'),
                recurring=bill_dict.get('recurring', False),
                frequency=bill_dict.get('frequency'),
                paid=bill_dict.get('paid', False),
                payment_date=payment_date
            )
            bills.append(bill)
        except Exception as e:
            print(f"Kunde inte parsa faktura: {e}")
            continue
    
    return bills


def update_bill(old_bill_name: str, old_bill_due_date: str, updated_bill: Bill) -> bool:
    """
    Uppdaterar en befintlig faktura.
    
    Args:
        old_bill_name: Namn på fakturan att uppdatera
        old_bill_due_date: Förfallodatum för fakturan att uppdatera (ISO format)
        updated_bill: Nytt Bill-objekt med uppdaterad information
        
    Returns:
        True om uppdateringen lyckades, False annars
    """
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    if not config_path.exists():
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'upcoming_bills' not in data or 'bills' not in data['upcoming_bills']:
        return False
    
    # Hitta och uppdatera fakturan
    updated = False
    for i, bill_dict in enumerate(data['upcoming_bills']['bills']):
        if bill_dict.get('name') == old_bill_name and bill_dict.get('due_date') == old_bill_due_date:
            # Uppdatera fakturan
            data['upcoming_bills']['bills'][i] = {
                'name': updated_bill.name,
                'amount': float(updated_bill.amount),
                'due_date': updated_bill.due_date.isoformat(),
                'category': updated_bill.category,
                'account': updated_bill.account,
                'recurring': updated_bill.recurring,
                'frequency': updated_bill.frequency,
                'paid': updated_bill.paid
            }
            
            if updated_bill.payment_date:
                data['upcoming_bills']['bills'][i]['payment_date'] = updated_bill.payment_date.isoformat()
            
            updated = True
            break
    
    if updated:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    
    return updated


def delete_bill(bill_name: str, bill_due_date: str) -> bool:
    """
    Tar bort en faktura.
    
    Args:
        bill_name: Namn på fakturan att ta bort
        bill_due_date: Förfallodatum för fakturan (ISO format)
        
    Returns:
        True om borttagningen lyckades, False annars
    """
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "upcoming_bills.yaml"
    
    if not config_path.exists():
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    if 'upcoming_bills' not in data or 'bills' not in data['upcoming_bills']:
        return False
    
    # Filtrera bort fakturan
    original_count = len(data['upcoming_bills']['bills'])
    data['upcoming_bills']['bills'] = [
        bill for bill in data['upcoming_bills']['bills']
        if not (bill.get('name') == bill_name and bill.get('due_date') == bill_due_date)
    ]
    
    deleted = len(data['upcoming_bills']['bills']) < original_count
    
    if deleted:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    
    return deleted


def validate_bill_format(bill: Bill) -> bool:
    """
    Säkerställer korrekt struktur.
    
    Validerar att en faktura har alla nödvändiga fält och
    att de har korrekt format och värden. Pydantic validerar
    automatiskt, men denna funktion kan lägga till extra affärslogik.
    
    Args:
        bill: Bill-objekt att validera
        
    Returns:
        True om fakturastrukturen är korrekt, annars False
    """
    try:
        # Pydantic validerar automatiskt vid skapande
        # Extra affärslogik kan läggas till här
        
        # Kontrollera att namn inte är tomt
        if not bill.name or not bill.name.strip():
            return False
        
        # Kontrollera att belopp är positivt (redan validerat av Pydantic)
        if bill.amount <= 0:
            return False
        
        # Kontrollera att kategori finns
        if not bill.category or not bill.category.strip():
            return False
        
        # Om återkommande, måste frekvens anges
        if bill.recurring and not bill.frequency:
            return False
        
        # Om betald, måste betalningsdatum anges
        if bill.paid and not bill.payment_date:
            return False
        
        return True
    except Exception:
        return False
