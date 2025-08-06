import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar,
  ComposedChart,
  ReferenceLine,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { Box, Typography, Paper } from '@mui/material';

interface ChartData {
  [key: string]: any;
}

interface AdvancedMetricsChartProps {
  data: ChartData[];
  type: 'line' | 'area' | 'bar' | 'pie' | 'radial' | 'composed' | 'heatmap';
  title?: string;
  subtitle?: string;
  height?: number;
  xAxisKey?: string;
  yAxisKey?: string | string[];
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  colors?: string[];
  gradient?: boolean;
  interactive?: boolean;
  benchmark?: number;
  trendline?: boolean;
}

const AdvancedMetricsChart: React.FC<AdvancedMetricsChartProps> = ({
  data,
  type,
  title,
  subtitle,
  height = 300,
  xAxisKey = 'name',
  yAxisKey = 'value',
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  colors,
  gradient = false,
  interactive = true,
  benchmark,
  trendline = false,
}) => {
  const theme = useTheme();

  const defaultColors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main,
    theme.palette.info.main,
  ];

  const chartColors = colors || defaultColors;

  const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper
          sx={{
            p: 2,
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            boxShadow: 3,
          }}
        >
          <Typography variant="body2" fontWeight={600} mb={1}>
            {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Typography
              key={index}
              variant="body2"
              sx={{ color: entry.color }}
            >
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
              {entry.unit && ` ${entry.unit}`}
            </Typography>
          ))}
        </Paper>
      );
    }
    return null;
  };

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />}
        <XAxis
          dataKey={xAxisKey}
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        {benchmark && (
          <ReferenceLine
            y={benchmark}
            stroke={theme.palette.warning.main}
            strokeDasharray="5 5"
            label="Target"
          />
        )}
        {Array.isArray(yAxisKey) ? (
          yAxisKey.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={chartColors[index % chartColors.length]}
              strokeWidth={2}
              dot={{ fill: chartColors[index % chartColors.length], strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: chartColors[index % chartColors.length], strokeWidth: 2 }}
            />
          ))
        ) : (
          <Line
            type="monotone"
            dataKey={yAxisKey}
            stroke={chartColors[0]}
            strokeWidth={2}
            dot={{ fill: chartColors[0], strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: chartColors[0], strokeWidth: 2 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );

  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        {gradient && (
          <defs>
            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColors[0]} stopOpacity={0.8} />
              <stop offset="95%" stopColor={chartColors[0]} stopOpacity={0.1} />
            </linearGradient>
          </defs>
        )}
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />}
        <XAxis
          dataKey={xAxisKey}
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        <Area
          type="monotone"
          dataKey={yAxisKey}
          stroke={chartColors[0]}
          fill={gradient ? "url(#colorGradient)" : chartColors[0]}
          fillOpacity={gradient ? 1 : 0.6}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />}
        <XAxis
          dataKey={xAxisKey}
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        {benchmark && (
          <ReferenceLine
            y={benchmark}
            stroke={theme.palette.warning.main}
            strokeDasharray="5 5"
            label="Target"
          />
        )}
        <Bar
          dataKey={yAxisKey}
          fill={chartColors[0]}
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={Math.min(height * 0.3, 80)}
          fill="#8884d8"
          dataKey={yAxisKey}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
          ))}
        </Pie>
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
      </PieChart>
    </ResponsiveContainer>
  );

  const renderRadialChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <RadialBarChart cx="50%" cy="50%" innerRadius="20%" outerRadius="90%" data={data}>
        <RadialBar
          minAngle={15}
          label={{ position: 'insideStart', fill: '#fff' }}
          background
          clockWise
          dataKey={yAxisKey}
          fill={chartColors[0]}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
      </RadialBarChart>
    </ResponsiveContainer>
  );

  const renderComposedChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />}
        <XAxis
          dataKey={xAxisKey}
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        <Area
          type="monotone"
          dataKey="area"
          fill={chartColors[0]}
          fillOpacity={0.6}
          stroke={chartColors[0]}
        />
        <Bar dataKey="bar" barSize={20} fill={chartColors[1]} />
        <Line
          type="monotone"
          dataKey="line"
          stroke={chartColors[2]}
          strokeWidth={2}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );

  const renderChart = () => {
    switch (type) {
      case 'line': return renderLineChart();
      case 'area': return renderAreaChart();
      case 'bar': return renderBarChart();
      case 'pie': return renderPieChart();
      case 'radial': return renderRadialChart();
      case 'composed': return renderComposedChart();
      default: return renderLineChart();
    }
  };

  return (
    <Paper sx={{ p: 3, height: 'fit-content' }}>
      {(title || subtitle) && (
        <Box mb={2}>
          {title && (
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      )}
      {renderChart()}
    </Paper>
  );
};

export default AdvancedMetricsChart;