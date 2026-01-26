import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import path from 'path';
import studyRouter from './modules/study/study.router';

const app = express();

// Habilita o CORS de forma mais permissiva para depuração
app.use(cors());

/*
// Configuração original mais restritiva
app.use(cors({
  origin: 'http://localhost:5173', // Permite apenas requisições deste domínio
  methods: ['GET', 'POST', 'PUT', 'DELETE'], // Métodos permitidos
  allowedHeaders: ['Content-Type', 'Authorization'], // Cabeçalhos permitidos
}));
*/

const PORT = Number(process.env.PORT) || 3000;

// ================= Middlewares =================

// Servir arquivos estáticos do diretório 'frontend'
// A requisição para '/' vai servir 'frontend/index.html'
app.use(express.static(path.join(__dirname, '../../frontend')));

// Parsing de JSON com limite (evita payload gigante)
app.use(express.json({ limit: '1mb' }));

// Log simples e consistente por requisição
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(
      `[${new Date().toISOString()}] ${req.method} ${req.originalUrl} ` +
      `${res.statusCode} - ${duration}ms`
    );
  });

  next();
});

// ================= Rotas =================

app.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({
    status: 'UP',
    service: 'BFF',
    timestamp: new Date().toISOString(),
  });
});

// Rotas do módulo de estudo
app.use('/api/study', studyRouter);

// ================= Error Handler Global =================

// Fallback de erro (não vaza stack)
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('Unhandled error:', err.message);

  res.status(500).json({
    error: 'Internal server error',
  });
});

// ================= Inicialização =================

app.listen(PORT, () => {
  console.log(`🚀 BFF Server running at http://localhost:${PORT}`);
});
