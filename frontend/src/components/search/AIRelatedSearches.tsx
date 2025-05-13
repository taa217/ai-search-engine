import React, { useEffect } from 'react';
import {
  Box,
  Text,
  Wrap,
  WrapItem,
  useColorModeValue,
  Heading,
  Flex,
  IconButton,
  Fade
} from '@chakra-ui/react';
import { ArrowForwardIcon } from '@chakra-ui/icons';
import { useSearch } from '../../context/SearchContext';

interface AIRelatedSearchesProps {
  relatedSearches: string[];
  onSearchClick: (query: string) => void;
  isVisible?: boolean;
  baseQuery?: string; // Optional base query to generate fallbacks
}

const AIRelatedSearches: React.FC<AIRelatedSearchesProps> = ({ 
  relatedSearches = [], 
  onSearchClick,
  isVisible = true,
  baseQuery = ''
}) => {
  // Define colors based on color mode (light/dark)
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const hoverBgColor = useColorModeValue('blue.50', 'blue.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.800', 'white');

  // Debug log
  useEffect(() => {
    console.log('RelatedSearches prop:', relatedSearches);
    console.log('BaseQuery prop:', baseQuery);
    console.log('RelatedSearches details:', {
      isArray: Array.isArray(relatedSearches),
      length: relatedSearches ? relatedSearches.length : 0,
      firstItem: relatedSearches && relatedSearches.length > 0 ? relatedSearches[0] : null
    });
  }, [relatedSearches, baseQuery]);

  // Generate fallback searches if no results from backend
  const displaySearches = relatedSearches && relatedSearches.length > 0 
    ? relatedSearches 
    : baseQuery 
      ? generateBasicFallbacks(baseQuery)
      : [];
      
  // Additional debug log to check final decision
  useEffect(() => {
    console.log('AIRelatedSearches component:', {
      relatedSearchesProp: relatedSearches,
      baseQueryProp: baseQuery,
      usingFallback: !(relatedSearches && relatedSearches.length > 0),
      finalSearches: displaySearches
    });
  }, [displaySearches, relatedSearches, baseQuery]);

  function generateBasicFallbacks(query: string): string[] {
    if (!query) return [];
    
    const cleanQuery = query.trim();
    if (!cleanQuery) return [];
    
    console.log('Generating temporary fallbacks for query:', cleanQuery);
    
    // These are only shown temporarily until the server responds with proper AI-generated related searches
    // Much more minimal set of generic placeholders
    return [
      `More about ${cleanQuery}`,
      `${cleanQuery} details`,
      `Understanding ${cleanQuery}`,
      `${cleanQuery} explained`,
      `${cleanQuery} information`
    ];
  }

  // Skip rendering if we have nothing to show and we're not visible
  if ((!displaySearches || displaySearches.length === 0) && !isVisible) {
    console.log('No related searches to display, component hidden');
    return null;
  }

  // Force display of something if we're visible
  const searchesToShow = (displaySearches && displaySearches.length > 0) 
    ? displaySearches 
    : baseQuery 
      ? generateBasicFallbacks(baseQuery) 
      : ["Search examples", "Recent topics", "Popular questions", "Related concepts", "Similar searches"];

  return (
    <Fade in={isVisible} unmountOnExit>
      <Box 
        mt={0} 
        p={4} 
        borderRadius="lg" 
        borderWidth="1px"
        borderColor={borderColor}
        bg={bgColor}
        boxShadow="sm"
      >
        <Heading as="h3" size="sm" mb={3} color={textColor}>
          People also search for
        </Heading>
        
        <Wrap spacing={2}>
          {searchesToShow.map((searchQuery, index) => (
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
    </Fade>
  );
};

export default AIRelatedSearches; 