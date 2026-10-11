import type { Metadata } from 'next';
import './globals.css';
import { Navigation } from '@/components/dashboard';

export const metadata: Metadata = { title: 'Theo dõi tiếp nhận AI coding agent', description: 'Dashboard tái lập và theo dõi tiếp nhận AI coding agent' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="vi"><body><header className="site-header"><div><p className="eyebrow">TÁI LẬP NGHIÊN CỨU</p><h1>Tiếp nhận AI coding agent</h1></div><Navigation /></header><main>{children}</main><footer className="site-footer">Cập nhật lần cuối <FooterTimestamp /></footer></body></html>; }
function FooterTimestamp() { return <span id="generated-at">theo snapshot dữ liệu</span>; }
