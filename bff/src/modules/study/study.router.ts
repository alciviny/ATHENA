import { Router, Request, Response } from 'express';
import { studyService } from './study.service';
import { authMiddleware } from '../../middlewares/auth.middleware';

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

export default router;

