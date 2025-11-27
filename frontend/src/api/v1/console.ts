/**
 * Console API Client (Viz.pdf仕様準拠)
 * Global Growth Console - 世界レベルの意思決定コンソール
 */
import { api } from '../../utils/api';
import type {
  DecisionConsoleSummary,
  WindowType
} from '../../types/console';

export const consoleAPI = {
  /**
   * Global Growth Console サマリー取得
   *
   * GET /api/console/summary
   *
   * @param window - 時間窓 ("14d" | "28d" | "56d")
   * @returns DecisionConsoleSummary
   */
  getSummary: async (window: WindowType = "28d"): Promise<DecisionConsoleSummary> => {
    const queryParams = new URLSearchParams({ window });
    return await api.get<DecisionConsoleSummary>(
      `/api/console/summary?${queryParams.toString()}`
    );
  },
};
