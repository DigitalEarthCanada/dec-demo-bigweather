# Importation of Python modules
import json
from datetime import datetime
import logging
import os

import pandas
import click


# add and configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join("./", "plots")

logger.info("Creating output directory")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@click.command()
@click.option("--input_data", required=True, type=str)
def main(input_data: str):
    logger.info("Importing data from the command line")

    import_data = json.loads(input_data)
    logger.info(f"Data imported: {import_data}")

    local_time = [
        datetime.strptime(loc_time, "%Y-%m-%d %H:%M:%S")
        for loc_time in import_data["local_time"]
    ]
    logger.info(f"Local time: {local_time} with length: {len(local_time)}")

    pixel_value = import_data["pixel_value"]
    logger.info(f"Pixel value: {pixel_value} with length: {len(pixel_value)}")

    open_hours = [datetime.strptime(open_hour, "%Y-%m-%d %H:%M:%S") for open_hour in import_data["open_hours"]]
    logger.info(f"Open hours: {open_hours}")

    cumulative_profit = import_data["cumulative_profit"]
    logger.info(f"Cumulative profit: {cumulative_profit}")
    
    # Probability of precipitations and cumulative
    # profits only within open hours
    probability = []
    profit = []
    for index, timestep in enumerate(local_time):
        if timestep in open_hours:
            probability.append(pixel_value[index])
            profit.append(cumulative_profit[index])

    # Create table
    profit_df = pandas.DataFrame(
        {
            "Local date and time": open_hours,
            "Probability (%)": probability,
            "Anticipated cumulative profits ($)": profit,
        }
    )

    # Show table
    logger.info(
        "Anticipated profits from umbrellas sales depending on precipitations probability"
    )

    # Save in CSV format (remove # from the following lines)
    logger.info("Saving table in CSV format")
    profit_df.to_csv(
        os.path.join(OUTPUT_DIR, "profit.csv"),
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    logger.info("Table saved")

if __name__ == "__main__":
    main()