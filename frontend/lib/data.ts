'use client';

import useSWR from 'swr';

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? '';
export const DATA_BASE = process.env.NEXT_PUBLIC_DATA_BASE ?? `${basePath}/data`;
export const isApiData = process.env.NEXT_PUBLIC_DATA_BASE?.includes('/api/') ?? false;
const fetcher = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
};
export function useSnapshot<T>(name: string) {
  const url = name.startsWith('http') ? name : `${DATA_BASE}/${name}.json`;
  return useSWR<T>(url, fetcher, { refreshInterval: 60_000 });
}
