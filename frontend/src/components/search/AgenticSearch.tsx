import React, { useState, useEffect } from 'react';
import { FaSpinner, FaSearch, FaCheckCircle, FaClock, FaFileAlt } from 'react-icons/fa';
import { useSearchContext } from '../../context/SearchContext';
import { VStack, Box, Text, Skeleton, Tabs, TabList, Tab, TabPanels, TabPanel, Badge, Flex, Icon } from '@chakra-ui/react';
import { InfoIcon } from '@chakra-ui/icons';
import ResultSection from './ResultSection';
import SourcesPanel from './SourcesPanel';
import ImageGallery from './ImageGallery';
import ResultPreview from './ResultPreview';
import { motion } from 'framer-motion';

const MotionBox = motion(Box);

interface ResearchStep {
  id: string;
  query: string;
  reasoning: string;
  results_count: number;
  timestamp: string;
  execution_time: number;
}

interface ResearchPlan {
  id: string;
  original_query: string;
  steps: ResearchStep[];
  created_at: string;
  updated_at: string;
  synthesis: string;
  final_answer: string;
  status: string;
}

const AgenticSearch: React.FC = () => {
  const { agenticSearch, isLoading, error } = useSearchContext();
  const [activeTab, setActiveTab] = useState<'report' | 'steps'>('report');
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  // Toggle step expansion
  const toggleStep = (stepId: string) => {
    const newExpandedSteps = new Set(expandedSteps);
    if (expandedSteps.has(stepId)) {
      newExpandedSteps.delete(stepId);
    } else {
      newExpandedSteps.add(stepId);
    }
    setExpandedSteps(newExpandedSteps);
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Prepare the research results in a format similar to standard search
  const prepareSynthesisResult = () => {
    if (!agenticSearch?.synthesis) return [];
    
    return [{
      content: agenticSearch.synthesis,
      type: 'text'
    }];
  };

  // Prepare research steps as "reasoning" similar to standard search
  const prepareReasoningSteps = () => {
    if (!agenticSearch?.research_steps) return [];
    
    return agenticSearch.research_steps.map((step, index) => ({
      step: index + 1,
      thought: `${step.query} - ${step.reasoning}`
    }));
  };

  // Render the final research report in the standard search format
  const renderResearchReport = () => {
    if (!agenticSearch?.synthesis) {
      return <Text color="gray.500" py={4}>No research synthesis available</Text>;
    }

    const synthesisResults = prepareSynthesisResult();
    const reasoningSteps = prepareReasoningSteps();
    
    return (
      <ResultSection 
        query={agenticSearch.original_query}
        results={synthesisResults}
        reasoning={reasoningSteps}
        sources={[]} // We could extract sources from research steps if needed
      />
    );
  };

  // Render each research step
  const renderResearchSteps = () => {
    if (!agenticSearch?.research_steps || agenticSearch.research_steps.length === 0) {
      return <Text color="gray.500" mt={4}>No research steps available</Text>;
    }

    return (
      <VStack spacing={4} mt={4} align="stretch">
        {agenticSearch.research_steps.map((step, index) => (
          <Box 
            key={step.id} 
            borderWidth="1px"
            borderRadius="lg"
            overflow="hidden"
            shadow="sm"
          >
            <Flex 
              bg="gray.50" 
              p={4} 
              alignItems="center" 
              justifyContent="space-between"
              cursor="pointer"
              onClick={() => toggleStep(step.id)}
            >
              <Flex alignItems="center" gap={3}>
                <Badge colorScheme="blue" borderRadius="full">
                  Step {index + 1}
                </Badge>
                <Text fontWeight="medium" color="gray.900">{step.query}</Text>
              </Flex>
              <Flex alignItems="center" fontSize="sm" color="gray.500" gap={4}>
                <Flex alignItems="center" gap={1}>
                  <Icon as={FaClock} color="gray.400" />
                  {formatTime(step.timestamp)}
                </Flex>
                <Flex alignItems="center" gap={1}>
                  <Icon as={FaFileAlt} color="gray.400" />
                  {step.results_count} results
                </Flex>
                <Text color="gray.400">
                  {expandedSteps.has(step.id) ? '▲' : '▼'}
                </Text>
              </Flex>
            </Flex>
            
            {expandedSteps.has(step.id) && (
              <Box p={4} bg="white" borderTopWidth="1px" borderColor="gray.200">
                <Box mb={3}>
                  <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={1}>
                    Reasoning
                  </Text>
                  <Text color="gray.600" fontSize="sm">{step.reasoning}</Text>
                </Box>
                <Box>
                  <Text fontSize="sm" fontWeight="semibold" color="gray.700" mb={1}>
                    Execution
                  </Text>
                  <Text color="gray.600" fontSize="sm">
                    Found {step.results_count} results in {step.execution_time.toFixed(2)}s
                  </Text>
                </Box>
              </Box>
            )}
          </Box>
        ))}
      </VStack>
    );
  };

  // Loading skeleton - matches the skeleton pattern in Home.tsx
  const renderLoadingSkeleton = () => {
    return (
      <VStack spacing={4} align="stretch" py={4}>
        <Skeleton height="20px" width="90%" borderRadius="md" />
        <Skeleton height="20px" width="100%" borderRadius="md" />
        <Skeleton height="20px" width="95%" borderRadius="md" />
        <Skeleton height="20px" width="85%" borderRadius="md" />
        <Skeleton height="20px" width="90%" borderRadius="md" />
      </VStack>
    );
  };

  // Error state
  const renderError = () => {
    return (
      <Box rounded="md" bg="red.50" p={4} mt={4}>
        <Flex>
          <Box flexShrink={0}>
            <InfoIcon color="red.400" />
          </Box>
          <Box ml={3}>
            <Text fontSize="sm" fontWeight="medium" color="red.800">
              Error conducting research
            </Text>
            <Text mt={2} fontSize="sm" color="red.700">
              {error || 'An unexpected error occurred'}
            </Text>
          </Box>
        </Flex>
      </Box>
    );
  };

  return (
    <MotionBox 
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      width="100%"
    >
      {/* Research status indicator */}
      {agenticSearch && !isLoading && (
        <Flex alignItems="center" mb={4}>
          <Badge 
            colorScheme={
              agenticSearch.status === 'completed' ? 'green' : 
              agenticSearch.status === 'in_progress' ? 'blue' : 'yellow'
            }
            fontSize="xs"
            borderRadius="full"
            px={2}
            py={1}
            mr={2}
          >
            {agenticSearch.status}
          </Badge>
          <Text fontSize="sm" color="gray.500">
            {agenticSearch.iterations_completed} of {agenticSearch.max_iterations} iterations completed
          </Text>
        </Flex>
      )}

      {/* Tabs - using the same style as in Home.tsx */}
      <Tabs variant="soft-rounded" colorScheme="blue" isLazy width="100%">
        <TabList mb={4} pb={2} borderBottom="1px" borderColor="gray.100">
          <Tab mr={2} borderRadius="md" _selected={{ color: 'blue.700', bg: 'blue.50' }}>
            Answer
          </Tab>
          <Tab borderRadius="md" _selected={{ color: 'blue.700', bg: 'blue.50' }}>
            Research Process
            {agenticSearch?.research_steps && (
              <Badge ml={2} colorScheme="gray" borderRadius="full">
                {agenticSearch.research_steps.length}
              </Badge>
            )}
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel px={0} pt={4}>
            {/* Loading or Results for the Answer tab */}
            {isLoading ? (
              renderLoadingSkeleton()
            ) : error ? (
              renderError()
            ) : agenticSearch ? (
              renderResearchReport()
            ) : (
              <Flex direction="column" align="center" py={12}>
                <Icon as={FaSearch} boxSize={12} color="gray.300" />
                <Text mt={2} fontSize="sm" fontWeight="semibold" color="gray.900">
                  No research results
                </Text>
                <Text mt={1} fontSize="sm" color="gray.500">
                  Start a search to see agentic research results.
                </Text>
              </Flex>
            )}
          </TabPanel>
          
          <TabPanel px={0} pt={4}>
            {/* Research Steps Tab */}
            {isLoading ? (
              renderLoadingSkeleton()
            ) : error ? (
              renderError()
            ) : agenticSearch ? (
              renderResearchSteps()
            ) : (
              <Text color="gray.500" py={4}>No research steps available</Text>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </MotionBox>
  );
};

export default AgenticSearch; 