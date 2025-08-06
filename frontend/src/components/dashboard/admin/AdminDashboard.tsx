import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import CountUp from 'react-countup';
import { motion } from 'framer-motion';
import {
  DollarSign,
  Users,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Server,
  Clock,
  UserCheck,
  UserPlus,
  HeartPulse,
  FileText,
  BarChart3,
  PieChart as PieChartIcon,
  Calendar,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { AdminMetrics, RevenueChartData, UserActivityData, RiskDistributionData } from '@/types/dashboard';
import { MockDataService } from '@/lib/mock-data';

const AdminDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueChartData[]>([]);
  const [userActivityData, setUserActivityData] = useState<UserActivityData[]>([]);
  const [riskData, setRiskData] = useState<RiskDistributionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('30d');

  const mockService = MockDataService.getInstance();

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [adminMetrics, revenue, activity, risk] = await Promise.all([
          mockService.getAdminMetrics(),
          mockService.getRevenueData(),
          mockService.getUserActivityData(),
          mockService.getRiskDistribution()
        ]);
        
        setMetrics(adminMetrics);
        setRevenueData(revenue);
        setUserActivityData(activity);
        setRiskData(risk);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();

    // Subscribe to real-time updates
    const unsubscribe = mockService.subscribeToMetrics((updatedMetrics) => {
      setMetrics(updatedMetrics);
    });

    return unsubscribe;
  }, []);

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <RefreshCw className="h-8 w-8 text-blue-500" />
        </motion.div>
      </div>
    );
  }

  const MetricCard = ({ 
    title, 
    value, 
    change, 
    trend, 
    icon: Icon, 
    description,
    color = "blue" 
  }: {
    title: string;
    value: number | string;
    change?: number;
    trend?: 'up' | 'down' | 'stable';
    icon: React.ElementType;
    description?: string;
    color?: string;
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="hover:shadow-lg transition-shadow duration-200">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <Icon className={`h-4 w-4 text-${color}-500`} />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {typeof value === 'number' ? (
              <CountUp 
                end={value} 
                duration={2} 
                separator="," 
                prefix={title.includes('Revenue') || title.includes('MRR') || title.includes('ARR') ? '$' : ''}
                suffix={title.includes('Uptime') || title.includes('Rate') || title.includes('Score') ? '%' : ''}
              />
            ) : (
              value
            )}
          </div>
          {change !== undefined && (
            <div className="flex items-center pt-1">
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : trend === 'down' ? (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              ) : (
                <Activity className="h-4 w-4 text-gray-500 mr-1" />
              )}
              <span className={`text-xs ${
                trend === 'up' ? 'text-green-600' : 
                trend === 'down' ? 'text-red-600' : 
                'text-gray-600'
              }`}>
                {change > 0 ? '+' : ''}{change}%
              </span>
            </div>
          )}
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );

  const SystemStatusCard = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          System Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Uptime</span>
          <Badge variant={metrics.system.uptime > 99 ? "default" : "destructive"}>
            {metrics.system.uptime}%
          </Badge>
        </div>
        <Progress value={metrics.system.uptime} className="h-2" />
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Response Time</span>
          <span className="text-sm text-muted-foreground">{metrics.system.responseTime}ms</span>
        </div>
        <Progress value={Math.max(0, 100 - (metrics.system.responseTime / 10))} className="h-2" />
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Error Rate</span>
          <Badge variant={metrics.system.errorRate < 0.1 ? "default" : "destructive"}>
            {metrics.system.errorRate}%
          </Badge>
        </div>
        <Progress value={Math.max(0, 100 - (metrics.system.errorRate * 100))} className="h-2" />
        
        <div className="flex items-center justify-between pt-2">
          <span className="text-sm font-medium">Overall Status</span>
          {metrics.system.status === 'healthy' ? (
            <Badge className="bg-green-100 text-green-800">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Healthy
            </Badge>
          ) : metrics.system.status === 'warning' ? (
            <Badge variant="secondary">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Warning
            </Badge>
          ) : (
            <Badge variant="destructive">
              <XCircle className="h-3 w-3 mr-1" />
              Critical
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const ComplianceCard = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Compliance Status
        </CardTitle>
        <CardDescription>SOC2 & HIPAA Compliance Monitoring</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{metrics.compliance.hipaaScore}%</div>
            <div className="text-sm text-muted-foreground">HIPAA Score</div>
            <Progress value={metrics.compliance.hipaaScore} className="h-2 mt-2" />
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{metrics.compliance.soc2Score}%</div>
            <div className="text-sm text-muted-foreground">SOC2 Score</div>
            <Progress value={metrics.compliance.soc2Score} className="h-2 mt-2" />
          </div>
        </div>
        
        <Separator />
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Audit Alerts</span>
          <Badge variant={metrics.compliance.auditAlerts === 0 ? "default" : "destructive"}>
            {metrics.compliance.auditAlerts} Active
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Last Audit</span>
          <span className="text-sm text-muted-foreground">{metrics.compliance.lastAudit}</span>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            Healthcare Platform Administration & Analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Last 30 days
          </Button>
          <Button size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Monthly Recurring Revenue"
          value={metrics.revenue.mrr}
          change={metrics.revenue.growth}
          trend={metrics.revenue.trend}
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="Total Users"
          value={metrics.users.total}
          change={((metrics.users.new / metrics.users.total) * 100)}
          trend="up"
          icon={Users}
          description={`${metrics.users.active} active users`}
          color="blue"
        />
        <MetricCard
          title="System Uptime"
          value={metrics.system.uptime}
          trend={metrics.system.uptime > 99 ? 'up' : 'down'}
          icon={Activity}
          description={`${metrics.system.responseTime}ms avg response`}
          color="purple"
        />
        <MetricCard
          title="HIPAA Compliance"
          value={metrics.compliance.hipaaScore}
          trend="up"
          icon={Shield}
          description={`${metrics.compliance.auditAlerts} alerts pending`}
          color="red"
        />
      </div>

      {/* Charts and Analytics */}
      <Tabs defaultValue="revenue" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="revenue">Revenue Analytics</TabsTrigger>
          <TabsTrigger value="users">User Activity</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Revenue Trends</CardTitle>
                <CardDescription>Monthly recurring revenue and growth metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value: number) => [`$${value.toLocaleString()}`, 'MRR']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="mrr" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.1}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">MRR</span>
                    <span className="text-sm font-bold">${metrics.revenue.mrr.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">ARR</span>
                    <span className="text-sm font-bold">${metrics.revenue.arr.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Growth Rate</span>
                    <Badge variant="default">+{metrics.revenue.growth}%</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Customer Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">New Customers</span>
                    <span className="text-sm font-bold text-green-600">+{metrics.users.new}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Retention Rate</span>
                    <span className="text-sm font-bold">{metrics.users.retention}%</span>
                  </div>
                  <Progress value={metrics.users.retention} className="h-2" />
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Activity (24h)</CardTitle>
                <CardDescription>Real-time user engagement metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={userActivityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="activeUsers" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Distribution</CardTitle>
                <CardDescription>Patient risk level distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={riskData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={120}
                      paddingAngle={5}
                      dataKey="count"
                    >
                      {riskData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [value.toLocaleString(), 'Patients']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SystemStatusCard />
            
            <Card>
              <CardHeader>
                <CardTitle>Healthcare Staff Metrics</CardTitle>
                <CardDescription>Doctor and patient management overview</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{metrics.doctors.total}</div>
                    <div className="text-sm text-muted-foreground">Total Doctors</div>
                    <div className="text-xs text-green-600">{metrics.doctors.active} active</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{metrics.patients.total}</div>
                    <div className="text-sm text-muted-foreground">Total Patients</div>
                    <div className="text-xs text-red-600">{metrics.patients.highRisk} high risk</div>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Doctor Utilization</span>
                    <span className="text-sm font-bold">{metrics.doctors.utilization}%</span>
                  </div>
                  <Progress value={metrics.doctors.utilization} className="h-2" />
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Avg Patients/Day</span>
                    <span className="text-sm font-bold">{metrics.doctors.avgPatientsPerDay}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">New Registrations</span>
                    <Badge variant="default">+{metrics.patients.newRegistrations}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ComplianceCard />
            
            <Card>
              <CardHeader>
                <CardTitle>Security & Audit Log</CardTitle>
                <CardDescription>Recent security events and compliance activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { time: '10:30 AM', event: 'HIPAA compliance check completed', status: 'success' },
                    { time: '09:15 AM', event: 'User access audit initiated', status: 'info' },
                    { time: '08:45 AM', event: 'Data encryption verification', status: 'success' },
                    { time: '08:30 AM', event: 'Failed login attempt detected', status: 'warning' },
                    { time: '07:20 AM', event: 'Backup integrity verified', status: 'success' }
                  ].map((log, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 rounded-lg border">
                      {log.status === 'success' ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : log.status === 'warning' ? (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-blue-500" />
                      )}
                      <div className="flex-1">
                        <div className="text-sm font-medium">{log.event}</div>
                        <div className="text-xs text-muted-foreground">{log.time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminDashboard;