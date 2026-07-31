import os
from typing import Any

from flask import Flask

from app.routes import main_bp
from app.storage import ensure_storage_files


def create_app(
    test_config: dict[str, Any] | None = None,
    rag_service: Any | None = None,
) -> Flask:
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

    if test_config:
        app.config.update(test_config)

    ensure_storage_files()

    if rag_service is not None:
        app.extensions["rag_service"] = rag_service
    else:
        # Import only when the real service is needed.
        # This prevents model loading during test collection.
        from app.rag import RAGService

        try:
            app.extensions["rag_service"] = RAGService()
            app.logger.info("RAG service initialized successfully.")
        except Exception:
            app.logger.exception("RAG service failed to initialize.")
            raise

    app.register_blueprint(main_bp)

    return app


if __name__ == "__main__":
    flask_app = create_app()

    debug_mode = (
        os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )

    flask_app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=debug_mode,
    )