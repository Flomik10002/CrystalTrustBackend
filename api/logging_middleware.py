import logging

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("crystal")

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        logger.info(
            f"Request: {request.method} {request.url} | Headers: {dict(request.headers)} | Body: {body.decode(errors='ignore')}"
        )
        try:
            response: Response = await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            raise

        logger.info(
            f"Response: {request.method} {request.url} | Status: {response.status_code} | Headers: {dict(response.headers)}"
        )
        return response
