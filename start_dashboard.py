#!/usr/bin/env python3
"""
Startup script för BudgetAgent Dashboard.

Detta script startar Dash-webbapplikationen som tillhandahåller
det interaktiva gränssnittet för BudgetAgent.

Användning:
    python start_dashboard.py

Dashboard öppnas automatiskt på http://localhost:8050
"""

import sys
from pathlib import Path

# Lägg till budgetagent till Python-sökvägen
sys.path.insert(0, str(Path(__file__).parent))

from budgetagent.modules.dashboard_ui import render_dashboard

if __name__ == "__main__":
    print("=" * 60)
    print("💸 Startar BudgetAgent Dashboard...")
    print("=" * 60)
    print()
    print("Dashboard kommer att vara tillgänglig på:")
    print("  http://localhost:8050")
    print()
    print("Tryck Ctrl+C för att stoppa servern")
    print("=" * 60)
    print()
    
    try:
        render_dashboard()
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard stoppad")
    except Exception as e:
        print(f"\n\n❌ Fel vid start av dashboard: {e}")
        sys.exit(1)
