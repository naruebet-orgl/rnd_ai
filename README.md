# 🧴 AI01_01_myskin_scraper

A comprehensive data collection and analysis toolkit for cosmetic product information and ingredient formulation research.

Google Drive (Raws Data)

https://drive.google.com/drive/folders/10htwGUZmsa3-XUg9TjnihBevG6_Cm-Pt?usp=drive_link

## 📋 Project Overview

This repository contains two main components:
1. **MySkin Web Scraper** - Ultra-fast cosmetic product data collection from MySkinRecipes
2. **Internal R&D Data Processing** - Ingredient and formula analysis tools for cosmetic formulation research

## 🚀 Features

### MySkin Scraping Module
- **Ultra-fast scraping**: Collect 9,000+ cosmetic products in 30-60 minutes
- **20 parallel workers** for maximum efficiency
- **Direct URL scraping** bypassing slow category processing
- **Progress saving** - No data loss with incremental saves every 500 products
- **Comprehensive data extraction** - 30+ product fields including ingredients, benefits, specifications
- **Multiple output formats** - JSON, CSV, TSV, Excel

### Internal R&D Module
- **SQL data processing** from MySQL dumps
- **Ingredient analysis** with comprehensive ingredient database
- **Formula processing** with ingredient-formula relationships
- **Data verification** and quality control
- **Pandas-based data manipulation** for research workflows

## 📁 Project Structure

```
AI01_01_myskin_scraper/
├── README.md                              # This file
├── .gitignore                            # Git ignore patterns
│
├── myskin_scraping/                      # 🕷️ Web Scraping Module
│   ├── Enhanced_Dynamic_Scraper.ipynb   # 🚀 Main ultra-fast scraping notebook
│   ├── myskin_scraper.py                # Core scraper class implementation
│   ├── check_progress.py                # Progress monitoring utilities
│   ├── verify.ipynb                     # Data verification notebook
│   ├── requirements.txt                 # Python dependencies
│   ├── README.md                        # Detailed scraping documentation
│   ├── scraping_log.txt                 # Scraping operation logs
│   ├── results/                         # Metadata and discovered categories
│   │   ├── discovered_categories.json
│   │   ├── progress_summary_*.json
│   │   └── remaining_categories_*.json
│   └── raws/                            # 📁 Scraped data output (excluded from git)
│       ├── ALL_PRODUCTS_*.csv
│       ├── ALL_PRODUCTS_*.json
│       ├── ALL_PRODUCTS_*.tsv
│       └── ALL_PRODUCTS_*.xlsx
│
└── internal_raw/                        # 🧪 R&D Data Processing Module
    ├── extract_ingredients_formulas.py  # SQL data extraction script
    ├── ingredients_formulas_examples.py # Usage examples and workflows
    ├── verify.ipynb                     # Data verification notebook
    ├── active_ingredients.csv           # Processed active ingredients data
    ├── ingredients.csv                  # Complete ingredients database
    ├── ingredients_data.csv             # Enhanced ingredients with metadata
    ├── formulas.csv                     # Formula definitions
    ├── formulas_data.csv                # Enhanced formula data
    ├── formula_ingredients.csv          # Formula-ingredient relationships
    ├── formula_ingredients_data.csv     # Enhanced relationship data
    ├── formulas_with_ingredients_data.csv # Complete formula compositions
    └── Organics RD Sept 16 2025.sql    # MySQL dump (excluded from git)
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Organics-AI-Team/AI01_01_myskin_scraper.git
   cd AI01_01_myskin_scraper
   ```

2. **Install dependencies**
   ```bash
   cd myskin_scraping
   pip install -r requirements.txt
   ```

3. **Additional dependencies for R&D module**
   ```bash
   pip install pandas sqlalchemy mysql-connector-python
   ```

## 🎯 Quick Start

### MySkin Data Scraping

1. **Navigate to scraping module**
   ```bash
   cd myskin_scraping
   ```

2. **Open the main notebook**
   ```bash
   jupyter notebook Enhanced_Dynamic_Scraper.ipynb
   ```

3. **Run the ultra-fast scraper**
   - Execute cells 1-3 for immediate results
   - Monitor progress in real-time
   - Find results in the `raws/` folder

### R&D Data Processing

1. **Navigate to internal module**
   ```bash
   cd internal_raw
   ```

2. **Extract data from SQL dump**
   ```python
   python extract_ingredients_formulas.py
   ```

3. **Explore the data**
   ```bash
   jupyter notebook verify.ipynb
   ```

## 📊 Data Output

### MySkin Scraping Results
- **Product data**: 9,000+ cosmetic products with complete specifications
- **Ingredients**: Comprehensive ingredient lists with INCI names
- **Benefits**: Product claims and benefits
- **Categories**: Organized by skincare categories
- **Formats**: JSON, CSV, TSV, Excel

### R&D Processing Results
- **Ingredients database**: 1,000+ cosmetic ingredients with properties
- **Formulas**: Complete formulation data with percentages
- **Relationships**: Ingredient-formula mappings
- **Analysis**: Data quality metrics and verification

## 🔧 Configuration

### Scraping Configuration
- **Workers**: Adjust parallel workers (default: 20)
- **Delay**: Configure request delays for rate limiting
- **Filters**: Customize product category filters
- **Output**: Select output formats and locations

### R&D Configuration
- **Database**: MySQL connection parameters
- **Processing**: Data cleaning and validation rules
- **Export**: Output format preferences

## 📈 Performance

### MySkin Scraper
- **Speed**: 9,000+ products in 30-60 minutes
- **Efficiency**: 100x faster than category-based scraping
- **Reliability**: Auto-recovery and progress saving
- **Quality**: Complete data extraction with validation

### R&D Processing
- **Capacity**: Handles SQL dumps 150MB+
- **Performance**: Pandas-optimized data operations
- **Memory**: Efficient chunked processing for large datasets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is for internal R&D use at Organics AI Team.

## 👥 Team

- **Organics AI Team** - Research & Development
- **Project**: AI01_01 - Cosmetic Data Intelligence

## 🆘 Support

For questions or support:
1. Check the module-specific README files
2. Review the Jupyter notebooks for examples
3. Contact the Organics AI Team

## 🔄 Version History

- **v1.0.0** - Initial release with ultra-fast scraper and R&D processing tools
- **v1.0.1** - Added comprehensive documentation and examples

---

*Empowering cosmetic R&D with intelligent data collection and analysis*
