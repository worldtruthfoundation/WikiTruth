// Global variables for article page
let articleTitle;
let articleLanguage;
let articleSummary;
let articleContent = {};
let currentTranslation = '';

// Initialize the article page
document.addEventListener('DOMContentLoaded', function() {
    // Get article data from hidden form
    articleTitle = document.getElementById('article-title').value;
    articleLanguage = document.getElementById('article-language').value;
    articleSummary = document.getElementById('article-summary').value;
    
    // Load article sections
    const sectionInputs = document.querySelectorAll('[id^="article-section-"]');
    sectionInputs.forEach(input => {
        const sectionName = input.getAttribute('data-section');
        articleContent[sectionName] = input.value;
    });
    
    // Set up view mode switching
    const summaryMode = document.getElementById('summary-mode');
    const fullMode = document.getElementById('full-mode');
    
    if (summaryMode && fullMode) {
        summaryMode.addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('summary-view').style.display = 'block';
                document.getElementById('full-view').style.display = 'none';
            }
        });
        
        fullMode.addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('summary-view').style.display = 'none';
                document.getElementById('full-view').style.display = 'block';
            }
        });
    }
    
    // Set up language switcher
    const languageSelect = document.getElementById('article-language');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            const newLanguage = this.value;
            const currentPath = window.location.pathname;
            const pathParts = currentPath.split('/');
            
            // Replace language code in path
            pathParts[2] = newLanguage;
            
            // Redirect to the article in the new language
            window.location.href = pathParts.join('/');
        });
    }
    
    // Set up translation part selector
    const translatePartRadios = document.getElementsByName('translate-part');
    translatePartRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const sectionSelector = document.getElementById('section-selector');
            if (this.value === 'section') {
                sectionSelector.style.display = 'block';
            } else {
                sectionSelector.style.display = 'none';
            }
        });
    });
    
    // Set up Back to TOC button
    const backToTocButton = document.getElementById('back-to-toc');
    if (backToTocButton) {
        // Show button when scrolling down in full mode
        window.addEventListener('scroll', function() {
            // Get the full mode radio button to ensure it's available
            const fullMode = document.getElementById('full-mode');
            const tocContainer = document.querySelector('.toc-container');
            
            // Show button when scrolled past TOC container in full mode
            if (fullMode && fullMode.checked && tocContainer) {
                const tocRect = tocContainer.getBoundingClientRect();
                // If TOC is out of view (scrolled past it)
                if (tocRect.bottom < 0) {
                    backToTocButton.classList.remove('d-none');
                    backToTocButton.classList.add('d-block');
                } else {
                    backToTocButton.classList.remove('d-block');
                    backToTocButton.classList.add('d-none');
                }
            } else {
                backToTocButton.classList.remove('d-block');
                backToTocButton.classList.add('d-none');
            }
        });
        
        // Scroll back to TOC when clicked
        backToTocButton.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default behavior
            const tocContainer = document.querySelector('.toc-container');
            if (tocContainer) {
                // Add animation highlight
                tocContainer.classList.add('toc-highlight');
                
                // Scroll to the TOC
                tocContainer.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Remove highlight after animation
                setTimeout(() => {
                    tocContainer.classList.remove('toc-highlight');
                }, 2000);
            }
        });
    }
    
    // Update button visibility when switching views or resizing
    const viewModeRadios = document.querySelectorAll('input[name="view-mode"]');
    viewModeRadios.forEach(radio => {
        radio.addEventListener('change', updateBackToTocButton);
    });
    
    // Add resize handler to update TOC button visibility
    window.addEventListener('resize', updateBackToTocButton);
    
    // Function to update back to TOC button visibility
    function updateBackToTocButton() {
        if (!backToTocButton) return;
        
        const fullMode = document.getElementById('full-mode');
        const tocContainer = document.querySelector('.toc-container');
        
        if (fullMode && fullMode.checked && tocContainer) {
            const tocRect = tocContainer.getBoundingClientRect();
            if (tocRect.bottom < 0) {
                backToTocButton.classList.remove('d-none');
                backToTocButton.classList.add('d-block');
            } else {
                backToTocButton.classList.remove('d-block');
                backToTocButton.classList.add('d-none');
            }
        } else {
            backToTocButton.classList.remove('d-block');
            backToTocButton.classList.add('d-none');
        }
    }
});

// Download article content
function downloadContent(type) {
    const title = document.getElementById('article-title').value;
    const language = document.getElementById('article-language').value;
    let content = '';
    let downloadTitle = title;
    
    if (type === 'summary') {
        content = document.getElementById('article-summary').value;
        downloadTitle = `${title} - Summary`;
    } else if (type === 'full') {
        // Combine all sections into a single document
        const sections = {};
        document.querySelectorAll('[id^="article-section-"]').forEach(input => {
            const sectionName = input.getAttribute('data-section');
            sections[sectionName] = input.value;
        });
        content = JSON.stringify(sections);
        downloadTitle = `${title} - Full Article`;
    }
    
    // Show loading indicator
    const downloadButton = event.target.closest('button');
    const originalInnerHTML = downloadButton.innerHTML;
    downloadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    downloadButton.disabled = true;
    
    // Send request to server to generate DOCX
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'title': downloadTitle,
            'content': content,
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        downloadButton.innerHTML = originalInnerHTML;
        downloadButton.disabled = false;
        
        if (data.error) {
            alert('Error generating document: ' + data.error);
        } else {
            // Create a temporary link to download the file
            const downloadLink = document.createElement('a');
            downloadLink.href = data.docx_url;
            downloadLink.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}.docx`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // Show success message
            const successToast = document.createElement('div');
            successToast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            successToast.innerHTML = `
                <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="fas fa-check-circle me-2"></i> Document downloaded successfully!
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            document.body.appendChild(successToast);
            const toastEl = successToast.querySelector('.toast');
            const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
            toast.show();
            
            // Remove toast after it's hidden
            toastEl.addEventListener('hidden.bs.toast', () => {
                document.body.removeChild(successToast);
            });
        }
    })
    .catch(error => {
        // Reset button state
        downloadButton.innerHTML = originalInnerHTML;
        downloadButton.disabled = false;
        
        console.error('Download error:', error);
        alert('Error downloading content. Please try again.');
    });
}

// Download a specific section
function downloadSection(sectionName) {
    const title = document.getElementById('article-title').value;
    const language = document.getElementById('article-language').value;
    
    // Find the section content
    let sectionContent = '';
    document.querySelectorAll('[id^="article-section-"]').forEach(input => {
        if (input.getAttribute('data-section') === sectionName) {
            sectionContent = input.value;
        }
    });
    
    if (!sectionContent) {
        alert('Section content not found');
        return;
    }
    
    // Create a download title that includes the section name
    const downloadTitle = `${title} - ${sectionName}`;
    
    // Show loading indicator
    const downloadButton = event.target.closest('button');
    const originalInnerHTML = downloadButton.innerHTML;
    downloadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    downloadButton.disabled = true;
    
    // Send request to server to generate DOCX
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'title': downloadTitle,
            'content': sectionContent,
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        downloadButton.innerHTML = originalInnerHTML;
        downloadButton.disabled = false;
        
        if (data.error) {
            alert('Error generating document: ' + data.error);
        } else {
            // Create a temporary link to download the file
            const downloadLink = document.createElement('a');
            downloadLink.href = data.docx_url;
            // Create a safe filename
            const safeTitle = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${sectionName.replace(/[^a-zA-Z0-9]/g, '_')}`;
            downloadLink.download = `${safeTitle}.docx`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // Show success message
            const successToast = document.createElement('div');
            successToast.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            successToast.innerHTML = `
                <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="fas fa-check-circle me-2"></i> Section "${sectionName}" downloaded!
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            document.body.appendChild(successToast);
            const toastEl = successToast.querySelector('.toast');
            const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
            toast.show();
            
            // Remove toast after it's hidden
            toastEl.addEventListener('hidden.bs.toast', () => {
                document.body.removeChild(successToast);
            });
        }
    })
    .catch(error => {
        // Reset button state
        downloadButton.innerHTML = originalInnerHTML;
        downloadButton.disabled = false;
        
        console.error('Download error:', error);
        alert('Error downloading content. Please try again.');
    });
}

// Show article share options
function showArticleShareOptions() {
    // Set the global shareUrl to the current article URL
    shareUrl = window.location.href;
    
    // Show the share modal
    showShareOptions();
}

// Share article on social media
function shareArticleOn(platform) {
    // Set the global shareUrl to the current article URL
    shareUrl = window.location.href;
    
    // Use the global shareOn function
    shareOn(platform);
}

// Copy article share link
function copyArticleShareLink() {
    const shareUrlInput = document.getElementById('article-share-url');
    shareUrlInput.select();
    shareUrlInput.setSelectionRange(0, 99999);
    
    try {
        navigator.clipboard.writeText(shareUrlInput.value)
            .then(() => {
                const copyButton = shareUrlInput.nextElementSibling;
                const originalText = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
                
                setTimeout(() => {
                    copyButton.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Could not copy text: ', err);
                document.execCommand('copy');
            });
    } catch (err) {
        console.error('Could not copy text: ', err);
        document.execCommand('copy');
    }
}

// Translate selected content
function translateSelected() {
    const targetLang = document.getElementById('translate-target').value;
    const translatePart = document.querySelector('input[name="translate-part"]:checked').value;
    
    let textToTranslate = '';
    let titlePrefix = '';
    
    if (translatePart === 'summary') {
        textToTranslate = articleSummary;
        titlePrefix = 'Summary';
    } else {
        const sectionName = document.getElementById('translate-section-select').value;
        textToTranslate = articleContent[sectionName];
        titlePrefix = `Section: ${sectionName}`;
    }
    
    // Show loading indicator
    const translationResult = document.getElementById('translation-result');
    translationResult.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Translating...</p></div>';
    
    // Show the translation result modal while loading
    const translationResultModal = new bootstrap.Modal(document.getElementById('translationResultModal'));
    translationResultModal.show();
    
    // Send request to server to translate
    fetch('/translate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'text': textToTranslate,
            'source_lang': articleLanguage,
            'target_lang': targetLang
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            translationResult.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else {
            // Display the translated text
            currentTranslation = data.translated_text;
            
            // Update modal title and content
            document.querySelector('#translationResultModal .modal-title').textContent = 
                `${titlePrefix} (Translated to ${document.getElementById('translate-target').options[document.getElementById('translate-target').selectedIndex].text})`;
            
            translationResult.innerHTML = `<div class="translation-text">${currentTranslation.replace(/\n/g, '<br>')}</div>`;
        }
    })
    .catch(error => {
        console.error('Translation error:', error);
        translationResult.innerHTML = `<div class="alert alert-danger">Error during translation. Please try again.</div>`;
    });
    
    // Close the translate modal
    const translateModal = bootstrap.Modal.getInstance(document.getElementById('translateModal'));
    if (translateModal) translateModal.hide();
}

// Translate a specific section directly with selectable target language
function translateSection(sectionName, sourceLang) {
    // Create dropdown for language selection
    const dropdown = document.createElement('div');
    dropdown.className = 'dropdown-menu p-2 show';
    dropdown.id = 'quick-language-dropdown';
    dropdown.style.position = 'absolute';
    dropdown.style.zIndex = '1050';
    dropdown.style.maxHeight = '300px';
    dropdown.style.overflowY = 'auto';
    dropdown.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
    dropdown.style.minWidth = '200px';
    dropdown.style.backgroundColor = '#fff';
    dropdown.style.borderRadius = '8px';
    
    // Add header
    const header = document.createElement('h6');
    header.className = 'dropdown-header';
    header.textContent = 'Translate to:';
    dropdown.appendChild(header);
    
    // Get all available languages from the language selector
    const languageSelector = document.getElementById('article-language');
    const currentLang = languageSelector.value;
    
    // Add options for each language except the current one
    for (let i = 0; i < languageSelector.options.length; i++) {
        const option = languageSelector.options[i];
        // Skip current language
        if (option.value === currentLang) continue;
        
        const item = document.createElement('button');
        item.className = 'dropdown-item';
        item.textContent = option.text;
        item.value = option.value;
        
        // Add click handler for translation
        item.addEventListener('click', function() {
            // Get section text 
            let textToTranslate = '';
            for (let i = 0; i < document.querySelectorAll('[id^="article-section-"]').length; i++) {
                const section = document.querySelectorAll('[id^="article-section-"]')[i];
                if (section.getAttribute('data-section') === sectionName) {
                    textToTranslate = section.value;
                    break;
                }
            }
            
            // Remove dropdown
            document.body.removeChild(dropdown);
            
            // Show loading indicator
            const translationResult = document.getElementById('translation-result');
            translationResult.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p>Translating...</p></div>';
            
            // Show the translation result modal
            const translationResultModal = new bootstrap.Modal(document.getElementById('translationResultModal'));
            translationResultModal.show();
            
            // Perform translation
            fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'text': textToTranslate,
                    'source_lang': sourceLang,
                    'target_lang': this.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    translationResult.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                } else {
                    // Store translation for download
                    currentTranslation = data.translated_text;
                    
                    // Set modal title
                    document.querySelector('#translationResultModal .modal-title').textContent = 
                        `${sectionName} (Translated to ${this.textContent})`;
                    
                    // Show translated content
                    translationResult.innerHTML = `
                        <div class="mb-3 bg-light p-2 rounded">
                            <small class="text-muted">Translated from ${languageSelector.options[languageSelector.selectedIndex].text} to ${this.textContent}</small>
                        </div>
                        <div class="translation-text p-3 border rounded bg-white">${data.translated_text.replace(/\n/g, '<br>')}</div>
                    `;
                }
            })
            .catch(error => {
                console.error('Translation error:', error);
                translationResult.innerHTML = `<div class="alert alert-danger">Error during translation. Please try again.</div>`;
            });
        });
        
        dropdown.appendChild(item);
    }
    
    // Position dropdown near the button that was clicked
    const button = event.target.closest('button');
    const rect = button.getBoundingClientRect();
    
    // Append to body
    document.body.appendChild(dropdown);
    
    // Calculate position
    const dropdownRect = dropdown.getBoundingClientRect();
    
    // Adjust position to avoid overflow
    let top = rect.bottom + window.scrollY + 5;
    let left = rect.left + window.scrollX;
    
    // Check if dropdown would go off the right edge
    if (left + dropdownRect.width > window.innerWidth) {
        left = window.innerWidth - dropdownRect.width - 10;
    }
    
    // Set position
    dropdown.style.top = top + 'px';
    dropdown.style.left = left + 'px';
    
    // Close when clicking outside
    setTimeout(() => {
        const closeHandler = function(e) {
            if (!dropdown.contains(e.target) && e.target !== button) {
                if (document.body.contains(dropdown)) {
                    document.body.removeChild(dropdown);
                }
                document.removeEventListener('click', closeHandler);
            }
        };
        document.addEventListener('click', closeHandler);
    }, 100);
}

// Download the current translation
function downloadTranslation() {
    if (!currentTranslation) {
        alert('No translation available to download');
        return;
    }
    
    const title = document.getElementById('article-title').value;
    const targetLang = document.getElementById('translate-target').value;
    
    // Send request to server to generate DOCX
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'title': `${title} (Translated to ${targetLang})`,
            'content': currentTranslation,
            'language': targetLang
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
            downloadLink.download = `${title}_${targetLang}.docx`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Error downloading translation. Please try again.');
    });
}
