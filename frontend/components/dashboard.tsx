'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatNumber, formatPercent } from '@/lib/format';
import { monthLabel, navItems } from '@/lib/labels';
import type { Baseline, Monthly2026, MonthlyRow, Reference, SyncJob } from '@/lib/types';
import type { ToolMetadata } from '@/lib/tools-timeline';

export function DataError({ name }: { name: string }) { return <p className="data-error">Không tải được dữ liệu {name}.</p>; }
export function Loading() { return <p className="muted">Đang tải dữ liệu…</p>; }
export function Navigation() { const pathname = usePathname(); return <nav aria-label="Điều hướng chính">{navItems.map(([href, label]) => <Link key={href} href={href} className={pathname === href ? 'active' : ''}>{label}</Link>)}</nav>; }
export function ChartCard({ title, subtitle, sourceIds = [], references = [], children }: { title: string; subtitle?: string; sourceIds?: string[]; references?: Reference[]; children: ReactNode }) { return <section className="card chart-card"><header><h2>{title}</h2>{subtitle ? <p>{subtitle}</p> : null}</header>{children}<SourceNote sourceIds={sourceIds} references={references} /></section>; }
export function SourceNote({ sourceIds, references }: { sourceIds: string[]; references: Reference[] }) { const referenceIds = new Set(sourceIds.map(id => id.startsWith('P2-') ? '2' : id.startsWith('P3-') ? '3' : id)); const matched = references.filter(reference => referenceIds.has(reference.id)); return <footer className="source-note">{matched.length ? matched.map(reference => <span key={reference.id}><strong>{sourceIds.join(', ')}</strong> {reference.text} {reference.doi_url ? <a href={reference.doi_url}>DOI</a> : null} {reference.code_url ? <a href={reference.code_url}>mã</a> : null} {reference.data_url ? <a href={reference.data_url}>dữ liệu</a> : null}</span>) : <span>Nguồn và phương pháp được ghi ở trang Nguồn &amp; phương pháp.</span>}</footer>; }
export function KpiCard({ label, value, detail }: { label: string; value: string; detail: string }) { return <article className="card kpi"><p>{label}</p><strong>{value}</strong><small>{detail}</small></article>; }
export function YearBarChart({ data, keys, reference, stacked = false, log = false }: { data: Record<string, string|number|null>[]; keys: { key: string; label: string; color: string }[]; reference?: number; stacked?: boolean; log?: boolean }) {
  const processedData = log
    ? data.map(row => ({
        ...row,
        ...Object.fromEntries(
          keys.map(k => {
            const val = row[k.key];
            return [k.key, typeof val === 'number' && val > 0 ? val : null];
          })
        )
      }))
    : data;
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={processedData}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="year" tickLine={false} />
          <YAxis scale={log ? 'log' : 'auto'} domain={log ? [1, 'auto'] : undefined} allowDataOverflow={log} />
          <Tooltip formatter={(value) => formatNumber(typeof value === 'number' ? value : null)} />
          <Legend />
          {reference != null ? <ReferenceLine y={reference} stroke="var(--danger)" strokeDasharray="5 5" /> : null}
          {keys.map(item => (
            <Bar key={item.key} dataKey={item.key} name={item.label} fill={item.color} stackId={stacked ? 'year' : undefined} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
export function HorizontalToolBarChart({ data, keys }: { data: Record<string, string|number|null>[]; keys: { key: string; label: string; color: string }[] }) {
  return (
    <div className="chart" style={{ height: Math.max(340, data.length * 34) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 90, bottom: 5 }}>
          <CartesianGrid horizontal={false} />
          <XAxis type="number" tickLine={false} />
          <YAxis dataKey="tool" type="category" tickLine={false} width={85} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value) => formatNumber(typeof value === 'number' ? value : null)} />
          <Legend />
          {keys.map((item) => (
            <Bar key={item.key} dataKey={item.key} name={item.label} fill={item.color} stackId="year" isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
export function ToolsTimelineTable({ tools }: { tools: ToolMetadata[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Công cụ / Agent</th>
            <th>Nhà phát triển</th>
            <th>Phân loại</th>
            <th>Thời gian ra mắt</th>
            <th>Mốc xuất hiện trong nghiên cứu</th>
            <th>Dấu vết nhận diện</th>
            <th>Mô tả &amp; Vai trò</th>
          </tr>
        </thead>
        <tbody>
          {tools.map((item) => (
            <tr key={item.id}>
              <th>
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.name}
                </a>
              </th>
              <td>{item.provider}</td>
              <td><span className="provisional" style={{ padding: '0.15rem 0.4rem', borderRadius: 4 }}>{item.category}</span></td>
              <td>{item.launchDate}</td>
              <td><strong>{item.firstSeenInStudy}</strong></td>
              <td><small>{item.detectionType}</small></td>
              <td style={{ textAlign: 'left', whiteSpace: 'normal', minWidth: 260 }}>{item.descriptionVi}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function MonthlyLineChart({ data, lines, paperValue, studyWindow }: { data: Record<string, string|number|null>[]; lines: { key: string; label: string; color: string }[]; paperValue?: number; studyWindow?: [string, string] }) { return <div className="chart"><ResponsiveContainer width="100%" height={320}><LineChart data={data}><CartesianGrid vertical={false} /><XAxis dataKey="month" tickFormatter={monthLabel} tickLine={false} /><YAxis /><Tooltip /><Legend />{studyWindow ? <ReferenceArea x1={studyWindow[0]} x2={studyWindow[1]} fill="var(--line)" fillOpacity={.5} /> : null}{paperValue != null ? <ReferenceLine y={paperValue} stroke="var(--danger)" strokeDasharray="5 5" /> : null}{lines.map(line => <Line key={line.key} type="monotone" dataKey={line.key} name={line.label} stroke={line.color} dot={false} isAnimationActive={false} connectNulls={false} />)}</LineChart></ResponsiveContainer></div>; }
export function MonthlyTable({ snapshot }: { snapshot: Monthly2026 }) { return <div className="table-wrap"><table><thead><tr><th>Chỉ số</th>{snapshot.months.map(month => <th key={month}>{monthLabel(month)}</th>)}<th>T1 → tháng gần nhất (Δ)</th></tr></thead><tbody>{snapshot.rows.map(row => <MonthlyRowView key={row.id} row={row} months={snapshot.months} />)}</tbody></table></div>; }
function MonthlyRowView({ row, months }: { row: MonthlyRow; months: string[] }) { const first = row.values[months[0]]; const last = row.values[months.at(-1) ?? '']; return <tr><th>{row.label_vi}<small>{row.unit}</small></th>{months.map(month => { const provisional = row.provisional.includes(month); const low = row.low_n.includes(month); const n = row.n[month]; return <td key={month} className={provisional ? 'provisional' : low ? 'low-n' : ''} title={provisional ? 'Chưa ổn định: PR tạo trong 30 ngày gần nhất' : low ? `Mẫu nhỏ (n=${formatNumber(n)})` : undefined}>{formatNumber(row.values[month])}</td>; })}<td>{first == null || last == null ? '—' : formatNumber(last - first)}</td></tr>; }
export function CompareTable({ title, rows }: { title: string; rows: Record<string, unknown>[] }) { if (!rows.length) return null; const fields = Object.keys(rows[0]).filter(key => !['paper', 'reproduced', 'latest'].includes(key)); const measures = Object.keys((rows[0].paper ?? {}) as Record<string, unknown>); return <section className="card"><h2>{title}</h2><div className="table-wrap"><table><thead><tr>{fields.map(field => <th key={field}>{field}</th>)}{measures.map(measure => <th key={`${measure}-paper`}>{measure}<small>Bài báo</small></th>)}{measures.map(measure => <th key={`${measure}-repro`}>{measure}<small>Tái lập dữ liệu gốc</small></th>)}{measures.map(measure => <th key={`${measure}-latest`}>{measure}<small>Mới nhất</small></th>)}{measures.map(measure => <th key={`${measure}-delta`}>Δ {measure}</th>)}</tr></thead><tbody>{rows.map((row, index) => { const paper = (row.paper ?? {}) as Record<string, number|null>; const reproduced = (row.reproduced ?? {}) as Record<string, number|null>; const latest = (row.latest ?? {}) as Record<string, number|null>; return <tr key={index}>{fields.map(field => <th key={field}>{String(row[field] ?? '')}</th>)}{measures.map(measure => <td key={`${measure}-paper`}>{formatNumber(paper[measure])}</td>)}{measures.map(measure => <td key={`${measure}-repro`}>{formatNumber(reproduced[measure])}</td>)}{measures.map(measure => <td key={`${measure}-latest`}>{formatNumber(latest[measure])}</td>)}{measures.map(measure => <td key={`${measure}-delta`}>{latest[measure] == null || paper[measure] == null ? '—' : formatNumber(latest[measure]! - paper[measure]!)}</td>)}</tr>; })}</tbody></table></div></section>; }
export function SyncStatus({ jobs, baseline }: { jobs?: SyncJob[]; baseline?: Baseline }) { const checks = baseline ? Object.values(baseline.checks).flat() : []; return <section className="card"><h2>Trạng thái đồng bộ</h2>{jobs?.length ? <ul>{jobs.slice(0, 8).map(job => <li key={job.id}><strong>{job.source}</strong> — {job.status} {job.message ? `: ${job.message}` : ''}</li>)}</ul> : <p className="muted">Trạng thái job chỉ hiển thị khi ứng dụng dùng API local.</p>}{checks.length ? <p>{checks.filter(check => check.deviation_flag).length ? 'Có chỉ số tái lập được gắn cờ LỆCH.' : 'Các kiểm tra tái lập hiện không có cờ LỆCH.'}</p> : null}</section>; }
export const asPercent = formatPercent;
