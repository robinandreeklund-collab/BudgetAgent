"""
Modul för extrahering och strukturering av transaktioner från rådata.

Denna modul bearbetar råa banktransaktioner och konverterar dem till ett
strukturerat format. Den hanterar datumkonvertering, textbearbetning och
extrahering av metadata som butik, kategori och plats.
"""

import pandas as pd
from typing import List
from .models import Transaction


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
