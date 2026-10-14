/** @format */

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="min-h-dvh bg-slate-50 lg:h-dvh lg:overflow-hidden">
      <div className="grid min-h-dvh lg:h-full lg:min-h-0 lg:grid-cols-2">
        {/* Left branding section */}
        <section className="relative hidden flex-col justify-between overflow-hidden bg-slate-950 p-8 text-white lg:flex xl:p-10">
          <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl" />

          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500 text-xl font-bold">
                D
              </div>

              <div>
                <h1 className="text-xl font-bold tracking-wide">DermAI</h1>
                <p className="text-xs text-slate-400">
                  Skin Image Research Platform
                </p>
              </div>
            </div>
          </div>

          <div className="relative z-10 max-w-lg">
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">
              Research. Understand. Explore.
            </p>

            <h2 className="text-4xl font-bold leading-tight xl:text-5xl">
              A smarter workspace for skin image analysis.
            </h2>

            <p className="mt-5 max-w-md leading-7 text-slate-400">
              Organize image-based research cases in one place. DermAI is an
              academic research prototype, not a substitute for professional
              medical diagnosis.
            </p>
          </div>

          <p className="relative z-10 text-sm text-slate-500">
            © {new Date().getFullYear()} DermAI · Academic Research Project
          </p>
        </section>

        {/* Right content section */}
        <section className="flex items-center justify-center px-5 py-5 sm:px-8 lg:h-full lg:overflow-y-auto lg:px-10 lg:py-4 xl:px-12">
          <div className="w-full max-w-md">
            {/* Mobile branding */}
            <div className="mb-5 flex items-center gap-3 lg:hidden">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-700 text-xl font-bold text-white">
                D
              </div>

              <div>
                <h1 className="text-xl font-bold text-slate-900">DermAI</h1>
                <p className="text-xs text-slate-500">
                  Skin Image Research Platform
                </p>
              </div>
            </div>

            <div className="mb-5">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                {title}
              </h2>

              <p className="mt-2 text-sm leading-5 text-slate-600">
                {subtitle}
              </p>
            </div>

            {children}
          </div>
        </section>
      </div>
    </main>
  );
}
