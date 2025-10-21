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
        # Försök olika separatorer och encodings
        # Nordea kan använda komma, tab eller semikolon som separator
        # Encodings: UTF-8 med BOM eller Windows-1252
        
        # Lista över kombinationer att testa
        attempts = [
            {'sep': ';', 'encoding': 'utf-8-sig'},    # Semikolon (vanlig för svenska Nordea)
            {'sep': '\t', 'encoding': 'utf-8-sig'},   # Tab
            {'sep': ',', 'encoding': 'utf-8-sig'},    # Komma
            {'sep': None, 'encoding': 'utf-8-sig', 'engine': 'python'},  # Auto-detect med python engine
            {'sep': ';', 'encoding': 'windows-1252'}, # Semikolon med Windows-1252
            {'sep': '\t', 'encoding': 'windows-1252'}, # Tab med Windows-1252
        ]
        
        last_error = None
        for attempt in attempts:
            try:
                df = pd.read_csv(path, **attempt)
                # Kontrollera att vi fick flera kolumner (inte bara en kolumn med fel separator)
                if len(df.columns) > 1:
                    return df
            except Exception as e:
                last_error = e
                continue
        
        # Om inget fungerade, ge ett informativt felmeddelande
        raise ValueError(f"Kunde inte läsa CSV-fil med någon separator (komma, tab, semikolon). Senaste fel: {str(last_error)}")
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
        # Prioritera Rubrik om den finns och inte är tom, annars Namn
        if 'Rubrik' in df.columns and not df['Rubrik'].isna().all():
            column_mapping['Rubrik'] = 'description'
        elif 'Namn' in df.columns and not df['Namn'].isna().all():
            # Format med Namn-kolumn (det är den riktiga beskrivningen)
            column_mapping['Namn'] = 'description'
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


def extract_balance_info(raw_data: pd.DataFrame, bank_format: str) -> Optional[tuple]:
    """
    Extraherar saldoinformation från bankdata.
    
    Letar efter saldo-kolumn i bankunderlaget och extraherar det senaste saldot
    samt datum för detta saldo.
    
    Args:
        raw_data: DataFrame med rådata
        bank_format: Bankformat identifierat av detect_format()
        
    Returns:
        Tuple (balance, balance_date, currency) eller None om inget saldo hittas
    """
    from decimal import Decimal
    
    balance = None
    balance_date = None
    currency = "SEK"
    
    # Olika banker har olika sätt att visa saldo
    if bank_format == "Nordea":
        # Nordea har flera olika format
        # Format 1: Traditionellt med Saldo-kolumn för saldovärden
        # Format 2: Där "Saldo" = valuta och "Rubrik" = saldo-belopp
        
        # Först, försök hitta datum
        if 'Bokföringsdatum' in raw_data.columns:
            date_col = raw_data['Bokföringsdatum'].dropna()
            if not date_col.empty:
                balance_date = pd.to_datetime(date_col.iloc[-1]).date()
        elif 'Bokföringsdag' in raw_data.columns:
            date_col = raw_data['Bokföringsdag'].dropna()
            if not date_col.empty:
                balance_date = pd.to_datetime(date_col.iloc[-1]).date()
        
        # Försök extrahera saldo
        # Fall 1: Saldo är valuta och Rubrik är saldo-beloppet
        if 'Saldo' in raw_data.columns and 'Rubrik' in raw_data.columns and 'Valuta' in raw_data.columns:
            # Kontrollera om Saldo-kolumnen innehåller valuta-värden (SEK, EUR etc)
            saldo_sample = raw_data['Saldo'].dropna()
            if not saldo_sample.empty:
                first_val = str(saldo_sample.iloc[0]).strip().upper()
                if first_val in ['SEK', 'EUR', 'USD', 'NOK', 'DKK']:
                    # Detta är formatet där Saldo=valuta och Rubrik=saldo-belopp
                    rubrik_col = raw_data['Rubrik']
                    if not rubrik_col.isna().all():
                        balance_val = rubrik_col.dropna().iloc[-1]
                        try:
                            balance = Decimal(str(balance_val).replace(',', '.').replace(' ', ''))
                        except:
                            pass
                    currency = first_val
                else:
                    # Saldo innehåller numeriska värden
                    balance_val = saldo_sample.iloc[-1]
                    try:
                        balance = Decimal(str(balance_val).replace(',', '.').replace(' ', ''))
                    except:
                        pass
                    # Hämta valuta från Valuta-kolumnen
                    if not raw_data['Valuta'].isna().all():
                        currency = raw_data['Valuta'].dropna().iloc[0]
        
        # Fall 2: Saldo är en vanlig kolumn med saldovärden
        elif 'Saldo' in raw_data.columns:
            saldo_col = raw_data['Saldo']
            if not saldo_col.isna().all():
                balance_val = saldo_col.dropna().iloc[-1]
                try:
                    # Testa om det är ett numeriskt värde
                    balance = Decimal(str(balance_val).replace(',', '.').replace(' ', ''))
                except:
                    pass
            
            # Hämta valuta
            if 'Valuta' in raw_data.columns and not raw_data['Valuta'].isna().all():
                currency = raw_data['Valuta'].dropna().iloc[0]
        
        # Fall 3: Ingen Saldo-kolumn, försök hitta i annan kolumn
        # Vissa Nordea-format kan ha saldo i en kolumn som heter något annat
        # Kontrollera kolumner med numeriska värden som inte är Belopp
        if balance is None:
            for col in raw_data.columns:
                if col not in ['Belopp', 'Bokföringsdatum', 'Bokföringsdag', 'Rubrik', 'Namn', 
                              'Avsändare', 'Mottagare', 'Valuta']:
                    # Testa om denna kolumn innehåller numeriska värden
                    try:
                        test_col = raw_data[col].dropna()
                        if not test_col.empty:
                            last_val = test_col.iloc[-1]
                            # Försök konvertera till Decimal
                            balance = Decimal(str(last_val).replace(',', '.').replace(' ', ''))
                            break
                    except:
                        continue
    
    elif bank_format == "SEB":
        # SEB har alltid Saldo-kolumn
        if 'Saldo' in raw_data.columns:
            saldo_col = raw_data['Saldo']
            if not saldo_col.isna().all():
                balance_val = saldo_col.dropna().iloc[-1]
                try:
                    balance = Decimal(str(balance_val).replace(',', '.').replace(' ', ''))
                except:
                    pass
        
        if 'Bokföringsdatum' in raw_data.columns:
            date_col = raw_data['Bokföringsdatum'].dropna()
            if not date_col.empty:
                balance_date = pd.to_datetime(date_col.iloc[-1]).date()
        
        if 'Valuta' in raw_data.columns and not raw_data['Valuta'].isna().all():
            currency = raw_data['Valuta'].dropna().iloc[0]
    
    if balance is not None and balance_date is not None:
        return (balance, balance_date, currency)
    
    return None


def import_and_parse(file_path: str, check_duplicates: bool = True) -> List[Transaction]:
    """
    Importerar och konverterar bankdata till Transaction-objekt.
    
    Huvudfunktion som kombinerar filimport, formatdetektering och
    konvertering till standardiserade Transaction-objekt. Inkluderar
    automatisk kontohantering och dupliceringsskydd.
    
    Args:
        file_path: Sökväg till filen att importera
        check_duplicates: Om True, kontrollera och filtrera bort dubbletter
        
    Returns:
        Lista med Transaction-objekt (endast nya transaktioner om check_duplicates=True)
    """
    from datetime import datetime
    from decimal import Decimal
    from . import account_manager
    
    # Steg 1: Extrahera kontonamn från filnamn
    account_name = account_manager.extract_account_from_filename(file_path)
    
    # Steg 2: Kontrollera om filen redan har importerats
    if check_duplicates and account_manager.is_file_imported(account_name, file_path):
        print(f"Fil {file_path} har redan importerats för konto {account_name}")
        return []
    
    # Steg 3: Ladda fil
    raw_data = load_file(file_path)
    
    # Steg 4: Detektera format
    bank_format = detect_format(raw_data)
    
    # Steg 4.5: Extrahera saldoinformation innan normalisering
    balance_info = extract_balance_info(raw_data, bank_format)
    
    # Steg 5: Normalisera kolumner
    normalized_data = normalize_columns(raw_data, bank_format)
    
    # Filtrera bort tomma rader (alla värden är NaN)
    normalized_data = normalized_data.dropna(how='all')
    
    # Steg 6: Konvertera till Transaction-objekt
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
    
    # Steg 7: Filtrera bort dubbletter av transaktioner
    if check_duplicates:
        new_transactions, duplicates = account_manager.filter_duplicate_transactions(
            account_name, transactions
        )
        
        if duplicates:
            print(f"Hittade {len(duplicates)} dubbletter som filtrerades bort")
        
        # Registrera de nya transaktionerna
        if new_transactions:
            account_manager.register_transactions(account_name, new_transactions)
        
        # Uppdatera saldoinformation om tillgänglig
        if balance_info:
            balance, balance_date, currency = balance_info
            account_manager.update_account_balance(account_name, balance, balance_date, currency)
        
        # Markera filen som importerad
        account_manager.add_imported_file(account_name, file_path)
        
        return new_transactions
    
    return transactions
