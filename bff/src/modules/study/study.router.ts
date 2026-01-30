import { Router, Request, Response } from 'express';
import { studyService } from './study.service';
import { brainApi } from '../../infra/http/brain.api';

const router = Router();

// ... rota generate ...

router.post(
  '/review/:nodeId',
  async (req: Request, res: Response) => {
    try {
      const { nodeId } = req.params;
      const { grade, response_time_seconds } = req.body; 

      // ID fixo de testes (mesmo usado no generate)
      const studentId = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';

      // Mapeamento de Sucesso: Se grade > 1 (Não é "Again"), consideramos sucesso técnico
      const isSuccess = grade > 1;

      // Payload estrito conforme ReviewSchema do Python
      const payload = {
        student_id: studentId,
        success: isSuccess,
        response_time_seconds: response_time_seconds || 0,
        grade: grade // Enviando a nota explícita
      };

      console.log(`[BFF] Sending Review for Node ${nodeId}:`, payload);

      const response = await brainApi.post(`/study/review/${nodeId}`, payload);

      return res.json(response.data);
    } catch (error: any) {
      console.error('[BFF] Error recording review:', error.message);
      if (error.response) {
          console.error('[BFF] Brain Response:', error.response.data);
      }
      return res.status(500).json({ error: error.message });
    }
  }
);

export default router;


