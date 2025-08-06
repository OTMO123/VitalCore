import React, { useState } from 'react';
import { Mic, Camera, Shield, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AnalysisResult {
  diagnosis: string;
  confidence: number;
  recommendations: string[];
}

const SymptomInputPage: React.FC = () => {
  const [symptoms, setSymptoms] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  const handleVoiceInput = async () => {
    setIsRecording(true);
    // Mock voice recording for now - would integrate with Web Speech API
    setTimeout(() => {
      setSymptoms("I have been experiencing chest pain and shortness of breath for the past 2 days...");
      setIsRecording(false);
    }, 3000);
  };

  const handlePhotoInput = async () => {
    // Mock photo capture for now - would integrate with device camera API
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment';
    
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        setSymptoms(prev => prev + " [Image uploaded: " + file.name + "]");
      }
    };
    
    input.click();
  };

  const handleAnalyze = async () => {
    if (!symptoms.trim()) return;
    
    setIsAnalyzing(true);
    
    // Mock analysis - would call real AI service
    setTimeout(() => {
      setResult({
        diagnosis: "Based on your symptoms, this appears to be related to cardiac strain. Immediate medical attention recommended.",
        confidence: 87,
        recommendations: [
          "Seek immediate emergency care",
          "Monitor blood pressure",
          "Avoid physical exertion",
          "Take prescribed medications as directed"
        ]
      });
      setIsAnalyzing(false);
    }, 4000);
  };

  const handleRealDoctorConsult = () => {
    // Would redirect to doctor consultation booking
    alert("Redirecting to doctor consultation booking...");
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="flex items-center justify-between p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-medium text-gray-900">HEMA3N</h1>
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <Shield className="w-4 h-4 text-blue-600" />
            <span>Secure PHI</span>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          Patient Portal
        </div>
      </header>

      <div className="max-w-4xl mx-auto p-8">
        {/* Main Content */}
        {!result && !isAnalyzing && (
          <div className="text-center space-y-8">
            <div className="space-y-4">
              <h2 className="text-3xl font-medium text-gray-900 mb-8">
                Describe your symptoms...
              </h2>
              
              {/* Text Input Area */}
              <div className="relative">
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder="Tell us what you're experiencing. Include when symptoms started, their severity, and any relevant details..."
                  className="w-full h-40 p-6 text-lg border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isRecording}
                />
                {isRecording && (
                  <div className="absolute inset-0 bg-blue-50 rounded-lg flex items-center justify-center">
                    <div className="flex items-center gap-2 text-blue-600">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-lg">Recording...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Input Buttons */}
            <div className="flex justify-center gap-6">
              <Button
                onClick={handleVoiceInput}
                disabled={isRecording}
                className="flex items-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg transition-colors"
              >
                <Mic className="w-6 h-6" />
                {isRecording ? 'Recording...' : 'Voice Input'}
              </Button>
              
              <Button
                onClick={handlePhotoInput}
                variant="outline"
                className="flex items-center gap-3 px-8 py-4 border-2 border-blue-600 text-blue-600 hover:bg-blue-50 text-lg rounded-lg transition-colors"
              >
                <Camera className="w-6 h-6" />
                Photo
              </Button>
            </div>

            {/* Analyze Button */}
            {symptoms.trim() && (
              <Button
                onClick={handleAnalyze}
                className="px-12 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg transition-colors"
              >
                Analyze Symptoms
              </Button>
            )}
          </div>
        )}

        {/* Analysis Loading State */}
        {isAnalyzing && (
          <div className="text-center space-y-8">
            <div className="relative w-32 h-32 mx-auto">
              <div className="absolute inset-0 border-4 border-blue-100 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Shield className="w-8 h-8 text-blue-600" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-2xl font-medium text-gray-900">Analyzing securely...</h3>
              <p className="text-gray-600">Our AI is reviewing your symptoms with medical-grade security</p>
            </div>
          </div>
        )}

        {/* Results Display */}
        {result && (
          <Card className="p-8 space-y-6">
            <div className="space-y-4">
              <h3 className="text-2xl font-medium text-gray-900">Analysis Results</h3>
              
              {/* Confidence Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Confidence Level</span>
                  <span className="font-medium text-gray-900">{result.confidence}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all duration-1000 ${
                      result.confidence >= 80 ? 'bg-green-500' : 
                      result.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${result.confidence}%` }}
                  ></div>
                </div>
              </div>

              {/* Diagnosis */}
              <div className="p-6 bg-gray-50 rounded-lg">
                <p className="text-lg text-gray-900">{result.diagnosis}</p>
              </div>

              {/* Recommendations */}
              <div className="space-y-3">
                <h4 className="text-lg font-medium text-gray-900">Recommendations</h4>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                {result.confidence < 80 && (
                  <Button
                    onClick={handleRealDoctorConsult}
                    className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    Turn Real - Consult Doctor
                  </Button>
                )}
                
                <Button
                  onClick={() => {
                    setResult(null);
                    setSymptoms('');
                  }}
                  variant="outline"
                  className="px-8 py-3 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  New Analysis
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Footer */}
        <footer className="text-center pt-12 text-sm text-gray-500">
          <div className="flex justify-center gap-6">
            <button className="hover:text-gray-700 transition-colors">Language</button>
            <button className="hover:text-gray-700 transition-colors">Settings</button>
            <button className="hover:text-gray-700 transition-colors">Privacy</button>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default SymptomInputPage;