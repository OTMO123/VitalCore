import React from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  TreeMap,
  ScatterChart,
  Scatter,
} from 'recharts';
import { Box, Typography, Card, CardContent, CardHeader, useTheme, Grid } from '@mui/material';

interface HealthcareMetricsProps {
  patientVolume?: any[];
  immunizationRates?: any[];
  complianceMetrics?: any[];
  phiAccessPatterns?: any[];
  systemPerformance?: any[];
}

const HealthcareMetrics: React.FC<HealthcareMetricsProps> = ({
  patientVolume = [],
  immunizationRates = [],
  complianceMetrics = [],
  phiAccessPatterns = [],
  systemPerformance = [],
}) => {
  const theme = useTheme();

  // Default mock data if none provided
  const defaultPatientVolume = patientVolume.length ? patientVolume : [
    { month: 'Jan', newPatients: 120, totalVisits: 1340, avgWaitTime: 15 },
    { month: 'Feb', newPatients: 98, totalVisits: 1180, avgWaitTime: 12 },
    { month: 'Mar', newPatients: 156, totalVisits: 1520, avgWaitTime: 18 },
    { month: 'Apr', newPatients: 134, totalVisits: 1420, avgWaitTime: 14 },
    { month: 'May', newPatients: 142, totalVisits: 1380, avgWaitTime: 16 },
    { month: 'Jun', newPatients: 178, totalVisits: 1620, avgWaitTime: 13 },
  ];

  const defaultImmunizationRates = immunizationRates.length ? immunizationRates : [
    { vaccine: 'COVID-19', completed: 87, inProgress: 8, notStarted: 5 },
    { vaccine: 'Influenza', completed: 76, inProgress: 12, notStarted: 12 },
    { vaccine: 'Hepatitis B', completed: 92, inProgress: 5, notStarted: 3 },
    { vaccine: 'MMR', completed: 95, inProgress: 3, notStarted: 2 },
    { vaccine: 'Tdap', completed: 89, inProgress: 7, notStarted: 4 },
  ];

  const defaultComplianceMetrics = complianceMetrics.length ? complianceMetrics : [
    { framework: 'HIPAA', score: 98, target: 95 },
    { framework: 'SOC2', score: 96, target: 95 },
    { framework: 'ISO 27001', score: 87, target: 90 },
    { framework: 'FHIR R4', score: 94, target: 95 },
  ];

  const defaultPhiAccessPatterns = phiAccessPatterns.length ? phiAccessPatterns : [
    { hour: '00:00', accesses: 12, users: 3 },
    { hour: '06:00', accesses: 45, users: 8 },
    { hour: '09:00', accesses: 186, users: 24 },
    { hour: '12:00', accesses: 234, users: 31 },
    { hour: '15:00', accesses: 198, users: 28 },
    { hour: '18:00', accesses: 89, users: 15 },
    { hour: '21:00', accesses: 34, users: 7 },
  ];

  const ComplianceRadialChart = () => (
    <Card>
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={600}>
            Compliance Framework Scores
          </Typography>
        }
      />
      <CardContent>
        <Box height={300}>
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="20%"
              outerRadius="90%"
              data={defaultComplianceMetrics}
            >
              <RadialBar
                minAngle={15}
                label={{ position: 'insideStart', fill: '#fff', fontWeight: 600 }}
                background
                clockWise
                dataKey="score"
                fill={theme.palette.primary.main}
              />
              <Legend iconSize={10} />
              <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
            </RadialBarChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );

  const PatientVolumeChart = () => (
    <Card>
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={600}>
            Patient Volume & Wait Times
          </Typography>
        }
      />
      <CardContent>
        <Box height={300}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={defaultPatientVolume}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar
                yAxisId="left"
                dataKey="newPatients"
                fill={theme.palette.primary.main}
                name="New Patients"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                yAxisId="left"
                dataKey="totalVisits"
                fill={theme.palette.secondary.main}
                name="Total Visits"
                radius={[4, 4, 0, 0]}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgWaitTime"
                stroke={theme.palette.error.main}
                strokeWidth={3}
                name="Avg Wait Time (min)"
                dot={{ fill: theme.palette.error.main, strokeWidth: 2, r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );

  const ImmunizationTreeMap = () => {
    const treeMapData = defaultImmunizationRates.map(vaccine => ({
      name: vaccine.vaccine,
      size: vaccine.completed,
      fill: vaccine.completed >= 90 ? theme.palette.success.main : 
            vaccine.completed >= 80 ? theme.palette.warning.main : 
            theme.palette.error.main,
    }));

    return (
      <Card>
        <CardHeader
          title={
            <Typography variant="h6" fontWeight={600}>
              Immunization Coverage by Vaccine
            </Typography>
          }
        />
        <CardContent>
          <Box height={300}>
            <ResponsiveContainer width="100%" height="100%">
              <TreeMap
                data={treeMapData}
                dataKey="size"
                ratio={4/3}
                stroke="#fff"
                fill={theme.palette.primary.main}
              />
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const PhiAccessScatterChart = () => (
    <Card>
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={600}>
            PHI Access Patterns (24-Hour)
          </Typography>
        }
      />
      <CardContent>
        <Box height={300}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart data={defaultPhiAccessPatterns}>
              <CartesianGrid />
              <XAxis dataKey="hour" />
              <YAxis dataKey="accesses" name="Accesses" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter
                name="PHI Accesses"
                dataKey="accesses"
                fill={theme.palette.warning.main}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} lg={6}>
        <PatientVolumeChart />
      </Grid>
      <Grid item xs={12} lg={6}>
        <ComplianceRadialChart />
      </Grid>
      <Grid item xs={12} lg={6}>
        <ImmunizationTreeMap />
      </Grid>
      <Grid item xs={12} lg={6}>
        <PhiAccessScatterChart />
      </Grid>
    </Grid>
  );
};

export default HealthcareMetrics;