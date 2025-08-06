import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Calendar,
  Clock,
  RefreshCw,
  Download,
  ArrowRight,
  ArrowDown,
  TrendingUp,
  TrendingDown,
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
  Eye,
  MoreHorizontal,
  GitBranch as Timeline,
  Zap,
  Target,
  Award,
  AlertCircle,
  Info,
  Filter,
  Search
} from 'lucide-react';

import doctorHistoryService, {
  LinkedTimelineResponse,
  LinkedTimelineEvent,
  TimelineFilters,
  EventType,
  EventPriority,
  CarePhase
} from '@/services/doctorHistory.service';

// ============================================
// INTERFACE DEFINITIONS
// ============================================

interface LinkedMedicalTimelineProps {
  caseId: string;
  className?: string;
  onEventSelect?: (event: LinkedTimelineEvent) => void;
  showFilters?: boolean;
}

interface TimelineNodeProps {
  event: LinkedTimelineEvent;
  isSelected?: boolean;
  connections: {
    incoming: LinkedTimelineEvent[];
    outgoing: LinkedTimelineEvent[];
  };
  onEventClick?: (event: LinkedTimelineEvent) => void;
  onShowConnections?: (eventId: string) => void;
}

interface CareCyclePathProps {
  pathway: LinkedTimelineEvent[];
  startEvent: LinkedTimelineEvent;
  endEvent: LinkedTimelineEvent;
  duration: number;
  isExpanded?: boolean;
  onToggle?: () => void;
}

// ============================================
// CONSTANTS & STYLES
// ============================================

const CARE_PHASE_COLORS = {
  ASSESSMENT: 'bg-blue-50 border-blue-200 text-blue-800',
  PLANNING: 'bg-purple-50 border-purple-200 text-purple-800',
  INTERVENTION: 'bg-green-50 border-green-200 text-green-800',
  EVALUATION: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  MAINTENANCE: 'bg-gray-50 border-gray-200 text-gray-800',
  TRANSITION: 'bg-orange-50 border-orange-200 text-orange-800',
  FOLLOW_UP: 'bg-indigo-50 border-indigo-200 text-indigo-800'
} as const;

const CONNECTION_STYLES = {
  DIRECT: 'stroke-green-500 stroke-2',
  PROBABLE: 'stroke-yellow-500 stroke-2 stroke-dasharray-4',
  SUSPECTED: 'stroke-gray-400 stroke-1 stroke-dasharray-2',
  TEMPORAL: 'stroke-blue-400 stroke-1'
} as const;

const EVENT_TYPE_ICONS = {
  ADMISSION: <Activity className="h-4 w-4" />,
  DISCHARGE: <ArrowRight className="h-4 w-4" />,
  DIAGNOSIS: <Eye className="h-4 w-4" />,
  MEDICATION: <Pill className="h-4 w-4" />,
  PROCEDURE: <Stethoscope className="h-4 w-4" />,
  LAB_RESULT: <TestTube className="h-4 w-4" />,
  IMAGING: <Camera className="h-4 w-4" />,
  CONSULTATION: <User className="h-4 w-4" />,
  VITAL_SIGNS: <Heart className="h-4 w-4" />,
  ALLERGIES: <AlertTriangle className="h-4 w-4" />,
  IMMUNIZATION: <Shield className="h-4 w-4" />,
  CARE_PLAN: <ClipboardList className="h-4 w-4" />,
  PROGRESS_NOTE: <Timeline className="h-4 w-4" />,
  DISCHARGE_SUMMARY: <Award className="h-4 w-4" />
} as const;

// ============================================
// TIMELINE NODE COMPONENT
// ============================================

const TimelineNode: React.FC<TimelineNodeProps> = ({
  event,
  isSelected = false,
  connections,
  onEventClick,
  onShowConnections
}) => {
  const carePhaseStyle = event.care_phase ? 
    CARE_PHASE_COLORS[event.care_phase as keyof typeof CARE_PHASE_COLORS] : 
    'bg-gray-50 border-gray-200 text-gray-800';
    
  const eventIcon = EVENT_TYPE_ICONS[event.event_type as keyof typeof EVENT_TYPE_ICONS] || <Timeline className="h-4 w-4" />;
  
  const hasConnections = connections.incoming.length > 0 || connections.outgoing.length > 0;
  
  return (
    <TooltipProvider>
      <motion.div
        className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
          isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
        } ${carePhaseStyle}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onEventClick?.(event)}
        layout
      >
        {/* Connection Indicators */}
        {hasConnections && (
          <div className="absolute -top-2 -right-2">
            <Badge variant="default" className="h-5 w-5 p-0 rounded-full flex items-center justify-center text-xs">
              {connections.incoming.length + connections.outgoing.length}
            </Badge>
          </div>
        )}
        
        {/* Priority Indicator */}
        <div className={`absolute -top-1 -left-1 w-3 h-3 rounded-full ${
          event.priority === 'CRITICAL' ? 'bg-red-500' :
          event.priority === 'HIGH' ? 'bg-orange-500' :
          event.priority === 'MEDIUM' ? 'bg-yellow-500' :
          'bg-blue-500'
        }`} />
        
        {/* Event Content */}
        <div className="space-y-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 rounded-full bg-white/50">
                {eventIcon}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-medium truncate">
                  {event.title}
                </h4>
                <div className="flex items-center text-xs text-gray-600 mt-1">
                  <Clock className="h-3 w-3 mr-1" />
                  {new Date(event.event_date).toLocaleString()}
                </div>
              </div>
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEventClick?.(event)}>
                  <Eye className="h-4 w-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onShowConnections?.(event.event_id)}>
                  <GitBranch className="h-4 w-4 mr-2" />
                  Show Connections
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Download className="h-4 w-4 mr-2" />
                  Export Event
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          {/* Event Metadata */}
          <div className="space-y-1">
            {event.provider_name && (
              <div className="flex items-center text-xs text-gray-600">
                <User className="h-3 w-3 mr-1" />
                {event.provider_name}
              </div>
            )}
            
            {event.care_phase && (
              <div className="flex items-center">
                <Badge variant="outline" className="text-xs">
                  {event.care_phase.replace('_', ' ')}
                </Badge>
              </div>
            )}
            
            {event.outcome_status && (
              <div className="flex items-center text-xs">
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  event.outcome_status.toLowerCase().includes('success') || event.outcome_status.toLowerCase().includes('resolved') ? 
                  'bg-green-100 text-green-800' :
                  event.outcome_status.toLowerCase().includes('failed') || event.outcome_status.toLowerCase().includes('adverse') ?
                  'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {event.outcome_status}
                </span>
              </div>
            )}
          </div>
          
          {/* Connection Preview */}
          {hasConnections && (
            <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-white/20">
              <div className="flex items-center space-x-2">
                {connections.incoming.length > 0 && (
                  <Tooltip>
                    <TooltipTrigger>
                      <div className="flex items-center">
                        <ArrowDown className="h-3 w-3 mr-1" />
                        {connections.incoming.length}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{connections.incoming.length} incoming connection{connections.incoming.length !== 1 ? 's' : ''}</p>
                    </TooltipContent>
                  </Tooltip>
                )}
                
                {connections.outgoing.length > 0 && (
                  <Tooltip>
                    <TooltipTrigger>
                      <div className="flex items-center">
                        <ArrowRight className="h-3 w-3 mr-1" />
                        {connections.outgoing.length}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{connections.outgoing.length} outgoing connection{connections.outgoing.length !== 1 ? 's' : ''}</p>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
              
              <Button
                size="sm"
                variant="ghost"
                className="h-5 px-2 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onShowConnections?.(event.event_id);
                }}
              >
                <GitBranch className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>
      </motion.div>
    </TooltipProvider>
  );
};

// ============================================
// CARE CYCLE PATH COMPONENT
// ============================================

const CareCyclePath: React.FC<CareCyclePathProps> = ({
  pathway,
  startEvent,
  endEvent,
  duration,
  isExpanded = false,
  onToggle
}) => {
  const durationDays = Math.ceil(duration / (1000 * 60 * 60 * 24));
  const isSuccessful = endEvent.outcome_status?.toLowerCase().includes('success') || 
                      endEvent.outcome_status?.toLowerCase().includes('resolved');
  
  return (
    <motion.div
      className={`border rounded-lg p-4 ${
        isSuccessful ? 'border-green-200 bg-green-50' : 
        endEvent.outcome_status?.toLowerCase().includes('failed') ? 'border-red-200 bg-red-50' :
        'border-blue-200 bg-blue-50'
      }`}
      layout
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-full ${
            isSuccessful ? 'bg-green-100' : 
            endEvent.outcome_status?.toLowerCase().includes('failed') ? 'bg-red-100' :
            'bg-blue-100'
          }`}>
            <GitBranch className="h-4 w-4" />
          </div>
          
          <div>
            <h4 className="font-medium text-sm">
              {startEvent.title} → {endEvent.title}
            </h4>
            <div className="flex items-center space-x-2 text-xs text-gray-600">
              <Clock className="h-3 w-3" />
              <span>{durationDays} days</span>
              <span>•</span>
              <span>{pathway.length} events</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {isSuccessful ? (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ) : endEvent.outcome_status?.toLowerCase().includes('failed') ? (
            <XCircle className="h-5 w-5 text-red-600" />
          ) : (
            <AlertCircle className="h-5 w-5 text-yellow-600" />
          )}
          
          <Button
            size="sm"
            variant="ghost"
            onClick={onToggle}
            className="h-6 px-2"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </div>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-2"
          >
            <Separator />
            <div className="flex items-center space-x-2 overflow-x-auto py-2">
              {pathway.map((event, index) => (
                <React.Fragment key={event.event_id}>
                  <div className="flex flex-col items-center min-w-0 flex-shrink-0">
                    <div className={`p-2 rounded-full text-white text-xs ${
                      event.priority === 'CRITICAL' ? 'bg-red-500' :
                      event.priority === 'HIGH' ? 'bg-orange-500' :
                      'bg-blue-500'
                    }`}>
                      {EVENT_TYPE_ICONS[event.event_type as keyof typeof EVENT_TYPE_ICONS]}
                    </div>
                    <span className="text-xs text-center mt-1 max-w-20 truncate">
                      {event.title}
                    </span>
                  </div>
                  
                  {index < pathway.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
            
            {endEvent.outcome_status && (
              <div className="flex items-center justify-between text-sm pt-2 border-t">
                <span className="font-medium">Outcome:</span>
                <Badge variant={isSuccessful ? 'default' : 'destructive'}>
                  {endEvent.outcome_status}
                </Badge>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const LinkedMedicalTimeline: React.FC<LinkedMedicalTimelineProps> = ({
  caseId,
  className = '',
  onEventSelect,
  showFilters = true
}) => {
  // ============================================
  // STATE MANAGEMENT
  // ============================================
  
  const [timelineData, setTimelineData] = useState<LinkedTimelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  
  // Filter states
  const [filters, setFilters] = useState<TimelineFilters>({});
  const [activeView, setActiveView] = useState<'timeline' | 'pathways' | 'correlations'>('timeline');
  
  // ============================================
  // DATA LOADING
  // ============================================
  
  const loadLinkedTimeline = useCallback(async () => {
    if (!caseId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await doctorHistoryService.getLinkedMedicalTimeline(caseId, filters);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setTimelineData(response.data!);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load linked timeline');
    } finally {
      setLoading(false);
    }
  }, [caseId, filters]);
  
  useEffect(() => {
    loadLinkedTimeline();
  }, [loadLinkedTimeline]);
  
  // ============================================
  // DATA PROCESSING
  // ============================================
  
  const processedData = useMemo(() => {
    if (!timelineData) return null;
    
    const events = timelineData.timeline_events;
    
    // Build connection map
    const connectionMap = new Map<string, { incoming: LinkedTimelineEvent[], outgoing: LinkedTimelineEvent[] }>();
    
    events.forEach(event => {
      connectionMap.set(event.event_id, { incoming: [], outgoing: [] });
    });
    
    // Process correlations
    Object.entries(timelineData.event_correlations).forEach(([eventId, relatedIds]) => {
      const sourceEvent = events.find(e => e.event_id === eventId);
      if (sourceEvent) {
        relatedIds.forEach(relatedId => {
          const relatedEvent = events.find(e => e.event_id === relatedId);
          if (relatedEvent) {
            connectionMap.get(eventId)?.outgoing.push(relatedEvent);
            connectionMap.get(relatedId)?.incoming.push(sourceEvent);
          }
        });
      }
    });
    
    // Extract care pathways
    const carePathways = doctorHistoryService.extractCarePathways(events);
    
    return {
      events,
      connectionMap,
      carePathways,
      phases: events.reduce((acc, event) => {
        if (event.care_phase) {
          if (!acc[event.care_phase]) acc[event.care_phase] = [];
          acc[event.care_phase].push(event);
        }
        return acc;
      }, {} as Record<string, LinkedTimelineEvent[]>)
    };
  }, [timelineData]);
  
  // ============================================
  // EVENT HANDLERS
  // ============================================
  
  const handleEventClick = (event: LinkedTimelineEvent) => {
    setSelectedEventId(event.event_id);
    onEventSelect?.(event);
  };
  
  const handleShowConnections = (eventId: string) => {
    setSelectedEventId(eventId);
    // Could implement a modal or side panel showing connections
  };
  
  const handleTogglePathExpansion = (pathwayIndex: number) => {
    setExpandedPaths(prev => {
      const newSet = new Set(prev);
      const key = `pathway-${pathwayIndex}`;
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };
  
  // ============================================
  // RENDER HELPERS
  // ============================================
  
  const renderTimelineView = () => {
    if (!processedData) return null;
    
    const sortedEvents = processedData.events.sort((a, b) => 
      new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
    );
    
    return (
      <div className="space-y-4">
        {sortedEvents.map((event, index) => {
          const connections = processedData.connectionMap.get(event.event_id) || { incoming: [], outgoing: [] };
          
          return (
            <motion.div
              key={event.event_id}
              className="relative"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* GitBranch as Timeline Line */}
              {index < sortedEvents.length - 1 && (
                <div className="absolute left-6 top-full w-0.5 h-4 bg-gray-200 z-0" />
              )}
              
              <TimelineNode
                event={event}
                isSelected={selectedEventId === event.event_id}
                connections={connections}
                onEventClick={handleEventClick}
                onShowConnections={handleShowConnections}
              />
            </motion.div>
          );
        })}
      </div>
    );
  };
  
  const renderPathwaysView = () => {
    if (!processedData?.carePathways) return null;
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium">Care Pathways</h3>
          <span className="text-sm text-gray-500">
            {processedData.carePathways.length} pathway{processedData.carePathways.length !== 1 ? 's' : ''} identified
          </span>
        </div>
        
        {processedData.carePathways.map((pathway, index) => (
          <CareCyclePath
            key={`pathway-${index}`}
            pathway={pathway.pathway}
            startEvent={pathway.startEvent}
            endEvent={pathway.endEvent}
            duration={pathway.duration}
            isExpanded={expandedPaths.has(`pathway-${index}`)}
            onToggle={() => handleTogglePathExpansion(index)}
          />
        ))}
        
        {processedData.carePathways.length === 0 && (
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No care pathways identified</p>
                <p className="text-sm text-gray-400">
                  Events may not have sufficient correlation data
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };
  
  const renderCorrelationsView = () => {
    if (!timelineData) return null;
    
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Event Correlations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(timelineData.event_correlations).map(([eventId, correlations]) => {
                  const event = timelineData.timeline_events.find(e => e.event_id === eventId);
                  return (
                    <div key={eventId} className="flex items-center justify-between text-sm">
                      <span className="truncate">{event?.title || 'Unknown Event'}</span>
                      <Badge variant="outline">{correlations.length}</Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Care Transitions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {timelineData.care_transitions.map((transition, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    <ArrowRight className="h-3 w-3 text-blue-500" />
                    <span>{JSON.stringify(transition)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };
  
  // ============================================
  // MAIN RENDER
  // ============================================
  
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
              <h3 className="text-lg font-medium text-red-900 mb-2">Error Loading Timeline</h3>
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadLinkedTimeline} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (!timelineData) {
    return null;
  }
  
  return (
    <div className={`p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <GitBranch className="h-8 w-8 mr-3 text-blue-600" />
            Linked Medical Timeline
          </h1>
          <p className="text-gray-600 mt-1">
            Interactive correlation analysis and care pathway visualization
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button size="sm" variant="outline" onClick={loadLinkedTimeline}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          
          <Button size="sm" variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Timeline
          </Button>
        </div>
      </div>
      
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{timelineData.total_linked_events}</div>
            <div className="text-sm text-gray-600">Linked Events</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{Object.keys(timelineData.event_correlations).length}</div>
            <div className="text-sm text-gray-600">Correlations</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{timelineData.care_transitions.length}</div>
            <div className="text-sm text-gray-600">Care Transitions</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{processedData?.carePathways.length || 0}</div>
            <div className="text-sm text-gray-600">Care Pathways</div>
          </CardContent>
        </Card>
      </div>
      
      {/* Main Content */}
      <Tabs value={activeView} onValueChange={(value) => setActiveView(value as typeof activeView)}>
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="pathways">Care Pathways</TabsTrigger>
          <TabsTrigger value="correlations">Correlations</TabsTrigger>
        </TabsList>
        
        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Interactive Medical Timeline</CardTitle>
              <CardDescription>
                Click events to explore connections and relationships
              </CardDescription>
            </CardHeader>
            <CardContent>
              {renderTimelineView()}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="pathways" className="space-y-4">
          {renderPathwaysView()}
        </TabsContent>
        
        <TabsContent value="correlations" className="space-y-4">
          {renderCorrelationsView()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LinkedMedicalTimeline;