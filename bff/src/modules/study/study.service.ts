import { brainApi } from '../../infra/http/brain.api';
import { StudyPlanResponse } from '../../contracts/study.dto';

class StudyService {
  async generatePlan(studentId: string): Promise<StudyPlanResponse> {
    try {
      const { data } = await brainApi.post<StudyPlanResponse>(
        `/study/generate-plan/${studentId}`
      );

      return data;
    } catch (error: any) {
      console.error('[StudyService][generatePlan]', {
        studentId,
        message: error.message,
      });

      throw error;
    }
  }
}

export const studyService = new StudyService();
