// Global variables
let shareUrl = window.location.href;

// Show share modal with correct URL
function showShareOptions() {
    // Set the URL to the current page URL
    document.getElementById('share-url').value = shareUrl;
    
    // Show the modal
    const shareModal = new bootstrap.Modal(document.getElementById('shareModal'));
    shareModal.show();
}

// Share on social media platforms
function shareOn(platform) {
    const url = encodeURIComponent(shareUrl);
    const title = encodeURIComponent('Check out WikiTruth!');
    
    // Define sharing URLs for different platforms
    const platforms = {
        reddit: `https://www.reddit.com/submit?url=${url}&title=${title}`,
        whatsapp: `https://api.whatsapp.com/send?text=${title}%20${url}`,
        telegram: `https://t.me/share/url?url=${url}&text=${title}`,
        x:        `https://twitter.com/intent/tweet?text=${title}%20${url}`,
        linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
        gmail: `https://mail.google.com/mail/?view=cm&su=${title}&body=${url}`
    };
    
    if (platforms[platform] === 'copy') {
        copyShareLink();
        alert('Link copied to clipboard! Instagram does not support direct sharing - please paste the link manually.');
    } else {
        // Open the share URL in a new window
        window.open(platforms[platform], '_blank');
    }
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('shareModal'));
    if (modal) modal.hide();
}

// Copy share link to clipboard
function copyShareLink() {
    const shareUrlInput = document.getElementById('share-url');
    shareUrlInput.select();
    shareUrlInput.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        // Copy the text inside the text field
        navigator.clipboard.writeText(shareUrlInput.value)
            .then(() => {
                // Show success feedback
                const copyButton = shareUrlInput.nextElementSibling;
                const originalText = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
                
                // Reset button text after 2 seconds
                setTimeout(() => {
                    copyButton.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Could not copy text: ', err);
                // Fallback to legacy approach
                document.execCommand('copy');
            });
    } catch (err) {
        console.error('Could not copy text: ', err);
        // Try the older method as fallback
        document.execCommand('copy');
    }
}

// Handle errors gracefully
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.message);
    // We could add more sophisticated error handling here
});

// Responsive design adjustments
function handleResponsiveAdjustments() {
    // Adjust UI based on screen size if needed
    const isMobile = window.innerWidth < 768;
    
    if (isMobile) {
        // Mobile-specific adjustments
    } else {
        // Desktop-specific adjustments
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Apply responsive adjustments
    handleResponsiveAdjustments();
    
    // Detect changes in screen size
    window.addEventListener('resize', handleResponsiveAdjustments);
    
    // Initialize any Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
