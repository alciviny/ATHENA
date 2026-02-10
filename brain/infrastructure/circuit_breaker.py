"""
Circuit Breaker Pattern implementation for AI service calls.
Previne sobrecarga de APIs externas e melhora resiliência do sistema.
"""

import time
import asyncio
import logging
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass, field

from brain.domain.exceptions import CircuitBreakerOpenError, AIServiceError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados possíveis do Circuit Breaker."""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Detectou falhas, rejeitando requisições
    HALF_OPEN = "half_open"  # Testando se o serviço voltou


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker."""
    failure_threshold: int = 5  # Número de falhas antes de abrir
    success_threshold: int = 2  # Sucessos necessários para fechar (em half-open)
    timeout: int = 60  # Segundos antes de tentar half-open
    expected_exceptions: tuple = (AIServiceError, TimeoutError, ConnectionError)


class CircuitBreaker:
    """
    Implementa o padrão Circuit Breaker para proteger chamadas a serviços externos.
    
    Estados:
    - CLOSED: Tudo funcionando, requisições passam normalmente
    - OPEN: Muitas falhas detectadas, rejeita requisições imediatamente
    - HALF_OPEN: Testando se o serviço voltou, permite algumas requisições
    
    Uso:
        breaker = CircuitBreaker(name="gemini_api", config=CircuitBreakerConfig())
        result = await breaker.call(async_function, *args, **kwargs)
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
        
        logger.info(
            f"[CircuitBreaker:{self.name}] Initialized - "
            f"threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout}s"
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa uma função protegida pelo circuit breaker.
        
        Args:
            func: Função async a ser executada
            *args, **kwargs: Argumentos da função
            
        Returns:
            Resultado da função
            
        Raises:
            CircuitBreakerOpenError: Se o circuit breaker estiver aberto
        """
        async with self._lock:
            self._check_state()
            
            if self.state == CircuitState.OPEN:
                logger.warning(
                    f"[CircuitBreaker:{self.name}] ⛔ OPEN - Rejeitando requisição. "
                    f"Retry em {self._time_until_half_open():.0f}s"
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' está aberto. "
                    f"Falhas consecutivas: {self.failure_count}. "
                    f"Tente novamente em {self._time_until_half_open():.0f}s",
                    provider=self.name,
                    retry_after=int(self._time_until_half_open())
                )
        
        try:
            logger.debug(f"[CircuitBreaker:{self.name}] Executando chamada...")
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.config.expected_exceptions as e:
            await self._on_failure()
            logger.error(
                f"[CircuitBreaker:{self.name}] ❌ Falha: {e.__class__.__name__} - {e}"
            )
            raise
        except Exception as e:
            # Exceções inesperadas não afetam o circuit breaker
            logger.error(
                f"[CircuitBreaker:{self.name}] 💥 Exceção inesperada: {e.__class__.__name__}"
            )
            raise
    
    def _check_state(self):
        """Verifica e atualiza o estado do circuit breaker."""
        if self.state == CircuitState.OPEN and self._should_attempt_reset():
            logger.info(f"[CircuitBreaker:{self.name}] 🔄 OPEN → HALF_OPEN")
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
    
    async def _on_success(self):
        """Callback executado após sucesso."""
        async with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.info(
                    f"[CircuitBreaker:{self.name}] ✅ Sucesso em HALF_OPEN "
                    f"({self.success_count}/{self.config.success_threshold})"
                )
                
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"[CircuitBreaker:{self.name}] 🟢 HALF_OPEN → CLOSED")
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
    
    async def _on_failure(self):
        """Callback executado após falha."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"[CircuitBreaker:{self.name}] 🔴 HALF_OPEN → OPEN")
                self.state = CircuitState.OPEN
                
            elif self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"[CircuitBreaker:{self.name}] 🔴 CLOSED → OPEN "
                    f"(Falhas: {self.failure_count})"
                )
                self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se já passou tempo suficiente para tentar half-open."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.config.timeout
    
    def _time_until_half_open(self) -> float:
        """Retorna segundos até o próximo teste."""
        if self.last_failure_time is None:
            return 0
        elapsed = time.time() - self.last_failure_time
        remaining = self.config.timeout - elapsed
        return max(0, remaining)
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "time_until_retry": self._time_until_half_open() if self.state == CircuitState.OPEN else 0
        }
    
    async def reset(self):
        """Reset manual do circuit breaker (para testes ou admin)."""
        async with self._lock:
            logger.info(f"[CircuitBreaker:{self.name}] 🔄 Manual reset")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
