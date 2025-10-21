"""
Modul för import av bankutdrag från olika format (CSV, Excel, JSON).

Denna modul hanterar inläsning och normalisering av banktransaktioner från olika
svenska banker som Swedbank, SEB, Revolut och andra. Modulen identifierar automatiskt
bankformatet och standardiserar kolumnnamn för enhetlig vidare bearbetning.

Exempel på YAML-konfiguration (settings_panel.yaml):
    settings_panel:
      import_format:
        type: dropdown
        options: ["Swedbank CSV", "SEB Excel", "Revolut JSON"]
"""

import pandas as pd
from typing import Optional, List
from .models import Transaction


def load_file(path: str) -> pd.DataFrame:
    """
    Läser in filen och returnerar rådata.
    
    Args:
        path: Sökväg till filen som ska läsas in
        
    Returns:
        DataFrame med rådata från filen
    """
    from pathlib import Path
    
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Filen {path} hittades inte")
    
    suffix = file_path.suffix.lower()
    
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    elif suffix == '.json':
        return pd.read_json(path)
    else:
        raise ValueError(f"Filformat {suffix} stöds inte. Använd CSV, Excel eller JSON.")


def detect_format(data: pd.DataFrame) -> str:
    """
    Identifierar bankformat (Swedbank, SEB, Revolut, Nordea etc.).
    
    Analyserar strukturen och innehållet i DataFrame för att identifiera
    vilken bank som har skapat utdraget.
    
    Args:
        data: DataFrame med rådata
        
    Returns:
        Sträng med banknamn, t.ex. "Swedbank", "SEB", "Revolut", "Nordea"
    """
    if data.empty:
        return "Unknown"
    
    columns = [col.lower() for col in data.columns]
    
    # Nordea format: Bokföringsdatum, Belopp, och ofta Rubrik eller Avsändare/Mottagare
    # Nordea använder ofta "Bokföringsdatum" och antingen "Rubrik" eller både "Avsändare" och "Mottagare"
    if 'bokföringsdatum' in columns and 'belopp' in columns:
        # Kontrollera om det är Nordea (har Rubrik eller Avsändare/Mottagare)
        if 'rubrik' in columns or ('avsändare' in columns or 'mottagare' in columns):
            # Men inte SEB som också har Bokföringsdatum
            if 'saldo' not in columns:
                return "Nordea"
    
    # Swedbank format: Datum, Belopp, Beskrivning
    if 'datum' in columns and 'belopp' in columns and 'beskrivning' in columns:
        return "Swedbank"
    
    # SEB format: Bokföringsdatum, Valuta, Belopp, Saldo
    if 'bokföringsdatum' in columns and 'saldo' in columns:
        return "SEB"
    
    # Revolut format: Completed Date, Description, Amount, Currency
    if 'completed date' in columns or ('description' in columns and 'amount' in columns and 'currency' in columns):
        return "Revolut"
    
    # Generic format med standardkolumner
    if any(col in columns for col in ['date', 'datum']) and \
       any(col in columns for col in ['amount', 'belopp']):
        return "Generic"
    
    return "Unknown"


def normalize_columns(data: pd.DataFrame, format: str) -> pd.DataFrame:
    """
    Standardiserar kolumnnamn till date, amount, description, currency.
    
    Konverterar bankspecifika kolumnnamn till standardiserade namn för
    enhetlig bearbetning i resten av systemet.
    
    Args:
        data: DataFrame med rådata
        format: Bankformat identifierat av detect_format()
        
    Returns:
        DataFrame med standardiserade kolumnnamn
    """
    df = data.copy()
    
    # Mapping av kolumnnamn baserat på format
    if format == "Nordea":
        column_mapping = {
            'Bokföringsdatum': 'date',
            'Belopp': 'amount',
            'Rubrik': 'description',
            'Valuta': 'currency'
        }
        # Nordea kan ha "Avsändare" eller "Mottagare" som beskrivning
        if 'Rubrik' not in df.columns and 'Avsändare' in df.columns:
            column_mapping['Avsändare'] = 'description'
        elif 'Rubrik' not in df.columns and 'Mottagare' in df.columns:
            column_mapping['Mottagare'] = 'description'
    elif format == "Swedbank":
        column_mapping = {
            'Datum': 'date',
            'Belopp': 'amount',
            'Beskrivning': 'description',
            'Valuta': 'currency'
        }
    elif format == "SEB":
        column_mapping = {
            'Bokföringsdatum': 'date',
            'Belopp': 'amount',
            'Mottagare': 'description',
            'Valuta': 'currency'
        }
    elif format == "Revolut":
        column_mapping = {
            'Completed Date': 'date',
            'Amount': 'amount',
            'Description': 'description',
            'Currency': 'currency'
        }
    elif format == "Generic":
        # Försök hitta kolumner med liknande namn
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['date', 'datum']:
                column_mapping[col] = 'date'
            elif col_lower in ['amount', 'belopp']:
                column_mapping[col] = 'amount'
            elif col_lower in ['description', 'beskrivning', 'rubrik']:
                column_mapping[col] = 'description'
            elif col_lower in ['currency', 'valuta']:
                column_mapping[col] = 'currency'
    else:
        return df
    
    # Byt namn på kolumnerna
    df = df.rename(columns=column_mapping)
    
    # Säkerställ att valuta finns om den saknas
    if 'currency' not in df.columns:
        df['currency'] = 'SEK'
    
    # Välj endast standardkolumner som finns
    available_cols = [col for col in ['date', 'amount', 'description', 'currency'] if col in df.columns]
    return df[available_cols]


def import_and_parse(file_path: str) -> List[Transaction]:
    """
    Importerar och konverterar bankdata till Transaction-objekt.
    
    Huvudfunktion som kombinerar filimport, formatdetektering och
    konvertering till standardiserade Transaction-objekt.
    
    Args:
        file_path: Sökväg till filen att importera
        
    Returns:
        Lista med Transaction-objekt
    """
    from datetime import datetime
    from decimal import Decimal
    
    # Steg 1: Ladda fil
    raw_data = load_file(file_path)
    
    # Steg 2: Detektera format
    bank_format = detect_format(raw_data)
    
    # Steg 3: Normalisera kolumner
    normalized_data = normalize_columns(raw_data, bank_format)
    
    # Steg 4: Konvertera till Transaction-objekt
    transactions = []
    for _, row in normalized_data.iterrows():
        try:
            # Parsa datum
            date_val = pd.to_datetime(row['date']).date()
            
            # Konvertera belopp till Decimal
            amount_val = Decimal(str(row['amount']))
            
            # Beskrivning
            description = str(row['description'])
            
            # Valuta
            currency = row.get('currency', 'SEK')
            
            transaction = Transaction(
                date=date_val,
                amount=amount_val,
                description=description,
                currency=currency
            )
            transactions.append(transaction)
        except Exception as e:
            # Hoppa över transaktioner som inte kan parsas
            print(f"Kunde inte parsa transaktion: {e}")
            continue
    
    return transactions
