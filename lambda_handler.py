"""Lambda handler wrapping FastAPI with Mangum."""

from mangum import Mangum
from spokane_public_brief.api.main import app

handler = Mangum(app, lifespan="off")
