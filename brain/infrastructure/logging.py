"""
Structured logging utilities for Athena.
Fornece logging contextual com trace IDs e metadata estruturada.
"""

import logging
import uuid
import json
from typing import Any, Optional
from contextvars import ContextVar
from datetime import datetime, timezone

# Context var para armazenar o trace_id da requisição atual
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredLogger:
    """
    Logger que adiciona contexto estruturado a todas as mensagens.
    
    Uso:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id=user.id, ip=request.ip)
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _build_message(self, message: str, **context) -> str:
        """Constrói mensagem com contexto estruturado."""
        trace_id = trace_id_var.get()
        user_id = user_id_var.get()
        
        structured_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": self.name,
            "message": message,
        }
        
        if trace_id:
            structured_data["trace_id"] = trace_id
        
        if user_id:
            structured_data["user_id"] = user_id
        
        # Adiciona contexto extra
        if context:
            structured_data["context"] = context
        
        return json.dumps(structured_data, ensure_ascii=False, default=str)
    
    def debug(self, message: str, **context):
        """Log de debug com contexto."""
        self.logger.debug(self._build_message(message, **context))
    
    def info(self, message: str, **context):
        """Log de info com contexto."""
        self.logger.info(self._build_message(message, **context))
    
    def warning(self, message: str, **context):
        """Log de warning com contexto."""
        self.logger.warning(self._build_message(message, **context))
    
    def error(self, message: str, **context):
        """Log de error com contexto."""
        self.logger.error(self._build_message(message, **context))
    
    def critical(self, message: str, **context):
        """Log critical com contexto."""
        self.logger.critical(self._build_message(message, **context))
    
    def exception(self, message: str, **context):
        """Log de exceção com stack trace e contexto."""
        self.logger.exception(self._build_message(message, **context))


def set_trace_id(trace_id: str = None):
    """Define o trace_id para a requisição atual."""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> Optional[str]:
    """Retorna o trace_id atual."""
    return trace_id_var.get()


def set_user_id(user_id: str):
    """Define o user_id para a requisição atual."""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Retorna o user_id atual."""
    return user_id_var.get()


def clear_context():
    """Limpa todo o contexto (útil entre requisições)."""
    trace_id_var.set(None)
    user_id_var.set(None)


# Função helper para criar loggers estruturados
def get_logger(name: str) -> StructuredLogger:
    """
    Cria um logger estruturado.
    
    Uso:
        from brain.infrastructure.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened", extra_data="value")
    """
    return StructuredLogger(name)
