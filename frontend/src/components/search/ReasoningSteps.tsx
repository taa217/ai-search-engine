import React from 'react';
import {
  Box,
  Heading,
  VStack,
  Text,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  useColorModeValue,
  Badge,
  Divider
} from '@chakra-ui/react';
import { ReasoningStep } from '../../context/SearchContext';

interface ReasoningStepsProps {
  steps: ReasoningStep[];
}

const ReasoningSteps: React.FC<ReasoningStepsProps> = ({ steps }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  if (!steps || steps.length === 0) {
    return null;
  }

  return (
    <Box 
      w="100%" 
      p={5} 
      borderRadius="lg" 
      bg={bgColor} 
      borderWidth="1px" 
      borderColor={borderColor}
      boxShadow="sm"
      mt={4}
    >
      <Accordion allowToggle>
        <AccordionItem border="none">
          <AccordionButton px={0}>
            <Box flex="1" textAlign="left">
              <Heading as="h3" size="md" fontWeight="semibold">
                AI Reasoning Process
              </Heading>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4} px={0}>
            <Divider my={4} />
            <VStack align="stretch" spacing={4}>
              {steps.map((step) => (
                <Box key={step.step} p={4} bg="gray.50" borderRadius="md">
                  <Box mb={2} display="flex" alignItems="center">
                    <Badge colorScheme="blue" mr={2}>Step {step.step}</Badge>
                    <Text fontWeight="semibold">Reasoning</Text>
                  </Box>
                  <Text>{step.thought}</Text>
                </Box>
              ))}
            </VStack>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </Box>
  );
};

export default ReasoningSteps;
