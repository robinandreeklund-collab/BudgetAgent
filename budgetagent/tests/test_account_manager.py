"""
Test för account_manager-modulen.

Testsuite för kontohantering, filimport-spårning och dupliceringsskydd.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date
from decimal import Decimal

from budgetagent.modules import account_manager
from budgetagent.modules.models import Account, Transaction


class TestExtractAccountFromFilename:
    """Tester för extract_account_from_filename."""

    def test_extract_account_with_date_pattern(self):
        """Test att extrahera kontonamn med datum-mönster."""
        filename = "PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv"
        result = account_manager.extract_account_from_filename(filename)
        assert result == "PERSONKONTO 1709 20 72840"

    def test_extract_account_with_full_path(self):
        """Test att extrahera kontonamn från fullständig sökväg."""
        filepath = "/home/user/data/PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv"
        result = account_manager.extract_account_from_filename(filepath)
        assert result == "PERSONKONTO 1709 20 72840"

    def test_extract_account_number_only(self):
        """Test att extrahera kontonamn med enbart kontonummer."""
        filename = "1709 20 72840 - 2025-10-21.csv"
        result = account_manager.extract_account_from_filename(filename)
        assert "1709 20 72840" in result

    def test_extract_account_no_date(self):
        """Test att extrahera kontonamn utan datum."""
        filename = "SPARKONTO_NORDEA.csv"
        result = account_manager.extract_account_from_filename(filename)
        assert result == "SPARKONTO_NORDEA"

    def test_extract_account_alternative_date_format(self):
        """Test att extrahera kontonamn med alternativt datumformat."""
        filename = "KONTO 1234 - 20251021.csv"
        result = account_manager.extract_account_from_filename(filename)
        assert "KONTO 1234" in result


class TestAccountManagement:
    """Tester för kontohanteringsfunktioner."""

    @pytest.fixture(autouse=True)
    def setup_temp_db(self, tmp_path, monkeypatch):
        """Skapar en temporär accounts-databas för varje test."""
        temp_accounts_path = tmp_path / "accounts.yaml"
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        yield temp_accounts_path

    def test_get_or_create_account_new(self):
        """Test att skapa ett nytt konto."""
        account = account_manager.get_or_create_account("TEST_KONTO", "1234567890")
        
        assert account.account_name == "TEST_KONTO"
        assert account.account_number == "1234567890"
        assert account.imported_files == []
        assert len(account.transaction_hashes) == 0

    def test_get_or_create_account_existing(self):
        """Test att hämta ett befintligt konto."""
        # Skapa konto första gången
        account1 = account_manager.get_or_create_account("TEST_KONTO", "1234567890")
        
        # Hämta samma konto
        account2 = account_manager.get_or_create_account("TEST_KONTO")
        
        assert account1.account_name == account2.account_name
        assert account1.account_number == account2.account_number

    def test_load_and_save_accounts(self):
        """Test att spara och ladda konton."""
        # Skapa och spara ett konto
        account = Account(
            account_name="TEST_KONTO",
            account_number="1234567890",
            imported_files=[],
            transaction_hashes=set()
        )
        
        accounts = {"TEST_KONTO": account}
        account_manager.save_accounts(accounts)
        
        # Ladda tillbaka
        loaded_accounts = account_manager.load_accounts()
        
        assert "TEST_KONTO" in loaded_accounts
        assert loaded_accounts["TEST_KONTO"].account_name == "TEST_KONTO"
        assert loaded_accounts["TEST_KONTO"].account_number == "1234567890"

    def test_save_accounts_with_transaction_hashes(self):
        """Test att spara konto med transaktions-hasher."""
        # Skapa konto med transaktions-hasher
        account = Account(
            account_name="TEST_KONTO",
            account_number="1234567890",
            imported_files=[],
            transaction_hashes={"hash1", "hash2", "hash3"}
        )
        
        accounts = {"TEST_KONTO": account}
        account_manager.save_accounts(accounts)
        
        # Ladda tillbaka
        loaded_accounts = account_manager.load_accounts()
        
        assert len(loaded_accounts["TEST_KONTO"].transaction_hashes) == 3
        assert "hash1" in loaded_accounts["TEST_KONTO"].transaction_hashes


class TestFileImportTracking:
    """Tester för filimport-spårning."""

    @pytest.fixture(autouse=True)
    def setup_temp_db(self, tmp_path, monkeypatch):
        """Skapar en temporär accounts-databas för varje test."""
        temp_accounts_path = tmp_path / "accounts.yaml"
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        yield tmp_path

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Skapar en exempelfil för testning."""
        test_file = tmp_path / "test_import.csv"
        test_file.write_text("Bokföringsdatum,Belopp,Rubrik\n2025-01-15,-350.50,ICA Maxi\n", encoding='utf-8')
        return str(test_file)

    def test_is_file_imported_new_file(self, sample_file):
        """Test att kontrollera om en ny fil är importerad."""
        result = account_manager.is_file_imported("TEST_KONTO", sample_file)
        assert result is False

    def test_is_file_imported_after_import(self, sample_file):
        """Test att kontrollera fil efter import."""
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_imported_file("TEST_KONTO", sample_file)
        
        result = account_manager.is_file_imported("TEST_KONTO", sample_file)
        assert result is True

    def test_add_imported_file(self, sample_file):
        """Test att registrera en importerad fil."""
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_imported_file("TEST_KONTO", sample_file)
        
        accounts = account_manager.load_accounts()
        account = accounts["TEST_KONTO"]
        
        assert len(account.imported_files) == 1
        assert account.imported_files[0]['filename'] == Path(sample_file).name
        assert 'checksum' in account.imported_files[0]
        assert account.last_import_date is not None

    def test_is_file_imported_by_checksum(self, tmp_path):
        """Test att identifiera fil med samma checksumma men annat namn."""
        # Skapa första filen
        file1 = tmp_path / "file1.csv"
        file1.write_text("Bokföringsdatum,Belopp,Rubrik\n2025-01-15,-350.50,ICA Maxi\n", encoding='utf-8')
        
        # Registrera fil1
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_imported_file("TEST_KONTO", str(file1))
        
        # Skapa identisk fil med annat namn
        file2 = tmp_path / "file2.csv"
        file2.write_text("Bokföringsdatum,Belopp,Rubrik\n2025-01-15,-350.50,ICA Maxi\n", encoding='utf-8')
        
        # Kontrollera att file2 identifieras som redan importerad via checksumma
        result = account_manager.is_file_imported("TEST_KONTO", str(file2))
        assert result is True


class TestTransactionDuplicateDetection:
    """Tester för transaktions-dupliceringsskydd."""

    @pytest.fixture(autouse=True)
    def setup_temp_db(self, tmp_path, monkeypatch):
        """Skapar en temporär accounts-databas för varje test."""
        temp_accounts_path = tmp_path / "accounts.yaml"
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        yield temp_accounts_path

    @pytest.fixture
    def sample_transaction(self):
        """Skapar en exempeltransaktion."""
        return Transaction(
            date=date(2025, 1, 15),
            amount=Decimal('-350.50'),
            description="ICA Maxi Linköping",
            currency="SEK"
        )

    def test_calculate_transaction_hash(self, sample_transaction):
        """Test att beräkna transaktions-hash."""
        hash1 = account_manager.calculate_transaction_hash(sample_transaction)
        hash2 = account_manager.calculate_transaction_hash(sample_transaction)
        
        # Samma transaktion ska ge samma hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex är 64 tecken

    def test_different_transactions_different_hashes(self):
        """Test att olika transaktioner ger olika hasher."""
        trans1 = Transaction(
            date=date(2025, 1, 15),
            amount=Decimal('-350.50'),
            description="ICA Maxi",
            currency="SEK"
        )
        
        trans2 = Transaction(
            date=date(2025, 1, 16),
            amount=Decimal('-350.50'),
            description="ICA Maxi",
            currency="SEK"
        )
        
        hash1 = account_manager.calculate_transaction_hash(trans1)
        hash2 = account_manager.calculate_transaction_hash(trans2)
        
        assert hash1 != hash2

    def test_is_transaction_duplicate_new(self, sample_transaction):
        """Test att kontrollera om ny transaktion är dubblett."""
        account_manager.get_or_create_account("TEST_KONTO")
        result = account_manager.is_transaction_duplicate("TEST_KONTO", sample_transaction)
        assert result is False

    def test_is_transaction_duplicate_after_add(self, sample_transaction):
        """Test att kontrollera transaktion efter registrering."""
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_transaction("TEST_KONTO", sample_transaction)
        
        result = account_manager.is_transaction_duplicate("TEST_KONTO", sample_transaction)
        assert result is True

    def test_add_transaction(self, sample_transaction):
        """Test att registrera en transaktion."""
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_transaction("TEST_KONTO", sample_transaction)
        
        accounts = account_manager.load_accounts()
        account = accounts["TEST_KONTO"]
        
        assert len(account.transaction_hashes) == 1

    def test_filter_duplicate_transactions(self):
        """Test att filtrera bort dubbletter från transaktionslista."""
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                amount=Decimal('-350.50'),
                description="ICA Maxi",
                currency="SEK"
            ),
            Transaction(
                date=date(2025, 1, 16),
                amount=Decimal('-120.00'),
                description="Circle K",
                currency="SEK"
            ),
            Transaction(
                date=date(2025, 1, 17),
                amount=Decimal('-75.00'),
                description="Apotek",
                currency="SEK"
            )
        ]
        
        # Registrera första transaktionen
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_transaction("TEST_KONTO", transactions[0])
        
        # Filtrera listan (innehåller en dubblett)
        new_trans, duplicates = account_manager.filter_duplicate_transactions(
            "TEST_KONTO", transactions
        )
        
        assert len(new_trans) == 2
        assert len(duplicates) == 1
        assert duplicates[0].description == "ICA Maxi"

    def test_register_transactions(self):
        """Test att registrera flera transaktioner samtidigt."""
        transactions = [
            Transaction(
                date=date(2025, 1, 15),
                amount=Decimal('-350.50'),
                description="ICA Maxi",
                currency="SEK"
            ),
            Transaction(
                date=date(2025, 1, 16),
                amount=Decimal('-120.00'),
                description="Circle K",
                currency="SEK"
            )
        ]
        
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.register_transactions("TEST_KONTO", transactions)
        
        accounts = account_manager.load_accounts()
        account = accounts["TEST_KONTO"]
        
        assert len(account.transaction_hashes) == 2


class TestCalculateFileChecksum:
    """Tester för checksumma-beräkning."""

    def test_calculate_file_checksum(self, tmp_path):
        """Test att beräkna checksumma för en fil."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("test content", encoding='utf-8')
        
        checksum = account_manager.calculate_file_checksum(str(test_file))
        
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5 hex är 32 tecken

    def test_identical_files_same_checksum(self, tmp_path):
        """Test att identiska filer ger samma checksumma."""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.csv"
        
        content = "Bokföringsdatum,Belopp,Rubrik\n2025-01-15,-350.50,ICA\n"
        file1.write_text(content, encoding='utf-8')
        file2.write_text(content, encoding='utf-8')
        
        checksum1 = account_manager.calculate_file_checksum(str(file1))
        checksum2 = account_manager.calculate_file_checksum(str(file2))
        
        assert checksum1 == checksum2

    def test_different_files_different_checksum(self, tmp_path):
        """Test att olika filer ger olika checksummor."""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.csv"
        
        file1.write_text("content1", encoding='utf-8')
        file2.write_text("content2", encoding='utf-8')
        
        checksum1 = account_manager.calculate_file_checksum(str(file1))
        checksum2 = account_manager.calculate_file_checksum(str(file2))
        
        assert checksum1 != checksum2


class TestDeleteOperations:
    """Tester för att ta bort filer och konton."""

    @pytest.fixture(autouse=True)
    def setup_temp_db(self, tmp_path, monkeypatch):
        """Skapar en temporär accounts-databas för varje test."""
        temp_accounts_path = tmp_path / "accounts.yaml"
        monkeypatch.setattr(account_manager, 'ACCOUNTS_DB_PATH', temp_accounts_path)
        yield temp_accounts_path

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Skapar en exempelfil för testning."""
        test_file = tmp_path / "test_import.csv"
        test_file.write_text("Bokföringsdatum,Belopp,Rubrik\n2025-01-15,-350.50,ICA Maxi\n", encoding='utf-8')
        return str(test_file)

    def test_delete_imported_file_success(self, sample_file):
        """Test att ta bort en importerad fil."""
        # Skapa konto och importera fil
        account_manager.get_or_create_account("TEST_KONTO")
        account_manager.add_imported_file("TEST_KONTO", sample_file)
        
        # Verifiera att filen finns
        accounts = account_manager.load_accounts()
        assert len(accounts["TEST_KONTO"].imported_files) == 1
        
        # Ta bort filen
        filename = Path(sample_file).name
        result = account_manager.delete_imported_file("TEST_KONTO", filename)
        
        assert result is True
        
        # Verifiera att filen är borttagen
        accounts = account_manager.load_accounts()
        assert len(accounts["TEST_KONTO"].imported_files) == 0

    def test_delete_imported_file_not_found(self):
        """Test att ta bort en fil som inte finns."""
        account_manager.get_or_create_account("TEST_KONTO")
        
        result = account_manager.delete_imported_file("TEST_KONTO", "nonexistent.csv")
        
        assert result is False

    def test_delete_imported_file_nonexistent_account(self):
        """Test att ta bort fil från konto som inte finns."""
        result = account_manager.delete_imported_file("NONEXISTENT_ACCOUNT", "file.csv")
        
        assert result is False

    def test_delete_account_success(self):
        """Test att ta bort ett konto."""
        # Skapa konto
        account_manager.get_or_create_account("TEST_KONTO", "1234567890")
        
        # Verifiera att kontot finns
        accounts = account_manager.load_accounts()
        assert "TEST_KONTO" in accounts
        
        # Ta bort kontot
        result = account_manager.delete_account("TEST_KONTO")
        
        assert result is True
        
        # Verifiera att kontot är borttaget
        accounts = account_manager.load_accounts()
        assert "TEST_KONTO" not in accounts

    def test_delete_account_not_found(self):
        """Test att ta bort ett konto som inte finns."""
        result = account_manager.delete_account("NONEXISTENT_ACCOUNT")
        
        assert result is False

    def test_clear_all_accounts(self):
        """Test att rensa alla konton."""
        # Skapa flera konton
        account_manager.get_or_create_account("KONTO1")
        account_manager.get_or_create_account("KONTO2")
        account_manager.get_or_create_account("KONTO3")
        
        # Verifiera att konton finns
        accounts = account_manager.load_accounts()
        assert len(accounts) == 3
        
        # Rensa alla konton
        account_manager.clear_all_accounts()
        
        # Verifiera att alla konton är borttagna
        accounts = account_manager.load_accounts()
        assert len(accounts) == 0
