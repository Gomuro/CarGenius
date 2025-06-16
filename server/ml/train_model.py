import joblib
import pandas as pd
from features import preprocess_data, NUMERIC_COLS


def train_and_save_model():
    import json
    with open("car_data_Audi_1.json", "r") as f:
        data = json.load(f)

    flat_data = []
    for item in data:
        flat_item = {}
        flat_item.update(item.get("listing", {}))
        flat_item.update(item.get("technical_details", {}))
        equipment = item.get("equipment", {})
        for key, value in equipment.items():
            flat_item[f"equipment_{key}"] = value
        flat_data.append(flat_item)

    df = pd.DataFrame(flat_data)
    print(df[NUMERIC_COLS].dtypes)
    print(df[NUMERIC_COLS].head())

    df, scaler = preprocess_data(df, fit=True)

    x = df.drop(columns=["price"])
    y = df["price"]

    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100)
    print("x.dtypes**********", x.dtypes)
    print("x.head~~~~~~~~~~~~", x.head())

    model.fit(x, y)

    # joblib.dump(model, "app/ml/model/price_model.pkl")
    joblib.dump(model, "model/price_model.pkl")
    # joblib.dump(scaler, "app/ml/model/scaler.pkl")
    joblib.dump(scaler, "model/scaler.pkl")

if __name__ == "__main__":
    train_and_save_model()
