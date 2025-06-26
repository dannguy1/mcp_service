import logging
from typing import List, Dict, Any, Optional
import os

from .generic_agent import GenericAgent
from .ml_based_agent import MLBasedAgent
from .rule_based_agent import RuleBasedAgent

class HybridAgent(GenericAgent):
    """
    Hybrid agent that combines ML-based and rule-based detection approaches.
    Falls back to rule-based detection when ML model is unavailable.
    """
    
    def __init__(self, config: Dict[str, Any], data_service, model_manager=None):
        """
        Initialize the hybrid agent.
        
        Args:
            config: Configuration dictionary containing agent settings
            data_service: DataService instance for database access
            model_manager: ModelManager instance for model handling
        """
        super().__init__(config, data_service, model_manager)
        
        # Hybrid-specific configuration
        self.fallback_rules = self.analysis_rules.get('fallback_rules', {})
        self.enable_fallback = self.fallback_rules.get('enable_fallback', True)
        self.rule_based_detection = self.fallback_rules.get('rule_based_detection', True)
        
        # Initialize sub-agents
        self.ml_agent = None
        self.rule_agent = None
        
        # Determine primary detection method
        self.primary_method = 'ml_based' if self.model_path and os.path.exists(self.model_path) else 'rule_based'
        
        self._initialize_sub_agents()
    
    def _initialize_sub_agents(self):
        """Initialize the ML-based and rule-based sub-agents."""
        try:
            # Create ML-based agent if model is available
            if self.model_path and os.path.exists(self.model_path):
                self.ml_agent = MLBasedAgent(self.config, self.data_service, self.model_manager)
                self.logger.info("Initialized ML-based sub-agent")
            
            # Create rule-based agent for fallback or primary detection
            if self.enable_fallback or self.primary_method == 'rule_based':
                self.rule_agent = RuleBasedAgent(self.config, self.data_service, self.model_manager)
                self.logger.info("Initialized rule-based sub-agent")
            
            if not self.ml_agent and not self.rule_agent:
                raise ValueError("No detection method available for hybrid agent")
                
        except Exception as e:
            self.logger.error(f"Error initializing sub-agents: {e}")
            raise
    
    async def _perform_analysis(self, logs: List[Dict[str, Any]]):
        """
        Perform hybrid analysis on logs.
        
        Args:
            logs: List of log entries to analyze
        """
        try:
            anomalies_detected = 0
            
            # Primary detection method
            if self.primary_method == 'ml_based' and self.ml_agent:
                try:
                    await self.ml_agent._perform_analysis(logs)
                    self.logger.info("ML-based analysis completed successfully")
                    anomalies_detected += 1
                except Exception as e:
                    self.logger.warning(f"ML-based analysis failed: {e}")
                    if self.enable_fallback and self.rule_agent:
                        self.logger.info("Falling back to rule-based detection")
                        await self.rule_agent._perform_analysis(logs)
                        anomalies_detected += 1
            
            elif self.primary_method == 'rule_based' and self.rule_agent:
                await self.rule_agent._perform_analysis(logs)
                self.logger.info("Rule-based analysis completed successfully")
                anomalies_detected += 1
            
            # Secondary detection method (if enabled)
            if self.rule_based_detection and self.rule_agent and self.primary_method == 'ml_based':
                try:
                    await self.rule_agent._perform_analysis(logs)
                    self.logger.info("Secondary rule-based analysis completed")
                    anomalies_detected += 1
                except Exception as e:
                    self.logger.warning(f"Secondary rule-based analysis failed: {e}")
            
            self.logger.info(f"Hybrid analysis completed with {anomalies_detected} detection methods")
            
        except Exception as e:
            self.logger.error(f"Error in hybrid analysis: {e}")
            raise
    
    async def start(self):
        """Start the hybrid agent."""
        try:
            # Start sub-agents
            if self.ml_agent:
                await self.ml_agent.start()
            
            if self.rule_agent:
                await self.rule_agent.start()
            
            # Start the generic agent
            await super().start()
            
            self.logger.info(f"{self.agent_name} hybrid agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start hybrid agent: {e}")
            raise
    
    async def stop(self, unregister=True):
        """Stop the hybrid agent."""
        try:
            # Stop sub-agents
            if self.ml_agent:
                await self.ml_agent.stop(unregister=False)
            
            if self.rule_agent:
                await self.rule_agent.stop(unregister=False)
            
            # Stop the generic agent
            await super().stop(unregister)
            
            self.logger.info(f"{self.agent_name} hybrid agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping hybrid agent: {e}")
            raise
    
    def get_detection_methods(self) -> Dict[str, Any]:
        """
        Get information about the detection methods.
        
        Returns:
            dict: Detection method information
        """
        return {
            'primary_method': self.primary_method,
            'enable_fallback': self.enable_fallback,
            'rule_based_detection': self.rule_based_detection,
            'ml_agent_available': self.ml_agent is not None,
            'rule_agent_available': self.rule_agent is not None,
            'fallback_rules': self.fallback_rules
        }
    
    def update_detection_config(self, new_config: Dict[str, Any]):
        """
        Update the detection configuration.
        
        Args:
            new_config: New detection configuration
        """
        try:
            if 'fallback_rules' in new_config:
                self.fallback_rules = new_config['fallback_rules']
                self.enable_fallback = self.fallback_rules.get('enable_fallback', True)
                self.rule_based_detection = self.fallback_rules.get('rule_based_detection', True)
            
            # Update sub-agents if they exist
            if self.ml_agent and 'model_path' in new_config:
                self.ml_agent.update_model(new_config['model_path'])
            
            if self.rule_agent and 'analysis_rules' in new_config:
                self.rule_agent.update_rules(new_config['analysis_rules'])
            
            self.logger.info("Updated hybrid agent detection configuration")
            
        except Exception as e:
            self.logger.error(f"Error updating detection configuration: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the hybrid agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        status = super().get_status()
        status.update({
            'detection_methods': self.get_detection_methods(),
            'ml_agent_status': self.ml_agent.get_status() if self.ml_agent else None,
            'rule_agent_status': self.rule_agent.get_status() if self.rule_agent else None
        })
        return status
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model (from ML agent).
        
        Returns:
            dict: Model information
        """
        if self.ml_agent:
            return self.ml_agent.get_model_info()
        return {}
    
    def get_rule_info(self) -> Dict[str, Any]:
        """
        Get information about the current rules (from rule agent).
        
        Returns:
            dict: Rule information
        """
        if self.rule_agent:
            return self.rule_agent.get_rule_info()
        return {} 