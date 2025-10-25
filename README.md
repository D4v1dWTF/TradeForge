# 📈 TradeForge - Local Trading Journal

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

**TradeForge** is a free, open-source trading journal desktop application designed to be a local alternative to TradesViz with all premium features unlocked. It runs entirely on your local machine with no internet dependency for core functionality.

## ✨ Features

### 🎯 Core Functionality
- **📝 Trade Entry**: Easy-to-use forms for stocks and options
- **📊 Analysis**: Comprehensive trading metrics and statistics  
- **📈 Charts**: Beautiful visualizations with Plotly
- **🤖 AI Insights**: Rule-based trading pattern analysis
- **💾 Data Management**: Import/export and backup functionality
- **🏠 Local Storage**: All data stored locally in SQLite
- **🆓 Free & Open Source**: No limits, no subscriptions

### 📊 Trading Features
- **Stock Trading**: Support for US and HK stocks
- **Options Trading**: Call/Put options with strike prices and expiration dates
- **P&L Tracking**: Realized and unrealized profit/loss calculations
- **Risk Management**: 1% risk calculations and position sizing
- **Portfolio Analysis**: 20+ key performance indicators
- **Chart Export**: Export charts as PNG, PDF, or HTML

### 🔧 Technical Features
- **Local Database**: SQLite with automatic migration
- **Responsive Design**: Mobile-friendly interface
- **Data Export**: CSV, Excel, and ZIP backup formats
- **Live Prices**: Optional yfinance integration for real-time quotes
- **Error Handling**: Robust error handling and validation
- **Cross-Platform**: Windows, macOS, and Linux support

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tradeforge.git
   cd tradeforge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, manually navigate to the URL

### Windows One-Click Setup

For Windows users, you can use the provided setup script:

1. **Download the repository**
2. **Double-click `setup.bat`**
3. **Follow the on-screen instructions**

## 📁 Project Structure

```
TradeForge/
├── app.py              # Main Streamlit application
├── data.py             # Database models and operations
├── utils.py            # Utility functions and calculations
├── charts.py           # Plotly chart generation
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── setup.bat          # Windows setup script
└── trades.db          # SQLite database (created on first run)
```

## 🎮 Usage Guide

### Adding Your First Trade

1. **Open the Trade Entry tab**
2. **Fill in the trade details**:
   - Date and time
   - Ticker symbol (e.g., AAPL, NVDA, 0700.HK)
   - Asset type (Stock or Option)
   - Trade type (Buy or Sell)
   - Price and quantity
   - Fees (optional)
   - Notes (optional)

3. **Click Submit Trade**
4. **View your trade in the Recent Trades section**

### Analyzing Your Performance

1. **Go to the Analysis tab**
2. **View key metrics**:
   - Total trades and P&L
   - Win rate and profit factor
   - Average win/loss
   - Maximum drawdown
   - Sharpe ratio

3. **Use filters** to analyze specific:
   - Tickers
   - Asset types
   - Date ranges

### Creating Charts

1. **Navigate to the Charts tab**
2. **Select a chart type**:
   - Equity Curve
   - Win/Loss Distribution
   - Monthly Returns
   - Drawdown Chart
   - Ticker Performance
   - And more...

3. **Export charts** as PNG, PDF, or HTML

### Getting AI Insights

1. **Visit the AI Insights tab**
2. **Review automated analysis**:
   - Win rate analysis
   - Profit factor insights
   - Drawdown warnings
   - Trading frequency recommendations
   - Best/worst performers

## 🔧 Configuration

### Database
- **Location**: `trades.db` in the project root
- **Type**: SQLite (no setup required)
- **Backup**: Use the Data Management tab

### Market Data
- **Live Prices**: Optional yfinance integration
- **Offline Mode**: Works without internet
- **Currency Support**: USD and HKD

### Customization
- **Themes**: Light/Dark mode support
- **Charts**: Customizable colors and styles
- **Export**: Multiple format options

## 📊 Supported Markets

### US Markets
- **Stocks**: NYSE, NASDAQ
- **Options**: All major exchanges
- **Currency**: USD

### International Markets
- **Hong Kong**: HKEX stocks (e.g., 0700.HK)
- **Currency**: HKD with manual conversion
- **Other**: Extensible for additional markets

## 🛠️ Development

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tradeforge.git
   cd tradeforge
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run in development mode**
   ```bash
   streamlit run app.py --server.runOnSave true
   ```

### Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Code Structure

- **`app.py`**: Main Streamlit application with UI
- **`data.py`**: Database models and operations
- **`utils.py`**: Utility functions and calculations
- **`charts.py`**: Plotly chart generation
- **`requirements.txt`**: Python dependencies

## 🐛 Troubleshooting

### Common Issues

**Port already in use**
```bash
streamlit run app.py --server.port 8502
```

**Database locked**
- Close any other instances of the app
- Check if `trades.db` is being used by another process

**Import errors**
```bash
pip install --upgrade -r requirements.txt
```

**Permission errors on Windows**
- Run Command Prompt as Administrator
- Or use the provided `setup.bat` script

### Getting Help

1. **Check the Issues tab** on GitHub
2. **Create a new issue** with:
   - Operating system
   - Python version
   - Error message
   - Steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TradesViz**: Inspiration for the feature set
- **Streamlit**: Amazing framework for data apps
- **Plotly**: Beautiful interactive charts
- **SQLAlchemy**: Robust database ORM
- **yfinance**: Market data integration

## 🔮 Roadmap

### Version 1.1
- [ ] Advanced charting options
- [ ] More AI insights
- [ ] Portfolio rebalancing tools
- [ ] Tax reporting features

### Version 1.2
- [ ] Mobile app (React Native)
- [ ] Cloud sync (optional)
- [ ] Advanced risk metrics
- [ ] Options strategy analyzer

### Version 2.0
- [ ] Multi-account support
- [ ] Advanced backtesting
- [ ] Social features
- [ ] Plugin system


---

**Happy Trading! 📈**

*TradeForge - Your Local Trading Journal*

