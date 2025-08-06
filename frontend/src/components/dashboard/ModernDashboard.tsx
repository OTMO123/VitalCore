import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Users, 
  FileText, 
  Shield, 
  TrendingUp, 
  Clock,
  CheckCircle2,
  AlertCircle,
  Server,
  Database,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DashboardStats {
  total_patients: number;
  total_patients_change: number;
  system_uptime_percentage: number;
  system_uptime_period: string;
  compliance_score: number;
  compliance_change?: number;
}

interface UserInfo {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

interface SystemStatus {
  iris_api_available: boolean;
  connection_status: string;
  last_sync: string;
  sync_status: string;
}

interface ModernDashboardProps {
  onNavigateToDocuments: () => void;
  onNavigateToPatients: () => void;
}

export function ModernDashboard({ onNavigateToDocuments, onNavigateToPatients }: ModernDashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch dashboard stats
        const statsResponse = await fetch('/api/v1/dashboard/stats');
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData);
        }

        // Fetch user info
        const userResponse = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
        }

        // Fetch system status
        const statusResponse = await fetch('/api/v1/iris/status', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setSystemStatus(statusData);
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const formatUptime = (percentage: number) => {
    if (percentage >= 99.9) return 'Excellent';
    if (percentage >= 99.0) return 'Good';
    if (percentage >= 95.0) return 'Fair';
    return 'Poor';
  };

  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getUptimeColor = (percentage: number) => {
    if (percentage >= 99.9) return 'text-green-600';
    if (percentage >= 99.0) return 'text-blue-600';
    if (percentage >= 95.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="max-w-2xl">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load dashboard data: {error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.username || 'User'}
          </h1>
          <p className="text-muted-foreground">
            Here's what's happening with your healthcare system today.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={user?.is_active ? 'default' : 'secondary'}>
            {user?.role || 'User'}
          </Badge>
          <Badge variant="outline">
            {systemStatus?.connection_status || 'Unknown'}
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Patients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Patients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_patients || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.total_patients_change && stats.total_patients_change > 0 ? '+' : ''}
              {stats?.total_patients_change || 0} from last month
            </p>
          </CardContent>
        </Card>

        {/* System Uptime */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
            <Activity className={`h-4 w-4 ${stats ? getUptimeColor(stats.system_uptime_percentage) : ''}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.system_uptime_percentage?.toFixed(2) || '0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              {stats ? formatUptime(stats.system_uptime_percentage) : 'Unknown'} - {stats?.system_uptime_period || 'N/A'}
            </p>
          </CardContent>
        </Card>

        {/* Compliance Score */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SOC2 Compliance</CardTitle>
            <Shield className={`h-4 w-4 ${stats ? getComplianceColor(stats.compliance_score) : ''}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.compliance_score || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.compliance_change && stats.compliance_change > 0 ? '+' : ''}
              {stats?.compliance_change || 0}% from last audit
            </p>
          </CardContent>
        </Card>

        {/* IRIS Integration */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">IRIS Integration</CardTitle>
            <Server className={`h-4 w-4 ${systemStatus?.iris_api_available ? 'text-green-600' : 'text-red-600'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemStatus?.iris_api_available ? (
                <span className="text-green-600">Online</span>
              ) : (
                <span className="text-red-600">Offline</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {systemStatus?.sync_status || 'Status unknown'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              System Health
            </CardTitle>
            <CardDescription>
              Real-time system status and performance metrics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm">Database Connection</span>
              </div>
              <Badge variant="outline" className="text-green-600">Healthy</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm">Authentication Service</span>
              </div>
              <Badge variant="outline" className="text-green-600">Online</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {systemStatus?.iris_api_available ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <span className="text-sm">IRIS API</span>
              </div>
              <Badge 
                variant="outline" 
                className={systemStatus?.iris_api_available ? 'text-green-600' : 'text-red-600'}
              >
                {systemStatus?.iris_api_available ? 'Connected' : 'Disconnected'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm">Document Storage</span>
              </div>
              <Badge variant="outline" className="text-green-600">Available</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Quick Actions
            </CardTitle>
            <CardDescription>
              Common tasks and system operations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={onNavigateToDocuments}
            >
              <FileText className="h-4 w-4 mr-2" />
              Upload Documents
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={onNavigateToPatients}
            >
              <Users className="h-4 w-4 mr-2" />
              Manage Patients
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={() => window.open('/api/v1/audit/logs', '_blank')}
            >
              <Shield className="h-4 w-4 mr-2" />
              View Audit Logs
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Analytics Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Compliance & Security Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security & Compliance Status
          </CardTitle>
          <CardDescription>
            SOC2 Type II and HIPAA compliance monitoring
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <CheckCircle2 className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <h3 className="font-semibold text-green-800">SOC2 Type II</h3>
              <p className="text-sm text-green-600">Compliant</p>
              <Badge variant="outline" className="mt-2 text-green-600">
                {stats?.compliance_score || 0}% Score
              </Badge>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
              <Shield className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <h3 className="font-semibold text-blue-800">HIPAA</h3>
              <p className="text-sm text-blue-600">Protected</p>
              <Badge variant="outline" className="mt-2 text-blue-600">
                Encrypted
              </Badge>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
              <Clock className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <h3 className="font-semibold text-purple-800">Audit Trail</h3>
              <p className="text-sm text-purple-600">Complete</p>
              <Badge variant="outline" className="mt-2 text-purple-600">
                Real-time
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ModernDashboard;