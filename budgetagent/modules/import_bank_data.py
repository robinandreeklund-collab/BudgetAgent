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
        # Försök först med komma-separator, sedan tab
        # Hantera olika encodings (Nordea kan använda UTF-8 med BOM eller Windows-1252)
        try:
            # Försök UTF-8 först (med BOM-hantering)
            df = pd.read_csv(path, encoding='utf-8-sig')
            # Om endast en kolumn hittas, försök med tab som separator
            if len(df.columns) == 1:
                df = pd.read_csv(path, sep='\t', encoding='utf-8-sig')
            return df
        except (UnicodeDecodeError, Exception) as e1:
            # Försök med Windows-1252 (vanlig för svenska banker)
            try:
                df = pd.read_csv(path, encoding='windows-1252')
                if len(df.columns) == 1:
                    df = pd.read_csv(path, sep='\t', encoding='windows-1252')
                return df
            except Exception as e2:
                # Försök med tab-separator direkt
                try:
                    return pd.read_csv(path, sep='\t', encoding='utf-8-sig')
                except:
                    raise ValueError(f"Kunde inte läsa CSV-fil. Försökte UTF-8 och Windows-1252. Fel: {str(e1)}")
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
    # Nordea använder ofta "Bokföringsdatum" eller "Bokföringsdag" och antingen "Rubrik", "Namn" eller både "Avsändare" och "Mottagare"
    # Kan även ha "Saldo"-kolumn (till skillnad från SEB som alltid har Saldo)
    if ('bokföringsdatum' in columns or 'bokföringsdag' in columns) and 'belopp' in columns:
        # Kontrollera om det är Nordea (har Rubrik, Namn eller Avsändare/Mottagare)
        if 'rubrik' in columns or 'namn' in columns or ('avsändare' in columns or 'mottagare' in columns):
            # Nordea kan ha Saldo, men SEB har alltid Saldo + specifik struktur
            # Om både Saldo och typiska SEB-kolumner finns, är det SEB
            if not ('saldo' in columns and 'valutadatum' not in columns and 'rubrik' not in columns):
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
        # Nordea kan ha olika kolumnformat
        # Format 1: Bokföringsdatum, Belopp, Rubrik, Valuta
        # Format 2: Bokföringsdag, Belopp, Avsändare, Mottagare, Namn, Rubrik, Saldo, Valuta
        # där Namn = beskrivning, Saldo = valuta, Rubrik = saldo-belopp
        
        column_mapping = {}
        
        # Datum-kolumn
        if 'Bokföringsdatum' in df.columns:
            column_mapping['Bokföringsdatum'] = 'date'
        elif 'Bokföringsdag' in df.columns:
            column_mapping['Bokföringsdag'] = 'date'
        
        # Belopp
        column_mapping['Belopp'] = 'amount'
        
        # Beskrivning - Nordea har olika varianter
        if 'Namn' in df.columns:
            # Format med Namn-kolumn (det är den riktiga beskrivningen)
            column_mapping['Namn'] = 'description'
        elif 'Rubrik' in df.columns:
            column_mapping['Rubrik'] = 'description'
        elif 'Avsändare' in df.columns:
            column_mapping['Avsändare'] = 'description'
        elif 'Mottagare' in df.columns:
            column_mapping['Mottagare'] = 'description'
        
        # Valuta - Nordea kan ha Valuta eller Saldo som valuta-kolumn
        if 'Saldo' in df.columns and 'Valuta' in df.columns:
            # Kontrollera om Valuta-kolumnen är tom (NaN)
            if df['Valuta'].isna().all():
                # Använd Saldo-kolumnen istället
                column_mapping['Saldo'] = 'currency'
            else:
                column_mapping['Valuta'] = 'currency'
        elif 'Valuta' in df.columns:
            column_mapping['Valuta'] = 'currency'
        elif 'Saldo' in df.columns:
            column_mapping['Saldo'] = 'currency'
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
    
    # Filtrera bort tomma rader (alla värden är NaN)
    normalized_data = normalized_data.dropna(how='all')
    
    # Steg 4: Konvertera till Transaction-objekt
    transactions = []
    for idx, row in normalized_data.iterrows():
        try:
            # Hoppa över rader där datum saknas eller är ogiltigt
            if pd.isna(row['date']) or str(row['date']).strip() == '':
                continue
            
            # Parsa datum
            date_val = pd.to_datetime(row['date']).date()
            
            # Konvertera belopp till Decimal (hantera komma som decimaltecken)
            if pd.isna(row['amount']):
                continue
            amount_str = str(row['amount']).replace(',', '.')
            amount_val = Decimal(amount_str)
            
            # Beskrivning
            description = str(row['description']) if not pd.isna(row['description']) else ''
            if description.strip() == '' or description.lower() == 'nan':
                description = 'Transaktion'
            
            # Valuta
            currency = row.get('currency', 'SEK')
            if pd.isna(currency) or str(currency).strip() == '':
                currency = 'SEK'
            
            transaction = Transaction(
                date=date_val,
                amount=amount_val,
                description=description.strip(),
                currency=str(currency)
            )
            transactions.append(transaction)
        except Exception as e:
            # Hoppa över transaktioner som inte kan parsas
            print(f"Kunde inte parsa transaktion på rad {idx}: {e}")
            continue
    
    return transactions
