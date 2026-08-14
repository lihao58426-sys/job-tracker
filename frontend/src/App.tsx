import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import JobList from './pages/JobList';
import JobDetail from './pages/JobDetail';

const navStyle: React.CSSProperties = {
  display: 'flex', gap: 0, background: '#1a1a2e', padding: '0 24px', alignItems: 'center',
};

const linkBase: React.CSSProperties = {
  color: '#a0a0b8', textDecoration: 'none', padding: '14px 20px',
  fontSize: '14px', fontWeight: 500, borderBottom: '2px solid transparent',
  transition: 'all 0.2s',
};

export default function App() {
  return (
    <div>
      <nav style={navStyle}>
        <span style={{ color: '#fff', fontWeight: 700, fontSize: '16px', marginRight: 32 }}>
          📋 求职跟踪
        </span>
        <NavLink to="/" end style={({ isActive }) => ({ ...linkBase, color: isActive ? '#fff' : '#a0a0b8', borderBottomColor: isActive ? '#4fc3f7' : 'transparent' })}>
          仪表盘
        </NavLink>
        <NavLink to="/jobs" style={({ isActive }) => ({ ...linkBase, color: isActive ? '#fff' : '#a0a0b8', borderBottomColor: isActive ? '#4fc3f7' : 'transparent' })}>
          岗位列表
        </NavLink>
      </nav>
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<JobList />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
        </Routes>
      </main>
    </div>
  );
}
