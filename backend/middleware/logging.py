# backend/middleware/logging.py
import uuid
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("mem-switch")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }

        try:
            response = await call_next(request)
            log_data["status"] = response.status_code
            logger.info(json.dumps(log_data))
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            log_data["error"] = str(e)
            logger.error(json.dumps(log_data))
            raise
