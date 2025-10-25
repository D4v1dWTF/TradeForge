"""
TradeForge Utility Functions
Handles calculations, risk management, and utility functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
import os
import zipfile
import json
from data import DatabaseManager

class TradingCalculator:
    """Handles trading calculations and metrics"""
    
    @staticmethod
    def calculate_pnl(trades_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate P&L for trades"""
        df = trades_df.copy()
        
        # Group by ticker to calculate position-based P&L
        for ticker in df['ticker'].unique():
            ticker_trades = df[df['ticker'] == ticker].sort_values('date')
            
            position = 0
            total_cost = 0
            realized_pnl = 0
            
            for idx, trade in ticker_trades.iterrows():
                if trade['trade_type'] == 'Buy':
                    position += trade['quantity']
                    total_cost += trade['total_cost']
                else:  # Sell
                    if position > 0:
                        # Calculate average cost
                        avg_cost = total_cost / position if position > 0 else 0
                        # Calculate P&L for this sell
                        trade_pnl = (trade['price'] - avg_cost) * trade['quantity'] - trade['fees']
                        realized_pnl += trade_pnl
                        
                        # Update position and cost
                        position -= trade['quantity']
                        total_cost = total_cost * (position / (position + trade['quantity'])) if position > 0 else 0
                
                # Update the dataframe
                df.loc[idx, 'realized_pnl'] = realized_pnl
                df.loc[idx, 'unrealized_pnl'] = 0  # Will be calculated with live prices
        
        return df
    
    @staticmethod
    def get_live_price(ticker: str) -> Optional[float]:
        """Get live price for a ticker using yfinance"""
        try:
            # Handle HK stocks
            if ticker.endswith('.HK'):
                ticker_symbol = ticker
            else:
                ticker_symbol = ticker
            
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            return info.get('currentPrice') or info.get('regularMarketPrice')
        except Exception as e:
            print(f"Error getting live price for {ticker}: {e}")
            return None
    
    @staticmethod
    def calculate_unrealized_pnl(trades_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate unrealized P&L using live prices"""
        df = trades_df.copy()
        
        for ticker in df['ticker'].unique():
            ticker_trades = df[df['ticker'] == ticker].sort_values('date')
            
            # Calculate current position
            position = ticker_trades[ticker_trades['trade_type'] == 'Buy']['quantity'].sum() - \
                      ticker_trades[ticker_trades['trade_type'] == 'Sell']['quantity'].sum()
            
            if position > 0:  # Long position
                # Calculate average cost
                buy_trades = ticker_trades[ticker_trades['trade_type'] == 'Buy']
                total_cost = buy_trades['total_cost'].sum()
                avg_cost = total_cost / buy_trades['quantity'].sum()
                
                # Get live price
                live_price = TradingCalculator.get_live_price(ticker)
                if live_price:
                    unrealized_pnl = (live_price - avg_cost) * position
                    df.loc[df['ticker'] == ticker, 'unrealized_pnl'] = unrealized_pnl
        
        return df
    
    @staticmethod
    def calculate_metrics(trades_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive trading metrics"""
        if trades_df.empty:
            return {}
        
        # Basic metrics
        total_trades = len(trades_df)
        total_pnl = trades_df['realized_pnl'].sum() + trades_df['unrealized_pnl'].sum()
        
        # Win/Loss analysis
        realized_trades = trades_df[trades_df['realized_pnl'] != 0]
        if not realized_trades.empty:
            winning_trades = realized_trades[realized_trades['realized_pnl'] > 0]
            losing_trades = realized_trades[realized_trades['realized_pnl'] < 0]
            
            win_rate = len(winning_trades) / len(realized_trades) * 100
            avg_win = winning_trades['realized_pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['realized_pnl'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(winning_trades['realized_pnl'].sum() / losing_trades['realized_pnl'].sum()) if len(losing_trades) > 0 and losing_trades['realized_pnl'].sum() != 0 else float('inf')
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        # Drawdown calculation
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (simplified)
        if len(realized_trades) > 1:
            returns = realized_trades['realized_pnl'].pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
        else:
            sharpe_ratio = 0
        
        # Risk metrics
        largest_win = trades_df['realized_pnl'].max() if not trades_df.empty else 0
        largest_loss = trades_df['realized_pnl'].min() if not trades_df.empty else 0
        
        # Monthly returns
        trades_df['month'] = trades_df['date'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['realized_pnl'].sum()
        best_month = monthly_pnl.max() if not monthly_pnl.empty else 0
        worst_month = monthly_pnl.min() if not monthly_pnl.empty else 0
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'best_month': best_month,
            'worst_month': worst_month,
            'total_volume': trades_df['total_cost'].sum(),
            'avg_trade_size': trades_df['total_cost'].mean()
        }
    
    @staticmethod
    def calculate_risk_metrics(account_value: float, trade_data: Dict) -> Dict:
        """Calculate risk management metrics"""
        # 1% risk calculation
        one_percent_risk = account_value * 0.01
        
        # Position sizing based on risk
        stop_loss_pct = trade_data.get('stop_loss_pct', 0.02)  # 2% default stop loss
        risk_per_share = trade_data['price'] * stop_loss_pct
        max_shares = int(one_percent_risk / risk_per_share) if risk_per_share > 0 else 0
        
        # Kelly Criterion (simplified)
        win_rate = trade_data.get('win_rate', 0.5)
        avg_win = trade_data.get('avg_win', 0)
        avg_loss = trade_data.get('avg_loss', 0)
        
        if avg_loss != 0:
            kelly_pct = (win_rate * avg_win - (1 - win_rate) * abs(avg_loss)) / avg_win
            kelly_pct = max(0, min(kelly_pct, 0.25))  # Cap at 25%
        else:
            kelly_pct = 0
        
        return {
            'one_percent_risk': one_percent_risk,
            'max_shares_1pct': max_shares,
            'kelly_percentage': kelly_pct,
            'recommended_position_size': min(max_shares, int(account_value * kelly_pct / trade_data['price']))
        }

class DataExporter:
    """Handles data export and backup functionality"""
    
    @staticmethod
    def export_to_excel(trades_df: pd.DataFrame, filepath: str) -> bool:
        """Export trades to Excel file"""
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                trades_df.to_excel(writer, sheet_name='Trades', index=False)
                
                # Add summary sheet
                metrics = TradingCalculator.calculate_metrics(trades_df)
                summary_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            return True
        except Exception as e:
            print(f"Excel export error: {e}")
            return False
    
    @staticmethod
    def create_backup_zip(db_path: str, backup_path: str) -> bool:
        """Create a ZIP backup of the database and related files"""
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                if os.path.exists(db_path):
                    zipf.write(db_path, 'trades.db')
                
                # Add any other important files
                for file in ['app.py', 'data.py', 'charts.py', 'utils.py']:
                    if os.path.exists(file):
                        zipf.write(file)
            
            return True
        except Exception as e:
            print(f"Backup creation error: {e}")
            return False
    
    @staticmethod
    def restore_from_zip(backup_path: str, restore_dir: str = '.') -> bool:
        """Restore from ZIP backup"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            return True
        except Exception as e:
            print(f"Restore error: {e}")
            return False

class AIInsights:
    """Basic rule-based AI insights for trading patterns"""
    
    @staticmethod
    def generate_insights(trades_df: pd.DataFrame) -> List[str]:
        """Generate basic trading insights"""
        insights = []
        
        if trades_df.empty:
            return ["No trades found. Start by adding your first trade!"]
        
        # Win rate insights
        realized_trades = trades_df[trades_df['realized_pnl'] != 0]
        if not realized_trades.empty:
            win_rate = len(realized_trades[realized_trades['realized_pnl'] > 0]) / len(realized_trades) * 100
            
            if win_rate >= 60:
                insights.append(f"🎯 Excellent win rate of {win_rate:.1f}%! You're making good trading decisions.")
            elif win_rate >= 50:
                insights.append(f"📈 Good win rate of {win_rate:.1f}%. Consider improving your entry/exit timing.")
            else:
                insights.append(f"⚠️ Win rate of {win_rate:.1f}% needs improvement. Review your trading strategy.")
        
        # Profit factor insights
        winning_trades = realized_trades[realized_trades['realized_pnl'] > 0]
        losing_trades = realized_trades[realized_trades['realized_pnl'] < 0]
        
        if len(losing_trades) > 0 and len(winning_trades) > 0:
            profit_factor = abs(winning_trades['realized_pnl'].sum() / losing_trades['realized_pnl'].sum())
            
            if profit_factor >= 2.0:
                insights.append(f"💰 Strong profit factor of {profit_factor:.2f}. Your winners are significantly larger than losers.")
            elif profit_factor >= 1.5:
                insights.append(f"💪 Good profit factor of {profit_factor:.2f}. Keep up the good work!")
            else:
                insights.append(f"📉 Profit factor of {profit_factor:.2f} suggests your losses are too large relative to wins.")
        
        # Drawdown insights
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        if max_drawdown < -0.1:  # 10% drawdown
            insights.append(f"⚠️ Maximum drawdown of {max_drawdown:.1%} is concerning. Consider reducing position sizes.")
        elif max_drawdown < -0.05:  # 5% drawdown
            insights.append(f"📊 Maximum drawdown of {max_drawdown:.1%} is manageable but monitor closely.")
        else:
            insights.append(f"✅ Low maximum drawdown of {max_drawdown:.1%}. Good risk management!")
        
        # Trading frequency insights
        if len(trades_df) > 0:
            days_trading = (trades_df['date'].max() - trades_df['date'].min()).days
            trades_per_day = len(trades_df) / max(days_trading, 1)
            
            if trades_per_day > 1:
                insights.append(f"⚡ High trading frequency of {trades_per_day:.1f} trades/day. Consider quality over quantity.")
            elif trades_per_day < 0.1:
                insights.append(f"🐌 Low trading frequency of {trades_per_day:.1f} trades/day. More opportunities might be available.")
        
        # Best performing ticker
        ticker_pnl = trades_df.groupby('ticker')['realized_pnl'].sum().sort_values(ascending=False)
        if not ticker_pnl.empty and ticker_pnl.iloc[0] > 0:
            best_ticker = ticker_pnl.index[0]
            insights.append(f"🏆 {best_ticker} is your best performer with ${ticker_pnl.iloc[0]:.2f} profit.")
        
        # Worst performing ticker
        if not ticker_pnl.empty and ticker_pnl.iloc[-1] < 0:
            worst_ticker = ticker_pnl.index[-1]
            insights.append(f"📉 {worst_ticker} is your worst performer with ${ticker_pnl.iloc[-1]:.2f} loss.")
        
        return insights

class CurrencyConverter:
    """Handles currency conversion for international trades"""
    
    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str) -> float:
        """Get exchange rate between currencies"""
        try:
            if from_currency == to_currency:
                return 1.0
            
            # For demo purposes, using fixed rates
            # In production, you'd use a real API like exchangerate-api.com
            rates = {
                'USD_HKD': 7.8,
                'HKD_USD': 1/7.8,
                'USD_EUR': 0.85,
                'EUR_USD': 1/0.85
            }
            
            key = f"{from_currency}_{to_currency}"
            return rates.get(key, 1.0)
        except Exception as e:
            print(f"Currency conversion error: {e}")
            return 1.0
    
    @staticmethod
    def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another"""
        rate = CurrencyConverter.get_exchange_rate(from_currency, to_currency)
        return amount * rate

if __name__ == "__main__":
    # Test utility functions
    print("Testing utility functions...")
    
    # Test metrics calculation
    sample_data = {
        'date': [datetime.now() - timedelta(days=i) for i in range(5)],
        'ticker': ['AAPL', 'GOOGL', 'AAPL', 'MSFT', 'GOOGL'],
        'trade_type': ['Buy', 'Buy', 'Sell', 'Buy', 'Sell'],
        'price': [150, 2800, 155, 300, 2850],
        'quantity': [10, 1, 10, 5, 1],
        'fees': [5, 1, 5, 3, 1],
        'realized_pnl': [0, 0, 50, 0, 50],
        'unrealized_pnl': [0, 0, 0, 0, 0]
    }
    
    df = pd.DataFrame(sample_data)
    df['total_cost'] = df['price'] * df['quantity'] + df['fees']
    
    metrics = TradingCalculator.calculate_metrics(df)
    print(f"Sample metrics: {metrics}")
    
    # Test AI insights
    insights = AIInsights.generate_insights(df)
    print(f"Sample insights: {insights}")
    
    print("Utility functions test completed!")
