import React, { useState, useRef, KeyboardEvent } from 'react';
import { 
  InputGroup, 
  Input, 
  InputRightElement, 
  IconButton, 
  useColorModeValue,
  Box,
  Spinner,
  Flex,
  Tooltip,
  useBreakpointValue,
  Textarea
} from '@chakra-ui/react';
import { ArrowForwardIcon } from '@chakra-ui/icons';

interface SearchInputProps {
  placeholder?: string;
  initialValue?: string;
  isLoading?: boolean;
  onSearch: (query: string) => void;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'outline' | 'filled' | 'flushed' | 'unstyled';
  autoFocus?: boolean;
  radius?: string;
  isFullWidth?: boolean;
  width?: string;
  value?: string,
  isMobileLayout?: boolean;
}


const SearchInput: React.FC<SearchInputProps> = ({
  placeholder = 'Ask anything...',
  initialValue = '',
  isLoading = false,
  onSearch,
  size = 'lg',
  variant = 'outline',
  autoFocus = false,
  radius = '1xl',
  isFullWidth = true,
  width = '100%',
  value,
  isMobileLayout,
}) => {
  const [query, setQuery] = useState(initialValue);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  const isMobile = useBreakpointValue({ base: true, md: false });
  
  // Use the prop if provided, otherwise determine from breakpoint
  const isInMobileLayout = isMobileLayout !== undefined ? isMobileLayout : isMobile;
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.300', 'gray.600');
  const hoverBorderColor = useColorModeValue('gray.400', 'gray.500');
  const focusBorderColor = useColorModeValue('blue.500', 'blue.300');
  const buttonBgColor = useColorModeValue('blue.500', 'blue.400');
  const buttonHoverBgColor = useColorModeValue('blue.600', 'blue.500');

  const handleSearch = () => {
    if (query.trim()) {
      onSearch((query.trim()));
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  // Adjust height based on size prop and mobile layout
  const getInputHeight = () => {
    if (isInMobileLayout) return '50px';
    if (size === 'lg') return '100px';
    if (size === 'md') return '50px';
    return '40px';
  };

  // Adjust styling for mobile bottom bar style
  if (isInMobileLayout) {
    return (
      <Box 
        width="100%" 
        px={3}
        py={3}
        bg={bgColor}
        borderTopWidth="1px"
        borderTopColor={borderColor}
        boxShadow="0 -2px 10px rgba(0, 0, 0, 0.05)"
      >
        <Box position="relative">
          <Textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus={autoFocus}
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
            {isLoading ? (
              <Spinner size="sm" color="blue.500" thickness="2px" />
            ) : (
              <IconButton
                aria-label="Send"
                icon={<ArrowForwardIcon boxSize="16px" />}
                size="sm"
                isRound
                onClick={handleSearch}
                bg="blue.500"
                color="white"
                _hover={{ bg: "blue.600" }}
              />
            )}
          </Box>
        </Box>
      </Box>
    );
  }

  // Original desktop styling
  return (
    <Box 
      width={isFullWidth ? '100%' : width} 
      transition="all 0.3s ease"
    >
      <Flex
        position="relative"
        alignItems="center"
        transition="all 0.3s ease"
        transform={isFocused ? 'translateY(-2px)' : 'none'}
      >
        <InputGroup 
          size={size}
          boxShadow={isFocused ? 'lg' : 'sm'}
          borderRadius={radius}
          transition="all 0.3s ease"
        >
          <Input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            variant={variant}
            autoFocus={autoFocus}
            bg={variant === 'filled' ? 'gray.50' : bgColor}
            borderColor={borderColor}
            _hover={{ 
              bg: variant === 'filled' ? 'gray.100' : bgColor,
              borderColor: 'gray.300'
            }}
            _focus={{ 
              borderColor: 'gray.400', 
              boxShadow: 'sm',
              bg: 'white'
            }}
            borderRadius={radius}
            pr="60px"
            fontSize="md"
            height={getInputHeight()}
            paddingX="8"
            paddingY="3"
            transition="all 0.2s ease"
            _placeholder={{ 
              opacity: 0.7,
              color: 'gray.500'
            }}
          />
          <InputRightElement h="full" width="60px">
            {isLoading ? (
              <Spinner size="md" color="blue.500" mr={3} thickness="2px" />
            ) : (
              <Tooltip label="Send" placement="top" hasArrow>
                <IconButton
                  aria-label="Send"
                  icon={<ArrowForwardIcon boxSize="20px" />}
                  size="md"
                  isRound
                  onClick={handleSearch}
                  bg="blue.500"
                  color="white"
                  _hover={{ bg: "blue.600", transform: 'scale(1.05)' }}
                  _active={{ transform: 'scale(0.95)' }}
                  mr={5}
                  boxShadow="md"
                  transition="all 0.2s ease"
                />
              </Tooltip>
            )}
          </InputRightElement>
        </InputGroup>
      </Flex>
    </Box>
  );
};

export default SearchInput;
