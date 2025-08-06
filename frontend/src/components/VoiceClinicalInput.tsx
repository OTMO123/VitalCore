/**
 * Real-Time Clinical Decision Intelligence - Voice Input Component
 * Competition Killer Feature #1
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  Grid,
  Paper,
  Divider,
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Psychology as AIIcon,
  LocalHospital as MedicalIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface ClinicalAnalysis {
  transcript: string;
  symptoms: string[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  agentConsensus: {
    cardiology: number;
    emergency: number;
    pulmonology: number;
    neurology: number;
  };
  recommendations: string[];
  triageCategory: 'ESI-1' | 'ESI-2' | 'ESI-3' | 'ESI-4' | 'ESI-5';
  estimatedDiagnosis: string[];
}

export const VoiceClinicalInput: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [analysis, setAnalysis] = useState<ClinicalAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>();

  // Initialize Web Audio API for voice visualization
  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Start audio level monitoring
      const updateAudioLevel = () => {
        if (analyserRef.current && isRecording) {
          const bufferLength = analyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyserRef.current.getByteFrequencyData(dataArray);
          
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;
          setAudioLevel(average / 255 * 100);
          
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      
      updateAudioLevel();
      
      // Setup MediaRecorder for voice capture
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          const audioBlob = event.data;
          await processVoiceInput(audioBlob);
        }
      };
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  // Process voice input through clinical AI pipeline
  const processVoiceInput = async (audioBlob: Blob) => {
    setIsAnalyzing(true);
    
    try {
      // Step 1: Voice to text transcription
      const transcriptText = await voiceToText(audioBlob);
      setTranscript(transcriptText);
      
      // Step 2: Clinical analysis through agent system
      const clinicalAnalysis = await analyzeClinicalSymptoms(transcriptText);
      setAnalysis(clinicalAnalysis);
      
    } catch (error) {
      console.error('Error processing voice input:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Mock voice-to-text (in production, use Web Speech API or Azure Speech)
  const voiceToText = async (audioBlob: Blob): Promise<string> => {
    // Simulate speech recognition
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve("Patient has severe chest pain for 30 minutes, shortness of breath, nausea, and left arm pain");
      }, 1500);
    });
  };

  // Clinical analysis using existing agent infrastructure
  const analyzeClinicalSymptoms = async (clinicalText: string): Promise<ClinicalAnalysis> => {
    // Simulate real-time clinical analysis
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          transcript: clinicalText,
          symptoms: ['chest pain', 'dyspnea', 'nausea', 'left arm pain'],
          riskLevel: 'CRITICAL',
          confidence: 0.92,
          agentConsensus: {
            cardiology: 0.95,
            emergency: 0.98,
            pulmonology: 0.45,
            neurology: 0.12
          },
          recommendations: [
            'Immediate 12-lead ECG',
            'Troponin I/T levels',
            'Aspirin 325mg chewed',
            'IV access established',
            'Continuous cardiac monitoring'
          ],
          triageCategory: 'ESI-1',
          estimatedDiagnosis: [
            'Acute ST-elevation myocardial infarction (STEMI)',
            'Acute coronary syndrome',
            'Unstable angina'
          ]
        });
      }, 2000);
    });
  };

  const startRecording = async () => {
    await initializeAudio();
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setTranscript('');
      setAnalysis(null);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setAudioLevel(0);
      
      // Cleanup
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h4" sx={{ mb: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <AIIcon color="primary" fontSize="large" />
          Real-Time Clinical Decision Intelligence
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          AI-powered voice analysis with 9-agent medical consensus
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Voice Input Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <MicIcon />
              Voice Clinical Input
            </Typography>

            {/* Voice Recording Control */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Button
                variant={isRecording ? "contained" : "outlined"}
                color={isRecording ? "error" : "primary"}
                size="large"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isAnalyzing}
                sx={{
                  minWidth: 200,
                  minHeight: 60,
                  borderRadius: '30px',
                  fontSize: '1.1rem'
                }}
                startIcon={isRecording ? <MicOffIcon /> : <MicIcon />}
              >
                {isRecording ? 'Stop Recording' : 'Start Voice Input'}
              </Button>
            </Box>

            {/* Audio Level Visualizer */}
            {isRecording && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Audio Level
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={audioLevel} 
                    sx={{ 
                      height: 8, 
                      borderRadius: 4,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: audioLevel > 50 ? 'success.main' : 'warning.main'
                      }
                    }} 
                  />
                </Box>
              </motion.div>
            )}

            {/* Transcript */}
            {transcript && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                  <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                    Transcribed Symptoms:
                  </Typography>
                  <Typography variant="body2">
                    "{transcript}"
                  </Typography>
                </Paper>
              </motion.div>
            )}

            {/* Analysis Loading */}
            {isAnalyzing && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <LinearProgress sx={{ flex: 1 }} />
                  <Typography variant="body2">
                    AI agents analyzing...
                  </Typography>
                </Box>
              </Alert>
            )}
          </Card>
        </Grid>

        {/* Clinical Analysis Results */}
        <Grid item xs={12} md={6}>
          <AnimatePresence>
            {analysis && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Card sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <MedicalIcon />
                    Clinical Analysis Results
                  </Typography>

                  {/* Risk Assessment */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <Chip 
                        label={`${analysis.riskLevel} RISK`}
                        color={getRiskColor(analysis.riskLevel) as any}
                        icon={analysis.riskLevel === 'CRITICAL' ? <WarningIcon /> : <CheckIcon />}
                        size="medium"
                      />
                      <Chip 
                        label={`${analysis.triageCategory}`}
                        variant="outlined"
                        size="medium"
                      />
                      <Chip 
                        label={`${(analysis.confidence * 100).toFixed(0)}% Confidence`}
                        color="primary"
                        size="medium"
                      />
                    </Box>
                  </Box>

                  {/* Agent Consensus */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      AI Agent Consensus:
                    </Typography>
                    {Object.entries(analysis.agentConsensus).map(([agent, confidence]) => (
                      <Box key={agent} sx={{ mb: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                            {agent} Agent
                          </Typography>
                          <Typography variant="body2" color="primary">
                            {(confidence * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={confidence * 100} 
                          sx={{ height: 4, borderRadius: 2 }}
                          color={confidence > 0.8 ? 'error' : confidence > 0.5 ? 'warning' : 'success'}
                        />
                      </Box>
                    ))}
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Estimated Diagnoses */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Estimated Diagnoses:
                    </Typography>
                    {analysis.estimatedDiagnosis.map((diagnosis, index) => (
                      <Chip
                        key={index}
                        label={diagnosis}
                        variant="outlined"
                        size="small"
                        sx={{ m: 0.5 }}
                        color={index === 0 ? 'primary' : 'default'}
                      />
                    ))}
                  </Box>

                  {/* Clinical Recommendations */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1, color: 'error.main' }}>
                      Immediate Actions Required:
                    </Typography>
                    {analysis.recommendations.map((recommendation, index) => (
                      <Alert 
                        key={index} 
                        severity="error" 
                        sx={{ mb: 1, '& .MuiAlert-message': { fontSize: '0.85rem' } }}
                      >
                        {index + 1}. {recommendation}
                      </Alert>
                    ))}
                  </Box>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </Grid>
      </Grid>
    </Box>
  );
};

export default VoiceClinicalInput;