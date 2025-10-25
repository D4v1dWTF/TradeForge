"""
TradeForge - Local Trading Journal Desktop App
A free, open-source alternative to TradesViz with all premium features unlocked
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os
import tempfile
import zipfile
from io import BytesIO
import base64
import hashlib
import json

# Import our modules
from data import DatabaseManager, create_sample_data
from utils import TradingCalculator, DataExporter, AIInsights, CurrencyConverter
from charts import ChartGenerator, ChartExporter

# Page configuration
st.set_page_config(
    page_title="TradeForge - 交易日誌",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language and Login Management
class LanguageManager:
    def __init__(self):
        self.languages = {
            'en': {
                'title': 'TradeForge - Trading Journal',
                'welcome': 'Welcome to TradeForge!',
                'login': 'Login',
                'register': 'Register',
                'username': 'Username',
                'password': 'Password',
                'confirm_password': 'Confirm Password',
                'login_button': 'Login',
                'register_button': 'Register',
                'logout': 'Logout',
                'dashboard': 'Dashboard',
                'trade_entry': 'Trade Entry',
                'analysis': 'Analysis',
                'charts': 'Charts',
                'calendar': 'Calendar',
                'data': 'Data',
                'about': 'About'
            },
            'zh': {
                'title': 'TradeForge - 交易日誌',
                'welcome': '歡迎使用 TradeForge！',
                'login': '登入',
                'register': '註冊',
                'username': '用戶名',
                'password': '密碼',
                'confirm_password': '確認密碼',
                'login_button': '登入',
                'register_button': '註冊',
                'logout': '登出',
                'dashboard': '儀表板',
                'trade_entry': '交易記錄',
                'analysis': '分析',
                'charts': '圖表',
                'calendar': '日曆',
                'data': '數據',
                'about': '關於'
            }
        }
    
    def get_text(self, key, lang='en'):
        return self.languages.get(lang, self.languages['en']).get(key, key)

class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.load_users()
    
    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
    
    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password):
        if username in self.users:
            return False, "Username already exists"
        
        self.users[username] = {
            'password': self.hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        self.save_users()
        return True, "User registered successfully"
    
    def login_user(self, username, password):
        if username not in self.users:
            return False, "User not found"
        
        if self.users[username]['password'] != self.hash_password(password):
            return False, "Invalid password"
        
        return True, "Login successful"
    
    def get_user_database(self, username):
        return f"trades_{username}.db"

# Initialize managers
lang_manager = LanguageManager()
user_manager = UserManager()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86AB;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffeaa7;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .language-selector {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# Language selector
with st.container():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        language = st.selectbox("🌐 Language / 語言", ["English", "繁體中文"], index=0)
        if language == "English":
            st.session_state.language = 'en'
        else:
            st.session_state.language = 'zh'

# Get current language
lang = st.session_state.language

# Login Page
if not st.session_state.authenticated:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.markdown(f'<h1 style="text-align: center; color: #2E86AB;">📈 {lang_manager.get_text("title", lang)}</h1>', unsafe_allow_html=True)
    
    # Login/Register tabs
    login_tab, register_tab = st.tabs([lang_manager.get_text("login", lang), lang_manager.get_text("register", lang)])
    
    with login_tab:
        with st.form("login_form"):
            st.markdown(f"### {lang_manager.get_text('welcome', lang)}")
            
            username = st.text_input(lang_manager.get_text("username", lang))
            password = st.text_input(lang_manager.get_text("password", lang), type="password")
            
            submitted = st.form_submit_button(lang_manager.get_text("login_button", lang), width='stretch')
            
            if submitted:
                if username and password:
                    success, message = user_manager.login_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        # Initialize user-specific database
                        user_db_path = user_manager.get_user_database(username)
                        st.session_state.db = DatabaseManager(user_db_path)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all fields")
    
    with register_tab:
        with st.form("register_form"):
            st.markdown(f"### {lang_manager.get_text('register', lang)}")
            
            username = st.text_input(lang_manager.get_text("username", lang))
            password = st.text_input(lang_manager.get_text("password", lang), type="password")
            confirm_password = st.text_input(lang_manager.get_text("confirm_password", lang), type="password")
            
            submitted = st.form_submit_button(lang_manager.get_text("register_button", lang), width='stretch')
            
            if submitted:
                if username and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        success, message = user_manager.register_user(username, password)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all fields")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show info about the app
    st.markdown("---")
    st.markdown("### 🌟 Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📝 **Trade Entry**\n\nRecord stocks, options, crypto, and more")
    with col2:
        st.info("📊 **Analysis**\n\nComprehensive trading metrics")
    with col3:
        st.info("📈 **Charts**\n\nBeautiful visualizations")
    
    st.stop()

# Main app (only shown when authenticated)
# Initialize user-specific database
if 'db' not in st.session_state:
    user_db_path = user_manager.get_user_database(st.session_state.username)
    st.session_state.db = DatabaseManager(user_db_path)

if 'trades_df' not in st.session_state:
    st.session_state.trades_df = st.session_state.db.get_trades()

# Main header
st.markdown(f'<h1 class="main-header">📈 {lang_manager.get_text("title", lang)}</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">Welcome, {st.session_state.username}! | 歡迎, {st.session_state.username}!</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/2E86AB/FFFFFF?text=TradeForge", width=200)
    
    # User info
    st.markdown(f"### 👤 {st.session_state.username}")
    
    # Logout button
    if st.button("🚪 Logout / 登出", width='stretch'):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.db = None
        st.session_state.trades_df = None
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🚀 Quick Actions")
    
    if st.button("🔄 Refresh Data / 刷新數據", width='stretch'):
        st.session_state.trades_df = st.session_state.db.get_trades()
        st.rerun()
    
    if st.button("📊 Add Sample Data / 添加示例數據", width='stretch'):
        create_sample_data()
        st.session_state.trades_df = st.session_state.db.get_trades()
        st.success("Sample data added! / 示例數據已添加！")
        st.rerun()
    
    if st.button("🗑️ Reset Database / 重置數據庫", width='stretch'):
        if st.session_state.db.reset_database():
            st.session_state.trades_df = st.session_state.db.get_trades()
            st.success("Database reset successfully! / 數據庫重置成功！")
            st.rerun()
        else:
            st.error("Failed to reset database / 重置數據庫失敗")
    
    st.markdown("---")
    
    # Database info
    st.markdown("### 📊 Database Info / 數據庫信息")
    st.info(f"Total Trades / 總交易數: {len(st.session_state.trades_df)}")
    
    if not st.session_state.trades_df.empty:
        total_pnl = st.session_state.trades_df['realized_pnl'].sum() + st.session_state.trades_df['unrealized_pnl'].sum()
        st.metric("Total P&L / 總盈虧", f"${total_pnl:.2f}")

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    f"🏠 {lang_manager.get_text('dashboard', lang)}", 
    f"📝 {lang_manager.get_text('trade_entry', lang)}", 
    f"📊 {lang_manager.get_text('analysis', lang)}", 
    f"📈 {lang_manager.get_text('charts', lang)}", 
    f"📅 {lang_manager.get_text('calendar', lang)}", 
    f"💾 {lang_manager.get_text('data', lang)}", 
    f"ℹ️ {lang_manager.get_text('about', lang)}"
])

# Tab 1: Dashboard
with tab1:
    st.header("🏠 Trading Dashboard")
    
    if st.session_state.trades_df.empty:
        # Welcome screen for new users
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin: 2rem 0;">
            <h2>🎉 Welcome to TradeForge!</h2>
            <p style="font-size: 1.2rem; margin: 1rem 0;">Your personal trading journal is ready to use.</p>
            <p>Start by adding your first trade in the "Add Trade" tab above.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📝 **Add Trades**\n\nRecord your stock and options trades with detailed tracking.")
        with col2:
            st.info("📊 **Analyze Performance**\n\nView comprehensive metrics and statistics.")
        with col3:
            st.info("📈 **Create Charts**\n\nVisualize your trading data with beautiful charts.")
    else:
        # Dashboard with key metrics
        st.markdown("### 📊 Quick Overview")
        
        # Key metrics in a nice layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_trades = len(st.session_state.trades_df)
            st.metric("Total Trades", total_trades)
        
        with col2:
            total_pnl = st.session_state.trades_df['realized_pnl'].sum() + st.session_state.trades_df['unrealized_pnl'].sum()
            st.metric("Total P&L", f"${total_pnl:.2f}")
        
        with col3:
            realized_trades = st.session_state.trades_df[st.session_state.trades_df['realized_pnl'] != 0]
            if not realized_trades.empty:
                win_rate = len(realized_trades[realized_trades['realized_pnl'] > 0]) / len(realized_trades) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            else:
                st.metric("Win Rate", "N/A")
        
        with col4:
            unique_tickers = st.session_state.trades_df['ticker'].nunique()
            st.metric("Tickers", unique_tickers)
        
        # Recent trades preview
        st.markdown("### 📋 Recent Trades")
        recent_trades = st.session_state.trades_df.head(5)
        
        if not recent_trades.empty:
            # Create a cleaner display
            display_df = recent_trades[['date', 'ticker', 'asset_type', 'trade_type', 'price', 'quantity', 'total_cost']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%m/%d %H:%M')
            display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
            display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No trades found. Add your first trade in the 'Add Trade' tab!")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("📝 **Add New Trade**\n\nClick the 'Add Trade' tab above to record your trades.")
        
        with col2:
            st.info("📊 **View Analysis**\n\nCheck the 'Analysis' tab for detailed metrics.")
        
        with col3:
            st.info("📈 **Create Charts**\n\nVisit the 'Charts' tab for visualizations.")

# Tab 2: Trade Entry
with tab2:
    st.header("📝 Trade Entry")
    
    # Asset type selection
    st.markdown("### 🎯 Select Asset Type")
    asset_type = st.radio(
        "What type of trade do you want to record?",
        ["📈 Stock", "🎯 Options", "₿ Crypto", "🏦 Forex", "📊 ETF", "🏢 Bonds"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Stock Trading Section
    if asset_type == "📈 Stock":
        st.subheader("📈 Stock Trade")
        
        with st.form("stock_trade_form"):
            col1, col2 = st.columns(2)
            with col1:
                trade_date = st.date_input("📅 Date", value=date.today())
            with col2:
                trade_time = st.time_input("🕐 Time", value=datetime.now().time())
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("🏷️ Ticker Symbol", placeholder="AAPL, NVDA, 0700.HK")
                st.caption("Enter stock symbol (e.g., AAPL for Apple, 0700.HK for Tencent)")
            with col2:
                trade_type = st.selectbox("📊 Trade Type", ["Buy", "Sell"])
            
            col1, col2 = st.columns(2)
            with col1:
                price = st.number_input("💰 Price ($)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                quantity = st.number_input("📦 Quantity", min_value=0.0, step=0.01)
            
            col1, col2 = st.columns(2)
            with col1:
                fees = st.number_input("💳 Fees ($)", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            with col2:
                currency = st.selectbox("💱 Currency", ["USD", "HKD", "EUR", "GBP"])
            
            notes = st.text_area("📝 Notes", placeholder="Enter any additional notes about this trade...")
            
            submitted = st.form_submit_button("📝 Submit Stock Trade", width='stretch')
            
            if submitted:
                if ticker and price > 0 and quantity > 0:
                    try:
                        trade_data = {
                            'date': datetime.combine(trade_date, trade_time),
                            'ticker': ticker.upper(),
                            'asset_type': 'Stock',
                            'trade_type': trade_type,
                            'price': price,
                            'quantity': quantity,
                            'fees': fees,
                            'notes': notes,
                            'currency': currency
                        }
                        
                        trade_id = st.session_state.db.add_trade(trade_data)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        
                        st.success(f"✅ Stock Trade #{trade_id} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding trade: {str(e)}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Options Trading Section
    elif asset_type == "🎯 Options":
        st.subheader("🎯 Options Trade")
        
        with st.form("options_trade_form"):
            col1, col2 = st.columns(2)
            with col1:
                trade_date = st.date_input("📅 Date", value=date.today(), key="opt_date")
            with col2:
                trade_time = st.time_input("🕐 Time", value=datetime.now().time(), key="opt_time")
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("🏷️ Underlying Stock", placeholder="AAPL", key="opt_ticker")
                st.caption("Enter the underlying stock symbol")
            with col2:
                trade_type = st.selectbox("📊 Trade Type", ["Buy", "Sell"], key="opt_type")
            
            col1, col2 = st.columns(2)
            with col1:
                option_type = st.selectbox("🎯 Option Type", ["Call", "Put"], key="opt_option_type")
            with col2:
                strike_price = st.number_input("🎯 Strike Price ($)", min_value=0.0, step=0.01, format="%.2f", key="opt_strike")
            
            col1, col2 = st.columns(2)
            with col1:
                premium = st.number_input("💰 Premium ($)", min_value=0.0, step=0.01, format="%.2f", key="opt_premium")
            with col2:
                contracts = st.number_input("📦 Contracts", min_value=0, step=1, key="opt_contracts")
            
            col1, col2 = st.columns(2)
            with col1:
                expiration_date = st.date_input("📅 Expiration Date", key="opt_exp")
            with col2:
                strategy = st.selectbox("📊 Strategy", ["Long Call", "Long Put", "Short Call", "Short Put", "Covered Call", "Protective Put", "Straddle", "Strangle"], key="opt_strategy")
            
            col1, col2 = st.columns(2)
            with col1:
                fees = st.number_input("💳 Fees ($)", min_value=0.0, step=0.01, format="%.2f", value=0.0, key="opt_fees")
            with col2:
                currency = st.selectbox("💱 Currency", ["USD", "HKD", "EUR", "GBP"], key="opt_currency")
            
            notes = st.text_area("📝 Notes", placeholder="Enter any additional notes about this options trade...", key="opt_notes")
            
            submitted = st.form_submit_button("🎯 Submit Options Trade", width='stretch')
            
            if submitted:
                if ticker and premium > 0 and contracts > 0 and strike_price > 0:
                    try:
                        trade_data = {
                            'date': datetime.combine(trade_date, trade_time),
                            'ticker': ticker.upper(),
                            'asset_type': 'Option',
                            'trade_type': trade_type,
                            'price': premium,
                            'quantity': contracts,
                            'fees': fees,
                            'notes': notes,
                            'option_type': option_type,
                            'strike_price': strike_price,
                            'expiration_date': datetime.combine(expiration_date, datetime.min.time()),
                            'premium': premium,
                            'strategy': strategy,
                            'currency': currency
                        }
                        
                        trade_id = st.session_state.db.add_trade(trade_data)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        
                        st.success(f"✅ Options Trade #{trade_id} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding options trade: {str(e)}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Crypto Trading Section
    elif asset_type == "₿ Crypto":
        st.subheader("₿ Cryptocurrency Trade")
        
        with st.form("crypto_trade_form"):
            col1, col2 = st.columns(2)
            with col1:
                trade_date = st.date_input("📅 Date", value=date.today(), key="crypto_date")
            with col2:
                trade_time = st.time_input("🕐 Time", value=datetime.now().time(), key="crypto_time")
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("🏷️ Crypto Symbol", placeholder="BTC, ETH, ADA", key="crypto_ticker")
                st.caption("Enter cryptocurrency symbol (e.g., BTC, ETH, ADA)")
            with col2:
                trade_type = st.selectbox("📊 Trade Type", ["Buy", "Sell"], key="crypto_type")
            
            col1, col2 = st.columns(2)
            with col1:
                price = st.number_input("💰 Price ($)", min_value=0.0, step=0.01, format="%.2f", key="crypto_price")
            with col2:
                quantity = st.number_input("📦 Quantity", min_value=0.0, step=0.00000001, format="%.8f", key="crypto_quantity")
            
            col1, col2 = st.columns(2)
            with col1:
                fees = st.number_input("💳 Fees ($)", min_value=0.0, step=0.01, format="%.2f", value=0.0, key="crypto_fees")
            with col2:
                currency = st.selectbox("💱 Currency", ["USD", "EUR", "GBP", "JPY"], key="crypto_currency")
            
            notes = st.text_area("📝 Notes", placeholder="Enter any additional notes about this crypto trade...", key="crypto_notes")
            
            submitted = st.form_submit_button("₿ Submit Crypto Trade", width='stretch')
            
            if submitted:
                if ticker and price > 0 and quantity > 0:
                    try:
                        trade_data = {
                            'date': datetime.combine(trade_date, trade_time),
                            'ticker': ticker.upper(),
                            'asset_type': 'Crypto',
                            'trade_type': trade_type,
                            'price': price,
                            'quantity': quantity,
                            'fees': fees,
                            'notes': notes,
                            'currency': currency
                        }
                        
                        trade_id = st.session_state.db.add_trade(trade_data)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        
                        st.success(f"✅ Crypto Trade #{trade_id} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding crypto trade: {str(e)}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Other asset types (simplified)
    else:
        st.subheader(f"{asset_type} Trade")
        st.info(f"🚧 {asset_type} trading form coming soon! For now, use the Stock form and add notes about the asset type.")
        
        # Show a simplified form for other asset types
        with st.form(f"{asset_type.lower().replace(' ', '_')}_trade_form"):
            col1, col2 = st.columns(2)
            with col1:
                trade_date = st.date_input("📅 Date", value=date.today())
            with col2:
                trade_time = st.time_input("🕐 Time", value=datetime.now().time())
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("🏷️ Symbol", placeholder="Enter symbol")
            with col2:
                trade_type = st.selectbox("📊 Trade Type", ["Buy", "Sell"])
            
            col1, col2 = st.columns(2)
            with col1:
                price = st.number_input("💰 Price ($)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                quantity = st.number_input("📦 Quantity", min_value=0.0, step=0.01)
            
            notes = st.text_area("📝 Notes", placeholder=f"Enter details about this {asset_type} trade...")
            
            submitted = st.form_submit_button(f"📝 Submit {asset_type} Trade", width='stretch')
            
            if submitted:
                if ticker and price > 0 and quantity > 0:
                    try:
                        trade_data = {
                            'date': datetime.combine(trade_date, trade_time),
                            'ticker': ticker.upper(),
                            'asset_type': asset_type.split()[1],  # Remove emoji
                            'trade_type': trade_type,
                            'price': price,
                            'quantity': quantity,
                            'fees': 0.0,
                            'notes': f"{asset_type}: {notes}",
                            'currency': 'USD'
                        }
                        
                        trade_id = st.session_state.db.add_trade(trade_data)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        
                        st.success(f"✅ {asset_type} Trade #{trade_id} added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding trade: {str(e)}")
                else:
                    st.error("❌ Please fill in all required fields")

# Tab 3: Analysis
with tab3:
    st.header("📊 Trading Analysis")
    
    if st.session_state.trades_df.empty:
        st.warning("No trades found. Add some trades to see analysis.")
    else:
        # Calculate metrics
        metrics = TradingCalculator.calculate_metrics(st.session_state.trades_df)
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", f"{metrics.get('total_trades', 0)}")
        
        with col2:
            total_pnl = metrics.get('total_pnl', 0)
            st.metric("Total P&L", f"${total_pnl:.2f}", delta=f"{total_pnl:.2f}")
        
        with col3:
            win_rate = metrics.get('win_rate', 0)
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col4:
            profit_factor = metrics.get('profit_factor', 0)
            st.metric("Profit Factor", f"{profit_factor:.2f}")
        
        # Additional metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_win = metrics.get('avg_win', 0)
            st.metric("Avg Win", f"${avg_win:.2f}")
        
        with col2:
            avg_loss = metrics.get('avg_loss', 0)
            st.metric("Avg Loss", f"${avg_loss:.2f}")
        
        with col3:
            max_drawdown = metrics.get('max_drawdown', 0)
            st.metric("Max Drawdown", f"${max_drawdown:.2f}")
        
        with col4:
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        # Risk management section
        st.markdown("---")
        st.subheader("🎯 Risk Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            account_value = st.number_input("Account Value ($)", min_value=0.0, value=10000.0, step=1000.0)
        
        with col2:
            if st.button("Calculate Risk Metrics"):
                risk_data = {
                    'price': 100.0,  # Example price
                    'win_rate': win_rate / 100,
                    'avg_win': avg_win,
                    'avg_loss': abs(avg_loss)
                }
                
                risk_metrics = TradingCalculator.calculate_risk_metrics(account_value, risk_data)
                
                st.info(f"**1% Risk Amount:** ${risk_metrics['one_percent_risk']:.2f}")
                st.info(f"**Max Shares (1% Risk):** {risk_metrics['max_shares_1pct']}")
                st.info(f"**Kelly Percentage:** {risk_metrics['kelly_percentage']:.1%}")
        
        # Trade analysis table
        st.markdown("---")
        st.subheader("📋 Detailed Trade Analysis")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_filter = st.selectbox("Filter by Ticker", ["All"] + list(st.session_state.trades_df['ticker'].unique()))
        
        with col2:
            asset_filter = st.selectbox("Filter by Asset Type", ["All"] + list(st.session_state.trades_df['asset_type'].unique()))
        
        with col3:
            date_range = st.date_input("Date Range", value=[st.session_state.trades_df['date'].min().date(), st.session_state.trades_df['date'].max().date()])
        
        # Apply filters
        filtered_df = st.session_state.trades_df.copy()
        
        if ticker_filter != "All":
            filtered_df = filtered_df[filtered_df['ticker'] == ticker_filter]
        
        if asset_filter != "All":
            filtered_df = filtered_df[filtered_df['asset_type'] == asset_filter]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
        
        # Display filtered results
        if not filtered_df.empty:
            st.dataframe(filtered_df, width='stretch')
        else:
            st.warning("No trades match the selected filters.")

# Tab 4: Charts
with tab4:
    st.header("📈 Trading Charts & Visualizations")
    
    if st.session_state.trades_df.empty:
        st.warning("No trades found. Add some trades to see charts.")
    else:
        # Chart selection
        chart_type = st.selectbox(
            "Select Chart Type",
            [
                "Equity Curve",
                "Win/Loss Distribution", 
                "Monthly Returns",
                "Drawdown Chart",
                "Ticker Performance",
                "Asset Type Performance",
                "Trade Size Distribution",
                "Metrics Dashboard",
                "Correlation Heatmap",
                "Time Series Analysis"
            ]
        )
        
        # Generate selected chart
        if chart_type == "Equity Curve":
            fig = ChartGenerator.create_equity_curve(st.session_state.trades_df)
        elif chart_type == "Win/Loss Distribution":
            fig = ChartGenerator.create_win_loss_chart(st.session_state.trades_df)
        elif chart_type == "Monthly Returns":
            fig = ChartGenerator.create_monthly_returns_chart(st.session_state.trades_df)
        elif chart_type == "Drawdown Chart":
            fig = ChartGenerator.create_drawdown_chart(st.session_state.trades_df)
        elif chart_type == "Ticker Performance":
            fig = ChartGenerator.create_ticker_performance_chart(st.session_state.trades_df)
        elif chart_type == "Asset Type Performance":
            fig = ChartGenerator.create_asset_type_chart(st.session_state.trades_df)
        elif chart_type == "Trade Size Distribution":
            fig = ChartGenerator.create_trade_size_distribution(st.session_state.trades_df)
        elif chart_type == "Metrics Dashboard":
            fig = ChartGenerator.create_metrics_dashboard(st.session_state.trades_df)
        elif chart_type == "Correlation Heatmap":
            fig = ChartGenerator.create_correlation_heatmap(st.session_state.trades_df)
        elif chart_type == "Time Series Analysis":
            fig = ChartGenerator.create_time_series_analysis(st.session_state.trades_df)
        
        # Display chart
        st.plotly_chart(fig, width='stretch')
        
        # Export options
        st.markdown("---")
        st.subheader("📤 Export Chart")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📷 Export as PNG", width='stretch'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    if ChartExporter.export_chart_as_png(fig, tmp_file.name):
                        with open(tmp_file.name, "rb") as file:
                            st.download_button(
                                label="Download PNG",
                                data=file.read(),
                                file_name=f"{chart_type.lower().replace(' ', '_')}.png",
                                mime="image/png"
                            )
                    else:
                        st.error("Failed to export PNG")
        
        with col2:
            if st.button("📄 Export as PDF", width='stretch'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    if ChartExporter.export_chart_as_pdf(fig, tmp_file.name):
                        with open(tmp_file.name, "rb") as file:
                            st.download_button(
                                label="Download PDF",
                                data=file.read(),
                                file_name=f"{chart_type.lower().replace(' ', '_')}.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error("Failed to export PDF")
        
        with col3:
            if st.button("🌐 Export as HTML", width='stretch'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                    if ChartExporter.export_chart_as_html(fig, tmp_file.name):
                        with open(tmp_file.name, "rb") as file:
                            st.download_button(
                                label="Download HTML",
                                data=file.read(),
                                file_name=f"{chart_type.lower().replace(' ', '_')}.html",
                                mime="text/html"
                            )
                    else:
                        st.error("Failed to export HTML")

# Tab 5: Calendar
with tab5:
    st.header("📅 Trading Calendar")
    
    if st.session_state.trades_df.empty:
        st.warning("No trades found. Add some trades to see the calendar view.")
    else:
        # Calendar view options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            view_type = st.selectbox("📊 View Type", ["Monthly", "Weekly", "Daily"])
        
        with col2:
            year = st.selectbox("📅 Year", range(2020, 2030), index=len(range(2020, 2030))-1)
        
        with col3:
            if view_type == "Monthly":
                month = st.selectbox("📆 Month", range(1, 13), index=datetime.now().month-1)
            else:
                month = None
        
        # Calculate daily P&L
        trades_df = st.session_state.trades_df.copy()
        trades_df['date_only'] = trades_df['date'].dt.date
        
        # Group by date and calculate daily P&L
        daily_pnl = trades_df.groupby('date_only').agg({
            'realized_pnl': 'sum',
            'unrealized_pnl': 'sum',
            'total_cost': 'sum',
            'ticker': 'count'
        }).reset_index()
        
        daily_pnl['total_pnl'] = daily_pnl['realized_pnl'] + daily_pnl['unrealized_pnl']
        
        # Rename columns and ensure Date is datetime
        daily_pnl = daily_pnl.rename(columns={
            'date_only': 'Date',
            'realized_pnl': 'Realized P&L',
            'unrealized_pnl': 'Unrealized P&L',
            'total_cost': 'Total Cost',
            'ticker': 'Trade Count',
            'total_pnl': 'Total P&L'
        })
        
        # Ensure Date column is datetime
        daily_pnl['Date'] = pd.to_datetime(daily_pnl['Date'])
        
        # Filter by selected period
        if view_type == "Monthly" and month:
            daily_pnl = daily_pnl[
                (daily_pnl['Date'].dt.year == year) & 
                (daily_pnl['Date'].dt.month == month)
            ]
        elif view_type == "Yearly":
            daily_pnl = daily_pnl[daily_pnl['Date'].dt.year == year]
        
        if not daily_pnl.empty:
            # Display calendar-style view
            st.markdown("### 📊 Daily P&L Summary")
            
            # Create a calendar-like display
            display_pnl = daily_pnl.copy()
            display_pnl['Date'] = display_pnl['Date'].dt.strftime('%Y-%m-%d')
            display_pnl['Realized P&L'] = display_pnl['Realized P&L'].apply(lambda x: f"${x:.2f}")
            display_pnl['Unrealized P&L'] = display_pnl['Unrealized P&L'].apply(lambda x: f"${x:.2f}")
            display_pnl['Total P&L'] = display_pnl['Total P&L'].apply(lambda x: f"${x:.2f}")
            display_pnl['Total Cost'] = display_pnl['Total Cost'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(display_pnl, width='stretch')
            
            # Summary statistics
            st.markdown("### 📈 Period Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = daily_pnl['Trade Count'].sum()
                st.metric("Total Trades", total_trades)
            
            with col2:
                total_realized = daily_pnl['Realized P&L'].sum()
                st.metric("Total Realized P&L", f"${total_realized:.2f}")
            
            with col3:
                total_unrealized = daily_pnl['Unrealized P&L'].sum()
                st.metric("Total Unrealized P&L", f"${total_unrealized:.2f}")
            
            with col4:
                total_pnl = daily_pnl['Total P&L'].sum()
                st.metric("Total P&L", f"${total_pnl:.2f}")
            
            # Best and worst days
            st.markdown("### 🏆 Best & Worst Days")
            col1, col2 = st.columns(2)
            
            with col1:
                best_day = daily_pnl.loc[daily_pnl['Total P&L'].idxmax()]
                st.success(f"**Best Day:** {best_day['Date'].strftime('%Y-%m-%d')} - ${best_day['Total P&L']:.2f}")
            
            with col2:
                worst_day = daily_pnl.loc[daily_pnl['Total P&L'].idxmin()]
                st.error(f"**Worst Day:** {worst_day['Date'].strftime('%Y-%m-%d')} - ${worst_day['Total P&L']:.2f}")
            
            # Create a simple calendar heatmap
            st.markdown("### 📅 P&L Heatmap")
            
            # Create a simple heatmap using st.bar_chart
            chart_data = daily_pnl.set_index('Date')['Total P&L']
            
            st.bar_chart(chart_data)
            
        else:
            st.info(f"No trades found for the selected {view_type.lower()} period.")
        
        # Recent trades in calendar context
        st.markdown("---")
        st.subheader("📋 Recent Trades")
        
        recent_trades = st.session_state.trades_df.head(10)
        if not recent_trades.empty:
            display_df = recent_trades[['date', 'ticker', 'asset_type', 'trade_type', 'price', 'quantity', 'total_cost', 'realized_pnl']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
            display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:.2f}")
            display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(display_df, width='stretch')

# Tab 6: Data Management (moved AI Insights here)
with tab6:
    st.header("🤖 AI Trading Insights")
    
    if st.session_state.trades_df.empty:
        st.warning("No trades found. Add some trades to get AI insights.")
    else:
        # Generate insights
        insights = AIInsights.generate_insights(st.session_state.trades_df)
        
        # Display insights
        for i, insight in enumerate(insights, 1):
            st.markdown(f"**{i}.** {insight}")
        
        # Additional analysis
        st.markdown("---")
        st.subheader("📊 Pattern Analysis")
        
        # Best performing ticker
        if not st.session_state.trades_df.empty:
            ticker_pnl = st.session_state.trades_df.groupby('ticker')['realized_pnl'].sum().sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top Performers")
                top_3 = ticker_pnl.head(3)
                for ticker, pnl in top_3.items():
                    if pnl > 0:
                        st.success(f"{ticker}: ${pnl:.2f}")
                    else:
                        st.info(f"{ticker}: ${pnl:.2f}")
            
            with col2:
                st.subheader("📉 Underperformers")
                bottom_3 = ticker_pnl.tail(3)
                for ticker, pnl in bottom_3.items():
                    if pnl < 0:
                        st.error(f"{ticker}: ${pnl:.2f}")
                    else:
                        st.info(f"{ticker}: ${pnl:.2f}")

    st.markdown("---")
    st.subheader("💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Export Data")
        
        # Export to CSV
        if st.button("📊 Export to CSV", width='stretch'):
            if not st.session_state.trades_df.empty:
                csv = st.session_state.trades_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
        
        # Export to Excel
        if st.button("📈 Export to Excel", width='stretch'):
            if not st.session_state.trades_df.empty:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                    if DataExporter.export_to_excel(st.session_state.trades_df, tmp_file.name):
                        with open(tmp_file.name, "rb") as file:
                            st.download_button(
                                label="Download Excel",
                                data=file.read(),
                                file_name=f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.error("Failed to export Excel file")
            else:
                st.warning("No data to export")
        
        # Create backup
        if st.button("💾 Create Backup", width='stretch'):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                if DataExporter.create_backup_zip(st.session_state.db.db_path, tmp_file.name):
                    with open(tmp_file.name, "rb") as file:
                        st.download_button(
                            label="Download Backup",
                            data=file.read(),
                            file_name=f"trades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )
                else:
                    st.error("Failed to create backup")
    
    with col2:
        st.subheader("📥 Import Data")
        
        # Import CSV
        uploaded_file = st.file_uploader("Choose CSV file", type="csv")
        if uploaded_file is not None:
            if st.button("📊 Import CSV", width='stretch'):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file.flush()
                        
                        # Import data
                        successful, failed = st.session_state.db.import_from_csv(tmp_file.name)
                        st.session_state.trades_df = st.session_state.db.get_trades()
                        
                        st.success(f"Import completed! {successful} trades imported, {failed} failed.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")
        
        # Restore from backup
        uploaded_backup = st.file_uploader("Choose backup file", type="zip")
        if uploaded_backup is not None:
            if st.button("💾 Restore Backup", width='stretch'):
                try:
                    # Save uploaded backup temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                        tmp_file.write(uploaded_backup.getvalue())
                        tmp_file.flush()
                        
                        # Restore data
                        if DataExporter.restore_from_zip(tmp_file.name):
                            st.session_state.trades_df = st.session_state.db.get_trades()
                            st.success("Backup restored successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to restore backup")
                except Exception as e:
                    st.error(f"Restore failed: {str(e)}")
    
    # Database statistics
    st.markdown("---")
    st.subheader("📊 Database Statistics")
    
    if not st.session_state.trades_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", len(st.session_state.trades_df))
        
        with col2:
            unique_tickers = st.session_state.trades_df['ticker'].nunique()
            st.metric("Unique Tickers", unique_tickers)
        
        with col3:
            date_range = (st.session_state.trades_df['date'].max() - st.session_state.trades_df['date'].min()).days
            st.metric("Trading Days", date_range)
        
        with col4:
            # Get database size safely
            try:
                db_path = st.session_state.db.db_path
                if os.path.exists(db_path):
                    db_size = os.path.getsize(db_path) / 1024  # KB
                    st.metric("Database Size", f"{db_size:.1f} KB")
                else:
                    st.metric("Database Size", "0 KB")
            except:
                st.metric("Database Size", "N/A")

# Tab 7: About
with tab7:
    st.header("ℹ️ About TradeForge")
    
    st.markdown("""
    ### 🚀 Welcome to TradeForge!
    
    **TradeForge** is a free, open-source trading journal desktop application designed to be a local alternative to TradesViz with all premium features unlocked.
    
    ### ✨ Features
    
    - **📝 Trade Entry**: Easy-to-use forms for stocks and options
    - **📊 Analysis**: Comprehensive trading metrics and statistics
    - **📈 Charts**: Beautiful visualizations with Plotly
    - **🤖 AI Insights**: Rule-based trading pattern analysis
    - **💾 Data Management**: Import/export and backup functionality
    - **🏠 Local Storage**: All data stored locally in SQLite
    - **🆓 Free & Open Source**: No limits, no subscriptions
    
    ### 🛠️ Technology Stack
    
    - **Frontend**: Streamlit
    - **Database**: SQLite with SQLAlchemy
    - **Charts**: Plotly
    - **Data Processing**: Pandas
    - **Market Data**: yfinance (optional)
    
    ### 🚀 Getting Started
    
    1. **Install Dependencies**: `pip install -r requirements.txt`
    2. **Run Application**: `streamlit run app.py`
    3. **Add Trades**: Use the Trade Entry tab to add your first trade
    4. **View Analysis**: Check the Analysis tab for metrics
    5. **Explore Charts**: Use the Charts tab for visualizations
    
    ### 📁 File Structure
    
    ```
    TradeForge/
    ├── app.py              # Main Streamlit application
    ├── data.py             # Database models and operations
    ├── utils.py            # Utility functions and calculations
    ├── charts.py           # Plotly chart generation
    ├── requirements.txt    # Python dependencies
    ├── README.md          # Documentation
    └── .gitignore         # Git ignore rules
    ```
    
    ### 🔧 Configuration
    
    - **Database**: User-specific database files (e.g., `trades_username.db`)
    - **Port**: Default Streamlit port (8501)
    - **Theme**: Light/Dark mode support
    - **Mobile**: Responsive design for local viewing
    
    ### 🤝 Contributing
    
    TradeForge is open source! Feel free to:
    - Report bugs
    - Suggest features
    - Submit pull requests
    - Improve documentation
    
    ### 📄 License
    
    This project is licensed under the MIT License - see the LICENSE file for details.
    
    ### 🙏 Acknowledgments
    
    - Inspired by TradesViz
    - Built with Streamlit, Plotly, and SQLAlchemy
    - Market data provided by yfinance
    
    ---
    
    **Happy Trading! 📈**
    """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>TradeForge v1.0.0 | Made with ❤️ for traders | 
            <a href='https://github.com/yourusername/tradeforge' target='_blank'>GitHub</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        <p>TradeForge - Your Local Trading Journal | 
        <a href='https://github.com/yourusername/tradeforge' target='_blank'>GitHub</a> | 
        <a href='#' onclick='alert("TradeForge v1.0.0")'>About</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
