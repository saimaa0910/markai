import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/providers';
import { BrandConfig } from '@/components/ui/brand-config';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: `${BrandConfig.name} — ${BrandConfig.tagline}`,
  description: BrandConfig.description,
  keywords: [
    'AI marketing platform',
    'marketing operating system',
    'AI agents marketing',
    'campaign automation',
    'content generation AI',
    'CRM AI',
    'marketing analytics',
    BrandConfig.name,
  ],
  authors: [{ name: `${BrandConfig.name} Inc.` }],
  openGraph: {
    title: `${BrandConfig.name} — ${BrandConfig.tagline}`,
    description: 'Plan, create, automate, optimize and analyze marketing using AI Agents.',
    type: 'website',
    locale: 'en_US',
    siteName: BrandConfig.name,
  },
  twitter: {
    card: 'summary_large_image',
    title: `${BrandConfig.name} — ${BrandConfig.tagline}`,
    description: 'Plan, create, automate, optimize and analyze marketing using AI Agents.',
  },
  manifest: '/site.webmanifest',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [{ url: '/apple-touch-icon.png', sizes: '180x180' }],
  },
};

// Anti-flash theme script — runs synchronously before React hydration
// so the correct dark/light class is applied with zero FOUC.
const themeScript = `
(function(){
  try{
    var s=localStorage.getItem('theme');
    var mq=window.matchMedia('(prefers-color-scheme: dark)');
    var d=document.documentElement;
    if(s==='light'){d.classList.remove('dark');}
    else if(s==='dark'){d.classList.add('dark');}
    else{if(mq.matches){d.classList.add('dark');}else{d.classList.remove('dark');}}
  }catch(e){}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
      suppressHydrationWarning
    >
      <head>
        {/* Anti-FOUC: apply theme class before first paint */}
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full flex flex-col bg-background">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
