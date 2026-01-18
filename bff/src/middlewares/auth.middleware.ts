import { Request, Response, NextFunction } from 'express';
import jwt, { JwtPayload } from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
  throw new Error('JWT_SECRET não definido');
}

interface AuthTokenPayload extends JwtPayload {
  sub: string;
}

export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      error: 'Token não fornecido',
    });
  }

  const [scheme, token] = authHeader.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({
      error: 'Formato de token inválido',
    });
  }

  try {
    const decoded = jwt.verify(
      token,
      JWT_SECRET!
    ) as AuthTokenPayload;

    req.studentId = decoded.sub;

    return next();
  } catch {
    return res.status(401).json({
      error: 'Token inválido ou expirado',
    });
  }
}
