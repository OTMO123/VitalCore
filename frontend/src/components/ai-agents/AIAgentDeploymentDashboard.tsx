import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  Chip,
  LinearProgress,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  CloudDownload as DeployIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  DevicesOther as EdgeIcon,
} from '@mui/icons-material';
import AIAgentCard from './AIAgentCard';

interface AIAgent {
  id: string;
  name: string;
  description: string;
  type: 'clinical-assistant' | 'compliance-monitor' | 'data-analyzer' | 'security-guardian';
  status: 'deployed' | 'stopped' | 'deploying' | 'error';
  version: string;
  performance: {
    cpuUsage: number;
    memoryUsage: number;
    responseTime: number;
    accuracy: number;
  };
  compliance: {
    hipaaCompliant: boolean;
    soc2Certified: boolean;
    modelValidated: boolean;
  };
  lastDeployed: string;
  edgeDevices: number;
}

interface DeploymentMetrics {
  totalAgents: number;
  activeAgents: number;
  edgeDevices: number;
  totalDeployments: number;
  avgResponseTime: number;
  complianceScore: number;
}

const AIAgentDeploymentDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [deployDialogOpen, setDeployDialogOpen] = useState(false);
  const [newAgentConfig, setNewAgentConfig] = useState({
    type: 'clinical-assistant',
    name: '',
    version: '1.0.0',
    targetDevices: 'all',
    complianceMode: 'strict',
  });

  // Mock data
  const [agents, setAgents] = useState<AIAgent[]>([
    {
      id: 'agent-1',
      name: 'Clinical Assistant Pro',
      description: 'AI assistant for clinical decision support and patient care recommendations with FHIR integration.',
      type: 'clinical-assistant',
      status: 'deployed',
      version: '2.1.3',
      performance: {
        cpuUsage: 45,
        memoryUsage: 67,
        responseTime: 180,
        accuracy: 94.5,
      },
      compliance: {
        hipaaCompliant: true,
        soc2Certified: true,
        modelValidated: true,
      },
      lastDeployed: '2 hours ago',
      edgeDevices: 12,
    },
    {
      id: 'agent-2',
      name: 'Compliance Monitor',
      description: 'Real-time compliance monitoring for HIPAA, SOC2, and healthcare data protection.',
      type: 'compliance-monitor',
      status: 'deployed',
      version: '1.8.2',
      performance: {
        cpuUsage: 23,
        memoryUsage: 34,
        responseTime: 95,
        accuracy: 98.7,
      },
      compliance: {
        hipaaCompliant: true,
        soc2Certified: true,
        modelValidated: true,
      },
      lastDeployed: '6 hours ago',
      edgeDevices: 8,
    },
    {
      id: 'agent-3',
      name: 'Data Analytics Engine',
      description: 'Advanced analytics for patient data patterns, outcome predictions, and operational insights.',
      type: 'data-analyzer',
      status: 'stopped',
      version: '3.0.1',
      performance: {
        cpuUsage: 0,
        memoryUsage: 0,
        responseTime: 0,
        accuracy: 91.2,
      },
      compliance: {
        hipaaCompliant: true,
        soc2Certified: false,
        modelValidated: true,
      },
      lastDeployed: '2 days ago',
      edgeDevices: 0,
    },
    {
      id: 'agent-4',
      name: 'Security Guardian',
      description: 'AI-powered security monitoring for threat detection and anomaly analysis.',
      type: 'security-guardian',
      status: 'deploying',
      version: '1.5.0',
      performance: {
        cpuUsage: 78,
        memoryUsage: 45,
        responseTime: 234,
        accuracy: 96.8,
      },
      compliance: {
        hipaaCompliant: true,
        soc2Certified: true,
        modelValidated: false,
      },
      lastDeployed: 'deploying now',
      edgeDevices: 3,
    },
  ]);

  const deploymentMetrics: DeploymentMetrics = {
    totalAgents: agents.length,
    activeAgents: agents.filter(a => a.status === 'deployed').length,
    edgeDevices: agents.reduce((sum, a) => sum + a.edgeDevices, 0),
    totalDeployments: 47,
    avgResponseTime: Math.round(
      agents.filter(a => a.status === 'deployed')
        .reduce((sum, a) => sum + a.performance.responseTime, 0) /
      agents.filter(a => a.status === 'deployed').length
    ),
    complianceScore: Math.round(
      agents.reduce((sum, a) => {
        const score = (
          (a.compliance.hipaaCompliant ? 1 : 0) +
          (a.compliance.soc2Certified ? 1 : 0) +
          (a.compliance.modelValidated ? 1 : 0)
        ) / 3 * 100;
        return sum + score;
      }, 0) / agents.length
    ),
  };

  const handleDeploy = (agentId: string) => {
    setAgents(prev => prev.map(agent =>
      agent.id === agentId ? { ...agent, status: 'deploying' as const } : agent
    ));

    // Simulate deployment
    setTimeout(() => {
      setAgents(prev => prev.map(agent =>
        agent.id === agentId ? {
          ...agent,
          status: 'deployed' as const,
          lastDeployed: 'just now',
          edgeDevices: Math.floor(Math.random() * 10) + 1,
        } : agent
      ));
    }, 3000);
  };

  const handleStop = (agentId: string) => {
    setAgents(prev => prev.map(agent =>
      agent.id === agentId ? {
        ...agent,
        status: 'stopped' as const,
        edgeDevices: 0,
        performance: { ...agent.performance, cpuUsage: 0, memoryUsage: 0 }
      } : agent
    ));
  };

  const handleConfigure = (agentId: string, config: any) => {
    console.log('Configuring agent:', agentId, config);
    // Implementation for agent configuration
  };

  const handleViewAnalytics = (agentId: string) => {
    console.log('Viewing analytics for agent:', agentId);
    // Implementation for analytics view
  };

  const handleDeployNew = () => {
    if (!newAgentConfig.name) return;

    const newAgent: AIAgent = {
      id: `agent-${Date.now()}`,
      name: newAgentConfig.name,
      description: `Auto-generated ${newAgentConfig.type} agent`,
      type: newAgentConfig.type as any,
      status: 'deploying',
      version: newAgentConfig.version,
      performance: {
        cpuUsage: 0,
        memoryUsage: 0,
        responseTime: 0,
        accuracy: 85,
      },
      compliance: {
        hipaaCompliant: newAgentConfig.complianceMode === 'strict',
        soc2Certified: newAgentConfig.complianceMode === 'strict',
        modelValidated: false,
      },
      lastDeployed: 'deploying now',
      edgeDevices: 0,
    };

    setAgents(prev => [...prev, newAgent]);
    setDeployDialogOpen(false);
    setNewAgentConfig({
      type: 'clinical-assistant',
      name: '',
      version: '1.0.0',
      targetDevices: 'all',
      complianceMode: 'strict',
    });

    // Simulate deployment completion
    setTimeout(() => {
      handleDeploy(newAgent.id);
    }, 2000);
  };

  const MetricCard: React.FC<{ title: string; value: string | number; icon: React.ReactNode; color?: string }> = ({
    title, value, icon, color = 'primary'
  }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={600} color={`${color}.main`}>
              {value}
            </Typography>
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          AI Agent Deployment Center
        </Typography>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh Status">
            <IconButton 
              onClick={() => window.location.reload()}
              aria-label="Refresh deployment status"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDeployDialogOpen(true)}
            aria-label="Open dialog to deploy a new AI agent"
          >
            Deploy New Agent
          </Button>
        </Box>
      </Box>

      {/* Deployment Metrics */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Total Agents"
            value={deploymentMetrics.totalAgents}
            icon={<DeployIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Active Agents"
            value={deploymentMetrics.activeAgents}
            icon={<AnalyticsIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Edge Devices"
            value={deploymentMetrics.edgeDevices}
            icon={<EdgeIcon />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Deployments"
            value={deploymentMetrics.totalDeployments}
            icon={<DeployIcon />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Avg Response"
            value={`${deploymentMetrics.avgResponseTime}ms`}
            icon={<AnalyticsIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Compliance"
            value={`${deploymentMetrics.complianceScore}%`}
            icon={<SecurityIcon />}
            color="success"
          />
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All Agents" aria-label="View all AI agents" />
          <Tab label="Active" aria-label="View active AI agents" />
          <Tab label="Stopped" aria-label="View stopped AI agents" />
          <Tab label="Deploying" aria-label="View deploying AI agents" />
        </Tabs>
      </Paper>

      {/* Agents Grid */}
      <Grid container spacing={3}>
        {agents
          .filter(agent => {
            switch (tabValue) {
              case 1: return agent.status === 'deployed';
              case 2: return agent.status === 'stopped';
              case 3: return agent.status === 'deploying';
              default: return true;
            }
          })
          .map(agent => (
            <Grid item xs={12} md={6} lg={4} key={agent.id}>
              <AIAgentCard
                agent={agent}
                onDeploy={handleDeploy}
                onStop={handleStop}
                onConfigure={handleConfigure}
                onViewAnalytics={handleViewAnalytics}
              />
            </Grid>
          ))}
      </Grid>

      {/* Deploy New Agent Dialog */}
      <Dialog open={deployDialogOpen} onClose={() => setDeployDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Deploy New AI Agent</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} pt={1}>
            <TextField
              label="Agent Name"
              value={newAgentConfig.name}
              onChange={(e) => setNewAgentConfig({ ...newAgentConfig, name: e.target.value })}
              fullWidth
              required
              id="agent-name-input"
              aria-describedby="agent-name-helper"
              helperText="Enter a unique name for your AI agent"
            />

            <FormControl fullWidth>
              <InputLabel id="agent-type-label">Agent Type</InputLabel>
              <Select
                value={newAgentConfig.type}
                onChange={(e) => setNewAgentConfig({ ...newAgentConfig, type: e.target.value })}
                label="Agent Type"
                labelId="agent-type-label"
                id="agent-type-select"
                aria-describedby="agent-type-helper"
                required
              >
                <MenuItem value="clinical-assistant">Clinical Assistant</MenuItem>
                <MenuItem value="compliance-monitor">Compliance Monitor</MenuItem>
                <MenuItem value="data-analyzer">Data Analyzer</MenuItem>
                <MenuItem value="security-guardian">Security Guardian</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Version"
              value={newAgentConfig.version}
              onChange={(e) => setNewAgentConfig({ ...newAgentConfig, version: e.target.value })}
              fullWidth
              id="agent-version-input"
              aria-describedby="agent-version-helper"
              helperText="Agent version (e.g., 1.0.0)"
            />

            <FormControl fullWidth>
              <InputLabel id="target-devices-label">Target Devices</InputLabel>
              <Select
                value={newAgentConfig.targetDevices}
                onChange={(e) => setNewAgentConfig({ ...newAgentConfig, targetDevices: e.target.value })}
                label="Target Devices"
                labelId="target-devices-label"
                id="target-devices-select"
                aria-describedby="target-devices-helper"
              >
                <MenuItem value="all">All Edge Devices</MenuItem>
                <MenuItem value="clinical">Clinical Devices Only</MenuItem>
                <MenuItem value="admin">Admin Devices Only</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="compliance-mode-label">Compliance Mode</InputLabel>
              <Select
                value={newAgentConfig.complianceMode}
                onChange={(e) => setNewAgentConfig({ ...newAgentConfig, complianceMode: e.target.value })}
                label="Compliance Mode"
                labelId="compliance-mode-label"
                id="compliance-mode-select"
                aria-describedby="compliance-mode-helper"
                required
              >
                <MenuItem value="strict">Strict (HIPAA/SOC2)</MenuItem>
                <MenuItem value="standard">Standard</MenuItem>
                <MenuItem value="development">Development</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info">
              New agents will be deployed with the latest security patches and compliance validations.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeployDialogOpen(false)} aria-label="Cancel agent deployment">
            Cancel
          </Button>
          <Button
            onClick={handleDeployNew}
            variant="contained"
            disabled={!newAgentConfig.name}
            startIcon={<DeployIcon />}
            aria-label={`Deploy ${newAgentConfig.name || 'new'} AI agent`}
          >
            Deploy Agent
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIAgentDeploymentDashboard;