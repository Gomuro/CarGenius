from ml.predict import predict_price

def evaluate_offer(listing_data: dict) -> dict:
    predicted_price = predict_price(listing_data)
    actual_price = listing_data.get("price", 0)

    return {
        "actual_price": actual_price,
        "predicted_price": predicted_price,
        "difference": actual_price - predicted_price,
        "is_profitable": actual_price < predicted_price * 0.85
    }
