"""
SHL Assessment Catalog Scraper
Scrapes all Individual Test Solutions from https://www.shl.com/solutions/products/product-catalog/
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_page(url, retries=3, delay=1):
    """Fetch a page with retry logic."""
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Attempt {i+1} failed for {url}: {e}")
            if i < retries - 1:
                time.sleep(delay * (i + 1))
    return None


def parse_test_type_badges(element):
    """Extract test type badges (A, B, C, D, E, K, P, S) from an element."""
    badges = []
    type_map = {
        'A': 'Ability & Aptitude',
        'B': 'Biodata & Situational Judgement',
        'C': 'Competencies',
        'D': 'Development & 360',
        'E': 'Assessment Exercises',
        'K': 'Knowledge & Skills',
        'P': 'Personality & Behavior',
        'S': 'Simulations'
    }
    # Look for badge elements
    badge_elements = element.find_all(class_=re.compile(r'badge|type|tag', re.I))
    for badge in badge_elements:
        text = badge.get_text(strip=True)
        if text in type_map:
            badges.append(type_map[text])
    return badges if badges else []


def scrape_catalog_page(url):
    """Scrape a single catalog page and return list of assessment items."""
    html = get_page(url)
    if not html:
        return [], None
    
    soup = BeautifulSoup(html, 'html.parser')
    assessments = []
    
    # Find the individual test solutions section
    # The catalog has a table/grid of assessments
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue
        
        # Look for assessment name link
        name_cell = cells[0] if cells else None
        if not name_cell:
            continue
            
        link = name_cell.find('a')
        if not link:
            continue
            
        name = link.get_text(strip=True)
        href = link.get('href', '')
        
        if not name or not href:
            continue
        
        # Build full URL
        if href.startswith('http'):
            full_url = href
        else:
            full_url = urljoin(BASE_URL, href)
        
        assessment = {
            'name': name,
            'url': full_url,
            'adaptive_support': 'No',
            'remote_support': 'Yes',
            'duration': None,
            'test_type': [],
            'description': ''
        }
        
        # Extract additional info from other cells
        for i, cell in enumerate(cells[1:], 1):
            cell_text = cell.get_text(strip=True)
            
            # Check for remote/adaptive indicators
            if 'remote' in cell_text.lower():
                assessment['remote_support'] = 'Yes'
            
            # Check for duration
            duration_match = re.search(r'(\d+)\s*min', cell_text, re.I)
            if duration_match:
                assessment['duration'] = int(duration_match.group(1))
            
            # Extract test types from badges/icons in cells
            spans = cell.find_all('span')
            for span in spans:
                span_text = span.get_text(strip=True)
                type_map = {
                    'A': 'Ability & Aptitude',
                    'B': 'Biodata & Situational Judgement', 
                    'C': 'Competencies',
                    'D': 'Development & 360',
                    'E': 'Assessment Exercises',
                    'K': 'Knowledge & Skills',
                    'P': 'Personality & Behavior',
                    'S': 'Simulations'
                }
                if span_text in type_map:
                    assessment['test_type'].append(type_map[span_text])
                    
                # Check for Yes/No indicators
                title = span.get('title', '') or span.get('aria-label', '')
                if 'adaptive' in title.lower():
                    assessment['adaptive_support'] = 'Yes' if 'yes' in title.lower() else 'No'
                if 'remote' in title.lower():
                    assessment['remote_support'] = 'Yes' if 'yes' in title.lower() else 'No'
        
        # Also look for checkmark/cross icons in the row
        icons = row.find_all(['i', 'svg', 'img'])
        for icon in icons:
            icon_class = ' '.join(icon.get('class', []))
            parent_title = icon.get('title', '') or icon.parent.get('title', '') if icon.parent else ''
            
        assessments.append(assessment)
    
    # Find next page link
    next_page = None
    pagination = soup.find(class_=re.compile(r'pagination|pager|next', re.I))
    if pagination:
        next_link = pagination.find('a', string=re.compile(r'next|>', re.I))
        if next_link and next_link.get('href'):
            next_page = urljoin(BASE_URL, next_link['href'])
    
    return assessments, next_page


def scrape_assessment_detail(url):
    """Scrape the detail page of a single assessment."""
    html = get_page(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    details = {}
    
    # Get description
    desc_selectors = [
        '.product-description',
        '.description',
        '[class*="description"]',
        '.content p',
        'article p',
        '.hero-text',
        '.product-detail p'
    ]
    
    for selector in desc_selectors:
        desc_el = soup.select_one(selector)
        if desc_el:
            text = desc_el.get_text(strip=True)
            if len(text) > 30:
                details['description'] = text[:500]
                break
    
    # Get duration from detail page
    duration_patterns = [
        r'(\d+)\s*minutes?',
        r'(\d+)\s*mins?',
        r'duration[:\s]+(\d+)',
    ]
    
    page_text = soup.get_text()
    for pattern in duration_patterns:
        match = re.search(pattern, page_text, re.I)
        if match:
            details['duration'] = int(match.group(1))
            break
    
    # Get adaptive support
    if 'adaptive' in page_text.lower():
        if re.search(r'adaptive[:\s]*(yes|supported|available)', page_text, re.I):
            details['adaptive_support'] = 'Yes'
    
    # Get test types from badges on detail page
    type_map = {
        'A': 'Ability & Aptitude',
        'B': 'Biodata & Situational Judgement',
        'C': 'Competencies',
        'D': 'Development & 360',
        'E': 'Assessment Exercises',
        'K': 'Knowledge & Skills',
        'P': 'Personality & Behavior',
        'S': 'Simulations'
    }
    
    test_types = []
    badges = soup.find_all(class_=re.compile(r'badge|type-icon|test-type', re.I))
    for badge in badges:
        text = badge.get_text(strip=True)
        if text in type_map:
            test_types.append(type_map[text])
    
    if test_types:
        details['test_type'] = test_types
    
    return details


def scrape_full_catalog():
    """Scrape the complete SHL product catalog."""
    logger.info("Starting SHL catalog scrape...")
    
    all_assessments = []
    
    # The catalog uses pagination with start parameter
    # Individual Test Solutions section
    page_num = 0
    page_size = 12  # SHL typically shows 12 per page
    
    while True:
        if page_num == 0:
            url = f"{CATALOG_URL}?start=0&type=1&pagesize=12"
        else:
            url = f"{CATALOG_URL}?start={page_num * page_size}&type=1&pagesize=12"
        
        logger.info(f"Scraping page {page_num + 1}: {url}")
        html = get_page(url)
        
        if not html:
            logger.error(f"Failed to get page {page_num + 1}")
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find assessment rows in the table
        # SHL catalog uses a specific table structure
        table = soup.find('table') or soup.find(class_=re.compile(r'catalog|product-list|assessment-list', re.I))
        
        if not table:
            # Try to find assessment cards/items
            items = soup.find_all(class_=re.compile(r'product-item|catalog-item|assessment-item', re.I))
            if not items:
                # Last resort: find all links in the product catalog area
                content = soup.find('main') or soup.find('div', id='content') or soup
                links = content.find_all('a', href=re.compile(r'/product-catalog/view/'))
                
                if not links:
                    logger.info(f"No more items found on page {page_num + 1}")
                    break
                
                for link in links:
                    name = link.get_text(strip=True)
                    href = link.get('href', '')
                    if name and href:
                        full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
                        all_assessments.append({
                            'name': name,
                            'url': full_url,
                            'adaptive_support': 'No',
                            'remote_support': 'Yes',
                            'duration': None,
                            'test_type': [],
                            'description': ''
                        })
        else:
            rows = table.find_all('tr')
            page_assessments = []
            
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                
                link = cells[0].find('a') if cells else None
                if not link:
                    continue
                
                name = link.get_text(strip=True)
                href = link.get('href', '')
                
                if name and href:
                    full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
                    
                    assessment = {
                        'name': name,
                        'url': full_url,
                        'adaptive_support': 'No',
                        'remote_support': 'Yes',
                        'duration': None,
                        'test_type': [],
                        'description': ''
                    }
                    
                    # Parse additional cells
                    # Typically: Name | Remote | Adaptive | Test Types | Duration
                    for j, cell in enumerate(cells[1:], 1):
                        # Check for Yes/No symbols or checkmarks
                        cell_html = str(cell)
                        if 'remote' in cell_html.lower() or j == 1:
                            if '✓' in cell.get_text() or 'yes' in cell.get_text().lower():
                                assessment['remote_support'] = 'Yes'
                        if 'adaptive' in cell_html.lower() or j == 2:
                            if '✓' in cell.get_text() or 'yes' in cell.get_text().lower():
                                assessment['adaptive_support'] = 'Yes'
                        
                        # Test type badges
                        for span in cell.find_all(['span', 'div']):
                            t = span.get_text(strip=True)
                            type_labels = {
                                'A': 'Ability & Aptitude', 'B': 'Biodata & Situational Judgement',
                                'C': 'Competencies', 'D': 'Development & 360',
                                'E': 'Assessment Exercises', 'K': 'Knowledge & Skills',
                                'P': 'Personality & Behavior', 'S': 'Simulations'
                            }
                            if t in type_labels and type_labels[t] not in assessment['test_type']:
                                assessment['test_type'].append(type_labels[t])
                        
                        # Duration
                        dur = re.search(r'(\d+)\s*min', cell.get_text(), re.I)
                        if dur:
                            assessment['duration'] = int(dur.group(1))
                    
                    page_assessments.append(assessment)
            
            if not page_assessments:
                break
            
            all_assessments.extend(page_assessments)
            logger.info(f"Found {len(page_assessments)} assessments on page {page_num + 1}. Total: {len(all_assessments)}")
        
        # Check if there's a next page
        next_btn = soup.find('a', string=re.compile(r'next|>|→', re.I))
        if not next_btn:
            # Check pagination
            current_page_el = soup.find(class_=re.compile(r'current|active', re.I))
            total_count_el = soup.find(class_=re.compile(r'total|count|results', re.I))
            
            if total_count_el:
                count_text = total_count_el.get_text()
                total_match = re.search(r'(\d+)', count_text)
                if total_match:
                    total = int(total_match.group(1))
                    if len(all_assessments) >= total:
                        break
        
        page_num += 1
        time.sleep(0.5)  # Be polite to the server
        
        if page_num > 50:  # Safety limit
            logger.warning("Reached page limit (50). Stopping.")
            break
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_assessments = []
    for a in all_assessments:
        if a['url'] not in seen_urls:
            seen_urls.add(a['url'])
            unique_assessments.append(a)
    
    logger.info(f"Total unique assessments scraped: {len(unique_assessments)}")
    return unique_assessments


def enrich_with_details(assessments, max_items=None, delay=0.3):
    """Enrich assessments with details from their individual pages."""
    items = assessments[:max_items] if max_items else assessments
    enriched = []
    
    for i, assessment in enumerate(items):
        logger.info(f"Enriching {i+1}/{len(items)}: {assessment['name']}")
        
        details = scrape_assessment_detail(assessment['url'])
        
        if details.get('description'):
            assessment['description'] = details['description']
        if details.get('duration') and not assessment.get('duration'):
            assessment['duration'] = details['duration']
        if details.get('adaptive_support'):
            assessment['adaptive_support'] = details['adaptive_support']
        if details.get('test_type') and not assessment['test_type']:
            assessment['test_type'] = details['test_type']
        
        enriched.append(assessment)
        time.sleep(delay)
    
    return enriched


def save_catalog(assessments, output_path='data/shl_catalog.json'):
    """Save scraped catalog to JSON."""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(assessments)} assessments to {output_path}")


if __name__ == '__main__':
    # Run the full scrape
    assessments = scrape_full_catalog()
    
    if len(assessments) >= 377:
        logger.info(f"✓ Successfully scraped {len(assessments)} assessments (>= 377 required)")
    else:
        logger.warning(f"⚠ Only scraped {len(assessments)} assessments (< 377 required). Check scraper.")
    
    # Enrich with details (this adds descriptions, etc.)
    logger.info("Enriching with detail page data...")
    enriched = enrich_with_details(assessments, delay=0.5)
    
    save_catalog(enriched, 'data/shl_catalog.json')
    print(f"\nDone! Scraped and saved {len(enriched)} assessments.")
