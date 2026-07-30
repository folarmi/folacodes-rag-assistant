import os

from flask import Flask

from app.rag import RAGService
from app.routes import main_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config.update(
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    try:
        app.extensions["rag_service"] = RAGService()
        app.logger.info("RAG service initialized successfully.")
    except Exception:
        app.logger.exception("RAG service failed to initialize.")
        raise

    app.register_blueprint(main_bp)

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=debug_mode,
    )