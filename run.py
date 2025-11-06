import os
from app import create_app


def get_config_name() -> str:
    return os.getenv("FLASK_ENV", "development").lower()


app = create_app(get_config_name())


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    # Development server only. Use a production WSGI server for deployment.
    app.run(debug=debug, host=host, port=port)
