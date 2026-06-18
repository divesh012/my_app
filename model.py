import math

# --------------------------------------------
# Haversine distance
# --------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) ** 2

    return 2 * R * math.asin(math.sqrt(a))


# ------------------------------------------------
# Normalize values 0–1
# ------------------------------------------------
def normalize(value, max_value):
    return max(0, min(1, value / max_value))


# ------------------------------------------------
# Master Recommendation Model
# ------------------------------------------------
def recommend_salons(user_lat, user_lon, category, salons, radius_km=7):
    nearby = []

    for shop in salons:
        distance = haversine(user_lat, user_lon, shop["lat"], shop["lon"])

        if distance <= radius_km:

            # Scores
            distance_score = 1 - normalize(distance, radius_km)
            rating_score = normalize(shop.get("rating", 3), 5)
            popularity_score = normalize(shop.get("bookings", 10), 100)
            category_match = 1 if category.lower() in shop["category"].lower() else 0

            # Weighted final score (like Zomato/Swiggy)
            final_score = (
                0.45 * distance_score +
                0.30 * rating_score +
                0.15 * popularity_score +
                0.10 * category_match
            )

            shop["distance"] = round(distance, 2)
            shop["rank_score"] = round(final_score, 4)

            nearby.append(shop)

    # Sort by rank score (descending)
    nearby = sorted(nearby, key=lambda x: x["rank_score"], reverse=True)

    return nearby
