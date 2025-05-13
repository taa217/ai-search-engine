import React from 'react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Flex,
  IconButton,
  Text,
  useColorModeValue,
  Tooltip,
  Badge
} from '@chakra-ui/react';
import { FiChevronRight, FiX, FiClock } from 'react-icons/fi';
import { useSearch } from 'context/SearchContext';

const SearchSessionHeader = () => {
  const { sessionHistory, sessionId, clearSession, performSearch } = useSearch();
  const dividerColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Flex
      align="center"
      px={4}
      py={2}
      borderBottomWidth="1px"
      borderColor={dividerColor}
      bg="white"
      zIndex="sticky"
    >
      <Flex align="center" flex={1} overflowX="auto">
        <Breadcrumb
          separator={<FiChevronRight color={dividerColor} />}
          spacing={2}
          fontSize="sm"
        >
          <BreadcrumbItem>
            <BreadcrumbLink
              href="#"
              fontWeight="medium"
              display="flex"
              alignItems="center"
              onClick={(e) => {
                e.preventDefault();
                clearSession();
              }}
            >
              <FiClock style={{ marginRight: '6px' }} />
              {sessionId ? `Session #${sessionId.slice(0, 6)}` : 'New Session'}
            </BreadcrumbLink>
          </BreadcrumbItem>

          {sessionHistory?.map((query, index) => (
            <BreadcrumbItem key={index} isCurrentPage={index === sessionHistory?.length - 1}>
              <BreadcrumbLink
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  performSearch(query);
                }}
                maxW="200px"
                noOfLines={1}
              >
                <Badge
                  colorScheme="blue"
                  variant="subtle"
                  fontWeight="medium"
                  borderRadius="md"
                  px={2}
                  py={1}
                >
                  {query}
                </Badge>
              </BreadcrumbLink>
            </BreadcrumbItem>
          ))}
        </Breadcrumb>
      </Flex>

      {sessionHistory && sessionHistory.length > 0 && (
        <Tooltip label="Clear session history">
          <IconButton
            aria-label="Clear session"
            icon={<FiX />}
            size="sm"
            variant="ghost"
            onClick={() => clearSession()}
            ml={2}
          />
        </Tooltip>
      )}
    </Flex>
  );
};

export default SearchSessionHeader;