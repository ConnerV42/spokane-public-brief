"""Lambda handler wrapping FastAPI with Mangum."""

import os
from mangum import Mangum
from spokane_public_brief.api.main import app

stage = os.environ.get("STAGE", "dev")
handler = Mangum(app, lifespan="off", api_gateway_base_path=f"/{stage}")
