import streamlit as st
import pandas as pd
import joblib
import random
import plotly.express as px
import plotly.graph_objects as go
import re

# ==============================
# App Constants
# ==============================
REQUIRED_COLUMNS = [
    'Brand', 'Model', 'Estimated_US_Value', 'km_of_range', 'Battery',
    '0-100', 'Top_Speed', 'Efficiency', 'Number_of_seats', 'Towing_capacity_in_kg'
]

# ==============================
# Page Configuration
# ==============================
st.set_page_config(page_title="EV Data Hub", page_icon="⚡", layout="wide")

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
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

model = load_model()

# ==============================
# Data Loading & Processing
# ==============================
@st.cache_data
def load_default_data():
    """Loads the default CSV file."""
    try:
        return pd.read_csv('cars_data_cleaned.csv')
    except FileNotFoundError:
        st.error("Default data file 'cars_data_cleaned.csv' not found.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading default data: {e}")
        return pd.DataFrame()

def process_dataframe(df):
    """Checks, validates, and processes a DataFrame."""
    if df.empty:
        st.session_state.data_valid = False
        return df

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.session_state.data_valid = False
        st.warning(f"Uploaded file is missing required columns: {', '.join(missing_cols)}")
        return df

    st.session_state.data_valid = True
    try:
        processed_df = df.copy()
        
        # Normalize Brand and Model
        processed_df['Brand'] = processed_df['Brand'].astype(str).str.strip().str.upper()
        processed_df['Model'] = processed_df['Model'].astype(str).str.strip()

        # Create robust search keys
        processed_df['Model_Key'] = (
            processed_df['Model']
            .str.lower()
            .str.replace(r'[^a-z0-9\s]', '', regex=True)
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
        processed_df['Search_Key'] = (
            processed_df['Brand'].str.lower() + ' ' + processed_df['Model'].str.lower()
        ).str.replace(r'[^a-z0-9\s]', '', regex=True)
         .str.replace(r'\s+', ' ', regex=True)
         .str.strip()

        return processed_df
    except Exception as e:
        st.error(f"Error processing DataFrame: {e}")
        st.session_state.data_valid = False
        return df

# ==============================
# Helper Function
# ==============================
def find_car(query, df):
    """Finds the best match for a car query in the provided dataframe."""
    if df.empty or not st.session_state.get('data_valid', False):
        return None

    q_norm = (
        re.sub(r'[^a-z0-9\s]', '', query.lower())
        .replace(r'\s+', ' ', regex=True)
        .strip()
    )

    # 1. Exact match on 'Brand Model'
    exact_match = df[df['Search_Key'] == q_norm]
    if not exact_match.empty:
        return exact_match.iloc[0]

    # 2. Exact match on 'Model' only
    exact_model_match = df[df['Model_Key'] == q_norm]
    if not exact_model_match.empty:
        return exact_model_match.iloc[0]

    # 3. Contains match on 'Brand Model'
    contains_match = df[df['Search_Key'].str.contains(q_norm, na=False, regex=False)]
    if not contains_match.empty:
        return contains_match.iloc[0]

    # 4. Contains match on 'Model' only
    contains_model_match = df[df['Model_Key'].str.contains(q_norm, na=False, regex=False)]
    if not contains_model_match.empty:
        return contains_model_match.iloc[0]

    return None

# ==============================
# Chatbot Logic
# ==============================
def process_query(query, df):
    """Processes the user's query against the provided dataframe."""
    if df.empty or not st.session_state.get('data_valid', False):
        return "Sorry, the loaded data is invalid or missing required columns. Please upload a valid EV data CSV."

    q = query.lower().strip()
    original_q = query.strip()

    # --- Standard Greetings/Help ---
    if any(g in q for g in ["hi", "hello", "hey", "yo", "howdy", "greetings"]):
        return random.choice([
            "Hey there! Ready to dive into the world of EVs?",
            "Hi! I'm your EV guru. Ask me about **range**, **price**, **speed**, or **compare cars**!",
            "Hello! What EV are you dreaming about today?"
        ])

    if any(h in q for h in ["help", "what can you", "who are you", "info", "what do you do"]):
        return (
            "I'm your **EV Assistant**! Here's what I can do:\n\n"
            "• **Compare cars**: `compare Tesla Model 3 vs BMW i4`\n"
            "• **Compare brands**: `Tesla vs BMW`\n"
            "• **Car summary**: `tell me about Lucid Air`\n"
            "• **Best in class**: `longest range`, `cheapest car`, `fastest 0-100`\n"
            "• **Brand stats**: `best Tesla for towing`, `cheapest Porsche`\n"
            "• **Dataset info**: `show summary`, `how many cars?`\n"
            "• **List brands**: `brands`\n\n"
            "Try any of these!"
        )

    if any(t in q for t in ["thanks", "thank you", "thankyou", "bye", "goodbye", "see you"]):
        return random.choice([
            "You're welcome! Charge safe!",
            "Happy to help!",
            "See you next time!"
        ])

    # --- Data-Dependent Queries ---
    # === LIST ALL BRANDS ===
    if "brand" in q and any(x in q for x in ["list", "all", "available", "show"]):
        brands = sorted(df['Brand'].unique())
        return f"**Available Brands** ({len(brands)}): \n`{', '.join(brands)}`"

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

    # === BRAND DETECTION (Case-Insensitive) ===
    q_lower = q.lower()
    all_brands_lower = [b.lower() for b in df['Brand'].unique()]
    found_brands_in_query = [b.title() for b in all_brands_lower if b in q_lower]

    # === BRAND-LEVEL COMPARISON ===
    if "vs" in q and len(found_brands_in_query) >= 2:
        b1, b2 = found_brands_in_query[0], found_brands_in_query[1]
        df1 = df[df['Brand'] == b1]
        df2 = df[df['Brand'] == b2]

        if df1.empty or df2.empty:
            missing = b1 if df1.empty else b2
            return f"**{missing}** not found in the dataset."

        def brand_stats(d):
            return {
                'Models': len(d),
                'Avg Price': f"${d['Estimated_US_Value'].mean():,.0f}",
                'Avg Range': f"{d['km_of_range'].mean():.0f} km",
                'Best Range': f"{d['km_of_range'].max()} km",
                'Cheapest': f"${d['Estimated_US_Value'].min():,.0f}",
                'Fastest 0-100': f"{d['0-100'].min()} sec"
            }
        s1, s2 = brand_stats(df1), brand_stats(df2)
        return (
            f"### Brand Comparison: **{b1}** vs **{b2}**\n\n"
            f"| Metric | **{b1}** | **{b2}** |\n"
            "| :--- | :--- | :--- |\n"
            f"| Models | {s1['Models']} | {s2['Models']} |\n"
            f"| Avg Price | {s1['Avg Price']} | {s2['Avg Price']} |\n"
            f"| Avg Range | {s1['Avg Range']} | {s2['Avg Range']} |\n"
            f"| Best Range | {s1['Best Range']} | {s2['Best Range']} |\n"
            f"| Cheapest | {s1['Cheapest']} | {s2['Cheapest']} |\n"
            f"| Fastest 0-100 | {s1['Fastest 0-100']} | {s2['Fastest 0-100']} |"
        )

    # === SET BRAND CONTEXT ===
    found_brand = found_brands_in_query[0] if len(found_brands_in_query) == 1 else None
    df_context = df[df['Brand'] == found_brand] if found_brand else df
    context = f"For **{found_brand}**" if found_brand else "Overall"

    # === CAR COMPARISON ===
    if "compare" in q and "vs" in q:
        parts = q.split("vs")
        car1_query = parts[0].replace("compare", "").strip()
        car2_query = parts[1].strip()
        car1 = find_car(car1_query, df)
        car2 = find_car(car2_query, df)

        if car1 is None or car2 is None:
            missing = car1_query if car1 is None else car2_query
            return f"Couldn't find **{missing}**. Try a full name like **Tesla Model Y** or **BMW i4**."

        def format_val(val, unit="", fmt=",.0f"):
            if pd.isna(val):
                return "N/A"
            try:
                return f"{val:{fmt}} {unit}".strip()
            except:
                return f"{val} {unit}".strip()

        return (
            f"### Car Comparison: **{car1['Brand']} {car1['Model']}** vs **{car2['Brand']} {car2['Model']}**\n\n"
            f"| Metric | **{car1['Model']}** | **{car2['Model']}** |\n"
            "| :--- | :--- | :--- |\n"
            f"| Price | {format_val(car1['Estimated_US_Value'], unit='$')} | {format_val(car2['Estimated_US_Value'], unit='$')} |\n"
            f"| Range | {format_val(car1['km_of_range'], unit='km')} | {format_val(car2['km_of_range'], unit='km')} |\n"
            f"| 0-100 | {format_val(car1['0-100'], unit='sec', fmt='.1f')} | {format_val(car2['0-100'], unit='sec', fmt='.1f')} |\n"
            f"| Top Speed | {format_val(car1['Top_Speed'], unit='km/h')} | {format_val(car2['Top_Speed'], unit='km/h')} |\n"
            f"| Battery | {format_val(car1['Battery'], unit='kWh', fmt='.1f')} | {format_val(car2['Battery'], unit='kWh', fmt='.1f')} |\n"
            f"| Seats | {format_val(car1['Number_of_seats'], fmt='.0f')} | {format_val(car2['Number_of_seats'], fmt='.0f')} |\n"
            f"| Towing | {format_val(car1['Towing_capacity_in_kg'], unit='kg')} | {format_val(car2['Towing_capacity_in_kg'], unit='kg')} |"
        )

    # === CAR SUMMARY ===
    if any(x in q for x in ["tell me about", "info on", "summary", "details", "what is", "describe"]):
        model_query = original_q
        for prefix in ["tell me about ", "info on ", "summary of ", "details of ", "what is ", "describe "]:
            if model_query.lower().startswith(prefix):
                model_query = model_query[len(prefix):].strip()
                break
        car = find_car(model_query, df)
        if car is None:
            return f"Sorry, I couldn't find **{model_query}**. Try a full model name."
        return (
            f"### {car['Brand']} {car['Model']}\n\n"
            f"• **Price**: `${car['Estimated_US_Value']:,.0f}`\n"
            f"• **Range**: {int(car['km_of_range'])} km\n"
            f"• **0-100 km/h**: {car['0-100']} sec\n"
            f"• **Top Speed**: {int(car['Top_Speed'])} km/h\n"
            f"• **Battery**: {car['Battery']:.1f} kWh\n"
            f"• **Efficiency**: {int(car['Efficiency'])} Wh/km\n"
            f"• **Seats**: {int(car['Number_of_seats'])}\n"
            f"• **Towing**: {int(car['Towing_capacity_in_kg'])} kg"
        )

    # === EXTREME QUERIES (with brand context) ===
    if ("longest" in q or "most" in q or "best" in q) and "range" in q:
        if df_context.empty:
            return f"No cars found {context.lower()}."
        car = df_context.loc[df_context['km_of_range'].idxmax()]
        return f"{context}, the **{car['Brand']} {car['Model']}** has the longest range: **{int(car['km_of_range'])} km**."

    if "cheapest" in q or ("lowest" in q and "price" in q):
        valid = df_context[df_context['Estimated_US_Value'] > 0]
        if valid.empty:
            return f"No priced cars found {context.lower()}."
        car = valid.loc[valid['Estimated_US_Value'].idxmin()]
        return f"{context}, the cheapest is **{car['Brand']} {car['Model']}** at **${car['Estimated_US_Value']:,.0f}**."

    if ("fastest" in q or "quickest" in q) and ("0-100" in q or "acceleration" in q):
        if df_context.empty:
            return f"No cars found {context.lower()}."
        car = df_context.loc[df_context['0-100'].idxmin()]
        return f"{context}, the fastest 0-100 is **{car['Brand']} {car['Model']}** in **{car['0-100']} sec**."

    if "towing" in q and any(x in q for x in ["most", "highest", "best", "max"]):
        if df_context.empty:
            return f"No cars found {context.lower()}."
        car = df_context.loc[df_context['Towing_capacity_in_kg'].idxmax()]
        return f"{context}, the **{car['Brand']} {car['Model']}** tows the most: **{int(car['Towing_capacity_in_kg'])} kg**."

    # === BRAND SUMMARY (SAFE) ===
    if found_brand and len(q.split()) <= 4:  # Slightly more lenient
        if df_context.empty:
            suggestions = [b for b in df['Brand'].unique() if found_brand.lower() in b.lower()][:3]
            if suggestions:
                return f"**{found_brand}** not found. Did you mean: {', '.join(suggestions)}?"
            return f"**{found_brand}** not found in the dataset."

        count = len(df_context)
        avg_price = df_context['Estimated_US_Value'].mean()
        avg_range = df_context['km_of_range'].mean()
        return (
            f"**{found_brand}** has **{count} model{'s' if count != 1 else ''}**.\n"
            f"• Avg Price: **${avg_price:,.0f}**\n"
            f"• Avg Range: **{avg_range:.0f} km**\n"
            f"• Price Range: `${df_context['Estimated_US_Value'].min():,.0f}` – `${df_context['Estimated_US_Value'].max():,.0f}`"
        )

    # === FALLBACK ===
    return random.choice([
        "I didn't quite get that. Try:\n• Tesla vs BMW\n• tell me about Model Y\n• longest range Porsche\n• show summary",
        "Hmm, try asking:\n• **Compare**: Model 3 vs i4\n• **Best**: cheapest Tesla\n• **Stats**: how many cars?"
    ])

# ==============================
# MAIN APP & DATA MANAGEMENT
# ==============================
if 'active_df' not in st.session_state:
    default_df = load_default_data()
    st.session_state.active_df = process_dataframe(default_df)
    st.session_state.data_source = "Default Data"
    st.session_state.data_valid = True

# --- Sidebar ---
st.sidebar.title("⚡ EV Data Hub")
st.sidebar.markdown("---")

page = st.sidebar.selectbox("Choose a feature", [
    "🏠 Home",
    "🤖 EV Price Predictor",
    "💬 EV Data Chatbot",
    "📊 Data Visualization"
])

st.sidebar.markdown("---")
st.sidebar.header("Data Source")
st.sidebar.info("Upload a CSV to power the Chatbot and Visualizations.")

uploaded_file = st.sidebar.file_uploader("Upload your own EV CSV", type="csv")
if uploaded_file is not None:
    try:
        user_df = pd.read_csv(uploaded_file)
        st.session_state.active_df = process_dataframe(user_df)
        st.session_state.data_source = uploaded_file.name
        st.toast(f"Successfully loaded {uploaded_file.name}!")
        if "messages" in st.session_state:
            del st.session_state.messages
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        st.session_state.data_valid = False

if st.sidebar.button("Reset to Default Data"):
    default_df = load_default_data()
    st.session_state.active_df = process_dataframe(default_df)
    st.session_state.data_source = "Default Data"
    st.toast("Reset to default dataset.")
    if "messages" in st.session_state:
        del st.session_state.messages
    st.rerun()

st.sidebar.metric("Active Data Source", st.session_state.data_source)

if not st.session_state.get('data_valid', True):
    st.sidebar.error("Data is missing required columns. Chatbot and Viz are disabled.")

# Debug: Show available brands
with st.sidebar.expander("Debug: Available Brands", expanded=False):
    if st.session_state.get('data_valid', False):
        brands = sorted(st.session_state.active_df['Brand'].unique())
        st.write(f"**{len(brands)} brands**: {', '.join(brands)}")
    else:
        st.write("No valid data loaded.")

# ==============================
# PAGES
# ==============================

# --- Home ---
if page == "🏠 Home":
    st.title("⚡ Welcome to the EV Data Hub")
    st.markdown("This app is your all-in-one tool for exploring, analyzing, and predicting information about Electric Vehicles.")
    st.image("https://cdn.pixabay.com/photo/2024/04/11/15/22/ev-8690460_1280.jpg", use_container_width=True)
    st.subheader("What You Can Do:", divider="rainbow")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🤖 EV Price Predictor")
            st.markdown("Estimate the price of an EV based on its technical specs.")
    with col2:
        with st.container(border=True):
            st.markdown("#### 💬 EV Data Chatbot")
            st.markdown("Ask natural language questions about the active dataset.")
    with col3:
        with st.container(border=True):
            st.markdown("#### 📊 Data Visualization")
            st.markdown("Use interactive charts and filters to explore the dataset.")
    st.info("**Get Started:** Select a feature from the sidebar. Upload your own CSV or use default data!")

# --- Price Predictor ---
elif page == "🤖 EV Price Predictor":
    st.image("https://cdn.pixabay.com/photo/2022/01/25/19/12/electric-car-6968348_1280.jpg", use_container_width=True)
    st.title("🤖 EV Price Predictor")
    st.markdown("### Tune specs → Get instant price estimate")
    st.info("ℹ️ This predictor uses a pre-trained model and is independent of the data you upload.")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            battery = st.number_input("Battery (kWh)", 20.0, 150.0, 75.0)
            accel = st.number_input("0-100 km/h (sec)", 2.0, 20.0, 6.0)
            seats = st.slider("Seats", 2, 8, 5)
        with col2:
            top_speed = st.number_input("Top Speed (km/h)", 100, 400, 200)
            range_km = st.number_input("Range (km)", 100, 800, 400)
            efficiency = st.number_input("Efficiency (Wh/km)", 100, 300, 180)
        if st.button("Predict Price", type="primary", use_container_width=True):
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

# --- Chatbot ---
elif page == "💬 EV Data Chatbot":
    st.title("💬 EV Data Chatbot")
    st.markdown(f"Ask anything about the **{st.session_state.data_source}** dataset!")
    df = st.session_state.active_df

    if not st.session_state.get('data_valid', False):
        st.error("Chatbot disabled: The active data file is missing required columns.")
        st.markdown(f"Please upload a valid CSV with columns like: `{', '.join(REQUIRED_COLUMNS)}`")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": (
                    "Hi! I'm your **EV Expert**\n\n"
                    "I'm ready to answer questions about the active dataset.\n"
                    "• Try: **Tesla vs BMW**\n"
                    "• Try: **compare Model 3 vs i4**\n"
                    "• Try: **longest range**"
                )
            }]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about EVs..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.spinner("Thinking..."):
                response = process_query(prompt, df)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

# --- Visualization ---
elif page == "📊 Data Visualization":
    st.title("📊 Data Visualization")
    st.markdown(f"Interactive charts for the **{st.session_state.data_source}** dataset")
    df = st.session_state.active_df

    if not st.session_state.get('data_valid', False):
        st.error("Visualizations disabled: The active data file is missing required columns.")
    elif df.empty:
        st.warning("No data loaded.")
    else:
        viz_df = df[df['Estimated_US_Value'] > 0].copy()

        with st.expander("Show Chart Filters", expanded=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                brands = sorted(viz_df['Brand'].unique())
                sel_brands = st.multiselect("Brands", brands, default=brands[:5] if len(brands) > 5 else brands)
                all_seats = sorted(viz_df['Number_of_seats'].unique())
                sel_seats = st.multiselect("Seats", all_seats, default=all_seats)
            with f_col2:
                pmin, pmax = int(viz_df['Estimated_US_Value'].min()), int(viz_df['Estimated_US_Value'].max())
                sel_price = st.slider("Price", pmin, pmax, (pmin, pmax), step=1000, format="$%d")
                rmin, rmax = int(viz_df['km_of_range'].min()), int(viz_df['km_of_range'].max())
                sel_range = st.slider("Range (km)", rmin, rmax, (rmin, rmax), step=10)

        filtered = viz_df[
            viz_df['Brand'].isin(sel_brands) &
            viz_df['Estimated_US_Value'].between(*sel_price) &
            viz_df['km_of_range'].between(*sel_range) &
            viz_df['Number_of_seats'].isin(sel_seats)
        ]

        if filtered.empty:
            st.info("ℹ️ No cars match the current filters. Try expanding your selection.")
        else:
            t1, t2, t3, t4, t5 = st.tabs(["Price vs Range", "Brands", "Performance", "Efficiency", "Top 10"])
            with t1:
                st.subheader("Price vs. Range (Bubble Size by Battery)")
                fig = px.scatter(filtered, x='km_of_range', y='Estimated_US_Value', color='Brand', size='Battery',
                                 hover_data=['Model'], labels={'km_of_range': 'Range (km)', 'Estimated_US_Value': 'Price (USD)'})
                st.plotly_chart(fig, use_container_width=True)
            with t2:
                st.subheader("Model Count per Brand")
                counts = filtered['Brand'].value_counts().reset_index()
                fig = px.bar(counts, x='Brand', y='count', color='count', title="Models per Brand (Filtered)")
                st.plotly_chart(fig, use_container_width=True)
            with t3:
                st.subheader("Performance: 0-100 vs. Top Speed")
                fig = px.scatter(filtered, x='0-100', y='Top_Speed', color='Brand', size='Estimated_US_Value',
                                 hover_data=['Model'], labels={'0-100': '0-100 (sec)', 'Top_Speed': 'Top Speed (km/h)'})
                fig.update_xaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            with t4:
                st.subheader("Average Efficiency by Brand (Lower is Better)")
                eff = filtered.groupby('Brand')['Efficiency'].mean().sort_values().reset_index()
                fig = px.bar(eff, x='Brand', y='Efficiency', color='Efficiency', color_continuous_scale='RdYlGn_r')
                st.plotly_chart(fig, use_container_width=True)
            with t5:
                st.subheader("Top 10 Lists")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### Most Expensive")
                    top_price = filtered.nlargest(10, 'Estimated_US_Value')[['Brand', 'Model', 'Estimated_US_Value']]
                    top_price['Estimated_US_Value'] = top_price['Estimated_US_Value'].map('${:,.0f}'.format)
                    st.dataframe(top_price, use_container_width=True, hide_index=True)
                with c2:
                    st.markdown("#### Longest Range")
                    top_range = filtered.nlargest(10, 'km_of_range')[['Brand', 'Model', 'km_of_range']]
                    top_range['km_of_range'] = top_range['km_of_range'].map('{:,.0f} km'.format)
                    st.dataframe(top_range, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("Filtered Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Models Found", len(filtered))
            c2.metric("Avg Price", f"${filtered['Estimated_US_Value'].mean():,.0f}")
            c3.metric("Avg Range", f"{filtered['km_of_range'].mean():.0f} km")
            c4.metric("Avg Battery", f"{filtered['Battery'].mean():.1f} kWh")
