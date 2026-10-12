import "./globals.css";
export const metadata = { title: "APEX-AI" };
export default function Root({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body className="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">{children}
    <footer className="p-3 text-center text-xs opacity-60">Designed and developed by NIKHIL CHARY SRIRAMOJU</footer></body></html>);
}
