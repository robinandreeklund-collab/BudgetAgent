"""
Modul för extrahering och strukturering av transaktioner från rådata.

Denna modul bearbetar råa banktransaktioner och konverterar dem till ett
strukturerat format. Den hanterar datumkonvertering, textbearbetning och
extrahering av metadata som butik, kategori och plats.
"""

import pandas as pd
from typing import List
from .models import Transaction
from pathlib import Path
import yaml


def parse_dates(data: pd.DataFrame) -> pd.DataFrame:
    """
    Konverterar datum till ISO-format.
    
    Parsar olika datumformat från olika banker och standardiserar
    till ISO 8601-format (YYYY-MM-DD).
    
    Args:
        data: DataFrame med transaktionsdata
        
    Returns:
        DataFrame med standardiserade datum
    """
    df = data.copy()
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    return df


def clean_descriptions(data: pd.DataFrame) -> pd.DataFrame:
    """
    Tar bort onödig text, symboler, bankkoder.
    
    Rensar transaktionsbeskrivningar från tekniska koder, extra mellanslag
    och andra störande element för att göra dem mer läsbara.
    
    Args:
        data: DataFrame med transaktionsdata
        
    Returns:
        DataFrame med rensade beskrivningar
    """
    import re
    
    df = data.copy()
    
    if 'description' in df.columns:
        # Trimma extra mellanslag
        df['description'] = df['description'].str.strip()
        
        # Ta bort multipla mellanslag
        df['description'] = df['description'].str.replace(r'\s+', ' ', regex=True)
        
        # Ta bort vanliga bankkoder (t.ex. *XXXX XXXX)
        df['description'] = df['description'].str.replace(r'\*\d{4}\s+\d{4}', '', regex=True)
        
        # Ta bort referensnummer (mönster som REF:12345)
        df['description'] = df['description'].str.replace(r'REF:\d+', '', regex=True)
        
        # Trimma igen efter rensning
        df['description'] = df['description'].str.strip()
    
    return df


def extract_metadata(data: pd.DataFrame) -> pd.DataFrame:
    """
    Identifierar butik, kategori, plats via regex/heuristik.
    
    Använder mönsterigenkänning och heuristiska regler för att extrahera
    strukturerad metadata från transaktionsbeskrivningar.
    
    Args:
        data: DataFrame med transaktionsdata
        
    Returns:
        DataFrame med extraherad metadata i nya kolumner
    """
    import re
    
    df = data.copy()
    
    # Initiera metadata-kolumner
    df['store'] = None
    df['location'] = None
    
    if 'description' in df.columns:
        for idx, row in df.iterrows():
            desc = str(row['description'])
            
            # Extrahera butiksnamn (vanligtvis början av beskrivningen)
            # Format: "ICA Maxi Linköping" eller "Circle K Bensin"
            parts = desc.split()
            if len(parts) >= 2:
                # Ta första 2-3 ord som butiksnamn
                store_name = ' '.join(parts[:2])
                df.at[idx, 'store'] = store_name
                
                # Resten kan vara plats
                if len(parts) > 2:
                    location = ' '.join(parts[2:])
                    df.at[idx, 'location'] = location
            elif len(parts) == 1:
                df.at[idx, 'store'] = parts[0]
    
    return df


def save_transactions(transactions: List[Transaction], append: bool = True) -> None:
    """
    Sparar transaktioner till CSV-fil.
    
    Lagrar importerade transaktioner i en CSV-fil för senare användning
    i prognoser och analyser.
    
    Args:
        transactions: Lista med Transaction-objekt att spara
        append: Om True, lägg till i befintlig fil. Om False, skriv över.
    """
    if not transactions:
        return
    
    # Bestäm sökväg till transaktionsfil
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    transactions_file = data_dir / "transactions.csv"
    
    # Konvertera transaktioner till DataFrame
    data = []
    for trans in transactions:
        data.append({
            'date': str(trans.date),
            'amount': float(trans.amount),
            'description': trans.description,
            'category': trans.category,
            'currency': trans.currency
        })
    
    new_df = pd.DataFrame(data)
    
    # Lägg till eller skriv över
    if append and transactions_file.exists():
        # Läs befintliga transaktioner
        existing_df = pd.read_csv(transactions_file)
        # Kombinera och ta bort dubbletter
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        # Ta bort dubbletter baserat på datum, belopp och beskrivning
        combined_df = combined_df.drop_duplicates(subset=['date', 'amount', 'description'], keep='first')
        combined_df.to_csv(transactions_file, index=False)
    else:
        new_df.to_csv(transactions_file, index=False)


def load_transactions() -> List[Transaction]:
    """
    Läser sparade transaktioner från CSV-fil.
    
    Returns:
        Lista med Transaction-objekt
    """
    from datetime import datetime
    from decimal import Decimal
    
    data_dir = Path(__file__).parent.parent / "data"
    transactions_file = data_dir / "transactions.csv"
    
    if not transactions_file.exists():
        return []
    
    df = pd.read_csv(transactions_file)
    transactions = []
    
    for _, row in df.iterrows():
        try:
            trans = Transaction(
                date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                amount=Decimal(str(row['amount'])),
                description=str(row['description']),
                category=str(row['category']) if pd.notna(row.get('category')) else None,
                currency=str(row['currency']) if pd.notna(row.get('currency')) else 'SEK'
            )
            transactions.append(trans)
        except Exception as e:
            print(f"Kunde inte läsa transaktion: {e}")
            continue
    
    return transactions
