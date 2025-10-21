"""
Modul för hantering av bankkonton och dupliceringsskydd.

Denna modul hanterar kontoregistrering baserat på importerade filer,
håller koll på vilka filer som redan importerats, och förhindrar
dubbletter av både filer och transaktioner.

Konton skapas automatiskt baserat på filnamn vid import och alla
importerade filer och transaktioner spåras för att undvika dubblering.
"""

import hashlib
import yaml
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from .models import Account, Transaction


# Global sökväg till konto-databasen
ACCOUNTS_DB_PATH = Path(__file__).parent.parent / "config" / "accounts.yaml"


def extract_account_from_filename(filename: str) -> str:
    """
    Extraherar kontonamn från filnamn.
    
    Tolkar filnamn som "PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv"
    och extraherar kontonamnet (t.ex. "PERSONKONTO 1709 20 72840").
    
    Args:
        filename: Filnamn att extrahera kontonamn från
        
    Returns:
        Extraherat kontonamn eller standardnamn
    """
    # Ta bort sökväg om den finns
    base_filename = Path(filename).name
    
    # Ta bort filändelse
    name_without_ext = base_filename.rsplit('.', 1)[0]
    
    # Försök extrahera kontonamn före datum-timestamp
    # Mönster: "KONTONAMN - YYYY-MM-DD HH.MM.SS" eller liknande
    match = re.match(r'^(.+?)\s*-\s*\d{4}[-/]\d{2}[-/]\d{2}', name_without_ext)
    if match:
        return match.group(1).strip()
    
    # Om inget datum-mönster hittas, försök extrahera kontonummer
    # Mönster: kontonummer med mellanslag eller bindestreck
    account_number_match = re.search(r'\d{4}[\s\-]\d{2}[\s\-]\d{5}', name_without_ext)
    if account_number_match:
        # Returnera text fram till och med kontonumret
        end_pos = account_number_match.end()
        return name_without_ext[:end_pos].strip()
    
    # Om inget specifikt mönster hittas, använd hela filnamnet utan datum
    # Ta bort vanliga datum-format från slutet
    cleaned = re.sub(r'\s*[-_]\s*\d{4}[-/]\d{2}[-/]\d{2}.*$', '', name_without_ext)
    cleaned = re.sub(r'\s*[-_]\s*\d{8}.*$', '', cleaned)
    
    return cleaned.strip() if cleaned else name_without_ext


def calculate_file_checksum(filepath: str) -> str:
    """
    Beräknar MD5-checksumma för en fil.
    
    Används för att identifiera om samma fil har importerats tidigare,
    även om filnamnet har ändrats.
    
    Args:
        filepath: Sökväg till filen
        
    Returns:
        MD5-checksumma som hexadecimal sträng
    """
    md5_hash = hashlib.md5()
    
    with open(filepath, 'rb') as f:
        # Läs filen i chunks för att hantera stora filer
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def calculate_transaction_hash(transaction: Transaction) -> str:
    """
    Beräknar unik hash för en transaktion.
    
    Används för att identifiera om samma transaktion redan har importerats,
    baserat på datum, belopp och beskrivning.
    
    Args:
        transaction: Transaction-objekt
        
    Returns:
        SHA256-hash som hexadecimal sträng
    """
    # Skapa en unik sträng från transaktionens nyckelvärden
    transaction_str = f"{transaction.date}|{transaction.amount}|{transaction.description}|{transaction.currency}"
    
    return hashlib.sha256(transaction_str.encode()).hexdigest()


def load_accounts() -> dict:
    """
    Laddar alla konton från YAML-databasen.
    
    Returns:
        Dictionary med kontonamn som nyckel och Account-objekt som värde
    """
    if not ACCOUNTS_DB_PATH.exists():
        return {}
    
    try:
        with open(ACCOUNTS_DB_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        accounts = {}
        for account_name, account_data in data.get('accounts', {}).items():
            # Konvertera transaction_hashes från lista till set
            if 'transaction_hashes' in account_data:
                account_data['transaction_hashes'] = set(account_data['transaction_hashes'])
            else:
                account_data['transaction_hashes'] = set()
            
            # Konvertera last_import_date från sträng till datetime om det finns
            if 'last_import_date' in account_data and account_data['last_import_date']:
                account_data['last_import_date'] = datetime.fromisoformat(account_data['last_import_date'])
            
            # Konvertera current_balance från float/string till Decimal om det finns
            if 'current_balance' in account_data and account_data['current_balance'] is not None:
                account_data['current_balance'] = Decimal(str(account_data['current_balance']))
            
            # Konvertera balance_date från sträng till date om det finns
            if 'balance_date' in account_data and account_data['balance_date']:
                account_data['balance_date'] = date.fromisoformat(account_data['balance_date'])
            
            accounts[account_name] = Account(**account_data)
        
        return accounts
    except Exception as e:
        print(f"Varning: Kunde inte ladda konton från {ACCOUNTS_DB_PATH}: {e}")
        return {}


def save_accounts(accounts: dict) -> None:
    """
    Sparar alla konton till YAML-databasen.
    
    Args:
        accounts: Dictionary med kontonamn som nyckel och Account-objekt som värde
    """
    # Konvertera Account-objekt till dictionaries för YAML-serialisering
    accounts_data = {}
    for account_name, account in accounts.items():
        account_dict = account.model_dump()
        
        # Konvertera set till lista för YAML-serialisering
        if 'transaction_hashes' in account_dict:
            account_dict['transaction_hashes'] = list(account_dict['transaction_hashes'])
        
        # Konvertera datetime till ISO-format sträng
        if 'last_import_date' in account_dict and account_dict['last_import_date']:
            account_dict['last_import_date'] = account_dict['last_import_date'].isoformat()
        
        # Konvertera Decimal till string för YAML-serialisering
        if 'current_balance' in account_dict and account_dict['current_balance'] is not None:
            account_dict['current_balance'] = str(account_dict['current_balance'])
        
        # Konvertera date till ISO-format sträng
        if 'balance_date' in account_dict and account_dict['balance_date']:
            account_dict['balance_date'] = account_dict['balance_date'].isoformat()
        
        accounts_data[account_name] = account_dict
    
    # Skapa config-katalog om den inte finns
    ACCOUNTS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Spara till YAML
    with open(ACCOUNTS_DB_PATH, 'w', encoding='utf-8') as f:
        yaml.dump({'accounts': accounts_data}, f, allow_unicode=True, default_flow_style=False)


def get_or_create_account(account_name: str, account_number: Optional[str] = None) -> Account:
    """
    Hämtar ett befintligt konto eller skapar ett nytt.
    
    Laddar konton från databasen, returnerar befintligt konto om det finns,
    eller skapar och sparar ett nytt konto.
    
    Args:
        account_name: Namn på kontot
        account_number: Valfritt kontonummer
        
    Returns:
        Account-objekt
    """
    accounts = load_accounts()
    
    if account_name in accounts:
        return accounts[account_name]
    
    # Skapa nytt konto
    new_account = Account(
        account_name=account_name,
        account_number=account_number,
        imported_files=[],
        transaction_hashes=set()
    )
    
    # Spara det nya kontot
    accounts[account_name] = new_account
    save_accounts(accounts)
    
    return new_account


def is_file_imported(account_name: str, filepath: str) -> bool:
    """
    Kontrollerar om en fil redan har importerats för ett konto.
    
    Använder både filnamn och checksumma för att identifiera om filen
    redan har importerats tidigare.
    
    Args:
        account_name: Namn på kontot
        filepath: Sökväg till filen
        
    Returns:
        True om filen redan är importerad, annars False
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        return False
    
    account = accounts[account_name]
    filename = Path(filepath).name
    
    # Kontrollera om filnamnet finns
    for imported_file in account.imported_files:
        if imported_file.get('filename') == filename:
            return True
    
    # Kontrollera checksumma
    try:
        checksum = calculate_file_checksum(filepath)
        for imported_file in account.imported_files:
            if imported_file.get('checksum') == checksum:
                return True
    except Exception:
        # Om checksumman inte kan beräknas, fortsätt ändå
        pass
    
    return False


def add_imported_file(account_name: str, filepath: str) -> None:
    """
    Registrerar en importerad fil för ett konto.
    
    Lägger till filnamn och checksumma i kontots lista över importerade filer
    och uppdaterar senaste importdatum.
    
    Args:
        account_name: Namn på kontot
        filepath: Sökväg till filen
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        accounts[account_name] = get_or_create_account(account_name)
    
    account = accounts[account_name]
    filename = Path(filepath).name
    
    # Beräkna checksumma
    try:
        checksum = calculate_file_checksum(filepath)
    except Exception as e:
        print(f"Varning: Kunde inte beräkna checksumma för {filepath}: {e}")
        checksum = "unknown"
    
    # Lägg till fil-information
    file_info = {
        'filename': filename,
        'checksum': checksum,
        'import_date': datetime.now().isoformat()
    }
    account.imported_files.append(file_info)
    account.last_import_date = datetime.now()
    
    # Spara uppdaterat konto
    accounts[account_name] = account
    save_accounts(accounts)


def is_transaction_duplicate(account_name: str, transaction: Transaction) -> bool:
    """
    Kontrollerar om en transaktion redan har importerats för ett konto.
    
    Använder transaktionens hash (baserad på datum, belopp, beskrivning)
    för att identifiera dubbletter.
    
    Args:
        account_name: Namn på kontot
        transaction: Transaction-objekt att kontrollera
        
    Returns:
        True om transaktionen redan finns, annars False
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        return False
    
    account = accounts[account_name]
    transaction_hash = calculate_transaction_hash(transaction)
    
    return transaction_hash in account.transaction_hashes


def add_transaction(account_name: str, transaction: Transaction) -> None:
    """
    Registrerar en transaktion för ett konto.
    
    Lägger till transaktionens hash i kontots set av transaktioner
    för framtida dupliceringsskydd.
    
    Args:
        account_name: Namn på kontot
        transaction: Transaction-objekt att registrera
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        accounts[account_name] = get_or_create_account(account_name)
    
    account = accounts[account_name]
    transaction_hash = calculate_transaction_hash(transaction)
    
    # Lägg till transaktions-hash
    account.transaction_hashes.add(transaction_hash)
    
    # Spara uppdaterat konto
    accounts[account_name] = account
    save_accounts(accounts)


def filter_duplicate_transactions(
    account_name: str, 
    transactions: List[Transaction]
) -> Tuple[List[Transaction], List[Transaction]]:
    """
    Filtrerar bort dubbletter från en lista av transaktioner.
    
    Separerar nya transaktioner från dubbletter baserat på kontots
    tidigare importerade transaktioner.
    
    Args:
        account_name: Namn på kontot
        transactions: Lista med Transaction-objekt att filtrera
        
    Returns:
        Tuple med (nya_transaktioner, dubbletter)
    """
    new_transactions = []
    duplicate_transactions = []
    
    for transaction in transactions:
        if is_transaction_duplicate(account_name, transaction):
            duplicate_transactions.append(transaction)
        else:
            new_transactions.append(transaction)
    
    return new_transactions, duplicate_transactions


def register_transactions(account_name: str, transactions: List[Transaction]) -> None:
    """
    Registrerar flera transaktioner samtidigt för ett konto.
    
    Effektiv metod för att registrera många transaktioner på en gång,
    med endast en sparoperation till databasen.
    
    Args:
        account_name: Namn på kontot
        transactions: Lista med Transaction-objekt att registrera
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        accounts[account_name] = get_or_create_account(account_name)
    
    account = accounts[account_name]
    
    # Lägg till alla transaktions-hasher
    for transaction in transactions:
        transaction_hash = calculate_transaction_hash(transaction)
        account.transaction_hashes.add(transaction_hash)
    
    # Spara uppdaterat konto
    accounts[account_name] = account
    save_accounts(accounts)


def delete_imported_file(account_name: str, filename: str) -> bool:
    """
    Tar bort en importerad fil från ett kontos historik.
    
    Detta tar endast bort filreferensen, inte de faktiska transaktionerna
    som importerades från filen.
    
    Args:
        account_name: Namn på kontot
        filename: Filnamn att ta bort
        
    Returns:
        True om filen togs bort, False om filen inte hittades
    """
    accounts = load_accounts()
    
    if account_name not in accounts:
        return False
    
    account = accounts[account_name]
    
    # Hitta och ta bort filen
    original_length = len(account.imported_files)
    account.imported_files = [
        f for f in account.imported_files 
        if f.get('filename') != filename
    ]
    
    if len(account.imported_files) < original_length:
        accounts[account_name] = account
        save_accounts(accounts)
        return True
    
    return False


def delete_account(account_name: str) -> bool:
    """
    Tar bort ett helt konto från systemet.
    
    VARNING: Detta tar bort all historik om importerade filer och
    transaktions-hasher för kontot. Använd med försiktighet.
    
    Args:
        account_name: Namn på kontot att ta bort
        
    Returns:
        True om kontot togs bort, False om kontot inte hittades
    """
    accounts = load_accounts()
    
    if account_name in accounts:
        del accounts[account_name]
        save_accounts(accounts)
        return True
    
    return False


def clear_all_accounts() -> None:
    """
    Rensar alla konton från systemet.
    
    VARNING: Detta tar bort ALL kontohistorik. Använd endast för
    test/demo-syften eller när du vill börja om från scratch.
    """
    save_accounts({})


def update_account_balance(account_name: str, balance, balance_date, currency: str = "SEK") -> None:
    """
    Uppdaterar saldoinformation för ett konto.
    
    Sparar det aktuella saldot, datum för saldot och valuta.
    Detta används för att hålla koll på kontobalanser och kan
    användas i prognoser och budgetplanering.
    
    Args:
        account_name: Namn på kontot
        balance: Saldo som Decimal
        balance_date: Datum för saldot
        currency: Valuta (standard: SEK)
    """
    from decimal import Decimal
    
    accounts = load_accounts()
    
    if account_name not in accounts:
        accounts[account_name] = get_or_create_account(account_name)
    
    account = accounts[account_name]
    account.current_balance = Decimal(str(balance))
    account.balance_date = balance_date
    account.balance_currency = currency
    
    accounts[account_name] = account
    save_accounts(accounts)
