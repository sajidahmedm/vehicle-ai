import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Vehicle Advisor AI", layout="wide")

# ---------- SESSION ----------
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'show_showroom' not in st.session_state:
    st.session_state.show_showroom = False
if 'vehicle_type' not in st.session_state:
    st.session_state.vehicle_type = None

# ---------- LOAD DATA ----------
@st.cache_data
def load_showroom_data():
    df = pd.read_csv("showrooms1.csv", sep=",", engine='python')
    df.columns = df.columns.str.strip().str.replace('\n','')
    return df

showroom_df = load_showroom_data()

# ---------- UI ----------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?q=80&w=1966&auto=format&fit=crop");
    background-size: cover;
}
h1, label { color: white; }

.vehicle-card {
    background: rgba(0,0,0,0.6);
    padding: 20px;
    border-radius: 12px;
    transition: 0.3s;
}
.vehicle-card:hover {
    transform: scale(1.05);
    background: rgba(0,0,0,0.9);
}
</style>
""", unsafe_allow_html=True)

# ---------- HOME ----------
if st.session_state.page == 'home':

    st.markdown("<h1 style='text-align:center;'>🚘 AI Based Vehicle Recommendation</h1>", unsafe_allow_html=True)

    with st.form("user_form"):
        age = st.number_input("Enter your age", min_value=0)
        salary = st.number_input("Enter your monthly salary (₹)")
        vehicle_type = st.selectbox("Preferred Vehicle Type", ["Scooter","Bike","Car"])
        submit = st.form_submit_button("Get Recommendations")

    if submit:
        if age < 18:
            st.warning("No vehicles for age under 18")
        else:
            payload = {
                "age": age,
                "salary": salary,
                "vehicleType": {"Scooter":0,"Bike":1,"Car":2}[vehicle_type]
            }

            st.info("⏳ Connecting... first request may take up to 60 sec")

            try:
                response = requests.post(
                    "https://vehicle-ai-uy20-7odh.onrender.com",
                    # "http://127.0.0.1:5000/recommend",
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    try:
                        data = response.json()

                        if not data:
                            st.warning("No recommendations found")
                        else:
                            st.session_state.recommendations = data
                            st.session_state.vehicle_type = vehicle_type
                            st.session_state.page = 'recommendations'

                    except:
                        st.warning("⚠️ Server responded but data not ready. Try again.")
                else:
                    st.error("❌ Server error. Please try again.")

            except requests.exceptions.Timeout:
                st.warning("⚠️ Server is waking up... click again after few seconds")

            except requests.exceptions.ConnectionError:
                st.error("❌ Network issue. Check internet connection.")

            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ---------- RECOMMENDATIONS (MISSING PART FIXED) ----------
elif st.session_state.page == 'recommendations':

    st.title("Recommended Vehicles")

    # SIDEBAR
    with st.sidebar:
        st.markdown("### 📍 Showroom Info")
        st.session_state.show_showroom = st.checkbox("Show Nearby Showrooms")

        if st.session_state.show_showroom:
            if st.button("View Showrooms"):
                st.session_state.page = 'showrooms'

    if not st.session_state.recommendations:
        st.warning("No recommendations found")
        if st.button("Back"):
            st.session_state.page = 'home'

    else:
        cols = st.columns(3)

        for i, rec in enumerate(st.session_state.recommendations):
            with cols[i % 3]:
                name = rec['name']
                price = float(rec['price'])
                mileage = rec.get('mileage', 'N/A')
                fuel = rec.get('fuel', 'N/A')

                st.markdown(f"""
                <div class='vehicle-card'>
                    <h4>{name}</h4>
                    <p><b>Price:</b> ₹{price:,.0f}</p>
                    <p><b>Mileage:</b> {mileage}</p>
                    <p><b>Fuel:</b> {fuel}</p>
                </div>
                """, unsafe_allow_html=True)

                # EMI
                with st.expander("₹ EMI Options"):
                    st.write(f"1 Year: ₹{price/12:,.0f} / month")
                    st.write(f"3 Years: ₹{price/36:,.0f} / month")
                    st.write(f"5 Years: ₹{price/60:,.0f} / month")

        if st.button("Back"):
            st.session_state.page = 'home'

# ---------- SHOWROOM ----------
elif st.session_state.page == 'showrooms':

    st.title("Nearby Showrooms")

    recommended_brands = set([rec['name'].split()[0].lower() for rec in st.session_state.recommendations])

    showroom_df['Brand'] = showroom_df['Brand'].astype(str).str.lower()

    filtered = showroom_df[showroom_df['Brand'].isin(recommended_brands)]

    if filtered.empty:
        st.warning("No showroom data found")
    else:
        for _, row in filtered.iterrows():
            showroom_name = row['Showroom Name']
            address = row['Address']
            pincode = row.get('Pincode','')

            maps_query = f"{showroom_name},{address},{pincode}".replace(" ","+")
            maps_url = f"https://www.google.com/maps/search/?api=1&query={maps_query}"

            st.markdown(f"""
            <div class='vehicle-card'>
                <b>{showroom_name}</b><br>
                {address}<br>
                {pincode}<br>
                <a href="{maps_url}" target="_blank">🗺️ View on Map</a>
            </div>
            """, unsafe_allow_html=True)

    if st.button("Back"):
        st.session_state.page = 'recommendations'