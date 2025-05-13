import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Text,
  Tooltip,
  IconButton,
  useClipboard,
  Badge,
  Link,
  HStack,
  useColorModeValue,
  Flex,
  VStack,
  Button,
  Divider,
  LinkBox,
  LinkOverlay,
  Image,
  Grid,
  GridItem
} from '@chakra-ui/react';
import { CopyIcon, CheckIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { SearchResult as SearchResultType, Source, ImageResult } from '../../context/SearchContext';
import DOMPurify from 'isomorphic-dompurify';
import Markdown from 'markdown-to-jsx';
import ImageGallery from './ImageGallery';

interface SearchResultProps {
  query: string;
  result: SearchResultType;
  sources?: Source[];
  images?: string[];
  onFeedback?: (feedback: 'positive' | 'negative') => void;
}

// Updated Source interface to include the link property that may come from the API
interface EnhancedSource extends Source {
  link?: string;
  imageUrl?: string;
}

// Helper to create regex for finding citation patterns like [1] or [1][2][3]
const createCitationRegex = () => {
  return /\[(\d+)\]/g;
};

// Helper to extract domain from URL for display
const getDomainFromUrl = (url: string): string => {
  try {
    const hostname = new URL(url).hostname;
    return hostname.replace('www.', '');
  } catch (e) {
    return url;
  }
};

const extractNumberFromCitation = (citation: string): number | null => {
  const match = citation.match(/\[(\d+)\]/);
  return match ? parseInt(match[1], 10) : null;
};

const ensureValidUrl = (url: string | undefined): string => {
  if (!url) return '#';
  
  try {
    new URL(url);
    return url;
  } catch (e) {
    // If it's not a valid URL, try to fix it by adding https://
    if (!url.startsWith('http')) {
      return `https://${url}`;
    }
    return url;
  }
};

const SearchResult: React.FC<SearchResultProps> = ({ query, result, sources = [], images, onFeedback }) => {
  const { hasCopied, onCopy } = useClipboard(result?.content || '');
  const [hoveredCitation, setHoveredCitation] = useState<number | null>(null);
  const [processedContent, setProcessedContent] = useState<string>(result?.content || '');
  const resultRef = useRef<HTMLDivElement>(null);
  
  // Cast sources to enhanced type that includes link and imageUrl properties
  const enhancedSources = sources as EnhancedSource[];
  
  // Color tokens - moved all useColorModeValue calls outside of conditional renders
  const textColor = useColorModeValue('gray.800', 'gray.100');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const paragraphBg = useColorModeValue('white', 'gray.800');
  const citationBg = useColorModeValue('blue.50', 'blue.900');
  const citationColor = useColorModeValue('blue.600', 'blue.200');
  const citationHoverBg = useColorModeValue('blue.100', 'blue.800');
  const tooltipBg = useColorModeValue('white', 'gray.700');
  const tooltipBorder = useColorModeValue('gray.200', 'gray.600');
  const bgColor = useColorModeValue('white', 'gray.800');
  
  // Additional color values for citation links in markdown
  const citationLinkBg = useColorModeValue('blue.50', 'blue.900');
  const citationLinkHoverBg = useColorModeValue('blue.100', 'blue.800');
  const citationLinkHoverColor = useColorModeValue('blue.700', 'blue.300');

  // Process citations and convert them to clickable links
  useEffect(() => {
    if (!result?.content) return;

    // Process the text to convert markdown to HTML and handle citations
    let content = result.content;

    // Replace citations [1], [2], etc. with clickable links
    content = content.replace(/\[(\d+)\]/g, (match, num) => {
      const sourceIndex = parseInt(num, 10) - 1;
      if (enhancedSources && enhancedSources[sourceIndex]) {
        const sourceUrl = enhancedSources[sourceIndex].url || enhancedSources[sourceIndex].link;
        if (sourceUrl) {
          return `<a href="${ensureValidUrl(sourceUrl)}" target="_blank" rel="noopener noreferrer" 
                    class="citation-link">${match}</a>`;
        }
      }
      return match;
    });

    // Set the processed content
    setProcessedContent(content);
  }, [result?.content, enhancedSources]);

  // Extract images from sources if they exist
  const sourceImages = enhancedSources
    ? enhancedSources
        .filter(source => source.imageUrl)
        .map(source => ({
          url: source.imageUrl || '',
          sourceUrl: ensureValidUrl(source.url || source.link || ''),
          alt: source.title || 'Image from search result'
        }))
    : [];

  // Combine provided images and source images
  const allImages = [
    ...(images || []).map(img => ({ url: img, sourceUrl: null, alt: 'Search result image' })),
    ...sourceImages
  ];

  const renderFormattedTextWithCitations = (text: string) => {
    if (!text) return null;
    
    // Split the text by paragraphs
    const paragraphs = text.split('\n\n');
    
    return paragraphs.map((paragraph, pIdx) => {
      // Check if the paragraph contains citations
      if (paragraph.includes('[') && paragraph.includes(']')) {
        // Split by citation pattern
        const segments = paragraph.split(/(\[\d+\])/g);
        
        return (
          <Box 
            key={pIdx} 
            p={4} 
            bg={paragraphBg} 
            borderRadius="md" 
            mb={4} 
            boxShadow="sm"
          >
            <Text
              fontSize={{ base: "lg", md: "xl" }}
              lineHeight="tall"
              color={textColor}
            >
              {segments.map((segment, sIdx) => {
                // Check if this segment is a citation
                if (/\[\d+\]/.test(segment)) {
                  const citationNumber = parseInt(segment.replace(/\[|\]/g, ''), 10);
                  const sourceIndex = citationNumber - 1;
                  
                  return (
                    <Link
                      key={sIdx}
                      href={enhancedSources[sourceIndex]?.url ? ensureValidUrl(enhancedSources[sourceIndex]?.url) : '#'}
                      isExternal
                      position="relative"
                      as="span"
                      px={1}
                      py={0.5}
                      mx={0.5}
                      borderRadius="md"
                      bg={citationBg}
                      color={citationColor}
                      fontWeight="medium"
                      fontSize="sm"
                      _hover={{ bg: citationHoverBg }}
                      onMouseEnter={() => setHoveredCitation(citationNumber)}
                      onMouseLeave={() => setHoveredCitation(null)}
                    >
                      {segment}
                    </Link>
                  );
                }
                
                // Regular text
                return <React.Fragment key={sIdx}>{segment}</React.Fragment>;
              })}
            </Text>
          </Box>
        );
      }
      
      // Regular paragraph without citations
      return (
        <Box 
          key={pIdx} 
          p={4} 
          bg={paragraphBg} 
          borderRadius="md" 
          mb={4}
          boxShadow="sm"
        >
          <Text
            fontSize={{ base: "lg", md: "xl" }}
            lineHeight="tall"
            color={textColor}
          >
            {paragraph}
          </Text>
        </Box>
      );
    });
  };

  if (!result?.content) return null;

  return (
    <Box 
      width="100%"
      position="relative"
      bg={bgColor}
      borderRadius="lg"
      overflow="hidden"
      boxShadow="sm"
      mb={6}
    >
      <Box p={5} ref={resultRef}>
        {/* Main content section */}
        <Box 
          className="search-result-content"
          fontSize="md"
          lineHeight="tall"
          color={textColor}
          sx={{
            // Style citations
            'a.citation-link': {
              color: 'blue.500',
              fontWeight: 'medium',
              fontSize: 'sm',
              padding: '0.1rem 0.3rem',
              borderRadius: '0.25rem',
              bg: citationLinkBg,
              textDecoration: 'none',
              whiteSpace: 'nowrap',
              verticalAlign: 'text-top',
              transition: 'all 0.2s',
              _hover: {
                bg: citationLinkHoverBg,
                color: citationLinkHoverColor,
              }
            },
            'p': {
              mb: 4
            },
            'ul, ol': {
              paddingLeft: 5,
              mb: 4
            },
            'li': {
              mb: 1
            }
          }}
        >
          {/* Custom renderer for Markdown content */}
          <Markdown
            options={{
              overrides: {
                a: {
                  component: ({ children, ...props }: any) => {
                    // Check if this is a citation link
                    const isCitation = props.className === 'citation-link';
                    if (isCitation) {
                      const sourceIndex = extractNumberFromCitation(children[0] as string);
                      if (sourceIndex !== null && enhancedSources && enhancedSources[sourceIndex - 1]) {
                        const source = enhancedSources[sourceIndex - 1];
                        const url = ensureValidUrl(source.url || source.link || '');
                        return (
                          <Link
                            href={url}
                            isExternal
                            className="citation-link"
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                            {...props}
                          >
                            {children}
                          </Link>
                        );
                      }
                    }
                    
                    // Regular links
                    return (
                      <Link isExternal {...props}>
                        {children}
                      </Link>
                    );
                  }
                }
              }
            }}
          >
            {DOMPurify.sanitize(processedContent)}
          </Markdown>
        </Box>

        {/* Copy button */}
        <HStack spacing={2} mt={4} justifyContent="flex-end">
          <Button
            size="sm"
            leftIcon={hasCopied ? <CheckIcon /> : <CopyIcon />}
            onClick={onCopy}
            colorScheme={hasCopied ? "green" : "gray"}
            variant="outline"
          >
            {hasCopied ? "Copied" : "Copy"}
          </Button>
        </HStack>

        {/* Feedback Section */}
        {onFeedback && (
          <Flex justifyContent="flex-end" mt={4} pt={4} borderTopWidth="1px" borderColor={borderColor}>
            <Text fontSize="sm" color="gray.500" mr={2}>
              Was this helpful?
            </Text>
            <Button 
              size="xs" 
              colorScheme="green" 
              variant="outline" 
              mr={2}
              onClick={() => onFeedback('positive')}
            >
              Yes
            </Button>
            <Button 
              size="xs" 
              colorScheme="red" 
              variant="outline"
              onClick={() => onFeedback('negative')}
            >
              No
            </Button>
          </Flex>
        )}
      </Box>
    </Box>
  );
};

export default SearchResult;
