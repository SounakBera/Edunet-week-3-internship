import pandas as pd
from flask import Flask, request, jsonify

# Initialize the Flask app
app = Flask(__name__)

# Load your EV data
try:
    df = pd.read_csv('cars_data_cleaned.csv')
    # Convert brand names to uppercase for easier matching
    df['Brand'] = df['Brand'].str.upper()
except FileNotFoundError:
    print("ERROR: cars_data_cleaned.csv not found.")
    df = pd.DataFrame() # Create empty dataframe to avoid errors

def process_query(query):
    """
    Processes a user's text query and returns a string response.
    """
    query = query.lower().strip()

    if df.empty:
        return "Sorry, I can't access the car data at the moment."

    if query in ["hi", "hello", "hey"]:
        return "Hi! I'm an EV chatbot. Ask me about the data. You can ask 'longest range', 'cheapest car', or 'info on [Brand]'."

    elif query == "how many cars are there?":
        return f"There are {len(df)} car models in the dataset."

    elif query == "what brands are available?":
        brands = df['Brand'].unique()
        return f"Available brands: {', '.join(brands)}"

    elif query.startswith("info on "):
        brand_name = query.replace("info on ", "").upper()
        brand_data = df[df['Brand'] == brand_name]
        
        if brand_data.empty:
            return f"Sorry, I have no information on the brand '{brand_name}'."
        else:
            return f"I found {len(brand_data)} models for {brand_name}. The average US value is ${brand_data['Estimated_US_Value'].mean():,.2f}."

    elif query == "longest range":
        car = df.loc[df['km_of_range'].idxmax()]
        return f"The car with the longest range is the {car['Brand']} {car['Model']}, with {car['km_of_range']} km."

    elif query == "cheapest car":
        car = df.loc[df['Estimated_US_Value'].idxmin()]
        return f"The cheapest car is the {car['Brand']} {car['Model']}, valued at ${car['Estimated_US_Value']:,.0f}."

    elif query == "fastest car": # Based on 0-100 time
        car = df.loc[df['0-100'].idxmin()]
        return f"The quickest car (0-100 km/h) is the {car['Brand']} {car['Model']} at {car['0-100']} seconds."

    elif query == "most towing capacity":
        car = df.loc[df['Towing_capacity_in_kg'].idxmax()]
        return f"The car with the most towing capacity is the {car['Brand']} {car['Model']}, at {car['Towing_capacity_in_kg']} kg."

    else:
        return "Sorry, I don't understand that. Try 'longest range', 'cheapest car', or 'info on [Brand]'."

# This route is for the chatbot API
@app.route('/chat', methods=['POST'])
def chat():
    # Get the user's query from the JSON request
    user_query = request.json.get('query')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Process the query and get a response
    bot_response = process_query(user_query)
    
    # Return the response as JSON
    return jsonify({'response': bot_response})

# A simple home page to show the server is running
@app.route('/')
def home():
    return "EV Chatbot API is running. Use the /chat endpoint to interact."

# This allows the app to be run by Gunicorn (for Render)
if __name__ == '__main__':
    app.run(debug=False)
