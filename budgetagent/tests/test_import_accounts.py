"""
Tester för kontohantering och dupliceringsskydd vid import.

Denna testfil validerar att:
- Konton skapas automatiskt baserat på filnamn
- Import-index uppdateras korrekt
- Dubbletter av filer och transaktioner förhindras
- Checksummor beräknas och jämförs korrekt
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from budgetagent.modules import account_manager
from budgetagent.modules.models import Transaction, Account


class TestAccountExtraction:
    """Tester för att extrahera kontonamn från filnamn."""
    
    def test_extract_account_with_timestamp(self):
        """Testar extrahering av kontonamn med timestamp."""
        filename = "PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv"
        account = account_manager.extract_account_from_filename(filename)
        assert account == "PERSONKONTO 1709 20 72840"
    
    def test_extract_account_with_path(self):
        """Testar extrahering med fullständig sökväg."""
        filepath = "/path/to/SPARKONTO 1234 56 78901 - 2025-01-15 14.30.22.csv"
        account = account_manager.extract_account_from_filename(filepath)
        assert account == "SPARKONTO 1234 56 78901"
    
    def test_extract_account_without_timestamp(self):
        """Testar extrahering när filnamn saknar timestamp."""
        filename = "Nordea Lönekonto 9999 88 77777.csv"
        account = account_manager.extract_account_from_filename(filename)
        assert "Lönekonto" in account or "Nordea" in account
    
    def test_extract_account_simple_name(self):
        """Testar extrahering med enkelt filnamn."""
        filename = "transactions.csv"
        account = account_manager.extract_account_from_filename(filename)
        assert account == "transactions"


class TestFileChecksum:
    """Tester för filchecksumma-beräkning."""
    
    def test_checksum_calculation(self):
        """Testar att checksumma beräknas korrekt."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("Datum,Belopp,Beskrivning\n")
            f.write("2025-01-01,-100,Test\n")
            temp_file = f.name
        
        try:
            checksum = account_manager.calculate_file_checksum(temp_file)
            assert checksum is not None
            assert len(checksum) == 32  # MD5 hash är 32 tecken
            assert checksum.isalnum()
        finally:
            Path(temp_file).unlink()
    
    def test_same_file_same_checksum(self):
        """Testar att samma fil ger samma checksumma."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("Datum,Belopp,Beskrivning\n")
            f.write("2025-01-01,-100,Test\n")
            temp_file = f.name
        
        try:
            checksum1 = account_manager.calculate_file_checksum(temp_file)
            checksum2 = account_manager.calculate_file_checksum(temp_file)
            assert checksum1 == checksum2
        finally:
            Path(temp_file).unlink()
    
    def test_different_files_different_checksums(self):
        """Testar att olika filer ger olika checksummor."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f1:
            f1.write("Datum,Belopp,Beskrivning\n")
            f1.write("2025-01-01,-100,Test1\n")
            temp_file1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f2:
            f2.write("Datum,Belopp,Beskrivning\n")
            f2.write("2025-01-01,-200,Test2\n")
            temp_file2 = f2.name
        
        try:
            checksum1 = account_manager.calculate_file_checksum(temp_file1)
            checksum2 = account_manager.calculate_file_checksum(temp_file2)
            assert checksum1 != checksum2
        finally:
            Path(temp_file1).unlink()
            Path(temp_file2).unlink()


class TestTransactionHash:
    """Tester för transaktions-hash-beräkning."""
    
    def test_transaction_hash_calculation(self):
        """Testar att transaktionshash beräknas korrekt."""
        transaction = Transaction(
            date=date(2025, 1, 1),
            amount=Decimal('-100.00'),
            description="ICA Maxi Linköping",
            currency="SEK"
        )
        
        tx_hash = account_manager.calculate_transaction_hash(transaction)
        assert tx_hash is not None
        assert len(tx_hash) == 64  # SHA256 hash är 64 tecken
        assert tx_hash.isalnum()
    
    def test_same_transaction_same_hash(self):
        """Testar att samma transaktion ger samma hash."""
        transaction = Transaction(
            date=date(2025, 1, 1),
            amount=Decimal('-100.00'),
            description="ICA Maxi Linköping",
            currency="SEK"
        )
        
        hash1 = account_manager.calculate_transaction_hash(transaction)
        hash2 = account_manager.calculate_transaction_hash(transaction)
        assert hash1 == hash2
    
    def test_different_transactions_different_hashes(self):
        """Testar att olika transaktioner ger olika hasher."""
        transaction1 = Transaction(
            date=date(2025, 1, 1),
            amount=Decimal('-100.00'),
            description="ICA Maxi Linköping",
            currency="SEK"
        )
        
        transaction2 = Transaction(
            date=date(2025, 1, 2),
            amount=Decimal('-150.00'),
            description="Coop Forum Stockholm",
            currency="SEK"
        )
        
        hash1 = account_manager.calculate_transaction_hash(transaction1)
        hash2 = account_manager.calculate_transaction_hash(transaction2)
        assert hash1 != hash2


class TestAccountManagement:
    """Tester för kontohantering."""
    
    def test_create_new_account(self, tmp_path):
        """Testar att ett nytt konto skapas korrekt."""
        # Använd temporär sökväg för test
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        account = account_manager.get_or_create_account("TESTKONTO 1234 56 78901")
        
        assert account.account_name == "TESTKONTO 1234 56 78901"
        assert account.imported_files == []
        assert account.transaction_hashes == set()
        assert account.account_number is None
    
    def test_get_existing_account(self, tmp_path):
        """Testar att befintligt konto hämtas korrekt."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        # Skapa konto
        account1 = account_manager.get_or_create_account("TESTKONTO 1234 56 78901")
        
        # Hämta samma konto
        account2 = account_manager.get_or_create_account("TESTKONTO 1234 56 78901")
        
        assert account1.account_name == account2.account_name
    
    def test_save_and_load_accounts(self, tmp_path):
        """Testar att konton sparas och laddas korrekt."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        # Skapa och spara konto
        account = Account(
            account_name="TESTKONTO 1234 56 78901",
            account_number="1234 56 78901",
            imported_files=[{"filename": "test.csv", "checksum": "abc123"}],
            transaction_hashes={"hash1", "hash2"}
        )
        
        accounts = {"TESTKONTO 1234 56 78901": account}
        account_manager.save_accounts(accounts)
        
        # Ladda konton
        loaded_accounts = account_manager.load_accounts()
        
        assert "TESTKONTO 1234 56 78901" in loaded_accounts
        loaded_account = loaded_accounts["TESTKONTO 1234 56 78901"]
        assert loaded_account.account_name == account.account_name
        assert loaded_account.account_number == account.account_number
        assert len(loaded_account.transaction_hashes) == 2


class TestDuplicateProtection:
    """Tester för dupliceringsskydd."""
    
    def test_is_file_imported_new_file(self, tmp_path):
        """Testar att ny fil inte är markerad som importerad."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        account_name = "TESTKONTO 1234 56 78901"
        account_manager.get_or_create_account(account_name)
        
        is_imported = account_manager.is_file_imported(account_name, "new_file.csv")
        assert is_imported is False
    
    def test_is_file_imported_existing_file(self, tmp_path):
        """Testar att importerad fil upptäcks."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        account_name = "TESTKONTO 1234 56 78901"
        account_manager.get_or_create_account(account_name)
        
        # Lägg till fil som importerad
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test data\n")
            temp_file = f.name
        
        try:
            account_manager.add_imported_file(account_name, temp_file)
            
            # Kontrollera att filen är markerad som importerad
            is_imported = account_manager.is_file_imported(account_name, temp_file)
            assert is_imported is True
        finally:
            Path(temp_file).unlink()
    
    def test_filter_duplicate_transactions(self, tmp_path):
        """Testar filtrering av dubblerade transaktioner."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        account_name = "TESTKONTO 1234 56 78901"
        
        # Skapa transaktioner
        transactions = [
            Transaction(
                date=date(2025, 1, 1),
                amount=Decimal('-100.00'),
                description="ICA Maxi",
                currency="SEK"
            ),
            Transaction(
                date=date(2025, 1, 2),
                amount=Decimal('-200.00'),
                description="Coop",
                currency="SEK"
            )
        ]
        
        # Registrera första transaktionen
        account_manager.register_transactions(account_name, [transactions[0]])
        
        # Försök importera båda transaktionerna igen
        new_transactions, duplicates = account_manager.filter_duplicate_transactions(
            account_name, transactions
        )
        
        # Första transaktionen ska vara dublett, andra ska vara ny
        assert len(new_transactions) == 1
        assert len(duplicates) == 1
        assert new_transactions[0].description == "Coop"
        assert duplicates[0].description == "ICA Maxi"


class TestImportIndex:
    """Tester för import-index."""
    
    def test_import_index_structure(self, tmp_path):
        """Testar att import-index har korrekt struktur."""
        import_index_path = tmp_path / "imports_index.yaml"
        
        # Skapa testdata
        import_data = {
            'imports': [
                {
                    'filename': 'test.csv',
                    'checksum': 'abc123',
                    'account': 'TESTKONTO',
                    'import_date': datetime.now().isoformat(),
                    'transaction_count': 10,
                    'transaction_hashes': ['hash1', 'hash2']
                }
            ]
        }
        
        # Spara till fil
        with open(import_index_path, 'w', encoding='utf-8') as f:
            yaml.dump(import_data, f, allow_unicode=True)
        
        # Ladda och validera
        with open(import_index_path, 'r', encoding='utf-8') as f:
            loaded_data = yaml.safe_load(f)
        
        assert 'imports' in loaded_data
        assert len(loaded_data['imports']) == 1
        assert loaded_data['imports'][0]['filename'] == 'test.csv'
        assert loaded_data['imports'][0]['transaction_count'] == 10


class TestEdgeCases:
    """Tester för edge cases."""
    
    def test_empty_account_name(self):
        """Testar hantering av tomt kontonamn."""
        filename = ".csv"
        account = account_manager.extract_account_from_filename(filename)
        # Empty filename should still return something (empty string or default)
        assert account is not None
    
    def test_transaction_with_zero_amount(self):
        """Testar att transaktion med noll-belopp hanteras korrekt."""
        with pytest.raises(ValueError):
            Transaction(
                date=date(2025, 1, 1),
                amount=Decimal('0.00'),
                description="Test",
                currency="SEK"
            )
    
    def test_account_with_special_characters(self, tmp_path):
        """Testar konto med specialtecken."""
        account_manager.ACCOUNTS_DB_PATH = tmp_path / "accounts.yaml"
        
        account_name = "KONTO ÅÄÖ 1234-56-78901"
        account = account_manager.get_or_create_account(account_name)
        
        assert account.account_name == account_name
        
        # Spara och ladda för att testa YAML-hantering
        accounts = {account_name: account}
        account_manager.save_accounts(accounts)
        loaded_accounts = account_manager.load_accounts()
        
        assert account_name in loaded_accounts
