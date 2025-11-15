# ⚡ EV Data Hub

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-render-app-url.onrender.com)

An interactive, multi-page Streamlit application for analyzing, visualizing, and interacting with Electric Vehicle (EV) data.

![EV Data Hub Home Page](assets/home_image.jpg)

## 📖 Overview

The EV Data Hub is an all-in-one tool for exploring, analyzing, and predicting information about Electric Vehicles. It combines a pre-trained machine learning model, a conversational chatbot, and an interactive data dashboard into a single, user-friendly web application.

## ✨ Key Features

* **🏠 Home Page:** A welcoming landing page that explains the app's features.
* **🤖 EV Price Predictor:** Uses a pre-trained Scikit-learn model to estimate the price of an EV based on its technical specifications (battery, range, speed, etc.).
* **💬 EV Data Chatbot:** A natural language interface to query the dataset. Ask questions like:
    * *"Tesla vs BMW"*
    * *"compare Model 3 vs i4"*
    * *"longest range"*
    * *"cheapest Porsche"*
* **📊 Data Visualization:** An interactive dashboard built with Plotly. Users can filter the dataset by brand, price, range, and seats to see dynamic charts.
* **📂 CSV Data Uploader:** Users can upload their own EV data (as a CSV file) to power the Chatbot and Visualization pages.

## 🛠️ Tech Stack

* **Python:** The core programming language.
* **Streamlit:** The web application framework.
* **Pandas:** For data loading, processing, and analysis.
* **Scikit-learn (sklearn) & Joblib:** For loading and using the pre-trained machine learning model.
* **Plotly:** For creating interactive data visualizations.

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

* Python 3.8 or newer
* `pip` (Python package installer)

### Installation & Running

1.  **Clone the repository:**
    ```bash
    # === TO DO: REPLACE with your GitHub URL ===
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    Make sure you have all the necessary files in your project directory:
    * `app.py`
    * `model.pkl` (your pre-trained model)
    * `cars_data_cleaned.csv` (the default dataset)
    * `requirements.txt`
    * `assets/` (folder with `home_image.jpg` and `predictor_image.jpg`)

    Then, install the requirements:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
    Your app will open automatically in your web browser.

---

## 📁 Project Structure
