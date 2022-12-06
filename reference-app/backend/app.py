import logging

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from jaeger_client import Config
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"


def init_jaeger_tracer(service_name='backend_service'):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config = Config(config={
        'sampler': {
            'type': 'const',
            'param': 1,
        },
        'logging': True,
    },
        service_name=service_name,
        validate=True
    )
    return config.initialize_tracer()


tracer = init_jaeger_tracer()

mongo = PyMongo(app)
metrics = PrometheusMetrics(app, group_by='endpoint')


@app.route("/")
def homepage():
    with tracer.start_span('HomePage') as span:
        message = "Hello World"
        span.set_tag('message', message)
        return (message)


@app.route("/api")
def my_api():
    with tracer.start_span('API') as span:
        answer = "something"
        span.set_tag('message', answer)
    return jsonify(response=answer)


@app.route("/star", methods=["POST"])
def add_star():
    with tracer.start_span('star') as span:
        star = mongo.db.stars
        name = request.json["name"]
        distance = request.json["distance"]
        star_id = star.insert({"name": name, "distance": distance})
        new_star = star.find_one({"_id": star_id})
        output = {"name": new_star["name"], "distance": new_star["distance"]}
        span.set_tag('status', 'SUCCESS')
    return jsonify({"result": output})


if __name__ == "__main__":
    app.run()
