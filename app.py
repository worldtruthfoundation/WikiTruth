import os
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash

from wikipedia_api import (
    search_wikipedia, 
    get_article_summary, 
    get_article_content, 
    get_article_images,
    get_random_articles,
    get_article_languages
)
from translation_api import translate_text
from docx_generator import generate_docx

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "wikitruth-dev-key")

# Available languages for search and display
LANGUAGES = {
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

@app.route('/')
def home():
    # Set default language if not already set
    if 'language' not in session:
        session['language'] = 'en'
    
    return render_template('home.html', languages=LANGUAGES, current_lang=session['language'])

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    language = request.form.get('language', 'en')
    
    # Save language preference in session
    session['language'] = language
    
    if not query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('home'))
    
    # Search Wikipedia
    try:
        search_results = search_wikipedia(query, language)
        if not search_results:
            flash('No results found', 'info')
            return redirect(url_for('home'))
            
        return render_template('tag_results.html', 
                              results=search_results, 
                              query=query, 
                              language=language,
                              languages=LANGUAGES)
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        flash(f"Error searching Wikipedia: {str(e)}", 'error')
        return redirect(url_for('home'))

@app.route('/article/<lang>/<title>')
def article(lang, title):
    try:
        # Validate language code
        if lang not in LANGUAGES:
            lang = 'en'  # Default to English if invalid language
        
        # Get article summary and content
        summary = get_article_summary(title, lang)
        content = get_article_content(title, lang)
        images = get_article_images(title, lang)
        available_languages = get_article_languages(title, lang)
        
        # Get main image for top of article
        main_image = None
        content_images = []
        
        # Process images to separate main image from content images
        if images:
            # First try to find an image marked as main
            for img in images:
                if isinstance(img, dict) and img.get('is_main'):
                    main_image = img.get('url')
                    break
                
            # If no main image found, use the first one
            if not main_image and images:
                main_image = images[0]['url'] if isinstance(images[0], dict) else images[0]
            
            # Add remaining images to content images
            for img in images:
                img_url = img.get('url') if isinstance(img, dict) else img
                if img_url != main_image:
                    content_images.append(img_url)
        
        # Filter available languages to only include those we support
        # Make sure we have the current language in the available options
        filtered_languages = {k: v for k, v in available_languages.items() if k in LANGUAGES}
        
        # If current language isn't in filtered_languages, add it
        if lang not in filtered_languages:
            filtered_languages[lang] = LANGUAGES[lang]
        
        # Get additional Wikipedia language links to show all available languages
        try:
            # Format URL for more translations on Wikipedia
            wiki_lang_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
        except Exception:
            wiki_lang_url = None
        
        return render_template('article.html',
                              title=title,
                              summary=summary,
                              content=content,
                              main_image=main_image,
                              content_images=content_images,
                              language=lang,
                              languages=LANGUAGES,
                              available_languages=filtered_languages,
                              wiki_lang_url=wiki_lang_url)
    except Exception as e:
        logging.error(f"Article retrieval error: {str(e)}")
        flash(f"Error retrieving article: {str(e)}", 'error')
        return redirect(url_for('home'))

@app.route('/translate', methods=['POST'])
def translate():
    try:
        text = request.form.get('text', '')
        source_lang = request.form.get('source_lang', 'en')
        target_lang = request.form.get('target_lang', 'en')
        
        translated_text = translate_text(text, source_lang, target_lang)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        language = request.form.get('language', 'en')
        
        # Generate the DOCX file and send it
        docx_file = generate_docx(title, content)
        
        return jsonify({'docx_url': docx_file})
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/wikitok')
def wikitok():
    # Get languages from query parameter or default to English
    languages_param = request.args.get('languages', 'en')
    selected_langs = languages_param.split(',')
    
    # Validate languages are in our supported list
    selected_langs = [lang for lang in selected_langs if lang in LANGUAGES]
    if not selected_langs:
        selected_langs = ['en']
    
    images_only = request.args.get('images_only', 'true') == 'true'
    
    return render_template('wikitok.html', 
                          languages=LANGUAGES, 
                          selected_langs=selected_langs,
                          images_only=images_only)

@app.route('/api/wikitok/articles')
def get_wikitok_articles():
    try:
        # Get language parameter - can be a single language
        language = request.args.get('language', 'en')
        
        # Make sure language is valid
        if language not in LANGUAGES:
            language = 'en'
            
        images_only = request.args.get('images_only', 'true') == 'true'
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 5))
        
        # Get random articles for the requested language
        # Use a smaller limit to improve performance
        articles = get_random_articles(language, min(limit, 10), images_only, offset)
        
        # Add language name to each article
        for article in articles:
            article['language_name'] = LANGUAGES.get(article['language'], 'Unknown')
            
        return jsonify(articles)
    except Exception as e:
        logging.error(f"WikiTok articles error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500
