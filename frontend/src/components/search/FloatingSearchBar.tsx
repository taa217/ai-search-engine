import React, { useState, useEffect, useRef } from 'react';
import {
  InputGroup,
  InputLeftElement,
  Input,
  InputRightElement,
  Box,
  IconButton,
  useDisclosure,
  SlideFade,
  List,
  ListItem,
  Text,
  Kbd,
  Flex,
} from '@chakra-ui/react';
import { FiSearch, FiCommand, FiArrowUp, FiArrowDown } from 'react-icons/fi';
import { useSearch } from 'context/SearchContext';

const FloatingSearchBar = () => {
  const { query, setQuery, performSearch, isLoading } = useSearch();
  const [localQuery, setLocalQuery] = useState(query);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [activeSuggestion, setActiveSuggestion] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Mock autocomplete - replace with API call
  useEffect(() => {
    if (localQuery.length > 2) {
      setSuggestions([
        `${localQuery} machine learning`,
        `${localQuery} AI applications`,
        `${localQuery} neural networks`,
      ]);
      onOpen();
    } else {
      onClose();
    }
  }, [localQuery]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch(localQuery);
      onClose();
    }
    if (e.key === 'ArrowDown') {
      setActiveSuggestion(prev => Math.min(prev + 1, suggestions.length - 1));
    }
    if (e.key === 'ArrowUp') {
      setActiveSuggestion(prev => Math.max(prev - 1, 0));
    }
  };

  return (
    <Box maxW="800px" mx="auto" px={4} pb={4}>
      <InputGroup size="lg" variant="flushed">
        <InputLeftElement pointerEvents="none">
          <FiSearch color="gray.400" />
        </InputLeftElement>

        <Input
          ref={inputRef}
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about AI..."
          fontSize="lg"
          pr="120px"
          _focusVisible={{ borderColor: 'blue.500', boxShadow: 'none' }}
        />

        <InputRightElement width="fit-content" mr={2}>
          <Flex align="center" gap={2}>
            <Kbd display={{ base: 'none', md: 'flex' }}>⌘ K</Kbd>
            <IconButton
              aria-label="Search"
              icon={<FiCommand />}
              size="sm"
              borderRadius="md"
              onClick={() => inputRef.current?.focus()}
            />
          </Flex>
        </InputRightElement>
      </InputGroup>

      <SlideFade in={isOpen && suggestions.length > 0} offsetY={-10}>
        <Box
          mt={2}
          bg="white"
          borderRadius="lg"
          boxShadow="xl"
          borderWidth="1px"
          borderColor="gray.100"
          maxH="300px"
          overflowY="auto"
        >
          <List spacing={0}>
            {suggestions.map((suggestion, index) => (
              <ListItem
                key={suggestion}
                p={3}
                bg={activeSuggestion === index ? 'blue.50' : 'transparent'}
                borderBottomWidth="1px"
                borderColor="gray.100"
                _last={{ border: 'none' }}
                _hover={{ bg: 'gray.50' }}
                cursor="pointer"
                onClick={() => {
                  setLocalQuery(suggestion);
                  performSearch(suggestion);
                  onClose();
                }}
              >
                <Flex align="center" justify="space-between">
                  <Text fontWeight="medium">{suggestion}</Text>
                  {activeSuggestion === index && (
                    <Flex gap={1} color="gray.500">
                      <FiArrowUp />
                      <FiArrowDown />
                    </Flex>
                  )}
                </Flex>
              </ListItem>
            ))}
          </List>
        </Box>
      </SlideFade>
    </Box>
  );
};

export default FloatingSearchBar;