/**
 * Mock Backend API for Development
 * 
 * Provides complete mock responses for all API endpoints
 * to enable full UI functionality without a running backend
 */

// Decision Console Mock Data
export const mockConsoleSummary = {
  total_incremental_profit: 125000000,
  total_decisions: 342,
  active_policies: 28,
  avg_roi: 2.34,
  period_start: "2024-01-01",
  period_end: "2024-12-31"
};

export const mockDeltaYenHistory = [
  { date: "2024-01", delta_yen: 8500000, decision_count: 24 },
  { date: "2024-02", delta_yen: 9200000, decision_count: 28 },
  { date: "2024-03", delta_yen: 10100000, decision_count: 31 },
  { date: "2024-04", delta_yen: 9800000, decision_count: 29 },
  { date: "2024-05", delta_yen: 11200000, decision_count: 35 },
  { date: "2024-06", delta_yen: 10500000, decision_count: 32 }
];

export const mockVerdictDistribution = {
  adopt: 156,
  reject: 98,
  pending: 88
};

export const mockDecisionCards = [
  {
    id: "dc-001",
    title: "Email Campaign Optimization",
    policy_name: "Dynamic Discount Policy",
    decision_date: "2024-11-15",
    delta_yen: 2450000,
    roi: 3.2,
    verdict: "adopt",
    risk_score: 0.15,
    cas_score: 0.89,
    lcb95: 1850000
  },
  {
    id: "dc-002",
    title: "Retargeting Budget Allocation",
    policy_name: "Multi-touch Attribution",
    decision_date: "2024-11-14",
    delta_yen: 1890000,
    roi: 2.8,
    verdict: "adopt",
    risk_score: 0.22,
    cas_score: 0.84,
    lcb95: 1420000
  },
  {
    id: "dc-003",
    title: "Landing Page A/B Test",
    policy_name: "Conversion Rate Optimizer",
    decision_date: "2024-11-13",
    delta_yen: 3100000,
    roi: 4.1,
    verdict: "adopt",
    risk_score: 0.12,
    cas_score: 0.92,
    lcb95: 2650000
  },
  {
    id: "dc-004",
    title: "Social Media Ad Mix",
    policy_name: "Platform ROI Balance",
    decision_date: "2024-11-12",
    delta_yen: -450000,
    roi: 0.8,
    verdict: "reject",
    risk_score: 0.65,
    cas_score: 0.42,
    lcb95: -890000
  },
  {
    id: "dc-005",
    title: "Customer Segmentation",
    policy_name: "LTV-based Targeting",
    decision_date: "2024-11-11",
    delta_yen: 2780000,
    roi: 3.5,
    verdict: "adopt",
    risk_score: 0.18,
    cas_score: 0.87,
    lcb95: 2200000
  }
];

// Policy Lab Mock Data
const mockPolicies = [
  {
    id: "pol-001",
    name: "Dynamic Discount Policy",
    description: "Adaptive discount strategy based on customer LTV and purchase history",
    status: "completed",
    dataset_id: "ds-001",
    target_rule: "ltv > 100000 AND purchase_count > 3",
    channels: ["email", "app_push"],
    budget_limit: 5000000,
    created_at: "2024-10-01T10:00:00Z",
    updated_at: "2024-11-15T14:30:00Z"
  },
  {
    id: "pol-002",
    name: "Multi-touch Attribution",
    description: "Optimize marketing spend across multiple touchpoints",
    status: "completed",
    dataset_id: "ds-002",
    target_rule: "engagement_score > 0.7",
    channels: ["email", "display", "search"],
    budget_limit: 8000000,
    created_at: "2024-09-15T09:00:00Z",
    updated_at: "2024-11-14T16:20:00Z"
  },
  {
    id: "pol-003",
    name: "Conversion Rate Optimizer",
    description: "Maximize conversion through personalized offers",
    status: "completed",
    dataset_id: "ds-003",
    target_rule: "visit_frequency > 5 AND cart_abandon = true",
    channels: ["email", "web"],
    budget_limit: 3000000,
    created_at: "2024-08-20T11:00:00Z",
    updated_at: "2024-11-13T12:45:00Z"
  },
  {
    id: "pol-004",
    name: "Seasonal Campaign Strategy",
    description: "Seasonal promotion targeting high-value segments",
    status: "draft",
    dataset_id: "ds-001",
    target_rule: "season_affinity > 0.8",
    channels: ["email", "sms"],
    budget_limit: 2000000,
    created_at: "2024-11-10T08:00:00Z",
    updated_at: "2024-11-10T08:00:00Z"
  }
];

// Datasets Mock Data
const mockDatasets = [
  {
    id: "ds-001",
    name: "Email Campaign Data Q4 2024",
    uploaded_at: "2024-11-01",
    row_count: 125000,
    column_count: 24,
    size_mb: 45.2,
    status: "ready"
  },
  {
    id: "ds-002",
    name: "Web Traffic Analytics Oct 2024",
    uploaded_at: "2024-10-28",
    row_count: 890000,
    column_count: 32,
    size_mb: 156.8,
    status: "ready"
  },
  {
    id: "ds-003",
    name: "Customer Purchase History 2024",
    uploaded_at: "2024-10-15",
    row_count: 450000,
    column_count: 18,
    size_mb: 78.5,
    status: "ready"
  }
];

// Diagnostics Mock Data
export const mockDiagnostics = {
  balance_check: {
    status: "pass",
    max_smd: 0.08,
    threshold: 0.10,
    features_checked: ["age", "gender", "region", "ltv_segment"]
  },
  overlap_check: {
    status: "pass",
    common_support: 0.92,
    threshold: 0.85
  },
  sensitivity_analysis: {
    status: "warning",
    robust_range: [1850000, 2650000],
    point_estimate: 2450000
  },
  placebo_tests: {
    status: "pass",
    p_value: 0.68,
    threshold: 0.05
  }
};

// Experiment Design Mock Data
export const mockExperiments = [
  {
    id: "exp-001",
    name: "Landing Page Redesign Test",
    status: "running",
    start_date: "2024-11-10",
    end_date: "2024-11-24",
    sample_size: 50000,
    treatment_arms: ["control", "variant_a", "variant_b"],
    primary_metric: "conversion_rate",
    current_results: {
      control: { mean: 0.045, se: 0.002 },
      variant_a: { mean: 0.052, se: 0.002 },
      variant_b: { mean: 0.049, se: 0.002 }
    }
  },
  {
    id: "exp-002",
    name: "Email Send Time Optimization",
    status: "completed",
    start_date: "2024-10-15",
    end_date: "2024-11-01",
    sample_size: 80000,
    treatment_arms: ["morning", "afternoon", "evening"],
    primary_metric: "open_rate",
    current_results: {
      morning: { mean: 0.28, se: 0.015 },
      afternoon: { mean: 0.32, se: 0.016 },
      evening: { mean: 0.24, se: 0.014 }
    }
  }
];

// Portfolio & ROI Mock Data
export const mockPortfolio = {
  total_investment: 125000000,
  total_return: 292500000,
  roi: 2.34,
  roi_by_channel: [
    { channel: "email", investment: 35000000, return: 91000000, roi: 2.6 },
    { channel: "display", investment: 48000000, return: 110400000, roi: 2.3 },
    { channel: "search", investment: 42000000, return: 91140000, roi: 2.17 }
  ],
  pareto_frontier: [
    { risk: 0.1, return: 2.1 },
    { risk: 0.15, return: 2.34 },
    { risk: 0.2, return: 2.52 },
    { risk: 0.25, return: 2.65 },
    { risk: 0.3, return: 2.71 }
  ]
};

// Admin Mock Data
export const mockUsers = [
  {
    id: "user-001",
    email: "admin@cqox.local",
    name: "Admin User",
    roles: ["admin", "analyst"],
    created_at: "2024-01-01",
    last_login: "2024-11-16"
  },
  {
    id: "user-002",
    email: "analyst@cqox.local",
    name: "Data Analyst",
    roles: ["analyst"],
    created_at: "2024-02-15",
    last_login: "2024-11-15"
  },
  {
    id: "user-003",
    email: "viewer@cqox.local",
    name: "Viewer User",
    roles: ["viewer"],
    created_at: "2024-03-20",
    last_login: "2024-11-14"
  }
];

export const mockAuditLogs = [
  {
    id: "log-001",
    timestamp: "2024-11-16T10:30:00Z",
    user: "admin@cqox.local",
    action: "policy.create",
    resource: "Dynamic Discount Policy",
    status: "success"
  },
  {
    id: "log-002",
    timestamp: "2024-11-16T09:15:00Z",
    user: "analyst@cqox.local",
    action: "dataset.upload",
    resource: "Email Campaign Data Q4 2024",
    status: "success"
  },
  {
    id: "log-003",
    timestamp: "2024-11-16T08:45:00Z",
    user: "admin@cqox.local",
    action: "user.update",
    resource: "analyst@cqox.local",
    status: "success"
  }
];

// Helper function to simulate API delay
export const delay = (ms: number = 300) => 
  new Promise(resolve => setTimeout(resolve, ms));

// Mock API functions
export const mockBackend = {
  // Console APIs
  getConsoleSummary: async () => {
    await delay();
    return mockConsoleSummary;
  },
  
  getDeltaYenHistory: async (_period: string = "week") => {
    await delay();
    return mockDeltaYenHistory;
  },

  getVerdictDistribution: async (_period: string = "week") => {
    await delay();
    return mockVerdictDistribution;
  },
  
  getDecisionCards: async () => {
    await delay();
    return mockDecisionCards;
  },
  
  // Policy APIs
  getPolicies: async () => {
    await delay();
    return mockPolicies;
  },
  
  getPolicy: async (id: string) => {
    await delay();
    return mockPolicies.find(p => p.id === id) || mockPolicies[0];
  },
  
  createPolicy: async (data: any) => {
    await delay();
    return {
      id: `pol-${Date.now()}`,
      ...data,
      status: "active",
      created_at: new Date().toISOString()
    };
  },
  
  // Dataset APIs
  getDatasets: async () => {
    await delay();
    return mockDatasets;
  },
  
  getDataset: async (id: string) => {
    await delay();
    return mockDatasets.find(d => d.id === id) || mockDatasets[0];
  },
  
  uploadDataset: async (file: File) => {
    await delay(1000);
    return {
      id: `ds-${Date.now()}`,
      name: file.name,
      uploaded_at: new Date().toISOString(),
      row_count: Math.floor(Math.random() * 1000000),
      column_count: Math.floor(Math.random() * 50),
      size_mb: (file.size / 1024 / 1024).toFixed(1),
      status: "ready"
    };
  },
  
  // Diagnostics APIs
  getDiagnostics: async (_datasetId: string) => {
    await delay();
    return mockDiagnostics;
  },
  
  // Experiment APIs
  getExperiments: async () => {
    await delay();
    return mockExperiments;
  },
  
  getExperiment: async (id: string) => {
    await delay();
    return mockExperiments.find(e => e.id === id) || mockExperiments[0];
  },
  
  createExperiment: async (data: any) => {
    await delay();
    return {
      id: `exp-${Date.now()}`,
      ...data,
      status: "draft",
      created_at: new Date().toISOString()
    };
  },
  
  // Portfolio APIs
  getPortfolio: async () => {
    await delay();
    return mockPortfolio;
  },
  
  // Admin APIs
  getUsers: async () => {
    await delay();
    return mockUsers;
  },
  
  getAuditLogs: async () => {
    await delay();
    return mockAuditLogs;
  }
};

export default mockBackend;
export { mockPolicies, mockDatasets };

