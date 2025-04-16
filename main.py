from flask import Flask, request, jsonify, make_response
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import re
from bs4 import BeautifulSoup
from flask_cors import CORS
import sys

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Check for API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables")
    sys.exit(1)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/*": {
    "origins": ["*"],  # Allow all origins for Vercel deployment
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})

# Configure Gemini API
try:
    print("Configuring Gemini API...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

@app.route('/')
def home():
    return "Bon AIppetit API is running!"

@app.route('/api/test')
def test():
    return jsonify({"status": "API is working"})

def scrape(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # scrape all text, excluding script and style elements
        text_parts = [
            element.get_text(separator=' ', strip=True)
            for element in soup.find_all(string=True)
            if element.parent.name not in ['script', 'style']
        ]
        return " ".join(text_parts)

    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"
    except Exception as e:
        return f"Error parsing website: {e}"

def clean_mermaid_response(response_object):
    """
    Extracts and cleans the Mermaid code, ingredients, and recipe name from the API response.

    Args:
        response_object (google.generativeai.types.generation_types.GenerateContentResponse): The response object from the API.

    Returns:
        tuple: A tuple containing the recipe name, ingredients string, and the cleaned Mermaid code, or (None, None, None) if not found.
    """
    response_text = str(response_object.text)  # convert to string

    # Regular expression to find Mermaid code blocks
    mermaid_match = re.search(r"```mermaid\n(.*?)\n```", response_text, re.DOTALL)

    # Regular expression to find Ingredients
    ingredients_match = re.search(r"Ingredients:\n(.*?)\nSteps:", response_text, re.DOTALL)

    # Regular expression to find Recipe Name
    recipe_name_match = re.search(r"Recipe Name:\s*(.*?)\n", response_text)

    recipe_name = recipe_name_match.group(1).strip() if recipe_name_match else None

    if mermaid_match:
        mermaid_code = mermaid_match.group(1).strip()
        cleaned_code = mermaid_code.replace(";", "\n").replace("\n\n", "\n")

        if ingredients_match:
            ingredients = ingredients_match.group(1).strip()
            ingredients_steps = f"Ingredients:\n{ingredients}\n\nSteps:"
            return recipe_name, ingredients_steps, cleaned_code
        else:
            return recipe_name, "Steps:", cleaned_code

    elif ingredients_match:
        ingredients = ingredients_match.group(1).strip()
        ingredients_steps = f"Ingredients:\n{ingredients}"
        return recipe_name, ingredients_steps, None

    else:
        return None, None, None

@app.route('/api/gemini', methods=['POST', 'OPTIONS'])
def gemini_api():
    print(f"Received request method: {request.method}")
    print(f"Received headers: {request.headers}")
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        user_input = data.get('userInput')
        website_url = data.get('websiteUrl') #get the website URL from the request

        if not user_input and not website_url:
            return jsonify({'error': 'No user input or website URL provided'}), 400

        prompt_input = "" #initilize the prompt input

        if website_url:
            website_content = scrape(website_url)
            if "Error" in website_content:
                return jsonify({'error': website_content}), 500
            prompt_input += f"Website Content: {website_content}\n\n"

        if user_input:
            prompt_input += f"User Input: {user_input}\n\n"

        prompt = f"""
        Your name is Bon AIppetit. You are a helpful AI assistant that assists users in cooking recipes.
        You are given a recipe as an input. Use only Imperial measurements, do not use metric measurements in parenthesis.
        Generate a Mermaid flowchart that:
        1. Shows each step of the recipe as a node
        2. Connects steps with arrows that display both temperature and time information
        3. Labels each arrow with the appropriate cooking temperature whenever temperature is mentioned using the syntax "A-->|Temperature: 450°F| B[steps...]", never use "A-->B|Temperature: 450°F| B[steps...]"
        4. Labels each arrow with cooking/preparation time whenever time is mentioned using the syntax "A-->|15-20 minutes| B", always use the word "minutes", never use "A-->B|15-20 minutes| B"
        5. Combines both temperature and time on the same arrow when both apply using the syntax "A-->|Temperature: 450°F for 15-20 minutes| B", never use "A-->B|Temperature: 450°F| B"
        6. Includes all heating, baking, cooking temperatures, and timing information directly on the arrows between relevant steps
        7. Uses Imperial measurements exclusively throughout the diagram
        8. Keep the flowchart as small and simple as possible, do not include any additional text or explanation inside parentheses like (optional)
        9. Use only Top-Down flowchart direction
        10. Do not include any optional steps within parentheses
        11. The name of the recipe should be the name of the dish, do not include any adjectives

        Generate the output in the below syntax:
        Recipe Name: 
        Name of the recipe
        
        Ingredients:
        - Ingredient 1 measurement
        - Ingredient 2 measurement
        - Ingredient 3 measurement

        Steps:
        mermaid code

        {prompt_input}

        Response:
        """
        response = model.generate_content(prompt)
        print("Raw API response: \n", response.text)
        recipe_name, ingredients, steps = clean_mermaid_response(response)

        if recipe_name and ingredients and steps:
            print(steps)
            return jsonify([recipe_name, ingredients, steps])
        elif recipe_name and ingredients:
            print("Only Recipe Name and Ingredients found.")
            return jsonify([recipe_name, ingredients])
        elif recipe_name and steps:
            print("Only Recipe Name and Steps found.")
            return jsonify([recipe_name, steps])
        elif ingredients and steps:
            print("Only Ingredients and Steps found.")
            return jsonify([ingredients, steps])
        elif ingredients:
            print("Only Ingredients found.")
            return jsonify(ingredients)
        elif steps:
            print("Only steps found.")
            return jsonify(steps)
        else:
            print("No recipe found.")
            return jsonify("No recipe found.")

    except Exception as e:
        print(f"Error in API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        host = '0.0.0.0'  # Listen on all interfaces
        port = int(os.environ.get('PORT', 8000))  # Use PORT from environment or default to 8000
        print(f"Starting Flask server on http://{host}:{port}")
        app.run(host=host, port=port, debug=False)  # Set debug to False for production
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

