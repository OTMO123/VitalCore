import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
  Collapse,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  LocalHospital as HealthcareIcon,
  Sync as SyncIcon,
  Shield as SecurityIcon,
  Assessment as ComplianceIcon,
  SmartToy as AIIcon,
  Settings as SettingsIcon,
  ExpandLess,
  ExpandMore,
  AdminPanelSettings as AdminIcon,
  Insights as AnalyticsIcon,
  Shield as ShieldIcon,
  CloudSync as CloudSyncIcon,
  Folder as DocumentIcon,
  CloudUpload as UploadIcon,
  Search as SearchIcon,
  Psychology as AIClassificationIcon,
  History as VersionIcon,
} from '@mui/icons-material';

import { useAppSelector, useAppDispatch } from '@/store';
import { selectSidebarOpen, toggleSidebar } from '@/store/slices/uiSlice';
import { selectUser } from '@/store/slices/authSlice';

// ============================================
// SIDEBAR CONFIGURATION
// ============================================

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path?: string;
  children?: NavigationItem[];
  roles?: string[];
  adminOnly?: boolean;
  badge?: string;
  comingSoon?: boolean;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    id: 'patients',
    label: 'Patient Management',
    icon: <PeopleIcon />,
    children: [
      {
        id: 'patients-list',
        label: 'All Patients',
        icon: <PeopleIcon />,
        path: '/patients',
      },
      {
        id: 'patients-search',
        label: 'Search Patients',
        icon: <PeopleIcon />,
        path: '/patients?tab=search',
      },
    ],
  },
  {
    id: 'healthcare',
    label: 'Healthcare Records',
    icon: <HealthcareIcon />,
    children: [
      {
        id: 'clinical-documents',
        label: 'Clinical Documents',
        icon: <HealthcareIcon />,
        path: '/healthcare?tab=documents',
      },
      {
        id: 'consents',
        label: 'Patient Consents',
        icon: <ShieldIcon />,
        path: '/healthcare?tab=consents',
      },
      {
        id: 'fhir-validation',
        label: 'FHIR Validation',
        icon: <SecurityIcon />,
        path: '/healthcare?tab=fhir',
      },
      {
        id: 'anonymization',
        label: 'Data Anonymization',
        icon: <SecurityIcon />,
        path: '/healthcare?tab=anonymization',
      },
    ],
  },
  {
    id: 'documents',
    label: 'Document Management',
    icon: <DocumentIcon />,
    children: [
      {
        id: 'document-upload',
        label: 'Upload Documents',
        icon: <UploadIcon />,
        path: '/documents',
      },
      {
        id: 'document-search',
        label: 'Search & Browse',
        icon: <SearchIcon />,
        path: '/documents?tab=search',
      },
      {
        id: 'document-analytics',
        label: 'AI Classification',
        icon: <AIClassificationIcon />,
        path: '/documents?tab=analytics',
        badge: 'AI',
      },
      {
        id: 'document-compliance',
        label: 'Security & Audit',
        icon: <SecurityIcon />,
        path: '/documents?tab=security',
      },
    ],
  },
  {
    id: 'iris-integration',
    label: 'IRIS Integration',
    icon: <SyncIcon />,
    children: [
      {
        id: 'iris-health',
        label: 'Health Status',
        icon: <CloudSyncIcon />,
        path: '/iris?tab=health',
      },
      {
        id: 'iris-endpoints',
        label: 'API Endpoints',
        icon: <SyncIcon />,
        path: '/iris?tab=endpoints',
      },
      {
        id: 'iris-sync',
        label: 'Data Sync',
        icon: <CloudSyncIcon />,
        path: '/iris?tab=sync',
      },
    ],
  },
  {
    id: 'audit-compliance',
    label: 'Audit & Compliance',
    icon: <SecurityIcon />,
    children: [
      {
        id: 'audit-logs',
        label: 'Audit Logs',
        icon: <SecurityIcon />,
        path: '/audit',
      },
      {
        id: 'compliance-reports',
        label: 'Compliance Reports',
        icon: <ComplianceIcon />,
        path: '/compliance',
      },
      {
        id: 'phi-access',
        label: 'PHI Access Logs',
        icon: <ShieldIcon />,
        path: '/audit?tab=phi-access',
      },
    ],
  },
  {
    id: 'ai-agents',
    label: 'AI Agents',
    icon: <AIIcon />,
    path: '/ai-agents',
    badge: 'Beta',
    adminOnly: true,
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: <AnalyticsIcon />,
    children: [
      {
        id: 'system-metrics',
        label: 'System Metrics',
        icon: <AnalyticsIcon />,
        path: '/analytics?tab=system',
        comingSoon: true,
        adminOnly: true,
      },
      {
        id: 'health-insights',
        label: 'Health Insights',
        icon: <HealthcareIcon />,
        path: '/analytics?tab=health',
        comingSoon: true,
        adminOnly: true,
      },
    ],
    adminOnly: true,
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <SettingsIcon />,
    children: [
      {
        id: 'user-settings',
        label: 'User Settings',
        icon: <SettingsIcon />,
        path: '/settings',
      },
      {
        id: 'system-admin',
        label: 'System Admin',
        icon: <AdminIcon />,
        path: '/settings?tab=admin',
        roles: ['admin'],
      },
    ],
  },
];

// ============================================
// SIDEBAR COMPONENT
// ============================================

const Sidebar: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  
  const sidebarOpen = useAppSelector(selectSidebarOpen);
  const user = useAppSelector(selectUser);
  
  const [expandedItems, setExpandedItems] = React.useState<Set<string>>(new Set());

  const SIDEBAR_WIDTH = 280;
  const SIDEBAR_COLLAPSED_WIDTH = 64;

  // Auto-expand items based on current path
  React.useEffect(() => {
    const currentPath = location.pathname;
    const newExpanded = new Set<string>();
    
    navigationItems.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => 
          child.path && currentPath.startsWith(child.path.split('?')[0])
        );
        if (hasActiveChild) {
          newExpanded.add(item.id);
        }
      }
    });
    
    setExpandedItems(newExpanded);
  }, [location.pathname]);

  const handleItemClick = (item: NavigationItem) => {
    if (item.comingSoon) {
      // Show coming soon message
      return;
    }

    if (item.path) {
      navigate(item.path);
    } else if (item.children) {
      const newExpanded = new Set(expandedItems);
      if (newExpanded.has(item.id)) {
        newExpanded.delete(item.id);
      } else {
        newExpanded.add(item.id);
      }
      setExpandedItems(newExpanded);
    }
  };

  const isItemActive = (item: NavigationItem): boolean => {
    if (!item.path) return false;
    const currentPath = location.pathname;
    const itemPath = item.path.split('?')[0];
    return currentPath === itemPath || currentPath.startsWith(itemPath + '/');
  };

  const hasPermission = (item: NavigationItem): boolean => {
    if (!user) return false;
    
    // Check for admin-only items
    if (item.adminOnly) {
      const userRoleString = user.role?.name || user.role;
      const isAdmin = userRoleString === 'admin' || userRoleString === 'ADMIN';
      if (!isAdmin) return false;
    }
    
    // Check for specific roles
    if (item.roles && item.roles.length > 0) {
      return item.roles.includes(user.role?.name || user.role || '');
    }
    
    return true;
  };

  const renderNavigationItem = (item: NavigationItem, depth = 0) => {
    if (!hasPermission(item)) return null;

    const isActive = isItemActive(item);
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;

    const listItem = (
      <ListItemButton
        key={item.id}
        onClick={() => handleItemClick(item)}
        sx={{
          borderRadius: 1,
          margin: sidebarOpen ? '2px 8px' : '2px 4px',
          paddingLeft: sidebarOpen ? theme.spacing(2 + depth * 1.5) : theme.spacing(1.5),
          minHeight: 48,
          backgroundColor: isActive ? theme.palette.primary.main + '14' : 'transparent',
          color: isActive ? theme.palette.primary.main : theme.palette.text.primary,
          opacity: item.comingSoon ? 0.6 : 1,
          '&:hover': {
            backgroundColor: isActive 
              ? theme.palette.primary.main + '20'
              : theme.palette.action.hover,
          },
        }}
      >
        <ListItemIcon
          sx={{
            minWidth: sidebarOpen ? 40 : 'auto',
            color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
            marginRight: sidebarOpen ? 0 : 0,
          }}
        >
          {item.icon}
        </ListItemIcon>
        
        {sidebarOpen && (
          <>
            <ListItemText
              primary={item.label}
              primaryTypographyProps={{
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
              }}
            />
            
            {item.badge && (
              <Box
                sx={{
                  backgroundColor: theme.palette.warning.light,
                  color: theme.palette.warning.contrastText,
                  fontSize: '0.625rem',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  fontWeight: 600,
                  marginLeft: 1,
                }}
              >
                {item.badge}
              </Box>
            )}
            
            {hasChildren && (
              isExpanded ? <ExpandLess /> : <ExpandMore />
            )}
          </>
        )}
      </ListItemButton>
    );

    if (!sidebarOpen && (item.label || item.badge)) {
      return (
        <Tooltip
          key={item.id}
          title={
            <Box>
              <Typography variant="body2">{item.label}</Typography>
              {item.badge && (
                <Typography variant="caption" color="warning.main">
                  {item.badge}
                </Typography>
              )}
            </Box>
          }
          placement="right"
          arrow
        >
          {listItem}
        </Tooltip>
      );
    }

    return (
      <React.Fragment key={item.id}>
        {listItem}
        
        {hasChildren && sidebarOpen && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, depth + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: sidebarOpen ? SIDEBAR_WIDTH : SIDEBAR_COLLAPSED_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: sidebarOpen ? SIDEBAR_WIDTH : SIDEBAR_COLLAPSED_WIDTH,
          boxSizing: 'border-box',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.easeInOut,
            duration: theme.transitions.duration.standard,
          }),
          overflowX: 'hidden',
          backgroundColor: theme.palette.background.paper,
          borderRight: `1px solid ${theme.palette.divider}`,
          position: 'fixed',
          height: '100vh',
          zIndex: theme.zIndex.drawer,
        },
      }}
    >
      {/* Logo & Brand */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarOpen ? 'flex-start' : 'center',
          padding: theme.spacing(2),
          minHeight: 64,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <HealthcareIcon 
          sx={{ 
            color: theme.palette.primary.main,
            fontSize: 32,
            marginRight: sidebarOpen ? 1 : 0,
          }} 
        />
        {sidebarOpen && (
          <Box>
            <Typography variant="h6" fontWeight={700} color="primary">
              Healthcare AI
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Platform
            </Typography>
          </Box>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', paddingY: 1 }}>
        <List>
          {navigationItems.map(item => renderNavigationItem(item))}
        </List>
      </Box>

      {/* User Info */}
      <Box
        sx={{
          padding: theme.spacing(2),
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        {sidebarOpen && user && (
          <Box>
            <Typography variant="body2" fontWeight={600}>
              {user.username}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {user.role?.name || 'User'}
            </Typography>
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;