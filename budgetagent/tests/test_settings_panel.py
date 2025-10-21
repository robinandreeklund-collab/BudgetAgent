"""
Test settings_panel functionality.

Testsuite för settings_panel-modulen som hanterar läsning, visning
och uppdatering av systeminställningar från YAML-filer.
"""

import pytest
import yaml
from pathlib import Path
from budgetagent.modules.settings_panel import (
    load_settings,
    render_controls,
    update_settings,
    get_current_values
)


@pytest.fixture
def temp_settings_file(tmp_path):
    """Skapar en temporär inställningsfil för tester."""
    settings_file = tmp_path / "test_settings.yaml"
    test_data = {
        'settings_panel': {
            'import_format': {
                'type': 'dropdown',
                'options': ['Swedbank CSV', 'SEB Excel', 'Revolut JSON'],
                'default': 'Swedbank CSV'
            },
            'forecast_window': {
                'type': 'slider',
                'min': 1,
                'max': 12,
                'default': 6,
                'unit': 'months'
            },
            'split_rule': {
                'type': 'dropdown',
                'options': ['equal_split', 'income_weighted', 'custom_ratio', 'needs_based'],
                'default': 'equal_split'
            },
            'alert_threshold': {
                'type': 'slider',
                'min': 0,
                'max': 100,
                'default': 80,
                'unit': '%'
            },
            'show_debug_panel': {
                'type': 'toggle',
                'default': True
            }
        }
    }
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f, allow_unicode=True)
    
    return settings_file


class TestLoadSettings:
    """Tester för load_settings-funktionen."""
    
    def test_load_settings_from_valid_file(self, temp_settings_file):
        """Test att läsa in inställningar från giltig YAML-fil."""
        settings = load_settings(str(temp_settings_file))
        
        assert 'import_format' in settings
        assert 'forecast_window' in settings
        assert settings['import_format']['type'] == 'dropdown'
        assert settings['forecast_window']['min'] == 1
        assert settings['forecast_window']['max'] == 12
    
    def test_load_settings_missing_file(self):
        """Test att hantera saknad fil."""
        with pytest.raises(FileNotFoundError):
            load_settings('/path/to/nonexistent/file.yaml')
    
    def test_load_settings_empty_file(self, tmp_path):
        """Test att hantera tom YAML-fil."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding='utf-8')
        
        settings = load_settings(str(empty_file))
        assert settings == {}
    
    def test_load_settings_no_settings_panel_key(self, tmp_path):
        """Test att hantera YAML utan settings_panel-nyckel."""
        no_key_file = tmp_path / "no_key.yaml"
        with open(no_key_file, 'w', encoding='utf-8') as f:
            yaml.dump({'other_key': {}}, f)
        
        settings = load_settings(str(no_key_file))
        assert settings == {}


class TestRenderControls:
    """Tester för render_controls-funktionen."""
    
    def test_render_dropdown_control(self):
        """Test att rendera dropdown-kontroll."""
        settings = {
            'import_format': {
                'type': 'dropdown',
                'options': ['Option1', 'Option2'],
                'default': 'Option1'
            }
        }
        
        components = render_controls(settings)
        assert len(components) > 0
        
        # Verifiera att det finns både label och dropdown
        has_label = any(hasattr(comp, 'children') for comp in components)
        assert has_label
    
    def test_render_slider_control(self):
        """Test att rendera slider-kontroll."""
        settings = {
            'forecast_window': {
                'type': 'slider',
                'min': 1,
                'max': 12,
                'default': 6,
                'unit': 'months'
            }
        }
        
        components = render_controls(settings)
        assert len(components) > 0
    
    def test_render_toggle_control(self):
        """Test att rendera toggle-kontroll."""
        settings = {
            'show_debug': {
                'type': 'toggle',
                'default': True
            }
        }
        
        components = render_controls(settings)
        assert len(components) > 0
    
    def test_render_multiple_controls(self, temp_settings_file):
        """Test att rendera flera kontroller samtidigt."""
        settings = load_settings(str(temp_settings_file))
        components = render_controls(settings)
        
        # Bör innehålla komponenter för alla inställningar
        assert len(components) > 5  # Minst en label och kontroll per inställning


class TestUpdateSettings:
    """Tester för update_settings-funktionen."""
    
    def test_update_single_setting(self, temp_settings_file):
        """Test att uppdatera en enskild inställning."""
        new_values = {
            'forecast_window': 9
        }
        
        update_settings(str(temp_settings_file), new_values)
        
        # Verifiera att värdet uppdaterades
        settings = load_settings(str(temp_settings_file))
        assert settings['forecast_window']['default'] == 9
    
    def test_update_multiple_settings(self, temp_settings_file):
        """Test att uppdatera flera inställningar."""
        new_values = {
            'forecast_window': 10,
            'alert_threshold': 90
        }
        
        update_settings(str(temp_settings_file), new_values)
        
        settings = load_settings(str(temp_settings_file))
        assert settings['forecast_window']['default'] == 10
        assert settings['alert_threshold']['default'] == 90
    
    def test_update_nonexistent_setting(self, temp_settings_file):
        """Test att uppdatera icke-existerande inställning."""
        new_values = {
            'nonexistent_setting': 'value'
        }
        
        # Bör inte krascha, men inte heller lägga till ny inställning
        update_settings(str(temp_settings_file), new_values)
        
        settings = load_settings(str(temp_settings_file))
        assert 'nonexistent_setting' not in settings
    
    def test_update_missing_file(self):
        """Test att uppdatera saknad fil."""
        with pytest.raises(FileNotFoundError):
            update_settings('/path/to/nonexistent/file.yaml', {})


class TestGetCurrentValues:
    """Tester för get_current_values-funktionen."""
    
    def test_get_current_values(self, temp_settings_file):
        """Test att hämta aktuella värden."""
        current_values = get_current_values(str(temp_settings_file))
        
        assert 'import_format' in current_values
        assert 'forecast_window' in current_values
        assert current_values['forecast_window'] == 6
        assert current_values['import_format'] == 'Swedbank CSV'
    
    def test_get_current_values_empty_settings(self, tmp_path):
        """Test att hämta värden från tomma inställningar."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding='utf-8')
        
        current_values = get_current_values(str(empty_file))
        assert current_values == {}


class TestIntegration:
    """Integrationstester för hela flödet."""
    
    def test_full_settings_workflow(self, temp_settings_file):
        """Test hela arbetsflödet: läs, uppdatera, läs igen."""
        # Läs ursprungliga värden
        original = get_current_values(str(temp_settings_file))
        assert original['forecast_window'] == 6
        
        # Uppdatera värden
        new_values = {'forecast_window': 8}
        update_settings(str(temp_settings_file), new_values)
        
        # Verifiera att värdena uppdaterades
        updated = get_current_values(str(temp_settings_file))
        assert updated['forecast_window'] == 8
        
        # Verifiera att andra värden inte påverkades
        assert updated['alert_threshold'] == original['alert_threshold']
