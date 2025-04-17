# Bon AIppétit Backend 🍳

The backend service for Bon AIppétit, a web application that transforms recipe URLs into beautiful, easy-to-follow cuisinograms.
You can find the frontend repository [here](https://github.com/rexgraystone/bon-aippetit).
## ✨ Features

- Recipe URL processing
- Integration with Google Gemini API
- RESTful API endpoints
- Secure API key management

## 🛠️ Tech Stack

- Python
- Flask
- Google Gemini API
- RESTful architecture

## 📦 Installation

1. Clone the repositories

```bash
git clone https://github.com/rexgraystone/bon-aippetit.git
git clone https://github.com/rexgraystone/bon-aippetit-backend.git
cd bon-aippetit-backend
```

1. Create and activate a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔧 Configuration

1. Create a `.env` file in the root directory
2. Add your Google Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

## 🏃‍♂️ Running Locally

1. Start the Flask server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📚 API Documentation

### Endpoints

- `POST /api/gemini`
  - Accepts a recipe URL
  - Returns a processed recipe into a cuisinogram

## 🔒 Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `FLASK_ENV`: Development or Production environment
- `PORT`: Port number for the server (default: 5000)

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
