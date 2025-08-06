import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Alert,
  Chip,
  Paper,
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Analytics as AnalyticsIcon,
  Monitor as MonitoringIcon,
  Settings as ManagementIcon,
} from '@mui/icons-material';
import AIAgentDeploymentDashboard from '../../components/ai-agents/AIAgentDeploymentDashboard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box>{children}</Box>}
  </div>
);

const AIAgentsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600} mr={2}>
          AI Agents Platform
        </Typography>
        <Chip label="Beta" color="primary" />
      </Box>

      {/* Status Alert */}
      <Alert severity="success" sx={{ mb: 3 }}>
        <Box display="flex" alignItems="center" gap={1}>
          <AIIcon />
          <Typography variant="body2">
            AI Agent platform is now active • SOC2 compliant • HIPAA ready • Real-time deployment
          </Typography>
        </Box>
      </Alert>

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            label="Deployment Center" 
            icon={<AIIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Performance Analytics" 
            icon={<AnalyticsIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Real-time Monitoring" 
            icon={<MonitoringIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Model Management" 
            icon={<ManagementIcon />} 
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        <AIAgentDeploymentDashboard />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Performance Analytics
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            <Typography variant="body1">
              🚀 <strong>Advanced Analytics Dashboard</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Model accuracy trends and performance metrics
              • Response time optimization analytics  
              • Resource utilization patterns
              • Compliance scoring and drift detection
              • Edge device performance monitoring
              • Training data quality assessments
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              Advanced analytics available with deployed agents. Deploy your first agent to access detailed performance insights.
            </Alert>
          </Box>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Real-time Monitoring
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            <Typography variant="body1">
              📊 <strong>Live Monitoring Dashboard</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Real-time agent health and status monitoring
              • Live performance metrics and alerting
              • Security event detection and response
              • Compliance violation monitoring
              • Edge device connectivity status
              • Automatic failover and recovery tracking
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              Real-time monitoring activates automatically when agents are deployed to edge devices.
            </Alert>
          </Box>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Model Management
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            <Typography variant="body1">
              🔧 <strong>AI Model Lifecycle Management</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Model versioning and rollback capabilities
              • Training data pipeline management
              • A/B testing for model performance
              • Automated model validation and testing
              • Compliance certification tracking
              • Custom model deployment workflows
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              Model management tools enable enterprise-grade AI operations with full audit trails and compliance validation.
            </Alert>
          </Box>
        </Paper>
      </TabPanel>
    </Box>
  );
};

export default AIAgentsPage;