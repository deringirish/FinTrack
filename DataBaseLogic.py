from pymongo import MongoClient
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import DisplayDetails

# Global client variable
client = None


def database_setup():
    global client
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["receipt_scanner"]
        collection = db["receipts"]
        return collection 
    except Exception as e:
        st.error(f"Failed to configure MongoDB: {e}")
        return None


def upload_to_database(json_data):
    collection = database_setup()  
    if collection is not None: 
        try:
            result = collection.insert_one(json_data)
            st.success("Data successfully saved to MongoDB!")
        except Exception as e:
            st.error(f"Failed to save data to MongoDB: {e}")
    else:
        st.error("Failed to connect to MongoDB. Collection not found.")


def display_all_data():
    collection = database_setup()  
    if collection is not None:
        try:
            documents = collection.find()  
            # Convert cursor to list of documents
            data_list = [doc for doc in documents]
            for index, doc in enumerate(data_list):
                # Display each document in a list-wise format
                st.header(f"Data {index + 1}")
                DisplayDetails.print_response_from_image(doc)
        except Exception as e:
            st.error(f"Failed to retrieve data from MongoDB: {e}")
    else:
        st.error("Failed to connect to MongoDB. Collection not found.")


def show_graph():
    """
    Fetch data from the database, sanitize it, and display it as a line chart.
    Handles None values and ensures data integrity before plotting.
    """
    collection = database_setup()
    if collection is not None:
        try:
            # Fetch the data
            data = list(collection.find())

            if not data:
                st.error("No data available in the collection.")
                return

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data)

            # Check if the DataFrame is empty
            if df.empty:
                st.error("No valid data to display.")
                return

            # Initialize a dictionary to store the total price for each category
            category_total = {}

            # Iterate over the data to calculate total price per category
            for index, row in df.iterrows():
                if "items" in row and row["items"]:
                    for item in row["items"]:
                        # Validate category and total_price fields
                        category = item.get("category")
                        price = item.get("total_price")

                        if category and isinstance(category, str) and price:
                            try:
                                price = float(price)
                                category_total[category] = category_total.get(
                                    category, 0) + price
                            except ValueError:
                                st.warning(
                                    f"Invalid price value for item: {item}")

            # Ensure there is data to plot
            if not category_total:
                st.error("No valid category data to display.")
                return

            # Plotting the data
            labels = list(category_total.keys())
            sizes = list(category_total.values())

            fig, ax = plt.subplots(figsize=(10, 4))

            # Create a line chart without dots (no markers) and labels
            ax.plot(labels, sizes, color='blue', linestyle='-', linewidth=2)

            # Remove x-axis and y-axis labels
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_title('')  # Remove chart title if needed

            # Rotate x-axis labels for better readability
            plt.xticks(rotation=90)

            # Adjust layout for better readability
            plt.tight_layout()

            # Display the graph in Streamlit
            st.pyplot(fig)

            # Display the category totals as a table
            summary_df = pd.DataFrame(list(category_total.items()), columns=[
                                      'Category', 'Total Price'])
            st.table(summary_df)

        except Exception as e:
            st.error(f"An error occurred while generating the graph: {e}")
    else:
        st.error("Failed to connect to MongoDB. Collection not found.")
