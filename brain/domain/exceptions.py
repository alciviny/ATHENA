"""
Exceções customizadas do domínio Athena.
Todas as exceções específicas do sistema devem herdar de AthenaException.
"""


class AthenaException(Exception):
    """Exceção base para todas as exceções do sistema Athena."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ========================================
# Exceções de Domínio
# ========================================

class DomainException(AthenaException):
    """Exceção base para erros de lógica de domínio."""
    pass


class InvalidStudyPlanError(DomainException):
    """Lançada quando um plano de estudos é inválido ou inconsistente."""
    pass


class InsufficientDataError(DomainException):
    """Lançada quando não há dados suficientes para realizar uma operação."""
    pass


class NodeNotFoundError(DomainException):
    """Lançada quando um nó de conhecimento não é encontrado."""
    pass


class PrerequisiteNotMetError(DomainException):
    """Lançada quando pré-requisitos de um nó não foram cumpridos."""
    pass


# ========================================
# Exceções de Aplicação
# ========================================

class ApplicationException(AthenaException):
    """Exceção base para erros da camada de aplicação."""
    pass


class UseCaseError(ApplicationException):
    """Erro genérico em use cases."""
    pass


class ValidationError(ApplicationException):
    """Erro de validação de dados de entrada."""
    pass


# ========================================
# Exceções de Infraestrutura
# ========================================

class InfrastructureException(AthenaException):
    """Exceção base para erros de infraestrutura."""
    pass


class DatabaseError(InfrastructureException):
    """Erro relacionado ao banco de dados."""
    pass


class ConnectionError(InfrastructureException):
    """Erro de conexão com serviços externos."""
    pass


# ========================================
# Exceções de IA
# ========================================

class AIServiceError(InfrastructureException):
    """Exceção base para erros de serviços de IA."""
    
    def __init__(self, message: str, provider: str = None, retry_after: int = None, details: dict = None):
        self.provider = provider
        self.retry_after = retry_after
        details = details or {}
        if provider:
            details['provider'] = provider
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, details)


class AIQuotaExceededError(AIServiceError):
    """Lançada quando a cota de API de IA é excedida."""
    pass


class AITimeoutError(AIServiceError):
    """Lançada quando há timeout em chamada de IA."""
    pass


class AIInvalidResponseError(AIServiceError):
    """Lançada quando a resposta da IA é inválida ou não parseável."""
    pass


class AIModelNotFoundError(AIServiceError):
    """Lançada quando o modelo de IA especificado não existe."""
    pass


class CircuitBreakerOpenError(AIServiceError):
    """Lançada quando o circuit breaker está aberto (muitas falhas)."""
    pass


# ========================================
# Exceções de Vector Store
# ========================================

class VectorStoreError(InfrastructureException):
    """Erro relacionado ao vector store (Qdrant)."""
    pass


class EmbeddingError(VectorStoreError):
    """Erro ao gerar embeddings."""
    pass


# ========================================
# Exceções de API
# ========================================

class APIException(AthenaException):
    """Exceção base para erros de API."""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.status_code = status_code
        super().__init__(message, details)


class UnauthorizedError(APIException):
    """Erro de autenticação (401)."""
    
    def __init__(self, message: str = "Não autorizado", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(APIException):
    """Erro de autorização (403)."""
    
    def __init__(self, message: str = "Acesso negado", details: dict = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(APIException):
    """Recurso não encontrado (404)."""
    
    def __init__(self, message: str = "Recurso não encontrado", details: dict = None):
        super().__init__(message, status_code=404, details=details)


class RateLimitExceededError(APIException):
    """Limite de requisições excedido (429)."""
    
    def __init__(self, message: str = "Limite de requisições excedido", retry_after: int = 60, details: dict = None):
        self.retry_after = retry_after
        details = details or {}
        details['retry_after'] = retry_after
        super().__init__(message, status_code=429, details=details)
