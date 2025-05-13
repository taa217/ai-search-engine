import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  HStack,
  Text,
  Image,
  Flex,
  Link,
  Icon,
  Badge,
  useColorModeValue,
  Skeleton,
  LinkBox,
  LinkOverlay,
  AspectRatio,
  IconButton,
  Divider
} from '@chakra-ui/react';
import { ExternalLinkIcon, ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';
import { Source } from '../../context/SearchContext';
import { FaGlobe } from 'react-icons/fa';

const MotionBox = motion(Box);

interface ImageData {
  url: string;
  alt: string;
  thumbnail?: string;
  sourceUrl?: string;
  source?: string;
}

interface ResultPreviewProps {
  sources: Source[];
  images?: ImageData[];
  showImages?: boolean;
  showSources?: boolean;
}

interface ScrollableContentProps {
  children: React.ReactNode;
  scrollbarStyles: { [key: string]: any };
}

// Extract domain from URL
const getDomainFromUrl = (url: string): string => {
  try {
    const hostname = new URL(url).hostname;
    return hostname.replace('www.', '');
  } catch (e) {
    return url;
  }
};

const ScrollableContent: React.FC<ScrollableContentProps> = ({ children, scrollbarStyles }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  
  // Check if scrolling is possible
  const checkScrollable = () => {
    const container = scrollContainerRef.current;
    if (container) {
      const hasHorizontalScroll = container.scrollWidth > container.clientWidth;
      setShowRightArrow(hasHorizontalScroll && container.scrollLeft < container.scrollWidth - container.clientWidth);
      setShowLeftArrow(hasHorizontalScroll && container.scrollLeft > 0);
    }
  };
  
  // Initialize and check on content changes
  useEffect(() => {
    checkScrollable();
    window.addEventListener('resize', checkScrollable);
    return () => window.removeEventListener('resize', checkScrollable);
  }, [children]);
  
  // Handle scrolling left/right
  const scroll = (direction: 'left' | 'right') => {
    const container = scrollContainerRef.current;
    if (container) {
      const scrollAmount = 300; // px to scroll
      const newScrollLeft = direction === 'left' 
        ? container.scrollLeft - scrollAmount 
        : container.scrollLeft + scrollAmount;
      
      container.scrollTo({
        left: newScrollLeft,
        behavior: 'smooth'
      });
      
      // Update arrows after scrolling
      setTimeout(checkScrollable, 400);
    }
  };
  
  return (
    <Box position="relative">
      {/* Left scroll arrow */}
      {showLeftArrow && (
        <IconButton
          aria-label="Scroll left"
          icon={<ChevronLeftIcon />}
          size="sm"
          colorScheme="blackAlpha"
          variant="ghost"
          position="absolute"
          left={0}
          top="50%"
          transform="translateY(-50%)"
          zIndex={2}
          onClick={() => scroll('left')}
          opacity={0.8}
          _hover={{ opacity: 1 }}
        />
      )}
      
      {/* Right scroll arrow */}
      {showRightArrow && (
        <IconButton
          aria-label="Scroll right"
          icon={<ChevronRightIcon />}
          size="sm"
          colorScheme="blackAlpha"
          variant="ghost"
          position="absolute"
          right={0}
          top="50%"
          transform="translateY(-50%)"
          zIndex={2}
          onClick={() => scroll('right')}
          opacity={0.8}
          _hover={{ opacity: 1 }}
        />
      )}
      
      {/* Scrollable content */}
      <HStack
        ref={scrollContainerRef} 
        spacing={3} 
        py={2}
        px={2}
        overflowX="auto"
        css={scrollbarStyles}
        onScroll={checkScrollable}
      >
        {children}
      </HStack>
    </Box>
  );
};

// Source Card component for top section
const SourceCard: React.FC<{ source: Source }> = ({ source }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const domain = source.url ? getDomainFromUrl(source.url) : 'unknown';
  
  return (
    <LinkBox
      p={3}
      borderWidth="1px"
      borderRadius="md"
      borderColor={borderColor}
      bg={bgColor}
      boxShadow="sm"
      _hover={{ boxShadow: "md", transform: "translateY(-1px)" }}
      transition="all 0.2s"
      overflow="hidden"
      minW="220px"
      maxW="300px"
    >
      <Flex alignItems="center" mb={2}>
        <Icon as={FaGlobe} mr={2} color="gray.500" />
        <Text fontSize="sm" color="gray.500" fontWeight="medium">
          {domain}
        </Text>
      </Flex>
      <LinkOverlay href={source.url || '#'} isExternal>
        <Text fontWeight="medium" fontSize="sm" noOfLines={3}>
          {source.title}
        </Text>
      </LinkOverlay>
    </LinkBox>
  );
};

const ResultPreview: React.FC<ResultPreviewProps> = ({
  sources,
  images = [],
  showImages = true,
  showSources = true
}) => {
  // Colors for styling - all hooks must be at the top level
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const cardBgColor = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const accentColor = useColorModeValue('blue.500', 'blue.300');
  const scrollThumbColor = useColorModeValue('rgba(0,0,0,0.1)', 'rgba(255,255,255,0.1)');
  
  // Filter sources that have images (for backward compatibility)
  const imageSources = sources?.filter(source => source.imageUrl) || [];
  const topSources = sources?.slice(0, 5) || [];
  const hasSources = sources && sources.length > 0;
  
  // Combine image sources with passed images, limiting to first 5 for preview
  const previewImages = [
    ...images,
    ...imageSources.map(source => ({
      url: source.imageUrl || '',
      alt: source.title || 'Image preview',
      thumbnail: '', // Ensure thumbnail property exists for type safety
      sourceUrl: source.url || '',
      source: source.source || getDomainFromUrl(source.url || '')
    }))
  ].slice(0, 5);
  
  const hasImages = previewImages.length > 0;
  
  // Shared scrollbar styles
  const scrollbarStyles = {
    '&::-webkit-scrollbar': { height: '6px' },
    '&::-webkit-scrollbar-track': { background: 'transparent' },
    '&::-webkit-scrollbar-thumb': { 
      background: scrollThumbColor,
      borderRadius: '8px'
    },
  };
  
  // Don't render if there's nothing to show
  if ((!showImages && !showSources) || 
      (showImages && previewImages.length === 0) && 
      (showSources && topSources.length === 0)) {
    return null;
  }

  return (
    <MotionBox
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      mb={4}
      overflow="hidden"
    >
      {/* Source Cards Section */}
      {showSources && hasSources && (
        <Box mb={hasSources && showImages ? 3 : 0}>
          <ScrollableContent scrollbarStyles={scrollbarStyles}>
            {topSources.map((source, index) => (
              <SourceCard key={`source-card-${index}`} source={source} />
            ))}
            
            {/* "More sources" indicator if we have more than what's shown */}
            {sources.length > 5 && (
              <Box
                p={3}
                borderWidth="1px"
                borderStyle="dashed"
                borderRadius="md"
                borderColor="gray.200"
                bg={bgColor}
                display="flex"
                alignItems="center"
                justifyContent="center"
                minW="100px"
                h="80px"
              >
                <Text fontWeight="medium" color="blue.500">+{sources.length - 5} sources</Text>
              </Box>
            )}
          </ScrollableContent>
        </Box>
      )}

      {/* Divider between sources and images */}
      {hasSources && showImages && imageSources.length > 0 && (
        <Divider mb={3} />
      )}

      {/* Images Section */}
      {showImages && hasImages && (
        <ScrollableContent scrollbarStyles={scrollbarStyles}>
          {/* Show preview images */}
          {previewImages.map((image, index) => (
            <LinkBox 
              key={`img-${index}`} 
              borderRadius="md" 
              overflow="hidden"
              boxShadow="sm"
              bg={cardBgColor}
              borderWidth="1px"
              borderColor={borderColor}
              transition="all 0.2s"
              _hover={{ 
                transform: "translateY(-2px)",
                boxShadow: "md",
                borderColor: accentColor
              }}
              flex="0 0 auto"
              width="160px" 
              height="120px"
              position="relative"
            >
              <AspectRatio ratio={4/3} height="full">
                <Box position="relative" width="100%" height="100%">
                  <Box
                    position="absolute"
                    top={0}
                    left={0}
                    width="100%"
                    height="100%"
                    backgroundImage={`url(${image.url || image.thumbnail || ''})`}
                    backgroundSize="cover"
                    backgroundPosition="center"
                  />
                  <Image
                    src={image.url || image.thumbnail || ''}
                    alt={image.alt || 'Image preview'}
                    objectFit="cover"
                    width="100%"
                    height="100%"
                    position="relative"
                    opacity="0.9"
                    fallbackSrc="https://via.placeholder.com/300x200?text=Image"
                    onError={({ currentTarget }) => {
                      // If image fails, try thumbnail
                      if (image.thumbnail && currentTarget.src !== image.thumbnail) {
                        currentTarget.src = image.thumbnail;
                      } else {
                        // If thumbnail fails too, use placeholder
                        currentTarget.src = "https://via.placeholder.com/300x200?text=Image";
                      }
                    }}
                  />
                </Box>
              </AspectRatio>
              <Box
                position="absolute"
                bottom="0"
                left="0"
                right="0"
                bg="rgba(0,0,0,0.6)"
                p={1}
                color="white"
              >
                <LinkOverlay href={image.sourceUrl || '#'} isExternal>
                  <Text fontSize="xs" fontWeight="medium" noOfLines={1}>
                    {image.source || 'Source'}
                  </Text>
                </LinkOverlay>
              </Box>
            </LinkBox>
          ))}
          
          {/* Add non-image sources if needed */}
          {topSources.filter(s => !s.imageUrl).map((source, index) => (
            <LinkBox 
              key={`src-${index}`}
              borderRadius="md" 
              p={2}
              boxShadow="sm"
              bg={cardBgColor}
              borderWidth="1px"
              borderColor={borderColor}
              flex="0 0 auto"
              width="160px"
              height="120px"
              transition="all 0.2s"
              _hover={{ 
                transform: "translateY(-2px)",
                boxShadow: "md",
                borderColor: accentColor
              }}
              display="flex"
              flexDirection="column"
            >
              <Badge colorScheme="gray" fontSize="xs" alignSelf="flex-start" mb={1}>
                Source
              </Badge>
              <LinkOverlay href={source.url} isExternal>
                <Text fontSize="xs" fontWeight="semibold" noOfLines={2} mb={1}>
                  {source.title}
                </Text>
              </LinkOverlay>
              <Text fontSize="10px" color="gray.600" noOfLines={3} flex="1">
                {source.snippet}
              </Text>
              <Flex justify="flex-end" align="center" mt="auto">
                <Icon as={ExternalLinkIcon} boxSize={3} color="gray.500" />
              </Flex>
            </LinkBox>
          ))}
          
          {/* "More sources" indicator if we have more than what's shown */}
          {sources.length > 5 && !hasSources && (
            <Box
              borderRadius="md"
              p={2}
              bg={bgColor}
              borderWidth="1px"
              borderStyle="dashed"
              borderColor={borderColor}
              flex="0 0 auto"
              width="100px"
              height="120px"
              display="flex"
              flexDirection="column"
              justifyContent="center"
              alignItems="center"
              textAlign="center"
              color="gray.500"
            >
              <Text fontSize="sm" fontWeight="medium">
                +{sources.length - 5}
              </Text>
              <Text fontSize="xs">
                more sources
              </Text>
            </Box>
          )}
        </ScrollableContent>
      )}
    </MotionBox>
  );
};

export default ResultPreview; 