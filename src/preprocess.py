
import re
import pandas as pd


def clean_text(text):

    # Convert text into lowercase
    text = str(text).lower()

    # Remove unnecessary extra spaces
    text = re.sub(r"\s+", " ", text)

    # Remove leading and trailing spaces
    text = text.strip()

    return text


def prepare_search_text(products):

    # Create a copy to preserve original data
    products = products.copy()

    # Combine important product information
    products["search_text"] = (
        products["product_name"].astype(str) + ". " +
        products["category"].astype(str) + ". " +
        products["brand"].astype(str) + ". " +
        products["description"].astype(str)
    )

    # Clean the combined text
    products["search_text"] = (
        products["search_text"].apply(clean_text)
    )

    return products


if __name__ == "__main__":

    from data_loader import load_products

    products = load_products()

    processed_products = prepare_search_text(products)

    print("Text preprocessing completed!")

    print("\nOriginal product description:")
    print(products["description"].iloc[0])

    print("\nProcessed search text:")
    print(processed_products["search_text"].iloc[0])

