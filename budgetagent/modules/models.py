"""
Gemensamma datamodeller för BudgetAgent-systemet.

Denna modul innehåller Pydantic-modeller som används av alla moduler
för att säkerställa konsistent datatyper och validering genom hela systemet.

Modellerna representerar kärnentiteterna:
- Transaction: Enskilda banktransaktioner
- Bill: Framtida fakturor och betalningar
- Income: Inkomster (återkommande och engångs)
- ForecastData: Prognosdata för framtida saldo
- AlertConfig: Konfiguration för varningar och tröskelvärden
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Literal
from datetime import date, datetime
from decimal import Decimal


class Transaction(BaseModel):
    """
    Representerar en banktransaktion.
    
    Används av import_bank_data, parse_transactions och categorize_expenses
    för att hantera historiska transaktioner.
    
    Attributes:
        date: Transaktionsdatum
        amount: Belopp (positivt för inkomster, negativt för utgifter)
        description: Beskrivning från banken
        category: Tilldelad kategori (t.ex. "Mat", "Boende", "Transport")
        currency: Valuta (standard: SEK)
        metadata: Extra information som butik, plats, etc.
    """
    date: date
    amount: Decimal
    description: str
    category: Optional[str] = None
    currency: str = "SEK"
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @field_validator('amount')
    @classmethod
    def amount_must_not_be_zero(cls, v: Decimal) -> Decimal:
        """Säkerställer att belopp inte är noll."""
        if v == 0:
            raise ValueError('Belopp kan inte vara noll')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "date": "2025-11-15",
                "amount": -350.50,
                "description": "ICA Maxi Linköping",
                "category": "Mat",
                "currency": "SEK",
                "metadata": {"store": "ICA Maxi", "location": "Linköping"}
            }
        }


class Bill(BaseModel):
    """
    Representerar en kommande faktura eller betalning.
    
    Används av upcoming_bills, parse_pdf_bills och forecast_engine
    för att spåra och planera framtida utgifter.
    
    Attributes:
        name: Fakturans namn/beskrivning
        amount: Belopp att betala
        due_date: Förfallodatum
        category: Kategori (t.ex. "Boende", "Försäkring")
        recurring: Om fakturan är återkommande
        frequency: Frekvens om återkommande (monthly, yearly, etc.)
        paid: Om fakturan är betald
        payment_date: Datum då fakturan betalades
    """
    name: str
    amount: Decimal
    due_date: date
    category: str
    recurring: bool = False
    frequency: Optional[Literal["monthly", "quarterly", "yearly"]] = None
    paid: bool = False
    payment_date: Optional[date] = None
    
    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        """Säkerställer att belopp är positivt."""
        if v <= 0:
            raise ValueError('Fakturabelopp måste vara positivt')
        return v
    
    @field_validator('payment_date')
    @classmethod
    def payment_date_must_be_after_due_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validerar att betalningsdatum är efter förfallodatum om angivet."""
        if v is not None and 'due_date' in info.data:
            if v < info.data['due_date']:
                raise ValueError('Betalningsdatum kan inte vara före förfallodatum')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "Elräkning",
                "amount": 900,
                "due_date": "2025-11-30",
                "category": "Boende",
                "recurring": True,
                "frequency": "monthly",
                "paid": False
            }
        }


class Income(BaseModel):
    """
    Representerar en inkomst.
    
    Används av income_tracker och forecast_engine för att spåra
    både återkommande och engångsinkomster.
    
    Attributes:
        person: Personens namn
        source: Inkomstkälla (t.ex. "Lön", "Frilans", "Bonus")
        amount: Belopp
        date: Datum för inkomsten
        recurring: Om inkomsten är återkommande
        frequency: Frekvens om återkommande (monthly, yearly, etc.)
        category: Inkomstkategori (valfritt)
    """
    person: str
    source: str
    amount: Decimal
    date: date
    recurring: bool = False
    frequency: Optional[Literal["monthly", "yearly"]] = None
    category: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        """Säkerställer att belopp är positivt."""
        if v <= 0:
            raise ValueError('Inkomst måste vara positiv')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "person": "Robin",
                "source": "Lön",
                "amount": 28000,
                "date": "2025-11-25",
                "recurring": True,
                "frequency": "monthly"
            }
        }


class ForecastData(BaseModel):
    """
    Representerar prognosdata för ett specifikt datum.
    
    Används av forecast_engine för att lagra simulerade
    framtida saldon och kassaflöden.
    
    Attributes:
        date: Datum för prognosen
        balance: Prognostiserat saldo
        income: Förväntad inkomst för perioden
        expenses: Förväntade utgifter för perioden
        category_breakdown: Utgifter per kategori
        confidence: Konfidensnivå för prognosen (0-1)
    """
    date: date
    balance: Decimal
    income: Decimal = Decimal(0)
    expenses: Decimal = Decimal(0)
    category_breakdown: Dict[str, Decimal] = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "date": "2025-12-31",
                "balance": 15000,
                "income": 28000,
                "expenses": 13000,
                "category_breakdown": {
                    "Mat": 4500,
                    "Boende": 6000,
                    "Transport": 1500,
                    "Nöje": 1000
                },
                "confidence": 0.85
            }
        }


class AlertConfig(BaseModel):
    """
    Konfiguration för varningar och tröskelvärden.
    
    Används av alerts_and_insights för att definiera när
    varningar ska genereras baserat på utgifts- och inkomstmönster.
    
    Attributes:
        threshold_percentage: Tröskelprocent för varningar (0-100)
        category_limits: Utgiftsgränser per kategori
        alert_days_before_due: Dagar före förfallodag att varna
        min_balance_warning: Minimalt saldo som triggar varning
    """
    threshold_percentage: int = Field(default=80, ge=0, le=100)
    category_limits: Dict[str, Decimal] = Field(default_factory=dict)
    alert_days_before_due: int = Field(default=7, ge=1)
    min_balance_warning: Decimal = Field(default=Decimal(1000))
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "threshold_percentage": 80,
                "category_limits": {
                    "Mat": 5000,
                    "Nöje": 2000,
                    "Transport": 1500
                },
                "alert_days_before_due": 7,
                "min_balance_warning": 1000
            }
        }


class Scenario(BaseModel):
    """
    Representerar ett hypotetiskt scenario för jämförelse.
    
    Används av forecast_engine för att simulera "vad händer om"-scenarier
    och jämföra olika ekonomiska beslut.
    
    Attributes:
        name: Beskrivande namn för scenariot
        description: Detaljerad beskrivning
        income_adjustments: Justeringar av inkomster (person -> belopp)
        expense_adjustments: Justeringar av utgifter (kategori -> belopp)
        one_time_transactions: Engångstransaktioner att inkludera
    """
    name: str
    description: str
    income_adjustments: Dict[str, Decimal] = Field(default_factory=dict)
    expense_adjustments: Dict[str, Decimal] = Field(default_factory=dict)
    one_time_transactions: List[Transaction] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "Extra inkomst i januari",
                "description": "Vad händer om vi får 5000 kr extra bonus?",
                "income_adjustments": {"Robin": 5000},
                "expense_adjustments": {},
                "one_time_transactions": []
            }
        }


class Account(BaseModel):
    """
    Representerar ett bankkonto i systemet.
    
    Används av account_manager för att hålla koll på importerade konton
    och undvika dubbletter av både filer och transaktioner.
    
    Attributes:
        account_name: Unikt kontonamn (från filnamn)
        account_number: Kontonummer (om tillgängligt)
        imported_files: Lista över importerade filnamn med checksums
        last_import_date: Senaste importdatum
        transaction_hashes: Set av transaktions-hasher för dupliceringsskydd
        current_balance: Aktuellt saldo (från senaste import)
        balance_date: Datum för aktuellt saldo
        balance_currency: Valuta för saldo (standard: SEK)
    """
    account_name: str
    account_number: Optional[str] = None
    imported_files: List[Dict[str, str]] = Field(default_factory=list)
    last_import_date: Optional[datetime] = None
    transaction_hashes: set = Field(default_factory=set)
    current_balance: Optional[Decimal] = None
    balance_date: Optional[date] = None
    balance_currency: str = "SEK"
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "account_name": "PERSONKONTO 1709 20 72840",
                "account_number": "1709 20 72840",
                "imported_files": [
                    {"filename": "PERSONKONTO 1709 20 72840 - 2025-10-21 09.39.41.csv", "checksum": "abc123"}
                ],
                "last_import_date": "2025-10-21T09:39:41",
                "transaction_hashes": set(),
                "current_balance": "15000.00",
                "balance_date": "2025-10-21",
                "balance_currency": "SEK"
            }
        }
