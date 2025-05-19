# WikiTruth

WikiTruth is a mobile-friendly Flask web application that enhances Wikipedia content with advanced features like translation, document generation, and a TikTok-like content discovery feed.

## Features

- **Multi-language Support**: Read Wikipedia articles in multiple languages and switch between them seamlessly
- **Translation**: Translate article sections or summaries to any supported language
- **Document Generation**: Download Wikipedia content as beautifully formatted DOCX files
- **WikiTok Feed**: Discover random Wikipedia articles in a TikTok-like feed experience
- **Social Sharing**: Share articles across multiple social media platforms
- **Mobile-Optimized**: Responsive design that works on all device sizes

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Libraries**:
  - BeautifulSoup4: For HTML parsing
  - Trafilatura: For web content extraction
  - python-docx: For document generation
  - Wikipedia-API: For accessing Wikipedia content

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Environment Variables

- No API keys are required to run the basic application
- The application will run on port 5000 by default

## Usage

### Basic Navigation

1. Enter a search term in the homepage
2. Click on an article to read it
3. Use the language selector to switch languages
4. Use the view mode toggle to switch between summary and full content views

### Translation

1. In article view, click on "Translate" next to any section
2. Select the target language in the dropdown
3. The translation will appear in a popup modal
4. Download the translation as a document if desired

### WikiTok Feed

1. Navigate to the WikiTok section
2. Select language preferences using the dropdown
3. Scroll through randomly selected articles
4. Click "Read More" to view the full article

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.