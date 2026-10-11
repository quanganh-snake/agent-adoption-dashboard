'use client';

import { useState } from 'react';
import { ChartCard, DataError, HorizontalToolBarChart, Loading, ToolsTimelineTable, YearBarChart } from '@/components/dashboard';
import { useSnapshot } from '@/lib/data';
import { AI_TOOLS_TIMELINE } from '@/lib/tools-timeline';
import type { Baseline, Yearly } from '@/lib/types';

type SnapshotSection = Record<string, unknown>;

const colors = ['#135f7a', '#438c58', '#b7791f', '#805ad5', '#c05621', '#718096'];

const TABS = [
  { id: 'all', label: 'Tất cả (Y1–Y8)' },
  { id: 'Y1', label: 'Y1. Tỷ lệ tiếp nhận' },
  { id: 'Y2', label: 'Y2. Adopter theo công cụ' },
  { id: 'Y3', label: 'Y3. Tỷ lệ commit AI' },
  { id: 'Y4', label: 'Y4. Kích thước commit' },
  { id: 'Y5', label: 'Y5. PR theo agent' },
  { id: 'Y6', label: 'Y6. Merge rate Agent/Human' },
  { id: 'Y7', label: 'Y7. Merge rate theo task' },
  { id: 'Y8', label: 'Y8. Toàn GitHub' },
];

function objectValue(section: SnapshotSection, key: string): Record<string, unknown> {
  const value = section[key];
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

function yearValue(value: unknown, year: number | string): number | null {
  if (value && typeof value === 'object') {
    const rec = value as Record<string, unknown>;
    const val = rec[String(year)] ?? rec[Number(year)];
    return typeof val === 'number' ? val : null;
  }
  return null;
}

export default function YearComparison() {
  const [activeTab, setActiveTab] = useState<string>('all');
  const [toolViewMode, setToolViewMode] = useState<'top' | 'all'>('top');
  const yearly = useSnapshot<Yearly>('yearly');
  const baseline = useSnapshot<Baseline>('baseline');

  if (yearly.error || baseline.error) return <DataError name="so sánh năm" />;
  if (!yearly.data || !baseline.data) return <Loading />;

  const y = yearly.data;
  const p2 = y.p2 as SnapshotSection;
  const p3 = y.p3 as SnapshotSection;
  const global = y.global as SnapshotSection;
  const years = y.years;

  const perKey = objectValue(p3, 'per_key');
  const tools = objectValue(p2, 'new_adopters_by_tool');
  const taskRates = objectValue(p3, 'task_merge_rate_pct');
  const created = objectValue(global, 'created');
  const sizeMedian = objectValue(p2, 'size_median');

  const namedData = (section: SnapshotSection, key: string) =>
    years.map((year) => ({
      year: String(year),
      ...Object.fromEntries(
        Object.entries(objectValue(section, key)).map(([name, values]) => [
          name,
          yearValue(values, year),
        ])
      ),
    }));

  const simple = (section: SnapshotSection, key: string, label: string) =>
    years.map((year) => ({
      year: String(year),
      [label]: yearValue(section[key], year),
    }));

  const commitSizeData = years.flatMap((year) =>
    ['AI', 'Human', 'Bot'].map((author) => {
      const yearStats = objectValue(sizeMedian, String(year));
      const authorStats = objectValue(yearStats, author);
      return {
        year: `${year} ${author}`,
        added: typeof authorStats.added === 'number' ? authorStats.added : null,
        deleted: typeof authorStats.deleted === 'number' ? authorStats.deleted : null,
        files: typeof authorStats.files === 'number' ? authorStats.files : null,
      };
    })
  );

  const taskRateData = years.map((year) => {
    const yearTasks = objectValue(taskRates, String(year));
    return {
      year: String(year),
      ...Object.fromEntries(
        Object.entries(yearTasks).map(([taskName, taskValues]) => {
          const agentVal = (taskValues as Record<string, unknown>)?.Agent;
          return [taskName, typeof agentVal === 'number' ? agentVal : null];
        })
      ),
    };
  });

  // Calculate tool rankings for horizontal bar chart
  const toolList = Object.entries(tools).map(([toolName, yearDict]) => {
    const counts = yearDict as Record<string, number>;
    const total = years.reduce((sum, yr) => sum + (counts[String(yr)] || 0), 0);
    return {
      tool: toolName,
      total,
      ...Object.fromEntries(years.map((yr) => [String(yr), counts[String(yr)] || 0])),
    };
  });

  toolList.sort((a, b) => b.total - a.total);
  const displayedTools = toolViewMode === 'top' ? toolList.slice(0, 10) : toolList;

  const show = (tabId: string) => activeTab === 'all' || activeTab === tabId;

  return (
    <>
      <header className="page-header">
        <h2>So sánh năm</h2>
        <p>So sánh 2024, 2025 và 2026 YTD đến {y.ytd_until}. Dữ liệu được đồng bộ và đối chiếu theo DOI của bài báo [2] và [3].</p>
      </header>

      <div className="subnav" role="tablist" aria-label="Bộ chọn biểu đồ năm">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className={activeTab === 'all' ? 'grid' : ''}>
        {show('Y1') && (
          <ChartCard
            title="Y1. Tỷ lệ tiếp nhận cuối năm"
            subtitle="Tỷ lệ repository có dấu vết AI coding agent theo bài báo [2] (DOI 10.1145/3822180)"
            sourceIds={['P2-06']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={simple(p2, 'adoption_rate_pct_year_end', 'Tỷ lệ tiếp nhận')}
              keys={[{ key: 'Tỷ lệ tiếp nhận', label: 'Tỷ lệ tiếp nhận (%)', color: colors[0] }]}
              reference={22.2}
            />
          </ChartCard>
        )}

        {show('Y2') && (
          <ChartCard
            title="Y2. Repo tiếp nhận mới theo công cụ"
            subtitle="Xếp hạng các công cụ có số repo tiếp nhận mới cao nhất theo năm từ artifact [2] (Zenodo 19256968)"
            sourceIds={['P2-07', 'P2-15']}
            references={baseline.data.references}
          >
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <button
                type="button"
                className={`tab-btn ${toolViewMode === 'top' ? 'active' : ''}`}
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.78rem' }}
                onClick={() => setToolViewMode('top')}
              >
                Top 10 phổ biến nhất
              </button>
              <button
                type="button"
                className={`tab-btn ${toolViewMode === 'all' ? 'active' : ''}`}
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.78rem' }}
                onClick={() => setToolViewMode('all')}
              >
                Tất cả ({toolList.length} công cụ)
              </button>
            </div>
            <HorizontalToolBarChart
              data={displayedTools}
              keys={years.map((yr, i) => ({
                key: String(yr),
                label: `Năm ${yr}`,
                color: colors[i % colors.length],
              }))}
            />
          </ChartCard>
        )}

        {show('Y2') && (
          <section className="card" style={{ gridColumn: activeTab === 'all' ? '1 / -1' : undefined }}>
            <header style={{ marginBottom: '0.75rem' }}>
              <h2>Thông tin thời gian ra mắt &amp; sử dụng của các AI Coding Agents</h2>
              <p className="muted">
                Tổng hợp thời điểm công bố chính thức, phân loại kiến trúc agent, mốc xuất hiện sớm nhất trong nghiên cứu [2] &amp; [3], cùng phương thức phát hiện dấu vết trên GitHub.
              </p>
            </header>
            <ToolsTimelineTable tools={AI_TOOLS_TIMELINE} />
          </section>
        )}

        {show('Y3') && (
          <ChartCard
            title="Y3. Tỷ lệ commit AI-assisted"
            subtitle="Tỷ trọng số commit có sự hỗ trợ của AI trên nhánh chính theo bài báo [2]"
            sourceIds={['P2-10']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={simple(p2, 'ai_commit_share_pct', 'AI-assisted')}
              keys={[{ key: 'AI-assisted', label: 'AI-assisted (%)', color: colors[1] }]}
            />
          </ChartCard>
        )}

        {show('Y4') && (
          <ChartCard
            title="Y4. Trung vị kích thước commit"
            subtitle="Trung vị số dòng thêm (added), dòng xóa (deleted), số file thay đổi theo tác giả (AI, Human, Bot) [2]"
            sourceIds={['P2-10', 'P2-11']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={commitSizeData}
              keys={[
                { key: 'added', label: 'Dòng thêm (added)', color: colors[0] },
                { key: 'deleted', label: 'Dòng xóa (deleted)', color: colors[2] },
                { key: 'files', label: 'Số file', color: colors[1] },
              ]}
            />
          </ChartCard>
        )}

        {show('Y5') && (
          <ChartCard
            title="Y5. Số PR agent theo agent"
            subtitle="Số pull request do từng coding agent tạo trong panel 2.807 repo theo bài báo [3] (DOI 10.1145/3805760.3814909)"
            sourceIds={['P3-02', 'P3-06']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={years.map((year) => ({
                year: String(year),
                ...Object.fromEntries(
                  Object.entries(perKey).map(([key, value]) => [
                    key,
                    yearValue((value as Record<string, unknown>)?.prs, year) ??
                      (value as Record<string, Record<string, unknown>>)?.[String(year)]?.prs ??
                      null,
                  ])
                ),
              }))}
              keys={Object.keys(perKey).map((key, i) => ({
                key,
                label: key,
                color: colors[i % colors.length],
              }))}
            />
          </ChartCard>
        )}

        {show('Y6') && (
          <ChartCard
            title="Y6. Merge rate Agent vs Human"
            subtitle="Tỷ lệ chấp nhận (merge rate) giữa PR do Agent và Human tạo ra qua các năm theo [3] (đường đỏ: mốc 71,5% bài báo)"
            sourceIds={['P3-06']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={years.map((year) => ({
                year: String(year),
                Agent:
                  (perKey?.Agent as Record<string, Record<string, number>>)?.[String(year)]
                    ?.merge_rate_pct ?? null,
                Human:
                  (perKey?.Human as Record<string, Record<string, number>>)?.[String(year)]
                    ?.merge_rate_pct ?? null,
              }))}
              keys={[
                { key: 'Agent', label: 'Agent (%)', color: colors[0] },
                { key: 'Human', label: 'Con người (%)', color: colors[1] },
              ]}
              reference={71.5}
            />
          </ChartCard>
        )}

        {show('Y7') && (
          <ChartCard
            title="Y7. Merge rate theo nhóm task"
            subtitle="Tỷ lệ merge của Agent theo 4 nhóm tác vụ (Docs & Style, Feature & Behavior, Infrastructure, Internal Quality) theo [3]"
            sourceIds={['P3-07']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={taskRateData}
              keys={['Docs & Style', 'Feature & Behavior', 'Infrastructure', 'Internal Quality'].map(
                (key, i) => ({
                  key,
                  label: key,
                  color: colors[i % colors.length],
                })
              )}
            />
          </ChartCard>
        )}

        {show('Y8') && (
          <ChartCard
            title="Y8. Toàn GitHub: PR theo agent"
            subtitle="Số PR tạo mới trên toàn bộ GitHub thu thập theo phương pháp bài báo [3] (DOI 10.1145/3805760.3814909, Zenodo 19098786) cho từng coding agent (thang log)"
            sourceIds={['P3-01', 'P3-02', 'P3-06']}
            references={baseline.data.references}
          >
            <YearBarChart
              data={namedData(global, 'created')}
              keys={Object.keys(created).map((key, i) => ({
                key,
                label: key,
                color: colors[i % colors.length],
              }))}
              log
            />
          </ChartCard>
        )}
      </div>
    </>
  );
}
