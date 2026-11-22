
from pathlib import Path
import pandas as pd

# Get the main project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset location
DATA_PATH = PROJECT_ROOT / "data" / "products.csv"

# Required dataset columns
REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "brand",
    "price",
    "description"
]


def load_products(path=DATA_PATH):

    # Check whether the dataset exists
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    # Load CSV file
    df = pd.read_csv(path)

    # Validate required columns
    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    # Convert price into numeric values
    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    )

    # Check for missing or invalid values
    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError(
            "Dataset contains missing or invalid values."
        )

    return df


# Run this file directly for testing
if __name__ == "__main__":

    products = load_products()

    print("Dataset loaded successfully!")
    print("Total products:", len(products))

    print("\nProduct details:")
    print(products.head())

