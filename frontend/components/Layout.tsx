import Link from "next/link";
import { useRouter } from "next/router";
import { Brain, Upload, MessageSquare } from "lucide-react";
import clsx from "clsx";

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();

  const links = [
    { href: "/upload", label: "Upload", icon: Upload },
    { href: "/chat", label: "Chat", icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0f1117" }}>
      <header style={{ background: "#181c27", borderBottom: "1px solid #252a38" }} className="px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 no-underline">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #6c63ff, #3d3880)" }}>
              <Brain size={18} color="white" />
            </div>
            <span className="font-semibold text-white text-sm tracking-tight">DocIntel</span>
          </Link>

          <nav className="flex gap-1">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline",
                  router.pathname === href
                    ? "text-white"
                    : "text-[#8b92a5] hover:text-white hover:bg-white/5"
                )}
                style={router.pathname === href ? { background: "rgba(108,99,255,0.2)", color: "#a5a0ff" } : {}}
              >
                <Icon size={15} />
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {children}
      </main>
    </div>
  );
}
