from flask import Flask, request, jsonify
import pandas as pd
import re
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load data
vehicle_df = pd.read_csv("updated_expanded_vehicle.csv")
car_df = pd.read_csv("updated_expanded_car.csv")

# Preprocess mileage
vehicle_df["Mileage"] = vehicle_df["Mileage"].apply(lambda x: float(re.sub(r"[^0-9.]", "", str(x))) if pd.notna(x) else 0)
car_df["Mileage"] = car_df["Mileage"].apply(lambda x: float(re.sub(r"[^0-9.]", "", str(x))) if pd.notna(x) else 0)

# Label Encoding
type_encoder = LabelEncoder()
fuel_encoder_vehicle = LabelEncoder()
variant_encoder = LabelEncoder()
fuel_encoder_car = LabelEncoder()

vehicle_df["TypeEncoded"] = type_encoder.fit_transform(vehicle_df["Type"])
vehicle_df["FuelEncoded"] = fuel_encoder_vehicle.fit_transform(vehicle_df["Fuel"])
car_df["VariantEncoded"] = variant_encoder.fit_transform(car_df["Variant"])
car_df["FuelEncoded"] = fuel_encoder_car.fit_transform(car_df["Fuel"])

# Train linear model
X_vehicle = vehicle_df[["TypeEncoded", "FuelEncoded", "Mileage"]]
y_vehicle = vehicle_df["Price"]
vehicle_model = LinearRegression()
vehicle_model.fit(X_vehicle, y_vehicle)

# Accuracy (R²)
y_pred = vehicle_model.predict(X_vehicle)
accuracy = r2_score(y_vehicle, y_pred)
print(f"Vehicle Price Prediction Model R² Accuracy: {accuracy:.2f}")

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    age = data.get("age")
    salary = data.get("salary")
    v_type = data.get("vehicleType")  # 0: Scooter, 1: Bike, 2: Car

    results = []

    if v_type == 2:
        if salary < 75000 or age <= 18:
            return jsonify([])

        if 75000 <= salary <= 100000:
            cars = car_df[car_df['Price'] <= 1300000]
        elif 100000 < salary < 150000:
            cars = car_df[car_df['Price'] <= 1900000]
        elif 150000 <= salary <= 300000:
            cars = car_df[car_df['Price'] <= 3200000]
        elif salary > 300000:
            cars = car_df[car_df['Price'] > 1900000]
        else:
            cars = pd.DataFrame()

        for _, row in cars.iterrows():
            results.append({
                "name": row["Name"],
                "price": row["Price"],
                "mileage": row.get("Mileage", "N/A"),
                "fuel": row.get("Fuel", "N/A")
            })

    else:
        if salary < 20000 or age < 18:
            return jsonify([])

        target_encoded = type_encoder.transform([["Scooter", "Bike"][v_type]])[0]
        min_price, max_price = 0, float("inf")

        if 18 <= age <= 35:
            if 20000 <= salary <= 50000:
                max_price = 100000
            elif 50000 < salary <= 100000:
                min_price, max_price = 100000, 200000
        elif 36 <= age <= 70:
            if 20000 <= salary <= 50000:
                max_price = 100000
            elif 36 <= age <= 50 and 50000 < salary <= 100000:
                min_price, max_price = 100000, 150000
            elif 51 <= age <= 70 and salary > 50000:
                max_price = 150000
            elif salary > 100000:
                max_price = 300000

        for _, row in vehicle_df.iterrows():
            if row['TypeEncoded'] == target_encoded:
                features = [[row['TypeEncoded'], row['FuelEncoded'], row['Mileage']]]
                pred_price = vehicle_model.predict(features)[0]
                if min_price <= pred_price <= max_price:
                    results.append({
                        "name": row["Name"],
                        "price": pred_price,
                        "mileage": row.get("Mileage", "N/A"),
                        "fuel": row.get("Fuel", "N/A")
                    })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
