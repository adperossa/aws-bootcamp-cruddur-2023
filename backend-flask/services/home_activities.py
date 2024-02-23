import json as jsonlib
from opentelemetry import trace
from lib.db import pool, query_wrap_array
import logging

LOGGER = logging.getLogger(__name__)

tracer = trace.get_tracer("service-home")


class HomeActivities:
    def run():
      with tracer.start_as_current_span("get-mock-homedata") as span:
          sql = query_wrap_array(
              """
    SELECT
      activities.uuid,
      users.display_name,
      users.handle,
      activities.message,
      activities.replies_count,
      activities.reposts_count,
      activities.likes_count,
      activities.reply_to_activity_uuid,
      activities.expires_at,
      activities.created_at
    FROM public.activities
    LEFT JOIN public.users ON users.uuid = activities.user_uuid
    ORDER BY activities.created_at DESC
    """
          )
          with pool.connection() as conn:
              with conn.cursor() as cur:
                  cur.execute(sql)
                  # this will return a tuple
                  # the first field being the data
                  json = cur.fetchone()
                  results = json[0]
                  span.set_attribute("results", jsonlib.dumps(results))
                  return results
