import pandas as pd
from flask import Flask, request, jsonify, render_template_string

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

# --- Chatbot Logic (Same as before) ---
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
        # Sort brands alphabetically for easier reading
        brands.sort()
        return f"Available brands: {', '.join(brands)}"

    elif query.startswith("info on "):
        # Find the brand name, even if it's multiple words
        brand_name = query[len("info on "):].upper() 
        
        brand_data = df[df['Brand'] == brand_name]
        
        if brand_data.empty:
            return f"Sorry, I have no information on the brand '{brand_name}'."
        else:
            avg_val = brand_data['Estimated_US_Value'].mean()
            avg_range = brand_data['km_of_range'].mean()
            return f"I found {len(brand_data)} models for {brand_name}. Average US value: ${avg_val:,.2f}. Average range: {avg_range:,.1f} km."

    elif query == "longest range":
        car = df.loc[df['km_of_range'].idxmax()]
        return f"The car with the longest range is the {car['Brand']} {car['Model']}, with {car['km_of_range']} km."

    elif query == "cheapest car":
        # Filter out cars with 0 value, as that's likely missing data
        non_zero_df = df[df['Estimated_US_Value'] > 0]
        if non_zero_df.empty:
            return "Sorry, I couldn't find any cars with a valid price."
        car = non_zero_df.loc[non_zero_df['Estimated_US_Value'].idxmin()]
        return f"The cheapest car (with a valid price) is the {car['Brand']} {car['Model']}, valued at ${car['Estimated_US_Value']:,.0f}."

    elif query == "fastest car": # Based on 0-100 time
        car = df.loc[df['0-100'].idxmin()]
        return f"The quickest car (0-100 km/h) is the {car['Brand']} {car['Model']} at {car['0-100']} seconds."

    elif query == "most towing capacity":
        car = df.loc[df['Towing_capacity_in_kg'].idxmax()]
        return f"The car with the most towing capacity is the {car['Brand']} {car['Model']}, at {car['Towing_capacity_in_kg']} kg."

    else:
        return "Sorry, I don't understand that. Try 'longest range', 'cheapest car', or 'info on [Brand]'."

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
