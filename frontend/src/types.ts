// ============================================================
// 类型定义
// ============================================================

export interface Scores {
  score_hard: number;
  score_project: number;
  score_level: number;
  score_salary: number;
  score_scale: number;
  score_growth: number;
  score_jd_match: number;
  total_score: number;
  location_bonus: number;
}

export interface StatusHistory {
  id: number;
  application_id: string;
  date: string;
  status: string;
  note: string;
}

export interface Application {
  id: string;
  date: string;
  company: string;
  position: string;
  salary_range: string;
  salary_min: number;
  salary_max: number;
  location: string;
  location_bonus: number;
  url: string;
  channel: string;
  resume_version: string;
  status: string;
  scores: Scores;
  verdict: string;
  job_type: string;
  jd_coverage: number;
  jd_hard_damage: string;
  jd_gaps: string;
  notes: string;
  research_core_business: string;
  research_tech_stack: string;
  research_team_features: string;
  research_match_advantages: string;
  research_weakness_strategy: string;
  status_history: StatusHistory[];
  last_updated: string;
  created_at: string;
}

export interface ApplicationListItem {
  id: string;
  date: string;
  company: string;
  position: string;
  salary_range: string;
  location: string;
  location_bonus: number;
  status: string;
  total_score: number;
  verdict: string;
  job_type: string;
  url: string;
}

export interface DashboardStats {
  total: number;
  active: number;
  interviewing: number;
  offered: number;
  rejected: number;
  by_status: Record<string, number>;
  by_verdict: Record<string, number>;
  by_location: Record<string, number>;
  top5: ApplicationListItem[];
}

export interface FunnelItem {
  name: string;
  value: number;
}

export const DIMENSIONS = [
  { key: 'score_hard', label: '硬能力匹配度' },
  { key: 'score_project', label: '项目经验契合度' },
  { key: 'score_level', label: '经验层级适配度' },
  { key: 'score_salary', label: '薪资期望适配度' },
  { key: 'score_scale', label: '企业规模适配度' },
  { key: 'score_growth', label: '成长空间适配度' },
  { key: 'score_jd_match', label: 'JD-能力匹配度' },
] as const;

export const STATUS_COLORS: Record<string, string> = {
  '已投递': '#1890ff',
  '已读': '#722ed1',
  '筛过': '#13c2c2',
  '笔试': '#fa8c16',
  '一面': '#eb2f96',
  '二面': '#eb2f96',
  '三面': '#eb2f96',
  'HR面': '#eb2f96',
  'Offer': '#52c41a',
  '入职': '#52c41a',
  '已拒': '#8c8c8c',
  '挂掉': '#f5222d',
};

export const VERDICT_COLORS: Record<string, string> = {
  '高度适配': '#52c41a',
  '中度适配': '#faad14',
  '不推荐投递': '#f5222d',
};
