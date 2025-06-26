import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../components/common/Table';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../components/common/Select';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '../components/common/Dialog';
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle, 
  AlertDialogTrigger 
} from '../components/common/AlertDialog';
import { useAgents } from '../hooks/useAgents';
import { Agent, AvailableModel } from '../services/types';
import { 
  Play, 
  Square, 
  RefreshCw, 
  Settings, 
  Trash2, 
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';

const Agents: React.FC = () => {
  const {
    agents,
    availableModels,
    isLoading,
    setAgentModel,
    restartAgent,
    unregisterAgent,
    isSettingModel,
    isRestarting,
    isUnregistering
  } = useAgents();

  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isModelDialogOpen, setIsModelDialogOpen] = useState(false);

  const handleSetModel = (agent: Agent) => {
    setSelectedAgent(agent);
    setSelectedModel(agent.model_path || '');
    setIsModelDialogOpen(true);
  };

  const handleConfirmSetModel = () => {
    if (selectedAgent && selectedModel) {
      setAgentModel(selectedAgent.id, selectedModel);
      setIsModelDialogOpen(false);
      setSelectedAgent(null);
      setSelectedModel('');
    }
  };

  const handleRestartAgent = (agent: Agent) => {
    restartAgent(agent.id);
  };

  const handleUnregisterAgent = (agent: Agent) => {
    unregisterAgent(agent.id);
  };

  const getStatusIcon = (agent: Agent) => {
    if (agent.is_running) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (agent.status === 'error') {
      return <XCircle className="h-4 w-4 text-red-500" />;
    } else {
      return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (agent: Agent) => {
    if (agent.is_running) {
      return <Badge variant="success">Running</Badge>;
    } else if (agent.status === 'error') {
      return <Badge variant="destructive">Error</Badge>;
    } else {
      return <Badge variant="secondary">Stopped</Badge>;
    }
  };

  const formatLastRun = (lastRun: string | null) => {
    if (!lastRun) return 'Never';
    const date = new Date(lastRun);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getModelName = (modelPath: string | null) => {
    if (!modelPath) return 'No model assigned';
    const model = availableModels.find(m => m.path === modelPath);
    return model ? model.name : modelPath.split('/').pop() || modelPath;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agent Management</h1>
          <p className="text-gray-600 mt-2">
            Manage agents and their model associations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            {agents.filter(a => a.is_running).length} Running
          </Badge>
          <Badge variant="outline">
            {agents.length} Total
          </Badge>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Registered Agents</CardTitle>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No agents registered</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Capabilities</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(agent)}
                        <div>
                          <div className="font-medium">{agent.name}</div>
                          <div className="text-sm text-gray-500">{agent.description}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(agent)}
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs truncate">
                        {getModelName(agent.model_path)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {formatLastRun(agent.last_run)}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {agent.capabilities.slice(0, 2).map((capability, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {capability}
                          </Badge>
                        ))}
                        {agent.capabilities.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{agent.capabilities.length - 2} more
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleSetModel(agent)}
                          disabled={isSettingModel}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRestartAgent(agent)}
                          disabled={isRestarting}
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              size="sm"
                              variant="destructive"
                              disabled={isUnregistering}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Unregister Agent</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to unregister {agent.name}? 
                                This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleUnregisterAgent(agent)}
                                className="bg-red-600 hover:bg-red-700"
                              >
                                Unregister
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Model Assignment Dialog */}
      <Dialog open={isModelDialogOpen} onOpenChange={setIsModelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Model to {selectedAgent?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Select Model
              </label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">No model</SelectItem>
                  {availableModels.map((model) => (
                    <SelectItem key={model.path} value={model.path}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setIsModelDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmSetModel}
                disabled={!selectedModel || isSettingModel}
              >
                {isSettingModel ? 'Updating...' : 'Update Model'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Agents; 