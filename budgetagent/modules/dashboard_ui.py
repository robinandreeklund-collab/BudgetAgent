"""
Modul för Dash-gränssnitt för visualisering, inmatning och agentinteraktion.

Denna modul implementerar det interaktiva webbgränssnittet med Dash (Plotly).
Den visar grafer, tillhandahåller formulär för inmatning och erbjuder
ett frågegränssnitt för agentinteraktion.

Exempel på YAML-konfiguration används från flera filer:
- settings_panel.yaml för allmänna inställningar
- forecast_engine.yaml för prognosinställningar
- income_tracker.yaml för inkomstdata
"""

import pandas as pd
from typing import Optional, List, Dict
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
from .models import Transaction, Bill, Income, ForecastData
from . import upcoming_bills, income_tracker, forecast_engine, alerts_and_insights, query_parser
import signal
import sys
import atexit
from pathlib import Path


def cleanup_demo_data():
    """
    Rensar all demo-data när servern avslutas.
    
    Denna funktion anropas automatiskt vid Ctrl+C eller serveravslut.
    Den tömmer alla YAML-filer och CSV-filer med användardata.
    """
    print("\n🧹 Rensar demo-data...")
    
    try:
        # Rensa YAML-filer
        config_dir = Path(__file__).parent.parent / "config"
        
        # Töm upcoming_bills.yaml
        bills_file = config_dir / "upcoming_bills.yaml"
        bills_file.write_text("upcoming_bills:\n  bills: []\n", encoding='utf-8')
        
        # Töm income_tracker.yaml  
        income_file = config_dir / "income_tracker.yaml"
        income_file.write_text("income_tracker:\n  incomes: []\n  people: []\n", encoding='utf-8')
        
        # Töm forecast_engine.yaml
        forecast_file = config_dir / "forecast_engine.yaml"
        forecast_file.write_text("forecast_engine:\n  history_window_months: 6\n  categories: []\n  future_income: []\n  future_bills: []\n", encoding='utf-8')
        
        # Ta bort transaktionsfil
        data_dir = Path(__file__).parent.parent / "data"
        transactions_file = data_dir / "transactions.csv"
        if transactions_file.exists():
            transactions_file.unlink()
        
        print("✅ Demo-data rensad!")
    except Exception as e:
        print(f"⚠️ Kunde inte rensa all data: {e}")


def signal_handler(sig, frame):
    """Hanterar Ctrl+C och avslutar servern rent."""
    print("\n⏹️  Avslutar server...")
    cleanup_demo_data()
    sys.exit(0)


# Registrera cleanup-funktioner
atexit.register(cleanup_demo_data)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def create_app_layout() -> html.Div:
    """
    Skapar huvudlayout för Dash-applikationen.
    
    Strukturerar hela gränssnittet med alla paneler och komponenter.
    
    Returns:
        Dash html.Div med komplett layout
    """
    return html.Div([
        html.H1("💸 BudgetAgent Dashboard", style={'textAlign': 'center'}),
        
        # Dold Store för att signalera datauppdateringar
        dcc.Store(id='data-update-trigger', data=0),
        
        # Flikar för olika sektioner
        dcc.Tabs([
            dcc.Tab(label='Översikt', children=[
                html.Div([
                    create_forecast_section(),
                    create_insights_section(),
                    create_expense_distribution_section()
                ])
            ]),
            dcc.Tab(label='Inmatning', children=[
                html.Div([
                    input_panel()
                ])
            ]),
            dcc.Tab(label='Konton', children=[
                html.Div([
                    accounts_panel()
                ])
            ]),
            dcc.Tab(label='Fakturor', children=[
                html.Div([
                    bills_panel()
                ])
            ]),
            dcc.Tab(label='Agentfrågor', children=[
                html.Div([
                    agent_query_interface()
                ])
            ]),
            dcc.Tab(label='Inställningar', children=[
                html.Div([
                    settings_panel()
                ])
            ])
        ])
    ])


def create_forecast_section() -> html.Div:
    """
    Skapar prognossektionen med graf och nyckeltal.
    
    Returns:
        Dash html.Div med prognoskomponenter
    """
    return html.Div([
        html.H2("Ekonomisk prognos"),
        dcc.Graph(id='forecast-graph'),
        html.Div(id='forecast-summary')
    ], style={'padding': '20px'})


def create_insights_section() -> html.Div:
    """
    Skapar sektionen för insikter och varningar.
    
    Returns:
        Dash html.Div med insiktskomponenter
    """
    return html.Div([
        html.H2("Insikter och varningar"),
        html.Div(id='alerts-container'),
        html.Div(id='insights-container')
    ], style={'padding': '20px'})


def create_expense_distribution_section() -> html.Div:
    """
    Skapar sektionen för utgiftsfördelning per kategori.
    
    Returns:
        Dash html.Div med utgiftsfördelning
    """
    return html.Div([
        html.H2("Utgiftsfördelning per kategori"),
        dcc.Graph(id='expense-distribution-graph')
    ], style={'padding': '20px'})


def input_panel() -> html.Div:
    """
    Skapar formulär för inkomster, fakturor, inställningar.
    
    Genererar Dash layout-komponenter för användarinmatning av
    ny data och justering av inställningar.
    
    Returns:
        Dash layout-objekt med inmatningsformulär
    """
    return html.Div([
        html.H2("Lägg till data"),
        
        # Nordea CSV-import
        html.H3("Importera Nordea CSV"),
        dcc.Upload(
            id='upload-nordea-csv',
            children=html.Div([
                '📁 Dra och släpp eller ',
                html.A('välj Nordea CSV-fil', style={'fontWeight': 'bold', 'cursor': 'pointer'})
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'marginBottom': '10px',
                'backgroundColor': '#f8f9fa'
            },
            multiple=False
        ),
        html.Div(id='upload-feedback', style={'marginBottom': '20px'}),
        
        # Store för att bevara transaktioner för granskning
        dcc.Store(id='temp-transactions-store', storage_type='memory'),
        
        # Kategoriserings- och granskningspanel
        html.Div(id='categorization-review-panel', style={'marginBottom': '20px'}),
        
        html.Hr(style={'margin': '20px 0'}),
        
        # Fakturainmatning
        html.H3("Ny faktura"),
        html.Div([
            dcc.Input(id='bill-name', type='text', placeholder='Namn'),
            dcc.Input(id='bill-amount', type='number', placeholder='Belopp'),
            dcc.DatePickerSingle(id='bill-due-date', placeholder='Förfallodag'),
            dcc.Dropdown(
                id='bill-category',
                options=[
                    {'label': 'Boende', 'value': 'Boende'},
                    {'label': 'Mat', 'value': 'Mat'},
                    {'label': 'Transport', 'value': 'Transport'},
                    {'label': 'Försäkring', 'value': 'Försäkring'},
                    {'label': 'Nöje', 'value': 'Nöje'}
                ],
                placeholder='Kategori'
            ),
            dcc.Dropdown(
                id='bill-account',
                options=[],  # Populated dynamically
                placeholder='Välj konto (valfritt)'
            ),
            html.Button('Lägg till faktura', id='add-bill-button', n_clicks=0)
        ], style={'marginBottom': '20px'}),
        
        # Inkomstinmatning
        html.H3("Ny inkomst"),
        html.Div([
            dcc.Input(id='income-person', type='text', placeholder='Person'),
            dcc.Input(id='income-source', type='text', placeholder='Källa'),
            dcc.Input(id='income-amount', type='number', placeholder='Belopp'),
            dcc.DatePickerSingle(id='income-date', placeholder='Datum'),
            dcc.Dropdown(
                id='income-account',
                options=[],  # Populated dynamically
                placeholder='Välj konto (valfritt)'
            ),
            dcc.Checklist(
                id='income-recurring',
                options=[{'label': 'Återkommande', 'value': 'recurring'}],
                value=[]
            ),
            html.Button('Lägg till inkomst', id='add-income-button', n_clicks=0)
        ], style={'marginBottom': '20px'}),
        
        # Feedback
        html.Div(id='input-feedback')
    ], style={'padding': '20px'})


def bills_panel() -> html.Div:
    """
    Skapar fakturapanelen som visar alla inlagda fakturor.
    
    Returns:
        Dash layout-objekt med fakturaöversikt
    """
    return html.Div([
        html.H2("Fakturahantering"),
        html.P("Här kan du se, redigera och ta bort alla dina inlagda fakturor."),
        html.Div([
            html.Button('Uppdatera fakturaöversikt', id='refresh-bills-button', n_clicks=0, 
                       style={'marginRight': '10px', 'marginBottom': '20px'}),
        ]),
        html.Div(id='bill-action-feedback', style={'marginBottom': '20px'}),
        html.Div(id='bills-container'),
        
        # Dialog för att redigera faktura
        html.Div(id='edit-bill-dialog', style={'display': 'none'}, children=[
            html.Div([
                html.H3("Redigera faktura"),
                html.Label("Namn:"),
                dcc.Input(id='edit-bill-name', type='text', style={'width': '100%', 'marginBottom': '10px'}),
                html.Label("Belopp:"),
                dcc.Input(id='edit-bill-amount', type='number', style={'width': '100%', 'marginBottom': '10px'}),
                html.Label("Förfallodag:"),
                dcc.DatePickerSingle(id='edit-bill-due-date', style={'marginBottom': '10px'}),
                html.Label("Kategori:"),
                dcc.Dropdown(
                    id='edit-bill-category',
                    options=[
                        {'label': 'Boende', 'value': 'Boende'},
                        {'label': 'Mat', 'value': 'Mat'},
                        {'label': 'Transport', 'value': 'Transport'},
                        {'label': 'Försäkring', 'value': 'Försäkring'},
                        {'label': 'Nöje', 'value': 'Nöje'}
                    ],
                    style={'marginBottom': '10px'}
                ),
                html.Label("Konto:"),
                dcc.Dropdown(
                    id='edit-bill-account',
                    options=[],
                    style={'marginBottom': '10px'}
                ),
                dcc.Store(id='edit-bill-original-data'),
                html.Button('Spara ändringar', id='save-bill-edit-button', n_clicks=0, 
                           style={'marginRight': '10px', 'backgroundColor': '#28a745', 'color': 'white', 
                                  'border': 'none', 'padding': '8px 16px', 'borderRadius': '5px', 'cursor': 'pointer'}),
                html.Button('Avbryt', id='cancel-bill-edit-button', n_clicks=0,
                           style={'backgroundColor': '#6c757d', 'color': 'white', 
                                  'border': 'none', 'padding': '8px 16px', 'borderRadius': '5px', 'cursor': 'pointer'})
            ], style={
                'border': '2px solid #007bff',
                'borderRadius': '10px',
                'padding': '20px',
                'backgroundColor': '#f8f9fa',
                'maxWidth': '500px',
                'margin': '20px auto'
            })
        ])
    ], style={'padding': '20px'})


def accounts_panel() -> html.Div:
    """
    Skapar kontopanelen som visar alla registrerade konton.
    
    Inklusive:
    - Lista över konton med importstatistik
    - Paginerad tabell med transaktioner (50 rader/sida)
    - Kategori-dropdown per transaktion
    - Knapp för att skapa ny kategori
    - "Lär AI"-knapp för att spara till träningsdata
    - "Förhandsgranska"-knapp för att köra auto_categorize
    
    Returns:
        Dash layout-objekt med kontoöversikt
    """
    return html.Div([
        html.H2("Kontohantering och Transaktionskategorisering"),
        
        # Kontoväljare
        html.Div([
            html.Label("Välj konto:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='account-selector',
                placeholder='Välj ett konto...',
                style={'width': '300px', 'display': 'inline-block'}
            ),
            html.Button('Uppdatera', id='refresh-accounts-button', n_clicks=0,
                       style={'marginLeft': '10px'})
        ], style={'marginBottom': '20px'}),
        
        # Kontostatistik
        html.Div(id='account-stats', style={'marginBottom': '20px'}),
        
        # Kategoriseringsverktyg
        html.Div([
            html.H3("Kategoriseringsverktyg"),
            html.Div([
                html.Button('Förhandsgranska kategorisering', id='preview-categorization-btn',
                           n_clicks=0, style={'marginRight': '10px'}),
                html.Button('Spara valda kategorier', id='save-categories-btn',
                           n_clicks=0, style={'marginRight': '10px'}),
                html.Button('Skapa ny kategori', id='create-category-btn',
                           n_clicks=0, style={'marginRight': '10px'}),
                html.Button('Träna AI med valda', id='train-ai-btn',
                           n_clicks=0, style={
                               'backgroundColor': '#28a745',
                               'color': 'white',
                               'border': 'none',
                               'padding': '8px 16px',
                               'borderRadius': '5px'
                           })
            ], style={'marginBottom': '10px'}),
            html.Div(id='categorization-feedback', style={'marginBottom': '20px'})
        ], style={'marginBottom': '20px'}),
        
        # Modal för att skapa ny kategori
        html.Div([
            dcc.Input(id='new-category-name', type='text', placeholder='Kategorinamn',
                     style={'marginRight': '10px', 'display': 'none'}),
            dcc.Input(id='new-category-keywords', type='text', 
                     placeholder='Nyckelord (kommaseparerade)',
                     style={'marginRight': '10px', 'display': 'none'}),
            html.Button('Spara kategori', id='save-new-category-btn', n_clicks=0,
                       style={'display': 'none'})
        ], id='new-category-form', style={'marginBottom': '20px'}),
        
        # Träningsdata-statistik
        html.Div(id='training-stats', style={'marginBottom': '20px'}),
        
        # Paginerings-kontroller
        html.Div([
            html.Button('← Föregående', id='prev-page-btn', n_clicks=0,
                       style={'marginRight': '10px'}),
            html.Span(id='page-info', children='Sida 1 av 1',
                     style={'marginRight': '10px', 'fontWeight': 'bold'}),
            html.Button('Nästa →', id='next-page-btn', n_clicks=0),
            html.Div([
                html.Label('Rader per sida:', style={'marginRight': '5px'}),
                dcc.Dropdown(
                    id='rows-per-page',
                    options=[
                        {'label': '25', 'value': 25},
                        {'label': '50', 'value': 50},
                        {'label': '100', 'value': 100}
                    ],
                    value=50,
                    clearable=False,
                    style={'width': '100px', 'display': 'inline-block'}
                )
            ], style={'display': 'inline-block', 'marginLeft': '20px'})
        ], style={'marginBottom': '20px'}),
        
        # Transaktionstabell
        html.Div(id='transactions-table'),
        
        # Dold Store för att hålla transaktionsdata
        dcc.Store(id='transactions-store', data=[]),
        dcc.Store(id='current-page', data=1),
        
        # Action feedback
        html.Div(id='account-action-feedback', style={'marginTop': '20px'})
    ], style={'padding': '20px'})


def agent_query_interface() -> html.Div:
    """
    Skapar frågefält för agentinteraktion, t.ex. "Hur mycket har vi kvar i januari?".
    
    Implementerar ett textbaserat gränssnitt där användaren kan
    ställa naturliga frågor om sin ekonomi.
    
    Returns:
        Dash layout-objekt med frågegränssnitt
    """
    return html.Div([
        html.H2("Ställ frågor till BudgetAgent"),
        html.P("Exempel på frågor:"),
        html.Ul([
            html.Li("Hur mycket har vi kvar i januari?"),
            html.Li("Visa alla fakturor i december"),
            html.Li("Vad händer om vi får 5000 kr extra?"),
            html.Li("Hur mycket spenderar vi på mat per månad?")
        ]),
        dcc.Input(
            id='agent-query-input',
            type='text',
            placeholder='Skriv din fråga här...',
            style={'width': '100%', 'padding': '10px'}
        ),
        html.Button('Skicka fråga', id='query-submit-button', n_clicks=0),
        html.Div(id='agent-response', style={'marginTop': '20px'})
    ], style={'padding': '20px'})


def settings_panel() -> html.Div:
    """
    Skapar inställningspanel baserad på settings_panel.yaml.
    
    Returns:
        Dash layout-objekt med inställningar
    """
    from . import settings_panel as sp
    from pathlib import Path
    
    # Ladda inställningar från YAML
    config_path = Path(__file__).parent.parent / "config" / "settings_panel.yaml"
    
    try:
        settings = sp.load_settings(str(config_path))
        current_values = sp.get_current_values(str(config_path))
        
        # Generera kontroller dynamiskt
        components = [html.H2("Inställningar")]
        components.extend(sp.render_controls(settings))
        
        # Lägg till spara-knapp och feedback
        components.append(html.Button('Spara inställningar', id='save-settings-button', n_clicks=0, style={'marginTop': '20px'}))
        components.append(html.Div(id='settings-feedback', style={'marginTop': '10px'}))
        
        return html.Div(components, style={'padding': '20px'})
        
    except Exception as e:
        # Fallback till statisk layout om YAML inte kan läsas
        print(f"Kunde inte ladda inställningar: {e}")
        return html.Div([
            html.H2("Inställningar"),
            
            html.H3("Import"),
            dcc.Dropdown(
                id='settings-import_format',
                options=[
                    {'label': 'Nordea CSV', 'value': 'nordea'},
                    {'label': 'Swedbank CSV', 'value': 'swedbank'},
                    {'label': 'SEB Excel', 'value': 'seb'},
                    {'label': 'Revolut JSON', 'value': 'revolut'}
                ],
                placeholder='Välj importformat'
            ),
            
            html.H3("Prognos"),
            html.Label("Prognosfönster (månader):"),
            dcc.Slider(
                id='settings-forecast_window',
                min=1,
                max=12,
                value=1,
                marks={i: str(i) for i in range(1, 13)}
            ),
            
            html.H3("Fördelningsregel"),
            dcc.Dropdown(
                id='settings-split_rule',
                options=[
                    {'label': 'Lika fördelning', 'value': 'equal_split'},
                    {'label': 'Inkomstbaserad', 'value': 'income_weighted'},
                    {'label': 'Anpassad andel', 'value': 'custom_ratio'},
                    {'label': 'Behovsbaserad', 'value': 'needs_based'}
                ],
                value='equal_split'
            ),
            
            html.H3("Varningströsklar"),
            html.Label("Varningsnivå (%):"),
            dcc.Slider(
                id='settings-alert_threshold',
                min=0,
                max=100,
                value=80,
                marks={i: f'{i}%' for i in range(0, 101, 20)}
            ),
            
            html.H3("Debug"),
            dcc.Checklist(
                id='settings-show_debug_panel',
                options=[{'label': 'Visa debug-panel', 'value': 'enabled'}],
                value=['enabled']
            ),
            
            html.Button('Spara inställningar', id='save-settings-button', n_clicks=0),
            html.Div(id='settings-feedback')
        ], style={'padding': '20px'})


def create_categorization_review_panel(transactions: List[Transaction], filename: str) -> html.Div:
    """
    Skapar en panel för att granska och redigera kategoriserade transaktioner.
    
    Args:
        transactions: Lista med kategoriserade transaktioner
        filename: Filnamn för importen
        
    Returns:
        Dash html.Div med granskningspanel
    """
    if not transactions:
        return html.Div()
    
    # Skapa tabell med transaktioner
    table_rows = []
    for idx, trans in enumerate(transactions):
        confidence = float(trans.metadata.get('confidence', 0))
        needs_review = trans.metadata.get('needs_review') == 'true'
        
        # Färgkodning baserat på confidence
        if confidence >= 0.9:
            row_color = '#d4edda'  # Grön
        elif confidence >= 0.7:
            row_color = '#fff3cd'  # Gul
        else:
            row_color = '#f8d7da'  # Röd
        
        # Ikon för review-status
        review_icon = '⚠️ ' if needs_review else '✓ '
        
        table_rows.append(
            html.Tr([
                html.Td(str(idx + 1), style={'padding': '8px', 'border': '1px solid #ddd'}),
                html.Td(str(trans.date), style={'padding': '8px', 'border': '1px solid #ddd'}),
                html.Td(trans.description[:40], style={'padding': '8px', 'border': '1px solid #ddd'}),
                html.Td(f'{trans.amount} SEK', style={'padding': '8px', 'border': '1px solid #ddd'}),
                html.Td([
                    review_icon,
                    dcc.Dropdown(
                        id={'type': 'category-select', 'index': idx},
                        options=[
                            {'label': 'Mat', 'value': 'Mat'},
                            {'label': 'Transport', 'value': 'Transport'},
                            {'label': 'Boende', 'value': 'Boende'},
                            {'label': 'Nöje', 'value': 'Nöje'},
                            {'label': 'Kläder', 'value': 'Kläder'},
                            {'label': 'Hälsa', 'value': 'Hälsa'},
                            {'label': 'Försäkring', 'value': 'Försäkring'},
                            {'label': 'Inkomst', 'value': 'Inkomst'},
                            {'label': 'Okategoriserad', 'value': 'Okategoriserad'}
                        ],
                        value=trans.category,
                        clearable=False,
                        style={'minWidth': '150px'}
                    ),
                    # Hidden store to hold selected category
                    dcc.Store(id={'type': 'category-store', 'index': idx}, data=trans.category)
                ], style={'padding': '8px', 'border': '1px solid #ddd'}),
                html.Td(
                    f'{confidence:.0%}',
                    style={
                        'padding': '8px',
                        'border': '1px solid #ddd',
                        'fontWeight': 'bold',
                        'color': 'green' if confidence >= 0.9 else ('orange' if confidence >= 0.7 else 'red')
                    }
                )
            ], style={'backgroundColor': row_color})
        )
    
    return html.Div([
        html.H3('Granska kategoriserade transaktioner'),
        html.P('Justera kategorier om nödvändigt och klicka sedan på "Godkänn och spara" nedan.'),
        html.Div([
            html.Table([
                html.Thead(html.Tr([
                    html.Th('#', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'}),
                    html.Th('Datum', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'}),
                    html.Th('Beskrivning', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'}),
                    html.Th('Belopp', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'}),
                    html.Th('Kategori', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'}),
                    html.Th('Säkerhet', style={'padding': '8px', 'border': '1px solid #ddd', 'backgroundColor': '#f8f9fa'})
                ])),
                html.Tbody(table_rows)
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginBottom': '20px'})
        ], style={'maxHeight': '400px', 'overflowY': 'auto', 'border': '1px solid #ddd'}),
        html.Button('Godkänn och spara transaktioner', id='confirm-import-button', n_clicks=0,
                   style={
                       'padding': '10px 20px',
                       'backgroundColor': '#28a745',
                       'color': 'white',
                       'border': 'none',
                       'borderRadius': '5px',
                       'fontSize': '16px',
                       'cursor': 'pointer',
                       'marginTop': '10px'
                   }),
        html.Div(id='confirm-import-feedback', style={'marginTop': '10px'})
    ], style={
        'border': '2px solid #007bff',
        'borderRadius': '10px',
        'padding': '20px',
        'backgroundColor': '#f8f9fa',
        'marginTop': '20px'
    })


def update_forecast_graph(forecast_data: List[ForecastData]) -> go.Figure:
    """
    Visar framtida saldo.
    
    Uppdaterar prognos-grafen med simulerat framtida saldo
    baserat på aktuell data och prognoser.
    
    Args:
        forecast_data: Lista med ForecastData-objekt
        
    Returns:
        Plotly Figure-objekt
    """
    if not forecast_data:
        # Tom graf om ingen data finns
        fig = go.Figure()
        fig.add_annotation(
            text="Ingen prognosdata tillgänglig",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Extrahera data från forecast_data
    dates = [f.date for f in forecast_data]
    balances = [float(f.balance) for f in forecast_data]
    incomes = [float(f.income) for f in forecast_data]
    expenses = [float(f.expenses) for f in forecast_data]
    
    # Skapa figur med flera linjer
    fig = go.Figure()
    
    # Saldo-linje
    fig.add_trace(go.Scatter(
        x=dates,
        y=balances,
        mode='lines+markers',
        name='Prognostiserat saldo',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8)
    ))
    
    # Inkomst-linje
    fig.add_trace(go.Scatter(
        x=dates,
        y=incomes,
        mode='lines',
        name='Inkomster',
        line=dict(color='#06A77D', width=2, dash='dash')
    ))
    
    # Utgifts-linje
    fig.add_trace(go.Scatter(
        x=dates,
        y=expenses,
        mode='lines',
        name='Utgifter',
        line=dict(color='#D62246', width=2, dash='dash')
    ))
    
    # Layout
    fig.update_layout(
        title='Ekonomisk prognos',
        xaxis_title='Datum',
        yaxis_title='Belopp (SEK)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig


def handle_agent_query(query: str) -> str:
    """
    Hanterar agentfråga genom att använda query_parser-modulen.
    
    Wrapper-funktion som anropar query_parser för att besvara
    användarens fråga.
    
    Args:
        query: Användarens fråga i naturligt språk
        
    Returns:
        Svar som formaterad text
    """
    return query_parser.answer_query(query)


def render_dashboard() -> None:
    """
    Startar Dash-app med alla komponenter.
    
    Initierar och kör Dash-applikationen med alla paneler,
    grafer och interaktiva element.
    """
    from decimal import Decimal
    from datetime import datetime
    import base64
    import io
    from . import import_bank_data, parse_transactions
    
    app = Dash(__name__, suppress_callback_exceptions=True)
    app.layout = create_app_layout()
    
    # Store för att hålla temporära transaktioner för granskning
    temp_transactions_store = {'transactions': [], 'filename': ''}
    
    # Callback för att hantera Nordea CSV-uppladdning
    @app.callback(
        [Output('upload-feedback', 'children'),
         Output('categorization-review-panel', 'children'),
         Output('temp-transactions-store', 'data'),
         Output('data-update-trigger', 'data')],
        Input('upload-nordea-csv', 'contents'),
        State('upload-nordea-csv', 'filename'),
        State('data-update-trigger', 'data'),
        prevent_initial_call=True
    )
    def handle_csv_upload(contents, filename, current_trigger):
        """Hanterar uppladdning av Nordea CSV-fil med kategorisering."""
        if contents is None:
            return html.Div(), html.Div(), None, current_trigger
        
        try:
            from . import categorize_expenses, account_manager
            import yaml
            
            # Dekoda innehållet
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Spara tillfälligt till fil
            temp_path = f'/tmp/{filename}'
            with open(temp_path, 'wb') as f:
                f.write(decoded)
            
            # Importera transaktioner
            transactions = import_bank_data.import_and_parse(temp_path)
            
            if not transactions:
                return (
                    html.Div([
                        html.Span('⚠️ ', style={'fontSize': '20px'}),
                        html.Span(f'Inga transaktioner hittades i {filename} (kan redan vara importerad)')
                    ], style={'color': 'orange', 'padding': '10px', 'backgroundColor': '#fff3cd', 'borderRadius': '5px'}),
                    html.Div(),
                    None,
                    current_trigger
                )
            
            # Ladda kategoriseringsregler
            config_path = Path(__file__).parent.parent / "config" / "categorization_rules.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
            
            # Kategorisera transaktioner
            categorized_transactions = categorize_expenses.categorize_transactions(transactions, rules)
            
            # Skapa store-data för granskning (serialisera till JSON-kompatibelt format)
            store_data = {
                'transactions': [
                    {
                        'date': str(t.date),
                        'description': t.description,
                        'amount': float(t.amount),
                        'category': t.category,
                        'metadata': t.metadata
                    }
                    for t in categorized_transactions
                ],
                'filename': filename
            }
            
            # Räkna kategorier och confidence
            total_trans = len(categorized_transactions)
            needs_review = sum(1 for t in categorized_transactions 
                              if t.metadata.get('needs_review') == 'true')
            uncategorized = sum(1 for t in categorized_transactions 
                               if t.category == 'Okategoriserad')
            
            # Skapa granskningspanel
            review_panel = create_categorization_review_panel(
                categorized_transactions, filename
            )
            
            feedback = html.Div([
                html.Span('✅ ', style={'fontSize': '20px'}),
                html.Span(f'Import lyckades! {total_trans} transaktioner laddade från {filename}'),
                html.Br(),
                html.Br(),
                html.Span('📊 Kategorisering: ', style={'fontWeight': 'bold'}),
                html.Br(),
                html.Span(f'• {total_trans - uncategorized} kategoriserade automatiskt'),
                html.Br(),
                html.Span(f'• {uncategorized} okategoriserade', 
                         style={'color': 'orange' if uncategorized > 0 else 'green'}),
                html.Br(),
                html.Span(f'• {needs_review} behöver granskning',
                         style={'color': 'red' if needs_review > 0 else 'green'}),
                html.Br(),
                html.Br(),
                html.Small('Granska och godkänn transaktionerna nedan innan import', 
                          style={'fontStyle': 'italic'})
            ], style={'color': '#155724', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
            
            return feedback, review_panel, store_data, current_trigger
            
        except FileNotFoundError as e:
            return (
                html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Fil hittades inte: {str(e)}')
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'}),
                html.Div(),
                None,
                current_trigger
            )
        except ValueError as e:
            return (
                html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Felaktigt filformat: {str(e)}')
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'}),
                html.Div(),
                None,
                current_trigger
            )
        except Exception as e:
            import traceback
            return (
                html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Fel vid import: {str(e)}'),
                    html.Br(),
                    html.Small(traceback.format_exc(), style={'fontSize': '10px', 'color': '#666'})
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'}),
                html.Div(),
                None,
                current_trigger
            )
    
    # Callback för att uppdatera prognos-grafen vid sidladdning
    @app.callback(
        Output('forecast-graph', 'figure'),
        Input('forecast-graph', 'id')  # Trigger vid laddning
    )
    def update_forecast(_):
        """Uppdaterar prognosgrafen."""
        try:
            # Standardprognos visar nuvarande dag och en månad framåt (2 datapunkter)
            forecast_data = forecast_engine.simulate_monthly_balance(2)
            return update_forecast_graph(forecast_data)
        except Exception as e:
            print(f"Fel vid uppdatering av prognos: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Fel: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    # Callback för att lägga till faktura
    @app.callback(
        Output('input-feedback', 'children'),
        Input('add-bill-button', 'n_clicks'),
        State('bill-name', 'value'),
        State('bill-amount', 'value'),
        State('bill-due-date', 'date'),
        State('bill-category', 'value'),
        State('bill-account', 'value'),
        prevent_initial_call=True
    )
    def add_bill_callback(n_clicks, name, amount, due_date, category, account):
        """Lägger till en ny faktura."""
        if n_clicks and name and amount and due_date and category:
            try:
                bill = Bill(
                    name=name,
                    amount=Decimal(str(amount)),
                    due_date=datetime.fromisoformat(due_date).date(),
                    category=category,
                    account=account,
                    recurring=False
                )
                upcoming_bills.add_bill(bill)
                return html.Div(f"✅ Faktura '{name}' tillagd!", style={'color': 'green'})
            except Exception as e:
                return html.Div(f"❌ Fel: {str(e)}", style={'color': 'red'})
        return html.Div("Fyll i alla fält", style={'color': 'orange'})
    
    # Callback för att lägga till inkomst
    @app.callback(
        [Output('input-feedback', 'children', allow_duplicate=True),
         Output('data-update-trigger', 'data', allow_duplicate=True)],
        Input('add-income-button', 'n_clicks'),
        State('income-person', 'value'),
        State('income-source', 'value'),
        State('income-amount', 'value'),
        State('income-date', 'date'),
        State('income-account', 'value'),
        State('income-recurring', 'value'),
        State('data-update-trigger', 'data'),
        prevent_initial_call=True
    )
    def add_income_callback(n_clicks, person, source, amount, date, account, recurring, current_trigger):
        """Lägger till en ny inkomst."""
        if n_clicks and person and source and amount and date:
            try:
                is_recurring = 'recurring' in (recurring or [])
                income = Income(
                    person=person,
                    source=source,
                    amount=Decimal(str(amount)),
                    date=datetime.fromisoformat(date).date(),
                    account=account,
                    recurring=is_recurring,
                    frequency='monthly' if is_recurring else None
                )
                income_tracker.add_income(income)
                return html.Div(f"✅ Inkomst för '{person}' tillagd!", style={'color': 'green'}), current_trigger + 1
            except Exception as e:
                return html.Div(f"❌ Fel: {str(e)}", style={'color': 'red'}), current_trigger
        return html.Div("Fyll i alla fält", style={'color': 'orange'}), current_trigger
    
    # Callback för agentfrågor
    @app.callback(
        Output('agent-response', 'children'),
        Input('query-submit-button', 'n_clicks'),
        State('agent-query-input', 'value'),
        prevent_initial_call=True
    )
    def handle_query_callback(n_clicks, query):
        """Hanterar agentfrågor."""
        if n_clicks and query:
            try:
                response = handle_agent_query(query)
                return html.Div([
                    html.H4("Svar:"),
                    html.P(response, style={'whiteSpace': 'pre-line'})
                ])
            except Exception as e:
                return html.Div(f"❌ Fel: {str(e)}", style={'color': 'red'})
        return html.Div()
    
    # Callback för insikter och varningar
    @app.callback(
        [Output('alerts-container', 'children'),
         Output('insights-container', 'children'),
         Output('forecast-graph', 'figure', allow_duplicate=True)],
        [Input('forecast-graph', 'id'),
         Input('data-update-trigger', 'data')],  # Lyssna också på datauppdateringar
        prevent_initial_call='initial_duplicate'
    )
    def update_insights(_, trigger_value):
        """Uppdaterar insikter, varningar och prognos."""
        try:
            # Ladda faktiska transaktioner
            transactions = parse_transactions.load_transactions()
            
            # Ladda konton för att hämta aktuellt saldo
            from . import account_manager
            accounts = account_manager.load_accounts()
            
            # Uppdatera prognos med aktuell data
            forecast_data = forecast_engine.simulate_monthly_balance(6)
            new_figure = update_forecast_graph(forecast_data)
            
            if transactions:
                total_transactions = len(transactions)
                total_expenses = sum(t.amount for t in transactions if t.amount < 0)
                total_income = sum(t.amount for t in transactions if t.amount > 0)
                
                alerts_list = [
                    "Inga varningar för tillfället"
                ]
                
                insights_list = [
                    f"Totalt {total_transactions} transaktioner importerade",
                    f"Totala utgifter: {total_expenses:.2f} SEK",
                    f"Totala inkomster: {total_income:.2f} SEK",
                    f"Nettosaldo: {(total_income + total_expenses):.2f} SEK"
                ]
                
                # Lägg till totalt aktuellt saldo från alla konton
                if accounts:
                    from decimal import Decimal
                    total_balance = Decimal('0')
                    currency = "SEK"  # Default valuta
                    accounts_with_balance = 0
                    currencies = set()

                    for acc_name, acc in accounts.items():
                        if acc.current_balance is not None:
                            total_balance += acc.current_balance
                            accounts_with_balance += 1
                            currencies.add(acc.balance_currency)
                            # Använd valutan från första kontot med saldo
                            if accounts_with_balance == 1:
                                currency = acc.balance_currency

                    if accounts_with_balance > 0:
                        if len(currencies) > 1:
                            alerts_list.append(
                                "⚠️ Konton har olika valutor. Summering av saldo kan vara missvisande."
                            )
                        else:
                            insights_list.append(
                                f"Aktuellt saldo: {float(total_balance):.2f} {currency}"
                            )
            else:
                alerts_list = ["Inga varningar för tillfället"]
                insights_list = ["Importera Nordea CSV-filer för att se insikter"]
            
            alerts_div = html.Div([
                html.H4("⚠️ Varningar"),
                html.Ul([html.Li(alert) for alert in alerts_list])
            ])
            
            insights_div = html.Div([
                html.H4("💡 Insikter"),
                html.Ul([html.Li(insight) for insight in insights_list])
            ])
            
            return alerts_div, insights_div, new_figure
        except Exception as e:
            return html.Div(f"Fel: {e}"), html.Div(), go.Figure()
    
    # Callback för att spara inställningar och uppdatera prognos
    @app.callback(
        [Output('settings-feedback', 'children'),
         Output('forecast-graph', 'figure', allow_duplicate=True)],
        Input('save-settings-button', 'n_clicks'),
        [State('settings-forecast_window', 'value'),
         State('settings-split_rule', 'value'),
         State('settings-alert_threshold', 'value'),
         State('settings-import_format', 'value'),
         State('settings-show_debug_panel', 'value')],
        prevent_initial_call=True
    )
    def save_settings_callback(n_clicks, forecast_window, split_rule, alert_threshold, import_format, show_debug):
        """Sparar inställningar och uppdaterar prognosen."""
        if n_clicks:
            try:
                from . import settings_panel as sp
                from pathlib import Path
                
                # Sökväg till inställningsfil
                config_path = Path(__file__).parent.parent / "config" / "settings_panel.yaml"
                
                # Förbered nya värden
                new_values = {}
                if forecast_window is not None:
                    new_values['forecast_window'] = forecast_window
                if split_rule is not None:
                    new_values['split_rule'] = split_rule
                if alert_threshold is not None:
                    new_values['alert_threshold'] = alert_threshold
                if import_format is not None:
                    new_values['import_format'] = import_format
                if show_debug is not None:
                    new_values['show_debug_panel'] = 'enabled' in show_debug
                
                # Spara inställningar till YAML
                sp.update_settings(str(config_path), new_values)
                
                # Uppdatera prognosen med nytt fönster
                forecast_data = forecast_engine.simulate_monthly_balance(forecast_window or 6)
                new_figure = update_forecast_graph(forecast_data)
                
                feedback = html.Div([
                    html.Span('✅ ', style={'fontSize': '20px'}),
                    html.Span(f'Inställningar sparade! Prognos uppdaterad för {forecast_window or 6} månader.')
                ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px', 'marginTop': '10px'})
                
                return feedback, new_figure
            except Exception as e:
                feedback = html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Fel vid sparande: {str(e)}')
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px', 'marginTop': '10px'})
                
                # Returnera gammal graf vid fel
                forecast_data = forecast_engine.simulate_monthly_balance(6)
                fallback_figure = update_forecast_graph(forecast_data)
                return feedback, fallback_figure
        
        return html.Div(), go.Figure()
    
    # Callback för uppdatering av kategorier (dynamisk per transaktion)
    @app.callback(
        Output({'type': 'category-store', 'index': MATCH}, 'data'),
        Input({'type': 'category-select', 'index': MATCH}, 'value'),
        prevent_initial_call=True
    )
    def update_category_store(selected_category):
        """Lagrar vald kategori för varje transaktion."""
        return selected_category
    
    # Callback för att godkänna och spara transaktioner med uppdaterade kategorier
    @app.callback(
        [Output('confirm-import-feedback', 'children'),
         Output('data-update-trigger', 'data', allow_duplicate=True),
         Output('categorization-review-panel', 'children', allow_duplicate=True),
         Output('temp-transactions-store', 'data', allow_duplicate=True)],
        Input('confirm-import-button', 'n_clicks'),
        [State({'type': 'category-store', 'index': ALL}, 'data'),
         State('temp-transactions-store', 'data')],
        prevent_initial_call=True
    )
    def confirm_and_save_transactions(n_clicks, category_values, store_data):
        """Sparar transaktioner med uppdaterade kategorier."""
        # Använd no_update för att undvika att rensa panelen när callback inte ska göra något
        if not n_clicks or not store_data or not store_data.get('transactions'):
            raise PreventUpdate
        
        try:
            # Reconstruct transactions from store
            from . import parse_transactions
            from datetime import date as dt_date
            
            transactions = []
            for trans_data in store_data['transactions']:
                trans = Transaction(
                    date=dt_date.fromisoformat(trans_data['date']),
                    description=trans_data['description'],
                    amount=Decimal(str(trans_data['amount'])),
                    category=trans_data['category'],
                    metadata=trans_data['metadata']
                )
                transactions.append(trans)
            
            # Uppdatera kategorier baserat på användarens val från stores
            for idx, trans in enumerate(transactions):
                if idx < len(category_values) and category_values[idx]:
                    trans.category = category_values[idx]
            
            # Spara transaktionerna
            parse_transactions.save_transactions(transactions, append=True)
            
            # Rensa temporär store
            saved_count = len(transactions)
            filename = store_data.get('filename', 'filen')
            
            feedback = html.Div([
                html.Span('✅ ', style={'fontSize': '24px'}),
                html.Span(f'Perfekt! {saved_count} transaktioner sparade från {filename}'),
                html.Br(),
                html.Small('Data uppdaterad - se översikten för uppdaterade grafer!',
                          style={'fontStyle': 'italic', 'color': '#28a745'})
            ], style={
                'color': '#155724',
                'padding': '15px',
                'backgroundColor': '#d4edda',
                'borderRadius': '5px',
                'marginTop': '10px',
                'border': '2px solid #28a745'
            })
            
            return feedback, 1, html.Div(), None  # Trigger uppdatering, rensa review panel och store
            
        except Exception as e:
            return (
                html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Fel vid sparande: {str(e)}')
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'}),
                0,
                html.Div(),
                None
            )
    
    # Callback för att uppdatera kontoöversikt
    @app.callback(
        Output('accounts-container', 'children'),
        [Input('refresh-accounts-button', 'n_clicks'),
         Input('accounts-container', 'id')]  # Trigger vid sidladdning också
    )
    def update_accounts_display(n_clicks, _):
        """Uppdaterar visningen av registrerade konton."""
        try:
            from . import account_manager
            
            accounts = account_manager.load_accounts()
            
            if not accounts:
                return html.Div([
                    html.P('Inga konton registrerade än. Importera en CSV-fil för att skapa ett konto.',
                          style={'fontStyle': 'italic', 'color': '#666'})
                ])
            
            # Skapa kort för varje konto
            account_cards = []
            for account_name, account in accounts.items():
                # Skapa lista med filer och delete-knappar
                file_items = []
                for idx, file in enumerate(account.imported_files[-10:]):  # Senaste 10
                    file_items.append(
                        html.Li([
                            html.Span(f"{file.get('filename', 'Okänd fil')} - {file.get('import_date', 'Okänt datum')}"),
                            html.Button('🗑️', 
                                       id={'type': 'delete-file', 'account': account_name, 'filename': file.get('filename')},
                                       n_clicks=0,
                                       style={
                                           'marginLeft': '10px',
                                           'backgroundColor': '#dc3545',
                                           'color': 'white',
                                           'border': 'none',
                                           'borderRadius': '3px',
                                           'cursor': 'pointer',
                                           'fontSize': '12px',
                                           'padding': '2px 6px'
                                       })
                        ])
                    )
                
                card = html.Div([
                    html.Div([
                        html.H4(account_name, style={'marginBottom': '10px', 'color': '#007bff', 'display': 'inline-block'}),
                        html.Button('Ta bort konto', 
                                   id={'type': 'delete-account', 'account': account_name},
                                   n_clicks=0,
                                   style={
                                       'float': 'right',
                                       'backgroundColor': '#dc3545',
                                       'color': 'white',
                                       'border': 'none',
                                       'padding': '5px 10px',
                                       'borderRadius': '5px',
                                       'cursor': 'pointer',
                                       'fontSize': '14px'
                                   })
                    ], style={'overflow': 'auto'}),
                    html.P([
                        html.Strong('Kontonummer: '),
                        html.Span(account.account_number or 'Ej angivet')
                    ]),
                    html.P([
                        html.Strong('Aktuellt saldo: '),
                        html.Span(
                            f'{account.current_balance:,.2f} {account.balance_currency}' if account.current_balance else 'Ej tillgängligt',
                            style={'fontWeight': 'bold', 'color': '#28a745' if account.current_balance and account.current_balance > 0 else '#dc3545'}
                        )
                    ]),
                    html.P([
                        html.Strong('Saldo per: '),
                        html.Span(str(account.balance_date) if account.balance_date else 'Okänt')
                    ]) if account.balance_date else html.Div(),
                    html.P([
                        html.Strong('Antal importerade filer: '),
                        html.Span(str(len(account.imported_files)))
                    ]),
                    html.P([
                        html.Strong('Totalt antal transaktioner: '),
                        html.Span(str(len(account.transaction_hashes)))
                    ]),
                    html.P([
                        html.Strong('Senaste import: '),
                        html.Span(str(account.last_import_date) if account.last_import_date else 'Aldrig')
                    ]),
                    html.Details([
                        html.Summary('Visa importhistorik', style={'cursor': 'pointer', 'color': '#007bff'}),
                        html.Ul(file_items) if file_items else html.P('Inga filer importerade än', style={'fontStyle': 'italic'})
                    ]) if account.imported_files else html.Div()
                ], style={
                    'border': '1px solid #dee2e6',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'marginBottom': '15px',
                    'backgroundColor': '#fff',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
                account_cards.append(card)
            
            return html.Div([
                html.P(f'Totalt {len(accounts)} konto(n) registrerade', 
                      style={'fontWeight': 'bold', 'marginBottom': '20px'}),
                *account_cards
            ])
            
        except Exception as e:
            return html.Div(f'Fel vid hämtning av konton: {str(e)}', style={'color': 'red'})
    
    # Callback för att uppdatera utgiftsfördelning
    @app.callback(
        Output('expense-distribution-graph', 'figure'),
        [Input('forecast-graph', 'id'),
         Input('data-update-trigger', 'data')]
    )
    def update_expense_distribution(_, trigger_value):
        """Uppdaterar utgiftsfördelning per kategori."""
        try:
            transactions = parse_transactions.load_transactions()
            
            if not transactions:
                fig = go.Figure()
                fig.add_annotation(
                    text="Ingen data tillgänglig. Importera transaktioner för att se fördelning.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Gruppera utgifter per kategori (endast negativa belopp)
            category_totals = {}
            for trans in transactions:
                if trans.amount < 0:  # Endast utgifter
                    category = trans.category or 'Okategoriserad'
                    category_totals[category] = category_totals.get(category, 0) + abs(float(trans.amount))
            
            if not category_totals:
                fig = go.Figure()
                fig.add_annotation(
                    text="Inga utgifter att visa",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Sortera kategorier efter storlek
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            categories = [cat for cat, _ in sorted_categories]
            amounts = [amt for _, amt in sorted_categories]
            
            # Skapa färgschema
            colors = px.colors.qualitative.Set3[:len(categories)]
            
            # Skapa cirkeldiagram
            fig = go.Figure(data=[go.Pie(
                labels=categories,
                values=amounts,
                hole=0.3,
                marker=dict(colors=colors),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>%{value:.2f} SEK<br>%{percent}<extra></extra>'
            )])
            
            fig.update_layout(
                title='Utgiftsfördelning per kategori',
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Fel: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    # Callback för att ta bort en fil från ett konto
    @app.callback(
        [Output('account-action-feedback', 'children'),
         Output('accounts-container', 'children', allow_duplicate=True)],
        Input({'type': 'delete-file', 'account': ALL, 'filename': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def delete_file_callback(n_clicks_list):
        """Ta bort en importerad fil från ett konto."""
        from . import account_manager
        from dash import ctx
        
        if not ctx.triggered or not any(n_clicks_list):
            return html.Div(), update_accounts_display(0, None)
        
        # I pattern-matching callbacks (Dash >=2.0), ctx.triggered_id är redan en dictionary
        # (med nycklar som 'type', 'account', 'filename'). I äldre Dash-versioner eller
        # icke-pattern-matching callbacks kan detta vara en JSON-sträng istället.
        # Här kan vi alltså använda ctx.triggered_id direkt som en dict.
        button_data = ctx.triggered_id
        
        if not button_data:
            return html.Div(), update_accounts_display(0, None)
        
        account_name = button_data['account']
        filename = button_data['filename']
        
        # Ta bort filen
        success = account_manager.delete_imported_file(account_name, filename)
        
        if success:
            feedback = html.Div([
                html.Span('✅ ', style={'fontSize': '20px'}),
                html.Span(f'Fil "{filename}" borttagen från konto "{account_name}"')
            ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
        else:
            feedback = html.Div([
                html.Span('❌ ', style={'fontSize': '20px'}),
                html.Span(f'Kunde inte ta bort fil "{filename}"')
            ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
        
        return feedback, update_accounts_display(0, None)
    
    # Callback för att ta bort ett helt konto
    @app.callback(
        [Output('account-action-feedback', 'children', allow_duplicate=True),
         Output('accounts-container', 'children', allow_duplicate=True)],
        Input({'type': 'delete-account', 'account': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def delete_account_callback(n_clicks_list):
        """Ta bort ett helt konto."""
        from . import account_manager
        from dash import ctx
        
        if not ctx.triggered or not any(n_clicks_list):
            return html.Div(), update_accounts_display(0, None)
        
        # Använd ctx.triggered_id direkt för pattern-matching callbacks
        # Det är redan en dictionary, inte en JSON-sträng
        button_data = ctx.triggered_id
        
        if not button_data:
            return html.Div(), update_accounts_display(0, None)
        
        account_name = button_data['account']
        
        # Ta bort kontot
        success = account_manager.delete_account(account_name)
        
        if success:
            feedback = html.Div([
                html.Span('✅ ', style={'fontSize': '20px'}),
                html.Span(f'Konto "{account_name}" har tagits bort helt')
            ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
        else:
            feedback = html.Div([
                html.Span('❌ ', style={'fontSize': '20px'}),
                html.Span(f'Kunde inte ta bort konto "{account_name}"')
            ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
        
        return feedback, update_accounts_display(0, None)
    
    # Callback för att rensa alla konton
    @app.callback(
        [Output('account-action-feedback', 'children', allow_duplicate=True),
         Output('accounts-container', 'children', allow_duplicate=True)],
        Input('clear-all-accounts-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def clear_all_accounts_callback(n_clicks):
        """Rensa alla konton."""
        from . import account_manager
        
        if not n_clicks:
            return html.Div(), update_accounts_display(0, None)
        
        # Rensa alla konton
        account_manager.clear_all_accounts()
        
        feedback = html.Div([
            html.Span('✅ ', style={'fontSize': '20px'}),
            html.Span('Alla konton har rensats')
        ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
        
        return feedback, update_accounts_display(0, None)
    
    # Callback för att uppdatera konto-dropdowns i faktura- och inkomstformulär
    @app.callback(
        [Output('bill-account', 'options'),
         Output('income-account', 'options'),
         Output('edit-bill-account', 'options')],
        [Input('refresh-accounts-button', 'n_clicks'),
         Input('data-update-trigger', 'data'),
         Input('bill-account', 'id'),  # Trigger on page load
         Input('income-account', 'id'),  # Trigger on page load
         Input('edit-bill-account', 'id')]  # Trigger on page load
    )
    def update_account_dropdowns(refresh_clicks, trigger, bill_id, income_id, edit_bill_id):
        """Uppdaterar konto-dropdowns med aktuella konton."""
        try:
            from . import account_manager
            
            accounts = account_manager.load_accounts()
            
            if not accounts:
                return [], [], []
            
            # Skapa options-lista från konton
            account_options = [
                {'label': account_name, 'value': account_name}
                for account_name in sorted(accounts.keys())
            ]
            
            return account_options, account_options, account_options
            
        except Exception as e:
            print(f"Fel vid hämtning av konton för dropdowns: {e}")
            return [], [], []
    
    # Callback för att uppdatera fakturaöversikt
    @app.callback(
        Output('bills-container', 'children'),
        [Input('refresh-bills-button', 'n_clicks'),
         Input('bills-container', 'id'),  # Trigger on page load
         Input('data-update-trigger', 'data')]
    )
    def update_bills_display(n_clicks, _, trigger):
        """Uppdaterar visningen av alla fakturor."""
        try:
            bills = upcoming_bills.get_all_bills()
            
            if not bills:
                return html.Div([
                    html.P('Inga fakturor registrerade än. Lägg till fakturor under fliken "Inmatning".',
                          style={'fontStyle': 'italic', 'color': '#666'})
                ])
            
            # Sortera efter förfallodatum
            bills.sort(key=lambda b: b.due_date)
            
            # Skapa kort för varje faktura
            bill_cards = []
            for bill in bills:
                status_color = '#28a745' if bill.paid else '#dc3545'
                status_text = 'Betald' if bill.paid else 'Obetald'
                recurring_text = f" ({bill.frequency})" if bill.recurring else ""
                
                card = html.Div([
                    html.Div([
                        html.H4(bill.name, style={'marginBottom': '10px', 'color': '#007bff', 'display': 'inline-block'}),
                        html.Span(status_text, style={
                            'marginLeft': '10px',
                            'padding': '4px 8px',
                            'backgroundColor': status_color,
                            'color': 'white',
                            'borderRadius': '4px',
                            'fontSize': '12px',
                            'fontWeight': 'bold'
                        })
                    ]),
                    html.P([
                        html.Strong('Belopp: '),
                        html.Span(f'{bill.amount:,.2f} SEK', style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#dc3545'})
                    ]),
                    html.P([
                        html.Strong('Förfallodatum: '),
                        html.Span(str(bill.due_date))
                    ]),
                    html.P([
                        html.Strong('Kategori: '),
                        html.Span(bill.category)
                    ]),
                    html.P([
                        html.Strong('Konto: '),
                        html.Span(bill.account if bill.account else 'Ej angivet', 
                                 style={'color': '#666' if not bill.account else 'inherit'})
                    ]),
                    html.P([
                        html.Strong('Återkommande: '),
                        html.Span(f'Ja{recurring_text}' if bill.recurring else 'Nej')
                    ]),
                    html.Div([
                        html.Button('Redigera', 
                                   id={'type': 'edit-bill', 'name': bill.name, 'due_date': str(bill.due_date)},
                                   n_clicks=0,
                                   style={
                                       'marginRight': '10px',
                                       'backgroundColor': '#007bff',
                                       'color': 'white',
                                       'border': 'none',
                                       'padding': '6px 12px',
                                       'borderRadius': '5px',
                                       'cursor': 'pointer'
                                   }),
                        html.Button('Ta bort', 
                                   id={'type': 'delete-bill', 'name': bill.name, 'due_date': str(bill.due_date)},
                                   n_clicks=0,
                                   style={
                                       'backgroundColor': '#dc3545',
                                       'color': 'white',
                                       'border': 'none',
                                       'padding': '6px 12px',
                                       'borderRadius': '5px',
                                       'cursor': 'pointer'
                                   })
                    ], style={'marginTop': '10px'})
                ], style={
                    'border': '1px solid #dee2e6',
                    'borderRadius': '10px',
                    'padding': '20px',
                    'marginBottom': '15px',
                    'backgroundColor': '#fff',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
                bill_cards.append(card)
            
            return html.Div([
                html.P(f'Totalt {len(bills)} faktura(or) registrerade', 
                      style={'fontWeight': 'bold', 'marginBottom': '20px'}),
                *bill_cards
            ])
            
        except Exception as e:
            return html.Div(f'Fel vid hämtning av fakturor: {str(e)}', style={'color': 'red'})
    
    # Callback för att ta bort en faktura
    @app.callback(
        [Output('bill-action-feedback', 'children'),
         Output('bills-container', 'children', allow_duplicate=True)],
        Input({'type': 'delete-bill', 'name': ALL, 'due_date': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def delete_bill_callback(n_clicks_list):
        """Ta bort en faktura."""
        from dash import ctx
        
        if not ctx.triggered or not any(n_clicks_list):
            return html.Div(), update_bills_display(0, None, 0)
        
        button_data = ctx.triggered_id
        
        if not button_data:
            return html.Div(), update_bills_display(0, None, 0)
        
        bill_name = button_data['name']
        bill_due_date = button_data['due_date']
        
        # Ta bort fakturan
        success = upcoming_bills.delete_bill(bill_name, bill_due_date)
        
        if success:
            feedback = html.Div([
                html.Span('✅ ', style={'fontSize': '20px'}),
                html.Span(f'Faktura "{bill_name}" har tagits bort')
            ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
        else:
            feedback = html.Div([
                html.Span('❌ ', style={'fontSize': '20px'}),
                html.Span(f'Kunde inte ta bort faktura "{bill_name}"')
            ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
        
        return feedback, update_bills_display(0, None, 0)
    
    # Callback för att öppna redigeringsdialog
    @app.callback(
        [Output('edit-bill-dialog', 'style'),
         Output('edit-bill-name', 'value'),
         Output('edit-bill-amount', 'value'),
         Output('edit-bill-due-date', 'date'),
         Output('edit-bill-category', 'value'),
         Output('edit-bill-account', 'value'),
         Output('edit-bill-original-data', 'data')],
        [Input({'type': 'edit-bill', 'name': ALL, 'due_date': ALL}, 'n_clicks'),
         Input('cancel-bill-edit-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def toggle_edit_dialog(edit_clicks, cancel_clicks):
        """Öppnar eller stänger redigeringsdialogen."""
        from dash import ctx
        
        if not ctx.triggered:
            raise PreventUpdate
        
        triggered_id = ctx.triggered[0]['prop_id']
        
        # Om cancel-knappen trycktes, stäng dialogen
        if 'cancel-bill-edit-button' in triggered_id:
            return {'display': 'none'}, '', None, None, None, None, None
        
        # Om edit-knappen trycktes, öppna dialogen
        if not any(edit_clicks):
            raise PreventUpdate
        
        button_data = ctx.triggered_id
        
        if not button_data:
            raise PreventUpdate
        
        bill_name = button_data['name']
        bill_due_date = button_data['due_date']
        
        # Hämta fakturan
        bills = upcoming_bills.get_all_bills()
        target_bill = None
        for bill in bills:
            if bill.name == bill_name and str(bill.due_date) == bill_due_date:
                target_bill = bill
                break
        
        if not target_bill:
            return {'display': 'none'}, '', None, None, None, None, None
        
        # Returnera dialogstil och fakturadata
        return (
            {'display': 'block'},
            target_bill.name,
            float(target_bill.amount),
            str(target_bill.due_date),
            target_bill.category,
            target_bill.account,
            {'name': bill_name, 'due_date': bill_due_date}
        )
    
    # Callback för att spara redigerad faktura
    @app.callback(
        [Output('bill-action-feedback', 'children', allow_duplicate=True),
         Output('bills-container', 'children', allow_duplicate=True),
         Output('edit-bill-dialog', 'style', allow_duplicate=True)],
        Input('save-bill-edit-button', 'n_clicks'),
        [State('edit-bill-name', 'value'),
         State('edit-bill-amount', 'value'),
         State('edit-bill-due-date', 'date'),
         State('edit-bill-category', 'value'),
         State('edit-bill-account', 'value'),
         State('edit-bill-original-data', 'data')],
        prevent_initial_call=True
    )
    def save_bill_edit(n_clicks, name, amount, due_date, category, account, original_data):
        """Sparar ändringar i en faktura."""
        if not n_clicks or not original_data:
            raise PreventUpdate
        
        try:
            from datetime import datetime
            from decimal import Decimal
            from .models import Bill
            
            # Skapa uppdaterad faktura
            updated_bill = Bill(
                name=name,
                amount=Decimal(str(amount)),
                due_date=datetime.fromisoformat(due_date).date(),
                category=category,
                account=account,
                recurring=False
            )
            
            # Uppdatera fakturan
            success = upcoming_bills.update_bill(
                original_data['name'],
                original_data['due_date'],
                updated_bill
            )
            
            if success:
                feedback = html.Div([
                    html.Span('✅ ', style={'fontSize': '20px'}),
                    html.Span(f'Faktura "{name}" har uppdaterats')
                ], style={'color': 'green', 'padding': '10px', 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
            else:
                feedback = html.Div([
                    html.Span('❌ ', style={'fontSize': '20px'}),
                    html.Span(f'Kunde inte uppdatera faktura "{name}"')
                ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
            
            return feedback, update_bills_display(0, None, 0), {'display': 'none'}
            
        except Exception as e:
            feedback = html.Div([
                html.Span('❌ ', style={'fontSize': '20px'}),
                html.Span(f'Fel vid uppdatering: {str(e)}')
            ], style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
            return feedback, update_bills_display(0, None, 0), {'display': 'none'}
    
    # Callback för att uppdatera account selector
    @app.callback(
        Output('account-selector', 'options'),
        Input('refresh-accounts-button', 'n_clicks')
    )
    def update_account_options(n_clicks):
        """Uppdaterar listan över konton i dropdown."""
        from . import api
        
        accounts = api.list_accounts()
        options = [
            {'label': f"{acc['account_name']} ({acc['transaction_count']} tx)", 
             'value': acc['account_name']}
            for acc in accounts
        ]
        return options
    
    # Callback för att visa kontostatistik
    @app.callback(
        Output('account-stats', 'children'),
        Input('account-selector', 'value')
    )
    def display_account_stats(account_name):
        """Visar statistik för valt konto."""
        if not account_name:
            return html.P("Välj ett konto för att se statistik.")
        
        from . import account_manager
        
        accounts = account_manager.load_accounts()
        if account_name not in accounts:
            return html.P("Kontot hittades inte.")
        
        account = accounts[account_name]
        
        return html.Div([
            html.H4(f"📊 Statistik för {account_name}"),
            html.Ul([
                html.Li(f"Importerade filer: {len(account.imported_files)}"),
                html.Li(f"Antal transaktioner: {len(account.transaction_hashes)}"),
                html.Li(f"Senaste import: {account.last_import_date.strftime('%Y-%m-%d %H:%M') if account.last_import_date else 'Aldrig'}"),
                html.Li(f"Aktuellt saldo: {account.current_balance} {account.balance_currency}" if account.current_balance else "Saldo: Ej tillgängligt"),
            ])
        ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px'})
    
    # Callback för träningsstatistik
    @app.callback(
        Output('training-stats', 'children'),
        Input('refresh-accounts-button', 'n_clicks')
    )
    def display_training_stats(n_clicks):
        """Visar statistik om träningsdata."""
        from . import api
        
        stats = api.get_training_data_stats()
        
        if stats['total_examples'] == 0:
            return html.Div([
                html.P("🤖 Ingen träningsdata ännu. Börja träna AI-modellen genom att välja kategorier och klicka 'Träna AI med valda'.")
            ], style={'backgroundColor': '#fff3cd', 'padding': '15px', 'borderRadius': '5px'})
        
        category_items = [
            html.Li(f"{cat}: {count} exempel")
            for cat, count in stats['categories'].items()
        ]
        
        return html.Div([
            html.H4(f"🤖 AI-träningsdata"),
            html.P(f"Totalt antal exempel: {stats['total_examples']}"),
            html.P(f"Antal kategorier: {stats['unique_categories']}"),
            html.Details([
                html.Summary("Visa fördelning per kategori"),
                html.Ul(category_items)
            ])
        ], style={'backgroundColor': '#d1ecf1', 'padding': '15px', 'borderRadius': '5px'})
    
    # Callback för att växla visning av ny kategori-formulär
    @app.callback(
        [Output('new-category-name', 'style'),
         Output('new-category-keywords', 'style'),
         Output('save-new-category-btn', 'style')],
        Input('create-category-btn', 'n_clicks'),
        State('new-category-name', 'style')
    )
    def toggle_category_form(n_clicks, current_style):
        """Växlar visning av formulär för ny kategori."""
        if n_clicks and n_clicks > 0:
            # Växla synlighet
            is_hidden = current_style.get('display') == 'none'
            new_style = {'marginRight': '10px'} if is_hidden else {'display': 'none'}
            return new_style, new_style, new_style
        return ({'display': 'none'}, {'display': 'none'}, {'display': 'none'})
    
    # Callback för att spara ny kategori
    @app.callback(
        Output('categorization-feedback', 'children'),
        Input('save-new-category-btn', 'n_clicks'),
        [State('new-category-name', 'value'),
         State('new-category-keywords', 'value')],
        prevent_initial_call=True
    )
    def save_new_category(n_clicks, name, keywords):
        """Sparar ny kategori."""
        if not name or not keywords:
            return html.Div("❌ Fyll i både kategorinamn och nyckelord.",
                          style={'color': 'red', 'padding': '10px'})
        
        from . import api
        
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        result = api.create_category(name, keyword_list)
        
        if result['success']:
            return html.Div(f"✅ {result['message']}",
                          style={'color': 'green', 'padding': '10px', 
                                 'backgroundColor': '#d4edda', 'borderRadius': '5px'})
        else:
            return html.Div(f"❌ Fel: {result.get('error', 'Okänt fel')}",
                          style={'color': 'red', 'padding': '10px',
                                 'backgroundColor': '#f8d7da', 'borderRadius': '5px'})
    
    # Kör server
    app.run(debug=True, host='0.0.0.0', port=8050)
