import { Router, Request, Response } from 'express';
import { studyService } from './study.service';
import { authMiddleware } from '../../middlewares/auth.middleware';
import { brainApi } from '../../infra/http/brain.api';

const router = Router();

router.post(
  '/generate',
  authMiddleware,
  async (req: Request, res: Response) => {
    try {
      const studentId = req.studentId!;

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
  authMiddleware,
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


