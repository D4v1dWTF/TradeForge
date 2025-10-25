"""
TradeForge Charts Module
Handles all Plotly visualizations and chart generation
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from utils import TradingCalculator

class ChartGenerator:
    """Generates various trading charts and visualizations"""
    
    @staticmethod
    def create_equity_curve(trades_df: pd.DataFrame) -> go.Figure:
        """Create equity curve chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Calculate cumulative P&L
        trades_df = trades_df.sort_values('date')
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        
        fig = go.Figure()
        
        # Add equity curve
        fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=cumulative_pnl,
            mode='lines+markers',
            name='Equity Curve',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            hovermode='x unified',
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_win_loss_chart(trades_df: pd.DataFrame) -> go.Figure:
        """Create win/loss bar chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Filter realized trades only
        realized_trades = trades_df[trades_df['realized_pnl'] != 0]
        
        if realized_trades.empty:
            return go.Figure().add_annotation(
                text="No realized trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Create win/loss data
        wins = realized_trades[realized_trades['realized_pnl'] > 0]['realized_pnl']
        losses = realized_trades[realized_trades['realized_pnl'] < 0]['realized_pnl']
        
        fig = go.Figure()
        
        # Add win bars
        if not wins.empty:
            fig.add_trace(go.Bar(
                x=list(range(len(wins))),
                y=wins,
                name='Wins',
                marker_color='#28a745',
                opacity=0.8
            ))
        
        # Add loss bars
        if not losses.empty:
            fig.add_trace(go.Bar(
                x=list(range(len(wins), len(wins) + len(losses))),
                y=losses,
                name='Losses',
                marker_color='#dc3545',
                opacity=0.8
            ))
        
        fig.update_layout(
            title="Win/Loss Distribution",
            xaxis_title="Trade Number",
            yaxis_title="P&L ($)",
            barmode='group',
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_monthly_returns_chart(trades_df: pd.DataFrame) -> go.Figure:
        """Create monthly returns chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Group by month
        trades_df['month'] = trades_df['date'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['realized_pnl'].sum().reset_index()
        monthly_pnl['month_str'] = monthly_pnl['month'].astype(str)
        
        # Create colors based on positive/negative
        colors = ['#28a745' if x >= 0 else '#dc3545' for x in monthly_pnl['realized_pnl']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=monthly_pnl['month_str'],
                y=monthly_pnl['realized_pnl'],
                marker_color=colors,
                opacity=0.8
            )
        ])
        
        fig.update_layout(
            title="Monthly Returns",
            xaxis_title="Month",
            yaxis_title="P&L ($)",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_drawdown_chart(trades_df: pd.DataFrame) -> go.Figure:
        """Create drawdown chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Calculate drawdown
        trades_df = trades_df.sort_values('date')
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        
        fig = go.Figure()
        
        # Add drawdown area
        fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=drawdown,
            fill='tozeroy',
            mode='lines',
            name='Drawdown',
            line=dict(color='#dc3545'),
            fillcolor='rgba(220, 53, 69, 0.3)'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Drawdown Chart",
            xaxis_title="Date",
            yaxis_title="Drawdown ($)",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_ticker_performance_chart(trades_df: pd.DataFrame) -> go.Figure:
        """Create ticker performance chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Group by ticker
        ticker_pnl = trades_df.groupby('ticker')['realized_pnl'].sum().sort_values(ascending=True)
        
        if ticker_pnl.empty:
            return go.Figure().add_annotation(
                text="No realized trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Create colors
        colors = ['#28a745' if x >= 0 else '#dc3545' for x in ticker_pnl.values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=ticker_pnl.values,
                y=ticker_pnl.index,
                orientation='h',
                marker_color=colors,
                opacity=0.8
            )
        ])
        
        fig.update_layout(
            title="Ticker Performance",
            xaxis_title="P&L ($)",
            yaxis_title="Ticker",
            template="plotly_white",
            height=max(300, len(ticker_pnl) * 30)
        )
        
        return fig
    
    @staticmethod
    def create_asset_type_chart(trades_df: pd.DataFrame) -> go.Figure:
        """Create asset type performance pie chart"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Group by asset type
        asset_pnl = trades_df.groupby('asset_type')['realized_pnl'].sum()
        
        if asset_pnl.empty:
            return go.Figure().add_annotation(
                text="No realized trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        fig = go.Figure(data=[
            go.Pie(
                labels=asset_pnl.index,
                values=asset_pnl.values,
                hole=0.3
            )
        ])
        
        fig.update_layout(
            title="Performance by Asset Type",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_trade_size_distribution(trades_df: pd.DataFrame) -> go.Figure:
        """Create trade size distribution histogram"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        fig = go.Figure(data=[
            go.Histogram(
                x=trades_df['total_cost'],
                nbinsx=20,
                marker_color='#2E86AB',
                opacity=0.7
            )
        ])
        
        fig.update_layout(
            title="Trade Size Distribution",
            xaxis_title="Trade Size ($)",
            yaxis_title="Frequency",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_metrics_dashboard(trades_df: pd.DataFrame) -> go.Figure:
        """Create metrics dashboard with key statistics"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Calculate metrics
        metrics = TradingCalculator.calculate_metrics(trades_df)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total P&L', 'Win Rate', 'Profit Factor', 'Max Drawdown'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Total P&L gauge
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=metrics.get('total_pnl', 0),
            title={"text": "Total P&L ($)"},
            domain={'x': [0, 0.5], 'y': [0.5, 1]}
        ), row=1, col=1)
        
        # Win Rate gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=metrics.get('win_rate', 0),
            title={"text": "Win Rate (%)"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}]},
            domain={'x': [0.5, 1], 'y': [0.5, 1]}
        ), row=1, col=2)
        
        # Profit Factor gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=min(metrics.get('profit_factor', 0), 5),  # Cap at 5 for display
            title={"text": "Profit Factor"},
            gauge={'axis': {'range': [None, 5]},
                   'bar': {'color': "darkgreen"},
                   'steps': [{'range': [0, 1], 'color': "lightgray"},
                            {'range': [1, 2], 'color': "yellow"},
                            {'range': [2, 5], 'color': "green"}]},
            domain={'x': [0, 0.5], 'y': [0, 0.5]}
        ), row=2, col=1)
        
        # Max Drawdown gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=abs(metrics.get('max_drawdown', 0)),
            title={"text": "Max Drawdown ($)"},
            gauge={'axis': {'range': [None, 1000]},
                   'bar': {'color': "darkred"},
                   'steps': [{'range': [0, 100], 'color': "green"},
                            {'range': [100, 500], 'color': "yellow"},
                            {'range': [500, 1000], 'color': "red"}]},
            domain={'x': [0.5, 1], 'y': [0, 0.5]}
        ), row=2, col=2)
        
        fig.update_layout(
            title="Trading Metrics Dashboard",
            template="plotly_white",
            height=600
        )
        
        return fig
    
    @staticmethod
    def create_correlation_heatmap(trades_df: pd.DataFrame) -> go.Figure:
        """Create correlation heatmap of trading metrics"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Prepare data for correlation
        numeric_cols = ['price', 'quantity', 'fees', 'total_cost', 'realized_pnl']
        available_cols = [col for col in numeric_cols if col in trades_df.columns]
        
        if len(available_cols) < 2:
            return go.Figure().add_annotation(
                text="Insufficient data for correlation analysis",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        corr_data = trades_df[available_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_data.values,
            x=corr_data.columns,
            y=corr_data.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(
            title="Trading Metrics Correlation",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_time_series_analysis(trades_df: pd.DataFrame) -> go.Figure:
        """Create time series analysis with moving averages"""
        if trades_df.empty:
            return go.Figure().add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Sort by date
        trades_df = trades_df.sort_values('date')
        
        # Calculate cumulative P&L
        cumulative_pnl = trades_df['realized_pnl'].cumsum()
        
        # Calculate moving averages
        ma_5 = cumulative_pnl.rolling(window=5, min_periods=1).mean()
        ma_20 = cumulative_pnl.rolling(window=20, min_periods=1).mean()
        
        fig = go.Figure()
        
        # Add cumulative P&L
        fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=cumulative_pnl,
            mode='lines',
            name='Cumulative P&L',
            line=dict(color='#2E86AB', width=2)
        ))
        
        # Add moving averages
        fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=ma_5,
            mode='lines',
            name='5-Trade MA',
            line=dict(color='orange', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=ma_20,
            mode='lines',
            name='20-Trade MA',
            line=dict(color='red', width=1, dash='dot')
        ))
        
        fig.update_layout(
            title="Time Series Analysis with Moving Averages",
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            hovermode='x unified',
            template="plotly_white",
            height=400
        )
        
        return fig

class ChartExporter:
    """Handles chart export functionality"""
    
    @staticmethod
    def export_chart_as_png(fig: go.Figure, filepath: str) -> bool:
        """Export chart as PNG"""
        try:
            fig.write_image(filepath, width=1200, height=800, scale=2)
            return True
        except Exception as e:
            print(f"PNG export error: {e}")
            return False
    
    @staticmethod
    def export_chart_as_pdf(fig: go.Figure, filepath: str) -> bool:
        """Export chart as PDF"""
        try:
            fig.write_image(filepath, format="pdf", width=1200, height=800)
            return True
        except Exception as e:
            print(f"PDF export error: {e}")
            return False
    
    @staticmethod
    def export_chart_as_html(fig: go.Figure, filepath: str) -> bool:
        """Export chart as HTML"""
        try:
            fig.write_html(filepath)
            return True
        except Exception as e:
            print(f"HTML export error: {e}")
            return False

if __name__ == "__main__":
    # Test chart generation
    print("Testing chart generation...")
    
    # Create sample data
    sample_data = {
        'date': pd.date_range('2024-01-01', periods=20, freq='D'),
        'ticker': ['AAPL'] * 10 + ['GOOGL'] * 10,
        'realized_pnl': np.random.normal(0, 100, 20),
        'total_cost': np.random.uniform(1000, 5000, 20),
        'asset_type': ['Stock'] * 20
    }
    
    df = pd.DataFrame(sample_data)
    
    # Test charts
    charts = [
        ('Equity Curve', ChartGenerator.create_equity_curve(df)),
        ('Win/Loss Chart', ChartGenerator.create_win_loss_chart(df)),
        ('Monthly Returns', ChartGenerator.create_monthly_returns_chart(df)),
        ('Drawdown Chart', ChartGenerator.create_drawdown_chart(df)),
        ('Ticker Performance', ChartGenerator.create_ticker_performance_chart(df)),
        ('Asset Type Chart', ChartGenerator.create_asset_type_chart(df)),
        ('Trade Size Distribution', ChartGenerator.create_trade_size_distribution(df)),
        ('Metrics Dashboard', ChartGenerator.create_metrics_dashboard(df))
    ]
    
    for name, chart in charts:
        print(f"Generated {name} chart successfully")
    
    print("Chart generation test completed!")
