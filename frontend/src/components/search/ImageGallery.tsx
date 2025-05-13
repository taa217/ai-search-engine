import React, { useState } from 'react';
import {
  Box,
  SimpleGrid,
  Text,
  Image,
  useColorModeValue,
  LinkBox,
  LinkOverlay,
  AspectRatio,
  Skeleton,
  Flex,
  Badge,
  Icon,
  Heading,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  IconButton,
  Link
} from '@chakra-ui/react';
import { ExternalLinkIcon, ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { FaCamera, FaExpand, FaGlobe } from 'react-icons/fa';
import { motion } from 'framer-motion';

const MotionBox = motion(Box);
const MotionFlex = motion(Flex);

interface ImageData {
  url: string;
  alt: string;
  thumbnail?: string; // Add thumbnail for smaller version
  sourceUrl?: string | null;
  source?: string; // Keep for backward compatibility
}

interface ImageGalleryProps {
  images: ImageData[];
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

// Ensure a URL is valid
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

// Simplified image card that ensures images display properly
const ImageCard = ({ image, index, onClick }: { image: ImageData; index: number; onClick: () => void }) => {
  const [isHovered, setIsHovered] = useState(false);
  const cardBg = useColorModeValue('white', 'gray.800');
  const overlayBg = useColorModeValue('rgba(0, 0, 0, 0.7)', 'rgba(0, 0, 0, 0.8)');
  const sourceBadgeBg = useColorModeValue('blue.50', 'blue.900');
  const sourceBadgeColor = useColorModeValue('blue.600', 'blue.200');
  
  // Use sourceUrl if available, otherwise fall back to source
  const sourceLink = image.sourceUrl || image.source;
  const domain = sourceLink ? getDomainFromUrl(ensureValidUrl(sourceLink)) : '';
  
  const isFeatured = index === 0;

  return (
    <Box
      position="relative"
      borderRadius="md"
      overflow="hidden"
      boxShadow="sm"
      height={isFeatured ? "300px" : "200px"}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      transition="all 0.2s"
      _hover={{ boxShadow: "md", transform: "translateY(-2px)" }}
      onClick={onClick}
      cursor="pointer"
    >
      {/* Source badge */}
      {domain && (
        <Badge
          position="absolute"
          top={2}
          right={2}
          bg={sourceBadgeBg}
          color={sourceBadgeColor}
          fontSize="xs"
          borderRadius="md"
          px={2}
          py={0.5}
          zIndex={2}
        >
          {domain}
        </Badge>
      )}
      
      {/* Featured badge */}
      {isFeatured && (
        <Badge
          position="absolute"
          top={2}
          left={2}
          colorScheme="purple"
          fontSize="xs"
          px={2}
          py={1}
          zIndex={2}
        >
          Featured
        </Badge>
      )}
      
      {/* Image with background fallback to handle CORS issues */}
      <Box
        position="relative"
        width="100%"
        height="100%"
        backgroundImage={`url(${image.url || image.thumbnail})`}
        backgroundSize="cover"
        backgroundPosition="center"
        backgroundRepeat="no-repeat"
        _before={{
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'blackAlpha.100', // Slight tint to improve visibility
        }}
      >
        <Image
          src={image.url || image.thumbnail}
          alt={image.alt}
          objectFit="cover"
          fallbackSrc="https://via.placeholder.com/600x400?text=Image"
          width="100%"
          height="100%"
          opacity="0.9" // Make slightly transparent for better visibility
          position="absolute"
          top="0"
          left="0"
          onError={({ currentTarget }) => {
            // If main image fails, try thumbnail
            if (image.thumbnail && currentTarget.src !== image.thumbnail) {
              currentTarget.src = image.thumbnail;
            } else {
              // If thumbnail fails too, use placeholder
              currentTarget.src = "https://via.placeholder.com/600x400?text=Image";
            }
          }}
        />
      </Box>
      
      {/* Hover overlay */}
      <Box
        position="absolute"
        bottom={0}
        left={0}
        right={0}
        bg={overlayBg}
        color="white"
        p={3}
        opacity={isHovered ? 1 : 0}
        transform={`translateY(${isHovered ? 0 : '10px'})`}
        transition="all 0.2s"
      >
        <Flex justify="space-between" align="center">
          <Text fontWeight="medium" fontSize="sm" noOfLines={1}>
            {image.alt}
          </Text>
          {sourceLink && (
            <Flex>
              <Tooltip label="View source" placement="top">
                <Box 
                  as="a" 
                  href={ensureValidUrl(sourceLink)} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                >
                  <Icon 
                    as={ExternalLinkIcon} 
                    boxSize={4} 
                    ml={2} 
                    cursor="pointer" 
                  />
                </Box>
              </Tooltip>
            </Flex>
          )}
        </Flex>
      </Box>
    </Box>
  );
};

const ImageGallery: React.FC<ImageGalleryProps> = ({ images }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const handleImageClick = (index: number) => {
    setSelectedImageIndex(index);
    onOpen();
  };

  const navigateImage = (direction: 'next' | 'prev') => {
    if (direction === 'next') {
      setSelectedImageIndex((prevIndex) => 
        prevIndex === images.length - 1 ? 0 : prevIndex + 1
      );
    } else {
      setSelectedImageIndex((prevIndex) => 
        prevIndex === 0 ? images.length - 1 : prevIndex - 1
      );
    }
  };

  // Filter out any invalid image URLs
  const validImages = images.filter(img => img.url && img.url.trim() !== '');

  if (!validImages || validImages.length === 0) {
    return null;
  }

  return (
    <>
      <Box
        w="100%"
        p={4}
        borderRadius="lg"
        bg="transparent"
      >
        <Flex align="center" mb={4}>
          <Icon as={FaCamera} color="blue.500" mr={2} />
          <Heading as="h3" size="md">Images</Heading>
          <Badge ml={2} colorScheme="blue" borderRadius="full">
            {validImages.length}
          </Badge>
        </Flex>
        
        <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={4}>
          {validImages.map((image, index) => (
            <ImageCard 
              key={index} 
              image={image} 
              index={index} 
              onClick={() => handleImageClick(index)}
            />
          ))}
        </SimpleGrid>
      </Box>

      {/* Modal for enlarged image view */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
        <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(10px)" />
        <ModalContent bg={bgColor} borderRadius="md" overflow="hidden" maxW="90vw">
          <ModalCloseButton zIndex={10} size="lg" />
          <ModalBody p={0} position="relative">
            <AspectRatio ratio={16/9} maxH="80vh">
              <Image
                src={validImages[selectedImageIndex]?.url}
                alt={validImages[selectedImageIndex]?.alt || 'Image'}
                objectFit="contain"
                width="100%"
                height="100%"
                fallbackSrc="https://via.placeholder.com/600x400?text=Image"
              />
            </AspectRatio>
            
            {/* Left/Right Navigation */}
            {validImages.length > 1 && (
              <>
                <IconButton
                  aria-label="Previous image"
                  icon={<ChevronLeftIcon boxSize={8} />}
                  position="absolute"
                  left={2}
                  top="50%"
                  transform="translateY(-50%)"
                  variant="ghost"
                  colorScheme="blackAlpha"
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    navigateImage('prev');
                  }}
                  borderRadius="full"
                  size="lg"
                  opacity={0.7}
                  _hover={{ opacity: 1, bg: 'blackAlpha.300' }}
                />
                
                <IconButton
                  aria-label="Next image"
                  icon={<ChevronRightIcon boxSize={8} />}
                  position="absolute"
                  right={2}
                  top="50%"
                  transform="translateY(-50%)"
                  variant="ghost"
                  colorScheme="blackAlpha"
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    navigateImage('next');
                  }}
                  borderRadius="full"
                  size="lg"
                  opacity={0.7}
                  _hover={{ opacity: 1, bg: 'blackAlpha.300' }}
                />
              </>
            )}

            {/* Source link at bottom */}
            {(validImages[selectedImageIndex]?.sourceUrl || validImages[selectedImageIndex]?.source) && (
              <Flex 
                position="absolute" 
                bottom={0} 
                left={0} 
                right={0} 
                bg="blackAlpha.700" 
                p={2} 
                justifyContent="flex-end"
              >
                <Link 
                  href={ensureValidUrl(validImages[selectedImageIndex].sourceUrl || validImages[selectedImageIndex].source || '#')} 
                  isExternal 
                  color="white"
                  fontSize="sm"
                  fontWeight="medium"
                  _hover={{ color: 'blue.200' }}
                >
                  View Source <ExternalLinkIcon mx={1} />
                </Link>
              </Flex>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default ImageGallery;
