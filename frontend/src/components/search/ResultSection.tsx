import React from 'react';
import {
  Box,
  VStack,
  Text,
  Divider,
  Skeleton,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Fade,
  SlideFade,
  useBreakpointValue,
  Wrap,
  WrapItem,
  LinkBox,
  LinkOverlay,
  AspectRatio,
  Image
} from '@chakra-ui/react';
import SearchResult from './SearchResult';
import ReasoningSteps from './ReasoningSteps';
import { useSearch } from 'context/SearchContext';
import { ReasoningStep, Source } from '../../context/SearchContext';

interface ResultSectionProps {
  query: string;
  results: any[];
  reasoning: ReasoningStep[];
  sources?: Source[];
  relatedSearches?: string[];
}

const ResultSection = ({ query, results, reasoning, sources = [], relatedSearches = [] }: ResultSectionProps) => {
  const { error, performSearch } = useSearch();

  const handleRelatedSearchClick = (searchQuery: string) => {
    performSearch(searchQuery);
  };

  return (
    <VStack spacing={6} align="stretch" width="100%">
      {error && (
        <Box color="red.500" mb={4}>
          Error: {error}
        </Box>
      )}

      {/* Single Search Result */}
      <Box width="100%">
        <SearchResult
          query={query}
          result={results[0]} // Show only the first result
          sources={sources}
        />
      </Box>
    </VStack>
  );
};

export default ResultSection;