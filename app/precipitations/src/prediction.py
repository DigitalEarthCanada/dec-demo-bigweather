# Importation of Python modules
import json
from datetime import datetime, timedelta
import logging
import os

# The following modules must first be installed to use
# this code out of Jupyter Notebook
import matplotlib.pyplot as plt
import click

from utils import fig

# add and configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join("./", "plots")
TEMP_OUTPUT_DIR = os.path.join("./", "data")

logger.info("Creating output directory")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_OUTPUT_DIR, exist_ok=True)

@click.command()
@click.option("--input_data", required=True, type=str)
def main(input_data: str):
    logger.info("Importing data from the command line")
    logger.info(input_data)
    import_data = json.loads(input_data)
    logger.info(f"Data imported: {import_data}")

    local_time = [datetime.strptime(loc_time, "%Y-%m-%d %H:%M:%S") for loc_time in import_data["local_time"]]
    logger.info(f"Local time: {local_time} with length: {len(local_time)}")
    pixel_value =  import_data["pixel_value"]
    logger.info(f"Pixel value: {pixel_value} with length: {len(pixel_value)}")
    interval = import_data["interval"]
    logger.info(f"Interval: {interval}")

    # Umbrellas sold per day in average when there is less than 30%
    # chance that there will be a minimum of 5 mm of precipitations
    logger.info("Calculating the number of umbrellas sold per day")
    base = 3

    # Profits per umbrella
    logger.info("Calculating the profits per umbrella")
    umbrella_profit = 10.00

    # Slope calculation data
    # When the probability of precipitations is 30%...
    x1 = 30
    # ... 10 umbrellas are sold each hour
    y1 = 10
    # When the probability of precipitations is 100%...
    x2 = 100
    # ... 30 umbrellas are sold each hour
    y2 = 30

    # Slope calculation
    slope = (y2 - y1) / (x2 - x1)

    # Open hours
    opening = datetime.strptime("09:00:00", "%H:%M:%S")
    closing = datetime.strptime("21:00:00", "%H:%M:%S")
    logger.info(f"Opening hours: {opening} - Closing hours: {closing}")

    # Prediction times that are within the open hours
    open_hours = []
    for timestep in local_time:
        if timestep.time() > opening.time() and timestep.time() < closing.time():
            open_hours.append(timestep)

    # Number of umbrellas sold each day independently of meteorological conditions
    opening_interval = (opening + timedelta(hours=interval)).time()
    umbrella: list[int] = []
    logger.info("Calculating the number of umbrellas sold each day")
    for timestep in local_time:
        new_day = timestep.time() < opening_interval
        if (umbrella == [] or new_day) and timestep in open_hours:
            umbrella.append(base)
        else:
            umbrella.append(0)

    # Number of umbrellas sold and anticipated profits
    # depending on precipitations probability
    logger.info("Calculating the number of umbrellas sold and anticipated profits")
    cumulative_profit = []
    logger.info("Calculating the cumulative profits")
    for index, probability in enumerate(pixel_value):
        # Equation to calculate the number of umbrellas sold per hour
        eq = y1 + round((probability - 30) * slope)
        # Equation to calculate the number of umbrellas sold between 2 predictions
        eq2 = eq * interval
        if local_time[index] in open_hours and probability > 30:
            if index == 0:
                umbrella[index] = umbrella[index] + eq2
            else:
                umbrella[index] = umbrella[index] + umbrella[index - 1] + eq2
        elif index != 0:
            umbrella[index] = umbrella[index] + umbrella[index - 1]
        cumulative_profit.append(umbrella[index] * umbrella_profit)

    # Create and show plot
    logger.info("Creating and showing the plot")
    fig(
        x=local_time,
        y=pixel_value,
        title=(
            "Anticipated profits from umbrellas sales "
            + "depending\non precipitations probability"
        ),
        xlabel="\nDate and time",
        ylabel="Probability of getting 5 mm\nor more of precipitations (%)",
        ylim=(-10, 110),
        y2=cumulative_profit,
        y2label="Cumulative anticipated profits ($)",
    )

    plt.savefig(os.path.join(OUTPUT_DIR, "prediction.png"))
    logger.info("Plot saved")

    with open(os.path.join(TEMP_OUTPUT_DIR, "values.json"), "w") as file:
        json.dump(
            {
                "local_time": [loc_time.strftime("%Y-%m-%d %H:%M:%S") for loc_time in local_time] ,
                "pixel_value": pixel_value,
                "cumulative_profit": cumulative_profit,
                "open_hours": [hour.strftime("%Y-%m-%d %H:%M:%S") for hour in open_hours],
                "layer": import_data["layer"],
                "bbox": import_data["bbox"],
                "start_time": import_data["start_time"],
                "end_time": import_data["end_time"],
            },
            file,
        )

if __name__ == "__main__":
    main()
