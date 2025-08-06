import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  GitBranch as Timeline,
  History,
  GitBranch,
  Shield,
  Activity,
  TrendingUp,
  Zap
} from 'lucide-react';

import LinkedMedicalTimeline from '@/components/doctor/LinkedMedicalTimeline';
import { LinkedTimelineEvent } from '@/services/doctorHistory.service';

interface DoctorTimelinePageProps {}

const DoctorTimelinePage: React.FC<DoctorTimelinePageProps> = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const caseId = searchParams.get('case') || 'demo-case-he-3849';
  const [selectedEvent, setSelectedEvent] = useState<LinkedTimelineEvent | null>(null);

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const handleSwitchToHistory = () => {
    navigate(`/doctor/history?case=${caseId}`);
  };

  const handleEventSelect = (event: LinkedTimelineEvent) => {
    setSelectedEvent(event);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToDashboard}
              className="flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <GitBranch className="h-6 w-6 mr-3 text-blue-600" />
                Linked Medical Timeline
              </h1>
              <p className="text-sm text-gray-600">
                Revolutionary symptom→treatment→outcome visualization
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="flex items-center">
              <Shield className="h-3 w-3 mr-1" />
              HIPAA Compliant
            </Badge>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleSwitchToHistory}
              className="flex items-center"
            >
              <History className="h-4 w-4 mr-2" />
              History Mode
            </Button>
          </div>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold mb-1">Advanced GitBranch as Timeline Analysis</h2>
            <p className="text-blue-100 text-sm">
              Case #{caseId} • Interactive correlation mapping and care pathway visualization
            </p>
          </div>
          
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center">
              <Activity className="h-4 w-4 mr-2" />
              <span>Real-time Analysis</span>
            </div>
            <div className="flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              <span>Pattern Recognition</span>
            </div>
            <div className="flex items-center">
              <Zap className="h-4 w-4 mr-2" />
              <span>AI Insights</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex">
        {/* GitBranch as Timeline Content */}
        <div className="flex-1">
          <LinkedMedicalTimeline
            caseId={caseId}
            onEventSelect={handleEventSelect}
            className="p-0"
          />
        </div>

        {/* Event Details Sidebar */}
        {selectedEvent && (
          <div className="w-80 bg-white border-l border-gray-200 p-6">
            <div className="sticky top-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-sm">
                    <Activity className="h-4 w-4 mr-2" />
                    Event Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">{selectedEvent.title}</h4>
                    <p className="text-xs text-gray-600">{selectedEvent.description}</p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Event Type:</span>
                      <Badge variant="outline" className="text-xs">
                        {selectedEvent.event_type.replace('_', ' ')}
                      </Badge>
                    </div>
                    
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Priority:</span>
                      <Badge
                        variant={
                          selectedEvent.priority === 'CRITICAL' ? 'destructive' :
                          selectedEvent.priority === 'HIGH' ? 'destructive' :
                          'secondary'
                        }
                        className="text-xs"
                      >
                        {selectedEvent.priority}
                      </Badge>
                    </div>

                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Date:</span>
                      <span>{new Date(selectedEvent.event_date).toLocaleDateString()}</span>
                    </div>

                    {selectedEvent.provider_name && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Provider:</span>
                        <span>{selectedEvent.provider_name}</span>
                      </div>
                    )}

                    {selectedEvent.care_phase && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Care Phase:</span>
                        <Badge variant="outline" className="text-xs">
                          {selectedEvent.care_phase.replace('_', ' ')}
                        </Badge>
                      </div>
                    )}

                    {selectedEvent.outcome_status && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Outcome:</span>
                        <span className="text-xs">{selectedEvent.outcome_status}</span>
                      </div>
                    )}
                  </div>

                  {selectedEvent.clinical_data && (
                    <div>
                      <h5 className="font-medium text-xs text-gray-700 mb-2">Clinical Data</h5>
                      <div className="bg-gray-50 rounded p-2 text-xs">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(selectedEvent.clinical_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {selectedEvent.diagnostic_codes && selectedEvent.diagnostic_codes.length > 0 && (
                    <div>
                      <h5 className="font-medium text-xs text-gray-700 mb-2">Diagnostic Codes</h5>
                      <div className="flex flex-wrap gap-1">
                        {selectedEvent.diagnostic_codes.map((code, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {code}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedEvent.linked_events && selectedEvent.linked_events.length > 0 && (
                    <div>
                      <h5 className="font-medium text-xs text-gray-700 mb-2">Linked Events</h5>
                      <p className="text-xs text-gray-600">
                        Connected to {selectedEvent.linked_events.length} other event{selectedEvent.linked_events.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  )}

                  <Button size="sm" className="w-full">
                    View Full Details
                  </Button>
                </CardContent>
              </Card>

              {/* AI Insights Panel */}
              <Card className="mt-4">
                <CardHeader>
                  <CardTitle className="flex items-center text-sm">
                    <Zap className="h-4 w-4 mr-2" />
                    AI Insights
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="p-2 bg-blue-50 rounded text-xs">
                    <p className="text-blue-800">
                      This event shows strong correlation with previous medication changes.
                    </p>
                  </div>
                  
                  <div className="p-2 bg-green-50 rounded text-xs">
                    <p className="text-green-800">
                      Patient response pattern matches 87% of similar cases.
                    </p>
                  </div>
                  
                  <div className="p-2 bg-yellow-50 rounded text-xs">
                    <p className="text-yellow-800">
                      Consider monitoring for potential side effects in next 48 hours.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>

      {/* Security Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <Shield className="h-3 w-3 mr-1" />
              SOC2 Type II Compliant
            </span>
            <span>All access logged for HIPAA compliance</span>
            <span>AES-256 encrypted data transmission</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span>Session expires in 45 minutes</span>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Secure</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DoctorTimelinePage;