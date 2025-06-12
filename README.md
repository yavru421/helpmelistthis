# ListGenie: Effortless Selling Post Generator

ListGenie is a Streamlit app that uses AI to help you quickly create professional, compelling listings for your items. Upload an image, and ListGenie will extract a list of items, generate catchy titles, descriptions, and price suggestions, and help you craft the perfect selling post for marketplaces or social media.

## Features
- Upload an image and extract a list of items using Groq's vision models
- AI-generated titles, descriptions, and price suggestions for each item
- Download your listing as a CSV for easy import to marketplaces
- Instantly copy your listing text
- Dynamically enhance your post (make it more persuasive, urgent, or concise) with one click
- Choose your Groq API key, endpoint, and model in the sidebar
- **Chat with the model at any time to ask questions, clarify, or correct anything—before or after generating your listing**
- **Simple, step-by-step interface designed for everyone—no tech skills needed!**

## Demo
![screenshot](screenshot.png)

## Getting Started

### 1. Clone the repository
```sh
# Use the official repo and MAIN branch

git clone -b main https://github.com/yavru421/helpmelistthis.git
cd helpmelistthis
```

### 2. Install dependencies
```sh
pip install -r requirements.txt
```

### 3. Set your Groq API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Or enter your key in the sidebar at runtime.

### 4. Run the app
```sh
streamlit run app.py
```

## Deploy on Hugging Face Spaces
- Add your `requirements.txt` and `app.py` to the root of your repo.
- Push to a public GitHub repo.
- Create a new Space on Hugging Face, select Streamlit, and point to your repo.

## Requirements
See `requirements.txt` for all dependencies.

## License
MIT

---

**ListGenie** is built to help you sell more, faster. Contributions and feature requests are welcome!
