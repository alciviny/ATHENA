"""
Middleware de Rate Limiting para FastAPI.
Protege a API contra abuso e sobrecarga.
"""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import asyncio

from brain.domain.exceptions import RateLimitExceededError
from brain.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Implementa rate limiting usando token bucket algorithm.
    
    Permite configurar:
    - Máximo de requisições por janela de tempo
    - Duração da janela
    - Rate limit por IP ou por user_id
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        cleanup_interval: int = 300
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        
        # Armazena: {identifier: [(timestamp1, timestamp2, ...)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
        
        logger.info(
            "RateLimiter inicializado",
            max_requests=max_requests,
            window_seconds=window_seconds
        )
    
    async def is_allowed(self, identifier: str) -> Tuple[bool, int, int]:
        """
        Verifica se a requisição pode passar.
        
        Args:
            identifier: IP ou user_id
            
        Returns:
            Tuple (allowed, remaining, reset_time)
            - allowed: Se a requisição pode passar
            - remaining: Requisições restantes
            - reset_time: Timestamp quando o limite reseta
        """
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove timestamps antigos
            self.requests[identifier] = [
                ts for ts in self.requests[identifier]
                if ts > cutoff
            ]
            
            request_count = len(self.requests[identifier])
            remaining = max(0, self.max_requests - request_count)
            
            if request_count >= self.max_requests:
                # Calcula quando o limite reseta (timestamp mais antigo + janela)
                oldest = min(self.requests[identifier])
                reset_time = int(oldest + self.window_seconds)
                
                logger.warning(
                    "Rate limit excedido",
                    identifier=identifier,
                    request_count=request_count,
                    max_requests=self.max_requests,
                    reset_in_seconds=reset_time - now
                )
                
                return False, 0, reset_time
            
            # Adiciona timestamp da requisição atual
            self.requests[identifier].append(now)
            return True, remaining - 1, int(now + self.window_seconds)
    
    async def cleanup_old_entries(self):
        """Remove entradas antigas periodicamente para economizar memória."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            
            async with self._lock:
                now = time.time()
                cutoff = now - self.window_seconds
                
                # Remove identifiers sem requisições recentes
                identifiers_to_remove = [
                    identifier
                    for identifier, timestamps in self.requests.items()
                    if not timestamps or max(timestamps) < cutoff
                ]
                
                for identifier in identifiers_to_remove:
                    del self.requests[identifier]
                
                if identifiers_to_remove:
                    logger.debug(
                        "Cleanup de rate limiter",
                        removed_count=len(identifiers_to_remove),
                        active_identifiers=len(self.requests)
                    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware do FastAPI que aplica rate limiting.
    
    Uso:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=100,
            window_seconds=60
        )
    """
    
    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        exempt_paths: list = None
    ):
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        
        # Inicia task de cleanup e salva referência
        self._cleanup_task = asyncio.create_task(self.limiter.cleanup_old_entries())
    
    async def dispatch(self, request: Request, call_next):
        """Processa cada requisição aplicando rate limiting."""
        
        # Pula rate limiting para rotas isentas
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Identifica o cliente (IP ou user_id do header)
        identifier = self._get_identifier(request)
        
        # Verifica rate limit
        allowed, remaining, reset_time = await self.limiter.is_allowed(identifier)
        
        if not allowed:
            retry_after = reset_time - int(time.time())
            
            logger.warning(
                "Requisição bloqueada por rate limit",
                identifier=identifier,
                path=request.url.path,
                method=request.method,
                retry_after=retry_after
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Limite de {self.limiter.max_requests} requisições por {self.limiter.window_seconds}s excedido",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Processa a requisição normalmente
        response = await call_next(request)
        
        # Adiciona headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """
        Extrai identificador único do cliente.
        Prioriza user_id, depois IP.
        """
        # Tenta pegar user_id do header (se tiver autenticação)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        
        # Senão, usa o IP
        # Considera proxies (X-Forwarded-For)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
