import requests
import logging
import urllib.parse
import wikipedia
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def search_wikipedia(query, language='en'):
    """
    Search Wikipedia for articles matching the query
    Returns a list of article titles
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Search for articles
        search_results = wikipedia.search(query, results=10)
        return search_results
    except Exception as e:
        logging.error(f"Wikipedia search error: {str(e)}")
        raise Exception(f"Failed to search Wikipedia: {str(e)}")

def get_article_summary(title, language='en'):
    """
    Get a summary of a Wikipedia article
    Returns a summary string
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Get article summary
        summary = wikipedia.summary(title)
        return summary
    except Exception as e:
        logging.error(f"Wikipedia summary error: {str(e)}")
        raise Exception(f"Failed to get article summary: {str(e)}")

def get_article_content(title, language='en'):
    """
    Get the full content of a Wikipedia article
    Returns a dictionary with section titles as keys and content as values
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Get full article content
        page = wikipedia.page(title)
        html_content = page.html()
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract sections
        sections = {}
        current_section = 'Introduction'
        sections[current_section] = ''
        
        # Get all content elements
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            content_div = soup  # Fallback to the whole page if content div not found
        
        # Loop through all elements in content
        elements = content_div.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'table'])
        for element in elements:
            # Skip navigation, references, and other non-content sections
            if element.find_parent('div', {'class': ['toc', 'reflist', 'navbox']}):
                continue
                
            # If we find a header, start a new section
            if element.name in ['h1', 'h2', 'h3']:
                section_text = element.get_text().strip()
                # Skip empty or special sections
                if section_text and not section_text.startswith(('See also', 'References', 'External links', 'Notes')):
                    current_section = section_text
                    if current_section not in sections:
                        sections[current_section] = ''
            # Add paragraph text to current section
            elif element.name == 'p' and element.get_text().strip():
                sections[current_section] += element.get_text().strip() + '\n\n'
            # Add list items
            elif element.name in ['ul', 'ol']:
                list_text = ""
                for li in element.find_all('li'):
                    list_text += "• " + li.get_text().strip() + "\n"
                if list_text:
                    sections[current_section] += list_text + '\n'
            # Add table data 
            elif element.name == 'table':
                # Skip infoboxes and navigational tables
                if element.get('class') and any(c in ['infobox', 'navbox', 'metadata'] for c in element.get('class')):
                    continue
                table_text = "Table: "
                # Extract some table data as text
                for row in element.find_all('tr')[:5]:  # Limit to first few rows
                    cells = row.find_all(['th', 'td'])
                    if cells:
                        row_text = " | ".join(cell.get_text().strip() for cell in cells)
                        table_text += row_text + "\n"
                sections[current_section] += table_text + "\n"
        
        # Remove any empty sections
        sections = {k: v for k, v in sections.items() if v.strip()}
        
        # Make sure we have at least the Introduction
        if not sections:
            sections['Introduction'] = page.summary
            
        return sections
    except Exception as e:
        logging.error(f"Wikipedia content error: {str(e)}")
        raise Exception(f"Failed to get article content: {str(e)}")

def get_article_images(title, language='en'):
    """
    Get images from a Wikipedia article
    Returns a list of image URLs with additional metadata
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Get page images through Wikipedia library first
        page = wikipedia.page(title)
        images = []
        
        # Filter images to exclude SVGs, icons, etc.
        valid_images = []
        for img in page.images:
            img_lower = img.lower()
            # Skip small icons, logos, and SVGs which are usually not content images
            if (not img_lower.endswith(('.svg', '.png')) or 
                'icon' not in img_lower and 
                'logo' not in img_lower and
                'flag' not in img_lower):
                valid_images.append({
                    'url': img,
                    'is_main': False
                })
        
        # If we found valid images, try to get thumbnail version for the first one
        if valid_images:
            # Mark the first non-SVG as main image
            for i, img in enumerate(valid_images):
                if not img['url'].lower().endswith('.svg'):
                    valid_images[i]['is_main'] = True
                    break
        
        # Use MediaWiki API to get better image data
        try:
            api_url = f"https://{language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'prop': 'images',
                'titles': title,
                'format': 'json'
            }
            response = requests.get(api_url, params=params)
            data = response.json()
            
            # Extract images from API response
            if 'query' in data and 'pages' in data['query']:
                page_id = next(iter(data['query']['pages']))
                if 'images' in data['query']['pages'][page_id]:
                    api_images = data['query']['pages'][page_id]['images']
                    
                    # Get image URLs for each image
                    for img_data in api_images:
                        img_title = img_data['title']
                        
                        # Skip commons, icons, and other non-content images
                        if ('File:Commons-' in img_title or 
                            'icon' in img_title.lower() or 
                            'logo' in img_title.lower() or
                            img_title.lower().endswith('.svg')):
                            continue
                        
                        # Get image info
                        img_params = {
                            'action': 'query',
                            'titles': img_title,
                            'prop': 'imageinfo',
                            'iiprop': 'url|dimensions',
                            'format': 'json'
                        }
                        img_response = requests.get(api_url, params=img_params)
                        img_data = img_response.json()
                        
                        if 'query' in img_data and 'pages' in img_data['query']:
                            for pid, page_data in img_data['query']['pages'].items():
                                if 'imageinfo' in page_data:
                                    for info in page_data['imageinfo']:
                                        # Use only decent sized images
                                        if 'width' in info and info['width'] > 200:
                                            img_url = info['url']
                                            # Add if not already in list
                                            if not any(i['url'] == img_url for i in valid_images):
                                                valid_images.append({
                                                    'url': img_url,
                                                    'is_main': False,
                                                    'width': info.get('width', 0),
                                                    'height': info.get('height', 0)
                                                })
        except Exception as img_api_error:
            logging.error(f"Error fetching additional image data: {str(img_api_error)}")
        
        # Make sure we have at least some images
        if not valid_images and page.images:
            # Fallback to using the first non-svg image
            for img in page.images:
                if not img.lower().endswith('.svg'):
                    valid_images.append({
                        'url': img,
                        'is_main': True
                    })
                    break
        
        return valid_images
    except Exception as e:
        logging.error(f"Wikipedia images error: {str(e)}")
        return []  # Return empty list on error

def get_article_languages(title, language='en'):
    """
    Get available languages for a Wikipedia article
    Returns a dictionary of language codes and names
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Get page languages
        page = wikipedia.page(title)
        # Try to get language links if available in the Wikipedia library
        if hasattr(page, 'langlinks'):
            return page.langlinks
        
        # If not available via the library, we'll create a basic mapping
        # This is a simplified approach as the actual Wikipedia API provides more details
        return {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese'
        }
    except Exception as e:
        logging.error(f"Wikipedia languages error: {str(e)}")
        return {}  # Return empty dict on error

def get_random_articles(language='en', limit=10, images_only=True, offset=0):
    """
    Get random Wikipedia articles for WikiTok feed
    Returns a list of dictionaries with article info
    """
    # Set the Wikipedia language
    wikipedia.set_lang(language)
    
    try:
        # Get random articles
        api_url = f"https://{language}.wikipedia.org/w/api.php"
        
        # Parameters for API request
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'random',
            'rnlimit': limit * 2,  # Request more than needed in case some don't have images
            'rnnamespace': 0  # Main articles only
        }
        
        response = requests.get(api_url, params=params)
        data = response.json()
        
        articles = []
        for article in data['query']['random']:
            title = article['title']
            
            try:
                # Get article summary and first image
                page = wikipedia.page(title)
                summary = page.summary
                images = page.images
                
                # Filter out articles without images if requested
                if images_only and not images:
                    continue
                
                # Get the first image that's not an SVG (usually icons)
                image_url = None
                for img in images:
                    if not img.lower().endswith('.svg'):
                        image_url = img
                        break
                
                if images_only and not image_url:
                    continue
                
                articles.append({
                    'title': title,
                    'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                    'image': image_url,
                    'language': language,
                    'url': page.url
                })
                
                # If we have enough articles, stop
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logging.error(f"Error getting article {title}: {str(e)}")
                continue
        
        return articles
    except Exception as e:
        logging.error(f"Random articles error: {str(e)}")
        raise Exception(f"Failed to get random articles: {str(e)}")
