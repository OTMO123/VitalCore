import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Search,
  History,
  GitBranch as Timeline,
  FileText,
  Activity,
  AlertTriangle,
  Shield
} from 'lucide-react';

import DoctorHistoryMode from '@/components/doctor/DoctorHistoryMode';
import LinkedMedicalTimeline from '@/components/doctor/LinkedMedicalTimeline';

interface DoctorHistoryPageProps {}

const DoctorHistoryPage: React.FC<DoctorHistoryPageProps> = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(
    searchParams.get('case') || null
  );
  const [activeView, setActiveView] = useState<'history' | 'timeline'>(
    searchParams.get('view') === 'timeline' ? 'timeline' : 'history'
  );
  const [searchTerm, setSearchTerm] = useState('');

  // Mock case data - in production this would come from API
  const mockCases = [
    {
      id: 'demo-case-he-3849',
      title: 'Acute Coronary Syndrome',
      patientAge: 54,
      status: 'active',
      priority: 'high',
      lastUpdate: '2025-08-06T14:30:00Z',
      provider: 'Dr. Emily Hart',
      events: 12,
      criticalEvents: 2
    },
    {
      id: 'case-he-3850',
      title: 'Chronic Heart Failure Management',
      patientAge: 67,
      status: 'monitoring',
      priority: 'medium',
      lastUpdate: '2025-08-05T09:15:00Z',
      provider: 'Dr. Samuel Lee',
      events: 8,
      criticalEvents: 1
    },
    {
      id: 'case-he-3851',
      title: 'Diabetes Type 2 Care Cycle',
      patientAge: 45,
      status: 'active',
      priority: 'medium',
      lastUpdate: '2025-08-04T16:45:00Z',
      provider: 'Dr. Sarah Kim',
      events: 15,
      criticalEvents: 0
    }
  ];

  const filteredCases = mockCases.filter(caseItem =>
    caseItem.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    caseItem.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    caseItem.provider.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Update URL when view or case changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedCaseId) params.set('case', selectedCaseId);
    if (activeView !== 'history') params.set('view', activeView);
    
    setSearchParams(params);
  }, [selectedCaseId, activeView, setSearchParams]);

  const handleCaseSelect = (caseId: string) => {
    setSelectedCaseId(caseId);
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const renderCaseSelector = () => (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Search className="h-5 w-5 mr-2" />
          Case Selection
        </CardTitle>
        <CardDescription>
          Select a medical case to view comprehensive history and timeline analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex space-x-2">
          <Input
            placeholder="Search cases, patient IDs, or providers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
          <Button size="icon" variant="outline">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCases.map((caseItem) => (
            <Card
              key={caseItem.id}
              className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                selectedCaseId === caseItem.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
              }`}
              onClick={() => handleCaseSelect(caseItem.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-sm mb-1">{caseItem.title}</h4>
                    <p className="text-xs text-gray-600">Case #{caseItem.id}</p>
                  </div>
                  <Badge
                    variant={
                      caseItem.priority === 'high' ? 'destructive' :
                      caseItem.priority === 'medium' ? 'secondary' : 'default'
                    }
                  >
                    {caseItem.priority}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Patient Age:</span>
                    <span>{caseItem.patientAge} years</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Provider:</span>
                    <span>{caseItem.provider}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Events:</span>
                    <span>{caseItem.events} total</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Critical:</span>
                    <span className={caseItem.criticalEvents > 0 ? 'text-red-600 font-medium' : ''}>
                      {caseItem.criticalEvents}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Status:</span>
                    <Badge variant="outline" className="text-xs">
                      {caseItem.status}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t">
                  <span className="text-xs text-gray-500">
                    Updated {new Date(caseItem.lastUpdate).toLocaleDateString()}
                  </span>
                  {selectedCaseId === caseItem.id && (
                    <Badge variant="default" className="text-xs">
                      Selected
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredCases.length === 0 && (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No cases found matching your search</p>
            <Button
              size="sm"
              variant="outline"
              className="mt-2"
              onClick={() => setSearchTerm('')}
            >
              Clear Search
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

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
              Back to Dashboard
            </Button>
            
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Doctor Medical History
              </h1>
              <p className="text-sm text-gray-600">
                Comprehensive case analysis and timeline visualization
              </p>
            </div>
          </div>

          {selectedCaseId && (
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="flex items-center">
                <Shield className="h-3 w-3 mr-1" />
                HIPAA Compliant
              </Badge>
              
              <Select value={activeView} onValueChange={(value) => setActiveView(value as typeof activeView)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="history">
                    <div className="flex items-center">
                      <History className="h-4 w-4 mr-2" />
                      History Mode
                    </div>
                  </SelectItem>
                  <SelectItem value="timeline">
                    <div className="flex items-center">
                      <Timeline className="h-4 w-4 mr-2" />
                      GitBranch as Timeline View
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {!selectedCaseId && renderCaseSelector()}

        {selectedCaseId && (
          <Tabs value={activeView} onValueChange={(value) => setActiveView(value as typeof activeView)}>
            <div className="mb-6">
              <TabsList className="grid w-full grid-cols-2 max-w-md">
                <TabsTrigger value="history" className="flex items-center">
                  <History className="h-4 w-4 mr-2" />
                  History Mode
                </TabsTrigger>
                <TabsTrigger value="timeline" className="flex items-center">
                  <Timeline className="h-4 w-4 mr-2" />
                  GitBranch as Timeline View
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="history" className="m-0">
              <DoctorHistoryMode
                caseId={selectedCaseId}
                onCaseSelect={handleCaseSelect}
              />
            </TabsContent>

            <TabsContent value="timeline" className="m-0">
              <LinkedMedicalTimeline
                caseId={selectedCaseId}
              />
            </TabsContent>
          </Tabs>
        )}

        {/* Security Notice */}
        <Card className="mt-6 border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-blue-800">
              <Shield className="h-4 w-4" />
              <span className="text-sm font-medium">Security & Compliance</span>
            </div>
            <p className="text-xs text-blue-700 mt-1">
              All PHI access is logged for HIPAA compliance. This interface follows SOC2 Type II security standards
              with end-to-end encryption and comprehensive audit trails.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DoctorHistoryPage;