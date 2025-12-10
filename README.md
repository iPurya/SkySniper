# SkySniper ✈️

> Find the Cheapest Flights, Automatically.

SkySniper is a smart flight scraping and monitoring tool designed to help travelers save money. Unlike standard search engines, SkySniper works for you 24/7. It aggregates flight data from multiple booking platforms, compares prices, and identifies the most cost-effective options.

## 🎯 Key Value Proposition

The core feature of SkySniper is its **"Last-Minute Drop"** detection. It continuously polls flight data up until the departure time. If a seat price drops due to last-minute cancellations or airline algorithm changes, SkySniper instantly notifies you, ensuring you never miss a deal.

## ✨ Features

- 🕷️ **Multi-Source Scraping**: Fetches data from various flight booking websites concurrently
- 📉 **Smart Comparison**: Aggregates and sorts results to highlight the absolute cheapest fare
- 🔔 **Real-Time Price Monitoring**: Watch specific routes and get alerted when prices drop
- ⏳ **Continuous Monitoring**: Runs periodic checks automatically with customizable intervals
- 📊 **Open Source & Extensible**: Easy to add new scraper modules for different airlines

## 📡 Supported Sources

| Source | Website | Status |
|--------|---------|--------|
| Alibaba | [alibaba.ir](https://alibaba.ir) | ✅ Ready |
| Ataair | [ataair.ir](https://ataair.ir) | ✅ Ready |
| MrBilit | [mrbilit.com](https://mrbilit.com) | ✅ Ready |

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/skysniper.git
cd skysniper
```

2. **Install the package**

```bash
# Install in editable mode (recommended for development)
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

3. **Verify installation**

```bash
skysniper --version
```

## 📖 Usage

### Search for Flights

Search for flights from Tehran (THR) to Istanbul (IST):

```bash
skysniper search THR IST 2025-01-15
```

With passengers:

```bash
skysniper search THR IST 2025-01-15 --adults 2 --children 1
```

Using specific sources:

```bash
skysniper search THR IST 2025-01-15 --source alibaba --source mrbilit
```

For domestic flights (Iran internal):

```bash
skysniper search THR MHD 2025-01-15 --domestic
```

### List Available Sources

```bash
skysniper sources
```

Output:
```
      Available Flight Sources      
┏━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Name    ┃ Status   ┃ Website     ┃
┡━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Alibaba │ ✅ Ready │ alibaba.ir  │
│ Ataair  │ ✅ Ready │ ataair.ir   │
│ Mrbilit │ ✅ Ready │ mrbilit.com │
└─────────┴──────────┴─────────────┘
```

### Monitor Prices

Continuously monitor a route for price drops:

```bash
skysniper monitor THR IST 2025-01-15
```

With a target price alert (in Rials):

```bash
skysniper monitor THR IST 2025-01-15 --target-price 50000000
```

Custom check interval (in seconds):

```bash
skysniper monitor THR IST 2025-01-15 --interval 300
```

Press `Ctrl+C` to stop monitoring.

### Command Reference

```bash
# Get help
skysniper --help
skysniper search --help
skysniper monitor --help

# Search options
skysniper search ORIGIN DEST DATE [OPTIONS]
  --adults, -a      Number of adult passengers (default: 1)
  --children, -c    Number of children (default: 0)
  --infants, -i     Number of infants (default: 0)
  --source, -s      Specific source(s) to use (can be repeated)
  --domestic        Search domestic flights only

# Monitor options
skysniper monitor ORIGIN DEST DATE [OPTIONS]
  --interval        Check interval in seconds (default: 60)
  --target-price    Alert when price drops below this (in Rials)
  --adults, -a      Number of adult passengers (default: 1)
```

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=skysniper

# Run specific test file
pytest tests/test_mrbilit.py -v
```

### Project Structure

```
skysniper/
├── __init__.py          # Package info & version
├── __main__.py          # Entry point for python -m skysniper
├── skysniper.py         # CLI application (click)
└── scrapers/
    ├── __init__.py      # Scraper registry
    ├── base.py          # Base classes (Flight, SearchParams, BaseScraper)
    ├── alibaba.py       # Alibaba.ir scraper
    ├── ataair.py        # Ataair.ir scraper
    └── mrbilit.py       # MrBilit.com scraper

tests/
├── conftest.py          # Pytest fixtures
├── test_base.py         # Base class tests
├── test_alibaba.py      # Alibaba scraper tests
├── test_ataair.py       # Ataair scraper tests
├── test_mrbilit.py      # MrBilit scraper tests
├── test_cli.py          # CLI tests
└── test_scrapers_registry.py
```

### Adding a New Scraper

1. Create a new file in `skysniper/scrapers/`:

```python
from skysniper.scrapers.base import BaseScraper, Flight, SearchParams

class MyScraper(BaseScraper):
    name = "myscraper"
    base_url = "https://example.com"

    async def search(self, params: SearchParams) -> list[Flight]:
        # Implement your scraping logic
        pass
```

2. Register it in `skysniper/scrapers/__init__.py`:

```python
from skysniper.scrapers.myscraper import MyScraper

SCRAPERS["myscraper"] = MyScraper
```

3. Add source info in `skysniper/skysniper.py`:

```python
source_info = {
    # ...
    "myscraper": ("✅ Ready", "example.com"),
}
```

## 🛣️ Roadmap

- [ ] Add more scrapers (Snapptrip, Flightio, etc.)
- [ ] Telegram/Email notifications
- [ ] Price history database
- [ ] Web dashboard
- [ ] Docker support
- [ ] And maybe will add deskto/android app

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

See the [LICENSE](LICENSE) file for details.

---

Made with ❤️ for budget-conscious travelers
