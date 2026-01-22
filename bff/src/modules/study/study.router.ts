import { Router, Request, Response } from 'express';
import { studyService } from './study.service';
import { authMiddleware } from '../../middlewares/auth.middleware';
import { brainApi } from '../../infra/http/brain.api';

const router = Router();

router.post(
  '/generate',
  // authMiddleware,
  async (req: Request, res: Response) => {
    try {
      // Para fins de teste, usamos um ID fixo, já que o middleware foi desativado.
      const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

      const plan = await studyService.generatePlan(studentId);

      return res.json(plan);
    } catch (error: any) {
      return res.status(500).json({
        error: error.message,
      });
    }
  }
);

router.post(
  '/review/:nodeId',
  // authMiddleware,
  async (req: Request, res: Response) => {
    try {
      const { nodeId } = req.params;
      const { grade } = req.body; // AGAIN = 1, HARD = 2, GOOD = 3, EASY = 4

      // Chamada para o Brain (FastAPI)
      const response = await brainApi.post(`/study/review/${nodeId}`, { grade });

      return res.json(response.data);
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  }
);

export default router;


