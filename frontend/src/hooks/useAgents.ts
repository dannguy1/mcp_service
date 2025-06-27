import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { endpoints } from '../services/api';
import type { Agent, AgentModelRequest, AvailableModel, AgentActionResponse, AgentDetailedInfo } from '../services/types';

export const useAgents = () => {
  const queryClient = useQueryClient();

  // Query for listing agents
  const {
    data: agents = [],
    isLoading: isLoadingAgents,
    error: agentsError,
    refetch: refetchAgents
  } = useQuery({
    queryKey: ['agents'],
    queryFn: endpoints.listAgents,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000 // Consider data stale after 10 seconds
  });

  // Debug: Log the agents data
  console.log('🔍 useAgents hook - Raw agents data:', agents);
  if (agents.length > 0) {
    console.log('🔍 useAgents hook - First agent:', {
      id: agents[0].id,
      name: agents[0].name,
      capabilities: agents[0].capabilities,
      process_filters: agents[0].process_filters,
      hasCapabilities: 'capabilities' in agents[0],
      hasProcessFilters: 'process_filters' in agents[0],
      capabilitiesType: typeof agents[0].capabilities,
      processFiltersType: typeof agents[0].process_filters
    });
  }

  // Query for available models
  const {
    data: availableModels = [],
    isLoading: isLoadingModels,
    error: modelsError,
    refetch: refetchModels
  } = useQuery({
    queryKey: ['available-models'],
    queryFn: endpoints.getAvailableModels,
    staleTime: 60000 // Consider data stale after 1 minute
  });

  // Mutation for setting agent model
  const setAgentModelMutation = useMutation({
    mutationFn: ({ agentId, modelPath }: { agentId: string; modelPath: string }) =>
      endpoints.setAgentModel(agentId, modelPath),
    onSuccess: (data, variables) => {
      toast.success(`Model updated for agent ${variables.agentId}`);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to update model: ${error.message || 'Unknown error'}`);
    }
  });

  // Mutation for restarting agent
  const restartAgentMutation = useMutation({
    mutationFn: (agentId: string) => endpoints.restartAgent(agentId),
    onSuccess: (data, agentId) => {
      toast.success(`Agent ${agentId} restarted successfully`);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to restart agent: ${error.message || 'Unknown error'}`);
    }
  });

  // Mutation for unregistering agent
  const unregisterAgentMutation = useMutation({
    mutationFn: (agentId: string) => endpoints.unregisterAgent(agentId),
    onSuccess: (data, agentId) => {
      toast.success(`Agent ${agentId} unregistered successfully`);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to unregister agent: ${error.message || 'Unknown error'}`);
    }
  });

  // Helper functions
  const setAgentModel = (agentId: string, modelPath: string) => {
    setAgentModelMutation.mutate({ agentId, modelPath });
  };

  const restartAgent = (agentId: string) => {
    restartAgentMutation.mutate(agentId);
  };

  const unregisterAgent = (agentId: string) => {
    unregisterAgentMutation.mutate(agentId);
  };

  const getAgentById = (agentId: string): Agent | undefined => {
    return agents.find(agent => agent.id === agentId);
  };

  const getAgentsByStatus = (status: string): Agent[] => {
    return agents.filter(agent => agent.status === status);
  };

  const getRunningAgents = (): Agent[] => {
    return agents.filter(agent => agent.is_running);
  };

  const getStoppedAgents = (): Agent[] => {
    return agents.filter(agent => !agent.is_running);
  };

  const getAgentsWithModels = (): Agent[] => {
    return agents.filter(agent => agent.model_path);
  };

  const getAgentsWithoutModels = (): Agent[] => {
    return agents.filter(agent => !agent.model_path);
  };

  return {
    // Data
    agents,
    availableModels,
    
    // Loading states
    isLoadingAgents,
    isLoadingModels,
    isLoading: isLoadingAgents || isLoadingModels,
    
    // Errors
    agentsError,
    modelsError,
    
    // Mutations
    setAgentModel,
    restartAgent,
    unregisterAgent,
    
    // Mutation states
    isSettingModel: setAgentModelMutation.isPending,
    isRestarting: restartAgentMutation.isPending,
    isUnregistering: unregisterAgentMutation.isPending,
    
    // Helper functions
    getAgentById,
    getAgentsByStatus,
    getRunningAgents,
    getStoppedAgents,
    getAgentsWithModels,
    getAgentsWithoutModels,
    
    // Refetch functions
    refetchAgents,
    refetchModels
  };
};

// Hook for a single agent
export const useAgent = (agentId: string) => {
  const queryClient = useQueryClient();

  const {
    data: agent,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => endpoints.getAgent(agentId),
    enabled: !!agentId,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000 // Consider data stale after 10 seconds
  });

  // Mutation for setting agent model
  const setAgentModelMutation = useMutation({
    mutationFn: (modelPath: string) => endpoints.setAgentModel(agentId, modelPath),
    onSuccess: (data) => {
      toast.success(`Model updated for agent ${agentId}`);
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to update model: ${error.message || 'Unknown error'}`);
    }
  });

  // Mutation for restarting agent
  const restartAgentMutation = useMutation({
    mutationFn: () => endpoints.restartAgent(agentId),
    onSuccess: (data) => {
      toast.success(`Agent ${agentId} restarted successfully`);
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to restart agent: ${error.message || 'Unknown error'}`);
    }
  });

  return {
    agent,
    isLoading,
    error,
    refetch,
    setAgentModel: setAgentModelMutation.mutate,
    restartAgent: restartAgentMutation.mutate,
    isSettingModel: setAgentModelMutation.isPending,
    isRestarting: restartAgentMutation.isPending
  };
};

// Hook for agent detailed information
export const useAgentDetailedInfo = (agentId: string) => {
  const {
    data: agentDetailedInfo,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['agent-detailed-info', agentId],
    queryFn: () => endpoints.getAgentDetailedInfo(agentId),
    enabled: !!agentId,
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000 // Consider data stale after 30 seconds
  });

  return {
    agentDetailedInfo,
    isLoading,
    error,
    refetch
  };
};

// Hook for multiple agents detailed information
export const useAgentsDetailedInfo = (agentIds?: string[]) => {
  const {
    data: agentsDetailedInfo = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['agents-detailed-info', agentIds],
    queryFn: () => endpoints.getAgentsDetailedInfo(agentIds),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000 // Consider data stale after 30 seconds
  });

  return {
    agentsDetailedInfo,
    isLoading,
    error,
    refetch
  };
}; 