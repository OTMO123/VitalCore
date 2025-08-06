import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  IconButton,
  Menu,
  MenuItem,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  MoreVert as MoreIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  CloudDownload as DeployIcon,
  Security as SecurityIcon,
  Memory as MemoryIcon,
  Speed as PerformanceIcon,
} from '@mui/icons-material';

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

interface AIAgentCardProps {
  agent: AIAgent;
  onDeploy: (agentId: string) => void;
  onStop: (agentId: string) => void;
  onConfigure: (agentId: string, config: any) => void;
  onViewAnalytics: (agentId: string) => void;
}

const AIAgentCard: React.FC<AIAgentCardProps> = ({
  agent,
  onDeploy,
  onStop,
  onConfigure,
  onViewAnalytics,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [configOpen, setConfigOpen] = useState(false);
  const [config, setConfig] = useState({
    autoScale: true,
    maxInstances: 3,
    targetDevices: 'all',
    complianceMode: 'strict',
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed': return 'success';
      case 'deploying': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'clinical-assistant': return '🏥';
      case 'compliance-monitor': return '📋';
      case 'data-analyzer': return '📊';
      case 'security-guardian': return '🛡️';
      default: return '🤖';
    }
  };

  const handleMenuClose = () => setAnchorEl(null);

  const handleConfigure = () => {
    setConfigOpen(true);
    handleMenuClose();
  };

  const handleSaveConfig = () => {
    onConfigure(agent.id, config);
    setConfigOpen(false);
  };

  return (
    <>
      <Card>
        <CardContent>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6" component="span" fontSize="1.5rem">
                {getTypeIcon(agent.type)}
              </Typography>
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  {agent.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  v{agent.version}
                </Typography>
              </Box>
            </Box>
            <Box display="flex" gap={1} alignItems="center">
              <Chip
                label={agent.status}
                color={getStatusColor(agent.status) as any}
                size="small"
                aria-label={`Agent status: ${agent.status}`}
              />
              <IconButton
                size="small"
                onClick={(e) => setAnchorEl(e.currentTarget)}
                aria-label={`More options for ${agent.name}`}
              >
                <MoreIcon />
              </IconButton>
            </Box>
          </Box>

          {/* Description */}
          <Typography variant="body2" color="text.secondary" mb={2}>
            {agent.description}
          </Typography>

          {/* Performance Metrics */}
          <Box mb={2}>
            <Typography variant="subtitle2" fontWeight={600} mb={1}>
              Performance Metrics
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <Box display="flex" alignItems="center" gap={2}>
                <MemoryIcon fontSize="small" color="action" />
                <Box flex={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="caption">CPU Usage</Typography>
                    <Typography variant="caption">{agent.performance.cpuUsage}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={agent.performance.cpuUsage} 
                    color={agent.performance.cpuUsage > 80 ? 'error' : 'primary'}
                    aria-label={`CPU Usage: ${agent.performance.cpuUsage}%`}
                  />
                </Box>
              </Box>
              <Box display="flex" alignItems="center" gap={2}>
                <PerformanceIcon fontSize="small" color="action" />
                <Box flex={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="caption">Response Time</Typography>
                    <Typography variant="caption">{agent.performance.responseTime}ms</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={Math.min(agent.performance.responseTime / 10, 100)} 
                    color={agent.performance.responseTime > 500 ? 'error' : 'success'}
                    aria-label={`Response Time: ${agent.performance.responseTime}ms`}
                  />
                </Box>
              </Box>
              <Box display="flex" alignItems="center" gap={2}>
                <AnalyticsIcon fontSize="small" color="action" />
                <Box flex={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="caption">Model Accuracy</Typography>
                    <Typography variant="caption">{agent.performance.accuracy}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={agent.performance.accuracy} 
                    color={agent.performance.accuracy > 90 ? 'success' : 'warning'}
                    aria-label={`Model Accuracy: ${agent.performance.accuracy}%`}
                  />
                </Box>
              </Box>
            </Box>
          </Box>

          {/* Compliance Status */}
          <Box mb={2}>
            <Typography variant="subtitle2" fontWeight={600} mb={1}>
              Compliance Status
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Chip
                label="HIPAA"
                color={agent.compliance.hipaaCompliant ? 'success' : 'error'}
                size="small"
                icon={<SecurityIcon />}
                aria-label={`HIPAA compliance: ${agent.compliance.hipaaCompliant ? 'Compliant' : 'Non-compliant'}`}
              />
              <Chip
                label="SOC2"
                color={agent.compliance.soc2Certified ? 'success' : 'error'}
                size="small"
                icon={<SecurityIcon />}
                aria-label={`SOC2 certification: ${agent.compliance.soc2Certified ? 'Certified' : 'Not certified'}`}
              />
              <Chip
                label="Model Validated"
                color={agent.compliance.modelValidated ? 'success' : 'warning'}
                size="small"
                icon={<AnalyticsIcon />}
                aria-label={`Model validation: ${agent.compliance.modelValidated ? 'Validated' : 'Pending validation'}`}
              />
            </Box>
          </Box>

          {/* Deployment Info */}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="caption" color="text.secondary">
                Last Deployed: {agent.lastDeployed}
              </Typography>
              <br />
              <Typography variant="caption" color="text.secondary">
                Edge Devices: {agent.edgeDevices}
              </Typography>
            </Box>
          </Box>
        </CardContent>

        <CardActions>
          <Box display="flex" gap={1} width="100%">
            {agent.status === 'deployed' ? (
              <Button
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                onClick={() => onStop(agent.id)}
                size="small"
                aria-label={`Stop ${agent.name} deployment`}
              >
                Stop
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayIcon />}
                onClick={() => onDeploy(agent.id)}
                disabled={agent.status === 'deploying'}
                size="small"
                aria-label={`Deploy ${agent.name} to edge devices`}
              >
                {agent.status === 'deploying' ? 'Deploying...' : 'Deploy'}
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<AnalyticsIcon />}
              onClick={() => onViewAnalytics(agent.id)}
              size="small"
              aria-label={`View analytics for ${agent.name}`}
            >
              Analytics
            </Button>
          </Box>
        </CardActions>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleConfigure} aria-label={`Configure settings for ${agent.name}`}>
          <SettingsIcon sx={{ mr: 1 }} />
          Configure
        </MenuItem>
        <MenuItem onClick={() => { onViewAnalytics(agent.id); handleMenuClose(); }} aria-label={`View analytics for ${agent.name}`}>
          <AnalyticsIcon sx={{ mr: 1 }} />
          View Analytics
        </MenuItem>
        <MenuItem onClick={handleMenuClose} aria-label={`Clone configuration for ${agent.name}`}>
          <DeployIcon sx={{ mr: 1 }} />
          Clone Configuration
        </MenuItem>
      </Menu>

      {/* Configuration Dialog */}
      <Dialog open={configOpen} onClose={() => setConfigOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure AI Agent: {agent.name}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} pt={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.autoScale}
                  onChange={(e) => setConfig({ ...config, autoScale: e.target.checked })}
                />
              }
              label="Auto-scaling enabled"
            />
            
            <TextField
              label="Maximum Instances"
              type="number"
              value={config.maxInstances}
              onChange={(e) => setConfig({ ...config, maxInstances: parseInt(e.target.value) })}
              inputProps={{ min: 1, max: 10 }}
              id="max-instances-input"
              helperText="Maximum number of agent instances (1-10)"
            />

            <FormControl fullWidth>
              <InputLabel>Target Devices</InputLabel>
              <Select
                value={config.targetDevices}
                onChange={(e) => setConfig({ ...config, targetDevices: e.target.value })}
                label="Target Devices"
              >
                <MenuItem value="all">All Edge Devices</MenuItem>
                <MenuItem value="clinical">Clinical Devices Only</MenuItem>
                <MenuItem value="admin">Admin Devices Only</MenuItem>
                <MenuItem value="specific">Specific Devices</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Compliance Mode</InputLabel>
              <Select
                value={config.complianceMode}
                onChange={(e) => setConfig({ ...config, complianceMode: e.target.value })}
                label="Compliance Mode"
              >
                <MenuItem value="strict">Strict (Full HIPAA/SOC2)</MenuItem>
                <MenuItem value="standard">Standard</MenuItem>
                <MenuItem value="development">Development (Relaxed)</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info">
              Changes will be applied on next deployment. Current running instances will not be affected.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigOpen(false)} aria-label="Cancel configuration changes">
            Cancel
          </Button>
          <Button onClick={handleSaveConfig} variant="contained" aria-label={`Save configuration for ${agent.name}`}>
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AIAgentCard;