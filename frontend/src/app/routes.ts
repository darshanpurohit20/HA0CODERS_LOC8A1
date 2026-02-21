import { createBrowserRouter } from 'react-router';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ApproveLeads } from './pages/ApproveLeads';
import { ApprovedLeads } from './pages/ApprovedLeads';
import { Conversations } from './pages/Conversations';
import { Meetings } from './pages/Meetings';
import { Analytics } from './pages/Analytics';
import { ContentEngine } from './pages/ContentEngine';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import LoginPage from './pages/LoginPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    Component: LoginPage,
  },
  {
    path: '/',
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: 'approve', Component: ApproveLeads },
      { path: 'approved', Component: ApprovedLeads },
      { path: 'conversations', Component: Conversations },
      { path: 'meetings', Component: Meetings },
      { path: 'analytics', Component: Analytics },
      { path: 'content', Component: ContentEngine },
      { path: 'profile', Component: Profile },
      { path: '*', Component: NotFound },
    ],
  },
]);