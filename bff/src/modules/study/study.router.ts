import { Router, Request, Response } from 'express';
import { generateStudyPlan } from './study.service';
import { GeneratePlanRequest } from '../../contracts/study.dto';

const router = Router();

router.post('/generate-plan', async (req: Request, res: Response) => {
  try {
    const { studentId } = req.body as GeneratePlanRequest;

    // Validação básica
    if (!studentId) {
      return res.status(400).json({
        error: 'studentId is required',
      });
    }

    console.info(
      'BFF | generate-plan | request received',
      { studentId }
    );

    const studyPlan = await generateStudyPlan(studentId);

    console.info(
      'BFF | generate-plan | response received from Brain',
      { studentId }
    );

    return res.status(200).json(studyPlan);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unknown error';

    console.error(
      'BFF | generate-plan | failed',
      { error: message }
    );

    // Gateway / core service error
    return res.status(502).json({
      error: 'Error communicating with the core service.',
      details: message, // útil em dev; em prod pode remover
    });
  }
});

export default router;

