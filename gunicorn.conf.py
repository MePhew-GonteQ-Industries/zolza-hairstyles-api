from init_app import init_app


def on_starting(_server):
    init_app()
