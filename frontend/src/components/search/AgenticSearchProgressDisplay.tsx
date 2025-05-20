import React, { useState, useEffect } from 'react';
import { Box, VStack, Text, Spinner, Progress, Icon, HStack, Fade } from '@chakra-ui/react';
import { FiClipboard, FiShuffle, FiCpu, FiFileText, FiCheckCircle, FiDatabase, FiFilter, FiGitMerge } from 'react-icons/fi';

// Define the phases of research
const researchPhasesList = [
  { text: "Understanding your query...", icon: FiClipboard, duration: 2500, subText: "Analyzing keywords and intent." },
  { text: "Planning research strategy...", icon: FiShuffle, duration: 3500, subText: "Defining search pathways." },
  { text: "Gathering initial information...", icon: FiDatabase, duration: 5000, subText: "Querying multiple diverse sources..." },
  { text: "Analyzing preliminary findings...", icon: FiFilter, duration: 4000, subText: "Identifying key insights and patterns." },
  { text: "Performing deeper investigation...", icon: FiCpu, duration: 5000, subText: "Cross-referencing data and exploring connections..." },
  { text: "Synthesizing comprehensive answer...", icon: FiGitMerge, duration: 4000, subText: "Combining information into a coherent narrative." },
  { text: "Finalizing report & insights...", icon: FiCheckCircle, duration: 2000, subText: "Preparing the results for you." }
];

interface AgenticSearchProgressDisplayProps {
  originalQuery: string;
}

const AgenticSearchProgressDisplay: React.FC<AgenticSearchProgressDisplayProps> = ({ originalQuery }) => {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [progressValue, setProgressValue] = useState(0);
  const [currentPhaseData, setCurrentPhaseData] = useState(researchPhasesList[0]);

  useEffect(() => {
    // Set initial phase data
    setCurrentPhaseData(researchPhasesList[0]);
    setProgressValue(5); // Start with a small progress

    const timers: NodeJS.Timeout[] = [];
    let cumulativeDuration = 0;

    researchPhasesList.forEach((phase, index) => {
      const timer = setTimeout(() => {
        setCurrentPhaseIndex(index);
        setCurrentPhaseData(phase);
        // Calculate progress more smoothly based on phase completion
        setProgressValue(((index + 1) / researchPhasesList.length) * 100 * 0.9); // Aim for 90% before final
      }, cumulativeDuration);
      
      timers.push(timer);
      cumulativeDuration += phase.duration;
    });

    // Timer for the final "almost done" state
    const finalTimer = setTimeout(() => {
        setProgressValue(95); // Show nearly complete
        // Optionally, cycle back or hold on the last message
        if (currentPhaseIndex < researchPhasesList.length -1) { // if not already on last phase by timeout
            setCurrentPhaseIndex(researchPhasesList.length -1);
            setCurrentPhaseData(researchPhasesList[researchPhasesList.length -1]);
        }
    }, cumulativeDuration + 1000); // After all phases seem done

    return () => {
      timers.forEach(clearTimeout);
      clearTimeout(finalTimer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount


  return (
    <VStack spacing={6} align="stretch" py={8} px={{base: 2, md: 4}} w="100%">
      <Box textAlign="center">
        <Text fontSize={{base: "md", md: "lg"}} fontWeight="medium" color="blue.600">
          Conducting Deep Research on:
        </Text>
        <Text fontSize={{base: "lg", md: "xl"}} fontWeight="bold" color="gray.700" mt={1} noOfLines={2} px={2}>
          "{originalQuery}"
        </Text>
      </Box>
      
      <Progress value={progressValue} size="sm" colorScheme="blue" borderRadius="md" hasStripe isAnimated={currentPhaseIndex < researchPhasesList.length -1} />

      <Fade in={true} key={currentPhaseIndex}>
        <HStack 
            spacing={4} 
            align="center" 
            justifyContent="center" 
            p={4} 
            bg="whiteAlpha.700" 
            borderRadius="lg" 
            boxShadow="md"
            borderWidth="1px"
            borderColor="gray.100"
            minHeight="80px"
        >
          <Icon as={currentPhaseData.icon} w={6} h={6} color="blue.500" />
          <VStack align="start" spacing={0} flex={1}>
              <Text fontSize={{base: "sm", md: "md"}} fontWeight="medium" color="gray.800">
              {currentPhaseData.text}
              </Text>
              {currentPhaseData.subText && (
                  <Text fontSize={{base: "xs", md: "sm"}} color="gray.500">
                      {currentPhaseData.subText}
                  </Text>
              )}
          </VStack>
        </HStack>
      </Fade>

      <Text fontSize="xs" color="gray.500" textAlign="center" mt={2}>
        This advanced analysis may take a few moments. We appreciate your patience.
      </Text>
    </VStack>
  );
};

export default AgenticSearchProgressDisplay; 