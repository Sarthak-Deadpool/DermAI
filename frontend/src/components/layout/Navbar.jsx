function Navbar({ user, onLogout }) {
  return (
    <header className="border-b border-slate-800 bg-slate-950 text-white">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="/dashboard" className="text-2xl font-bold text-cyan-400">
          DermAI
        </a>

        <div className="flex items-center gap-4">
          {user && (
            <span className="hidden text-sm text-slate-300 sm:inline">
              {user.username}
            </span>
          )}

          <button
            type="button"
            onClick={onLogout}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm hover:border-cyan-400 hover:text-cyan-400"
          >
            Log out
          </button>
        </div>
      </nav>
    </header>
  );
}

export default Navbar;