import React, { useState } from 'react';
import {
  Box,
  Heading,
  VStack,
  HStack,
  Link,
  Text,
  Icon,
  Badge,
  Divider,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Flex,
  Spacer,
  Image,
  AspectRatio,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '@chakra-ui/react';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import { FaGlobe, FaImage } from 'react-icons/fa';
import { Source } from '../../context/SearchContext';

interface SourcesPanelProps {
  sources: Source[];
  isCompact?: boolean;
}

// Helper to extract domain from URL for display
const getDomainFromUrl = (url: string): string => {
  try {
    const hostname = new URL(url).hostname;
    return hostname.replace('www.', '');
  } catch (e) {
    return url;
  }
};

// Helper to ensure we have a valid URL
const ensureValidUrl = (url: string): string => {
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

// Hard-coded image URLs for domains (used if other methods fail)
const DOMAIN_IMAGES: Record<string, string> = {
  'youtube.com': 'https://yt3.googleusercontent.com/584JjRp5QMuKbyduM_2k5RlXFqHJtQ0qLIPZpwbUjMJmgzZngHcam5JMuZQxyzGMV5ljwJRl0Q=s900-c-k-c0x00ffffff-no-rj',
  'en.wikipedia.org': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png',
  'imdb.com': 'https://m.media-amazon.com/images/G/01/IMDb/BG_rectangle._CB1509060989_SY230_SX307_AL_.png',
  'amazon.com': 'https://m.media-amazon.com/images/G/01/gc/designs/livepreview/a_generic_white_10_us_noto_email_v2016_us-main._CB627448186_.png'
};

// Default images by index to ensure every source has an image
const DEFAULT_IMAGES = [
  'https://images.unsplash.com/photo-1495020689067-958852a7765e?ixlib=rb-4.0.3',
  'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?ixlib=rb-4.0.3',
  'https://images.unsplash.com/photo-1477013743164-ffc3a5e556da?ixlib=rb-4.0.3',
  'https://images.unsplash.com/photo-1616530940355-351fabd9524b?ixlib=rb-4.0.3',
  'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?ixlib=rb-4.0.3'
];

const SourcesPanel: React.FC<SourcesPanelProps> = ({ sources, isCompact = false }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedTitle, setSelectedTitle] = useState<string>('');
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const linkColor = useColorModeValue('blue.600', 'blue.300');
  const textColor = useColorModeValue('gray.700', 'gray.300');
  const secondaryTextColor = useColorModeValue('gray.500', 'gray.400');
  const badgeBgColor = useColorModeValue('blue.50', 'blue.900');
  const badgeColor = useColorModeValue('blue.600', 'blue.200');
  const imageBgColor = useColorModeValue('gray.100', 'gray.700');
  
  // Get image URL for a given source
  const getSourceImageUrl = (source: Source, index: number): string => {
    // 1. Try source's own image URL if it exists and is valid
    if (source.imageUrl && source.imageUrl.startsWith('http')) {
      return source.imageUrl;
    }
    
    // 2. Try to match by domain
    const sourceUrl = source.url || (source as any).link || '';
    const domain = getDomainFromUrl(ensureValidUrl(sourceUrl));
    
    // Check if we have a pre-defined image for this domain
    for (const [domainKey, imageUrl] of Object.entries(DOMAIN_IMAGES)) {
      if (domain.includes(domainKey)) {
        return imageUrl;
      }
    }
    
    // 3. Use default image by index (cycling through the options)
    return DEFAULT_IMAGES[index % DEFAULT_IMAGES.length];
  };
  
  const handleImageClick = (imageUrl: string, title: string) => {
    setSelectedImage(imageUrl);
    setSelectedTitle(title);
    onOpen();
  };

  if (!sources || sources.length === 0) {
    return null;
  }

  if (isCompact) {
    return (
      <Box 
        w="100%" 
        p={4} 
        borderRadius="lg" 
        bg="transparent"
      >
        <Accordion allowToggle>
          <AccordionItem border="none">
            <AccordionButton px={0}>
              <Box flex="1" textAlign="left">
                <Heading as="h3" size="sm" fontWeight="semibold">
                  Sources ({sources.length})
                </Heading>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4} px={0}>
              <VStack align="stretch" spacing={3} mt={2}>
                {sources.map((source, index) => {
                  // Ensure linkUrl is always a string
                  const linkUrl = source.url || (source as any).link || '#';
                  
                  return (
                    <HStack key={index} spacing={3} align="start">
                      <Badge colorScheme="blue" mt={1}>{index + 1}</Badge>
                      <Box>
                        <Link href={ensureValidUrl(linkUrl)} isExternal color="blue.600" fontWeight="medium">
                          {source.title} <Icon as={ExternalLinkIcon} mx="2px" />
                        </Link>
                      </Box>
                    </HStack>
                  );
                })}
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
      </Box>
    );
  }

  // Full sources display
  return (
    <>
      <VStack 
        w="100%" 
        spacing={0} 
        align="stretch"
        divider={<Divider borderColor={borderColor} />}
        borderRadius="lg"
        overflow="hidden"
        bg="transparent"
      >
        {/* Header */}
        <Flex 
          px={5} 
          py={4} 
          borderBottomWidth="1px" 
          borderColor={borderColor}
          alignItems="center"
        >
          <Box as="span" color={textColor} fontWeight="semibold" fontSize="md">
            Sources
          </Box>
          <Spacer />
          <Badge 
            colorScheme="blue" 
            fontSize="xs" 
            px={2} 
            py={0.5} 
            borderRadius="full"
          >
            {sources.length}
          </Badge>
        </Flex>

        {/* Sources list */}
        <Box>
          {sources.map((source, index) => {
            // Ensure linkUrl is always a string
            const linkUrl = source.url || (source as any).link || '#';
            const domain = getDomainFromUrl(ensureValidUrl(linkUrl));
            const imageUrl = getSourceImageUrl(source, index);
            
            return (
              <Box 
                key={index} 
                py={4} 
                px={5}
                borderBottomWidth={index < sources.length - 1 ? "1px" : "0"}
                borderColor={borderColor}
                borderBottomStyle="dashed"
                transition="background 0.2s"
                _hover={{ bg: 'rgba(0,0,0,0.02)' }}
                mb={1}
              >
                <Flex direction={{ base: "column", sm: "row" }} alignItems="flex-start">
                  {/* Image section */}
                  <Box 
                    mr={4} 
                    mb={{ base: 3, sm: 0 }}
                    width={{ base: "100%", sm: "120px" }} 
                    height={{ base: "auto", sm: "90px" }}
                    flexShrink={0}
                    borderRadius="md"
                    overflow="hidden"
                    borderWidth="1px"
                    borderColor={borderColor}
                    bg={imageBgColor}
                    cursor="pointer"
                    onClick={() => handleImageClick(imageUrl, source.title)}
                    position="relative"
                  >
                    <AspectRatio ratio={4/3} w="100%" h="100%">
                      <Box position="relative">
                        {/* Domain badge overlay */}
                        <Badge
                          position="absolute"
                          top={1}
                          right={1}
                          bg="blackAlpha.700"
                          color="white"
                          fontSize="xs"
                          borderRadius="sm"
                          px={1}
                          py={0.5}
                          zIndex={2}
                        >
                          {domain}
                        </Badge>
                        
                        {/* Actual image */}
                        <Image
                          src={imageUrl}
                          alt={source.title}
                          objectFit="cover"
                          width="100%"
                          height="100%"
                          fallbackSrc={`https://dummyimage.com/300x200/4a5568/ffffff&text=${domain}`}
                        />
                      </Box>
                    </AspectRatio>
                  </Box>
                  
                  {/* Content section */}
                  <Box flex="1">
                    {/* Number and domain */}
                    <Flex alignItems="center" mb={2}>
                      <Badge 
                        bg={badgeBgColor} 
                        color={badgeColor} 
                        fontSize="sm" 
                        fontWeight="bold" 
                        borderRadius="md" 
                        px={2}
                        py={0.5}
                        mr={2}
                      >
                        {index + 1}
                      </Badge>
                      
                      <Icon as={FaGlobe} color={secondaryTextColor} boxSize="12px" mr={1} />
                      <Text fontSize="xs" color={secondaryTextColor} fontWeight="medium">
                        {domain}
                      </Text>
                      
                      {source.isRelevant && (
                        <Badge 
                          ml="auto" 
                          colorScheme="green" 
                          fontSize="xs"
                          variant="subtle"
                        >
                          Top Match
                        </Badge>
                      )}
                    </Flex>
                    
                    {/* Title */}
                    <Link 
                      href={ensureValidUrl(linkUrl)} 
                      isExternal 
                      color={linkColor} 
                      fontWeight="semibold"
                      fontSize="md"
                      display="block"
                      mb={1.5}
                      _hover={{ textDecoration: "underline" }}
                    >
                      {source.title}
                      <Icon as={ExternalLinkIcon} ml={1} boxSize="14px" verticalAlign="text-bottom" />
                    </Link>
                    
                    {/* URL - simplified and grayed out */}
                    <Text fontSize="xs" color={secondaryTextColor} mb={2} noOfLines={1}>
                      {linkUrl}
                    </Text>
                    
                    {/* Snippet/description */}
                    <Text fontSize="sm" color={textColor} lineHeight="tall">
                      {source.snippet}
                    </Text>
                  </Box>
                </Flex>
              </Box>
            );
          })}
        </Box>
      </VStack>
      
      {/* Image Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg" isCentered>
        <ModalOverlay backdropFilter="blur(5px)" />
        <ModalContent bg={bgColor} borderRadius="md" overflow="hidden">
          <ModalCloseButton zIndex={10} />
          <ModalBody p={0}>
            <Box position="relative">
              <AspectRatio ratio={16/9} maxH="80vh">
                <Image
                  src={selectedImage || ''}
                  alt={selectedTitle}
                  objectFit="contain"
                  width="100%"
                  height="100%"
                  fallbackSrc={`https://dummyimage.com/800x450/4a5568/ffffff&text=${encodeURIComponent(selectedTitle || 'Image')}`}
                />
              </AspectRatio>
              
              {/* Caption */}
              <Box
                position="absolute"
                bottom={0}
                left={0}
                right={0}
                bg="blackAlpha.700"
                color="white"
                p={3}
              >
                <Text fontWeight="medium">{selectedTitle}</Text>
              </Box>
            </Box>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default SourcesPanel;
