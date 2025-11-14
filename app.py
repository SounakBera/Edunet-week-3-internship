import pandas as pd
from flask import Flask, request, jsonify, render_template_string
import random # <-- ADDED THIS IMPORT

# Initialize the Flask app
app = Flask(__name__)

# --- Load Data ---
# Load your EV data
try:
    df = pd.read_csv('cars_data_cleaned.csv')
    # Convert brand names to uppercase for easier matching
    df['Brand'] = df['Brand'].str.upper()
except FileNotFoundError:
    print("ERROR: cars_data_cleaned.csv not found.")
    df = pd.DataFrame() # Create empty dataframe to avoid errors

# --- Chatbot Logic (NOW MORE HUMAN-LIKE) ---
def process_query(query):
    """
    Processes a user's text query and returns a string response.
    """
    query = query.lower().strip()

    if df.empty:
        return "Sorry, I can't access the car data at the moment."

    # --- NEW: Conversational Intents ---
    greetings = ["hi", "hello", "hey", "yo", "howdy"]
    if query in greetings:
        responses = [
            "Hi there! Ask me about the EV data.",
            "Hello! What EV info are you looking for?",
            "Hey! How can I help with the car data today?"
        ]
        return random.choice(responses)

    thanks_bye = ["thanks", "thank you", "bye", "goodbye", "ttyl", "cya"]
    if any(phrase in query for phrase in thanks_bye):
        responses = [
            "You're welcome! Happy to help.",
            "No problem! Have a great day.",
            "My pleasure! Let me know if you need anything else.",
            "Goodbye!"
        ]
        return random.choice(responses)

    help_identity = ["help", "what can you do", "who are you", "info"]
    if query in help_identity:
        return "I'm an EV chatbot! You can ask me questions like 'what's the fastest car?', 'cheapest car for TESLA', or 'tell me about PORSCHE'."

    # --- Standard Data Questions ---
    if query == "how many cars are there?":
        return f"There are {len(df)} car models in the dataset."

    elif query == "what brands are available?":
        brands = df['Brand'].unique()
        # Sort brands alphabetically for easier reading
        brands.sort()
        return f"Available brands: {', '.join(brands)}"

    # --- More flexible logic (from before) ---

    # Helper to find brand in query
    all_brands = list(df['Brand'].unique())
    
    def find_brand_in_query(q):
        for brand in all_brands:
            if brand.lower() in q:
                return brand
        # Check for the old "info on [Brand]" style as a fallback
        if q.startswith("info on "):
            brand_name_from_query = q[len("info on "):].upper()
            if brand_name_from_query in all_brands:
                return brand_name_from_query
        return None

    found_brand = find_brand_in_query(query)
    
    # Create a working DataFrame (df_context) that is filtered if a brand is found
    df_context = df
    context_text = "Overall"
    context_text_lower = "overall"
    
    if found_brand:
        df_context = df[df['Brand'] == found_brand]
        context_text = f"For {found_brand}"
        context_text_lower = f"for {found_brand}"
        if df_context.empty:
            return f"I found {found_brand} in your query, but I have no data for that brand."

    # --- Intent 1: Extremums (Max/Min) ---
    
    if ("longest" in query or "most" in query or "highest" in query) and "range" in query:
        car = df_context.loc[df_context['km_of_range'].idxmax()]
        responses = [
            f"{context_text}, the car with the longest range is the {car['Brand']} {car['Model']}, with {car['km_of_range']} km.",
            f"{context_text}, I found the {car['Brand']} {car['Model']} has the most range: {car['km_of_range']} km.",
            f"{context_text}, if you're looking for range, the {car['Brand']} {car['Model']} leads the pack at {car['km_of_range']} km."
        ]
        return random.choice(responses)

    if "cheapest" in query or "lowest price" in query:
        # Filter out cars with 0 value, as that's likely missing data
        non_zero_df = df_context[df_context['Estimated_US_Value'] > 0]
        if non_zero_df.empty:
            return f"Sorry, I couldn't find any cars with a valid price {context_text_lower}."
        car = non_zero_df.loc[non_zero_df['Estimated_US_Value'].idxmin()]
        responses = [
            f"{context_text}, the cheapest car (with a valid price) is the {car['Brand']} {car['Model']}, valued at ${car['Estimated_US_Value']:,.0f}.",
            f"{context_text}, the best value I see is the {car['Brand']} {car['Model']}, at ${car['Estimated_US_Value']:,.0f}.",
            f"{context_text}, the {car['Brand']} {car['Model']} is the most affordable at ${car['Estimated_US_Value']:,.0f}."
        ]
        return random.choice(responses)
    
    if ("fastest" in query or "quickest" in query) or ("0-100" in query):
        car = df_context.loc[df_context['0-100'].idxmin()]
        responses = [
            f"{context_text}, the quickest car (0-100 km/h) is the {car['Brand']} {car['Model']} at {car['0-100']} seconds.",
            f"{context_text}, for acceleration, nothing beats the {car['Brand']} {car['Model']} at {car['0-100']}s.",
            f"{context_text}, the {car['Brand']} {car['Model']} has the fastest 0-100 time: {car['0-100']}s."
        ]
        return random.choice(responses)

    if ("most" in query or "highest" in query) and "towing" in query:
        car = df_context.loc[df_context['Towing_capacity_in_kg'].idxmax()]
        responses = [
            f"{context_text}, the car with the most towing capacity is the {car['Brand']} {car['Model']}, at {car['Towing_capacity_in_kg']} kg.",
            f"{context_text}, if you need to tow, the {car['Brand']} {car['Model']} is your best bet at {car['Towing_capacity_in_kg']} kg."
        ]
        return random.choice(responses)

    # --- Intent 2: Brand Info (as a fallback if no extremum was asked) ---
    # This intent is *only* triggered if a brand was found but no extremum
    if found_brand:
        # 'found_brand' is already set, 'df_context' is already filtered
        avg_val = df_context['Estimated_US_Value'].mean()
        avg_range = df_context['km_of_range'].mean()
        return f"I found {len(df_context)} models for {found_brand}. On average, they cost ${avg_val:,.2f} and have a range of {avg_range:,.1f} km."

    # --- Fallback ---
    else:
        responses = [
            "Sorry, I'm not sure how to answer that. Try asking about 'fastest', 'cheapest', or 'range'.",
            "Hmm, I don't understand that. You can ask 'help' to see what I can do.",
            "I didn't quite get that. Try 'longest range', 'cheapest car for TESLA', or 'tell me about PORSCHE'."
        ]
        return random.choice(responses)

# --- API Endpoint (Same as before) ---
# This route is for the chatbot API
@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get('query')
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    bot_response = process_query(user_query)
    
    return jsonify({'response': bot_response})

# --- Web Page Route (NEW) ---
# This route serves the HTML page for the chat interface
@app.route('/')
def home():
    # We define the HTML, CSS, and JavaScript as one long string
    # This keeps everything in a single file
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-R-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EV Chatbot</title>
        <style>
            /* Basic styling for the chat interface */
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f4f7f6;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            #chat-container {
                width: 90%;
                max-width: 600px;
                height: 80vh;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            header {
                background-color: #007aff;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 12px 12px 0 0;
            }
            h1 {
                margin: 0;
                font-size: 1.5em;
            }
            #chat-window {
                flex-grow: 1;
                padding: 20px;
                overflow-y: auto; /* Allows scrolling */
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            /* Message bubbles */
            .message {
                padding: 12px 18px;
                border-radius: 20px;
                line-height: 1.5;
                max-width: 80%;
            }
            .user-message {
                background-color: #007aff;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
            }
            .bot-message {
                background-color: #e5e5ea;
                color: black;
                align-self: flex-start;
                border-bottom-left-radius: 5px;
            }
            #chat-form {
                display: flex;
                border-top: 1px solid #ddd;
                padding: 15px;
            }
            #chat-input {
                flex-grow: 1;
                border: 1px solid #ccc;
                border-radius: 20px;
                padding: 12px 15px;
                font-size: 1em;
                margin-right: 10px;
            }
            #chat-input:focus {
                outline: none;
                border-color: #007aff;
            }
            #send-button {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 1em;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            #send-button:hover {
                background-color: #005bb5;
            }
        </style>
    </head>
    <body>
        <div id="chat-container">
            <header>
                <h1>EV Data Chatbot</h1>
            </header>
            <div id="chat-window">
                <!-- Chat messages will be added here by JavaScript -->
                <div class="message bot-message">
                    Hi! I'm an EV chatbot. Ask me about the data. You can ask 'longest range', 'cheapest car', or 'info on [Brand]'.
                </div>
            </div>
            <form id="chat-form">
                <input type="text" id="chat-input" placeholder="Type your message..." autocomplete="off">
                <button type="submit" id="send-button">Send</button>
            </form>
        </div>

        <script>
            // JavaScript to handle the chat interaction
            const chatForm = document.getElementById('chat-form');
            const chatInput = document.getElementById('chat-input');
            const chatWindow = document.getElementById('chat-window');

            chatForm.addEventListener('submit', async (event) => {
                event.preventDefault(); // Stop the form from reloading the page

                const userQuery = chatInput.value.trim();
                if (userQuery === "") {
                    return; // Don't send empty messages
                }

                // 1. Display the user's message
                addMessageToWindow(userQuery, 'user');
                
                // Clear the input box
                chatInput.value = "";
                
                // 2. Send the message to the backend API
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ query: userQuery })
                    });

                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }

                    const data = await response.json();
                    
                    // 3. Display the bot's response
                    addMessageToWindow(data.response, 'bot');

                } catch (error) {
                    console.error('Error:', error);
                    addMessageToWindow('Sorry, something went wrong. Please try again.', 'bot');
                }
            });

            function addMessageToWindow(message, sender) {
                // Create a new message div
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                
                if (sender === 'user') {
                    messageDiv.classList.add('user-message');
                } else {
                    messageDiv.classList.add('bot-message');
                }

                messageDiv.textContent = message; // Set the text content
                
                // Add the message to the chat window
                chatWindow.appendChild(messageDiv);
                
                // Scroll to the bottom
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    # This sends the HTML string to the browser
    return render_template_string(html_template)

# --- Run the App (for Render) ---
if __name__ == '__main__':
    # This host and port are for local testing. Render will use Gunicorn.
    app.run(debug=False, host='0.0.0.0', port=5000)
