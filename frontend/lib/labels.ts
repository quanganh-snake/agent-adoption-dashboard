export const taskLabels: Record<string, string> = { 'Feature & Behavior': 'Tính năng & hành vi', 'Docs & Style': 'Tài liệu & style', Infrastructure: 'Hạ tầng', 'Internal Quality': 'Chất lượng nội bộ' };
export const metricLabels: Record<string, string> = { Agent: 'Agent', Human: 'Con người', merge_rate_pct: 'Tỷ lệ merge', ttm_mean_h: 'Thời gian merge trung bình', ai_commit_share_pct: 'Tỷ lệ commit AI-assisted' };
export const monthLabel = (month: string) => `T${Number(month.slice(5))}/${month.slice(0, 4)}`;
export const navItems = [['/','Tổng quan'], ['/so-sanh-nam','So sánh năm'], ['/bang-2026','Bảng 2026'], ['/bai-bao','Bài báo'], ['/nguon-phuong-phap','Nguồn & phương pháp']] as const;
