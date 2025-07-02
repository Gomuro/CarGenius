# server/ml/train_model.py
import os
import pathlib
import sys

import numpy as np
from dotenv import load_dotenv

load_dotenv()
print("✅ DATABASE_URL =", os.getenv("DATABASE_URL"))

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.core.database import get_db, async_session_maker
from app.models.car import ListingMobileDe
from ml.features import preprocess_data, NUMERIC_COLS, CATEGORICAL_COLS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


async def get_flat_listings_async(session):
    """ Retrieve active listings from the database and flatten their structure. """
    result = await session.execute(
        select(ListingMobileDe)
        .options(
            joinedload(ListingMobileDe.technical_details),
            joinedload(ListingMobileDe.equipment)
        )
        .filter(ListingMobileDe.is_active == True)
    )
    listings = result.scalars().all()

    flat_data = []
    for listing in listings:
        flat_item = {}
        for col in ListingMobileDe.__table__.columns.keys():
            if col not in ["id", "url", "currency"]:
                flat_item[col] = getattr(listing, col)

        if listing.technical_details:
            for key, value in listing.technical_details.__dict__.items():
                if not key.startswith("_"):
                    flat_item[key] = value

        if listing.equipment:
            for key, value in listing.equipment.__dict__.items():
                if not key.startswith("_"):
                    flat_item[key] = value

        flat_data.append(flat_item)

    return flat_data


async def train_and_save_model_from_db_async():
    """ Train a model using data from the database and save it to disk. """
    async with async_session_maker() as session:
        flat_data = await get_flat_listings_async(session)
        print(f"Retrieved {len(flat_data)} listings from the database")
        df = pd.DataFrame(flat_data)
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = np.nan  # so that pandas understands it as a space

            # Check which columns are still missing
        missing_cols = [col for col in CATEGORICAL_COLS if col not in df.columns]
        if missing_cols:
            print(f"Still missing categorical columns before preprocess_data: {missing_cols}")

        # Call preprocess_data
        df, scaler = preprocess_data(df, fit=True)

        x = df.drop(columns=["price"])
        y = df["price"]  #

        # Model training
        model = RandomForestRegressor(n_estimators=100)
        datetime_cols = x.select_dtypes(include=["datetime", "datetimetz"]).columns
        if len(datetime_cols) > 0:
            print(f"Dropping datetime columns: {list(datetime_cols)}")
            x = x.drop(columns=datetime_cols)
        model.fit(x, y)

        model_dir = pathlib.Path(__file__).resolve().parent / "model"
        model_dir.mkdir(exist_ok=True)

        features = x.columns.tolist()

        joblib.dump(model, model_dir / "price_model.pkl")
        joblib.dump(features, model_dir / "model_features.pkl")
        joblib.dump(scaler, model_dir / "scaler.pkl")


import asyncio

if __name__ == "__main__":
    asyncio.run(train_and_save_model_from_db_async())
