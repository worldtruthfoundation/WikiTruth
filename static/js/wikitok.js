// Global variables for WikiTok
let selectedLanguages = ['en']; // Default to English, can select multiple
let imagesOnly = true;
let offset = 0;
let loading = false;
let noMoreArticles = false;
let articlesPerPage = 5;
let currentArticles = [];

// Initialize WikiTok
document.addEventListener('DOMContentLoaded', function() {
    // Set initial filter values from URL parameters or defaults
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check for languages in URL parameter
    const langParam = urlParams.get('languages');
    if (langParam) {
        selectedLanguages = langParam.split(',');
    } else {
        selectedLanguages = ['en']; // Default to English if not specified
    }
    
    imagesOnly = urlParams.get('images_only') !== 'false';
    
    // Set form fields to match current settings
    selectedLanguages.forEach(lang => {
        const checkbox = document.getElementById(`lang-${lang}`);
        if (checkbox) checkbox.checked = true;
    });
    
    document.querySelector(`input[name="image-filter"][value="${imagesOnly}"]`).checked = true;
    
    // Set up language selection buttons
    document.getElementById('select-all-langs').addEventListener('click', function() {
        document.querySelectorAll('.language-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
    });
    
    document.getElementById('deselect-all-langs').addEventListener('click', function() {
        document.querySelectorAll('.language-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        // Always keep at least one language selected (English by default)
        const englishCheckbox = document.getElementById('lang-en');
        if (englishCheckbox) englishCheckbox.checked = true;
    });
    
    // Load initial set of articles
    loadArticles();
    
    // Set up filter button
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    
    // Set up infinite scroll (with throttling for performance)
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        if (scrollTimeout) clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(handleScroll, 100); // Throttle to once every 100ms
    });
});

// Apply filters from form
function applyFilters() {
    // Get selected languages
    selectedLanguages = [];
    document.querySelectorAll('.language-checkbox:checked').forEach(checkbox => {
        selectedLanguages.push(checkbox.value);
    });
    
    // Ensure at least one language is selected
    if (selectedLanguages.length === 0) {
        selectedLanguages = ['en'];
        document.getElementById('lang-en').checked = true;
        alert('Please select at least one language.');
        return;
    }
    
    // Get image filter setting
    imagesOnly = document.querySelector('input[name="image-filter"]:checked').value === 'true';
    
    // Reset pagination and article tracking
    offset = 0;
    noMoreArticles = false;
    currentArticles = [];
    
    // Update URL with new parameters
    const url = new URL(window.location);
    url.searchParams.set('languages', selectedLanguages.join(','));
    url.searchParams.set('images_only', imagesOnly);
    window.history.pushState({}, '', url);
    
    // Clear existing articles and show loading indicator
    const feed = document.getElementById('wikitok-feed');
    feed.innerHTML = `
        <div class="text-center p-5">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading articles from ${selectedLanguages.length} language(s)...</p>
        </div>
    `;
    
    // Load articles with new filters
    loadArticles();
}

// Load articles from API
function loadArticles() {
    if (loading || noMoreArticles) return;
    
    loading = true;
    
    // Show loader if this is the first page
    if (offset === 0) {
        document.getElementById('wikitok-feed').innerHTML = `
            <div class="text-center p-5">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading articles from ${selectedLanguages.length} language(s)...</p>
            </div>
        `;
    } else {
        // Show scroll loader
        document.getElementById('scroll-loader').style.display = 'block';
    }
    
    // Set up for loading articles from multiple languages simultaneously
    const promises = [];
    
    // Fetch articles for each selected language
    selectedLanguages.forEach(language => {
        const promise = fetch(`/api/wikitok/articles?language=${language}&images_only=${imagesOnly}&offset=${offset}&limit=${Math.ceil(articlesPerPage / selectedLanguages.length)}`)
            .then(response => response.json())
            .then(data => {
                if (Array.isArray(data)) {
                    return data;
                } else if (data.error) {
                    console.error(`Error fetching ${language} articles:`, data.error);
                    return [];
                }
                return [];
            })
            .catch(error => {
                console.error(`Error fetching ${language} articles:`, error);
                return [];
            });
        
        promises.push(promise);
    });
    
    // Process all language article requests simultaneously
    Promise.all(promises)
        .then(results => {
            // Combine all articles from different languages
            let allArticles = [];
            results.forEach(articles => {
                allArticles = allArticles.concat(articles);
            });
            
            // Clear loader
            if (offset === 0) {
                document.getElementById('wikitok-feed').innerHTML = '';
            }
            document.getElementById('scroll-loader').style.display = 'none';
            
            // Check if we have articles
            if (allArticles.length === 0) {
                if (offset === 0) {
                    // No articles found
                    document.getElementById('wikitok-feed').innerHTML = `
                        <div class="alert alert-info">
                            No articles found with the current filters.
                            Try selecting different languages or display settings.
                        </div>
                    `;
                    noMoreArticles = true;
                } else {
                    // End of articles
                    const endDiv = document.createElement('div');
                    endDiv.className = 'text-center p-3 text-muted';
                    endDiv.innerHTML = `
                        <i class="fas fa-check-circle mb-2"></i>
                        <p>You've reached the end of the feed.</p>
                    `;
                    document.getElementById('wikitok-feed').appendChild(endDiv);
                    noMoreArticles = true;
                }
            } else {
                // Sort and shuffle articles from different languages to mix them
                allArticles.sort(() => Math.random() - 0.5);
                
                // Add new articles to tracking array
                currentArticles = currentArticles.concat(allArticles);
                
                // Render articles
                renderArticles(allArticles);
                
                // Update offset for next page
                offset += Math.ceil(articlesPerPage / selectedLanguages.length);
            }
            
            loading = false;
        })
        .catch(error => {
            console.error('Error loading articles:', error);
            document.getElementById('scroll-loader').style.display = 'none';
            
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.textContent = 'Error loading articles. Please try again.';
            document.getElementById('wikitok-feed').appendChild(errorDiv);
            
            loading = false;
        });
}

// Render articles in the feed
function renderArticles(articles) {
    const feed = document.getElementById('wikitok-feed');
    
    // Calculate starting index for animation staggering
    const startIndex = document.querySelectorAll('.article-card').length;
    
    articles.forEach((article, index) => {
        const card = document.createElement('div');
        card.className = 'article-card';
        
        // Set staggered animation index as a CSS variable
        card.style.setProperty('--card-index', startIndex + index);
        
        // Add language badge if multiple languages are selected
        const languageBadge = selectedLanguages.length > 1 ? 
            `<span class="badge bg-light text-dark position-absolute top-0 end-0 m-2 language-badge">${article.language_name || article.language}</span>` : 
            '';
        
        // Prepare image HTML with loading optimization
        const imageHtml = article.image ? 
            `<div class="article-card-image-container">
                <img src="${article.image}" alt="${article.title}" 
                     class="article-card-image" loading="lazy">
                ${languageBadge}
             </div>` : 
            `<div class="article-card-image-placeholder">${languageBadge}</div>`;
        
        // Create card HTML with more detailed and engaging layout
        card.innerHTML = `
            ${imageHtml}
            <div class="article-card-content">
                <h3 class="article-card-title">${article.title}</h3>
                <div class="article-card-summary">${article.summary}</div>
                <div class="article-card-actions">
                    <a href="/article/${article.language}/${encodeURIComponent(article.title)}" class="btn btn-accent-blue">
                        <i class="fas fa-book-open"></i> Read More
                    </a>
                    <div class="btn-group">
                        <button class="btn btn-outline-secondary" title="Share" 
                                onclick="shareWikiTokArticle('${encodeURIComponent(article.title)}', '${article.language}')">
                            <i class="fas fa-share-alt"></i>
                        </button>
                        <button class="btn btn-outline-secondary" title="Download" 
                                onclick="downloadWikiTokArticle('${encodeURIComponent(article.title)}', '${article.summary}', '${article.language}')">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        feed.appendChild(card);
        
        // Add animation timing to ensure smooth performance
        // by staggering when animations and layout calculations happen
        if (index % 3 === 0) {
            // Allow browser to process a batch of 3 cards before continuing
            setTimeout(() => {}, 0);
        }
    });
}

// Infinite scroll handler
function handleScroll() {
    if (loading || noMoreArticles) return;
    
    const scrollTop = (document.documentElement && document.documentElement.scrollTop) || document.body.scrollTop;
    const scrollHeight = (document.documentElement && document.documentElement.scrollHeight) || document.body.scrollHeight;
    const clientHeight = document.documentElement.clientHeight || window.innerHeight;
    
    // Load more articles when scrolled near the bottom
    if (scrollTop + clientHeight >= scrollHeight - 300) {
        loadArticles();
    }
}

// Share a WikiTok article
function shareWikiTokArticle(title, language) {
    // Set the global shareUrl
    shareUrl = `${window.location.origin}/article/${language}/${title}`;
    
    // Show the share modal
    showShareOptions();
}

// Download a WikiTok article summary
function downloadWikiTokArticle(title, summary, language) {
    // Send request to server to generate DOCX
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'title': decodeURIComponent(title),
            'content': summary,
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error generating document: ' + data.error);
        } else {
            // Create a temporary link to download the file
            const downloadLink = document.createElement('a');
            downloadLink.href = data.docx_url;
            downloadLink.download = `${decodeURIComponent(title)}.docx`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Error downloading content. Please try again.');
    });
}
