import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Vehicle Advisor AI", layout="wide")

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'show_showroom' not in st.session_state:
    st.session_state.show_showroom = False
if 'vehicle_type' not in st.session_state:
    st.session_state.vehicle_type = None

@st.cache_data
def load_showroom_data():
    df = pd.read_csv("showrooms1.csv", sep=",", quotechar='"', engine='python', on_bad_lines='skip')
    df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '').str.replace('"', '')
    return df

showroom_df = load_showroom_data()

st.markdown("""
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=1966&auto=format&fit=crop");
        background-size: cover;
        background-repeat: no-repeat;
    }
    h1, label {
        color: #ffffff;
    }
    .vehicle-card {
        background: rgba(0, 0, 0, 0.5);
        padding: 20px;
        border-radius: 10px;
        transition: transform 0.3s ease, background 0.3s ease;
    }
    .vehicle-card:hover {
        background: rgba(0, 0, 0, 0.9);
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# Page 1: Input Form
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center;'>🚘 AI Vehicle Recommendation System</h1>", unsafe_allow_html=True)

    with st.form("user_input"):
        age = st.number_input("Enter your age", min_value=0, step=1)
        salary = st.number_input("Enter your monthly salary (₹)", step=1000)
        vehicle_type = st.selectbox("Preferred Vehicle Type", ["Scooter", "Bike", "Car"])
        submitted = st.form_submit_button("Get Recommendations (Double click on it with 2 sec pause for every rec")

    if submitted:
        if age < 18:
            st.warning("No recommended vehicles for age under 18.")
        else:
            type_map = {"Scooter": 0, "Bike": 1, "Car": 2}
            st.session_state.vehicle_type = vehicle_type
            payload = {
                "age": age,
                "salary": salary,
                "vehicleType": type_map[vehicle_type]
            }

            with st.spinner("Fetching recommendations..."):
                try:
                    response = requests.post("http://127.0.0.1:5000/recommend", json=payload)
                    st.session_state.recommendations = response.json()
                    st.session_state.page = 'recommendations'
                except Exception as e:
                    st.error(f"Backend error: {e}")

# Page 2: Recommendations
elif st.session_state.page == 'recommendations':
    st.title("Recommended Vehicles")

    with st.sidebar:
        st.markdown("### 📍 Showroom Info")
        st.session_state.show_showroom = st.checkbox("Show Nearby Showrooms")
        st.markdown("### 🔍 Model Accuracy")
        st.write("Check the terminal where Flask is running for accuracy info.")
        if st.session_state.show_showroom:
            if st.button("View Showrooms"):
                st.session_state.page = 'showrooms'

    if not st.session_state.recommendations:
        st.warning("No recommendations found.")
        if st.button("Back"):
            st.session_state.page = 'home'
    else:
        cols = st.columns(3)
        for idx, rec in enumerate(st.session_state.recommendations):
            with cols[idx % 3]:
                name = rec['name']
                price = float(rec['price'])
                mileage = rec.get('mileage', 'N/A')
                fuel = rec.get('fuel', 'N/A')

                st.markdown(f"""
                    <div class='vehicle-card'>
                        <h4>{name}</h4>
                        <p><b>Price:</b> ₹{price:,.0f}</p>
                        <p><b>Mileage:</b> {mileage} kmpl</p>
                        <p><b>Fuel:</b> {fuel}</p>
                        <details><summary><b>EMI Options</b></summary>
                        <ul>
                        <li>1 Year: ₹{price / 12:,.2f}/month</li>
                        <li>3 Years: ₹{price / 36:,.2f}/month</li>
                        <li>5 Years: ₹{price / 60:,.2f}/month</li>
                        </ul>
                        </details>
                    </div>
                """, unsafe_allow_html=True)

        if st.button("Back"):
            st.session_state.page = 'home'

# Page 3: Showroom Page
elif st.session_state.page == 'showrooms':
    st.title("Available Showrooms for Recommended Vehicles")

    recommended_brands = set()
    for rec in st.session_state.recommendations:
        brand = rec['name'].split()[0].lower()
        recommended_brands.add(brand)

    selected_vehicle_type = st.session_state.vehicle_type
    normalized_type = selected_vehicle_type.lower()
    if normalized_type in ['bike', 'scooter']:
        normalized_type = 'two-wheeler'

    brand_col = [col for col in showroom_df.columns if 'brand' in col.lower()]
    category_col = [col for col in showroom_df.columns if 'category' in col.lower()]

    if brand_col and category_col:
        brand_col, category_col = brand_col[0], category_col[0]

        showroom_df[brand_col] = showroom_df[brand_col].astype(str).str.lower()
        showroom_df[category_col] = showroom_df[category_col].astype(str).str.lower()

        filtered_showrooms = showroom_df[
            (showroom_df[brand_col].isin(recommended_brands)) &
            (showroom_df[category_col] == normalized_type)
        ]
    else:
        st.error("Showroom data missing 'Brand' or 'Category' columns.")
        filtered_showrooms = pd.DataFrame()

    if filtered_showrooms.empty:
        st.warning("No showroom info available for these vehicles.")
    else:
        for i, row in filtered_showrooms.reset_index(drop=True).iterrows():
            showroom_name = row['Showroom Name']
            address = row['Address']
            pincode = row.get('Pincode', '')
            maps_query = f"{showroom_name},{address}, {pincode}".replace(' ', '+')
            maps_url = f"https://www.google.com/maps/search/?api=1&query={maps_query}"

            st.markdown(f"""
                <div class='vehicle-card'>
                <b>{i+1}. {showroom_name}</b><br>
                Brand: {row[brand_col].title()}<br>
                Type: {row[category_col].title()}<br>
                Location: {address}<br>
                Pincode: {pincode}<br>
                <a href="{maps_url}" target="_blank" style="color:#1f77b4; text-decoration:underline;">🗺️ View on Map</a>
                </div>
            """, unsafe_allow_html=True)

    if st.button("Back to Recommendations"):
        st.session_state.page = 'recommendations'