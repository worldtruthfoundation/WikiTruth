# Deploying TruePedia to Streamlit Cloud

This guide will help you deploy the TruePedia application from your local PC to Streamlit Cloud so it's accessible online to anyone.

## Prerequisites

1. Make sure you have a [GitHub](https://github.com/) account
2. Create a [Streamlit Cloud](https://streamlit.io/cloud) account by signing in with your GitHub account

## Step 1: Set up a GitHub repository

1. Create a new repository on GitHub
2. Clone the repository to your local machine:
   ```
   git clone https://github.com/yourusername/yourrepository.git
   cd yourrepository
   ```

## Step 2: Copy TruePedia files to your local repository

1. Copy all these files from your Replit project to your local GitHub repository:
   - `main.py`
   - `wiki_utils.py`
   - `highlight_utils.py`
   - `.streamlit/config.toml` (make sure to maintain the folder structure)
   - `requirements.txt` (see step 3 for creating this file)

## Step 3: Create a requirements.txt file

Create a `requirements.txt` file in the root of your repository with the following content:

```
streamlit
wikipedia
wikipedia-api
translate
```

## Step 4: Push your code to GitHub

```
git add .
git commit -m "Add TruePedia application"
git push origin main
```

## Step 5: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Click on the "New app" button
3. Select your GitHub repository and branch (usually 'main')
4. Set the main file path to `main.py`
5. Click "Deploy!"

Your app will now be deployed to Streamlit Cloud and you'll get a public URL for your application.

## Step 6: Configure for local development (optional)

If you want to run the app locally on your PC:

1. Install Python 3.8 or higher
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   streamlit run main.py
   ```

## Data Storage Considerations

Note that the application stores highlights in a JSON file. When deployed to Streamlit Cloud:

1. The data will persist but may be cleared after periods of inactivity
2. You might want to implement a database solution (like SQLite, MongoDB Atlas, or Firebase) for more robust storage in a production environment

## Updating Your Deployed App

When you make changes to your code locally:

1. Push changes to GitHub:
   ```
   git add .
   git commit -m "Update app"
   git push origin main
   ```
2. Streamlit Cloud will automatically deploy the new version of your app