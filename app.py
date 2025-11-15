import streamlit as st
import pandas as pd
import joblib
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="EV App", page_icon="EV", layout="wide")

# Load the trained model
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl")
    except FileNotFoundError:
        st.error("Model file 'model.pkl' not found. Please ensure it's available.")
        return None

model = load_model()

# Load EV data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('cars_data_cleaned.csv')
        df['Brand'] = df['Brand'].str.upper()
        return df
    except FileNotFoundError:
        st.error("Data file 'cars_data_cleaned.csv' not found.")
        return pd.DataFrame()

df = load_data()

# Chatbot Logic
def process_query(query):
    query = query.lower().strip()
    if df.empty:
        return "Sorry, I can't access the car data at the moment."

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
        return ("I'm an EV chatbot! You can ask me questions like "
                "'what's the fastest car?', 'cheapest car for TESLA', "
                "'tell me about PORSCHE', 'highest towing capacity for FORD', "
                "'quickest 0-100 for BMW', or 'longest range overall'.")

    if query == "how many cars are there?":
        return f"There are {len(df)} car models in the dataset."

    elif query == "what brands are available?":
        brands = sorted(df['Brand'].unique())
        return f"Available brands: {', '.join(brands)}"

    all_brands = list(df['Brand'].unique())

    def find_brand_in_query(q):
        for brand in all_brands:
            if brand.lower() in q:
                return brand
        if q.startswith("info on "):
            brand_name = q[len("info on "):].upper()
            if brand_name in all_brands:
                return brand_name
        return None

    found_brand = find_brand_in_query(query)
    df_context = df
    context_text = "Overall"
    context_text_lower = "overall"

    if found_brand:
        df_context = df[df['Brand'] == found_brand]
        context_text = f"For {found_brand}"
        context_text_lower = f"for {found_brand}"

    if df_context.empty:
        return f"I found {found_brand} in your query, but I have no data for that brand."

    # Longest Range
    if ("longest" in query or "most" in query or "highest" in query) and "range" in query:
        car = df_context.loc[df_context['km_of_range'].idxmax()]
        responses = [
            f"{context_text}, the car with the longest range is the {car['Brand']} {car['Model']}, with {car['km_of_range']} km.",
            f"{context_text}, I found the {car['Brand']} {car['Model']} has the most range: {car['km_of_range']} km.",
            f"{context_text}, if you're looking for range, the {car['Brand']} {car['Model']} leads the pack at {car['km_of_range']} km."
        ]
        return random.choice(responses)

    # Cheapest Car
    if "cheapest" in query or "lowest price" in query:
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

    # Fastest 0-100
    if ("fastest" in query or "quickest" in query) or ("0-100" in query):
        car = df_context.loc[df_context['0-100'].idxmin()]
        responses = [
            f"{context_text}, the quickest car (0-100 km/h) is the {car['Brand']} {car['Model']} at {car['0-100']} seconds.",
            f"{context_text}, for acceleration, nothing beats the {car['Brand']} {car['Model']} at {car['0-100']}s.",
            f"{context_text}, the {car['Brand']} {car['Model']} has the fastest 0-100 time: {car['0-100']}s."
        ]
        return random.choice(responses)

    # Highest Towing
    if ("most" in query or "highest" in query) and "towing" in query:
        car = df_context.loc[df_context['Towing_capacity_in_kg'].idxmax()]
        responses = [
            f"{context_text}, the car with the most towing capacity is the {car['Brand']} {car['Model']}, at {car['Towing_capacity_in_kg']} kg.",
            f"{context_text}, if you need to tow, the {car['Brand']} {car['Model']} is your best bet at {car['Towing_capacity_in_kg']} kg."
        ]
        return random.choice(responses)

    # Brand Summary
    if found_brand:
        avg_val = df_context['Estimated_US_Value'].mean()
        avg_range = df_context['km_of_range'].mean()
        return f"I found {len(df_context)} models for {found_brand}. On average, they cost ${avg_val:,.2f} and have a range of {avg_range:,.1f} km."

    # Fallback
    responses = [
        "Sorry, I'm not sure how to answer that. Try asking about 'fastest', 'cheapest', or 'range'.",
        "Hmm, I don't understand that. You can ask 'help' to see what I can do.",
        "I didn't quite get that. Try 'longest range', 'cheapest car for TESLA', or 'tell me about PORSCHE'."
    ]
    return random.choice(responses)


# === MAIN APP ===
st.sidebar.title("EV App Navigation")
page = st.sidebar.selectbox("Choose a feature", ["EV Price Predictor", "EV Data Chatbot", "Data Visualization"])

# ==============================
# 1. EV Price Predictor
# ==============================
if page == "EV Price Predictor":
    st.image(
        "https://cdn.pixabay.com/photo/2022/01/25/19/12/electric-car-6968348_1280.jpg",
        use_container_width=True
    )
    st.title("EV Price Predictor")
    st.markdown("### Adjust the specifications to estimate the car's value.")

    col1, col2 = st.columns(2)
    with col1:
        battery = st.number_input("Battery Capacity (kWh)", min_value=20.0, max_value=150.0, value=75.0)
        accel = st.number_input("0-100 km/h (sec)", min_value=2.0, max_value=20.0, value=6.0)
        seats = st.slider("Number of Seats", 2, 8, 5)
    with col2:
        top_speed = st.number_input("Top Speed (km/h)", min_value=100, max_value=400, value=200)
        range_km = st.number_input("Range (km)", min_value=100, max_value=800, value=400)
        efficiency = st.number_input("Efficiency (Wh/km)", min_value=100, max_value=300, value=180)

    if st.button("Predict Price"):
        if model:
            input_data = pd.DataFrame({
                'Battery': [battery],
                '0-100': [accel],
                'Top_Speed': [top_speed],
                'Range': [range_km],
                'Efficiency': [efficiency],
                'Number_of_seats': [seats]
            })
            prediction = model.predict(input_data)[0]
            st.success(f"Estimated Price: **${prediction:,.2f}**")
        else:
            st.error("Model could not be loaded.")

# ==============================
# 2. EV Data Chatbot
# ==============================
elif page == "EV Data Chatbot":
    st.title("EV Data Chatbot")
    st.markdown("Ask me about the EV data! Examples: 'longest range', 'cheapest car for TESLA', "
                "'tell me about PORSCHE', 'highest towing capacity for FORD', "
                "'quickest 0-100 for BMW', or 'longest range overall'.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hi! I'm an EV chatbot. Ask me about the data. "
                       "Try 'longest range', 'cheapest car', 'info on [Brand]', "
                       "'highest towing capacity for FORD', or 'quickest 0-100 for BMW'."
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = process_query(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ==============================
# 3. Data Visualization
# ==============================
elif page == "Data Visualization":
    st.title("EV Data Visualization")
    st.markdown("Explore interactive charts with **real-time filters**.")

    if df.empty:
        st.warning("No data available for visualization.")
    else:
        viz_df = df.copy()
        viz_df = viz_df[viz_df['Estimated_US_Value'] > 0]

        # Sidebar Filters
        st.sidebar.header("Interactive Filters")

        all_brands = sorted(viz_df['Brand'].unique())
        selected_brands = st.sidebar.multiselect(
            "Select Brands", options=all_brands, default=all_brands[:5]
        )

        price_min, price_max = int(viz_df['Estimated_US_Value'].min()), int(viz_df['Estimated_US_Value'].max())
        selected_price = st.sidebar.slider(
            "Price Range (USD)", min_value=price_min, max_value=price_max,
            value=(price_min, price_max), step=1000, format="$%d"
        )

        range_min, range_max = int(viz_df['km_of_range'].min()), int(viz_df['km_of_range'].max())
        selected_range = st.sidebar.slider(
            "Range (km)", min_value=range_min, max_value=range_max,
            value=(range_min, range_max), step=10
        )

        battery_min, battery_max = float(viz_df['Battery'].min()), float(viz_df['Battery'].max())
        selected_battery = st.sidebar.slider(
            "Battery Capacity (kWh)", min_value=battery_min, max_value=battery_max,
            value=(battery_min, battery_max), step=0.1
        )

        selected_seats = st.sidebar.multiselect(
            "Number of Seats",
            options=sorted(viz_df['Number_of_seats'].unique()),
            default=sorted(viz_df['Number_of_seats'].unique())
        )

        # Apply Filters
        filtered_df = viz_df[
            (viz_df['Brand'].isin(selected_brands)) &
            (viz_df['Estimated_US_Value'].between(selected_price[0], selected_price[1])) &
            (viz_df['km_of_range'].between(selected_range[0], selected_range[1])) &
            (viz_df['Battery'].between(selected_battery[0], selected_battery[1])) &
            (viz_df['Number_of_seats'].isin(selected_seats))
        ]

        if filtered_df.empty:
            st.warning("No cars match the selected filters. Try adjusting them.")
        else:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Price vs Range", "Brand Distribution", "Performance", "Efficiency", "Top Models"
            ])

            with tab1:
                st.subheader("Price vs Range (Filtered)")
                fig = px.scatter(
                    filtered_df, x='km_of_range', y='Estimated_US_Value',
                    color='Brand', size='Battery',
                    hover_data=['Model', 'Top_Speed', '0-100', 'Efficiency'],
                    labels={'km_of_range': 'Range (km)', 'Estimated_US_Value': 'Price (USD)'},
                    title="Price vs Range"
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Models per Brand (Filtered)")
                brand_counts = filtered_df['Brand'].value_counts().reset_index()
                brand_counts.columns = ['Brand', 'Count']
                fig = px.bar(
                    brand_counts, x='Brand', y='Count', color='Count',
                    color_continuous_scale='Viridis', title="EV Models per Brand"
                )
                fig.update_layout(xaxis={'categoryorder': 'total descending'})
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.subheader("Acceleration vs Top Speed")
                fig = px.scatter(
                    filtered_df, x='0-100', y='Top_Speed',
                    color='Brand', size='Estimated_US_Value',
                    hover_data=['Model', 'km_of_range'],
                    labels={'0-100': '0-100 km/h (sec)', 'Top_Speed': 'Top Speed (km/h)'},
                    title="Performance Comparison"
                )
                fig.update_xaxes(autorange="reversed")
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)

            with tab4:
                st.subheader("Average Efficiency by Brand")
                eff_df = filtered_df.groupby('Brand')['Efficiency'].mean().reset_index().sort_values('Efficiency')
                fig = px.bar(
                    eff_df, x='Brand', y='Efficiency', color='Efficiency',
                    color_continuous_scale='RdYlGn_r',
                    title="Efficiency (Wh/km) – Lower is Better"
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab5:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Top 10 Most Expensive")
                    top10 = filtered_df.nlargest(10, 'Estimated_US_Value')[
                        ['Brand', 'Model', 'Estimated_US_Value', 'km_of_range']
                    ].copy()
                    top10['Estimated_US_Value'] = top10['Estimated_US_Value'].map('${:,.0f}'.format)
                    st.dataframe(top10.reset_index(drop=True), use_container_width=True)

                with col2:
                    st.subheader("Top 10 Longest Range")
                    range10 = filtered_df.nlargest(10, 'km_of_range')[
                        ['Brand', 'Model', 'km_of_range', 'Estimated_US_Value']
                    ].copy()
                    range10['Estimated_US_Value'] = range10['Estimated_US_Value'].map('${:,.0f}'.format)
                    st.dataframe(range10.reset_index(drop=True), use_container_width=True)

            # Summary Metrics
            st.markdown("---")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Filtered Models", len(filtered_df))
            with col2:
                st.metric("Avg Price", f"${filtered_df['Estimated_US_Value'].mean():,.0f}")
            with col3:
                st.metric("Avg Range", f"{filtered_df['km_of_range'].mean():.0f} km")
            with col4:
                st.metric("Avg Efficiency", f"{filtered_df['Efficiency'].mean():.0f} Wh/km")
            with col5:
                st.metric("Avg Battery", f"{filtered_df['Battery'].mean():.1f} kWh")
