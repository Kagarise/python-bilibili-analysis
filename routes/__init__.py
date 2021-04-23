from routes.api import api


def init_routes(app):
    app.register_blueprint(api)
