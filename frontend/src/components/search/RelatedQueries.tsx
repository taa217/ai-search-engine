import React from 'react';
import {
  Box,
  VStack,
  Text,
  Heading,
  useColorModeValue,
  Button,
  Wrap,
  WrapItem,
  Icon,
  Card,
  CardBody,
  Stack
} from '@chakra-ui/react';
import { FaLightbulb } from 'react-icons/fa';

interface RelatedQueriesProps {
  onSelectQuery: (query: string) => void;
}

// Example related queries - in a real app, these would be generated dynamically
const EXAMPLE_QUERIES = [
  "What are the latest advancements in AI?",
  "How does quantum computing work?",
  "Explain blockchain technology",
  "Best practices for web development in 2025",
  "How to implement machine learning models"
];

const RelatedQueries: React.FC<RelatedQueriesProps> = ({ onSelectQuery }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Card boxShadow="sm" bg={bgColor} borderColor={borderColor} borderWidth="1px" borderRadius="lg">
      <CardBody>
        <Stack spacing={4}>
          <Box display="flex" alignItems="center" mb={2}>
            <Icon as={FaLightbulb} color="yellow.500" mr={2} />
            <Heading as="h3" size="sm" fontWeight="semibold">
              Trending Queries
            </Heading>
          </Box>

          <VStack align="stretch" spacing={2}>
            {EXAMPLE_QUERIES.map((query, index) => (
              <Button
                key={index}
                size="sm"
                variant="ghost"
                justifyContent="flex-start"
                fontWeight="normal"
                overflow="hidden"
                textOverflow="ellipsis"
                whiteSpace="nowrap"
                onClick={() => onSelectQuery(query)}
                _hover={{ bg: 'blue.50', color: 'blue.600' }}
                borderRadius="md"
                px={3}
                py={2}
              >
                {query}
              </Button>
            ))}
          </VStack>
        </Stack>
      </CardBody>
    </Card>
  );
};

export default RelatedQueries;
