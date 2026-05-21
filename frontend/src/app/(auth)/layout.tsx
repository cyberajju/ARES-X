export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-abyss grid-bg relative overflow-hidden">
      {/* Corner accents */}
      <div className="absolute top-4 left-4 w-16 h-16 border-t-2 border-l-2 border-accent-cyan opacity-50" />
      <div className="absolute top-4 right-4 w-16 h-16 border-t-2 border-r-2 border-accent-cyan opacity-50" />
      <div className="absolute bottom-4 left-4 w-16 h-16 border-b-2 border-l-2 border-accent-cyan opacity-50" />
      <div className="absolute bottom-4 right-4 w-16 h-16 border-b-2 border-r-2 border-accent-cyan opacity-50" />

      {/* Scan line overlay */}
      <div className="absolute inset-0 scan-line pointer-events-none" />

      {/* Main content */}
      <div className="relative z-10 w-full max-w-md px-6">
        {/* ARES-X Branding */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-mono font-bold text-accent-cyan text-glow-cyan tracking-widest">
            ARES-X
          </h1>
          <p className="text-text-muted text-sm mt-2 tracking-wider uppercase">
            Cyber Battlefield Platform
          </p>
        </div>

        {children}
      </div>
    </div>
  );
}
