"""
main.py — Application entry point for local and production deployment.

Run with:
    python main.py
    OR
    uvicorn core.apis.api:app --host 0.0.0.0 --port 10000
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    is_dev = os.environ.get("ENV", "development").lower() == "development"
    uvicorn.run(
        "core.apis.api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        server_header=False,
    )
