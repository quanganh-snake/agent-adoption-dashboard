export interface ToolMetadata {
  id: string;
  name: string;
  provider: string;
  category: 'Autonomous Agent' | 'Agentic IDE / Editor' | 'CLI Agent' | 'Code Review Agent' | 'Assistant / Extension';
  launchDate: string; // YYYY-MM hoặc công bố chính thức
  firstSeenInStudy: string; // Mốc xuất hiện sớm nhất trong artifact nghiên cứu [2] & [3]
  detectionType: 'Commit & File' | 'PR Author / App' | 'PR Head Branch' | 'Co-Author Trailer';
  url: string;
  descriptionVi: string;
}

export const AI_TOOLS_TIMELINE: ToolMetadata[] = [
  {
    id: 'github-copilot',
    name: 'GitHub Copilot / Copilot SWE',
    provider: 'GitHub / Microsoft',
    category: 'Autonomous Agent',
    launchDate: '06/2021 (Preview) / 09/2025 (SWE Agent)',
    firstSeenInStudy: 'T1/2025 (P2) / T3/2025 (P3)',
    detectionType: 'Commit & File',
    url: 'https://github.com/features/copilot',
    descriptionVi: 'Trợ lý lập trình AI tiên phong; mở rộng thành Copilot Workspace và Copilot SWE Agent tích hợp tự động vào Pull Request.'
  },
  {
    id: 'openai-codex',
    name: 'OpenAI Codex',
    provider: 'OpenAI',
    category: 'Autonomous Agent',
    launchDate: '08/2021 (API) / T5/2025 (Codex Agent)',
    firstSeenInStudy: 'T5/2025 (P2 & P3)',
    detectionType: 'PR Head Branch',
    url: 'https://openai.com/codex',
    descriptionVi: 'Mô hình nền tảng dịch ngôn ngữ tự nhiên thành mã; trong nghiên cứu [3] là nhóm agent tạo số lượng PR lớn nhất (nhánh codex/).'
  },
  {
    id: 'devin',
    name: 'Devin',
    provider: 'Cognition AI',
    category: 'Autonomous Agent',
    launchDate: '03/2024 (Công bố) / 12/2024 (Enterprise)',
    firstSeenInStudy: 'T12/2024 (P3) / T1/2025 (P2)',
    detectionType: 'PR Author / App',
    url: 'https://devin.ai/',
    descriptionVi: 'Kỹ sư phần mềm AI tự trị đầu tiên thế giới, tự động giải quyết issue, viết test và tạo pull request hoàn chỉnh.'
  },
  {
    id: 'cursor',
    name: 'Cursor',
    provider: 'Anysphere',
    category: 'Agentic IDE / Editor',
    launchDate: '03/2023 (Ra mắt) / 08/2024 (Composer agentic)',
    firstSeenInStudy: 'T2/2025 (P3) / T5/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://cursor.com/',
    descriptionVi: 'IDE phân nhánh từ VS Code hỗ trợ lập trình agentic đa file qua tính năng Composer và điều hướng codebase sâu.'
  },
  {
    id: 'claude-code',
    name: 'Claude Code',
    provider: 'Anthropic',
    category: 'CLI Agent',
    launchDate: '02/2025 (CLI Preview) / 10/2024 (Computer Use)',
    firstSeenInStudy: 'T1/2025 (P2) / T2/2025 (P3)',
    detectionType: 'Co-Author Trailer',
    url: 'https://claude.com/product/claude-code',
    descriptionVi: 'Agent chạy trên dòng lệnh đầu cuối (terminal), tự đọc dự án, chỉnh sửa file, chạy bash/git test và tạo PR.'
  },
  {
    id: 'google-jules',
    name: 'Google Jules',
    provider: 'Google Labs',
    category: 'Autonomous Agent',
    launchDate: '12/2024 (Experimental) / 03/2025 (Public Preview)',
    firstSeenInStudy: 'T3/2025 (P2)',
    detectionType: 'PR Author / App',
    url: 'https://jules.google/',
    descriptionVi: 'AI coding agent của Google tích hợp trực tiếp vào GitHub workspace để xử lý bug, nâng cấp thư viện và refactor.'
  },
  {
    id: 'coderabbit',
    name: 'CodeRabbit',
    provider: 'CodeRabbit AI',
    category: 'Code Review Agent',
    launchDate: '07/2023',
    firstSeenInStudy: 'T1/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://coderabbit.ai/',
    descriptionVi: 'Agent chuyên trách review mã nguồn tự động, tóm tắt PR, phát hiện lỗi bảo mật và đưa ra các đề xuất commit chỉnh sửa.'
  },
  {
    id: 'aider',
    name: 'Aider',
    provider: 'Paul Gauthier / Open Source',
    category: 'CLI Agent',
    launchDate: '05/2023',
    firstSeenInStudy: 'T1/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://aider.chat/',
    descriptionVi: 'Công cụ lập trình cặp (pair programming) AI dòng lệnh mã nguồn mở hàng đầu, tự động commit git kèm thông điệp chuẩn.'
  },
  {
    id: 'gemini-code-assist',
    name: 'Gemini Code Assist',
    provider: 'Google Cloud',
    category: 'Assistant / Extension',
    launchDate: '04/2024',
    firstSeenInStudy: 'T3/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://cloud.google.com/gemini/docs/codeassist',
    descriptionVi: 'Bộ công cụ AI hỗ trợ lập trình của Google tích hợp trên VS Code, JetBrains và Cloud Workstations.'
  },
  {
    id: 'openhands',
    name: 'OpenHands (trước là OpenDevin)',
    provider: 'All-Hands-AI / Open Source',
    category: 'Autonomous Agent',
    launchDate: '03/2024',
    firstSeenInStudy: 'T1/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://github.com/All-Hands-AI/OpenHands',
    descriptionVi: 'Nền tảng agent kỹ sư phần mềm nguồn mở chạy trên container Docker, tự thực thi lệnh bash và chỉnh sửa repo.'
  },
  {
    id: 'sourcery',
    name: 'Sourcery',
    provider: 'Sourcery Technologies',
    category: 'Code Review Agent',
    launchDate: '2019 / 2023 (LLM Extension)',
    firstSeenInStudy: 'T1/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://sourcery.ai/',
    descriptionVi: 'Công cụ tái cấu trúc và đánh giá chất lượng mã nguồn tự động, tích hợp đề xuất dọn dẹp mã và tối ưu hiệu năng.'
  },
  {
    id: 'amp',
    name: 'Sourcegraph Amp / Cody',
    provider: 'Sourcegraph',
    category: 'Assistant / Extension',
    launchDate: '07/2023',
    firstSeenInStudy: 'T7/2025 (P2)',
    detectionType: 'Commit & File',
    url: 'https://sourcegraph.com/cody',
    descriptionVi: 'Trợ lý mã nguồn hiểu ngữ cảnh toàn bộ kho mã của Sourcegraph thông qua công nghệ đồ thị mã (Code Graph).'
  }
];
