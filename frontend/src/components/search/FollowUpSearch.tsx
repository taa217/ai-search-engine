import React, { useState, KeyboardEvent } from 'react';
import {
  Box,
  InputGroup,
  Input,
  InputRightElement,
  IconButton,
  useColorModeValue,
  Flex,
  Text,
  SlideFade,
  useBreakpointValue,
  Textarea
} from '@chakra-ui/react';
import { ArrowForwardIcon, SearchIcon, ChatIcon } from '@chakra-ui/icons';
import { useSearch } from 'context/SearchContext';

interface FollowUpSearchProps {
  onSearch: (query: string) => void;
  isVisible: boolean;
  useFixedPosition?: boolean;
  onNewThread?: () => void;
}

const FollowUpSearch: React.FC<FollowUpSearchProps> = ({ 
  onSearch, 
  isVisible,
  useFixedPosition = true,
  onNewThread
}) => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const { isConversationMode, searchThread } = useSearch();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const isMobile = useBreakpointValue({ base: true, md: false });

  // Dynamic placeholder text based on conversation context
  const getPlaceholderText = () => {
    if (!isConversationMode || searchThread.length === 0) {
      return "Ask anything...";
    }
    
    // In conversation mode with previous searches
    return "Continue the conversation...";
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setQuery('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (query.trim()) {
        onSearch(query.trim());
        setQuery('');
      }
    }
  };

  // Mobile-optimized version
  if (isMobile) {
    return (
      <Box
        position="fixed"
        bottom={0}
        left={0}
        right={0}
        bg={bgColor}
        boxShadow="0 -2px 10px rgba(0, 0, 0, 0.05)"
        borderTopWidth="1px"
        borderTopColor={borderColor}
        zIndex={100}
      >
        <form onSubmit={handleSubmit}>
          <Box px={3} py={3}>
            <Box position="relative">
              <Textarea
                placeholder={getPlaceholderText()}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                bg="gray.100"
                _hover={{ bg: "gray.200" }}
                _focus={{ bg: "gray.100", borderColor: "gray.300" }}
                borderRadius="xl"
                minHeight="60px"
                maxHeight="120px"
                fontSize="sm"
                paddingRight="50px"
                paddingY="16px"
                paddingLeft="16px"
                borderWidth="1px"
                borderColor="gray.200"
                resize="none"
                overflowY="auto"
              />
              <Box
                position="absolute"
                right="8px"
                bottom="8px"
                zIndex={2}
              >
                <IconButton
                  size="sm"
                  type="submit"
                  colorScheme="blue"
                  aria-label="Send question"
                  icon={<ArrowForwardIcon />}
                  isRound
                />
              </Box>
            </Box>
          </Box>
        </form>
      </Box>
    );
  }

  // Original desktop version
  return (
    <SlideFade in={isVisible} offsetY="20px">
      <Box
        position={useFixedPosition ? "fixed" : "relative"}
        bottom={useFixedPosition ? { base: "70px", md: "32px" } : undefined}
        left={useFixedPosition ? "50%" : undefined}
        transform={useFixedPosition ? "translateX(-50%)" : undefined}
        width={useFixedPosition ? { base: "calc(100% - 32px)", md: "80%", lg: "70%" } : "100%"}
        maxW={useFixedPosition ? { base: "calc(100% - 32px)", md: "calc(100% - 48px)", lg: "1400px" } : "100%"}
        px={useFixedPosition ? { base: 4, md: 6 } : 0}
        zIndex={useFixedPosition ? 10 : undefined}
        mb={isMobile ? 0 : undefined}
      >
        <Box
          boxShadow={isFocused ? "2xl" : (useFixedPosition ? "xl" : "none")}
          borderRadius={{ base: "xl", md: "2xl" }}
          bg={bgColor}
          borderWidth="1px"
          borderColor={isFocused ? "blue.400" : borderColor}
          overflow="hidden"
          transition="all 0.2s ease"
          _hover={{ boxShadow: useFixedPosition ? "2xl" : "none", borderColor: "blue.400" }}
          mb={0}
        >
          <form onSubmit={handleSubmit}>
            <Flex 
              align="center" 
              p={{ base: 2, md: 3 }}
              flexDir="row"
            >
              <Box 
                fontWeight="medium" 
                color="blue.600"
                ml={{ base: 2, md: 3 }}
                mr={{ base: 1, md: 2 }}
                display="flex"
                alignItems="center"
                width="auto"
                flexShrink={0}
              >
                {isConversationMode ? (
                  <ChatIcon boxSize={{ base: "14px", md: "16px" }} mr={{ base: 1, md: 2 }} />
                ) : (
                  <SearchIcon boxSize={{ base: "14px", md: "16px" }} mr={{ base: 1, md: 2 }} />
                )}
                <Text 
                  fontSize={{ base: "xs", md: "sm" }}
                  display={{ base: "none", md: "block" }}
                  whiteSpace="nowrap"
                >
                  {isConversationMode ? "Ask Nexus:" : "Search:"}
                </Text>
              </Box>
              <InputGroup size={{ base: "md", md: "lg" }}>
                <Input
                  placeholder={getPlaceholderText()}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  border="none"
                  fontSize={{ base: "sm", md: "md" }}
                  height={{ base: "40px", md: "50px" }}
                  _focus={{ boxShadow: "none" }}
                  _hover={{ bg: hoverBg }}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  pr="4rem"
                  autoFocus={!useFixedPosition}
                />
                <InputRightElement width="3.5rem" h="full">
                  <IconButton
                    size={{ base: "sm", md: "md" }}
                    type="submit"
                    colorScheme="blue"
                    aria-label="Send question"
                    icon={<ArrowForwardIcon />}
                    isRound
                    mr={{ base: 1, md: 2 }}
                    _hover={{ transform: 'scale(1.05)' }}
                    transition="all 0.2s"
                  />
                </InputRightElement>
              </InputGroup>
            </Flex>
          </form>
        </Box>
      </Box>
    </SlideFade>
  );
};

export default FollowUpSearch;
