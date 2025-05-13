import React from 'react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Flex,
  IconButton,
  Text,
  Badge,
  Tooltip,
  useColorModeValue
} from '@chakra-ui/react';
import { FiChevronRight, FiX } from 'react-icons/fi';
import { useSearch } from '../../context/SearchContext'

const SearchSessionHeader = () => {
  const { sessionHistory, sessionId, clearSession, performSearch } = useSearch();
  const dividerColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Flex
      align="center"
      px={4}
      py={2}
      bg="white"
      borderBottomWidth="1px"
      borderColor={dividerColor}
    >
      <Flex align="center" flex={1} overflowX="auto">
        <Breadcrumb
          separator={<FiChevronRight color={dividerColor} />}
          spacing={2}
          fontSize="sm"
        >
          <BreadcrumbItem>
            <Text fontSize="sm" color="gray.500">
              Session: {sessionId?.slice(0, 6)}
            </Text>
          </BreadcrumbItem>

          {sessionHistory?.map((query, index) => (
            <BreadcrumbItem key={index}>
              <BreadcrumbLink
                onClick={() => performSearch(query)}
                _hover={{ textDecoration: 'none' }}
              >
                <Badge
                  colorScheme="blue"
                  variant="subtle"
                  fontWeight="medium"
                  borderRadius="md"
                  maxW="160px"
                  noOfLines={1}
                >
                  {query}
                </Badge>
              </BreadcrumbLink>
            </BreadcrumbItem>
          ))}
        </Breadcrumb>
      </Flex>

      {sessionHistory && sessionHistory.length > 0 && (
        <Tooltip label="Clear search session">
          <IconButton
            aria-label="Clear session"
            icon={<FiX />}
            size="sm"
            variant="ghost"
            onClick={() => clearSession?.()}
          />
        </Tooltip>
      )}
    </Flex>
  );
};

export default SearchSessionHeader;