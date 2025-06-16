import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import joblib

with open("car_data_Audi_1.json", "r", encoding="utf-8") as f:
    data = json.load(f)

flat_data = []
for item in data:
    flat_item = {}
    flat_item.update(item.get("listing", {}))
    flat_item.update(item.get("technical_details", {}))
    flat_item.update(item.get("equipment", {}))
    flat_data.append(flat_item)

df = pd.DataFrame(flat_data)
if "price" not in df.columns:
    raise ValueError("❌ Column 'price' not found after flattening JSON!")

numeric_cols = df.select_dtypes(include=["int", "float"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "bool"]).columns.tolist()

# df.to_csv("car_data.csv", index=False)

print("➡️  Numeric columns:", numeric_cols)
print("➡️  Categorical columns:", categorical_cols)

if "price" in numeric_cols:
    numeric_cols.remove("price")

df = df[numeric_cols + categorical_cols + ["price"]]

# 4. Попередня обробка
df = df[numeric_cols + categorical_cols + ["price"]]
df = df.dropna(subset=["price"])

X = df.drop(columns=["price"])
y = df["price"]

X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

X = X.fillna(0)
X[numeric_cols] = StandardScaler().fit_transform(X[numeric_cols])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print(f"✅ Model trained. R² score: {score:.4f}")

# joblib.dump(model, "model.joblib")
joblib.dump(model, "model/price_model.pkl")
# joblib.dump(X.columns.tolist(), "model_features.joblib")
joblib.dump(X.columns.tolist(), "model/model_features.pkl")
