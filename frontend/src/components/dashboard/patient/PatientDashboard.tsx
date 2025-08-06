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
  AreaChart, 
  Area, 
  BarChart, 
  Bar,
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
  Heart,
  Activity,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Download,
  Share,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  User,
  Phone,
  MessageSquare,
  Bell,
  Settings,
  RefreshCw,
  Plus,
  TrendingUp,
  TrendingDown,
  Shield,
  Thermometer,
  Droplets,
  Weight,
  Zap,
  Stethoscope
} from 'lucide-react';
import { PatientMetrics, Appointment, VitalSign, LabResult, AccessLog } from '@/types/dashboard';
import { MockDataService } from '@/lib/mock-data';

const PatientDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PatientMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [privacyMode, setPrivacyMode] = useState(false);

  const mockService = MockDataService.getInstance();

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const patientMetrics = await mockService.getPatientMetrics();
        setMetrics(patientMetrics);
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
    status, 
    icon: Icon, 
    description,
    color = "blue",
    trend
  }: {
    title: string;
    value: string | number;
    status?: 'normal' | 'warning' | 'critical';
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
      <Card className={`hover:shadow-lg transition-shadow duration-200 ${
        status === 'critical' ? 'border-red-200 bg-red-50' :
        status === 'warning' ? 'border-yellow-200 bg-yellow-50' :
        'border-gray-200'
      }`}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <Icon className={`h-4 w-4 ${
            status === 'critical' ? 'text-red-500' :
            status === 'warning' ? 'text-yellow-500' :
            `text-${color}-500`
          }`} />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {value}
          </div>
          {trend && (
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
                {trend === 'stable' ? 'Stable' : 'Trending ' + trend}
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

  const VitalSignCard = ({ vital }: { vital: VitalSign }) => {
    const getVitalIcon = (type: string) => {
      switch (type) {
        case 'blood_pressure': return Droplets;
        case 'heart_rate': return Heart;
        case 'temperature': return Thermometer;
        case 'weight': return Weight;
        case 'glucose': return Zap;
        default: return Activity;
      }
    };

    const Icon = getVitalIcon(vital.type);

    return (
      <Card className={`hover:shadow-md transition-shadow duration-200 ${
        !vital.normal ? 'border-yellow-200 bg-yellow-50' : ''
      }`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Icon className={`h-8 w-8 ${vital.normal ? 'text-green-500' : 'text-yellow-500'}`} />
              <div>
                <h4 className="text-sm font-medium capitalize">
                  {vital.type.replace('_', ' ')}
                </h4>
                <p className="text-lg font-bold">{vital.value} {vital.unit}</p>
              </div>
            </div>
            <div className="text-right">
              <Badge variant={vital.normal ? 'default' : 'secondary'}>
                {vital.normal ? 'Normal' : 'Monitor'}
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">
                {new Date(vital.timestamp).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const AppointmentCard = ({ appointment }: { appointment: Appointment }) => (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback>
                <Stethoscope className="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <div>
              <h4 className="text-sm font-medium">{appointment.doctorName}</h4>
              <p className="text-xs text-muted-foreground">{appointment.type}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">{appointment.date}</p>
            <p className="text-sm font-medium">{appointment.time}</p>
          </div>
        </div>
        <Separator className="my-2" />
        <div className="flex items-center justify-between">
          <Badge variant={
            appointment.status === 'completed' ? 'default' :
            appointment.status === 'scheduled' ? 'secondary' :
            'destructive'
          }>
            {appointment.status}
          </Badge>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="h-6 px-2">
              <MessageSquare className="h-3 w-3" />
            </Button>
            <Button size="sm" variant="outline" className="h-6 px-2">
              <Phone className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const LabResultCard = ({ result }: { result: LabResult }) => (
    <Card className={`hover:shadow-md transition-shadow duration-200 ${
      result.status === 'critical' ? 'border-red-200 bg-red-50' :
      result.status === 'abnormal' ? 'border-yellow-200 bg-yellow-50' :
      ''
    }`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium">{result.test}</h4>
            <p className="text-lg font-bold">{result.result}</p>
            <p className="text-xs text-muted-foreground">Reference: {result.reference}</p>
          </div>
          <div className="text-right">
            <Badge variant={
              result.status === 'critical' ? 'destructive' :
              result.status === 'abnormal' ? 'secondary' :
              'default'
            }>
              {result.status}
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">{result.date}</p>
          </div>
        </div>
        {result.notes && (
          <>
            <Separator className="my-2" />
            <p className="text-xs text-muted-foreground">{result.notes}</p>
          </>
        )}
      </CardContent>
    </Card>
  );

  const AccessLogCard = ({ log }: { log: AccessLog }) => (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              log.authorized ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <div>
              <p className="text-sm font-medium">{log.accessor}</p>
              <p className="text-xs text-muted-foreground">{log.action}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium">
              {new Date(log.timestamp).toLocaleString()}
            </p>
            <p className="text-xs text-muted-foreground">{log.ipAddress}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Mock vital signs data for chart
  const vitalSignsHistory = [
    { date: '2024-06-25', bloodPressure: 118, heartRate: 68, weight: 70 },
    { date: '2024-06-26', bloodPressure: 120, heartRate: 72, weight: 70.2 },
    { date: '2024-06-27', bloodPressure: 119, heartRate: 70, weight: 70.1 },
    { date: '2024-06-28', bloodPressure: 121, heartRate: 74, weight: 70.3 },
    { date: '2024-06-29', bloodPressure: 120, heartRate: 72, weight: 70.2 },
    { date: '2024-06-30', bloodPressure: 120, heartRate: 72, weight: 70.2 }
  ];

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Health Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {metrics.profile.name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setPrivacyMode(!privacyMode)}
          >
            {privacyMode ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {privacyMode ? 'Show Data' : 'Privacy Mode'}
          </Button>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Book Appointment
          </Button>
        </div>
      </div>

      {/* Health Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Health Score"
          value={`${Math.round((10 - metrics.health.riskScore) * 10)}%`}
          status={metrics.health.riskScore > 7 ? 'critical' : metrics.health.riskScore > 4 ? 'warning' : 'normal'}
          trend={metrics.health.healthTrend === 'improving' ? 'up' : metrics.health.healthTrend === 'declining' ? 'down' : 'stable'}
          icon={Heart}
          description={`Risk level: ${metrics.health.riskScore}/10`}
          color="red"
        />
        <MetricCard
          title="Next Appointment"
          value={metrics.appointments.next ? new Date(metrics.appointments.next.date).toLocaleDateString() : 'None scheduled'}
          icon={Calendar}
          description={metrics.appointments.next ? metrics.appointments.next.doctorName : 'Book your next visit'}
          color="blue"
        />
        <MetricCard
          title="Pending Results"
          value={metrics.results.pending}
          status={metrics.results.pending > 0 ? 'warning' : 'normal'}
          icon={FileText}
          description={`${metrics.results.recent.length} recent results`}
          color="green"
        />
        <MetricCard
          title="Last Checkup"
          value={new Date(metrics.health.lastCheckup).toLocaleDateString()}
          icon={Activity}
          description="Regular checkups recommended"
          color="purple"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Health Overview</TabsTrigger>
          <TabsTrigger value="vitals">Vital Signs</TabsTrigger>
          <TabsTrigger value="appointments">Appointments</TabsTrigger>
          <TabsTrigger value="results">Lab Results</TabsTrigger>
          <TabsTrigger value="privacy">Privacy & Access</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Health Trends</CardTitle>
                  <CardDescription>Your vital signs over the past week</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={vitalSignsHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                      <YAxis />
                      <Tooltip labelFormatter={(value) => new Date(value).toLocaleDateString()} />
                      <Legend />
                      <Line type="monotone" dataKey="heartRate" stroke="#ef4444" name="Heart Rate (bpm)" />
                      <Line type="monotone" dataKey="bloodPressure" stroke="#3b82f6" name="Blood Pressure (systolic)" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Current Vital Signs</CardTitle>
                  <CardDescription>Latest readings from your health monitoring</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {metrics.health.vitalSigns.map((vital) => (
                    <VitalSignCard key={vital.id} vital={vital} />
                  ))}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Health Profile</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-16 w-16">
                      <AvatarFallback className="text-lg">
                        {metrics.profile.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="font-medium">{metrics.profile.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {metrics.profile.age} years • {metrics.profile.gender}
                      </p>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Blood Type:</span>
                      <span className="font-medium">{metrics.profile.bloodType}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Allergies:</span>
                      <span className="font-medium">{metrics.profile.allergies.join(', ')}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Risk Score:</span>
                      <Badge variant={metrics.health.riskScore > 7 ? 'destructive' : metrics.health.riskScore > 4 ? 'secondary' : 'default'}>
                        {metrics.health.riskScore}/10
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button className="w-full justify-start" variant="outline">
                    <Calendar className="h-4 w-4 mr-2" />
                    Book Appointment
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Message Doctor
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download Records
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Bell className="h-4 w-4 mr-2" />
                    Set Reminders
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="vitals" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {metrics.health.vitalSigns.map((vital) => (
              <VitalSignCard key={vital.id} vital={vital} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="appointments" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Upcoming Appointments</CardTitle>
                <CardDescription>Your scheduled medical appointments</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.appointments.next && (
                  <AppointmentCard appointment={metrics.appointments.next} />
                )}
                {metrics.appointments.upcoming.length === 0 && !metrics.appointments.next && (
                  <div className="text-center py-8">
                    <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No upcoming appointments</p>
                    <Button className="mt-4" size="sm">
                      Book Appointment
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Appointments</CardTitle>
                <CardDescription>Your appointment history</CardDescription>
              </CardHeader>
              <CardContent>
                {metrics.appointments.recent.length === 0 ? (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No recent appointments</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {metrics.appointments.recent.map((appointment) => (
                      <AppointmentCard key={appointment.id} appointment={appointment} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <div className="grid grid-cols-1 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Lab Results</CardTitle>
                <CardDescription>Your recent test results and findings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.results.recent.map((result) => (
                  <LabResultCard key={result.id} result={result} />
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="privacy" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Privacy Settings</CardTitle>
                <CardDescription>Control who can access your health information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium">Data Sharing</h4>
                    <p className="text-xs text-muted-foreground">Allow sharing for research purposes</p>
                  </div>
                  <Button variant={metrics.privacy.dataSharing ? 'default' : 'outline'} size="sm">
                    {metrics.privacy.dataSharing ? <Unlock className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
                  </Button>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="text-sm font-medium mb-2">Authorized Healthcare Providers</h4>
                  <div className="space-y-2">
                    {metrics.privacy.authorizedDoctors.map((doctor, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded">
                        <span className="text-sm">{doctor}</span>
                        <Badge variant="default">Active</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Access Log</CardTitle>
                <CardDescription>Recent access to your health records</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {metrics.privacy.accessLog.map((log) => (
                  <AccessLogCard key={log.id} log={log} />
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PatientDashboard;