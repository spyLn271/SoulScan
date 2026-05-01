"""
Exchange plugins for the cryptocurrency orderbook monitoring system.

Each exchange has its own plugin that inherits from BaseExchangeConnector
and implements exchange-specific functionality while leveraging shared infrastructure.
"""

# Import all exchange plugins
# These will be created as we convert each exchange to the plugin architecture