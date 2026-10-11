const number = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 });
export const formatNumber = (value: number | null | undefined) => value == null ? '—' : number.format(value);
export const formatPercent = (value: number | null | undefined) => value == null ? '—' : `${number.format(value)} %`;
export const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—';
