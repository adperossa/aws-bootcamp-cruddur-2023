import json as jsonlib
from opentelemetry import trace
from lib.db import db
import logging

LOGGER = logging.getLogger(__name__)

tracer = trace.get_tracer("service-home")


class HomeActivities:
    @staticmethod
    def run():
        with tracer.start_as_current_span("get-mock-homedata") as span:
            sql = db.template("activities", "home")
            results = db.query_array_json(sql)

            span.set_attribute("results", jsonlib.dumps(results))
            return results
