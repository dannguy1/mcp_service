import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { endpoints } from '../services/api';
import type { 
  ModelValidationResult,
  ModelPerformanceMetrics,
  ModelDriftResult,
  ModelTransferHistory
} from '../services/types';

export const useEnhancedModels = () => {
  const queryClient = useQueryClient();

  // Queries
  const modelsQuery = useQuery({
    queryKey: ['enhanced-models'],
    queryFn: () => endpoints.listEnhancedModels(),
    refetchInterval: 30000,
  });

  const transferHistoryQuery = useQuery({
    queryKey: ['transfer-history'],
    queryFn: () => endpoints.getTransferHistory(),
    refetchInterval: 60000,
  });

  const allPerformanceQuery = useQuery({
    queryKey: ['all-model-performance'],
    queryFn: () => endpoints.getAllModelPerformance(),
    refetchInterval: 30000,
  });

  // Mutations
  const deployMutation = useMutation({
    mutationFn: (version: string) => endpoints.deployModelVersion(version),
    onSuccess: () => {
      toast.success('Model deployed successfully');
      queryClient.invalidateQueries({ queryKey: ['enhanced-models'] });
    },
    onError: (error) => {
      toast.error(`Failed to deploy model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: (version: string) => endpoints.rollbackModel(version),
    onSuccess: () => {
      toast.success('Model rolled back successfully');
      queryClient.invalidateQueries({ queryKey: ['enhanced-models'] });
    },
    onError: (error) => {
      toast.error(`Failed to rollback model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const validateMutation = useMutation({
    mutationFn: (version: string) => endpoints.validateModel(version),
    onError: (error) => {
      toast.error(`Failed to validate model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const checkDriftMutation = useMutation({
    mutationFn: (version: string) => endpoints.checkModelDrift(version),
    onError: (error) => {
      toast.error(`Failed to check model drift: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const cleanupTransferHistoryMutation = useMutation({
    mutationFn: (daysToKeep: number = 30) => endpoints.cleanupTransferHistory(daysToKeep),
    onSuccess: () => {
      toast.success('Transfer history cleaned up successfully');
      queryClient.invalidateQueries({ queryKey: ['transfer-history'] });
    },
    onError: (error) => {
      toast.error(`Failed to cleanup transfer history: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const cleanupPerformanceMetricsMutation = useMutation({
    mutationFn: (daysToKeep: number = 30) => endpoints.cleanupPerformanceMetrics(daysToKeep),
    onSuccess: () => {
      toast.success('Performance metrics cleaned up successfully');
      queryClient.invalidateQueries({ queryKey: ['all-model-performance'] });
    },
    onError: (error) => {
      toast.error(`Failed to cleanup performance metrics: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Helper functions
  const getModelPerformance = async (version: string): Promise<ModelPerformanceMetrics> => {
    return endpoints.getModelPerformance(version);
  };

  const generateValidationReport = async (version: string) => {
    return endpoints.generateValidationReport(version);
  };

  const generatePerformanceReport = async (version: string) => {
    return endpoints.generatePerformanceReport(version);
  };

  const validateModelCompatibility = async (version: string, targetFeatures: string[]) => {
    return endpoints.validateModelCompatibility(version, targetFeatures);
  };

  return {
    // Queries
    models: modelsQuery.data,
    transferHistory: transferHistoryQuery.data,
    allPerformance: allPerformanceQuery.data,
    
    // Loading states
    isLoading: modelsQuery.isLoading,
    isModelsLoading: modelsQuery.isLoading,
    isTransferHistoryLoading: transferHistoryQuery.isLoading,
    isPerformanceLoading: allPerformanceQuery.isLoading,
    
    // Error states
    modelsError: modelsQuery.error,
    transferHistoryError: transferHistoryQuery.error,
    performanceError: allPerformanceQuery.error,
    
    // Mutations
    deployModel: deployMutation.mutate,
    rollbackModel: rollbackMutation.mutate,
    validateModel: validateMutation.mutate,
    checkDrift: checkDriftMutation.mutate,
    cleanupTransferHistory: cleanupTransferHistoryMutation.mutate,
    cleanupPerformanceMetrics: cleanupPerformanceMetricsMutation.mutate,
    
    // Mutation states
    isDeploying: deployMutation.isPending,
    isRollingBack: rollbackMutation.isPending,
    isValidating: validateMutation.isPending,
    isCheckingDrift: checkDriftMutation.isPending,
    isCleaningUpTransfer: cleanupTransferHistoryMutation.isPending,
    isCleaningUpPerformance: cleanupPerformanceMetricsMutation.isPending,
    
    // Helper functions
    getModelPerformance,
    generateValidationReport,
    generatePerformanceReport,
    validateModelCompatibility,
    
    // Refetch functions
    refetchModels: () => queryClient.invalidateQueries({ queryKey: ['enhanced-models'] }),
    refetchTransferHistory: () => queryClient.invalidateQueries({ queryKey: ['transfer-history'] }),
    refetchAllPerformance: () => queryClient.invalidateQueries({ queryKey: ['all-model-performance'] }),
  };
}; 