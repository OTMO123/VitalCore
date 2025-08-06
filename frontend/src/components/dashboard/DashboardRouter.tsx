import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Stethoscope,
  User,
  ChevronDown,
  Settings,
  LogOut,
  Bell,
  Search,
  Menu,
  Home,
  Calendar,
  FileText,
  Users,
  BarChart3,
  Activity,
  Lock
} from 'lucide-react';
import { UserRole } from '@/types/dashboard';

// Import dashboard components
import AdminDashboard from './admin/AdminDashboard';
import DoctorDashboard from './doctor/DoctorDashboard';
import PatientDashboard from './patient/PatientDashboard';

interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  permissions: string[];
}

const DashboardRouter: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<UserRole>('admin');
  const [currentUser, setCurrentUser] = useState<User>({
    id: 'admin-1',
    name: 'Dr. Alex Administrator',
    email: 'admin@healthcare.com',
    role: 'admin',
    permissions: ['admin:all', 'doctor:view', 'patient:view']
  });
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Mock role switching for admin users
  const availableRoles: { value: UserRole; label: string; icon: React.ElementType; description: string; color: string }[] = [
    { 
      value: 'admin', 
      label: 'Administrator', 
      icon: Shield, 
      description: 'Full system access and management',
      color: 'blue'
    },
    { 
      value: 'doctor', 
      label: 'Healthcare Provider', 
      icon: Stethoscope, 
      description: 'Patient care and clinical management',
      color: 'green'
    },
    { 
      value: 'patient', 
      label: 'Patient View', 
      icon: User, 
      description: 'Personal health dashboard',
      color: 'purple'
    }
  ];

  const canSwitchRole = (role: UserRole): boolean => {
    return currentUser.permissions.includes('admin:all') || 
           currentUser.permissions.includes(`${role}:view`);
  };

  const handleRoleSwitch = (newRole: UserRole) => {
    if (canSwitchRole(newRole)) {
      setCurrentRole(newRole);
      
      // Update user context based on role
      switch (newRole) {
        case 'admin':
          setCurrentUser({
            ...currentUser,
            name: 'Dr. Alex Administrator',
            email: 'admin@healthcare.com'
          });
          break;
        case 'doctor':
          setCurrentUser({
            ...currentUser,
            name: 'Dr. Sarah Wilson',
            email: 'doctor@healthcare.com'
          });
          break;
        case 'patient':
          setCurrentUser({
            ...currentUser,
            name: 'John Patient',
            email: 'patient@healthcare.com'
          });
          break;
      }
    }
  };

  const getCurrentRoleData = () => {
    return availableRoles.find(role => role.value === currentRole);
  };

  const roleData = getCurrentRoleData();
  const RoleIcon = roleData?.icon || Shield;

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, roles: ['admin', 'doctor', 'patient'] },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, roles: ['admin', 'doctor'] },
    { id: 'patients', label: 'Patients', icon: Users, roles: ['admin', 'doctor'] },
    { id: 'appointments', label: 'Appointments', icon: Calendar, roles: ['admin', 'doctor', 'patient'] },
    { id: 'reports', label: 'Reports', icon: FileText, roles: ['admin', 'doctor'] },
    { id: 'system', label: 'System Health', icon: Activity, roles: ['admin'] },
  ];

  const renderDashboard = () => {
    switch (currentRole) {
      case 'admin':
        return <AdminDashboard />;
      case 'doctor':
        return <DoctorDashboard />;
      case 'patient':
        return <PatientDashboard />;
      default:
        return <AdminDashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ duration: 0.3 }}
            className="w-70 bg-white shadow-lg border-r border-gray-200 flex flex-col"
          >
            {/* Sidebar Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg bg-${roleData?.color}-100`}>
                  <RoleIcon className={`h-6 w-6 text-${roleData?.color}-600`} />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Healthcare Platform</h2>
                  <p className="text-sm text-gray-500">{roleData?.label}</p>
                </div>
              </div>
            </div>

            {/* Role Switcher */}
            <div className="p-4 border-b border-gray-200">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 block">
                Switch Role
              </label>
              <Select value={currentRole} onValueChange={handleRoleSwitch}>
                <SelectTrigger className="w-full">
                  <SelectValue>
                    <div className="flex items-center space-x-2">
                      <RoleIcon className="h-4 w-4" />
                      <span>{roleData?.label}</span>
                    </div>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {availableRoles.map((role) => {
                    const Icon = role.icon;
                    const canSwitch = canSwitchRole(role.value);
                    return (
                      <SelectItem 
                        key={role.value} 
                        value={role.value}
                        disabled={!canSwitch}
                        className={`${!canSwitch ? 'opacity-50' : ''}`}
                      >
                        <div className="flex items-center space-x-3 w-full">
                          <Icon className={`h-4 w-4 text-${role.color}-500`} />
                          <div className="flex-1">
                            <div className="font-medium">{role.label}</div>
                            <div className="text-xs text-muted-foreground">{role.description}</div>
                          </div>
                          {!canSwitch && <Lock className="h-3 w-3" />}
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 block">
                Navigation
              </label>
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isAvailable = item.roles.includes(currentRole);
                return (
                  <Button
                    key={item.id}
                    variant={item.id === 'dashboard' ? 'default' : 'ghost'}
                    className={`w-full justify-start ${!isAvailable ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={!isAvailable}
                  >
                    <Icon className="h-4 w-4 mr-3" />
                    {item.label}
                    {!isAvailable && <Lock className="h-3 w-3 ml-auto" />}
                  </Button>
                );
              })}
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-gray-200">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="w-full justify-start p-2">
                    <Avatar className="h-8 w-8 mr-3">
                      <AvatarFallback>
                        {currentUser.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium">{currentUser.name}</div>
                      <div className="text-xs text-gray-500">{currentUser.email}</div>
                    </div>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Bell className="h-4 w-4 mr-2" />
                    Notifications
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-red-600">
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              
              <div className="flex items-center space-x-2">
                <Badge variant="outline" className={`border-${roleData?.color}-200 text-${roleData?.color}-700`}>
                  <RoleIcon className="h-3 w-3 mr-1" />
                  {roleData?.label}
                </Badge>
                {currentUser.role === 'admin' && currentRole !== 'admin' && (
                  <Badge variant="secondary">
                    <Shield className="h-3 w-3 mr-1" />
                    Admin View
                  </Badge>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                <Search className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute -top-1 -right-1 h-2 w-2 bg-red-500 rounded-full"></span>
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <div className="text-sm">
                <div className="font-medium">{currentUser.name}</div>
                <div className="text-gray-500">Viewing as {roleData?.label}</div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentRole}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {renderDashboard()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Role Switch Notification */}
      <AnimatePresence>
        {currentUser.role === 'admin' && currentRole !== 'admin' && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 z-50"
          >
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <Shield className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      Admin Override Active
                    </p>
                    <p className="text-xs text-blue-700">
                      You're viewing the {roleData?.label} dashboard as an administrator
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleRoleSwitch('admin')}
                    className="border-blue-300 text-blue-700 hover:bg-blue-100"
                  >
                    Return to Admin
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DashboardRouter;