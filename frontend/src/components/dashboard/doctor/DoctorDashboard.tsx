import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  LineChart, 
  Line, 
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
  Calendar,
  Clock,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Heart,
  Stethoscope,
  FileText,
  Phone,
  Video,
  MessageSquare,
  Star,
  TrendingUp,
  User,
  Bell,
  Settings,
  MoreHorizontal,
  RefreshCw,
  Plus,
  Search,
  Filter,
  Download
} from 'lucide-react';
import { DoctorMetrics, Appointment, Patient, Alert } from '@/types/dashboard';
import { MockDataService } from '@/lib/mock-data';

const DoctorDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DoctorMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  const mockService = MockDataService.getInstance();

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const doctorMetrics = await mockService.getDoctorMetrics();
        setMetrics(doctorMetrics);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
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
    icon: Icon, 
    description,
    color = "blue",
    trend
  }: {
    title: string;
    value: number | string;
    change?: number;
    icon: React.ElementType;
    description?: string;
    color?: string;
    trend?: 'up' | 'down' | 'stable';
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
                suffix={title.includes('Rate') || title.includes('Satisfaction') ? '%' : ''}
                decimals={title.includes('Time') ? 1 : 0}
              />
            ) : (
              value
            )}
          </div>
          {change !== undefined && (
            <div className="flex items-center pt-1">
              <TrendingUp className={`h-4 w-4 mr-1 ${trend === 'up' ? 'text-green-500' : 'text-red-500'}`} />
              <span className={`text-xs ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {change > 0 ? '+' : ''}{change}% from last week
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

  const AppointmentCard = ({ appointment }: { appointment: Appointment }) => (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback>
                {appointment.patientName.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h4 className="text-sm font-medium">{appointment.patientName}</h4>
              <p className="text-xs text-muted-foreground">{appointment.type}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">{appointment.time}</p>
            <Badge variant={
              appointment.status === 'completed' ? 'default' :
              appointment.status === 'scheduled' ? 'secondary' :
              'destructive'
            }>
              {appointment.status}
            </Badge>
          </div>
        </div>
        <Separator className="my-2" />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Duration: {appointment.duration}min
          </span>
          <div className="flex gap-2">
            {appointment.type === 'telemedicine' && (
              <Button size="sm" variant="outline" className="h-6 px-2">
                <Video className="h-3 w-3" />
              </Button>
            )}
            <Button size="sm" variant="outline" className="h-6 px-2">
              <MessageSquare className="h-3 w-3" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm" variant="outline" className="h-6 px-2">
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem>View Details</DropdownMenuItem>
                <DropdownMenuItem>Reschedule</DropdownMenuItem>
                <DropdownMenuItem>Cancel</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const PatientCard = ({ patient }: { patient: Patient }) => (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback>
                {patient.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h4 className="text-sm font-medium">{patient.name}</h4>
              <p className="text-xs text-muted-foreground">{patient.age} years • {patient.gender}</p>
            </div>
          </div>
          <Badge variant={
            patient.riskLevel === 'critical' ? 'destructive' :
            patient.riskLevel === 'high' ? 'destructive' :
            patient.riskLevel === 'medium' ? 'secondary' :
            'default'
          }>
            Risk: {patient.riskLevel}
          </Badge>
        </div>
        <Separator className="my-2" />
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Risk Score:</span>
            <span className="font-medium">{patient.riskScore}/10</span>
          </div>
          <Progress value={patient.riskScore * 10} className="h-1" />
          <div className="flex justify-between text-xs mt-2">
            <span className="text-muted-foreground">Last Visit:</span>
            <span>{patient.lastVisit}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Condition:</span>
            <span>{patient.condition}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const AlertCard = ({ alert }: { alert: Alert }) => (
    <Card className={`border-l-4 ${
      alert.type === 'urgent' ? 'border-l-red-500' :
      alert.type === 'warning' ? 'border-l-yellow-500' :
      'border-l-blue-500'
    }`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            {alert.type === 'urgent' ? (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            ) : alert.type === 'warning' ? (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            ) : (
              <Bell className="h-4 w-4 text-blue-500" />
            )}
            <div>
              <h4 className="text-sm font-medium">{alert.title}</h4>
              <p className="text-xs text-muted-foreground">{alert.description}</p>
            </div>
          </div>
          <Badge variant={alert.read ? 'secondary' : 'default'}>
            {alert.read ? 'Read' : 'New'}
          </Badge>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-muted-foreground">
            {new Date(alert.timestamp).toLocaleTimeString()}
          </span>
          {alert.actionRequired && (
            <Button size="sm" variant="outline" className="h-6 px-2">
              Take Action
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const performanceData = [
    { name: 'Mon', consultations: 12, satisfaction: 4.8 },
    { name: 'Tue', consultations: 15, satisfaction: 4.7 },
    { name: 'Wed', consultations: 18, satisfaction: 4.9 },
    { name: 'Thu', consultations: 14, satisfaction: 4.6 },
    { name: 'Fri', consultations: 16, satisfaction: 4.8 },
    { name: 'Sat', consultations: 8, satisfaction: 4.9 },
    { name: 'Sun', consultations: 6, satisfaction: 5.0 }
  ];

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Doctor Dashboard</h1>
          <p className="text-muted-foreground">
            Patient care and clinical management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Today
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Appointment
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Today's Appointments"
          value={metrics.appointments.today.length}
          change={8}
          trend="up"
          icon={Calendar}
          description={`${metrics.appointments.completed} completed`}
          color="blue"
        />
        <MetricCard
          title="Total Patients"
          value={metrics.patients.total}
          change={5}
          trend="up"
          icon={Users}
          description={`${metrics.patients.highRisk.length} high risk`}
          color="green"
        />
        <MetricCard
          title="Patient Satisfaction"
          value={metrics.performance.patientSatisfaction}
          change={0.2}
          trend="up"
          icon={Star}
          description="Average rating"
          color="yellow"
        />
        <MetricCard
          title="Consultation Time"
          value={metrics.performance.avgConsultationTime}
          change={-2}
          trend="up"
          icon={Clock}
          description="Average minutes"
          color="purple"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="today" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="today">Today's Schedule</TabsTrigger>
          <TabsTrigger value="patients">My Patients</TabsTrigger>
          <TabsTrigger value="alerts">Alerts & Notifications</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="history">Medical History</TabsTrigger>
        </TabsList>

        <TabsContent value="today" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    Today's Appointments
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">
                        <Search className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Filter className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardTitle>
                  <CardDescription>
                    {metrics.appointments.today.length} appointments scheduled for today
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {metrics.appointments.today.map((appointment) => (
                    <AppointmentCard key={appointment.id} appointment={appointment} />
                  ))}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Stats</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Completed Today</span>
                    <Badge variant="default">{metrics.appointments.completed}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Cancelled</span>
                    <Badge variant="destructive">{metrics.appointments.cancelled}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Pending Results</span>
                    <Badge variant="secondary">{metrics.patients.pendingResults}</Badge>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Completion Rate</span>
                      <span className="font-medium">{metrics.performance.completionRate}%</span>
                    </div>
                    <Progress value={metrics.performance.completionRate} className="h-2" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button className="w-full justify-start" variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Schedule Appointment
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <FileText className="h-4 w-4 mr-2" />
                    Write Prescription
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Heart className="h-4 w-4 mr-2" />
                    Update Vital Signs
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export Reports
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="patients" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>High Risk Patients</CardTitle>
                <CardDescription>Patients requiring immediate attention</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.patients.highRisk.map((patient) => (
                  <PatientCard key={patient.id} patient={patient} />
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Patient Overview</CardTitle>
                <CardDescription>Your patient portfolio summary</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{metrics.patients.total}</div>
                    <div className="text-sm text-muted-foreground">Total Patients</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{metrics.patients.highRisk.length}</div>
                    <div className="text-sm text-muted-foreground">High Risk</div>
                  </div>
                </div>
                
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Low Risk', value: 120, fill: '#22c55e' },
                        { name: 'Medium Risk', value: 25, fill: '#f59e0b' },
                        { name: 'High Risk', value: 8, fill: '#ef4444' },
                        { name: 'Critical', value: 3, fill: '#dc2626' }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Urgent Alerts</CardTitle>
                <CardDescription>Critical notifications requiring immediate action</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.alerts.urgentCases.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Weekly Performance</CardTitle>
                <CardDescription>Consultations and patient satisfaction trends</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="consultations" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Patient Satisfaction</span>
                    <span className="font-medium">{metrics.performance.patientSatisfaction}/5.0</span>
                  </div>
                  <Progress value={metrics.performance.patientSatisfaction * 20} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Completion Rate</span>
                    <span className="font-medium">{metrics.performance.completionRate}%</span>
                  </div>
                  <Progress value={metrics.performance.completionRate} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Efficiency Score</span>
                    <span className="font-medium">{metrics.performance.efficiency}%</span>
                  </div>
                  <Progress value={metrics.performance.efficiency} className="h-2" />
                </div>
                
                <Separator />
                
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {metrics.performance.avgConsultationTime}
                    </div>
                    <div className="text-xs text-muted-foreground">Avg Consultation (min)</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {metrics.performance.patientSatisfaction}
                    </div>
                    <div className="text-xs text-muted-foreground">Satisfaction Score</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2" />
                  History Mode
                </CardTitle>
                <CardDescription>
                  Comprehensive case history with audit trail visualization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg bg-blue-50">
                    <h4 className="font-medium text-blue-900 mb-2">Featured Capabilities</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• Complete medical case timeline</li>
                      <li>• Event filtering and prioritization</li>
                      <li>• HIPAA-compliant PHI access logging</li>
                      <li>• Care context and quality metrics</li>
                    </ul>
                  </div>
                  
                  <Button className="w-full" onClick={() => {
                    // Navigate to History Mode with demo case
                    window.location.href = '/doctor/history?case=demo-case-he-3849';
                  }}>
                    <Search className="h-4 w-4 mr-2" />
                    Open History Mode
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Linked Medical Timeline
                </CardTitle>
                <CardDescription>
                  Revolutionary symptom→treatment→outcome visualization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg bg-green-50">
                    <h4 className="font-medium text-green-900 mb-2">Advanced Features</h4>
                    <ul className="text-sm text-green-800 space-y-1">
                      <li>• Interactive event correlation analysis</li>
                      <li>• Care pathway visualization</li>
                      <li>• AI-powered pattern recognition</li>
                      <li>• Treatment outcome tracking</li>
                    </ul>
                  </div>
                  
                  <Button variant="outline" className="w-full" onClick={() => {
                    // Navigate to Linked GitBranch as Timeline with demo case
                    window.location.href = '/doctor/timeline?case=demo-case-he-3849';
                  }}>
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Open GitBranch as Timeline View
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DoctorDashboard;