import streamlit as st
import json
import os
import time
from wiki_utils import (
    get_wikipedia_search_results,
    get_article_content,
    get_available_languages,
    get_article_in_language,
    translate_text,
    get_language_name,
    get_native_language_name,
    split_content_into_sections,
    display_collapsible_sections,
    LANGUAGE_DICT
)
from highlight_utils import (
    get_highlights,
    save_highlight,
    apply_highlights_to_text,
    create_highlight_interface
)

# Page configuration
st.set_page_config(
    page_title="TruePedia - Multilingual Wikipedia Search",
    page_icon="📚",
    layout="wide"
)

# CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .article-title {
        font-size: 2rem;
        font-weight: bold;
        color: #1565C0;
        margin-bottom: 1rem;
    }
    .article-summary {
        font-size: 1.1rem;
        color: #424242;
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .lang-button {
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .article-content {
        font-size: 1rem;
        line-height: 1.5;
    }
    .wiki-link {
        color: #1565C0;
        text-decoration: none;
    }
    .wiki-link:hover {
        text-decoration: underline;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        font-size: 0.8rem;
        color: #757575;
    }
    .search-tag {
        display: inline-block;
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 8px 16px;
        margin: 4px;
        border-radius: 20px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
        border: 1px solid #BBDEFB;
    }
    .search-tag:hover {
        background-color: #BBDEFB;
        border-color: #1565C0;
    }
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
    }
    /* Style the buttons to look like tags */
    .stButton button {
        background-color: #E3F2FD;
        color: #1565C0;
        border-radius: 20px;
        border: 1px solid #BBDEFB;
        padding: 4px 12px;
        font-weight: 500;
        margin: 4px 0;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #BBDEFB;
        border-color: #1565C0;
    }
    mark {
        background-color: #FFFF00;
        padding: 0 2px;
    }
    .highlight-active {
        cursor: crosshair;
    }
    .highlight-btn {
        background-color: #FFF59D;
        color: #333;
        border: 1px solid #FBC02D;
    }
    .highlight-btn:hover {
        background-color: #FFEB3B;
    }
    .highlight-instructions {
        background-color: #FFF9C4;
        color: #333333;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        border: 1px solid #FBC02D;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'current_article' not in st.session_state:
    st.session_state.current_article = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'available_languages' not in st.session_state:
    st.session_state.available_languages = {}
if 'current_language' not in st.session_state:
    st.session_state.current_language = 'en'
if 'translate_to' not in st.session_state:
    st.session_state.translate_to = None
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = False
if 'highlight_mode' not in st.session_state:
    st.session_state.highlight_mode = False
if 'show_reviews' not in st.session_state:
    st.session_state.show_reviews = True

# Title and description
st.markdown('<div class="main-header">ЦWikiTruth</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Multilingual Wikipedia Search & Translation</div>', unsafe_allow_html=True)

# Sidebar for search and settings
with st.sidebar:
    st.subheader("Search Wikipedia")
    
    # Language selection for search
    search_lang = st.selectbox(
        "Search Language", 
        options=list(LANGUAGE_DICT.keys()),
        format_func=lambda x: f"{get_language_name(x)} ({x})"
    )
    
    # Search box
    search_query = st.text_input("Enter your search query", key="search_box")
    
    if st.button("Search"):
        if search_query:
            with st.spinner(f"Searching Wikipedia in {get_language_name(search_lang)}..."):
                st.session_state.search_results = get_wikipedia_search_results(search_query, search_lang)
                st.session_state.current_article = None
                st.session_state.available_languages = {}
                st.session_state.current_language = search_lang
                st.session_state.show_translation = False
    
    # Show search results if available
    if st.session_state.search_results:
        st.markdown("### 🔍 Search Results")
        
        # Add a styled container for search results
        st.markdown('<div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; border: 1px solid #BBDEFB;">', 
                   unsafe_allow_html=True)
        
        # Use multiple columns to create a cleaner tag layout
        cols = st.columns(2)
        
        # Display each result as a clickable button styled as a tag
        for idx, result in enumerate(st.session_state.search_results):
            with cols[idx % 2]:  # Distribute results across 2 columns for better visibility
                # Custom button style with more padding and distinctive appearance
                if st.button(f"🏷️ {result}", key=f"result_{idx}", use_container_width=True):
                    with st.spinner(f"Loading article: {result}..."):
                        st.session_state.current_article = get_article_content(result, st.session_state.current_language)
                        if st.session_state.current_article:
                            st.session_state.available_languages = get_available_languages(
                                result, 
                                st.session_state.current_language
                            )
                            st.session_state.show_translation = False
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Translation settings
    if st.session_state.current_article:
        st.markdown("### 🌐 Translation")
        st.markdown('<div style="padding: 10px; background-color: #E8F5E9; border-radius: 5px; border: 1px solid #81C784;">',
                  unsafe_allow_html=True)
        st.session_state.translate_to = st.selectbox(
            "Translate Article To",
            options=list(LANGUAGE_DICT.keys()),
            format_func=lambda x: f"{get_language_name(x)} ({x})",
            key="translate_lang"
        )
        
        if st.button("Translate Article", use_container_width=True):
            st.session_state.show_translation = True
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Review visibility toggle
    if st.session_state.current_article:
        st.markdown("### 👁️ Review Visibility")
        st.markdown('<div style="padding: 10px; background-color: #F3E5F5; border-radius: 5px; border: 1px solid #CE93D8;">',
                  unsafe_allow_html=True)
        
        show_reviews_toggle = st.toggle(
            "Show community reviews", 
            value=st.session_state.show_reviews,
            help="Toggle visibility of text marked for review by the community"
        )
        
        if show_reviews_toggle != st.session_state.show_reviews:
            st.session_state.show_reviews = show_reviews_toggle
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Highlighting controls
    if st.session_state.current_article:
        st.markdown("### ✏️ Collaborative Review")
        
        highlight_toggle = st.toggle("Enable Review Mode", value=st.session_state.highlight_mode)
        if highlight_toggle != st.session_state.highlight_mode:
            st.session_state.highlight_mode = highlight_toggle
            st.rerun()
            
        if st.session_state.highlight_mode:
            st.markdown("""
            <div style="background-color: #FFF9C4; color: #333333; padding: 12px; border-radius: 5px; 
                        margin-bottom: 10px; font-size: 0.9rem; border: 1px solid #FBC02D;">
                <b style="font-size: 1rem;">How to mark text for review:</b><br>
                1. Copy text from the article you want to review<br>
                2. Paste it in the "Part for review" box<br>
                3. Click 'Mark for Review'<br>
                4. Marked sections will be visible to all users
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        TruePedia uses Wikipedia API and free translation libraries<br>
        💡 Search in any language, explore articles, and collaborate with highlights
    </div>
    """, unsafe_allow_html=True)

# Main content area
if st.session_state.current_article:
    article = st.session_state.current_article
    
    # Display article title and summary
    st.markdown(f'<div class="article-title">{article["title"]}</div>', unsafe_allow_html=True)
    
    # Display Wikipedia link
    st.markdown(f'<a href="{article["url"]}" target="_blank" class="wiki-link">📖 View on Wikipedia</a>', unsafe_allow_html=True)
    
    # Display language options in an organized dropdown
    with st.expander("Available Languages", expanded=True):
        # Group languages by region/script for better organization
        st.write("Select a language to view this article in:")
        
        # Create a selectbox with native language names
        # Get the list of available languages with their native names
        language_options = []
        for lang_code, lang_title in st.session_state.available_languages.items():
            native_name = get_native_language_name(lang_code)
            display_name = f"{native_name} - {get_language_name(lang_code)} ({lang_code})"
            language_options.append((lang_code, lang_title, display_name))
        
        # Sort by display name
        language_options.sort(key=lambda x: x[2])
        
        # Create the dropdown
        if 'selected_language' not in st.session_state:
            st.session_state.selected_language = st.session_state.current_language
            
        selected_lang_index = 0
        for i, (code, _, _) in enumerate(language_options):
            if code == st.session_state.current_language:
                selected_lang_index = i
                break
                
        selected_option = st.selectbox(
            "Choose Language",
            options=range(len(language_options)),
            format_func=lambda i: language_options[i][2],
            index=selected_lang_index,
            key="language_selector"
        )
        
        # Button to load the selected language
        if st.button("View in Selected Language", use_container_width=True):
            lang_code, lang_title, _ = language_options[selected_option]
            with st.spinner(f"Loading article in {get_language_name(lang_code)}..."):
                st.session_state.current_article = get_article_in_language(lang_title, lang_code)
                st.session_state.current_language = lang_code
                st.session_state.show_translation = False
                st.rerun()
    
    # Create tabs for summary and full content
    summary_tab, content_tab = st.tabs(["Summary", "Full Content"])
    
    with summary_tab:
        # Get article ID for highlights
        article_id = f"{article['title']}_{st.session_state.current_language}"
        highlights = get_highlights(article_id)
        
        # If translation is requested, show translated summary
        if st.session_state.show_translation and st.session_state.translate_to != st.session_state.current_language:
            with st.spinner(f"Translating summary to {get_language_name(st.session_state.translate_to)}..."):
                translated_summary = translate_text(
                    article["summary"],
                    st.session_state.translate_to,
                    st.session_state.current_language
                )
                
                # Apply highlights if showing reviews is enabled
                if st.session_state.show_reviews and highlights:
                    highlighted_text = apply_highlights_to_text(translated_summary, highlights)
                else:
                    highlighted_text = translated_summary
                
                # Show the text
                st.markdown(f'<div class="article-summary">{highlighted_text}</div>', unsafe_allow_html=True)
                
                # Add highlighting interface if needed
                if st.session_state.highlight_mode:
                    create_highlight_interface(translated_summary, article_id, "summary")
        else:
            # Apply highlights if showing reviews is enabled
            if st.session_state.show_reviews and highlights:
                highlighted_text = apply_highlights_to_text(article["summary"], highlights)
            else:
                highlighted_text = article["summary"]
            
            # Show the text
            st.markdown(f'<div class="article-summary">{highlighted_text}</div>', unsafe_allow_html=True)
            
            # Add highlighting interface if needed
            if st.session_state.highlight_mode:
                create_highlight_interface(article["summary"], article_id, "summary")
    
    with content_tab:
        # Article ID for highlighting
        article_id = f"{article['title']}_{st.session_state.current_language}"
        
        # Make article content collapsible in sections
        if st.session_state.show_translation and st.session_state.translate_to != st.session_state.current_language:
            with st.spinner(f"Translating content to {get_language_name(st.session_state.translate_to)}..."):
                # Split the content into sections first for better handling of large texts
                original_sections = split_content_into_sections(article["content"])
                
                translated_sections = []
                
                # Create a progress bar for section translation
                section_progress = st.progress(0)
                section_text = st.empty()
                section_text.text("Preparing to translate sections...")
                
                # Translate each section separately (smaller chunks are easier to handle)
                for i, section in enumerate(original_sections):
                    section_text.text(f"Translating section {i+1}/{len(original_sections)}: {section['title']}")
                    
                    # Update progress
                    section_progress.progress((i) / len(original_sections))
                    
                    # Translate the section title and content
                    translated_title = translate_text(
                        section["title"],
                        st.session_state.translate_to,
                        st.session_state.current_language
                    )
                    
                    translated_content = translate_text(
                        section["content"],
                        st.session_state.translate_to,
                        st.session_state.current_language
                    )
                    
                    # Add to our list of translated sections
                    translated_sections.append({
                        "title": translated_title,
                        "content": translated_content
                    })
                    
                    # Update progress after section is complete
                    section_progress.progress((i+1) / len(original_sections))
                
                # Clear progress indicators
                section_progress.empty()
                section_text.empty()
                
                # Use the translated sections directly
                sections = translated_sections
                
                # Get highlights
                highlights = get_highlights(article_id)
                
                # For each section, apply highlights if showing reviews is enabled
                for i, section in enumerate(sections):
                    with st.expander(section["title"], expanded=(i == 0)):
                        # Apply highlights if showing reviews is enabled
                        if st.session_state.show_reviews and highlights:
                            section_content = apply_highlights_to_text(section["content"], highlights)
                        else:
                            section_content = section["content"]
                            
                        st.markdown(section_content, unsafe_allow_html=True)
                        
                        if st.session_state.highlight_mode:
                            create_highlight_interface(section["content"], article_id, f"section_{i}")
                
                # No length limitations on translation
                pass
        else:
            # Split content into sections for collapsible viewing
            sections = split_content_into_sections(article["content"])
            
            # Get highlights
            highlights = get_highlights(article_id)
            
            # For each section, apply highlights if showing reviews is enabled
            for i, section in enumerate(sections):
                with st.expander(section["title"], expanded=(i == 0)):
                    # Apply highlights if showing reviews is enabled
                    if st.session_state.show_reviews and highlights:
                        section_content = apply_highlights_to_text(section["content"], highlights)
                    else:
                        section_content = section["content"]
                        
                    st.markdown(section_content, unsafe_allow_html=True)
                    
                    if st.session_state.highlight_mode:
                        create_highlight_interface(section["content"], article_id, f"section_{i}")
else:
    # Welcome message when no article is selected
    st.info("👈 Search for a Wikipedia article in any language to get started!")
    
    # Brief instructions
    st.markdown("""
    ### How to use TruePedia:
    
    1. 🔍 **Search**: Enter a query and select your preferred language
    2. 📝 **Select**: Choose an article from the search results (displayed as tags)
    3. 🌐 **Explore**: View the article in different languages
    4. 🔄 **Translate**: Translate the article content to your preferred language
    5. 👁️ **Toggle Reviews**: Choose whether to see community reviews and highlights
    6. ✨ **Collaborate**: Highlight important passages for other users to see
    
    TruePedia gives you access to Wikipedia content across multiple languages, provides translation capabilities, and allows collaborative highlighting for better knowledge sharing.
    """)
