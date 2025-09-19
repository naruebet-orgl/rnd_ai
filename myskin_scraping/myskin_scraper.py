#!/usr/bin/env python3
"""
MySkinRecipes.com Web Scraper
Scrapes all product data from the Thai shop section including drilling down into categories and individual products.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import csv
from dataclasses import dataclass, asdict
import re
import html
from urllib.parse import unquote

@dataclass
class Product:
    name: str
    url: str
    price: Optional[str] = None
    original_price: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    usage: Optional[str] = None
    images: Optional[List[str]] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    rating: Optional[str] = None
    reviews_count: Optional[int] = None
    availability: Optional[str] = None
    sku: Optional[str] = None
    tags: Optional[List[str]] = None
    # Enhanced data extraction fields
    detailed_info: Optional[str] = None
    mechanism: Optional[str] = None
    appearance: Optional[str] = None
    storage: Optional[str] = None
    shelf_life: Optional[str] = None
    dosage: Optional[str] = None
    recommended_dosage: Optional[str] = None
    mix_method: Optional[str] = None
    heat_resistance: Optional[str] = None
    ph_stability: Optional[str] = None
    solubility: Optional[str] = None
    product_types: Optional[str] = None
    inci_name: Optional[str] = None
    coa_specifications: Optional[List[Dict[str, str]]] = None
    sample_products: Optional[List[str]] = None
    # Dynamic fields from data attributes
    usage_percent_lo: Optional[str] = None
    usage_percent_hi: Optional[str] = None
    usage_percent_best: Optional[str] = None
    internal_type: Optional[str] = None
    cost: Optional[str] = None
    lot: Optional[str] = None
    exp_date: Optional[str] = None
    product_type: Optional[str] = None
    id_product: Optional[str] = None
    stock_lot: Optional[str] = None
    stock_expdate: Optional[str] = None
    minimal_qty: Optional[str] = None
    product_reagent: Optional[str] = None

class MySkinRecipesScraper:
    def __init__(self, max_retries=3, batch_size=50, categories_file=None):
        self.base_url = "https://www.myskinrecipes.com"
        self.shop_url = "https://www.myskinrecipes.com/shop/th/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.products = []
        self.categories = []
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.failed_urls = []
        self.categories_file = categories_file
        self.discovered_categories = []
        self.category_patterns = []

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Load discovered categories if file provided
        self._load_discovered_categories()

    def _load_discovered_categories(self):
        """Load discovered categories and generate dynamic patterns"""
        if self.categories_file:
            try:
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    self.discovered_categories = json.load(f)

                self.logger.info(f"Loaded {len(self.discovered_categories)} discovered categories")

                # Generate dynamic patterns from discovered categories
                category_paths = set()
                for category in self.discovered_categories:
                    url = category.get('url', '')
                    if '/shop/th/' in url:
                        # Extract the path part after /shop/th/
                        path_part = url.split('/shop/th/')[-1]
                        if path_part and '-' in path_part:
                            # Extract category identifier (everything after first number-)
                            parts = path_part.split('-', 1)
                            if len(parts) > 1:
                                category_identifier = parts[1]
                                category_paths.add(category_identifier)

                # Convert to CSS selectors for product links
                self.category_patterns = [f'a[href*="/{path}/"]' for path in list(category_paths)[:100]]
                self.logger.info(f"Generated {len(self.category_patterns)} dynamic category patterns")

            except Exception as e:
                self.logger.warning(f"Could not load categories file {self.categories_file}: {e}")

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Fetching: {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Check if we got actual content
                if not response.content or len(response.content) < 100:
                    self.logger.warning(f"Page returned minimal content: {url}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None

                soup = BeautifulSoup(response.content, 'html.parser')

                # Basic validation - check if it looks like a product page
                if not soup.select('body'):
                    self.logger.warning(f"Invalid HTML structure: {url}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None

                return soup

            except Exception as e:
                self.logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.failed_urls.append(url)
                    return None

    def extract_categories(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract category links from main shop page - use discovered categories if available"""

        # If we have discovered categories, use them instead of scraping
        if self.discovered_categories:
            self.logger.info(f"Using {len(self.discovered_categories)} pre-discovered categories")
            return self.discovered_categories

        # Fallback to original category extraction
        categories = []

        # MySkinRecipes specific category selectors
        # Look for all links that contain category patterns
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)

            if not href or not text:
                continue

            # Skip the main shop URLs
            if href.endswith('/shop/th/') or href.endswith('/shop/th'):
                continue

            # Look for category patterns like the Anti-Aging example
            if '/shop/th/' in href:
                # Check for category ID patterns (like /11-เปปไทด์ลดริ้วรอย)
                if re.search(r'/\d+-[\w\-ก-๏]+/?$', href):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in [cat['url'] for cat in categories]:
                        categories.append({
                            'name': text,
                            'url': full_url
                        })
                        self.logger.info(f"Found category: {text} -> {full_url}")

        # Also check for nested category links in specific containers
        category_containers = soup.select('.category-list, .categories, .menu, nav')
        for container in category_containers:
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)

                if href and text and '/shop/th/' in href and not href.endswith('/shop/th/'):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in [cat['url'] for cat in categories]:
                        categories.append({
                            'name': text,
                            'url': full_url
                        })

        self.logger.info(f"Found {len(categories)} categories")
        return categories

    def extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract product links from category or listing page"""
        product_links = []

        # Start with basic selectors
        base_selectors = [
            'a.product-title.product-name-wrap',  # Main product title links
            '.product-item a',
            '.product-link',
            '.product-title a',
            '.product-card a',
            'h2 a[href*=".html"]',                # Product page links ending in .html
            'h3 a[href*=".html"]',
            'a[content*="myskinrecipes.com/shop/th/"]'  # Links with content attribute
        ]

        # Add dynamic category patterns if available
        selectors = base_selectors.copy()
        if self.category_patterns:
            selectors.extend(self.category_patterns)
            self.logger.debug(f"Using {len(self.category_patterns)} dynamic category patterns")
        else:
            # Fallback to static patterns
            fallback_selectors = [
                'a[href*="/anti-wrinkle/"]',          # Anti-wrinkle category products
                'a[href*="/moisturizer/"]',           # Moisturizer products
                'a[href*="/cleansing/"]',             # Cleansing products
                'a[href*="/vitamin/"]',               # Vitamin products
                'a[href*="/sunscreen/"]',             # Sunscreen products
                'a[href*="/whitening-"]',             # Whitening products
                'a[href*="/matte-liquid-lip/"]',      # Lip products
                'a[href*="/anti-aging/"]',            # Anti-aging products
                'a[href*="-copper-peptide"]',         # Specific product patterns
                'a[href*="-vitamin-"]',
                'a[href*="-peptide"]',
                'a[href*="-alpha-"]',                 # Alpha compounds
                'a[href*="-beta-"]',                  # Beta compounds
                'a[href*="-acid"]',                   # Acid products
            ]
            selectors.extend(fallback_selectors)
            self.logger.debug("Using fallback static patterns")

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href') or link.get('content')
                if href:
                    # Skip category-only URLs
                    if href.endswith('/shop/th/') or '/shop/th/' not in href:
                        continue

                    # Ensure it's a product page (contains product ID pattern)
                    if not re.search(r'/\d+-', href):
                        continue

                    full_url = urljoin(self.base_url, href)
                    if full_url not in product_links:
                        product_links.append(full_url)

        # Also look for pagination to get more products
        pagination_links = soup.select('.pagination a, .page-numbers a')
        for page_link in pagination_links:
            href = page_link.get('href')
            if href and 'page=' in href:
                # This indicates there are more pages - we'll handle this in scrape_category
                pass

        return product_links

    def extract_dynamic_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract all data dynamically using field names and data attributes"""
        data = {}

        try:
            # Extract data from data attributes (most reliable source)
            product_container = soup.select_one('.product-container, .js-product-container, [data-custom-modification]')
            if product_container:
                # Extract from data-custom-modification JSON
                custom_mod = product_container.get('data-custom-modification')
                if custom_mod:
                    try:
                        mod_data = json.loads(html.unescape(custom_mod))
                        if '0' in mod_data:
                            product_data = mod_data['0']
                            # Map the fields dynamically
                            data.update({
                                'usage_percent_lo': product_data.get('usage_percent_lo'),
                                'usage_percent_hi': product_data.get('usage_percent_hi'),
                                'usage_percent_best': product_data.get('usage_percent_best'),
                                'internal_type': product_data.get('internal_type'),
                                'cost': product_data.get('cost'),
                                'lot': product_data.get('lot'),
                                'exp_date': product_data.get('exp_date')
                            })

                        # Extract solubility info
                        if 'soluble' in mod_data:
                            soluble_data = mod_data['soluble']
                            if isinstance(soluble_data, list) and soluble_data:
                                data['solubility'] = soluble_data[0].get('name', '')
                    except (json.JSONDecodeError, KeyError):
                        pass

                # Extract from data-product-fields JSON
                product_fields = product_container.get('data-product-fields')
                if product_fields:
                    try:
                        fields_data = json.loads(html.unescape(product_fields))
                        data.update({
                            'product_type': fields_data.get('product_type'),
                            'id_product': fields_data.get('id_product'),
                            'stock_lot': fields_data.get('stock', {}).get('lot'),
                            'stock_expdate': fields_data.get('stock', {}).get('expdate')
                        })
                    except (json.JSONDecodeError, KeyError):
                        pass

                # Extract other data attributes
                data['internal_type'] = product_container.get('data-internal-type')
                data['minimal_qty'] = product_container.get('data-minimal-qty')
                data['product_reagent'] = product_container.get('data-product-reagent')

        except Exception as e:
            self.logger.warning(f"Error extracting dynamic data attributes: {e}")

        return data

    def extract_product_data(self, url: str, category: str = None) -> Optional[Product]:
        """Extract detailed product information from product page using completely dynamic approach"""
        soup = self.get_page(url)
        if not soup:
            self.logger.warning(f"Failed to fetch page: {url}")
            return None

        try:
            # First extract dynamic data from attributes
            dynamic_data = self.extract_dynamic_product_data(soup, url)

            # Product name - using MySkinRecipes specific selectors
            name = None
            name_selectors = [
                'h1.product-detail-header.product-name-wrap',
                '.product-title.product-name-wrap',
                'h1.product-title',
                'h1'
            ]
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    break

            # Price information
            price = None
            original_price = None
            price_selectors = [
                '.product-price .price',
                '.current-price',
                '.price-current',
                '.price',
                '[data-price]'
            ]
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price = price_elem.get_text(strip=True)
                    break

            # Original/old price
            original_price_selectors = [
                '.old-price',
                '.original-price',
                '.price-was',
                'del .price'
            ]
            for selector in original_price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    original_price = elem.get_text(strip=True)
                    break

            # Short description
            short_description = None
            short_desc_elem = soup.select_one('.product-description')
            if short_desc_elem:
                short_description = short_desc_elem.get_text(strip=True)

            # Full product info/description
            full_description = None
            full_desc_elem = soup.select_one('#product-info')
            if full_desc_elem:
                full_description = full_desc_elem.get_text(strip=True)

            # Also try alternative selectors for product info
            if not full_description:
                alt_selectors = [
                    '.product-description-full',
                    '#product-description-pdf',
                    '.product-details',
                    '.product-content'
                ]
                for selector in alt_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        full_description = elem.get_text(strip=True)
                        break

            # Combine descriptions
            description_parts = []
            if short_description:
                description_parts.append(short_description)
            if full_description:
                description_parts.append(full_description)
            description = "\n\n".join(description_parts) if description_parts else None

            # Extract INCI ingredients from the description
            ingredients = []
            if full_description:
                inci_match = re.search(r'INCI Name[:\s]*([^(]+)', full_description)
                if inci_match:
                    inci_ingredients = inci_match.group(1).strip()
                    ingredients = [ing.strip() for ing in inci_ingredients.split(',') if ing.strip()]

            # Extract comprehensive usage information dynamically
            usage_info = []

            # Use dynamic data first if available
            if dynamic_data.get('usage_percent_lo') and dynamic_data.get('usage_percent_hi'):
                usage_range = f"{dynamic_data['usage_percent_lo']}-{dynamic_data['usage_percent_hi']}%"
                if dynamic_data.get('usage_percent_best'):
                    usage_range += f" (แนะนำ {dynamic_data['usage_percent_best']}%)"
                usage_info.append(usage_range)

            # From full description (product info tab) - completely dynamic patterns
            if full_description:
                # Find ALL usage-related content without hardcoded boundaries
                usage_keywords = [
                    'อัตราการใช้', 'แนะนำ', 'ใช้', 'การใช้งาน', 'วิธีการผสม',
                    'ใช้ได้ในผลิตภัณฑ์', 'สำหรับ', 'ความเข้มข้น', 'ปริมาณ', 'วิธีใช้'
                ]

                # Split text into sentences and analyze each
                sentences = re.split(r'[.\n\r]+', full_description)
                for sentence in sentences:
                    sentence = sentence.strip()
                    # Check if sentence contains usage keywords
                    for keyword in usage_keywords:
                        if keyword in sentence:
                            # Extract the relevant part after the keyword
                            parts = sentence.split(keyword, 1)
                            if len(parts) > 1:
                                usage_part = parts[1].strip(':').strip()
                                if usage_part and len(usage_part) > 3 and usage_part not in usage_info:
                                    usage_info.append(usage_part)
                            break

                # Also look for percentage patterns anywhere in text
                percent_patterns = re.findall(r'\d+[.,]?\d*\s*%[^\n\r]*', full_description)
                for pattern in percent_patterns:
                    clean_pattern = pattern.strip()
                    if clean_pattern and clean_pattern not in usage_info:
                        usage_info.append(clean_pattern)

            usage = "\n".join(usage_info) if usage_info else None

            # Extract product characteristics
            characteristics = {}
            if full_description:
                char_patterns = [
                    (r'ลักษณะผลิตภัณฑ์[:\s]*([^การ]+)', 'appearance'),
                    (r'การละลาย[:\s]*([^การ]+)', 'solubility'),
                    (r'การเก็บรักษา[:\s]*([^INCI]+)', 'storage'),
                    (r'อุณหภูมิ[:\s]*([^\s]+)', 'temperature')
                ]
                for pattern, key in char_patterns:
                    match = re.search(pattern, full_description)
                    if match:
                        characteristics[key] = match.group(1).strip()

            # Extract benefits/effects completely dynamically
            benefits = []
            if full_description:
                # Find ALL benefits by looking for complete sentences with benefit keywords
                benefit_keywords = [
                    'ช่วย', 'แก้ปัญหา', 'ลด', 'ป้องกัน', 'บำรุง', 'เพิ่ม', 'ปรับปรุง', 'กระตุ้น',
                    'สำหรับ', 'ทำให้', 'ผลจาก', 'เหมาะสำหรับ', 'มีประสิทธิภาพ', 'ออกฤทธิ์', 'สามารถ'
                ]

                # First look for numbered benefits (1. 2. etc.)
                numbered_pattern = r'(\d+)\.[\s]*([^\d]+?)(?=\d+\.|$|อัตรา|ลักษณะ)'
                numbered_matches = re.findall(numbered_pattern, full_description, re.DOTALL)
                for num, benefit_text in numbered_matches:
                    clean_benefit = re.sub(r'\s+', ' ', benefit_text.strip())
                    clean_benefit = re.sub(r'[﻿\xa0]+', ' ', clean_benefit)
                    if clean_benefit and len(clean_benefit.strip()) > 5:
                        benefits.append(clean_benefit.strip())

                # Then look for keyword-based benefits in complete sentences
                sentences = re.split(r'[.\n\r]+', full_description)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 10:  # Skip very short sentences
                        continue

                    # Check if sentence contains benefit keywords
                    for keyword in benefit_keywords:
                        if keyword in sentence:
                            clean_sentence = re.sub(r'\s+', ' ', sentence)
                            clean_sentence = re.sub(r'[﻿\xa0]+', ' ', clean_sentence)
                            clean_sentence = clean_sentence.strip()

                            if (clean_sentence and clean_sentence not in benefits and
                                len(clean_sentence) > 10 and len(clean_sentence) < 200):
                                benefits.append(clean_sentence)
                            break

                # Remove duplicates while preserving order
                unique_benefits = []
                for benefit in benefits:
                    if benefit not in unique_benefits:
                        unique_benefits.append(benefit)
                benefits = unique_benefits

            # Images - look for all product images
            images = []
            img_selectors = [
                '#product-info img',
                '.product-images img',
                '.product-gallery img',
                'img[src*="myskinrecipes"]'
            ]
            for selector in img_selectors:
                imgs = soup.select(selector)
                for img in imgs:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.base_url + src
                        if src not in images:
                            images.append(src)

            # Extract concentration/strength if available
            concentration = None
            if name and 'ppm' in name:
                conc_match = re.search(r'(\d+ppm)', name)
                if conc_match:
                    concentration = conc_match.group(1)

            # Availability/stock
            availability = "In Stock"  # Default assumption
            stock_indicators = soup.select('.out-of-stock, .unavailable')
            if stock_indicators:
                availability = "Out of Stock"

            # Extract product ID from URL
            product_id = None
            id_match = re.search(r'/(\d+)-', url)
            if id_match:
                product_id = id_match.group(1)

            # Extract enhanced data from tabs (with error handling)
            try:
                enhanced_data = self.extract_enhanced_product_data(soup, full_description)
            except Exception as e:
                self.logger.error(f"Error in enhanced data extraction for {url}: {e}")
                enhanced_data = {}

            # Merge dynamic data with enhanced data (avoid overwriting if already exists)
            for key, value in dynamic_data.items():
                if value is not None and key not in enhanced_data:
                    enhanced_data[key] = value

            # Create comprehensive usage information
            if enhanced_data.get('usage_percent_lo') and not usage:
                usage_parts = []
                if enhanced_data.get('usage_percent_lo') and enhanced_data.get('usage_percent_hi'):
                    usage_parts.append(f"{enhanced_data['usage_percent_lo']}-{enhanced_data['usage_percent_hi']}%")
                if enhanced_data.get('usage_percent_best'):
                    usage_parts.append(f"(แนะนำ {enhanced_data['usage_percent_best']}%)")
                if usage_parts:
                    usage = ' '.join(usage_parts)

            return Product(
                name=name or "Unknown Product",
                url=url,
                price=price,
                original_price=original_price,
                description=description,
                ingredients=ingredients or None,
                benefits=benefits or None,
                usage=usage,
                images=images or None,
                category=category,
                subcategory=concentration,
                rating=None,  # Not visible in provided HTML
                reviews_count=None,
                availability=availability,
                sku=product_id,
                tags=list(characteristics.keys()) if characteristics else None,
                # Enhanced data from tabs and dynamic extraction
                **enhanced_data
            )

        except Exception as e:
            self.logger.error(f"Error extracting product data from {url}: {e}")
            return None

    def extract_enhanced_product_data(self, soup: BeautifulSoup, full_description: str = "") -> Dict:
        """Extract enhanced product data from all tabs (Info, Technical, Sample Products)"""
        enhanced_data = {}

        if not soup:
            self.logger.warning("No soup provided to extract_enhanced_product_data")
            return enhanced_data

        try:
            # Get the complete product container content first
            product_container = soup.select_one('.product-container, .js-product-container')
            if not product_container:
                product_container = soup
                self.logger.debug("Using full page as product container")

            # Tab 1: ข้อมูล (Info) - Detailed product information
            # Look for various tab selectors
            info_selectors = [
                '#info', '#product-info', '.tab-pane.active',
                '[data-tab="info"]', '.product-description',
                '.tab-content .active'
            ]

            detailed_info = ""
            for selector in info_selectors:
                info_tab = product_container.select_one(selector)
                if info_tab:
                    detailed_info = info_tab.get_text(strip=True)
                    break

            # Use the full description which contains all the data
            content_to_analyze = full_description or detailed_info or ""

            if content_to_analyze:
                enhanced_data['detailed_info'] = detailed_info or content_to_analyze

                # Extract INCI name from content - COMPLETELY DYNAMIC
                inci_patterns = [
                    r'INCI Name[:\s]*([^\n\r]+)',  # Any content after INCI Name
                    r'INCI[:\s]*([A-Za-z][^\n\r]*)',  # Any chemical name after INCI
                    r'ชื่อ INCI[:\s]*([^\n\r]+)',  # Thai INCI label
                    r'(?:INCI|inci)[:\s]*([A-Za-z][^\n\r]+)',  # Case insensitive
                    r'Name[:\s]*([A-Z][a-z]*\s*[A-Z][^\n\r]*)',  # Chemical name patterns
                ]

                inci_candidates = []
                for pattern in inci_patterns:
                    matches = re.findall(pattern, content_to_analyze, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        inci_name = match.strip()
                        inci_name = re.sub(r'[﻿\s]+$', '', inci_name)
                        inci_name = re.sub(r'﻿+', '', inci_name)
                        if inci_name and len(inci_name) > 2:
                            inci_candidates.append(inci_name)

                # Take the longest/most complete INCI name found
                if inci_candidates:
                    enhanced_data['inci_name'] = max(inci_candidates, key=len)

                # Extract comprehensive dosage information - COMPLETELY DYNAMIC
                dosage_patterns = [
                    r'อัตราการใช้[:\s]*([^\n\r]+)',  # Usage rate
                    r'(\d+[.,]?\d*\s*%[^\n\r]*)',  # Any percentage with context
                    r'แนะนำ[:\s]*([0-9][^\n\r]*)',  # Recommendations starting with numbers
                    r'ความเข้มข้น[:\s]*([^\n\r]+)',  # Concentration
                    r'การใช้[:\s]*([^\n\r]+)',  # Usage
                    r'วิธีใช้[:\s]*([^\n\r]+)',  # Method of use
                    r'ปริมาณ[:\s]*([^\n\r]+)',  # Quantity
                    r'สำหรับผิว[^\n\r]*([0-9][^\n\r]*)',  # For skin type with numbers
                ]

                dosage_candidates = []
                for pattern in dosage_patterns:
                    matches = re.findall(pattern, content_to_analyze, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        dosage = match.strip()
                        dosage = re.sub(r'﻿+', '', dosage)
                        if dosage and len(dosage) > 3:
                            dosage_candidates.append(dosage)

                # Take the longest/most detailed dosage found
                if dosage_candidates:
                    enhanced_data['recommended_dosage'] = max(dosage_candidates, key=len)

                # Extract ALL technical information - COMPLETELY DYNAMIC
                tech_patterns = {
                    'mechanism': [
                        r'ออกฤทธิ์หลัก[\s]*([^\n\r]+)',  # Primary action
                        r'กลไก[:\s]*([^\n\r]+)',  # Mechanism
                        r'วิธีการทำงาน[:\s]*([^\n\r]+)',  # How it works
                        r'การทำงาน[:\s]*([^\n\r]+)',  # Working method
                        r'หลักการ[:\s]*([^\n\r]+)',  # Principle
                    ],
                    'appearance': [
                        r'ลักษณะผลิตภัณฑ์[:\s]*([^\n\r]+)',  # Product appearance
                        r'ลักษณะ[:\s]*([^\n\r]+)',  # Appearance
                        r'รูปร่าง[:\s]*([^\n\r]+)',  # Shape/form
                        r'สี[:\s]*([^\n\r]+)',  # Color
                        r'เนื้อ[:\s]*([^\n\r]+)',  # Texture
                        r'ผง[^\n\r]*',  # Powder descriptions
                    ],
                    'storage': [
                        r'การเก็บรักษา[:\s]*([^\n\r]+)',  # Storage
                        r'เก็บในที่[^\n\r]*([^\n\r]+)',  # Store in place
                        r'วิธีเก็บ[:\s]*([^\n\r]+)',  # Storage method
                        r'เก็บ[:\s]*([^\n\r]+)',  # Store
                        r'อุณหภูมิการเก็บ[:\s]*([^\n\r]+)',  # Storage temperature
                    ],
                    'solubility': [
                        r'การละลาย[:\s]*([^\n\r]+)',  # Solubility
                        r'สามารถละลาย[^\n\r]*([^\n\r]*)',  # Can dissolve
                        r'ละลายได้[:\s]*([^\n\r]+)',  # Soluble
                        r'ละลาย[:\s]*([^\n\r]+)',  # Dissolve
                        r'ในน้ำ[^\n\r]*',  # In water
                        r'ในสารละลาย[^\n\r]*([^\n\r]*)',  # In solution
                    ],
                    'shelf_life': [
                        r'อายุ[:\s]*([^\n\r]+)',  # Age/shelf life
                        r'มีอายุ[:\s]*([^\n\r]+)',  # Has life of
                        r'เก็บได้[:\s]*([^\n\r]+)',  # Can store for
                        r'หมดอายุ[:\s]*([^\n\r]+)',  # Expiry
                        r'\d+\s*เดือน[^\n\r]*',  # X months
                        r'\d+\s*ปี[^\n\r]*',  # X years
                    ],
                    'ph_stability': [
                        r'pH[:\s]*([^\n\r]+)',  # pH
                        r'ค่า pH[:\s]*([^\n\r]+)',  # pH value
                        r'ความเป็นกรด[:\s]*([^\n\r]+)',  # Acidity
                        r'ความเป็นด่าง[:\s]*([^\n\r]+)',  # Alkalinity
                    ],
                    'heat_resistance': [
                        r'อุณหภูมิ[:\s]*([^\n\r]+)',  # Temperature
                        r'ความร้อน[:\s]*([^\n\r]+)',  # Heat
                        r'ทนความร้อน[:\s]*([^\n\r]+)',  # Heat resistant
                        r'เสถียรต่อความร้อน[:\s]*([^\n\r]+)',  # Heat stable
                    ]
                }

                for field_name, patterns in tech_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, content_to_analyze, re.DOTALL)
                        if match:
                            # Extract the matched group or full match depending on pattern
                            if match.groups():
                                value = match.group(1).strip()
                            else:
                                value = match.group(0).strip()

                            # Clean up the extracted value
                            value = re.sub(r'[:\s\ufeff]+$', '', value)
                            value = re.sub(r'\ufeff+', '', value)
                            value = value.strip()

                            if value and len(value) > 1:  # Accept any reasonable content
                                enhanced_data[field_name] = value
                                break

                # Extract sample products completely dynamically
                sample_patterns = [
                    r'ตัวอย่างผลิตภัณฑ์[^\n\r]*([\s\S]*?)(?=INCI|$)',  # Sample products section
                    r'ใช้ใน[^\n\r]*([\s\S]*?)(?=INCI|$)',  # Used in products
                    r'พบใน[^\n\r]*([\s\S]*?)(?=INCI|$)',  # Found in products
                ]

                for pattern in sample_patterns:
                    sample_match = re.search(pattern, content_to_analyze, re.DOTALL | re.IGNORECASE)
                    if sample_match:
                        sample_text = sample_match.group(1)
                        sample_products = []

                        # Split by various delimiters and clean
                        delimiters = ['\n', '\r', '﻿', '\xa0', '•', '→']
                        lines = [sample_text]
                        for delimiter in delimiters:
                            new_lines = []
                            for line in lines:
                                new_lines.extend(line.split(delimiter))
                            lines = new_lines

                        # Filter product names
                        for product in lines:
                            product = product.strip()
                            # Look for actual product names (brand + product structure)
                            if (product and len(product) > 10 and len(product) < 120 and
                                (' ' in product) and
                                not any(skip in product.lower() for skip in ['ตัวอย่าง', 'sample', 'ใช้', 'example'])):
                                # Check if it looks like a product name (has brand-like structure)
                                words = product.split()
                                if len(words) >= 2:  # At least brand + product
                                    sample_products.append(product)

                        if sample_products:
                            enhanced_data['sample_products'] = sample_products
                            break

            # Tab 2: เทคนิค (Technical) - Technical specifications
            # Look for technical tab with multiple selectors
            tech_selectors = [
                '#technical', '#tech', '.technical-tab',
                '[data-tab="technical"]', '.tab-pane[id*="tech"]'
            ]

            tech_content = ""
            tech_tab = None
            for selector in tech_selectors:
                found_tech_tab = product_container.select_one(selector)
                if found_tech_tab:
                    tech_tab = found_tech_tab
                    tech_content = tech_tab.get_text(strip=True)
                    break

            if tech_content:
                # Extract technical field data from text content
                tech_field_patterns = {
                    'mechanism': [r'กลไก[:\s]*([^ลักษณะ^การ^อุณหภูมิ]+)', r'วิธีการทำงาน[:\s]*([^ลักษณะ^การ]+)'],
                    'appearance': [r'ลักษณะ[:\s]*([^การ^อุณหภูมิ^วิธี]+)', r'รูปร่าง[:\s]*([^การ^อุณหภูมิ]+)'],
                    'storage': [r'การเก็บรักษา[:\s]*([^อุณหภูมิ^วิธี^INCI]+)', r'เก็บ[:\s]*([^อุณหภูมิ^วิธี]+)'],
                    'solubility': [r'การละลาย[:\s]*([^การ^อุณหภูมิ^วิธี]+)', r'ละลาย[:\s]*([^การ^อุณหภูมิ]+)'],
                    'ph_stability': [r'pH[:\s]*([^การ^อุณหภูมิ^วิธี]+)', r'ค่า pH[:\s]*([^การ^อุณหภูมิ]+)'],
                    'heat_resistance': [r'อุณหภูมิ[:\s]*([^การ^วิธี^INCI]+)', r'ความร้อน[:\s]*([^การ^วิธี]+)']
                }

                for field_name, patterns in tech_field_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, tech_content, re.DOTALL)
                        if match:
                            enhanced_data[field_name] = match.group(1).strip()
                            break

                # Also try to extract from field-specific selectors if we found a tech tab
                if tech_tab:
                    tech_fields = {
                        'mechanism': tech_tab.select_one('.field_mechanism'),
                        'appearance': tech_tab.select_one('.field_appearance'),
                        'storage': tech_tab.select_one('.field_storage'),
                        'shelf_life': tech_tab.select_one('.field_shelf_life'),
                        'dosage': tech_tab.select_one('.field_dosage'),
                        'mix_method': tech_tab.select_one('.field_mix_method'),
                        'heat_resistance': tech_tab.select_one('.field_heat_resistance'),
                        'ph_stability': tech_tab.select_one('.field_stable_in_ph_range'),
                        'solubility': tech_tab.select_one('.field_solubility'),
                        'product_types': tech_tab.select_one('.field_product_types'),
                        'inci_name': tech_tab.select_one('.field_inci')
                    }
                else:
                    tech_fields = {}

                for field_name, element in tech_fields.items():
                    if element and field_name not in enhanced_data:
                        text = element.get_text(strip=True)
                        if text and text != '@':  # Skip placeholder text
                            enhanced_data[field_name] = text

                # Extract COA (Certificate of Analysis) table
                # Extract COA specifications and ALL tabular data
                # Look for tables with multiple selectors
                coa_selectors = [
                    '.coa_table', '.table', 'table',
                    '.specifications', '.analysis', '.data-table'
                ]

                specifications = []

                # Also try to extract from text patterns if no tables found
                coa_text_patterns = [
                    r'COA[:\s]*([^INCI^ตัวอย่าง]+)',
                    r'Certificate of Analysis[:\s]*([^INCI^ตัวอย่าง]+)',
                    r'การทดสอบ[:\s]*([^INCI^ตัวอย่าง]+)',
                    r'ผลการทดสอบ[:\s]*([^INCI^ตัวอย่าง]+)',
                    r'มาตรฐาน[:\s]*([^INCI^ตัวอย่าง]+)'
                ]

                for coa_selector in coa_selectors:
                    coa_table = None
                    if tech_tab:
                        coa_table = tech_tab.select_one(coa_selector)
                    if not coa_table:
                        coa_table = product_container.select_one(coa_selector)

                    if coa_table:
                        # Look for table rows with test specifications
                        row_selectors = ['tbody tr', 'tr', '.table-row']
                        cell_selectors = ['td.table_td', 'td', 'th', '.cell']

                        for row_sel in row_selectors:
                            rows = coa_table.select(row_sel)
                            if not rows:
                                continue

                            for row in rows:
                                for cell_sel in cell_selectors:
                                    cells = row.select(cell_sel)
                                    if len(cells) >= 2:
                                        test_name = cells[0].get_text(strip=True)
                                        specification = cells[1].get_text(strip=True)
                                        if test_name and specification and test_name != specification:
                                            specifications.append({
                                                'test_name': test_name,
                                                'specification': specification
                                            })
                                        break
                            if specifications:
                                break
                        if specifications:
                            break

                # If no table data found, try text patterns
                if not specifications:
                    for pattern in coa_text_patterns:
                        match = re.search(pattern, content_to_analyze, re.DOTALL | re.IGNORECASE)
                        if match:
                            coa_text = match.group(1).strip()
                            if coa_text:
                                specifications.append({
                                    'test_name': 'COA Data',
                                    'specification': coa_text
                                })
                                break

                if specifications:
                    enhanced_data['coa_specifications'] = specifications

            # Tab 3: ตัวอย่างสินค้า (Sample Products) - Products using this ingredient
            # Look for sample products with multiple selectors
            samples_selectors = [
                '#cos-products', '#samples', '.samples-tab',
                '[data-tab="samples"]', '.sample-products'
            ]

            sample_products = []
            for selector in samples_selectors:
                samples_tab = product_container.select_one(selector)
                if samples_tab:
                    # Extract product names from various selectors
                    product_selectors = [
                        '.inci_name', '.product-name', '.sample-product',
                        'h3', 'h4', '.title', 'a[href*="product"]'
                    ]

                    for prod_selector in product_selectors:
                        products = samples_tab.select(prod_selector)
                        for product in products:
                            product_name = product.get_text(strip=True)
                            if product_name and product_name not in sample_products:
                                sample_products.append(product_name)

                    # Also extract from general text content if specific selectors don't work
                    if not sample_products:
                        sample_text = samples_tab.get_text()
                        # Look for product names in the sample text
                        lines = sample_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 10 and len(line) < 100:  # Reasonable product name length
                                # Skip common headers and footers
                                if not any(skip in line.lower() for skip in ['ตัวอย่าง', 'sample', 'products', 'ใช้', 'using']):
                                    sample_products.append(line)

                    # Also look for other product card formats
                    product_cards = samples_tab.select('.product-card-header h6, .product-title')
                    for card in product_cards:
                        product_name = card.get_text(strip=True)
                        if product_name and product_name not in sample_products:
                            sample_products.append(product_name)

                    if sample_products:
                        break

                if sample_products:
                    enhanced_data['sample_products'] = sample_products

            # Additional extraction from general page content
            # Look for mechanism description in general content
            if not enhanced_data.get('mechanism'):
                mechanism_patterns = [
                    r'ออกฤทธิ์หลัก[:\s]*([^1234567890]+)',
                    r'กลไก[:\s]*([^\n\r]+)',
                    r'ทำงาน[:\s]*([^\n\r]+)'
                ]
                page_text = soup.get_text()
                for pattern in mechanism_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_data['mechanism'] = match.group(1).strip()
                        break

            # Extract appearance from general description if not found in tech tab
            if not enhanced_data.get('appearance'):
                appearance_patterns = [
                    r'ลักษณะผลิตภัณฑ์[:\s]*([^\n\r]+)',
                    r'ลักษณะ[:\s]*([^\n\r]+)'
                ]
                page_text = soup.get_text()
                for pattern in appearance_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_data['appearance'] = match.group(1).strip()
                        break

            # Extract storage from general description if not found in tech tab
            if not enhanced_data.get('storage'):
                storage_patterns = [
                    r'การเก็บรักษา[:\s]*([^\n\r]+)',
                    r'เก็บ[:\s]*([^\n\r]+)'
                ]
                page_text = soup.get_text()
                for pattern in storage_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_data['storage'] = match.group(1).strip()
                        break

            # Extract solubility information
            if not enhanced_data.get('solubility'):
                solubility_patterns = [
                    r'การละลาย[:\s]*([^\n\r]+)',
                    r'ละลาย[:\s]*([^\n\r]+)'
                ]
                page_text = soup.get_text()
                for pattern in solubility_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_data['solubility'] = match.group(1).strip()
                        break

        except Exception as e:
            self.logger.error(f"Error extracting enhanced product data: {e}")

        return enhanced_data

    def scrape_category(self, category_url: str, category_name: str) -> List[Product]:
        """Scrape all products from a category page with batch processing"""
        products = []
        all_product_links = []

        soup = self.get_page(category_url)
        if not soup:
            return products

        # Get product links from this category page
        product_links = self.extract_product_links(soup)
        all_product_links.extend(product_links)

        # Check for pagination and collect all product links first
        page_num = 1
        while True:
            self.logger.info(f"Discovering products on page {page_num} of category: {category_name}")

            # Look for next page
            next_page = soup.select_one('.next, .pagination .next, a[rel="next"]')
            if next_page and next_page.get('href'):
                next_url = urljoin(self.base_url, next_page.get('href'))
                soup = self.get_page(next_url)
                if soup:
                    new_product_links = self.extract_product_links(soup)
                    all_product_links.extend(new_product_links)
                    page_num += 1
                else:
                    break
            else:
                break

        # Remove duplicates while preserving order
        unique_links = []
        seen = set()
        for link in all_product_links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)

        all_product_links = unique_links
        self.logger.info(f"Found {len(all_product_links)} unique products in category: {category_name}")

        # Process products in batches
        for i in range(0, len(all_product_links), self.batch_size):
            batch = all_product_links[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(all_product_links) + self.batch_size - 1)//self.batch_size} in category: {category_name}")

            for j, product_url in enumerate(batch):
                self.logger.info(f"  Product {i + j + 1}/{len(all_product_links)}: {product_url}")
                product = self.extract_product_data(product_url, category_name)
                if product:
                    products.append(product)
                time.sleep(1)  # Be respectful to the server

        return products

    def scrape_all(self) -> List[Product]:
        """Main scraping method"""
        self.logger.info("Starting MySkinRecipes scraping...")

        # Get main shop page
        main_soup = self.get_page(self.shop_url)
        if not main_soup:
            self.logger.error("Failed to fetch main shop page")
            return []

        # Extract categories
        categories = self.extract_categories(main_soup)

        # Also check for products on main page
        main_product_links = self.extract_product_links(main_soup)
        self.logger.info(f"Found {len(main_product_links)} products on main page")

        # Scrape products from main page
        for product_url in main_product_links:
            product = self.extract_product_data(product_url, "Main")
            if product:
                self.products.append(product)
            time.sleep(1)

        # Scrape each category
        for category in categories:
            category_products = self.scrape_category(category['url'], category['name'])
            self.products.extend(category_products)
            time.sleep(2)  # Longer delay between categories

        self.logger.info(f"Total products scraped: {len(self.products)}")
        if self.failed_urls:
            self.logger.warning(f"Failed to scrape {len(self.failed_urls)} URLs:")
            for url in self.failed_urls[:10]:  # Show first 10 failed URLs
                self.logger.warning(f"  {url}")
            if len(self.failed_urls) > 10:
                self.logger.warning(f"  ... and {len(self.failed_urls) - 10} more")

        return self.products

    def save_to_json(self, filename: str = "myskin_products.json"):
        """Save products to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([asdict(product) for product in self.products], f, indent=2, ensure_ascii=False)
        self.logger.info(f"Data saved to {filename}")

    def save_to_csv(self, filename: str = "myskin_products.csv"):
        """Save products to CSV file"""
        if not self.products:
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Headers
            headers = ['name', 'url', 'price', 'original_price', 'description', 'ingredients', 'benefits',
                      'usage', 'images', 'category', 'rating', 'reviews_count', 'availability', 'sku', 'tags']
            writer.writerow(headers)

            # Data
            for product in self.products:
                row = []
                for header in headers:
                    value = getattr(product, header)
                    if isinstance(value, list):
                        value = '; '.join(value) if value else ''
                    elif value is None:
                        value = ''
                    row.append(str(value))
                writer.writerow(row)

        self.logger.info(f"Data saved to {filename}")

def main():
    # Use discovered categories if available
    categories_file = "myskin_scraping/results/discovered_categories.json"

    # Check if categories file exists
    import os
    if not os.path.exists(categories_file):
        categories_file = None
        print("No discovered categories file found, will discover categories dynamically")
    else:
        print(f"Using discovered categories from {categories_file}")

    scraper = MySkinRecipesScraper(categories_file=categories_file)
    products = scraper.scrape_all()

    # Save data in multiple formats
    scraper.save_to_json("myskin_products.json")
    scraper.save_to_csv("myskin_products.csv")

    print(f"Scraping completed! Found {len(products)} products.")
    print("Data saved to myskin_products.json and myskin_products.csv")

if __name__ == "__main__":
    main()