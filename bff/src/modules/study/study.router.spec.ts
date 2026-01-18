import request from 'supertest';
import express from 'express';
import router from './study.router';
import jwt from 'jsonwebtoken';

const app = express();
app.use(express.json());
app.use('/study', router);

describe('Study Router Integration Tests', () => {
  const secret = process.env.JWT_SECRET as string;

  it('should return 401 if no token is provided', async () => {
    const response = await request(app).post('/study/generate');
    expect(response.status).toBe(401);
  });

  it('should return 500 (Brain Offline) if token is valid but brain is down', async () => {
    const token = jwt.sign({ sub: '123' }, secret);
    const response = await request(app)
      .post('/study/generate')
      .set('Authorization', `Bearer ${token}`);
    
    // Como o brainApi tentará chamar localhost:8000 e falhará
    expect(response.status).toBe(500);
    expect(response.body.error).toContain('Brain indisponível');
  });
});
