import csv
import os

CSV_PATH = os.path.join("static", "data", "skin_recommendations.csv")


def _parse_product(entry: str) -> dict:
    brand, _, name = entry.strip().partition("::")
    return {"brand": brand.strip(), "name": name.strip()}


def get_recommendation(predicted_class: str) -> dict:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["predicted_class"].lower() == predicted_class.lower():
                return {
                    "concern_name": row["concern_name"],
                    "explanation": row["explanation"],
                    "ingredients": [i.strip() for i in row["ingredients"].split("|")],
                    "suggested_products": [_parse_product(p) for p in row["suggested_products"].split("|")],
                    "skincare_advice": [a.strip() for a in row["skincare_advice"].split("|")],
                }
    return {
        "concern_name": predicted_class,
        "explanation": "No recommendation data found for this condition.",
        "ingredients": [],
        "suggested_products": [],
        "skincare_advice": [],
    }
