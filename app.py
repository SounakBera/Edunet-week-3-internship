import streamlit as st
import pandas as pd
import joblib
import random
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="EV App", page_icon="EV", layout="wide")

# Load model
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl")
    except FileNotFoundError:
        st.error("Model file 'model.pkl' not found.")
        return None

model = load_model()

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('cars_data_cleaned.csv')
        df['Brand'] = df['Brand'].str.upper()
        df['Model'] = df['Model'].str.strip()
        return df
    except FileNotFoundError:
        st.error("Data file 'cars_data_cleaned.csv' not found.")
        return pd.DataFrame()

df = load_data()

# Normalize model names for search
df['Model_Key'] = df['Model'].str.lower().str.replace(r'\s+', ' ', regex=True)

# Chatbot Logic - Enhanced
def process_query(query):
    if df.empty:
        return "Sorry, I can't access the car data right now."

    q = query.lower().strip()

    # Greetings
    if any(g in q for g in ["hi", "hello", "hey", "yo", "howdy"]):
        return random.choice([
            "Hey there! Ready to explore EVs?",
            "Hi! Ask me about range, speed, price, or compare cars!",
            "Hello! What EV are you curious about today?"
        ])

    # Help / Info
    if any(h in q for h in ["help", "what can you", "who are you", "info"]):
        return ("I'm your EV assistant! I can:\n"
                "• Find **fastest**, **cheapest**, **longest range**\n"
                "• Compare **two cars** (e.g., 'compare Tesla Model 3 vs BMW i4')\n"
                "• Show **summary** of any car (e.g., 'tell me about Lucid Air')\n"
                "• Answer by **brand** (e.g., 'best Tesla for towing')\n"
                "• Say **'brands'** to list all")

    if "thanks" in q or "thank you" in q or "bye" in q:
        return random.choice([
            "You're welcome! Charge on!",
            "Happy to help! Come back anytime.",
            "See you next time!"
        ])

    # Brand list
    if "brand" in q and ("list" in q or "available" in q or "all" in q):
        brands = sorted(df['Brand'].unique())
        return f"Available brands: **{', '.join(brands)}**"

    # How many cars?
    if "how many" in q and "car" in q:
        return f"There are **{len(df)} EV models** in the database."

    # Find brand
    all_brands = list(df['Brand'].unique())
    found_brand = None
    for b in all_brands:
        if b.lower() in q:
            found_brand = b
            break

    df_context = df[df['Brand'] == found_brand] if found_brand else df
    context = f"For **{found_brand}**" if found_brand else "Overall"

    # === COMPARISON ===
    if "compare" in q and "vs" in q:
        parts = q.replace("compare", "").replace("vs", "|").split("|")
        if len(parts) < 2:
            return "Please say: **compare [Car 1] vs [Car 2]**"
        car1_query = parts[0].strip()
        car2_query = parts[1].strip()

        def find_car(query):
            q_key = query.lower().replace(" ", "")
            matches = df[df['Model_Key'].str.contains(q_key, na=False)]
            return matches.iloc[0] if not matches.empty else None

        car1 = find_car(car1_query)
        car2 = find_car(car2_query)

        if not car1 or not car2:
            return "I couldn't find one or both cars. Try full model names like **Tesla Model 3** or **BMW i4**."

        def format_car(c):
            return (f"**{c['Brand']} {c['Model']}**\n"
                    f"💰 Price: `${c['Estimated_US_Value']:,.0f}`\n"
                    f"🔋 Range: {int(c['km_of_range'])} km\n"
                    f"⚡ 0-100: {c['0-100']} sec\n"
                    f"🔝 Top Speed: {int(c['Top_Speed'])} km/h\n"
                    f"🪫 Battery: {c['Battery']:.1f} kWh\n"
                    f"💺 Seats: {int(c['Number_of_seats'])}\n"
                    f"🚛 Towing: {int(c['Towing_capacity_in_kg'])} kg")

        return f"### Car Comparison\n\n**{car1['Brand']} {car1['Model']}** vs **{car2['Brand']} {car2['Model']}**\n\n" \
               f"{format_car(car1)}\n\n**VS**\n\n{format_car(car2)}"

    # === SUMMARY OF A CAR ===
    if any(x in q for x in ["tell me about", "info on", "summary", "details"]):
        model_query = q
        for prefix in ["tell me about ", "info on ", "summary of ", "details of "]:
            if q.startswith(prefix):
                model_query = q[len(prefix):].strip()
                break

        q_key = model_query.lower().replace(" ", "")
        matches = df[df['Model_Key'].str.contains(q_key, na=False)]
        if matches.empty:
            return f"Couldn't find a car matching **{model_query}**. Try a full model name."

        car = matches.iloc[0]
        return (f"### {car['Brand']} {car['Model']}\n\n"
                f"💰 **Price**: `${car['Estimated_US_Value']:,.0f}`\n"
                f"🔋 **Range**: {int(car['km_of_range'])} km\n"
                f"⚡ **0-100 km/h**: {car['0-100']} sec\n"
                f"🔝 **Top Speed**: {int(car['Top_Speed'])} km/h\n"
                f"🪫 **Battery**: {car['Battery']:.1f} kWh\n"
                f"⚡ **Efficiency**: {int(car['Efficiency'])} Wh/km\n"
                f"💺 **Seats**: {int(car['Number_of_seats'])}\n"
                f"🚛 **Towing**: {int(car['Towing_capacity_in_kg'])} kg")

    # === EXTREME QUERIES ===
    if ("longest" in q or "most" in q) and "range" in q:
        car = df_context.loc[df_context['km_of_range'].idxmax()]
        return random.choice([
            f"{context}, the **{car['Brand']} {car['Model']}** has the longest range: **{car['km_of_range']} km**.",
            f"Top range {context.lower()}: **{car['Brand']} {car['Model']}** — {car['km_of_range']} km!"
        ])

    if "cheapest" in q or "lowest price" in q:
        valid = df_context[df_context['Estimated_US_Value'] > 0]
        if valid.empty:
            return f"No priced cars found {context.lower()}."
        car = valid.loc[valid['Estimated_US_Value'].idxmin()]
        return random.choice([
            f"{context}, the cheapest is **{car['Brand']} {car['Model']}** at **${car['Estimated_US_Value']:,.0f}**.",
            f"Best deal {context.lower()}: **{car['Brand']} {car['Model']}** — `${car['Estimated_US_Value']:,.0f}`"
        ])

    if ("fastest" in q or "quickest" in q) or "0-100" in q:
        car = df_context.loc[df_context['0-100'].idxmin()]
        return random.choice([
            f"{context}, the fastest 0-100 is **{car['Brand']} {car['Model']}** in **{car['0-100']} sec**.",
            f"Quickest acceleration {context.lower()}: **{car['Brand']} {car['Model']}** — {car['0-100']}s!"
        ])

    if ("towing" in q or "tow" in q) and ("most" in q or "highest" in q):
        car = df_context.loc[df_context['Towing_capacity_in_kg'].idxmax()]
        return f"{context}, the **{car['Brand']} {car['Model']}** tows the most: **{car['Towing_capacity_in_kg']} kg**."

    # Brand summary
    if found_brand:
        count = len(df_context)
        avg_price = df_context['Estimated_US_Value'].mean()
        avg_range = df_context['km_of_range'].mean()
        return (f"**{found_brand}** has **{count} models**.\n"
                f"Average price: **${avg_price:,.0f}**\n"
                f"Average range: **{avg_range:.0f} km**")

    # Fallback
    return random.choice([
        "I didn't catch that. Try: **compare A vs B**, **tell me about [car]**, or **longest range**.",
        "Hmm, try asking about **range**, **price**, **speed**, or **compare two cars**.",
        "You can ask me to **compare cars**, give **summaries**, or find **best in class**!"
    ])


# === MAIN APP ===
st.sidebar.title("EV App Navigation")
page = st.sidebar.selectbox("Choose a feature", [
    "EV Price Predictor",
    "EV Data Chatbot",
    "Data Visualization"
])

# ==============================
# 1. EV Price Predictor
# ==============================
if page == "EV Price Predictor":
    st.image("https://cdn.pixabay.com/photo/2022/01/25/19/12/electric-car-6968348_1280.jpg",
             use_container_width=True)
    st.title("EV Price Predictor")
    st.markdown("### Tune specs → Get instant price estimate")

    col1, col2 = st.columns(2)
    with col1:
        battery = st.number_input("Battery (kWh)", 20.0, 150.0, 75.0)
        accel = st.number_input("0-100 km/h (sec)", 2.0, 20.0, 6.0)
        seats = st.slider("Seats", 2, 8, 5)
    with col2:
        top_speed = st.number_input("Top Speed (km/h)", 100, 400, 200)
        range_km = st.number_input("Range (km)", 100, 800, 400)
        efficiency = st.number_input("Efficiency (Wh/km)", 100, 300, 180)

    if st.button("Predict Price", type="primary"):
        if model:
            input_df = pd.DataFrame({
                'Battery': [battery], '0-100': [accel], 'Top_Speed': [top_speed],
                'Range': [range_km], 'Efficiency': [efficiency], 'Number_of_seats': [seats]
            })
            pred = model.predict(input_df)[0]
            st.success(f"### Estimated Price: **${pred:,.0f}**")
            st.balloons()
        else:
            st.error("Model not loaded.")

# ==============================
# 2. EV Data Chatbot (Enhanced)
# ==============================
elif page == "EV Data Chatbot":
    st.title("EV Chatbot")
    st.markdown("Ask anything! Try: **compare Tesla Model Y vs Rivian R1S**, **tell me about Lucid Air**, or **cheapest BMW**")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hi! I'm your EV expert. Try:\n"
                       "• **compare Model 3 vs i4**\n"
                       "• **tell me about Cybertruck**\n"
                       "• **longest range Porsche**\n"
                       "• **cheapest car**"
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about EVs..."):
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
    st.title("EV Data Explorer")
    st.markdown("Interactive charts with **live filters**")

    if df.empty:
        st.warning("No data loaded.")
    else:
        viz_df = df[df['Estimated_US_Value'] > 0].copy()

        st.sidebar.header("Filters")
        brands = sorted(viz_df['Brand'].unique())
        sel_brands = st.sidebar.multiselect("Brands", brands, default=brands[:5])

        pmin, pmax = int(viz_df['Estimated_US_Value'].min()), int(viz_df['Estimated_US_Value'].max())
        sel_price = st.sidebar.slider("Price", pmin, pmax, (pmin, pmax), step=1000, format="$%d")

        rmin, rmax = int(viz_df['km_of_range'].min()), int(viz_df['km_of_range'].max())
        sel_range = st.sidebar.slider("Range (km)", rmin, rmax, (rmin, rmax), step=10)

        bmin, bmax = float(viz_df['Battery'].min()), float(viz_df['Battery'].max())
        sel_battery = st.sidebar.slider("Battery (kWh)", bmin, bmax, (bmin, bmax), step=0.1)

        sel_seats = st.sidebar.multiselect("Seats", sorted(viz_df['Number_of_seats'].unique()),
                                           default=sorted(viz_df['Number_of_seats'].unique()))

        filtered = viz_df[
            viz_df['Brand'].isin(sel_brands) &
            viz_df['Estimated_US_Value'].between(*sel_price) &
            viz_df['km_of_range'].between(*sel_range) &
            viz_df['Battery'].between(*sel_battery) &
            viz_df['Number_of_seats'].isin(sel_seats)
        ]

        if filtered.empty:
            st.warning("No cars match filters.")
        else:
            t1, t2, t3, t4, t5 = st.tabs(["Price vs Range", "Brands", "Performance", "Efficiency", "Top 10"])

            with t1:
                fig = px.scatter(filtered, x='km_of_range', y='Estimated_US_Value',
                                 color='Brand', size='Battery', hover_data=['Model'],
                                 labels={'km_of_range': 'Range (km)', 'Estimated_US_Value': 'Price'})
                st.plotly_chart(fig, use_container_width=True)

            with t2:
                counts = filtered['Brand'].value_counts().reset_index()
                fig = px.bar(counts, x='Brand', y='count', color='count', title="Models per Brand")
                st.plotly_chart(fig, use_container_width=True)

            with t3:
                fig = px.scatter(filtered, x='0-100', y='Top_Speed', color='Brand', size='Estimated_US_Value',
                                 hover_data=['Model'], labels={'0-100': '0-100 (sec)'})
                fig.update_xaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

            with t4:
                eff = filtered.groupby('Brand')['Efficiency'].mean().sort_values().reset_index()
                fig = px.bar(eff, x='Brand', y='Efficiency', color='Efficiency',
                             color_continuous_scale='RdYlGn_r', title="Efficiency (Lower = Better)")
                st.plotly_chart(fig, use_container_width=True)

            with t5:
                c1, c2 = st.columns(2)
                with c1:
                    top_price = filtered.nlargest(10, 'Estimated_US_Value')[['Brand', 'Model', 'Estimated_US_Value']]
                    top_price['Estimated_US_Value'] = top_price['Estimated_US_Value'].map('${:,.0f}'.format)
                    st.subheader("Most Expensive")
                    st.dataframe(top_price, use_container_width=True)
                with c2:
                    top_range = filtered.nlargest(10, 'km_of_range')[['Brand', 'Model', 'km_of_range']]
                    st.subheader("Longest Range")
                    st.dataframe(top_range, use_container_width=True)

            # Summary
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Models", len(filtered))
            c2.metric("Avg Price", f"${filtered['Estimated_US_Value'].mean():,.0f}")
            c3.metric("Avg Range", f"{filtered['km_of_range'].mean():.0f} km")
            c4.metric("Avg Battery", f"{filtered['Battery'].mean():.1f} kWh")
