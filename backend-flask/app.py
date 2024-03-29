from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
from flask import got_request_exception
import os

# honeycomb telemetry
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# aws xray telemetry
# from aws_xray_sdk.core import xray_recorder
# from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
# cloudwatch logs
import watchtower
import logging
from time import strftime

# rollbar error logging
import rollbar
import rollbar.contrib.flask

# services
from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *
from services.users_short import *

# Helper libs
from lib.cognito_jwt_validator import cognito_auth_required

app = Flask(__name__)

# Initialize Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Initialize aws xray
# xray_url = os.getenv("AWS_XRAY_URL")
# xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)
# XRayMiddleware(app, xray_recorder)

# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
# cw_handler = watchtower.CloudWatchLogHandler(log_group="cruddur")
LOGGER.addHandler(console_handler)
# LOGGER.addHandler(cw_handler)

# cors
frontend = os.getenv("FRONTEND_URL")
backend = os.getenv("BACKEND_URL")
origins = [frontend, backend]
cors = CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    headers=["Content-Type", "Authorization"],
    expose_headers="Authorization",
    methods="OPTIONS,GET,HEAD,POST",
)


# routes
@app.route("/api/activities/home", methods=["GET"])
@cognito_auth_required
def data_home(claims):
    data = HomeActivities.run()
    return data, 200


@app.route("/api/activities", methods=["POST", "OPTIONS"])
@cross_origin()
@cognito_auth_required
def data_activities(claims):
    user_handle = claims["preferred_username"]
    message = request.json["message"]
    ttl = request.json["ttl"]
    model = CreateActivity.run(message, user_handle, ttl)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/notifications", methods=["GET"])
def data_notifications():
    data = NotificationsActivities.run()
    return data, 200


@app.route("/api/activities/search", methods=["GET"])
def data_search():
    term = request.args.get("term")
    model = SearchActivities.run(term)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities/@<string:handle>", methods=["GET"])
def data_handle(handle):
    model = UserActivities.run(handle)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/<string:activity_uuid>", methods=["GET"])
def data_show_activity(activity_uuid):
    data = ShowActivity.run(activity_uuid=activity_uuid)
    return data, 200


@app.route("/api/activities/<string:activity_uuid>/reply", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities_reply(activity_uuid):
    user_handle = "andrewbrown"
    message = request.json["message"]
    model = CreateReply.run(message, user_handle, activity_uuid)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/message_groups", methods=["GET"])
@cognito_auth_required
def data_message_groups(claims):
    cognito_user_id = claims["sub"]
    model = MessageGroups.run(cognito_user_id=cognito_user_id)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages/<string:message_group_uuid>", methods=["GET"])
@cognito_auth_required
def data_messages(message_group_uuid, claims):
    cognito_user_id = claims["sub"]
    model = Messages.run(
        cognito_user_id=cognito_user_id, message_group_uuid=message_group_uuid
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages", methods=["POST", "OPTIONS"])
@cross_origin()
@cognito_auth_required
def data_create_message(claims):
    message_group_uuid = request.json.get("message_group_uuid", None)
    user_receiver_handle = request.json.get("handle", None)
    message = request.json["message"]
    cognito_user_id = claims["sub"]

    if message_group_uuid is None:
        # Create for the first time
        model = CreateMessage.run(
            mode="create",
            message=message,
            cognito_user_id=cognito_user_id,
            user_receiver_handle=user_receiver_handle,
        )
    else:
        # Push onto existing Message Group
        model = CreateMessage.run(
            mode="update",
            message=message,
            message_group_uuid=message_group_uuid,
            cognito_user_id=cognito_user_id,
        )

    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/users/@<string:handle>/short", methods=["GET"])
def data_users_short(handle):
    data = UsersShort.run(handle)
    return data, 200


@app.route("/health", methods=["GET"])
def health():
    return "Healthy: OK"


@app.route("/rollbar/test")
def rollbar_test():
    rollbar.report_message("Hello World!", "warning")
    return "Hello World!"


# rollbar error logging
with app.app_context():
    rollbar_token = os.getenv("ROLLBAR_ACCESS_TOKEN")
    rollbar.init(
        # access token
        rollbar_token,
        # environment name
        "development",
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False,
    )

    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

if __name__ == "__main__":
    app.run()
