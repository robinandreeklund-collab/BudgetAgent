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
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from .models import Transaction, Bill, Income, ForecastData
from . import upcoming_bills, income_tracker, forecast_engine, alerts_and_insights, query_parser


def create_app_layout() -> html.Div:
    """
    Skapar huvudlayout för Dash-applikationen.
    
    Strukturerar hela gränssnittet med alla paneler och komponenter.
    
    Returns:
        Dash html.Div med komplett layout
    """
    return html.Div([
        html.H1("💸 BudgetAgent Dashboard", style={'textAlign': 'center'}),
        
        # Flikar för olika sektioner
        dcc.Tabs([
            dcc.Tab(label='Översikt', children=[
                html.Div([
                    create_forecast_section(),
                    create_insights_section()
                ])
            ]),
            dcc.Tab(label='Inmatning', children=[
                html.Div([
                    input_panel()
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
            html.Button('Lägg till faktura', id='add-bill-button', n_clicks=0)
        ], style={'marginBottom': '20px'}),
        
        # Inkomstinmatning
        html.H3("Ny inkomst"),
        html.Div([
            dcc.Input(id='income-person', type='text', placeholder='Person'),
            dcc.Input(id='income-source', type='text', placeholder='Källa'),
            dcc.Input(id='income-amount', type='number', placeholder='Belopp'),
            dcc.DatePickerSingle(id='income-date', placeholder='Datum'),
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
    return html.Div([
        html.H2("Inställningar"),
        
        html.H3("Import"),
        dcc.Dropdown(
            id='import-format',
            options=[
                {'label': 'Swedbank CSV', 'value': 'swedbank'},
                {'label': 'SEB Excel', 'value': 'seb'},
                {'label': 'Revolut JSON', 'value': 'revolut'}
            ],
            placeholder='Välj importformat'
        ),
        
        html.H3("Prognos"),
        html.Label("Prognosfönster (månader):"),
        dcc.Slider(
            id='forecast-window',
            min=1,
            max=12,
            value=6,
            marks={i: str(i) for i in range(1, 13)}
        ),
        
        html.H3("Fördelningsregel"),
        dcc.Dropdown(
            id='split-rule',
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
            id='alert-threshold',
            min=0,
            max=100,
            value=80,
            marks={i: f'{i}%' for i in range(0, 101, 20)}
        ),
        
        html.H3("Debug"),
        dcc.Checklist(
            id='show-debug',
            options=[{'label': 'Visa debug-panel', 'value': 'debug'}],
            value=['debug']
        ),
        
        html.Button('Spara inställningar', id='save-settings-button', n_clicks=0),
        html.Div(id='settings-feedback')
    ], style={'padding': '20px'})


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
    
    app = Dash(__name__)
    app.layout = create_app_layout()
    
    # Callback för att uppdatera prognos-grafen vid sidladdning
    @app.callback(
        Output('forecast-graph', 'figure'),
        Input('forecast-graph', 'id')  # Trigger vid laddning
    )
    def update_forecast(_):
        """Uppdaterar prognosgrafen."""
        try:
            forecast_data = forecast_engine.simulate_monthly_balance(6)
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
        prevent_initial_call=True
    )
    def add_bill_callback(n_clicks, name, amount, due_date, category):
        """Lägger till en ny faktura."""
        if n_clicks and name and amount and due_date and category:
            try:
                bill = Bill(
                    name=name,
                    amount=Decimal(str(amount)),
                    due_date=datetime.fromisoformat(due_date).date(),
                    category=category,
                    recurring=False
                )
                upcoming_bills.add_bill(bill)
                return html.Div(f"✅ Faktura '{name}' tillagd!", style={'color': 'green'})
            except Exception as e:
                return html.Div(f"❌ Fel: {str(e)}", style={'color': 'red'})
        return html.Div("Fyll i alla fält", style={'color': 'orange'})
    
    # Callback för att lägga till inkomst
    @app.callback(
        Output('input-feedback', 'children', allow_duplicate=True),
        Input('add-income-button', 'n_clicks'),
        State('income-person', 'value'),
        State('income-source', 'value'),
        State('income-amount', 'value'),
        State('income-date', 'date'),
        State('income-recurring', 'value'),
        prevent_initial_call=True
    )
    def add_income_callback(n_clicks, person, source, amount, date, recurring):
        """Lägger till en ny inkomst."""
        if n_clicks and person and source and amount and date:
            try:
                income = Income(
                    person=person,
                    source=source,
                    amount=Decimal(str(amount)),
                    date=datetime.fromisoformat(date).date(),
                    recurring='recurring' in (recurring or []),
                    frequency='monthly' if 'recurring' in (recurring or []) else None
                )
                income_tracker.add_income(income)
                return html.Div(f"✅ Inkomst för '{person}' tillagd!", style={'color': 'green'})
            except Exception as e:
                return html.Div(f"❌ Fel: {str(e)}", style={'color': 'red'})
        return html.Div("Fyll i alla fält", style={'color': 'orange'})
    
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
         Output('insights-container', 'children')],
        Input('forecast-graph', 'id')  # Trigger vid laddning
    )
    def update_insights(_):
        """Uppdaterar insikter och varningar."""
        try:
            # Hämta historiska transaktioner (placeholder)
            # I en riktig implementation skulle vi ladda faktiska transaktioner
            alerts_list = ["Inga varningar för tillfället"]
            insights_list = ["Ladda transaktionsdata för att se insikter"]
            
            alerts_div = html.Div([
                html.H4("⚠️ Varningar"),
                html.Ul([html.Li(alert) for alert in alerts_list])
            ])
            
            insights_div = html.Div([
                html.H4("💡 Insikter"),
                html.Ul([html.Li(insight) for insight in insights_list])
            ])
            
            return alerts_div, insights_div
        except Exception as e:
            return html.Div(f"Fel: {e}"), html.Div()
    
    # Kör server
    app.run(debug=True, host='0.0.0.0', port=8050)
