import React from 'react';
import {
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Box,
  Icon,
  Text,
  VStack,
  HStack,
  Image,
  Link,
  Skeleton,
  useColorModeValue,
  Badge,
  Divider
} from '@chakra-ui/react';
import { FiFileText, FiImage } from 'react-icons/fi';
import { SearchSource } from 'types/search';

interface SidePanelProps {
  sources: SearchSource[];
}

const SourceCard = ({ source }: { source: SearchSource }) => (
  <VStack
    align="stretch"
    p={3}
    spacing={2}
    borderRadius="md"
    _hover={{ bg: 'gray.50' }}
    transition="background 0.2s"
  >
    <HStack justify="space-between">
      <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
        {source.title}
      </Text>
      <Badge colorScheme="blue" fontSize="xs">
        {source.type}
      </Badge>
    </HStack>
    <Link
      href={source.url}
      fontSize="xs"
      color="blue.600"
      isExternal
      noOfLines={1}
    >
      {source.url}
    </Link>
    <Text fontSize="xs" color="gray.600" noOfLines={2}>
      {source.content}
    </Text>
  </VStack>
);

const ImageGalleryPanel = ({ sources }: { sources: SearchSource[] }) => (
  <Box
    display="grid"
    gridTemplateColumns="repeat(auto-fit, minmax(150px, 1fr))"
    gap={3}
    p={2}
  >
    {sources.slice(0, 6).map((source, index) => (
      <Box
        key={index}
        borderRadius="md"
        overflow="hidden"
        position="relative"
        pb="100%"
      >
        <Image
          src={`https://via.placeholder.com/300x200?text=${source.title}`}
          alt={source.title}
          position="absolute"
          objectFit="cover"
          w="100%"
          h="100%"
        />
      </Box>
    ))}
  </Box>
);

const SidePanel = ({ sources }: SidePanelProps) => {
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  return (
    <Tabs variant="enclosed-colored" isFitted defaultIndex={0}>
      <TabList>
        <Tab _focus={{ boxShadow: 'none' }} px={1}>
          <Icon as={FiFileText} mr={2} />
          <Text fontSize="sm">Sources</Text>
        </Tab>
        <Tab _focus={{ boxShadow: 'none' }} px={1}>
          <Icon as={FiImage} mr={2} />
          <Text fontSize="sm">Media</Text>
        </Tab>
      </TabList>

      <TabPanels
        borderRightWidth="1px"
        borderBottomWidth="1px"
        borderLeftWidth="1px"
        borderColor={borderColor}
        borderRadius="md"
      >
        {/* Sources Tab */}
        <TabPanel p={0}>
          <Box maxH="calc(100vh - 240px)" overflowY="auto">
            <VStack spacing={0} divider={<Divider />}>
              {sources?.map((source, index) => (
                <SourceCard key={index} source={source} />
              ))}
            </VStack>
          </Box>
        </TabPanel>

        {/* Images Tab */}
        <TabPanel p={2}>
          <ImageGalleryPanel sources={sources} />
        </TabPanel>
      </TabPanels>
    </Tabs>
  );
};



export default SidePanel;