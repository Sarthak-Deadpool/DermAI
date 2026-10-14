/** @format */


function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 text-white">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-cyan-400">
            DermAI
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Skin Disease Screening Research Prototype
          </p>
        </div>

        <h2 className="text-2xl font-semibold">{title}</h2>

        <p className="mt-2 text-sm text-slate-400">
          {subtitle}
        </p>

        <div className="mt-6">{children}</div>
      </section>
    </main>
  );
}

export default AuthLayout;

