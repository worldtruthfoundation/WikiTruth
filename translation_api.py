import os
import requests
import logging
import json
import html
import re
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Translation API options:
# 1. LibreTranslate API endpoint (free and open-source translation API)
LIBRE_TRANSLATE_API = os.environ.get("LIBRE_TRANSLATE_API", "https://libretranslate.de/translate")  # Using a public instance
LIBRE_TRANSLATE_API_KEY = os.environ.get("LIBRE_TRANSLATE_API_KEY", "")

# 2. Google Translate API (through free proxy - simulated for demo)
GOOGLE_TRANSLATE_API = "https://translate.googleapis.com/translate_a/single"

# Language name mapping for better error messages
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ru': 'Russian',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'pt': 'Portuguese',
    'it': 'Italian'
}

def translate_text(text, source_lang, target_lang):
    """
    Translate text from source language to target language
    Uses multiple translation services with fallback options
    
    Args:
        text (str): Text to translate
        source_lang (str): Source language code (e.g., 'en')
        target_lang (str): Target language code (e.g., 'es')
        
    Returns:
        str: Translated text
    """
    # If source and target languages are the same, return the original text
    if source_lang == target_lang:
        return text
    
    # Clean the text - remove excessive newlines and spaces
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Try multiple translation services with fallbacks
    translated_text = None
    errors = []
    
    # Try LibreTranslate first
    try:
        translated_text = _translate_with_libre(text, source_lang, target_lang)
        if translated_text:
            return translated_text
    except Exception as e:
        errors.append(f"LibreTranslate error: {str(e)}")
        logging.error(f"LibreTranslate error: {str(e)}")
    
    # Try Google Translate as fallback
    try:
        translated_text = _translate_with_google(text, source_lang, target_lang)
        if translated_text:
            return translated_text
    except Exception as e:
        errors.append(f"Google Translate error: {str(e)}")
        logging.error(f"Google Translate error: {str(e)}")
    
    # If both services failed, use our simple translation table as last resort
    try:
        translated_text = _simple_translation(text, source_lang, target_lang)
        if translated_text:
            return translated_text
    except Exception as e:
        errors.append(f"Simple translation error: {str(e)}")
        logging.error(f"Simple translation error: {str(e)}")
    
    # If all methods failed, return the original text with an error message
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    
    return f"Translation from {source_name} to {target_name} failed. Please try again later.\n\nOriginal text:\n{text}"

def _translate_with_libre(text, source_lang, target_lang):
    """Use LibreTranslate API for translation"""
    # Prepare the request payload
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    
    # Add API key if available
    if LIBRE_TRANSLATE_API_KEY:
        payload["api_key"] = LIBRE_TRANSLATE_API_KEY
    
    # Make the translation request with longer timeout
    response = requests.post(LIBRE_TRANSLATE_API, json=payload, timeout=10)
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        translated_text = result.get("translatedText")
        if translated_text:
            return html.unescape(translated_text)  # Unescape any HTML entities
    
    raise Exception(f"LibreTranslate API error: {response.status_code}")

def _translate_with_google(text, source_lang, target_lang):
    """Use Google Translate API for translation"""
    # Use the unofficial Google Translate API
    params = {
        'client': 'gtx',
        'sl': source_lang,
        'tl': target_lang,
        'dt': 't',
        'q': text
    }
    
    # Make the request with longer timeout
    response = requests.get(GOOGLE_TRANSLATE_API, params=params, timeout=10)
    
    if response.status_code == 200:
        # Parse the weird Google Translate response format
        result = response.json()
        if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            translated_parts = []
            
            # Collect all translated pieces
            for part in result[0]:
                if part and isinstance(part, list) and len(part) > 0 and isinstance(part[0], str):
                    translated_parts.append(part[0])
            
            if translated_parts:
                return ''.join(translated_parts)
    
    raise Exception(f"Google Translate API error: {response.status_code}")

def _simple_translation(text, source_lang, target_lang):
    """Ultra-simplistic translation for common words as last resort"""
    # Define some simple translation dictionaries for common words
    # This is just a fallback when online services fail
    translations = {
        'en-es': {
            'Hello': 'Hola',
            'World': 'Mundo',
            'Welcome': 'Bienvenido',
            'Thank you': 'Gracias',
            'Please': 'Por favor',
        },
        'en-fr': {
            'Hello': 'Bonjour',
            'World': 'Monde',
            'Welcome': 'Bienvenue',
            'Thank you': 'Merci',
            'Please': 'S\'il vous plaît',
        },
        # Add more languages as needed
    }
    
    # Try to use our simple translation
    trans_key = f"{source_lang}-{target_lang}"
    reverse_key = f"{target_lang}-{source_lang}"
    
    if trans_key in translations:
        # Forward translation
        dictionary = translations[trans_key]
        for eng, trans in dictionary.items():
            text = text.replace(eng, trans)
        return text
    elif reverse_key in translations:
        # Reverse translation
        dictionary = translations[reverse_key]
        reverse_dict = {v: k for k, v in dictionary.items()}
        for foreign, eng in reverse_dict.items():
            text = text.replace(foreign, eng)
        return text
    
    # If we don't have a dictionary for this language pair, add notice
    return f"{text}\n\n[This text would be translated from {source_lang} to {target_lang} with a proper API key]"
