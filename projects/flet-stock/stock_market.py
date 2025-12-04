import flet as ft
import random
import time
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional
import math

# Mock stock data model
class Stock:
    def __init__(self, symbol: str, name: str, price: float, change: float = 0.0, volume: int = 0):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.change = change
        self.change_percent = (change / (price - change)) * 100 if price - change != 0 else 0
        self.volume = volume
        self.market_cap = random.randint(10, 500) * 1e9  # Billions
        self.pe_ratio = round(random.uniform(10, 50), 2)
        self.sector = random.choice(["Technology", "Finance", "Healthcare", "Energy", "Consumer"])
        self.history = self.generate_price_history(price)
        
    def generate_price_history(self, current_price: float) -> List[float]:
        """Generate 30 days of historical price data"""
        history = []
        price = current_price * random.uniform(0.8, 1.2)  # Start from random point
        for _ in range(30):
            price = max(1, price * random.uniform(0.98, 1.02))
            history.append(round(price, 2))
        history[-1] = current_price  # Ensure last price matches current
        return history

# Mock portfolio holding
class PortfolioHolding:
    def __init__(self, stock: Stock, shares: int, purchase_price: float):
        self.stock = stock
        self.shares = shares
        self.purchase_price = purchase_price
        self.current_value = shares * stock.price
        self.total_cost = shares * purchase_price
        self.gain_loss = self.current_value - self.total_cost
        self.gain_loss_percent = (self.gain_loss / self.total_cost) * 100 if self.total_cost > 0 else 0

# Mock backend service
class StockMarketBackend:
    def __init__(self):
        self.stocks = self.initialize_stocks()
        self.watchlist = ["AAPL", "GOOGL", "TSLA", "AMZN", "MSFT", "NVDA"]
        self.portfolio = self.initialize_portfolio()
        self.transaction_history = []
        self.user_balance = 100000.0
        
    def initialize_stocks(self) -> Dict[str, Stock]:
        """Initialize with popular stocks"""
        stocks_data = [
            ("AAPL", "Apple Inc.", 182.63, 1.25),
            ("GOOGL", "Alphabet Inc.", 141.12, -0.75),
            ("MSFT", "Microsoft Corp", 407.81, 2.15),
            ("AMZN", "Amazon.com Inc.", 174.49, 0.89),
            ("TSLA", "Tesla Inc.", 175.79, -2.34),
            ("NVDA", "NVIDIA Corp", 903.56, 5.67),
            ("META", "Meta Platforms", 485.75, 1.45),
            ("JPM", "JPMorgan Chase", 191.23, -0.45),
            ("JNJ", "Johnson & Johnson", 151.88, 0.23),
            ("XOM", "Exxon Mobil", 118.34, -1.12),
            ("BAC", "Bank of America", 36.45, 0.15),
            ("WMT", "Walmart Inc.", 60.12, 0.33),
            ("PG", "Procter & Gamble", 161.45, -0.22),
            ("V", "Visa Inc.", 275.89, 0.78),
            ("MA", "Mastercard Inc.", 475.34, 1.12),
        ]
        return {symbol: Stock(symbol, name, price, change) for symbol, name, price, change in stocks_data}
    
    def initialize_portfolio(self) -> Dict[str, PortfolioHolding]:
        """Initialize sample portfolio"""
        portfolio = {}
        sample_stocks = ["AAPL", "MSFT", "NVDA", "TSLA", "JPM"]
        for symbol in sample_stocks:
            stock = self.stocks[symbol]
            shares = random.randint(10, 100)
            purchase_price = stock.price * random.uniform(0.8, 1.1)
            portfolio[symbol] = PortfolioHolding(stock, shares, purchase_price)
        return portfolio
    
    def get_watchlist_stocks(self) -> List[Stock]:
        """Get stocks in watchlist"""
        return [self.stocks[symbol] for symbol in self.watchlist if symbol in self.stocks]
    
    def get_top_gainers(self) -> List[Stock]:
        """Get top 5 gaining stocks"""
        all_stocks = list(self.stocks.values())
        all_stocks.sort(key=lambda x: x.change_percent, reverse=True)
        return all_stocks[:5]
    
    def get_top_losers(self) -> List[Stock]:
        """Get top 5 losing stocks"""
        all_stocks = list(self.stocks.values())
        all_stocks.sort(key=lambda x: x.change_percent)
        return all_stocks[:5]
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        return sum(holding.current_value for holding in self.portfolio.values())
    
    def get_portfolio_gain_loss(self) -> tuple:
        """Calculate total portfolio gain/loss"""
        total_cost = sum(holding.total_cost for holding in self.portfolio.values())
        total_value = self.get_portfolio_value()
        gain_loss = total_value - total_cost
        gain_loss_percent = (gain_loss / total_cost) * 100 if total_cost > 0 else 0
        return total_value, gain_loss, gain_loss_percent
    
    def buy_stock(self, symbol: str, shares: int) -> bool:
        """Simulate buying stocks"""
        if symbol not in self.stocks:
            return False
        
        cost = self.stocks[symbol].price * shares
        if cost > self.user_balance:
            return False
        
        self.user_balance -= cost
        
        if symbol in self.portfolio:
            holding = self.portfolio[symbol]
            total_shares = holding.shares + shares
            avg_price = ((holding.total_cost) + cost) / total_shares
            holding.shares = total_shares
            holding.purchase_price = avg_price
            holding.total_cost = total_shares * avg_price
        else:
            stock = self.stocks[symbol]
            self.portfolio[symbol] = PortfolioHolding(stock, shares, stock.price)
        
        # Record transaction
        self.transaction_history.append({
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': self.stocks[symbol].price,
            'total': cost,
            'timestamp': datetime.now()
        })
        
        self.update_portfolio_values()
        return True
    
    def sell_stock(self, symbol: str, shares: int) -> bool:
        """Simulate selling stocks"""
        if symbol not in self.portfolio:
            return False
        
        holding = self.portfolio[symbol]
        if holding.shares < shares:
            return False
        
        proceeds = self.stocks[symbol].price * shares
        self.user_balance += proceeds
        
        if holding.shares == shares:
            del self.portfolio[symbol]
        else:
            holding.shares -= shares
            holding.total_cost = holding.shares * holding.purchase_price
        
        # Record transaction
        self.transaction_history.append({
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': self.stocks[symbol].price,
            'total': proceeds,
            'timestamp': datetime.now()
        })
        
        self.update_portfolio_values()
        return True
    
    def update_portfolio_values(self):
        """Update portfolio values with current prices"""
        for holding in self.portfolio.values():
            holding.current_value = holding.shares * holding.stock.price
            holding.gain_loss = holding.current_value - holding.total_cost
            holding.gain_loss_percent = (holding.gain_loss / holding.total_cost) * 100 if holding.total_cost > 0 else 0
    
    def update_stock_prices(self):
        """Simulate random stock price movements"""
        for stock in self.stocks.values():
            # Random price change between -2% and +2%
            change_factor = random.uniform(0.98, 1.02)
            old_price = stock.price
            stock.price = round(stock.price * change_factor, 2)
            stock.change = round(stock.price - old_price, 2)
            stock.change_percent = round((stock.change / old_price) * 100, 2)
            
            # Update volume
            stock.volume = random.randint(1000000, 50000000)
            
            # Update history
            stock.history.append(stock.price)
            if len(stock.history) > 30:
                stock.history.pop(0)
        
        # Update portfolio values
        self.update_portfolio_values()

def main(page: ft.Page):
    page.title = "Stock Market Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1400
    page.window_height = 900
    page.window_min_width = 1000
    page.window_min_height = 700
    page.padding = 20
    
    # Initialize backend
    backend = StockMarketBackend()
    
    # Custom theme colors
    theme = {
        'primary': ft.Colors.BLUE_700,
        'secondary': ft.Colors.GREY_800,
        'success': ft.Colors.GREEN_700,
        'danger': ft.Colors.RED_700,
        'warning': ft.Colors.ORANGE_700,
        'text': ft.Colors.WHITE,
        'subtext': ft.Colors.GREY_400,
        'bg': ft.Colors.GREY_900,
        'card_bg': ft.Colors.GREY_800,
    }
    
    # Current time display
    current_time = ft.Text(
        datetime.now().strftime("%H:%M:%S"),
        size=12,
        color=theme['subtext']
    )
    
    # Status bar
    status_bar = ft.Text(
        "Market Open • Live data",
        size=12,
        color=theme['success']
    )
    
    # Search bar
    search_bar = ft.TextField(
        label="Search stocks...",
        prefix_icon=ft.Icons.SEARCH,
        width=300,
        border_color=theme['subtext'],
        focused_border_color=theme['primary']
    )
    
    def update_time():
        """Update current time every second"""
        while True:
            time.sleep(1)
            if page:
                current_time.value = datetime.now().strftime("%H:%M:%S")
                page.update()
    
    def update_stock_prices():
        """Update stock prices periodically"""
        while True:
            time.sleep(3)  # Update every 3 seconds
            backend.update_stock_prices()
            if page:
                # Update all UI components
                update_watchlist()
                update_market_overview()
                update_portfolio_summary()
                update_top_movers()
                page.update()
    
    # Start background threads
    threading.Thread(target=update_time, daemon=True).start()
    threading.Thread(target=update_stock_prices, daemon=True).start()
    
    def create_stock_card(stock: Stock):
        """Create a stock card widget"""
        change_color = theme['success'] if stock.change >= 0 else theme['danger']
        change_icon = ft.Icons.TRENDING_UP if stock.change >= 0 else ft.Icons.TRENDING_DOWN
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(stock.symbol, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(stock.name, size=12, color=theme['subtext']),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"${stock.price:.2f}", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(change_icon, size=14, color=change_color),
                                            ft.Text(f"{stock.change:+.2f} ({stock.change_percent:+.2f}%)", 
                                                   size=12, color=change_color),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Volume", size=10, color=theme['subtext']),
                                    ft.Text(f"{stock.volume:,}", size=12),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("P/E", size=10, color=theme['subtext']),
                                    ft.Text(f"{stock.pe_ratio}", size=12),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Sector", size=10, color=theme['subtext']),
                                    ft.Text(stock.sector, size=12),
                                ],
                                expand=True,
                            ),
                        ],
                    ),
                ],
                spacing=5,
            ),
            padding=15,
            border=ft.border.all(1, theme['secondary']),
            border_radius=10,
            bgcolor=theme['card_bg'],
            on_click=lambda e: show_stock_detail(stock),
        )
    
    def create_portfolio_card(holding: PortfolioHolding):
        """Create a portfolio holding card"""
        gain_color = theme['success'] if holding.gain_loss >= 0 else theme['danger']
        gain_icon = ft.Icons.TRENDING_UP if holding.gain_loss >= 0 else ft.Icons.TRENDING_DOWN
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(holding.stock.symbol, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{holding.shares} shares", size=12, color=theme['subtext']),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"${holding.current_value:,.2f}", size=16),
                                    ft.Row(
                                        controls=[
                                            ft.Icon(gain_icon, size=14, color=gain_color),
                                            ft.Text(f"{holding.gain_loss:+.2f} ({holding.gain_loss_percent:+.2f}%)", 
                                                   size=12, color=gain_color),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Avg Price", size=10, color=theme['subtext']),
                                    ft.Text(f"${holding.purchase_price:.2f}", size=12),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Current", size=10, color=theme['subtext']),
                                    ft.Text(f"${holding.stock.price:.2f}", size=12),
                                ],
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Buy",
                                icon=ft.Icons.ADD,
                                on_click=lambda e, s=holding.stock.symbol: show_trade_dialog(s, "buy"),
                                style=ft.ButtonStyle(
                                    color=theme['text'],
                                    bgcolor=theme['success'],
                                    padding=ft.padding.symmetric(horizontal=15, vertical=5),
                                ),
                                height=30,
                            ),
                            ft.ElevatedButton(
                                "Sell",
                                icon=ft.Icons.REMOVE,
                                on_click=lambda e, s=holding.stock.symbol: show_trade_dialog(s, "sell"),
                                style=ft.ButtonStyle(
                                    color=theme['text'],
                                    bgcolor=theme['danger'],
                                    padding=ft.padding.symmetric(horizontal=15, vertical=5),
                                ),
                                height=30,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=5,
            ),
            padding=15,
            border=ft.border.all(1, theme['secondary']),
            border_radius=10,
            bgcolor=theme['card_bg'],
        )
    
    def create_price_chart(prices: List[float]):
        """Create a simple price chart"""
        if not prices:
            return ft.Container(height=100)
        
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # Create line chart points
        points = []
        for i, price in enumerate(prices):
            x = (i / (len(prices) - 1)) * 200 if len(prices) > 1 else 100
            y = 100 - ((price - min_price) / price_range * 90) if price_range > 0 else 50
            points.append(ft.Offset(x, y))
        
        # Determine line color based on price trend
        line_color = theme['success'] if prices[-1] >= prices[0] else theme['danger']
        
        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.LineChart(
                            data_series=[
                                ft.LineChartData(
                                    data_points=points,
                                    stroke_width=2,
                                    color=line_color,
                                    curved=True,
                                ),
                            ],
                            border=None,
                            left_axis=ft.ChartAxis(labels_size=0),
                            bottom_axis=ft.ChartAxis(labels_size=0),
                            horizontal_grid_lines=ft.ChartGridLines(
                                color=ft.Colors.with_opacity(0.1, theme['text']),
                                width=1,
                            ),
                            vertical_grid_lines=ft.ChartGridLines(
                                color=ft.Colors.with_opacity(0.1, theme['text']),
                                width=1,
                            ),
                            expand=True,
                        ),
                        height=100,
                        width=200,
                    ),
                ],
            ),
            height=100,
            width=200,
        )
    
    # Watchlist section
    watchlist_title = ft.Text("Watchlist", size=18, weight=ft.FontWeight.BOLD)
    watchlist_grid = ft.GridView(
        expand=True,
        max_extent=300,
        child_aspect_ratio=2,
        spacing=10,
        run_spacing=10,
    )
    
    def update_watchlist():
        """Update watchlist display"""
        watchlist_grid.controls.clear()
        for stock in backend.get_watchlist_stocks():
            watchlist_grid.controls.append(create_stock_card(stock))
        page.update()
    
    # Market overview section
    market_overview_title = ft.Text("Market Overview", size=18, weight=ft.FontWeight.BOLD)
    
    portfolio_value, portfolio_gain, portfolio_gain_percent = backend.get_portfolio_gain_loss()
    portfolio_gain_color = theme['success'] if portfolio_gain >= 0 else theme['danger']
    
    overview_cards = ft.Row(
        controls=[
            # Portfolio Value Card
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Portfolio Value", size=12, color=theme['subtext']),
                        ft.Text(f"${portfolio_value:,.2f}", size=24, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.TRENDING_UP if portfolio_gain >= 0 else ft.Icons.TRENDING_DOWN,
                                    color=portfolio_gain_color,
                                ),
                                ft.Text(
                                    f"{portfolio_gain:+.2f} ({portfolio_gain_percent:+.2f}%)",
                                    color=portfolio_gain_color,
                                ),
                            ],
                            spacing=5,
                        ),
                    ],
                    spacing=5,
                ),
                padding=20,
                border_radius=10,
                bgcolor=theme['card_bg'],
                expand=True,
            ),
            
            # Cash Balance Card
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Cash Balance", size=12, color=theme['subtext']),
                        ft.Text(f"${backend.user_balance:,.2f}", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Available for trading", size=12, color=theme['subtext']),
                    ],
                    spacing=5,
                ),
                padding=20,
                border_radius=10,
                bgcolor=theme['card_bg'],
                expand=True,
            ),
            
            # Market Index Card
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("S&P 500", size=12, color=theme['subtext']),
                        ft.Text("5,145.11", size=24, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.TRENDING_UP, color=theme['success']),
                                ft.Text("+42.37 (+0.83%)", color=theme['success']),
                            ],
                            spacing=5,
                        ),
                    ],
                    spacing=5,
                ),
                padding=20,
                border_radius=10,
                bgcolor=theme['card_bg'],
                expand=True,
            ),
        ],
        spacing=20,
    )
    
    def update_market_overview():
        """Update market overview cards"""
        portfolio_value, portfolio_gain, portfolio_gain_percent = backend.get_portfolio_gain_loss()
        portfolio_gain_color = theme['success'] if portfolio_gain >= 0 else theme['danger']
        
        # Update portfolio value card
        overview_cards.controls[0].content.controls[1].value = f"${portfolio_value:,.2f}"
        overview_cards.controls[0].content.controls[2].controls[0].name = (
            ft.Icons.TRENDING_UP if portfolio_gain >= 0 else ft.Icons.TRENDING_DOWN
        )
        overview_cards.controls[0].content.controls[2].controls[0].color = portfolio_gain_color
        overview_cards.controls[0].content.controls[2].controls[1].value = (
            f"{portfolio_gain:+.2f} ({portfolio_gain_percent:+.2f}%)"
        )
        overview_cards.controls[0].content.controls[2].controls[1].color = portfolio_gain_color
        
        # Update cash balance card
        overview_cards.controls[1].content.controls[1].value = f"${backend.user_balance:,.2f}"
        
        # Randomly update market index
        market_change = random.uniform(-1, 1)
        market_icon = ft.Icons.TRENDING_UP if market_change >= 0 else ft.Icons.TRENDING_DOWN
        market_color = theme['success'] if market_change >= 0 else theme['danger']
        
        overview_cards.controls[2].content.controls[1].value = f"{5145.11 + market_change*50:.2f}"
        overview_cards.controls[2].content.controls[2].controls[0].name = market_icon
        overview_cards.controls[2].content.controls[2].controls[0].color = market_color
        overview_cards.controls[2].content.controls[2].controls[1].value = (
            f"{market_change*50:+.2f} ({market_change:+.2f}%)"
        )
        overview_cards.controls[2].content.controls[2].controls[1].color = market_color
    
    # Portfolio section
    portfolio_title = ft.Text("Your Portfolio", size=18, weight=ft.FontWeight.BOLD)
    portfolio_grid = ft.GridView(
        expand=True,
        max_extent=300,
        child_aspect_ratio=1.5,
        spacing=10,
        run_spacing=10,
    )
    
    def update_portfolio_summary():
        """Update portfolio display"""
        portfolio_grid.controls.clear()
        for holding in backend.portfolio.values():
            portfolio_grid.controls.append(create_portfolio_card(holding))
    
    # Top movers section
    top_movers_title = ft.Text("Top Movers", size=18, weight=ft.FontWeight.BOLD)
    top_movers_container = ft.Column(spacing=10)
    
    def update_top_movers():
        """Update top gainers and losers"""
        top_movers_container.controls.clear()
        
        # Top Gainers
        top_movers_container.controls.append(
            ft.Text("Top Gainers", size=14, weight=ft.FontWeight.BOLD, color=theme['success'])
        )
        for stock in backend.get_top_gainers()[:3]:
            top_movers_container.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(stock.symbol, size=14, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"${stock.price:.2f}", size=14),
                            ft.Text(f"{stock.change_percent:+.2f}%", size=14, color=theme['success']),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=5, horizontal=10),
                    border_radius=5,
                    bgcolor=ft.Colors.with_opacity(0.1, theme['success']),
                )
            )
        
        top_movers_container.controls.append(ft.Divider(height=20))
        
        # Top Losers
        top_movers_container.controls.append(
            ft.Text("Top Losers", size=14, weight=ft.FontWeight.BOLD, color=theme['danger'])
        )
        for stock in backend.get_top_losers()[:3]:
            top_movers_container.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(stock.symbol, size=14, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"${stock.price:.2f}", size=14),
                            ft.Text(f"{stock.change_percent:+.2f}%", size=14, color=theme['danger']),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=5, horizontal=10),
                    border_radius=5,
                    bgcolor=ft.Colors.with_opacity(0.1, theme['danger']),
                )
            )
    
    # Transaction history
    transaction_title = ft.Text("Recent Transactions", size=18, weight=ft.FontWeight.BOLD)
    transaction_list = ft.Column(
        spacing=5,
        scroll=ft.ScrollMode.AUTO,
        height=200,
    )
    
    def update_transaction_history():
        """Update transaction history display"""
        transaction_list.controls.clear()
        for tx in reversed(backend.transaction_history[-10:]):  # Show last 10 transactions
            tx_type_color = theme['success'] if tx['type'] == 'BUY' else theme['danger']
            tx_icon = ft.Icons.ARROW_UPWARD if tx['type'] == 'BUY' else ft.Icons.ARROW_DOWNWARD
            
            transaction_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(tx_icon, color=tx_type_color, size=16),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{tx['type']} {tx['symbol']}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(tx['timestamp'].strftime("%H:%M:%S"), size=10, color=theme['subtext']),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{tx['shares']} shares @ ${tx['price']:.2f}", size=12),
                                    ft.Text(f"${tx['total']:.2f}", size=12, weight=ft.FontWeight.BOLD),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                    ),
                    padding=10,
                    border_radius=5,
                    bgcolor=theme['card_bg'],
                )
            )
    
    # Trade dialog
    trade_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Trade Stock"),
        content=ft.Column(
            controls=[
                ft.Text("Symbol: AAPL", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Price: $0.00", size=14),
                ft.Divider(),
                ft.TextField(
                    label="Shares",
                    value="10",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                ft.Text("Estimated Cost: $0.00", size=14),
            ],
            spacing=10,
            tight=True,
            height=150,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
            ft.TextButton("Buy", on_click=lambda e: execute_trade("buy")),
            ft.TextButton("Sell", on_click=lambda e: execute_trade("sell")),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    def show_trade_dialog(symbol: str, action: str):
        """Show trade dialog for buying/selling"""
        if symbol not in backend.stocks:
            return
        
        stock = backend.stocks[symbol]
        trade_dialog.title.value = f"{action.upper()} {symbol}"
        trade_dialog.content.controls[0].value = f"Symbol: {symbol}"
        trade_dialog.content.controls[1].value = f"Price: ${stock.price:.2f}"
        
        # Update button visibility based on action
        trade_dialog.actions[1].visible = (action == "buy")
        trade_dialog.actions[2].visible = (action == "sell")
        
        # Store current symbol and action
        trade_dialog.data = {'symbol': symbol, 'action': action}
        
        page.dialog = trade_dialog
        trade_dialog.open = True
        page.update()
    
    def close_dialog():
        """Close the trade dialog"""
        trade_dialog.open = False
        page.update()
    
    def execute_trade(action: str):
        """Execute the trade"""
        shares_input = trade_dialog.content.controls[3]
        shares_text = shares_input.value.strip()
        
        if not shares_text.isdigit() or int(shares_text) <= 0:
            status_bar.value = "Invalid number of shares"
            status_bar.color = theme['danger']
            page.update()
            return
        
        shares = int(shares_text)
        symbol = trade_dialog.data['symbol']
        
        if action == "buy":
            success = backend.buy_stock(symbol, shares)
            message = f"Bought {shares} shares of {symbol}" if success else "Insufficient funds"
        else:  # sell
            success = backend.sell_stock(symbol, shares)
            message = f"Sold {shares} shares of {symbol}" if success else "Not enough shares"
        
        if success:
            status_bar.value = message
            status_bar.color = theme['success']
            
            # Update all displays
            update_watchlist()
            update_market_overview()
            update_portfolio_summary()
            update_transaction_history()
        else:
            status_bar.value = message
            status_bar.color = theme['danger']
        
        close_dialog()
        page.update()
    
    def show_stock_detail(stock: Stock):
        """Show stock detail view"""
        # Create a detailed view dialog
        detail_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Text(stock.symbol, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(stock.name, size=14, color=theme['subtext']),
                ],
            ),
            content=ft.Column(
                controls=[
                    # Price and change
                    ft.Row(
                        controls=[
                            ft.Text(f"${stock.price:.2f}", size=28, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.TRENDING_UP if stock.change >= 0 else ft.Icons.TRENDING_DOWN,
                                            color=theme['success'] if stock.change >= 0 else theme['danger'],
                                        ),
                                        ft.Text(
                                            f"{stock.change:+.2f} ({stock.change_percent:+.2f}%)",
                                            color=theme['success'] if stock.change >= 0 else theme['danger'],
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                border_radius=20,
                                bgcolor=ft.Colors.with_opacity(0.2, theme['success'] if stock.change >= 0 else theme['danger']),
                            ),
                        ],
                        spacing=20,
                    ),
                    
                    ft.Divider(),
                    
                    # Stock info
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Market Cap", size=12, color=theme['subtext']),
                                    ft.Text(f"${stock.market_cap/1e9:.1f}B", size=14),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("P/E Ratio", size=12, color=theme['subtext']),
                                    ft.Text(f"{stock.pe_ratio}", size=14),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Volume", size=12, color=theme['subtext']),
                                    ft.Text(f"{stock.volume:,}", size=14),
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Sector", size=12, color=theme['subtext']),
                                    ft.Text(stock.sector, size=14),
                                ],
                                expand=True,
                            ),
                        ],
                    ),
                    
                    ft.Divider(),
                    
                    # Price chart
                    ft.Text("30-Day Price History", size=16, weight=ft.FontWeight.BOLD),
                    create_price_chart(stock.history),
                    
                    ft.Divider(),
                    
                    # Trade buttons
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Buy",
                                icon=ft.Icons.ADD,
                                on_click=lambda e: show_trade_dialog(stock.symbol, "buy"),
                                style=ft.ButtonStyle(
                                    color=theme['text'],
                                    bgcolor=theme['success'],
                                    padding=ft.padding.symmetric(horizontal=30, vertical=10),
                                ),
                                expand=True,
                            ),
                            ft.ElevatedButton(
                                "Sell",
                                icon=ft.Icons.REMOVE,
                                on_click=lambda e: show_trade_dialog(stock.symbol, "sell"),
                                style=ft.ButtonStyle(
                                    color=theme['text'],
                                    bgcolor=theme['danger'],
                                    padding=ft.padding.symmetric(horizontal=30, vertical=10),
                                ),
                                expand=True,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=15,
                height=400,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: setattr(detail_dialog, 'open', False)),
            ],
        )
        
        page.dialog = detail_dialog
        detail_dialog.open = True
        page.update()
    
    # Search functionality
    def search_stocks(e):
        """Handle stock search"""
        query = search_bar.value.lower().strip()
        if not query:
            return
        
        # Filter stocks
        results = []
        for symbol, stock in backend.stocks.items():
            if query in symbol.lower() or query in stock.name.lower():
                results.append(stock)
        
        # Show results in dialog
        if results:
            result_controls = []
            for stock in results[:10]:  # Limit to 10 results
                result_controls.append(
                    ft.ListTile(
                        title=ft.Text(stock.symbol),
                        subtitle=ft.Text(stock.name),
                        trailing=ft.Text(f"${stock.price:.2f}"),
                        on_click=lambda e, s=stock: show_stock_detail(s),
                    )
                )
            
            search_dialog = ft.AlertDialog(
                title=ft.Text(f"Search Results for '{query}'"),
                content=ft.Column(
                    controls=result_controls,
                    height=300,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
            
            page.dialog = search_dialog
            search_dialog.open = True
            page.update()
    
    search_bar.on_submit = search_stocks
    
    # Initialize displays
    update_watchlist()
    update_market_overview()
    update_portfolio_summary()
    update_top_movers()
    update_transaction_history()
    
    # Create main layout
    main_content = ft.Column(
        controls=[
            # Header
            ft.Row(
                controls=[
                    ft.Text("📈 Stock Market Dashboard", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            search_bar,
                            current_time,
                        ],
                        spacing=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            
            ft.Divider(height=20),
            
            # Market Overview
            market_overview_title,
            overview_cards,
            
            ft.Divider(height=30),
            
            # Main content area
            ft.Row(
                controls=[
                    # Left column - Watchlist and Portfolio
                    ft.Column(
                        controls=[
                            portfolio_title,
                            portfolio_grid,
                            ft.Divider(height=20),
                            watchlist_title,
                            watchlist_grid,
                        ],
                        expand=2,
                        spacing=15,
                    ),
                    
                    # Right column - Top Movers and Transactions
                    ft.Column(
                        controls=[
                            top_movers_title,
                            top_movers_container,
                            ft.Divider(height=20),
                            transaction_title,
                            transaction_list,
                        ],
                        expand=1,
                        spacing=15,
                    ),
                ],
                spacing=30,
                expand=True,
            ),
            
            # Status bar
            ft.Divider(height=10),
            ft.Row(
                controls=[
                    status_bar,
                    ft.Text("© 2024 Stock Dashboard • Data is simulated", 
                           size=10, color=theme['subtext']),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ],
        spacing=20,
        expand=True,
    )
    
    # Add everything to page
    page.add(main_content)

if __name__ == "__main__":
    ft.app(target=main)