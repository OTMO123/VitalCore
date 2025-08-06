import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import {
  Calendar,
  Clock,
  Search,
  Filter,
  Download,
  RefreshCw,
  History,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Activity,
  User,
  Stethoscope,
  Heart,
  TestTube,
  Camera,
  Pill,
  ClipboardList,
  Shield,
  ArrowRight,
  Eye,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Info,
  GitBranch as Timeline
} from 'lucide-react';

import doctorHistoryService, {
  DoctorHistoryResponse,
  MedicalEvent,
  CaseSummary,
  TimelineFilters,
  EventType,
  EventPriority
} from '@/services/doctorHistory.service';

// ============================================
// INTERFACE DEFINITIONS
// ============================================

interface DoctorHistoryModeProps {
  caseId?: string;
  onCaseSelect?: (caseId: string) => void;
  className?: string;
}

interface EventCardProps {
  event: MedicalEvent;
  isExpanded?: boolean;
  onToggleExpand?: (eventId: string) => void;
  showConnections?: boolean;
}

// ============================================
// GOOGLE-STYLE DESIGN CONSTANTS
// ============================================

const COLORS = {
  primary: '#2F80ED',
  background: '#FFFFFF',
  surface: '#F5F5F5',
  text: '#333333',
  textSecondary: '#666666',
  success: '#27AE60',
  warning: '#F39C12',
  error: '#EB5757',
  info: '#2F80ED'
} as const;

const PRIORITY_STYLES = {
  CRITICAL: 'border-l-4 border-l-red-500 bg-red-50',
  HIGH: 'border-l-4 border-l-orange-500 bg-orange-50',
  MEDIUM: 'border-l-4 border-l-yellow-500 bg-yellow-50',
  LOW: 'border-l-4 border-l-blue-500 bg-blue-50',
  INFO: 'border-l-4 border-l-gray-500 bg-gray-50'
} as const;

const EVENT_TYPE_ICONS = {
  ADMISSION: <Activity className="h-4 w-4" />,
  DISCHARGE: <FileText className="h-4 w-4" />,
  DIAGNOSIS: <Search className="h-4 w-4" />,
  MEDICATION: <Pill className="h-4 w-4" />,
  PROCEDURE: <Stethoscope className="h-4 w-4" />,
  LAB_RESULT: <TestTube className="h-4 w-4" />,
  IMAGING: <Camera className="h-4 w-4" />,
  CONSULTATION: <User className="h-4 w-4" />,
  VITAL_SIGNS: <Heart className="h-4 w-4" />,
  ALLERGIES: <AlertTriangle className="h-4 w-4" />,
  IMMUNIZATION: <Shield className="h-4 w-4" />,
  CARE_PLAN: <ClipboardList className="h-4 w-4" />,
  PROGRESS_NOTE: <FileText className="h-4 w-4" />,
  DISCHARGE_SUMMARY: <FileText className="h-4 w-4" />
} as const;

// ============================================
// EVENT CARD COMPONENT
// ============================================

const EventCard: React.FC<EventCardProps> = ({ 
  event, 
  isExpanded = false, 
  onToggleExpand,
  showConnections = false
}) => {
  const priorityStyle = PRIORITY_STYLES[event.priority as keyof typeof PRIORITY_STYLES] || PRIORITY_STYLES.INFO;
  const eventIcon = EVENT_TYPE_ICONS[event.event_type as keyof typeof EVENT_TYPE_ICONS] || <FileText className="h-4 w-4" />;
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <Card className={`hover:shadow-md transition-shadow duration-200 ${priorityStyle}`}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-grow">
              {/* Event Type Icon */}
              <div className={`p-2 rounded-full ${
                event.priority === 'CRITICAL' ? 'bg-red-100' :
                event.priority === 'HIGH' ? 'bg-orange-100' :
                event.priority === 'MEDIUM' ? 'bg-yellow-100' :
                'bg-blue-100'
              }`}>
                {eventIcon}
              </div>
              
              {/* Event Details */}
              <div className="flex-grow min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {event.title}
                  </h4>
                  <Badge 
                    variant={
                      event.priority === 'CRITICAL' ? 'destructive' :
                      event.priority === 'HIGH' ? 'destructive' :
                      event.priority === 'MEDIUM' ? 'secondary' :
                      'default'
                    }
                    className="text-xs"
                  >
                    {event.priority}
                  </Badge>
                </div>
                
                {/* Event Metadata */}
                <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                  <span className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {doctorHistoryService.formatEventDate(event.event_date)}
                  </span>
                  {event.provider_name && (
                    <span className="flex items-center">
                      <User className="h-3 w-3 mr-1" />
                      {event.provider_name}
                    </span>
                  )}
                  {event.location && (
                    <span className="flex items-center">
                      📍 {event.location}
                    </span>
                  )}
                </div>
                
                {/* Event Description */}
                {event.description && (
                  <p className={`text-sm text-gray-600 ${
                    isExpanded ? '' : 'line-clamp-2'
                  }`}>
                    {event.description}
                  </p>
                )}
                
                {/* Linked Events Preview */}
                {showConnections && event.linked_events && event.linked_events.length > 0 && (
                  <div className="mt-2 flex items-center space-x-2">
                    <ArrowRight className="h-3 w-3 text-gray-400" />
                    <span className="text-xs text-gray-500">
                      Connected to {event.linked_events.length} event{event.linked_events.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center space-x-2 ml-4">
              {event.description && (
                <Button 
                  size="sm" 
                  variant="ghost"
                  className="h-6 px-2"
                  onClick={() => onToggleExpand?.(event.event_id)}
                >
                  {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </Button>
              )}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" className="h-6 px-2">
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Timeline className="h-4 w-4 mr-2" />
                    Show in Timeline
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <Download className="h-4 w-4 mr-2" />
                    Export Event
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const DoctorHistoryMode: React.FC<DoctorHistoryModeProps> = ({
  caseId,
  onCaseSelect,
  className = ''
}) => {
  // ============================================
  // STATE MANAGEMENT
  // ============================================
  
  const [historyData, setHistoryData] = useState<DoctorHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEventTypes, setSelectedEventTypes] = useState<Array<keyof EventType>>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<Array<keyof EventPriority>>([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');
  
  // UI states
  const [activeView, setActiveView] = useState<'list' | 'timeline'>('list');
  
  // ============================================
  // DATA LOADING
  // ============================================
  
  const loadCaseHistory = useCallback(async (targetCaseId: string) => {
    if (!targetCaseId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const filters: TimelineFilters = {};
      
      if (selectedEventTypes.length > 0) filters.event_types = selectedEventTypes;
      if (selectedPriorities.length > 0) filters.priority_levels = selectedPriorities;
      if (dateFrom) filters.date_from = dateFrom;
      if (dateTo) filters.date_to = dateTo;
      if (selectedProvider) filters.provider_filter = selectedProvider;
      
      const response = await doctorHistoryService.getCaseHistory(targetCaseId, filters);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setHistoryData(response.data!);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load case history');
    } finally {
      setLoading(false);
    }
  }, [selectedEventTypes, selectedPriorities, dateFrom, dateTo, selectedProvider]);
  
  // Load data when caseId changes
  useEffect(() => {
    if (caseId) {
      loadCaseHistory(caseId);
    }
  }, [caseId, loadCaseHistory]);
  
  // ============================================
  // EVENT HANDLERS
  // ============================================
  
  const handleRefresh = () => {
    if (caseId) {
      loadCaseHistory(caseId);
    }
  };
  
  const handleEventToggleExpand = (eventId: string) => {
    setExpandedEvents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };
  
  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedEventTypes([]);
    setSelectedPriorities([]);
    setDateFrom('');
    setDateTo('');
    setSelectedProvider('');
  };
  
  // ============================================
  // DATA FILTERING
  // ============================================
  
  const filteredEvents = React.useMemo(() => {
    if (!historyData?.timeline_events) return [];
    
    return historyData.timeline_events.filter(event => {
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        if (!event.title.toLowerCase().includes(searchLower) &&
            !event.description?.toLowerCase().includes(searchLower) &&
            !event.provider_name?.toLowerCase().includes(searchLower)) {
          return false;
        }
      }
      
      // Event type filter
      if (selectedEventTypes.length > 0 && !selectedEventTypes.includes(event.event_type as keyof EventType)) {
        return false;
      }
      
      // Priority filter
      if (selectedPriorities.length > 0 && !selectedPriorities.includes(event.priority as keyof EventPriority)) {
        return false;
      }
      
      return true;
    }).sort((a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime());
  }, [historyData?.timeline_events, searchTerm, selectedEventTypes, selectedPriorities]);
  
  // ============================================
  // RENDER HELPERS
  // ============================================
  
  const renderCaseSummary = (caseSummary: CaseSummary) => (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <span>{caseSummary.case_title}</span>
            </CardTitle>
            <CardDescription>
              Case #{caseSummary.case_id} • Started {doctorHistoryService.formatEventDate(caseSummary.start_date)}
            </CardDescription>
          </div>
          <Badge variant={caseSummary.case_status === 'active' ? 'default' : 'secondary'}>
            {caseSummary.case_status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{caseSummary.total_events}</div>
            <div className="text-sm text-blue-600">Total Events</div>
          </div>
          
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{caseSummary.critical_events}</div>
            <div className="text-sm text-red-600">Critical Events</div>
          </div>
          
          {caseSummary.length_of_stay && (
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{caseSummary.length_of_stay}</div>
              <div className="text-sm text-green-600">Days</div>
            </div>
          )}
        </div>
        
        {caseSummary.primary_diagnosis && (
          <div>
            <Label className="text-sm font-medium">Primary Diagnosis</Label>
            <p className="text-sm text-gray-600 mt-1">{caseSummary.primary_diagnosis}</p>
          </div>
        )}
        
        {caseSummary.attending_physician && (
          <div>
            <Label className="text-sm font-medium">Attending Physician</Label>
            <p className="text-sm text-gray-600 mt-1">{caseSummary.attending_physician}</p>
          </div>
        )}
        
        {caseSummary.care_team && caseSummary.care_team.length > 0 && (
          <div>
            <Label className="text-sm font-medium">Care Team</Label>
            <div className="flex flex-wrap gap-1 mt-1">
              {caseSummary.care_team.map((member, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {member}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
  
  const renderFilters = () => (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center">
            <Filter className="h-4 w-4 mr-2" />
            Filters & Search
          </span>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleClearFilters}
            className="text-xs"
          >
            Clear All
          </Button>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Search Bar */}
        <div className="flex space-x-2">
          <div className="flex-1">
            <Input
              placeholder="Search events, descriptions, providers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          <Button size="icon" variant="outline">
            <Search className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Filter Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Label className="text-sm font-medium">Event Types</Label>
            <Select>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="DIAGNOSIS">Diagnosis</SelectItem>
                <SelectItem value="MEDICATION">Medication</SelectItem>
                <SelectItem value="LAB_RESULT">Lab Results</SelectItem>
                <SelectItem value="PROCEDURE">Procedures</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label className="text-sm font-medium">Priority</Label>
            <Select>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="All priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="CRITICAL">Critical</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label className="text-sm font-medium">Date From</Label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          
          <div>
            <Label className="text-sm font-medium">Date To</Label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
  
  // ============================================
  // MAIN RENDER
  // ============================================
  
  if (!caseId) {
    return (
      <div className={`p-6 ${className}`}>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <History className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Case</h3>
              <p className="text-gray-500 mb-4">
                Choose a case to view comprehensive medical history
              </p>
              <Button onClick={() => onCaseSelect?.('demo-case-id')}>
                <Search className="h-4 w-4 mr-2" />
                Search Cases
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center justify-center py-12">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <RefreshCw className="h-8 w-8 text-blue-500" />
          </motion.div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <Card className="border-red-200">
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-red-900 mb-2">Error Loading Case History</h3>
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={handleRefresh} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (!historyData) {
    return null;
  }
  
  return (
    <div className={`p-6 space-y-6 bg-gray-50 min-h-screen ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <History className="h-8 w-8 mr-3 text-blue-600" />
            Doctor History Mode
          </h1>
          <p className="text-gray-600 mt-1">
            Comprehensive patient medical history and timeline analysis
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button size="sm" variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          
          <Button size="sm" variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          
          <Button size="sm">
            <Timeline className="h-4 w-4 mr-2" />
            GitBranch as Timeline View
          </Button>
        </div>
      </div>
      
      {/* Case Summary */}
      {renderCaseSummary(historyData.case_summary)}
      
      {/* Filters */}
      {renderFilters()}
      
      {/* Main Content */}
      <Tabs value={activeView} onValueChange={(value) => setActiveView(value as 'list' | 'timeline')}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="list">History List</TabsTrigger>
          <TabsTrigger value="timeline">Timeline View</TabsTrigger>
        </TabsList>
        
        <TabsContent value="list" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Medical Events ({filteredEvents.length})</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">
                    Last updated: {doctorHistoryService.formatEventDate(historyData.generated_at)}
                  </span>
                </div>
              </CardTitle>
              <CardDescription>
                Complete chronological history of medical events and interventions
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <AnimatePresence>
                {filteredEvents.map((event) => (
                  <EventCard
                    key={event.event_id}
                    event={event}
                    isExpanded={expandedEvents.has(event.event_id)}
                    onToggleExpand={handleEventToggleExpand}
                    showConnections={true}
                  />
                ))}
              </AnimatePresence>
              
              {filteredEvents.length === 0 && (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No events found matching your filters</p>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="mt-2"
                    onClick={handleClearFilters}
                  >
                    Clear Filters
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center">
                <Timeline className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Timeline View</h3>
                <p className="text-gray-500 mb-4">
                  Interactive timeline visualization will be implemented here
                </p>
                <Button variant="outline">
                  <ArrowRight className="h-4 w-4 mr-2" />
                  Switch to Linked Timeline
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DoctorHistoryMode;