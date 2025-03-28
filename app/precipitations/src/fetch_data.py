# Importation of Python modules
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import re
from typing import Union
import warnings
import logging
import os

# The following modules must first be installed to use
# this code out of Jupyter Notebook
import matplotlib.pyplot as plt
from owslib.wms import WebMapService
from owslib.map.wms130 import WebMapService_1_3_0
from owslib.map.wms111 import WebMapService_1_1_1
import click

from utils import fig

# Ignore warnings from the OWSLib module
warnings.filterwarnings("ignore", module="owslib", category=UserWarning)

# add and configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WMS = Union[WebMapService_1_3_0, WebMapService_1_1_1]

OUTPUT_DIR = os.path.join("./", "plots")
TEMP_OUTPUT_DIR = os.path.join("./", "data")

logger.info("Creating output directory")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_OUTPUT_DIR, exist_ok=True)


# Extraction of temporal information from metadata
def time_parameters(layer: str, wms: WMS) -> tuple[datetime, datetime, int]:
    start_time, end_time, interval = (
        wms[layer].dimensions["time"]["values"][0].split("/")
    )
    iso_format = "%Y-%m-%dT%H:%M:%SZ"
    start_time = datetime.strptime(start_time, iso_format)
    end_time = datetime.strptime(end_time, iso_format)
    interval = int(re.sub(r"\D", "", interval))
    return start_time, end_time, interval


# To use specific starting and ending time, remove the #
# from the next lines and replace the start_time and
# end_time with the desired values:
# start_time = 'YYYY-MM-DDThh:00'
# end_time = 'YYYY-MM-DDThh:00'
# fmt = '%Y-%m-%dT%H:%M'
# start_time = datetime.strptime(start_time, fmt) - timedelta(hours=time_zone)
# end_time = datetime.strptime(end_time, fmt) - timedelta(hours=time_zone)


@dataclass
class RequestInput:
    layer: str
    time: list[datetime]
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    wms: WMS

# Loop to carry out the requests and extract the probabilities
def request(input: RequestInput):
    info = []
    pixel_value = []
    for timestep in input.time:
        # WMS GetFeatureInfo query
        info.append(
            input.wms.getfeatureinfo(
                layers=[input.layer],
                srs="EPSG:4326",
                bbox=(input.min_x, input.min_y, input.max_x, input.max_y),
                size=(100, 100),
                format="image/jpeg",
                query_layers=[input.layer],
                info_format="text/plain",
                xy=(50, 50),
                feature_count=1,
                time=str(timestep.isoformat()) + "Z",
            )
        )
        # Probability extraction from the request's results
        text = info[-1].read().decode("utf-8")
        pixel_value.append(str(re.findall(r"value_0\s+\d*.*\d+", text)))
        pixel_value[-1] = float(
            re.sub("value_0 = '", "", pixel_value[-1]).strip('[""]')
        )

    return pixel_value


@click.command()
@click.option("--pos_x", type=str, help="X coordinate") 
@click.option("--pos_y", type=str, help="Y coordinate")
def main(pos_x: str, pos_y: str) -> None:
    # Parameters choice
    # Layer:
    layer = "REPS.DIAG.3_PRMM.ERGE5"
    logger.info(f"Layer: {layer}")

    # Coordinates: (from input)
    x = float(pos_x)  # -123.116
    y = float(pos_y)  # 49.288

    logger.info(f"Coordinates: {x}, {y}")

    # Local time zone (in this exemple, the local time zone is UTC-07:00):
    time_zone = -7
    logger.info(f"Local time zone: {time_zone}")

    # bbox parameter
    min_x, min_y, max_x, max_y = x - 0.25, y - 0.25, x + 0.25, y + 0.25

    logger.info(f"bbox: {min_x}, {min_y}, {max_x}, {max_y}")

    # WMS service connection
    logger.info("Connecting to the WMS service")
    wms = WebMapService(
        "https://geo.weather.gc.ca/geomet?SERVICE=WMS" + "&REQUEST=GetCapabilities",
        version="1.3.0",
        timeout=300,
    )

    start_time, end_time, interval = time_parameters(layer, wms)
    logger.info(f"Start time: {start_time}, End time: {end_time}, Interval: {interval}")

    # Calculation of date and time for available predictions
    logger.info("Calculating the date and time for available predictions")

    # (the time variable represents time at UTC±00:00)
    time = [start_time]
    local_time = [start_time + timedelta(hours=time_zone)]
    while time[-1] < end_time:
        time.append(time[-1] + timedelta(hours=interval))
        local_time.append(time[-1] + timedelta(hours=time_zone))

    request_input = RequestInput(
        layer=layer,
        time=time,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        wms=wms,
    )
    pixel_value = request(request_input)
    logger.info(f"Pixel value: {pixel_value}")

    # Add quantity of precipitations to the plot
    logger.info("Adding quantity of precipitations to the plot")
    # Verification of temporal parameters compatibility:
    start_time1, end_time1, interval1 = time_parameters(layer, wms)

    y2 = None
    y2label = None
    if start_time1 == start_time and end_time1 == end_time and interval1 == interval:
        # GetFeatureInfo request
        logger.info("GetFeatureInfo request")
        y2 = request(request_input)
        y2label = "Quantity of precipitations (mm)"

    # Create the plot with the fig function and show the plot
    logger.info("Creating the plot")
    logger.info(f"x: {local_time}")
    logger.info(f"y: {pixel_value}")
    logger.info(f"y2: {y2}")
    logger.info(f"y2label: {y2label}")
    fig(
        x=local_time,
        y=pixel_value,
        title=(
            "Probability of getting 5 mm or more of precipitations between"
            + f"\n{local_time[0]} and {local_time[-1]} (local time)"
        ),
        xlabel="\nDate and time",
        ylabel="Probability of getting 5 mm\nor more of precipitations (%)",
        ylim=(-10, 110),
        y2=y2,
        y2label=y2label,
    )

    logger.info("Saving the plot")
    plt.savefig(os.path.join(OUTPUT_DIR, "probability_of_rain.png"))

    logger.info("Plot saved")
    with open(os.path.join(TEMP_OUTPUT_DIR, "values.json"), "w") as file:
        json.dump(
            {
                "local_time": [
                    loc_time.strftime("%Y-%m-%d %H:%M:%S") for loc_time in local_time
                ],
                "pixel_value": pixel_value,
                "interval": interval,
                "layer": layer,
                "bbox": [min_x, min_y, max_x, max_y],
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            file,
        )
    


if __name__ == "__main__":
    main()
