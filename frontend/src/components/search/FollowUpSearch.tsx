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
  Textarea,
  ButtonGroup,
  Button,
  Icon,
  VStack
} from '@chakra-ui/react';
import { ArrowForwardIcon, SearchIcon as ChakraSearchIcon, ChatIcon } from '@chakra-ui/icons';
import { FiBriefcase, FiSearch } from 'react-icons/fi';
import { useSearchContext } from 'context/SearchContext';

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
  const { 
    isConversationMode, 
    searchThread, 
    agenticSearchMode, 
    setAgenticSearchMode 
  } = useSearchContext();
  
  // Hoist all useColorModeValue calls to the top level
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const buttonActiveBg = useColorModeValue("blue.50", "blue.800");
  const buttonActiveColor = useColorModeValue("blue.600", "blue.200");
  const buttonHoverBg = useColorModeValue("gray.100", "gray.700");
  const activeResearchIconColorValue = useColorModeValue("blue.600", "blue.200");
  const researchIconColor = agenticSearchMode ? activeResearchIconColorValue : "currentColor";

  const textareaBg = useColorModeValue("gray.100", "gray.700");
  const textareaHoverBg = useColorModeValue("gray.200", "gray.600");
  const textareaFocusBg = useColorModeValue("gray.100", "gray.700");
  const textareaFocusBorderColor = useColorModeValue("gray.300", "gray.500");
  const textareaBorderColor = useColorModeValue("gray.200", "gray.600");

  const isMobile = useBreakpointValue({ base: true, md: false });

  const getPlaceholderText = () => {
    if (agenticSearchMode) {
      return "Ask for in-depth research...";
    }
    if (!isConversationMode || searchThread.length === 0) {
      return "Ask anything...";
    }
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

  // Mobile-optimized version with integrated toggle
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
        p={3}
      >
        <form onSubmit={handleSubmit}>
          <VStack spacing={2} align="stretch">
            <ButtonGroup size="sm" isAttached variant="outline" width="100%">
              <Button 
                leftIcon={<Icon as={FiSearch} />}
                onClick={() => setAgenticSearchMode(false)} 
                isActive={!agenticSearchMode}
                flex="1"
                mr="-px"
                _active={{ bg: buttonActiveBg, color: buttonActiveColor }}
                _hover={{ bg: buttonHoverBg }}
              >
                Standard
              </Button>
              <Button 
                leftIcon={<Icon as={FiBriefcase} color={researchIconColor} />}
                onClick={() => setAgenticSearchMode(true)} 
                isActive={agenticSearchMode}
                flex="1"
                _active={{ bg: buttonActiveBg, color: buttonActiveColor }}
                _hover={{ bg: buttonHoverBg }}
              >
                Research
              </Button>
            </ButtonGroup>
            <Box position="relative">
              <Textarea
                placeholder={getPlaceholderText()}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                bg={textareaBg}
                _hover={{ bg: textareaHoverBg }}
                _focus={{ bg: textareaFocusBg, borderColor: textareaFocusBorderColor }}
                borderRadius="xl"
                minHeight="50px"
                maxHeight="120px"
                fontSize="sm"
                paddingRight="50px"
                paddingY="12px"
                paddingLeft="16px"
                borderWidth="1px"
                borderColor={textareaBorderColor}
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
          </VStack>
        </form>
      </Box>
    );
  }

  // Desktop version with integrated toggle
  return (
    <SlideFade in={isVisible} offsetY="20px">
      <Box
        position={useFixedPosition ? "fixed" : "relative"}
        bottom={useFixedPosition ? { base: "70px", md: "32px" } : undefined}
        left={useFixedPosition ? "50%" : undefined}
        transform={useFixedPosition ? "translateX(-50%)" : undefined}
        width={useFixedPosition ? { base: "calc(100% - 32px)", md: "80%", lg: "70%" } : "100%"}
        maxW={useFixedPosition ? { base: "calc(100% - 32px)", md: "calc(100% - 48px)", lg: "1400px" } : "100%"}
        px={useFixedPosition ? { base: 4, md: 0 } : 0}
        zIndex={useFixedPosition ? 10 : undefined}
      >
        <Box
          boxShadow={isFocused ? "2xl" : (useFixedPosition ? "xl" : "none")}
          borderRadius={{ base: "xl", md: "2xl" }}
          bg={bgColor}
          borderWidth="1px"
          borderColor={isFocused ? "blue.400" : borderColor}
          overflow="visible"
          transition="all 0.2s ease"
          _hover={{ boxShadow: useFixedPosition ? "2xl" : "none", borderColor: "blue.400" }}
        >
          <form onSubmit={handleSubmit}>
            <VStack spacing={0} align="stretch">
              <ButtonGroup 
                size="sm" 
                isAttached 
                variant="outline" 
                p={useFixedPosition ? 2 : 1}
                pb={0}
              >
                <Button 
                  leftIcon={<Icon as={FiSearch} />}
                  onClick={() => setAgenticSearchMode(false)} 
                  isActive={!agenticSearchMode}
                  flexGrow={1}
                  borderBottomRadius={0}
                  _active={{ bg: buttonActiveBg, color: buttonActiveColor }}
                  _hover={{ bg: buttonHoverBg }}
                >
                  Standard
                </Button>
                <Button 
                  leftIcon={<Icon as={FiBriefcase} color={researchIconColor} />}
                  onClick={() => setAgenticSearchMode(true)} 
                  isActive={agenticSearchMode}
                  flexGrow={1}
                  borderBottomRadius={0}
                  _active={{ bg: buttonActiveBg, color: buttonActiveColor }}
                  _hover={{ bg: buttonHoverBg }}
                >
                  Deep Research
                </Button>
              </ButtonGroup>
              <Flex 
                align="center" 
                p={{ base: 2, md: useFixedPosition ? 2 : 1 }}
                pt={{ base:1, md: useFixedPosition ? 1 : 0.5}}
                flexDir="row"
              >
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
            </VStack>
          </form>
        </Box>
      </Box>
    </SlideFade>
  );
};

export default FollowUpSearch;
