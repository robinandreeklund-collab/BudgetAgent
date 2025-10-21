"""
Modul för hantering av alla inställningar via sliders, dropdowns, toggles.

Denna modul hanterar läsning, visning och uppdatering av alla
systeminställningar som lagras i YAML-filer. Den genererar Dash-komponenter
för interaktiv konfiguration.

Exempel på YAML-konfiguration (settings_panel.yaml):
    settings_panel:
      import_format:
        type: dropdown
        options: ["Swedbank CSV", "SEB Excel", "Revolut JSON"]
      forecast_window:
        type: slider
        min: 1
        max: 12
        default: 6
        unit: "months"
      split_rule:
        type: dropdown
        options: ["equal_split", "income_weighted", "custom_ratio", "needs_based"]
"""

from typing import Dict, Optional, List
from pathlib import Path
import yaml
from dash import html, dcc


def load_settings(yaml_path: str) -> Dict:
    """
    Läser in alla inställningar.
    
    Laddar inställningar från YAML-fil och returnerar dem som
    en strukturerad dictionary.
    
    Args:
        yaml_path: Sökväg till YAML-konfigurationsfil
        
    Returns:
        Dictionary med alla inställningar
        
    Raises:
        FileNotFoundError: Om YAML-filen inte finns
        yaml.YAMLError: Om YAML-filen inte kan parsas
    """
    yaml_file = Path(yaml_path)
    
    if not yaml_file.exists():
        raise FileNotFoundError(f"Inställningsfil hittades inte: {yaml_path}")
    
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'settings_panel' not in data:
            return {}
        
        return data['settings_panel']
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Kunde inte läsa YAML-fil: {e}")


def render_controls(settings: Dict) -> List:
    """
    Skapar Dash-komponenter.
    
    Genererar interaktiva Dash-kontroller (sliders, dropdowns, toggles)
    baserat på inställningsdefinitioner.
    
    Args:
        settings: Dictionary med inställningsdefinitioner
        
    Returns:
        Lista med Dash-komponenter
    """
    components = []
    
    for setting_name, setting_config in settings.items():
        setting_type = setting_config.get('type')
        
        # Skapa rubrik
        label = setting_name.replace('_', ' ').title()
        components.append(html.H3(label, style={'marginTop': '20px'}))
        
        if setting_type == 'dropdown':
            # Skapa dropdown
            options = setting_config.get('options', [])
            default_value = setting_config.get('default')
            
            dropdown_options = [{'label': opt, 'value': opt} for opt in options]
            
            components.append(
                dcc.Dropdown(
                    id=f'settings-{setting_name}',
                    options=dropdown_options,
                    value=default_value,
                    placeholder=f'Välj {label.lower()}'
                )
            )
        
        elif setting_type == 'slider':
            # Skapa slider
            min_val = setting_config.get('min', 0)
            max_val = setting_config.get('max', 100)
            default_val = setting_config.get('default', min_val)
            unit = setting_config.get('unit', '')
            
            # Skapa label med enhet
            if unit:
                components.append(html.Label(f"{label} ({unit}):"))
            else:
                components.append(html.Label(f"{label}:"))
            
            # Skapa marks för slidern
            step = max(1, (max_val - min_val) // 12)
            marks = {i: f'{i}{unit}' if unit else str(i) 
                    for i in range(min_val, max_val + 1, step)}
            
            components.append(
                dcc.Slider(
                    id=f'settings-{setting_name}',
                    min=min_val,
                    max=max_val,
                    value=default_val,
                    marks=marks,
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            )
        
        elif setting_type == 'toggle':
            # Skapa toggle (checklist)
            default_val = setting_config.get('default', False)
            
            components.append(
                dcc.Checklist(
                    id=f'settings-{setting_name}',
                    options=[{'label': label, 'value': 'enabled'}],
                    value=['enabled'] if default_val else []
                )
            )
    
    return components


def update_settings(yaml_path: str, new_values: Dict) -> None:
    """
    Sparar ändringar till YAML.
    
    Uppdaterar YAML-konfigurationsfilen med nya inställningsvärden
    från användargränssnittet.
    
    Args:
        yaml_path: Sökväg till YAML-konfigurationsfil
        new_values: Dictionary med uppdaterade inställningsvärden
        
    Raises:
        FileNotFoundError: Om YAML-filen inte finns
        yaml.YAMLError: Om YAML-filen inte kan läsas eller skrivas
    """
    yaml_file = Path(yaml_path)
    
    if not yaml_file.exists():
        raise FileNotFoundError(f"Inställningsfil hittades inte: {yaml_path}")
    
    try:
        # Läs befintlig konfiguration
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        if 'settings_panel' not in data:
            data['settings_panel'] = {}
        
        # Uppdatera värden
        for setting_name, new_value in new_values.items():
            if setting_name in data['settings_panel']:
                # Uppdatera default-värdet
                if new_value is not None:
                    data['settings_panel'][setting_name]['default'] = new_value
        
        # Spara tillbaka
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Kunde inte uppdatera YAML-fil: {e}")


def get_current_values(yaml_path: str) -> Dict:
    """
    Hämtar aktuella inställningsvärden.
    
    Läser alla default-värden från YAML-konfigurationen.
    
    Args:
        yaml_path: Sökväg till YAML-konfigurationsfil
        
    Returns:
        Dictionary med aktuella inställningsvärden
    """
    settings = load_settings(yaml_path)
    current_values = {}
    
    for setting_name, setting_config in settings.items():
        default_value = setting_config.get('default')
        if default_value is not None:
            current_values[setting_name] = default_value
    
    return current_values
