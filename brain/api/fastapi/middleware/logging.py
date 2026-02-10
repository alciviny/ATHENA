"""
Middleware de logging e trace ID para FastAPI.
Adiciona trace_id a todas as requisições e logs contextuais.
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

from brain.infrastructure.logging import set_trace_id, clear_context, get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    - Adiciona trace_id único a cada requisição
    - Loga início e fim de cada requisição com contexto
    - Mede tempo de resposta
    """
    
    async def dispatch(self, request: Request, call_next):
        # Gera ou extrai trace_id
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        set_trace_id(trace_id)
        
        # Adiciona trace_id ao state da request para uso em routes
        request.state.trace_id = trace_id
        
        start_time = time.time()
        
        logger.info(
            "Requisição recebida",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            logger.info(
                "Requisição concluída",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=round(duration, 3)
            )
            
            # Adiciona trace_id ao header da resposta
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.exception(
                "Erro ao processar requisição",
                method=request.method,
                path=request.url.path,
                duration_seconds=round(duration, 3),
                error_type=e.__class__.__name__
            )
            raise
        finally:
            # Limpa o contexto após a requisição
            clear_context()
