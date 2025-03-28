from uuid import uuid4
from datetime import datetime

import pystac
import shapely

# From parameters, construct STAC
# Layer:
layer = 'REPS.DIAG.3_PRMM.ERGE5'
# Coordinates:
y, x = 49.288, -123.116
# Local time zone (in this exemple, the local time zone is UTC-07:00):
time_zone = -7

start_time = datetime.strptime('2024-05-13 15:00:00', '%Y-%m-%d %H:%M:%S')
p = shapely.Polygon([[x, y], [x, y], [x, y], [x, y]])

item = pystac.Item(
    id=f"{layer}-{uuid4().hex[:8]}",
    geometry={
        "type": "Point",
        "coordinates": [x, y]
    },
    bbox=shapely.bounds(p).tolist(),
    datetime=start_time,
    properties={}
)

item.add_asset(
    key="precipitation",
    asset=pystac.Asset(
        href="s3://ws-bob/processing-results/<job_id>/probability_of_rain.png",
        media_type=pystac.MediaType.PNG
    )
)

print(item.to_dict())