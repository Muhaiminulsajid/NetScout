import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const linkCls = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${
    isActive ? "bg-sky-600 text-white" : "text-slate-300 hover:bg-slate-800"
  }`;

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
          <span className="text-lg font-bold tracking-tight text-sky-400">
            Net<span className="text-white">Scout</span>
          </span>
          <NavLink to="/" end className={linkCls}>Dashboard</NavLink>
          <NavLink to="/webgraph" className={linkCls}>WebGraph</NavLink>
          <NavLink to="/imagetrace" className={linkCls}>ImageTrace</NavLink>
          <div className="ml-auto flex items-center gap-3 text-sm text-slate-400">
            <span>{user?.email}</span>
            <button
              onClick={logout}
              className="rounded-md border border-slate-700 px-3 py-1.5 hover:bg-slate-800"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
