/**
 * TypeScript types for Decision Console API (Viz.pdf仕様準拠)
 * Global Growth Console - 世界レベルの意思決定コンソール
 *
 * Matches backend Pydantic models in cqox/api/models/console.py
 */

/**
 * Global Summary KPIs
 */
export interface GlobalSummary {
  total_delta_yen: number;           // Total incremental profit (Δ¥)
  avg_delta_yen_per_policy: number;  // Average Δ¥ per policy
  mean_cas: number;                   // Mean Causal Assurance Score
  cvar_worst10: number;               // CVaR (worst 10%)
  budget_used: number;                // Total budget used
  budget_plan?: number;               // Planned budget (optional)
}

/**
 * Δ¥ Trend Point (weekly)
 */
export interface DeltaTrendPoint {
  week_label: string;        // ISO week format: "2025-W48"
  delta_yen: number;         // Total Δ¥ for this week
  go_delta_yen: number;      // Δ¥ from Go policies
  canary_delta_yen: number;  // Δ¥ from Canary policies
  hold_delta_yen: number;    // Δ¥ from Hold policies
}

/**
 * BCG Matrix quadrant type
 */
export type BCGQuadrant = "Star" | "Volume" | "Niche" | "Low";

/**
 * Segment Opportunity Map - Bubble Chart Point
 */
export interface SegmentBubble {
  segment_id: string;
  name: string;
  incremental_clv: number;   // Incremental CLV per user
  user_count: number;        // Segment population
  total_delta_yen: number;   // Total Δ¥ from policies targeting this segment
  mean_cas: number;          // Mean CAS for this segment
  bcg_quadrant: BCGQuadrant; // BCG Matrix quadrant
}

/**
 * Channel Performance Point
 */
export interface ChannelPoint {
  channel: string;
  total_delta_yen: number;
  risk: number;              // Risk score / CVaR
  mean_cas: number;
}

/**
 * Verdict type (Go/Canary/Hold)
 */
export type Verdict = "go" | "canary" | "hold";

/**
 * Decision Card - Individual Policy Decision
 */
export interface DecisionCard {
  policy_id: string;
  policy_name: string;
  dataset: string;
  channel: string | null;
  segment_label: string | null;
  delta_yen: number;
  roi: number;
  cas: number;
  risk: number;
  verdict: Verdict;
  period_start: string;      // ISO datetime string
  period_end: string;        // ISO datetime string
}

/**
 * GET /api/v1/console/summary response
 */
export interface DecisionConsoleSummary {
  window: {
    start: string;           // ISO date string
    end: string;             // ISO date string
  };
  kpis: GlobalSummary;
  trend: DeltaTrendPoint[];
  segment_portfolio: SegmentBubble[];
  channel_performance: ChannelPoint[];
  decision_cards: DecisionCard[];
}

/**
 * Window parameter type
 */
export type WindowType = "14d" | "28d" | "56d";
