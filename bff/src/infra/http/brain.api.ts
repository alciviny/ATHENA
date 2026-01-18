import axios, {
  AxiosInstance,
  AxiosError,
  AxiosResponse,
} from 'axios';

const BRAIN_API_URL =
  process.env.BRAIN_API_URL || 'http://localhost:8000';

export const brainApi: AxiosInstance = axios.create({
  baseURL: BRAIN_API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Interceptor de Response
 */
brainApi.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Tempo limite excedido ao comunicar com o Brain.');
    }

    if (!error.response) {
      throw new Error('Brain indisponível no momento.');
    }

    const status = error.response.status;

    if (status >= 500) {
      throw new Error('Erro interno no Brain.');
    }

    if (status === 404) {
      throw new Error('Recurso solicitado não encontrado no Brain.');
    }

    if (status === 401 || status === 403) {
      throw new Error('Acesso não autorizado ao Brain.');
    }

    throw new Error('Erro inesperado na comunicação com o Brain.');
  }
);
