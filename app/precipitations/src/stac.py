import os
import json
import logging
from uuid import uuid4
from datetime import datetime

import pystac
import shapely
import click

# add and configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join("./", "stac-items")

logger.info("Creating output directory")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@click.command()
@click.option("--input_data", required=True, type=str)
def stac(input_data: str):
    logger.info("Importing data from the command line")
    import_data = json.loads(input_data)
    logger.info(f"Data imported: {import_data}")

    bbox = import_data["bbox"]
    logger.info(f"Bbox: {bbox}")
    logger.info(f"Bbox type: {type(bbox)}")

    layer = import_data["layer"]
    logger.info(f"Layer: {layer}")

    start_time = datetime.strptime(import_data["start_time"], "%Y-%m-%d %H:%M:%S")
    logger.info(f"Start time: {start_time}")

    end_time = datetime.strptime(import_data["end_time"], "%Y-%m-%d %H:%M:%S")
    logger.info(f"End time: {end_time}")
    
    # write STAC
    logger.info("Writing STAC")
    
    # get information from the environment
    job_information = json.loads(os.getenv("JOB_INFORMATION", ""))
    bucket = job_information["BUCKET"]
    workflow_id = os.getenv("WORKFLOW_ID", "")
    collection_id = os.getenv("COLLECTION_ID", str(uuid4()))
    
    # create bucket path
    assets_bucket_path = os.path.join(
        "s3://",
        bucket,
        "processing-results",
        workflow_id,
    )

    logger.info(f"Assets bucket path: {assets_bucket_path}")

    # create Collection
    logger.info("Creating collection")
    collection = pystac.Collection(
        id=collection_id,
        description="rain-forecast",
        title="Rain forecast",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([bbox]),
            temporal=pystac.TemporalExtent(intervals=[[start_time, end_time]]),
        ),
        href=os.path.join(assets_bucket_path, "collection.json"),
        stac_extensions=[],
        keywords=["DEC"],
        license="proprietary",
    )

    # create Catalog
    logger.info("Creating catalog")
    catalog = pystac.Catalog(id="catalog", description="rain-forecast")

    # Create Item
    logger.info("Creating item")
    p = shapely.box(*bbox)
    item_id = f"{layer}-{uuid4().hex[:8]}"
    item = pystac.Item(
        id=item_id,
        geometry={
            "type": "Point",
            "coordinates": p.centroid.coords[0]
        },
        bbox=bbox,
        datetime=start_time,
        href=os.path.join(assets_bucket_path, f"{item_id}.json"),
        properties={}
    )

    item.add_asset(
        key="probability_of_rain",
        asset=pystac.Asset(
            title="Probability of rain",
            href=os.path.join(assets_bucket_path, "probability_of_rain.png"),
            media_type=pystac.MediaType.PNG,
            roles=["data", "visual"]
        )
    )

    item.add_asset(
        key="predicted_profit",
        asset=pystac.Asset(
            title="Predicted profit",
            href=os.path.join(assets_bucket_path, "prediction.png"),
            media_type=pystac.MediaType.PNG,
            roles=["data", "visual"]
        )
    )

    item.add_asset(
        key="profit",
        asset=pystac.Asset(
            title="Profit",
            href=os.path.join(assets_bucket_path, "profit.csv"),
            media_type=pystac.MediaType.TEXT,
            roles=["data", "visual"]
        )
    )

    # add item to catalog
    catalog.add_item(item)

    for index, link in enumerate(catalog.links):
        if link.rel == "root":
            catalog.links.pop(index)

    for item in catalog.get_items():
        logger.info(f"Adding item {item.id} to collection {collection.id}")
        item.set_collection(collection)
        collection.add_item(item)

        for key, value in item.get_assets().items():
            item.add_asset(key, value)

    # collection.update_extent_from_items()
    catalog.clear_items()
    catalog.add_child(collection)
    logger.info("Normalizing catalog hrefs")
    catalog.normalize_hrefs(assets_bucket_path)
    collection.normalize_hrefs(assets_bucket_path)

    item_path = os.path.join(OUTPUT_DIR, item_id, f"{item.id}.json")
    logger.info(f"Writing item to {item_path}")
    pystac.write_file(item, dest_href=item_path)

    catalog_path = os.path.join(OUTPUT_DIR, "catalog.json")
    logger.info(f"Writing catalog to {catalog_path}")
    pystac.write_file(catalog, dest_href=catalog_path)

    collection_path = os.path.join(OUTPUT_DIR, "collection.json")
    logger.info(f"Writing collection to {collection_path}")
    pystac.write_file(collection, dest_href=collection_path)

    logger.info("Catalog created successfully")

if __name__ == "__main__":
    stac()