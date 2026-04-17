import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AI based Vehicle Recommendation", layout="wide")

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
}
h1, label { color: white; }
.vehicle-card {
    background: rgba(0,0,0,0.6);
    padding: 20px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------- HOME PAGE --------
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align:center;'>🚘 AI Vehicle Recommendation System</h1>", unsafe_allow_html=True)

    with st.form("user_input"):
        age = st.number_input("Enter your age", min_value=0, step=1)
        salary = st.number_input("Enter your monthly salary (₹)", step=1000)
        vehicle_type = st.selectbox("Preferred Vehicle Type", ["Scooter", "Bike", "Car"])
        submitted = st.form_submit_button("Get Recommendations")

    if submitted:
        if age < 18:
            st.warning("No vehicles for age under 18.")
        else:
            type_map = {"Scooter": 0, "Bike": 1, "Car": 2}

            payload = {
                "age": age,
                "salary": salary,
                "vehicleType": type_map[vehicle_type]
            }

            st.info("⏳ First request may take 30–60 sec (free backend waking up)")

            try:
                response = requests.post(
                    "https://vehicle-ai-uy20.onrender.com/recommend",
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        st.session_state.recommendations = data
                        st.session_state.vehicle_type = vehicle_type
                        st.session_state.page = 'recommendations'
                    except:
                        st.error("⚠️ Backend waking up... Try again in 30 sec")
                else:
                    st.error(f"Error: {response.text}")

            except Exception as e:
                st.error(f"Backend error: {e}")

# -------- RECOMMENDATIONS --------
elif st.session_state.page == 'recommendations':
    st.title("Recommended Vehicles")

    if not st.session_state.recommendations:
        st.warning("No recommendations found")
        if st.button("Back"):
            st.session_state.page = 'home'
    else:
        cols = st.columns(3)
        for i, rec in enumerate(st.session_state.recommendations):
            with cols[i % 3]:
                st.markdown(f"""
                <div class='vehicle-card'>
                    <h4>{rec['name']}</h4>
                    <p>Price: ₹{float(rec['price']):,.0f}</p>
                    <p>Mileage: {rec.get('mileage','N/A')}</p>
                    <p>Fuel: {rec.get('fuel','N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

        if st.button("Back"):
            st.session_state.page = 'home'

# -------- SHOWROOM --------
elif st.session_state.page == 'showrooms':
    st.title("Showrooms")

    if st.button("Back"):
        st.session_state.page = 'recommendations'