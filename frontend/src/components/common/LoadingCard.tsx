import React from 'react';
import { Card, CardContent, Skeleton, Box } from '@mui/material';

// ============================================
// LOADING CARD COMPONENT
// ============================================

interface LoadingCardProps {
  height?: number;
  showAvatar?: boolean;
  lines?: number;
}

const LoadingCard: React.FC<LoadingCardProps> = ({ 
  height = 120, 
  showAvatar = false, 
  lines = 3 
}) => {
  return (
    <Card sx={{ height }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {showAvatar && (
            <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
          )}
          <Box flexGrow={1}>
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="text" width="40%" height={20} />
          </Box>
        </Box>
        
        {[...Array(lines)].map((_, index) => (
          <Skeleton 
            key={index}
            variant="text" 
            width={`${Math.random() * 40 + 60}%`} 
            height={16}
            sx={{ mb: 0.5 }}
          />
        ))}
      </CardContent>
    </Card>
  );
};

export default LoadingCard;