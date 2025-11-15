import streamlit as st
import pandas as pd
import joblib
import random
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# Page Configuration
# ==============================
st.set_page_config(page_title="EV App", page_icon="EV", layout="wide")

# ==============================
# Load Model
# ==============================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl")
    except FileNotFoundError:
        st.error("Model file 'model.pkl' not found.")
        return None

model = load_model()

# ==============================
# Load Data
# ==============================
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
if not df.empty:
    df['Model_Key'] = df['Model'].str.lower().str.replace(r'\s+', ' ', regex=True)

# ==============================
# Enhanced Chatbot Logic
# ==============================
def process_query(query):
    if df.empty:
        return "Sorry, I can't access the car data right now. Please check the data file."

    q = query.lower().strip()
    original_q = query.strip()

    # === GREETINGS ===
    if any(g in q for g in ["hi", "hello", "hey", "yo", "howdy", "greetings"]):
        return random.choice([
            "Hey there! Ready to dive into the world of EVs?",
            "Hi! I'm your EV guru. Ask me about **range**, **price**, **speed**, or **compare cars**!",
            "Hello! What EV are you dreaming about today?"
        ])

    # === HELP / INFO ===
    if any(h in q for h in ["help", "what can you", "who are you", "info", "what do you do"]):
        return (
            "I'm your **EV Assistant**! Here's what I can do:\n\n"
            "• **Compare cars**: `compare Tesla Model 3 vs BMW i4`\n"
            "• **Compare brands**: `compare Tesla vs BMW`\n"
            "• **Car summary**: `tell me about Lucid Air`\n"
            "• **Best in class**: `longest range`, `cheapest car`, `fastest 0-100`\n"
            "• **Brand stats**: `best Tesla for towing`, `cheapest Porsche`\n"
            "• **Dataset info**: `show summary`, `how many cars?`\n"
            "• **List brands**: `brands`\n\n"
            "Try any of these!"
        )

    # === THANKS / GOODBYE ===
    if any(t in q for t in ["thanks", "thank you", "thankyou", "bye", "goodbye", "see you"]):
        return random.choice([
            "You're welcome! Charge safe!",
            "Happy to help! Come back for more EV insights.",
            "See you next time! Keep it electric!"
        ])

    # === LIST ALL BRANDS ===
    if "brand" in q and any(x in q for x in ["list", "all", "available", "show"]):
        brands = sorted(df['Brand'].unique())
        return f"**Available Brands** ({len(brands)}):  \n`{', '.join(brands)}`"

    # === HOW MANY CARS? ===
    if "how many" in q and ("car" in q or "model" in q or "ev" in q):
        return f"There are **{len(df)} EV models** in the database from **{len(df['Brand'].unique())} brands**."

    # === DATASET SUMMARY ===
    if any(s in q for s in ["summary", "stats", "overview", "dataset", "data info"]):
        total = len(df)
        brands = df['Brand'].nunique()
        avg_price = df['Estimated_US_Value'].mean()
        avg_range = df['km_of_range'].mean()
        avg_battery = df['Battery'].mean()
        return (
            f"### EV Dataset Summary\n\n"
            f"**Total Models**: {total}\n"
            f"**Brands**: {brands}\n"
            f"**Avg Price**: `${avg_price:,.0f}`\n"
            f"**Avg Range**: {avg_range:.0f} km\n"
            f"**Avg Battery**: {avg_battery:.1f} kWh\n"
            f"**Price Range**: `${df['Estimated_US_Value'].min():,.0f}` → `${df['Estimated_US_Value'].max():,.0f}`\n"
            f"**Range Span**: {int(df['km_of_range'].min())} → {int(df['km_of_range'].max())} km"
        )

    # === BRAND DETECTION ===
    all_brands = [b.lower() for b in df['Brand'].unique()]
    found_brand = None
    for b in all_brands:
        if b in q:
            found_brand = b.title()
            break
    df_context = df[df['Brand'] == found_brand] if found_brand else df
    context = f"For **{found_brand}**" if found_brand else "Overall"

    # === BRAND-LEVEL COMPARISON: "compare Tesla vs BMW" ===
    if "compare" in q and "vs" in q and any(b in q for b in all_brands):
        parts = q.replace("compare", "").replace("vs", "|").split("|")
        brand_names = [p.strip().title() for p in parts if p.strip()]
        valid_brands = [b for b in brand_names if b in df['Brand'].unique()]
        
        if len(valid_brands) < 2:
            return "Please compare **two valid brands**, e.g., `compare Tesla vs BMW`"
        
        b1, b2 = valid_brands[0], valid_brands[1]
        df1 = df[df['Brand'] == b1]
        df2 = df[df['Brand'] == b2]

        def brand_stats(d):
            return {
                'Models': len(d),
                'Avg_Price': d['Estimated_US_Value'].mean(),
                'Avg_Range': d['km_of_range'].mean(),
                'Best_Range': d['km_of_range'].max(),
                'Cheapest': d['Estimated_US_Value'].min(),
                'Fastest': d['0-100'].min()
            }

        s1, s2 = brand_stats(df1), brand_stats(df2)

        return (
            f"### Brand Comparison: **{b1}** vs **{b2}**\n\n"
            f"**{b1}** ({s1['Models']} models)\n"
            f"• Avg Price: `${s1['Avg_Price']:,.0f}`\n"
            f"• Avg Range: {s1['Avg_Range']:.0f} km\n"
            f"• Longest Range: {s1['Best_Range']} km\n"
            f"• Cheapest: `${s1['Cheapest']:,.0f}`\n"
            f"• Fastest 0-100: {s1['Fastest']} sec\n\n"
            f"**{b2}** ({s2['Models']} models)\n"
            f"• Avg Price: `${s2['Avg_Price']:,.0f}`\n"
            f"• Avg Range: {s2['Avg_Range']:.0f} km\n"
            f"• Longest Range: {s2['Best_Range']} km\n"
            f"• Cheapest: `${s2['Cheapest']:,.0f}`\n"
            f"• Fastest 0-100: {s2['Fastest']} sec"
        )

    # === CAR COMPARISON: "compare Model 3 vs i4" ===
    if "compare" in q and "vs" in q:
        parts = q.replace("compare", "").replace("vs", "|").split("|")
        if len(parts) < 2:
            return "Please say: **compare [Car 1] vs [Car 2]** (e.g., `compare Model 3 vs i4`)"

        car1_query = parts[0].strip()
        car2_query = parts[1].strip()

        def find_car(query):
            q_key = query.lower().replace(" ", "").replace("-", "")
            matches = df[df['Model_Key'].str.contains(q_key, na=False)]
            return matches.iloc[0] if not matches.empty else None

        car1 = find_car(car1_query)
        car2 = find_car(car2_query)

        if not car1 or not car2:
            missing = car1_query if not car1 else car2_query
            return f"Couldn't find **{missing}**. Try full name like **Tesla Model Y** or **BMW i4**."

        def format_car(c):
            return (
                f"**{c['Brand']} {c['Model']}**\n"
                f"Price: `${c['Estimated_US_Value']:,.0f}`\n"
                f"Range: {int(c['km_of_range'])} km\n"
                f"0-100: {c['0-100']} sec\n"
                f"Top Speed: {int(c['Top_Speed'])} km/h\n"
                f"Battery: {c['Battery']:.1f} kWh\n"
                f"Seats: {int(c['Number_of_seats'])}\n"
                f"Towing: {int(c['Towing_capacity_in_kg'])} kg"
            )

        return f"### Car Comparison\n\n{format_car(car1)}\n\n**VS**\n\n{format_car(car2)}"

    # === CAR SUMMARY ===
    if any(x in q for x in ["tell me about", "info on", "summary", "details", "what is", "describe"]):
        model_query = original_q
        for prefix in ["tell me about ", "info on ", "summary of ", "details of ", "what is ", "describe "]:
            if model_query.lower().startswith(prefix):
                model_query = model_query[len(prefix):].strip()
                break
        q_key = model_query.lower().replace(" ", "").replace("-", "")
        matches = df[df['Model_Key'].str.contains(q_key, na=False)]
        if matches.empty:
            return f"Sorry, I couldn't find **{model_query}**. Try a full model name."
        car = matches.iloc[0]
        return (
            f"### {car['Brand']} {car['Model']}\n\n"
            f"**Price**: `${car['Estimated_US_Value']:,.0f}`\n"
            f"**Range**: {int(car['km_of_range'])} km\n"
            f"**0-100 km/h**: {car['0-100']} sec\n"
            f"**Top Speed**: {int(car['Top_Speed'])} km/h\n"
            f"**Battery**: {car['Battery']:.1f} kWh\n"
            f"**Efficiency**: {int(car['Efficiency'])} Wh/km\n"
            f"**Seats**: {int(car['Number_of_seats'])}\n"
            f"**Towing**: {int(car['Towing_capacity_in_kg'])} kg"
        )

    # === EXTREME QUERIES (with brand context) ===
    if ("longest" in q or "most" in q or "best" in q) and "range" in q:
        car = df_context.loc[df_context['km_of_range'].idxmax()]
        return f"{context}, the **{car['Brand']} {car['Model']}** has the longest range: **{int(car['km_of_range'])} km**."

    if "cheapest" in q or ("lowest" in q and "price" in q):
        valid = df_context[df_context['Estimated_US_Value'] > 0]
        if valid.empty:
            return f"No priced cars found {context.lower()}."
        car = valid.loc[valid['Estimated_US_Value'].idxmin()]
        return f"{context}, the cheapest is **{car['Brand']} {car['Model']}** at **${car['Estimated_US_Value']:,.0f}**."

    if ("fastest" in q or "quickest" in q) and ("0-100" in q or "acceleration" in q):
        car = df_context.loc[df_context['0-100'].idxmin()]
        return f"{context}, the fastest 0-100 is **{car['Brand']} {car['Model']}** in **{car['0-100']} sec**."

    if "towing" in q and any(x in q for x in ["most", "highest", "best", "max"]):
        car = df_context.loc[df_context['Towing_capacity_in_kg'].idxmax()]
        return f"{context}, the **{car['Brand']} {car['Model']}** tows the most: **{int(car['Towing_capacity_in_kg'])} kg**."

    # === BRAND-SPECIFIC BEST (e.g., "best Tesla for range") ===
    if found_brand and any(x in q for x in ["best", "top", "highest", "longest", "cheapest", "fastest"]):
        if "range" in q:
            car = df_context.loc[df_context['km_of_range'].idxmax()]
            return f"Best **{found_brand}** for range: **{car['Model']}** — {int(car['km_of_range'])} km"
        if "price" in q or "cheapest" in q:
            car = df_context[df_context['Estimated_US_Value'] > 0].loc[df_context['Estimated_US_Value'].idxmin()]
            return f"Cheapest **{found_brand}**: **{car['Model']}** — `${car['Estimated_US_Value']:,.0f}`"
        if "0-100" in q or "acceleration" in q or "fastest" in q:
            car = df_context.loc[df_context['0-100'].idxmin()]
            return f"Fastest **{found_brand}**: **{car['Model']}** — {car['0-100']} sec"

    # === BRAND SUMMARY (if only brand mentioned) ===
    if found_brand and len(q.split()) <= 3:
        count = len(df_context)
        avg_price = df_context['Estimated_US_Value'].mean()
        avg_range = df_context['km_of_range'].mean()
        return (
            f"**{found_brand}** has **{count} models**.\n"
            f"• Avg Price: **${avg_price:,.0f}**\n"
            f"• Avg Range: **{avg_range:.0f} km**\n"
            f"• Price Range: `${df_context['Estimated_US_Value'].min():,.0f}` – `${df_context['Estimated_US_Value'].max():,.0f}`"
        )

    # === FALLBACK ===
    return random.choice([
        "I didn't quite get that. Try:\n"
        "• `compare Tesla vs BMW`\n"
        "• `tell me about Model Y`\n"
        "• `longest range Porsche`\n"
        "• `show summary`",
        "Hmm, try asking:\n"
        "• **Compare**: `Model 3 vs i4`\n"
        "• **Best**: `cheapest Tesla`\n"
        "• **Stats**: `how many cars?`",
        "You can ask me to **compare brands**, **summarize cars**, or find the **best in any category**!"
    ])

# ==============================
# MAIN APP
# ==============================
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
    st.image("https://cdn.pixabay.com/photo/2022/01/25/19/12/electric-car-6968348_1280.jpg", use_container_width=True)
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
                'Battery': [battery],
                '0-100': [accel],
                'Top_Speed': [top_speed],
                'Range': [range_km],
                'Efficiency': [efficiency],
                'Number_of_seats': [seats]
            })
            pred = model.predict(input_df)[0]
            st.success(f"### Estimated Price: **${pred:,.0f}**")
            st.balloons()
        else:
            st.error("Model not loaded.")

# ==============================
# 2. EV Data Chatbot
# ==============================
elif page == "EV Data Chatbot":
    st.title("EV Chatbot")
    st.markdown("Ask anything! Try: **compare Tesla vs BMW**, **tell me about Lucid Air**, or **cheapest Porsche**")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": (
                "Hi! I'm your **EV Expert**\n\n"
                "Try asking:\n"
                "• `compare Tesla vs BMW`\n"
                "• `compare Model 3 vs i4`\n"
                "• `tell me about Lucid Air`\n"
                "• `longest range Porsche`\n"
                "• `cheapest car`\n"
                "• `show summary`"
            )
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

        sel_seats = st.sidebar.multiselect("Seats", sorted(viz_df['Number_of_seats'].unique()), default=sorted(viz_df['Number_of_seats'].unique()))

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
                fig = px.scatter(filtered, x='km_of_range', y='Estimated_US_Value', color='Brand', size='Battery',
                                 hover_data=['Model'], labels={'km_of_range': 'Range (km)', 'Estimated_US_Value': 'Price'})
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
