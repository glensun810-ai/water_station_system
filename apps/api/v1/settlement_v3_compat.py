"""
v3 settlement API compatibility bridge
The v3 settlement API uses water-specific services located in apps/water/services/.
This module adjusts sys.path so those imports work when running from the unified app.
"""

import sys
import os

# Ensure apps/water is on the path so water-specific services can be imported
_water_dir = os.path.join(os.path.dirname(__file__), "..", "..", "water")
if _water_dir not in sys.path:
    sys.path.insert(0, _water_dir)

# Import the v3 router and re-export it
from apps.water.api_settlement_v3 import router as v3_router  # noqa: E402

router = v3_router
