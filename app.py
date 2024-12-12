import plotly.express as px
from shiny.express import render, input, ui
from shinywidgets import render_plotly
import pandas as pd

from functools import partial
from shiny.ui import page_navbar
import requests
import joblib
from collections import Counter
import os

channel_id = 2781405
api_key = "2W0KWOEEQQTX9J49"

# Determine the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths for resources
MODEL_PATH = os.path.join(BASE_DIR, "optimized_emg_classifier.pkl")

clf = joblib.load(MODEL_PATH)

shared_data = pd.DataFrame()

def fetch_thingspeak_data(channel_id, api_key, results=15):
    base_url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={api_key}"
    params = {"results": results}
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data["feeds"])  # Convert feeds to a DataFrame
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

# Define UI
ui.page_opts(
    title="Hangboard Training Support",  
    page_fn=partial(page_navbar, id="page"),  
)

# First Panel: Fetched Data
with ui.nav_panel("Fetched Data"):
    ui.h3("Monitor Your Progress")
    ui.p("Below, you can input your body weight and refresh data to see your hang performance.")
    ui.hr()  # Horizontal line for separation

    ui.input_slider("slider", "Body Weight (kg):", 1, 150, 60)
    ui.input_slider("number", "How many sessions do you want to display?:", 1, 10, 1)

    ui.hr()  # Add separation before the plot
    ui.h4("Time-Series Data")


    @render_plotly
    def data_display():
        global shared_data
        try:
            display_number = input.number()
            # Fetch data
            data = fetch_thingspeak_data(channel_id, api_key, results=15*display_number)
            
            # Convert to DataFrame and ensure numeric values
            data["field2"] = pd.to_numeric(data["field2"], errors="coerce")
            data["field5"] = pd.to_numeric(data["field5"], errors="coerce")
            
            # Check for valid data
            if data["field2"].isnull().all() or data["field5"].isnull().all():
                raise Exception("No valid data to plot.")
            
            body_weight = input.slider()

            data["percent_lifted"] = ((body_weight - data["field5"]) / body_weight) * 100
            shared_data = data

            # Plot the data using Plotly Express
            fig = px.line(
                data,
                x="field2",  
                y="percent_lifted",  
                markers=True,  # Show markers at data points
                title="% Body weight lifted over time",
                labels={"field2": "Time (s)", "percent_lifted": "% Body Weight Lifted"},
            )

            fig.update_layout(
                yaxis=dict(range=[0, data["percent_lifted"].max() + 10], autorange=False)
            )

            return fig
        except Exception as e:
            print(f"Error: {e}")
            # Return an empty figure with error text
            return px.line(title="Error fetching or plotting data")

# Second Panel: Tips and Improvement
with ui.nav_panel("Tips and Improvement"):
    ui.h3("Performance Feedback")
    ui.p("Input your max effort hang percentage and get tailored advice based on your performance.")
    ui.hr()  # Horizontal line for separation

    ui.input_slider("effort", "Max Effort Hang (% Body weight):", 1, 250, 60)

    ui.hr()  # Add separation before the feedback
    ui.h4("Feedback")

    @render.text
    def tips_tricks():
        global shared_data
        try:
            max_effort = input.effort()
            result_str = ""
            # Fetch data
            shared_data["field3"] = pd.to_numeric(shared_data["field3"], errors="coerce")
            shared_data["field4"] = pd.to_numeric(shared_data["field4"], errors="coerce")

            shared_data.dropna(subset=["field3", "field4"], inplace=True)

            # Prepare feature matrix
            features = shared_data[["field3", "field4"]].copy()  # Convert to NumPy array

            # Make predictions
            predictions = clf.predict(features)

            # Map predictions to human-readable labels
            class_map = {0: "Drag", 1: "Crimp"}
            predicted_labels = [class_map[pred] for pred in predictions]
            print(predicted_labels)

            # Count the most common prediction
            prediction_counts = Counter(predicted_labels)
            most_common_prediction, count = prediction_counts.most_common(1)[0]

            if "percent_lifted" in shared_data.columns:
                avg_percent_lifted = shared_data["percent_lifted"].mean()
                print(avg_percent_lifted)

            # Format the result
            if avg_percent_lifted > (0.4 * max_effort) and most_common_prediction == "Crimp":
                result_str = "Awesome effort! Your crimp is strong, but be weary that you are now crossing into max hang territory. Doing a long session with this effort may lead to finger injury, so be careful to listen to your body and its limits!"
            elif avg_percent_lifted < (0.4 * max_effort) and most_common_prediction == "Crimp":
                result_str = "Well done! Your crimp is slightly below the load required for optimal growth, but the effort is definitely something to be proud of! Give it slightly more for the next attempt!"
            elif avg_percent_lifted > (0.4 * max_effort) and most_common_prediction == "Drag":
                result_str = "Awesome effort! Your drag is strong, but be weary that you are now crossing into max hang territory. Doing a long session with this effort may lead to finger injury, so be careful to listen to your body and its limits!"
            elif avg_percent_lifted < (0.4 * max_effort) and most_common_prediction == "Drag":
                result_str = "Well done! Your drag is slightly below the load required for optimal growth, but the effort is definitely something to be proud of! Give it slightly more for the next attempt!"
            return result_str

        except Exception as e:
            print(f"Error: {e}")
            return "Error generating predictions. Check the console for details."
