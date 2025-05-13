import React, { useState } from 'react';
import {
  Box,
  Text,
  Button,
  VStack,
  useColorModeValue,
  Center,
} from '@chakra-ui/react';
import { RepeatIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';
import { useSearch } from 'context/SearchContext';

const MotionBox = motion(Box);

interface ErrorRetryProps {
  query: string;
  searchId: string;
  onRetry?: () => void;
  errorMessage?: string;
}

const ErrorRetry: React.FC<ErrorRetryProps> = ({ 
  query, 
  searchId,
  onRetry,
  errorMessage = "We couldn't complete your search at this time."
}) => {
  const [isRetrying, setIsRetrying] = useState(false);
  const { retrySearch } = useSearch();
  
  // Colors - using neutral grays instead of red
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const textColor = useColorModeValue('gray.600', 'gray.300');
  
  // Handle retry with animation
  const handleRetryClick = () => {
    setIsRetrying(true);
    
    // Call the appropriate retry function
    const retryPromise = onRetry 
      ? Promise.resolve(onRetry()) 
      : retrySearch(searchId);
    
    // Wait for the retry to complete
    retryPromise
      .finally(() => {
        // Clear the retrying state after a reasonable delay for UX
        setTimeout(() => {
          setIsRetrying(false);
        }, 800);
      });
  };
  
  return (
    <MotionBox
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      width="100%"
      mb={4}
    >
      <Center>
        <VStack 
          spacing={6} 
          align="center" 
          py={10}
          px={4}
          maxW="500px"
        >
          <Text 
            color={textColor}
            fontSize="lg"
            textAlign="center"
          >
            Search failed
          </Text>
          
          <Button 
            leftIcon={<RepeatIcon />} 
            colorScheme="blue" 
            variant="solid" 
            size="md" 
            onClick={handleRetryClick}
            isLoading={isRetrying}
            loadingText="Retrying"
            _hover={{ transform: "translateY(-1px)" }}
            transition="all 0.2s"
          >
            Retry Search
          </Button>
        </VStack>
      </Center>
    </MotionBox>
  );
};

export default ErrorRetry; 