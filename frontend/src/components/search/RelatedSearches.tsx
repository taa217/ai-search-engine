import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Text,
  Button,
  Flex,
  Wrap,
  WrapItem,
  useColorModeValue,
  Tag,
  TagLabel,
  TagCloseButton,
  SlideFade,
  Heading,
  Icon,
  HStack,
  Tooltip,
  Spacer,
  IconButton
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaSearch, FaLightbulb, FaPlus } from 'react-icons/fa';
import { ArrowForwardIcon } from '@chakra-ui/icons';
import { useSearch } from '../../context/SearchContext';

// Animated version of the Box component
const MotionBox = motion(Box);
const MotionWrapItem = motion(WrapItem);

interface RelatedSearchesProps {
  baseQuery: string;
  onSearch: (query: string) => void;
  isMobile?: boolean;
  relatedSearches: string[];
  onSearchClick: (query: string) => void;
}

// In a real application, these would be generated based on the current search
const generateRelatedQueries = (baseQuery: string): string[] => {
  // Default suggestions
  const defaultSuggestions = [
    "best practices",
    "getting started",
    "advanced techniques",
    "comparison",
    "implementation guide",
    "use cases",
    "performance optimization",
    "security considerations",
    "industry trends",
    "expert insights",
    "troubleshooting",
    "integration guide"
  ];
  
  // Specific suggestions based on query types
  if (baseQuery.toLowerCase().includes('ai')) {
    return [
      "AI ethics",
      "machine learning vs AI",
      "AI in healthcare",
      "AI tools for business",
      "open source AI",
      "AI limitations",
      "future of AI",
      "AI programming languages"
    ];
  }
  
  if (baseQuery.toLowerCase().includes('climate') || baseQuery.toLowerCase().includes('environment')) {
    return [
      "climate solutions",
      "renewable energy",
      "carbon footprint",
      "climate policy",
      "sustainable development",
      "climate data",
      "environmental impact",
      "green technology"
    ];
  }
  
  // Combine the query with default suggestions
  return defaultSuggestions.map(s => `${baseQuery} ${s}`);
};

const RelatedSearches: React.FC<RelatedSearchesProps> = ({ baseQuery, onSearch, isMobile = false, relatedSearches, onSearchClick }) => {
  const [relatedQueries, setRelatedQueries] = useState<string[]>([]);
  const [selectedQueries, setSelectedQueries] = useState<string[]>([]);
  
  // Colors
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const chipBgColor = useColorModeValue('gray.50', 'gray.700');
  const selectedChipBgColor = useColorModeValue('blue.50', 'blue.900');
  const selectedChipTextColor = useColorModeValue('blue.700', 'blue.200');
  const buttonHoverBg = useColorModeValue('blue.600', 'blue.500');
  const textColor = useColorModeValue('gray.800', 'white');
  const hoverBgColor = useColorModeValue('blue.50', 'blue.800');
  
  // Generate related queries when base query changes
  useEffect(() => {
    if (baseQuery) {
      setRelatedQueries(generateRelatedQueries(baseQuery));
      setSelectedQueries([]);
    }
  }, [baseQuery]);
  
  // Toggle selection of a query
  const toggleQuery = useCallback((query: string) => {
    setSelectedQueries(prev => 
      prev.includes(query)
        ? prev.filter(q => q !== query)
        : [...prev, query]
    );
  }, []);
  
  // Execute the combined search
  const handleCombinedSearch = () => {
    if (selectedQueries.length === 0) return;
    
    // Create a combined query string
    const combinedQuery = selectedQueries.join(' + ');
    onSearch(combinedQuery);
  };
  
  // Clear all selected queries
  const clearSelections = () => {
    setSelectedQueries([]);
  };
  
  // If no related queries are available, don't render anything
  if (relatedQueries.length === 0) return null;

  return (
    <SlideFade in={relatedQueries.length > 0} offsetY="20px">
      <Box
        p={5}
        borderRadius="xl"
        bg="transparent"
        borderWidth="0px"
        mb={6}
        overflow="hidden"
        transition="all 0.2s ease"
      >
        {/* Header section with title and explanation */}
        <Flex align="center" mb={4}>
          <Icon as={FaLightbulb} color="yellow.400" mr={2} />
          <Heading size="sm" fontWeight="semibold">Expand your search</Heading>
          <Spacer />
          {selectedQueries.length > 0 && (
            <Tooltip label="Clear all selections">
              <Button 
                size="xs" 
                variant="ghost" 
                colorScheme="gray"
                onClick={clearSelections}
              >
                Clear
              </Button>
            </Tooltip>
          )}
        </Flex>
        
        {/* Selected queries - displayed as tags */}
        <AnimatePresence>
          {selectedQueries.length > 0 && (
            <MotionBox
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              overflow="hidden"
              mb={4}
            >
              <Wrap spacing={2}>
                {selectedQueries.map((query) => (
                  <MotionWrapItem
                    key={query}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.15 }}
                  >
                    <Tag
                      size="md"
                      colorScheme="blue"
                      borderRadius="full"
                      variant="solid"
                      boxShadow="sm"
                    >
                      <TagLabel>{query}</TagLabel>
                      <TagCloseButton onClick={() => toggleQuery(query)} />
                    </Tag>
                  </MotionWrapItem>
                ))}
              </Wrap>
            </MotionBox>
          )}
        </AnimatePresence>
        
        {/* Related query chips that can be selected */}
        <Wrap spacing={2} mb={selectedQueries.length > 0 ? 4 : 0}>
          {relatedQueries.map((query) => {
            const isSelected = selectedQueries.includes(query);
            return (
              <WrapItem key={query}>
                <Box
                  as="button"
                  py={1.5}
                  px={3}
                  borderRadius="full"
                  fontSize="sm"
                  fontWeight={isSelected ? "medium" : "normal"}
                  bg={isSelected ? selectedChipBgColor : chipBgColor}
                  color={isSelected ? selectedChipTextColor : "gray.700"}
                  borderWidth="1px"
                  borderColor={isSelected ? "blue.200" : "transparent"}
                  onClick={() => toggleQuery(query)}
                  transition="all 0.2s ease"
                  _hover={{
                    transform: "translateY(-1px)",
                    boxShadow: "sm",
                    bg: isSelected ? selectedChipBgColor : "gray.100"
                  }}
                  _active={{
                    transform: "scale(0.97)",
                  }}
                  position="relative"
                >
                  {isSelected && (
                    <motion.div
                      style={{
                        position: "absolute",
                        top: "-6px",
                        right: "-6px",
                        backgroundColor: "#3182CE",
                        borderRadius: "100%",
                        width: "16px",
                        height: "16px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white"
                      }}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Icon as={FaPlus} fontSize="8px" />
                    </motion.div>
                  )}
                  {query}
                </Box>
              </WrapItem>
            );
          })}
        </Wrap>
        
        {/* Search button - only shows when chips are selected */}
        <AnimatePresence>
          {selectedQueries.length > 0 && (
            <MotionBox
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.2 }}
            >
              <Button
                leftIcon={<FaSearch />}
                colorScheme="blue"
                onClick={handleCombinedSearch}
                size={isMobile ? "sm" : "md"}
                width={isMobile ? "full" : "auto"}
                _hover={{
                  bg: buttonHoverBg,
                  transform: "translateY(-2px)",
                  boxShadow: "md"
                }}
                transition="all 0.2s"
              >
                Search selected topics
              </Button>
            </MotionBox>
          )}
        </AnimatePresence>
      </Box>
      <Box 
        mt={6} 
        p={4} 
        borderRadius="md" 
        borderWidth="1px"
        borderColor={borderColor}
        bg={bgColor}
      >
        <Heading as="h3" size="sm" mb={3} color={textColor}>
          Related Searches
        </Heading>
        
        <Wrap spacing={2}>
          {relatedSearches.map((searchQuery, index) => (
            <WrapItem key={`related-${index}`}>
              <Flex
                alignItems="center"
                px={3}
                py={2}
                borderRadius="full"
                border="1px solid"
                borderColor={borderColor}
                bg={bgColor}
                cursor="pointer"
                _hover={{ bg: hoverBgColor, transform: 'translateY(-1px)' }}
                transition="all 0.2s"
                onClick={() => onSearchClick(searchQuery)}
              >
                <Text fontSize="sm" fontWeight="medium">
                  {searchQuery}
                </Text>
                <IconButton
                  icon={<ArrowForwardIcon />}
                  aria-label="Search this query"
                  size="xs"
                  ml={2}
                  variant="ghost"
                  colorScheme="blue"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSearchClick(searchQuery);
                  }}
                />
              </Flex>
            </WrapItem>
          ))}
        </Wrap>
      </Box>
    </SlideFade>
  );
};

export default RelatedSearches; 