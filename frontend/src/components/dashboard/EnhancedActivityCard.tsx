import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import {
  // Authentication & Security
  Login as LoginIcon,
  Logout as LogoutIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Shield as ShieldIcon,
  VpnKey as AuthIcon,
  
  // PHI & Medical
  LocalHospital as MedicalIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  
  // Administrative
  AdminPanelSettings as AdminIcon,
  Settings as ConfigIcon,
  PersonAdd as UserAddIcon,
  PersonRemove as UserRemoveIcon,
  
  // System & Technical
  CloudSync as SyncIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon,
  Assessment as ReportIcon,
  
  // Compliance
  Gavel as ComplianceIcon,
  Policy as PolicyIcon,
  VerifiedUser as ConsentIcon,
  
  // UI
  AccessTime as TimeIcon,
  MoreVert as MoreVertIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

// ============================================
// ENHANCED ACTIVITY TYPES FOR SOC2 COMPLIANCE
// ============================================

type ActivityType = 
  // Authentication Events
  | 'user_login' | 'user_logout' | 'user_login_failed' | 'user_locked'
  // PHI Access Events (CRITICAL for SOC2)
  | 'phi_accessed' | 'phi_created' | 'phi_updated' | 'phi_deleted' | 'phi_exported'
  // Patient Management
  | 'patient_created' | 'patient_updated' | 'patient_accessed' | 'patient_search'
  // Administrative Actions
  | 'user_created' | 'user_updated' | 'user_deleted' | 'role_changed' | 'permission_granted'
  // System Configuration
  | 'config_changed' | 'security_policy_updated' | 'system_setting_modified'
  // Security Violations
  | 'security_violation' | 'unauthorized_access' | 'suspicious_activity' | 'data_breach_detected'
  // IRIS Integration
  | 'iris_sync_completed' | 'iris_sync_failed' | 'external_api_error'
  // Compliance & Consent
  | 'consent_granted' | 'consent_withdrawn' | 'consent_updated' | 'audit_report_generated'
  // System Events
  | 'system_error' | 'database_error' | 'performance_issue';

interface EnhancedActivityItem {
  id: string;
  type: string; // Changed from ActivityType to string for flexibility
  category: 'security' | 'phi' | 'admin' | 'system' | 'compliance';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  userId?: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  ipAddress?: string;
  userAgent?: string;
  resourceId?: string;
  resourceType?: string;
  metadata?: Record<string, any>;
  complianceFlags?: string[];
}

interface EnhancedActivityCardProps {
  activities: EnhancedActivityItem[];
  loading?: boolean;
  maxItems?: number;
  showFilters?: boolean;
}

const EnhancedActivityCard: React.FC<EnhancedActivityCardProps> = ({
  activities,
  loading = false,
  maxItems = 10,
  showFilters = true,
}) => {
  const [selectedTab, setSelectedTab] = useState<string>('all');
  const [showCriticalOnly, setShowCriticalOnly] = useState(false);

  // ============================================
  // ACTIVITY CONFIGURATION
  // ============================================

  const getActivityIcon = (type: string) => {
    const iconMap: Record<string, React.ReactElement> = {
      // Authentication
      'user_login': <LoginIcon />,
      'user_logout': <LogoutIcon />,
      'user_login_failed': <WarningIcon />,
      'user_locked': <SecurityIcon />,
      
      // PHI Events (CRITICAL)
      'phi_accessed': <ViewIcon />,
      'phi_created': <MedicalIcon />,
      'phi_updated': <MedicalIcon />,
      'phi_deleted': <WarningIcon />,
      'phi_exported': <ExportIcon />,
      
      // Patient Management
      'patient_created': <UserAddIcon />,
      'patient_updated': <MedicalIcon />,
      'patient_accessed': <ViewIcon />,
      'patient_search': <ViewIcon />,
      
      // Administrative
      'user_created': <UserAddIcon />,
      'user_updated': <AdminIcon />,
      'user_deleted': <UserRemoveIcon />,
      'role_changed': <AdminIcon />,
      'permission_granted': <SecurityIcon />,
      
      // Configuration
      'config_changed': <ConfigIcon />,
      'security_policy_updated': <ShieldIcon />,
      'system_setting_modified': <ConfigIcon />,
      
      // Security Violations
      'security_violation': <WarningIcon />,
      'unauthorized_access': <ErrorIcon />,
      'suspicious_activity': <WarningIcon />,
      'data_breach_detected': <ErrorIcon />,
      
      // IRIS Integration
      'iris_sync_completed': <SyncIcon />,
      'iris_sync_failed': <ErrorIcon />,
      'external_api_error': <ErrorIcon />,
      
      // Compliance
      'consent_granted': <ConsentIcon />,
      'consent_withdrawn': <PolicyIcon />,
      'consent_updated': <ConsentIcon />,
      'audit_report_generated': <ReportIcon />,
      
      // System
      'system_error': <ErrorIcon />,
      'database_error': <ErrorIcon />,
      'performance_issue': <WarningIcon />,
    };

    return iconMap[type] || <InfoIcon />;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error.main';
      case 'high': return 'warning.main';
      case 'medium': return 'info.main';
      case 'low': return 'success.main';
      default: return 'grey.500';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'security': return 'error.main';
      case 'phi': return 'warning.main';
      case 'admin': return 'info.main';
      case 'system': return 'primary.main';
      case 'compliance': return 'success.main';
      default: return 'grey.500';
    }
  };

  // ============================================
  // FILTERING LOGIC
  // ============================================

  const filterActivities = () => {
    let filtered = activities;

    // Filter by category
    if (selectedTab !== 'all') {
      filtered = filtered.filter(activity => activity.category === selectedTab);
    }

    // Filter by severity
    if (showCriticalOnly) {
      filtered = filtered.filter(activity => 
        activity.severity === 'critical' || activity.severity === 'high'
      );
    }

    return filtered.slice(0, maxItems);
  };

  const getTabCounts = () => {
    const counts = {
      all: activities.length,
      security: activities.filter(a => a.category === 'security').length,
      phi: activities.filter(a => a.category === 'phi').length,
      admin: activities.filter(a => a.category === 'admin').length,
      system: activities.filter(a => a.category === 'system').length,
      compliance: activities.filter(a => a.category === 'compliance').length,
    };

    const criticalCount = activities.filter(a => 
      a.severity === 'critical' || a.severity === 'high'
    ).length;

    return { ...counts, critical: criticalCount };
  };

  const displayActivities = filterActivities();
  const tabCounts = getTabCounts();
  
  

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center">
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
              <TimeIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Security & Audit Activity
              </Typography>
              <Typography variant="body2" color="text.secondary">
                SOC2 Type 2 compliant activity monitoring
              </Typography>
            </Box>
          </Box>
          
          <Box>
            {tabCounts.critical > 0 && (
              <Badge badgeContent={tabCounts.critical} color="error" sx={{ mr: 1 }}>
                <Chip 
                  label="Critical Alerts" 
                  color="error" 
                  size="small"
                  onClick={() => setShowCriticalOnly(!showCriticalOnly)}
                  variant={showCriticalOnly ? "filled" : "outlined"}
                />
              </Badge>
            )}
            <Tooltip title="View all activities">
              <IconButton size="small" aria-label="View all activities">
                <MoreVertIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Critical Security Alert */}
        {tabCounts.critical > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>{tabCounts.critical} critical security events</strong> require immediate attention.
              Review PHI access and security violations.
            </Typography>
          </Alert>
        )}

        {/* Category Tabs */}
        {showFilters && (
          <Box mb={2}>
            <Tabs
              value={selectedTab}
              onChange={(_, newValue) => setSelectedTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minHeight: 36 }}
            >
              <Tab label={`All (${tabCounts.all})`} value="all" />
              <Tab 
                label={
                  <Badge badgeContent={tabCounts.security} color="error" variant="dot">
                    Security ({tabCounts.security})
                  </Badge>
                } 
                value="security" 
              />
              <Tab 
                label={
                  <Badge badgeContent={tabCounts.phi} color="warning" variant="dot">
                    PHI Access ({tabCounts.phi})
                  </Badge>
                } 
                value="phi" 
              />
              <Tab label={`Admin (${tabCounts.admin})`} value="admin" />
              <Tab label={`System (${tabCounts.system})`} value="system" />
              <Tab label={`Compliance (${tabCounts.compliance})`} value="compliance" />
            </Tabs>
          </Box>
        )}

        {/* Activity List - Limited to 10 items with scroll */}
        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <Typography variant="body2" color="text.secondary">
              Loading security audit logs...
            </Typography>
          </Box>
        ) : displayActivities.length === 0 ? (
          <Box textAlign="center" py={4}>
            <Typography variant="body2" color="text.secondary">
              No activities found for selected filters
            </Typography>
          </Box>
        ) : (
          <Box 
            sx={{ 
              maxHeight: '400px', 
              overflowY: 'auto',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              backgroundColor: 'background.paper'
            }}
          >
            <List sx={{ p: 0 }}>
              {displayActivities.slice(0, 10).map((activity, index) => (
              <React.Fragment key={activity.id}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    px: 0,
                    py: 2,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                      borderRadius: 1,
                    },
                    borderLeft: activity.severity === 'critical' ? '4px solid' : 'none',
                    borderLeftColor: 'error.main',
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 48, mt: 0.5 }}>
                    <Avatar
                      sx={{
                        bgcolor: getSeverityColor(activity.severity),
                        width: 36,
                        height: 36,
                      }}
                    >
                      {getActivityIcon(activity.type)}
                    </Avatar>
                  </ListItemIcon>
                  
                  <Box sx={{ flex: 1, mr: 1 }}>
                    {/* Title and Chips Row */}
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2" fontWeight={600}>
                        {activity.title}
                      </Typography>
                      <Box display="flex" gap={0.5}>
                        <Chip
                          label={activity.severity.toUpperCase()}
                          size="small"
                          color={
                            activity.severity === 'critical' ? 'error' :
                            activity.severity === 'high' ? 'warning' :
                            activity.severity === 'medium' ? 'info' : 'default'
                          }
                          sx={{ fontSize: '0.625rem', height: 18 }}
                        />
                        <Chip
                          label={activity.category.toUpperCase()}
                          size="small"
                          variant="outlined"
                          sx={{ 
                            fontSize: '0.625rem', 
                            height: 18,
                            borderColor: getCategoryColor(activity.category),
                            color: getCategoryColor(activity.category),
                          }}
                        />
                      </Box>
                    </Box>
                    
                    {/* Description */}
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {activity.description}
                    </Typography>
                    
                    {/* Metadata */}
                    <Typography variant="caption" color="text.secondary">
                      {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                      {activity.user && (
                        <>
                          {' • '}
                          <Typography 
                            component="span" 
                            variant="caption" 
                            fontWeight={600}
                            color="primary.main"
                          >
                            {activity.user}
                          </Typography>
                        </>
                      )}
                      {activity.ipAddress && (
                        <>
                          {' • '}
                          <Typography 
                            component="span" 
                            variant="caption"
                            color="text.secondary"
                          >
                            IP: {activity.ipAddress}
                          </Typography>
                        </>
                      )}
                    </Typography>
                    
                    {/* Compliance Flags */}
                    {activity.complianceFlags && activity.complianceFlags.length > 0 && (
                      <Box mt={0.5} display="flex" gap={0.5}>
                        {activity.complianceFlags.map((flag, idx) => (
                          <Chip
                            key={idx}
                            label={flag}
                            size="small"
                            color="warning"
                            variant="outlined"
                            sx={{ fontSize: '0.5rem', height: 16 }}
                          />
                        ))}
                      </Box>
                    )}
                  </Box>
                </ListItem>
                
                {index < Math.min(displayActivities.length, 10) - 1 && (
                  <Divider variant="inset" component="li" sx={{ ml: 6 }} />
                )}
              </React.Fragment>
              ))}
            </List>
          </Box>
        )}

        {/* Footer */}
        {activities.length > 10 && (
          <Box textAlign="center" mt={2} pt={2} borderTop={1} borderColor="divider">
            <Typography variant="body2" color="primary.main" sx={{ cursor: 'pointer' }}>
              Showing 10 of {activities.length} audit entries - scroll to view more →
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default EnhancedActivityCard;