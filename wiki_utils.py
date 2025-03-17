import streamlit as st
import time
import re
import threading
import urllib.parse
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Simple translation function without external dependencies
def basic_translate(text, to_lang, from_lang='auto'):
    """Basic translation using free web API"""
    if not text or not text.strip():
        return text
        
    try:
        # Using Google Translate API for public use (free tier)
        fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={from_lang}&tl={to_lang}&dt=t&q={urllib.parse.quote(text)}"
        fallback_response = requests.get(fallback_url)
        
        if fallback_response.status_code == 200:
            data = fallback_response.json()
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated = ''.join([sentence[0] for sentence in data[0] if isinstance(sentence, list) and len(sentence) > 0])
                return translated
            else:
                # Fallback to direct text return
                return text
        else:
            return text
                
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

@st.cache_data(ttl=3600)
def get_wikipedia_search_results(query, language="en"):
    """
    Search Wikipedia for articles matching the query in specified language
    using the MediaWiki API directly
    
    Args:
        query (str): The search term
        language (str): Language code (e.g., 'en', 'es', 'fr')
        
    Returns:
        list: List of article titles matching the query
    """
    if not query:
        return []
    
    try:
        # Use Wikipedia's API directly via requests
        url = f"https://{language}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 10
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract titles from the search results
        search_results = [item["title"] for item in data.get("query", {}).get("search", [])]
        return search_results
    except Exception as e:
        st.error(f"Error searching Wikipedia: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_article_content(title, language="en"):
    """
    Get the content of a Wikipedia article using the MediaWiki API directly
    
    Args:
        title (str): The title of the article
        language (str): Language code (e.g., 'en', 'es', 'fr')
        
    Returns:
        dict: Dictionary containing article title, summary, content and URL
    """
    if not title:
        return None
    
    try:
        # Use Wikipedia's API directly via requests
        url = f"https://{language}.wikipedia.org/w/api.php"
        
        # First get the summary (extracts)
        summary_params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True
        }
        
        summary_response = requests.get(url, params=summary_params)
        summary_data = summary_response.json()
        
        # Extract page ID and summary
        pages = summary_data.get("query", {}).get("pages", {})
        page_id = list(pages.keys())[0]
        
        if page_id == "-1":  # Page not found
            return None
        
        summary = pages[page_id].get("extract", "No summary available")
        
        # Now get the full content
        content_params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts",
            "explaintext": True
        }
        
        content_response = requests.get(url, params=content_params)
        content_data = content_response.json()
        
        # Extract full content
        content_pages = content_data.get("query", {}).get("pages", {})
        content = content_pages[page_id].get("extract", "No content available")
        
        # Create Wikipedia URL
        encoded_title = urllib.parse.quote(title.replace(' ', '_'))
        article_url = f"https://{language}.wikipedia.org/wiki/{encoded_title}"
        
        return {
            "title": title,
            "summary": summary,
            "content": content,
            "url": article_url
        }
    except Exception as e:
        st.error(f"Error retrieving article: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_available_languages(title, source_lang="en"):
    """
    Get available languages for a Wikipedia article using the MediaWiki API directly
    
    Args:
        title (str): The title of the article
        source_lang (str): Source language code
        
    Returns:
        dict: Dictionary of language codes and titles
    """
    if not title:
        return {}
    
    try:
        # Use Wikipedia's API directly via requests
        url = f"https://{source_lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "langlinks",
            "lllimit": 500  # Get many language links
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract language links
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return {source_lang: title}
            
        page_id = list(pages.keys())[0]
        
        if page_id == "-1":  # Page not found
            return {source_lang: title}
            
        langlinks = pages[page_id].get("langlinks", [])
        
        # Create a dictionary of language codes and titles
        available_langs = {source_lang: title}
        for lang in langlinks:
            available_langs[lang["lang"]] = lang["*"]
        
        return available_langs
    except Exception as e:
        st.error(f"Error retrieving language versions: {str(e)}")
        # Return at least the source language
        return {source_lang: title}

@st.cache_data(ttl=3600)
def get_article_in_language(title, lang):
    """
    Get article content in the specified language
    
    Args:
        title (str): Title of the article in the specified language
        lang (str): Language code
        
    Returns:
        dict: Article content in the specified language
    """
    return get_article_content(title, lang)

def split_text_into_chunks(text, chunk_size=800):
    """
    Split text into smaller chunks for translation.
    Try to split at sentence boundaries when possible.
    
    Args:
        text (str): Text to split
        chunk_size (int): Maximum size of each chunk
        
    Returns:
        list: List of text chunks
    """
    if not text:
        return []
    
    # Regular expression to find sentence boundaries
    sentence_endings = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_endings, text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If this sentence alone is bigger than chunk_size, split it by spaces
        if len(sentence) > chunk_size:
            words = sentence.split()
            temp_chunk = ""
            for word in words:
                if len(temp_chunk) + len(word) + 1 > chunk_size:
                    chunks.append(temp_chunk.strip())
                    temp_chunk = word + " "
                else:
                    temp_chunk += word + " "
            
            if temp_chunk.strip():
                current_chunk += temp_chunk
        # If adding this sentence would exceed the chunk size,
        # add current chunk to the list and start a new one
        elif len(current_chunk) + len(sentence) > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
        else:
            current_chunk += sentence + " "
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def translate_chunk(chunk, to_lang, from_lang):
    """
    Translate a single chunk of text using the public translation API
    
    Args:
        chunk (str): Text chunk to translate
        to_lang (str): Target language code
        from_lang (str): Source language code
        
    Returns:
        str: Translated text
    """
    if not chunk or not chunk.strip():
        return ""
    
    try:
        # Use the basic translate function for each chunk
        return basic_translate(chunk, to_lang, from_lang)
    except Exception as e:
        st.warning(f"Error translating chunk: {str(e)}")
        return chunk  # Return original chunk if translation fails

# Thread-safe lock for translation
translate_lock = threading.Lock()

def translate_text(text, to_lang, from_lang='auto'):
    """
    Translate text using multithreaded approach for efficiency
    
    Args:
        text (str): Text to translate
        to_lang (str): Target language code
        from_lang (str): Source language code
        
    Returns:
        str: Translated text
    """
    if not text:
        return ""
    
    try:
        # For very short texts, just translate directly without chunking
        if len(text) < 200:  # Reduced threshold to only skip chunking for very small texts
            return basic_translate(text, to_lang, from_lang)
            
        # Split text into smaller chunks for translation
        chunks = split_text_into_chunks(text)
        
        if not chunks:
            return ""
        
        # Create a progress bar
        progress_bar = st.progress(0)
        progress_text = st.empty()
        progress_text.text("Translating...")
        
        # Create a thread pool for concurrent translation
        translated_chunks = []
        total_chunks = len(chunks)
        
        # Use more workers for faster translation
        max_workers = min(12, total_chunks)
        
        # We'll use a dict to keep track of the original order
        chunk_results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all translation tasks
            future_to_chunk = {
                executor.submit(translate_chunk, chunk, to_lang, from_lang): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Process results as they complete
            for i, future in enumerate(as_completed(future_to_chunk)):
                chunk_index = future_to_chunk[future]
                try:
                    # Thread-safe translation
                    with translate_lock:
                        translated_text = future.result()
                    
                    # Store translated chunks (will sort by index later)
                    chunk_results[chunk_index] = translated_text
                    
                    # Update progress
                    progress = (i + 1) / total_chunks
                    progress_bar.progress(progress)
                    progress_text.text(f"Translating... {i+1}/{total_chunks} chunks complete")
                    
                except Exception as e:
                    st.warning(f"Error with chunk {chunk_index}: {str(e)}")
                    # Keep the original text for failed translations
                    chunk_results[chunk_index] = chunks[chunk_index]
        
        # Sort chunks by their original index
        sorted_chunks = [chunk_results.get(i, chunks[i]) for i in range(total_chunks)]
        result = ' '.join(sorted_chunks)
        
        # Clear progress indicators
        progress_bar.empty()
        progress_text.empty()
        
        return result
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails

# Dictionary mapping language codes to language names
LANGUAGE_DICT = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'ko': 'Korean',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'fi': 'Finnish',
    'no': 'Norwegian',
    'da': 'Danish',
    'pl': 'Polish',
    'uk': 'Ukrainian',
    'el': 'Greek',
    'he': 'Hebrew',
    'id': 'Indonesian',
    'vi': 'Vietnamese',
    'fa': 'Persian',
    'tr': 'Turkish',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'th': 'Thai'
}

# Dictionary mapping language codes to native language names
NATIVE_LANGUAGE_DICT = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'pt': 'Português',
    'ru': 'Русский',
    'ja': '日本語',
    'zh': '中文',
    'ar': 'العربية',
    'hi': 'हिन्दी',
    'ko': '한국어',
    'nl': 'Nederlands',
    'sv': 'Svenska',
    'fi': 'Suomi',
    'no': 'Norsk',
    'da': 'Dansk',
    'pl': 'Polski',
    'uk': 'Українська',
    'el': 'Ελληνικά',
    'he': 'עברית',
    'id': 'Bahasa Indonesia',
    'vi': 'Tiếng Việt',
    'fa': 'فارسی',
    'tr': 'Türkçe',
    'cs': 'Čeština',
    'hu': 'Magyar',
    'ro': 'Română',
    'th': 'ไทย'
}

def get_language_name(lang_code):
    """
    Get the full language name from a language code
    
    Args:
        lang_code (str): Language code (e.g., 'en', 'es')
        
    Returns:
        str: Full language name
    """
    return LANGUAGE_DICT.get(lang_code, lang_code)

def get_native_language_name(lang_code):
    """
    Get the native language name from a language code
    
    Args:
        lang_code (str): Language code (e.g., 'en', 'es')
        
    Returns:
        str: Native language name
    """
    return NATIVE_LANGUAGE_DICT.get(lang_code, lang_code)

def split_content_into_sections(content):
    """
    Split article content into sections for collapsible viewing
    
    Args:
        content (str): Article content text
        
    Returns:
        list: List of dictionaries with section titles and content
    """
    if not content:
        return []
    
    # Simple section detection by looking for lines that might be headers
    lines = content.split('\n')
    sections = []
    current_section = {"title": "Introduction", "content": ""}
    
    for line in lines:
        # Check if line looks like a section header (not perfect but works for basic cases)
        if line.strip() and len(line.strip()) < 100 and not line.strip().endswith('.'):
            # If we've accumulated content in the current section, add it to sections
            if current_section["content"].strip():
                sections.append(current_section)
            
            # Start a new section
            current_section = {
                "title": line.strip(),
                "content": ""
            }
        else:
            # Add line to current section
            current_section["content"] += line + "\n"
    
    # Add the last section if it has content
    if current_section["content"].strip():
        sections.append(current_section)
    
    return sections

def display_collapsible_sections(sections):
    """
    Display content sections in collapsible expanders
    
    Args:
        sections (list): List of dictionaries with section titles and content
    """
    if not sections:
        st.write("No content available")
        return
    
    # Display each section in an expander
    for i, section in enumerate(sections):
        # First section expanded by default, others collapsed
        with st.expander(section["title"], expanded=(i == 0)):
            st.markdown(section["content"])
            