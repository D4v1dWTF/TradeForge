"""
TradeForge Database Module
Handles SQLite database operations, data models, and data management
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()

class Trade(Base):
    """Trade model for SQLite database"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    ticker = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)  # Stock, Option
    trade_type = Column(String(10), nullable=False)  # Buy, Sell
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    notes = Column(Text, default="")
    
    # For options
    option_type = Column(String(10))  # Call, Put
    strike_price = Column(Float)
    expiration_date = Column(DateTime)
    premium = Column(Float)
    strategy = Column(String(50))  # Long Call, Long Put, etc.
    
    # Calculated fields
    total_cost = Column(Float)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    
    # Currency and market
    currency = Column(String(3), default="USD")
    market = Column(String(10), default="US")  # US, HK

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create user-specific database path
            import os
            import getpass
            username = getpass.getuser()
            db_path = f"trades_{username}.db"
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        Base.metadata.create_all(self.engine)
    
    def add_trade(self, trade_data: Dict) -> int:
        """Add a new trade to the database"""
        session = self.Session()
        try:
            # Calculate total cost
            total_cost = (trade_data['price'] * trade_data['quantity']) + trade_data.get('fees', 0)
            
            # Determine currency and market
            currency = "HKD" if trade_data['ticker'].endswith('.HK') else "USD"
            market = "HK" if trade_data['ticker'].endswith('.HK') else "US"
            
            trade = Trade(
                date=trade_data['date'],
                ticker=trade_data['ticker'],
                asset_type=trade_data['asset_type'],
                trade_type=trade_data['trade_type'],
                price=trade_data['price'],
                quantity=trade_data['quantity'],
                fees=trade_data.get('fees', 0),
                notes=trade_data.get('notes', ''),
                option_type=trade_data.get('option_type'),
                strike_price=trade_data.get('strike_price'),
                expiration_date=trade_data.get('expiration_date'),
                premium=trade_data.get('premium'),
                strategy=trade_data.get('strategy'),
                total_cost=total_cost,
                currency=currency,
                market=market
            )
            
            session.add(trade)
            session.commit()
            trade_id = trade.id
            return trade_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_trades(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all trades as DataFrame"""
        session = self.Session()
        try:
            query = session.query(Trade).order_by(Trade.date.desc())
            if limit:
                query = query.limit(limit)
            
            trades = query.all()
            data = []
            for trade in trades:
                data.append({
                    'id': trade.id,
                    'date': trade.date,
                    'ticker': trade.ticker,
                    'asset_type': trade.asset_type,
                    'trade_type': trade.trade_type,
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'fees': trade.fees,
                    'notes': trade.notes,
                    'option_type': trade.option_type,
                    'strike_price': trade.strike_price,
                    'expiration_date': trade.expiration_date,
                    'premium': trade.premium,
                    'strategy': trade.strategy,
                    'total_cost': trade.total_cost,
                    'realized_pnl': trade.realized_pnl,
                    'unrealized_pnl': trade.unrealized_pnl,
                    'currency': trade.currency,
                    'market': trade.market
                })
            
            return pd.DataFrame(data)
        finally:
            session.close()
    
    def update_trade(self, trade_id: int, trade_data: Dict) -> bool:
        """Update an existing trade"""
        session = self.Session()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return False
            
            # Update fields
            for key, value in trade_data.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            
            # Recalculate total cost
            trade.total_cost = (trade.price * trade.quantity) + trade.fees
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade"""
        session = self.Session()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return False
            
            session.delete(trade)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def reset_database(self):
        """Clear all trades from database"""
        session = self.Session()
        try:
            session.query(Trade).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_trade_stats(self) -> Dict:
        """Get basic trade statistics"""
        df = self.get_trades()
        if df.empty:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_drawdown': 0
            }
        
        # Calculate basic stats
        total_trades = len(df)
        total_pnl = df['realized_pnl'].sum() + df['unrealized_pnl'].sum()
        
        # Win rate calculation
        winning_trades = df[df['realized_pnl'] > 0]
        losing_trades = df[df['realized_pnl'] < 0]
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        avg_win = winning_trades['realized_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['realized_pnl'].mean() if len(losing_trades) > 0 else 0
        
        # Simple max drawdown calculation
        cumulative_pnl = df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown
        }
    
    def export_to_csv(self, filepath: str) -> bool:
        """Export trades to CSV"""
        try:
            df = self.get_trades()
            df.to_csv(filepath, index=False)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def import_from_csv(self, filepath: str) -> Tuple[int, int]:
        """Import trades from CSV. Returns (successful, failed) counts"""
        try:
            df = pd.read_csv(filepath)
            successful = 0
            failed = 0
            
            for _, row in df.iterrows():
                try:
                    trade_data = {
                        'date': pd.to_datetime(row['date']),
                        'ticker': str(row['ticker']),
                        'asset_type': str(row.get('asset_type', 'Stock')),
                        'trade_type': str(row['trade_type']),
                        'price': float(row['price']),
                        'quantity': float(row['quantity']),
                        'fees': float(row.get('fees', 0)),
                        'notes': str(row.get('notes', '')),
                        'option_type': row.get('option_type'),
                        'strike_price': row.get('strike_price'),
                        'expiration_date': pd.to_datetime(row['expiration_date']) if pd.notna(row.get('expiration_date')) else None,
                        'premium': row.get('premium'),
                        'strategy': row.get('strategy')
                    }
                    
                    self.add_trade(trade_data)
                    successful += 1
                except Exception as e:
                    print(f"Failed to import row: {e}")
                    failed += 1
            
            return successful, failed
        except Exception as e:
            print(f"Import error: {e}")
            return 0, 0
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Backup error: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            # Recreate tables
            self._create_tables()
            return True
        except Exception as e:
            print(f"Restore error: {e}")
            return False

# Sample data for testing
def create_sample_data():
    """Create sample trading data for testing"""
    db = DatabaseManager()
    
    sample_trades = [
        {
            'date': datetime(2024, 1, 15, 9, 30),
            'ticker': 'NVDA',
            'asset_type': 'Stock',
            'trade_type': 'Buy',
            'price': 187.50,
            'quantity': 10,
            'fees': 4.95,
            'notes': 'AI momentum play'
        },
        {
            'date': datetime(2024, 1, 20, 14, 15),
            'ticker': 'KO',
            'asset_type': 'Option',
            'trade_type': 'Buy',
            'price': 2.50,
            'quantity': 1,
            'fees': 0.65,
            'option_type': 'Call',
            'strike_price': 60.0,
            'expiration_date': datetime(2024, 3, 15),
            'premium': 2.50,
            'strategy': 'Long Call',
            'notes': 'Coca-Cola earnings play'
        },
        {
            'date': datetime(2024, 2, 1, 10, 0),
            'ticker': 'AAPL',
            'asset_type': 'Stock',
            'trade_type': 'Sell',
            'price': 195.20,
            'quantity': 5,
            'fees': 4.95,
            'notes': 'Profit taking'
        }
    ]
    
    for trade_data in sample_trades:
        try:
            db.add_trade(trade_data)
        except Exception as e:
            print(f"Error adding sample trade: {e}")

if __name__ == "__main__":
    # Test database functionality
    db = DatabaseManager()
    print("Database initialized successfully!")
    
    # Create sample data
    create_sample_data()
    print("Sample data created!")
    
    # Test queries
    trades = db.get_trades()
    print(f"Total trades: {len(trades)}")
    
    stats = db.get_trade_stats()
    print(f"Trade stats: {stats}")
