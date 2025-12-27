// Home component - Main page containing search functionality
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, VStack, Tabs, TabList, Tab, TabPanels, TabPanel, Text, Skeleton, Container, useBreakpointValue, Flex, Badge, HStack, Heading, Button, useColorModeValue, Icon, IconButton, ButtonGroup } from '@chakra-ui/react';
import { SearchIcon, InfoIcon, AddIcon, RepeatIcon } from '@chakra-ui/icons';
import { FiMessageCircle, FiBriefcase, FiSearch, FiCpu } from 'react-icons/fi';
import { useSearchContext } from 'context/SearchContext';
import SearchInput from 'components/search/SearchInput';
import ResultSection from 'components/search/ResultSection';
import SourcesPanel from 'components/search/SourcesPanel';
import ImageGallery from 'components/search/ImageGallery';
import FollowUpSearch from 'components/search/FollowUpSearch';
import AIRelatedSearches from '../components/search/AIRelatedSearches';
import ResultPreview from 'components/search/ResultPreview';
import { motion } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import ErrorRetry from 'components/search/ErrorRetry';
import { SearchThreadItem as SearchThreadItemType } from 'context/SearchContext';
import AgenticSearchProgressDisplay from 'components/search/AgenticSearchProgressDisplay';

const MotionBox = motion(Box);

// Reusable Search Thread Item Component
const SearchThreadItem = React.memo(({ item, isLatest, itemRef, onRelatedSearch }: {
  item: SearchThreadItemType,
  isLatest: boolean,
  itemRef: React.RefObject<HTMLDivElement> | undefined,
  onRelatedSearch: (query: string) => void
}) => {
  const isMobile = useBreakpointValue({ base: true, md: false });
  const itemIsLoading = item.isLoading;
  const itemHasError = item.isError;
  const { isConversationMode, performSearch } = useSearchContext();

  // Debug log
  React.useEffect(() => {
    if (isLatest && !itemIsLoading) {
      console.log('Latest search item (useEffect in Home.tsx):', {
        query: item.query,
        isAgentic: item.isAgentic,
        hasRelatedSearches: item.relatedSearches && item.relatedSearches.length > 0,
        relatedSearches: item.relatedSearches
      });
    }

    // --- BEGIN ADDED LOG for Agentic Item Props ---
    if (item.isAgentic && !itemIsLoading) {
      console.log('[Home.tsx SearchThreadItem] Agentic Item PROPS:', {
        id: item.id,
        query: item.query,
        relatedSearches: item.relatedSearches,
        relatedSearchesLength: item.relatedSearches ? item.relatedSearches.length : 'undefined',
        itemObjectForAgentic: item // Log the whole item object for inspection
      });
    }
    // --- END ADDED LOG for Agentic Item Props ---

  }, [isLatest, item, itemIsLoading]);

  // Get placeholder image URL
  const getImageUrl = (source: any) => {
    return source.imageUrl || `https://via.placeholder.com/300x200/E0E0E0/AAAAAA?text=${encodeURIComponent(source.title || 'Source Image')}`;
  };

  // Determine if we should show the preview section
  const shouldShowPreview = !itemIsLoading && item.sources && item.sources.length > 0;

  // Sanitize image URL function (ensures valid URL format and handles CORS issues)
  const sanitizeImageUrl = (url: string): string => {
    if (!url) return '';
    // Ensure URL has proper scheme
    if (!url.startsWith('http')) {
      return `https://${url}`;
    }
    return url;
  };

  // Extract all image data and map to the format expected by ImageGallery
  const allImages = [
    // Map image results from backend
    ...(item.imageResults || []).map((img: any) => {
      // Ensure we have a valid URL (use original or thumbnail)
      const imageUrl = sanitizeImageUrl(img.url || img.thumbnail || '');
      const thumbnailUrl = sanitizeImageUrl(img.thumbnail || img.url || '');

      return {
        url: imageUrl,
        thumbnail: thumbnailUrl, // Include thumbnail URL separately
        alt: img.alt || img.title || 'Image',
        sourceUrl: sanitizeImageUrl(img.source_url || ''),
        source: img.source_name || ''
      };
    }).filter((img: any) => img.url && img.url.trim() !== ''), // Filter out images with empty URLs

    // Additionally, extract images from sources if they have imageUrl
    ...(item.sources || [])
      .filter((source: any) => source.imageUrl && !source.imageUrl.includes('placeholder.com'))
      .map((source: any) => ({
        url: sanitizeImageUrl(source.imageUrl),
        thumbnail: sanitizeImageUrl(source.imageUrl),
        sourceUrl: sanitizeImageUrl(source.url || source.link || ''),
        alt: source.title || 'Source image',
        source: source.source || 'Web search'
      }))
  ];

  // Show query enhancement notice if available
  const hasQueryEnhancement = item.enhancedQuery && item.enhancedQuery !== item.query;

  // Handle retry for failed searches
  const handleRetry = () => {
    // Use the same query for retry
    performSearch(item.query);
  };

  return (
    <MotionBox
      ref={itemRef}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      mb={10}
      p={{ base: 3, md: 5 }}
      borderRadius="lg"
      bg="transparent"
      width="100%"
    >
      {/* Query Display - style differently based on conversation mode */}
      <Box
        pb={4}
        mb={4}
        borderBottom="1px"
        borderColor="gray.200"
        borderRadius={isConversationMode ? "lg" : "none"}
        bg={isConversationMode ? "blue.50" : "transparent"}
        px={isConversationMode ? 4 : 0}
        py={isConversationMode ? 3 : 0}
        mt={isConversationMode ? 4 : 0}
      >
        {isConversationMode && (
          <Flex mb={2} alignItems="center">
            <Icon as={FiMessageCircle} color="blue.500" mr={2} />
            <Text fontSize="sm" fontWeight="medium" color="blue.500">
              You asked
            </Text>
          </Flex>
        )}
        <Text fontSize={{ base: "xl", md: "2xl" }} fontWeight="semibold" color="gray.800">
          {item.query}
        </Text>

        {/* Enhanced Query Notice */}
        {hasQueryEnhancement && (
          <Flex align="center" mt={2}>
            <InfoIcon color="blue.500" mr={2} />
            <Text fontSize="sm" color="blue.500">
              Enhanced search: {item.enhancedQuery}
            </Text>
          </Flex>
        )}
      </Box>

      {/* Show error retry component if search failed */}
      {itemHasError && (
        <ErrorRetry
          query={item.query}
          searchId={item.id}
          errorMessage={
            item.results?.[0]?.content ||
            "We couldn't complete your search at this time. Please try again."
          }
        />
      )}

      {/* Always render the tab structure regardless of loading state, but hide if there's an error */}
      {!itemHasError && (
        <Tabs variant="soft-rounded" colorScheme="blue" isLazy width="100%">
          <TabList mb={4} pb={2} borderBottom="1px" borderColor="gray.100">
            <Tab mr={2} borderRadius="md" _selected={{ color: 'blue.700', bg: 'blue.50' }}>Answer</Tab>
            <Tab mr={2} borderRadius="md" _selected={{ color: 'blue.700', bg: 'blue.50' }}>
              Images
              {allImages.length > 0 && (
                <Badge ml={2} colorScheme="blue" borderRadius="full">{allImages.length}</Badge>
              )}
            </Tab>
            <Tab borderRadius="md" _selected={{ color: 'blue.700', bg: 'blue.50' }}>
              Sources
              {item.sources && item.sources.length > 0 && (
                <Badge ml={2} colorScheme="gray" borderRadius="full">{item.sources.length}</Badge>
              )}
            </Tab>
          </TabList>
          <TabPanels>
            <TabPanel px={0} pt={4}>
              {/* Loading or Results for the Answer tab */}
              {itemIsLoading && (!item.results || item.results.length === 0) ? (
                item.isAgentic ? (
                  <AgenticSearchProgressDisplay originalQuery={item.query} />
                ) : (
                  <Flex 
                    direction="column" 
                    align="center" 
                    justify="center" 
                    py={12} 
                    px={4}
                    bg="whiteAlpha.500"
                    borderRadius="xl"
                    backdropFilter="blur(5px)"
                  >
                    <Box
                      as={motion.div}
                      animate={{ 
                        scale: [1, 1.1, 1],
                        opacity: [0.7, 1, 0.7]
                      }}
                      // @ts-ignore - Framer motion types issue
                      transition={{ 
                        duration: 2, 
                        repeat: Infinity,
                        ease: "easeInOut" 
                      }}
                      mb={4}
                      position="relative"
                    >
                      <Box
                        position="absolute"
                        top="50%"
                        left="50%"
                        transform="translate(-50%, -50%)"
                        w="40px"
                        h="40px"
                        bg="blue.400"
                        borderRadius="full"
                        filter="blur(20px)"
                        opacity={0.3}
                      />
                      <Icon as={FiCpu} w={10} h={10} color="blue.500" />
                    </Box>
                    <Text 
                      fontSize="lg" 
                      fontWeight="medium" 
                      bgGradient="linear(to-r, blue.600, purple.600)"
                      bgClip="text"
                      animation="pulse 2s infinite"
                    >
                      Nexus is thinking...
                    </Text>
                    <Text fontSize="sm" color="gray.500" mt={2}>
                      Searching the web and analyzing sources
                    </Text>
                  </Flex>
                )
              ) : (
                <>
                  {/* Preview Images and Sources - placed here, just above the result text */}
                  {shouldShowPreview && (isLatest || item.sources.some((s: any) => s.isRelevant)) && (
                    <ResultPreview
                      sources={item.sources}
                      images={allImages}
                      showImages={allImages.length > 0}
                      showSources={item.sources.length > 0}
                    />
                  )}

                  {/* Main Answer */}
                  {item.results && item.results.length > 0 ? (
                    item.results[0]?.type === 'error' ? (
                      <Box my={4}>
                        <ErrorRetry
                          query={item.query}
                          searchId={item.id}
                          onRetry={() => performSearch(item.query)}
                          errorMessage={item.results[0].content}
                        />
                      </Box>
                    ) : (
                      <ResultSection
                        query={item.query}
                        results={item.results}
                        reasoning={item.reasoning}
                        sources={item.sources}
                      />
                    )
                  ) : (
                    <Text color="gray.500" py={4}>No results found for this query.</Text>
                  )}

                  {/* Related Searches - always show for the latest search result */}
                  {isLatest && (
                    <Box mt={4}>
                      <AIRelatedSearches
                        relatedSearches={item.relatedSearches || []}
                        onSearchClick={onRelatedSearch}
                        isVisible={true}
                        baseQuery={item.query}
                      />
                    </Box>
                  )}
                </>
              )}
            </TabPanel>

            {/* Images Tab - always render but conditionally show content */}
            <TabPanel px={0} pt={4}>
              {itemIsLoading ? (
                <VStack spacing={4} align="stretch" py={4}>
                  <Skeleton height="200px" width="100%" borderRadius="md" />
                </VStack>
              ) : allImages.length > 0 ? (
                <ImageGallery
                  images={allImages}
                />
              ) : (
                <Box textAlign="center" py={8} px={4}>
                  <Text color="gray.500" fontSize="lg">
                    No images found for this query. Try another search term that might have relevant images.
                  </Text>
                </Box>
              )}
            </TabPanel>

            {/* Sources Tab */}
            <TabPanel px={0} pt={4}>
              {itemIsLoading ? (
                <VStack spacing={4} align="stretch" py={4}>
                  <Skeleton height="20px" width="90%" borderRadius="md" />
                  <Skeleton height="20px" width="100%" borderRadius="md" />
                  <Skeleton height="20px" width="95%" borderRadius="md" />
                </VStack>
              ) : (
                <SourcesPanel sources={item.sources} />
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>
      )}
    </MotionBox>
  );
});

const Home: React.FC = () => {
  // Get if mobile view is active via breakpoint
  const isMobile = useBreakpointValue({ base: true, md: false });

  // Using search context
  const {
    searchThread,
    performSearch,
    performAgenticSearch,
    isLoading,
    sessionId,
    clearSession,
    isConversationMode,
    setConversationMode,
    agenticSearchMode,
    setAgenticSearchMode,
    conversationContext
  } = useSearchContext();

  // Hoisted color values for initial view toggles
  const initialViewButtonActiveBg = useColorModeValue("blue.50", "blue.800");
  const initialViewButtonActiveColor = useColorModeValue("blue.600", "blue.200");
  const initialViewResearchIconColorValue = useColorModeValue("blue.600", "blue.200");
  // Conditionally set icon color based on agenticSearchMode AFTER fetching the active color
  const initialViewResearchIconColor = agenticSearchMode ? initialViewResearchIconColorValue : "currentColor";

  const lastSearchItemRef = useRef<HTMLDivElement>(null);
  const threadContainerRef = useRef<HTMLDivElement>(null);
  const scrollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Create header ref for scroll behavior
  const headerRef = useRef<HTMLDivElement>(null);

  // Unified scroll function with animation enhancement
  const scrollToLatestSearch = (delay = 100) => {
    if (!lastSearchItemRef.current) return;

    // Cancel any previous scroll timers
    if (scrollTimerRef.current) {
      clearTimeout(scrollTimerRef.current);
      scrollTimerRef.current = null;
    }

    // Set new scroll timer
    scrollTimerRef.current = setTimeout(() => {
      lastSearchItemRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }, delay);
  };

  // Function to initiate a new search
  const handleSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    // Execute search with session continuity
    if (agenticSearchMode) {
      performAgenticSearch(searchQuery, {
        sessionId: sessionId || undefined,
        maxIterations: 5,
        previousContext: isConversationMode && searchThread.length > 0 ? conversationContext : undefined
      });
    } else {
      performSearch(searchQuery, {
        sessionId: sessionId || undefined,
        modalities: ["text", "images"],
        useEnhancement: true
      });
    }

    // Scroll to bottom after a short delay
    setTimeout(() => scrollToLatestSearch(50), 100);
  }, [performSearch, performAgenticSearch, sessionId, agenticSearchMode, isConversationMode, searchThread.length, conversationContext]);

  // Handle related search queries
  const handleRelatedSearch = useCallback((searchQuery: string) => {
    handleSearch(searchQuery);
  }, [handleSearch]);

  // Start a new conversation thread
  const handleNewThread = useCallback(() => {
    clearSession();
    setConversationMode(true);

    // Scroll to top after resetting
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [clearSession, setConversationMode]);

  // Toggle agentic mode - will be used by new buttons
  const toggleAgenticMode = useCallback(() => {
    console.log('Toggling agentic mode. Current mode before toggle:', agenticSearchMode);
    setAgenticSearchMode(!agenticSearchMode);
  }, [agenticSearchMode, setAgenticSearchMode]);

  // Automatically scroll to latest search when a new one is added
  useEffect(() => {
    if (searchThread.length > 0 && !isLoading) {
      scrollToLatestSearch();
    }
  }, [searchThread.length, isLoading]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (scrollTimerRef.current) {
        clearTimeout(scrollTimerRef.current);
      }
    };
  }, []);

  // Get latest search data for display
  const latestSearch = searchThread.length > 0 ? searchThread[searchThread.length - 1] : null;

  // Extract latest related searches from the thread
  const latestRelatedSearches = latestSearch?.relatedSearches || [];

  // Debug to verify what's being passed
  useEffect(() => {
    console.log('Latest search thread item:', latestSearch);
    console.log('Latest related searches from thread:', latestRelatedSearches);

    // Additional debug for AI related searches
    if (latestSearch) {
      console.log('Thread item related searches check:', {
        item: latestSearch.id,
        query: latestSearch.query,
        hasRelatedSearches: !!(latestSearch.relatedSearches && latestSearch.relatedSearches.length > 0),
        relatedSearchesCount: latestSearch.relatedSearches ? latestSearch.relatedSearches.length : 0,
        relatedSearchesSample: latestSearch.relatedSearches ? latestSearch.relatedSearches.slice(0, 2) : []
      });
    }
  }, [latestSearch, latestRelatedSearches]);

  // Initial View with no searches - different layouts for mobile and desktop
  if (searchThread.length === 0) {
    // Mobile initial view - Perplexity style
    if (isMobile) {
      return (
        <Box
          minH="100vh"
          w="100%"
          display="flex"
          flexDirection="column"
          justifyContent="center"
          position="relative"
        >
          {/* Top fixed header for consistency */}
          <Flex
            position="fixed"
            top={0}
            left={0}
            right={0}
            height="60px"
            bg="white"
            borderBottomWidth="1px"
            borderBottomColor="gray.200"
            justify="center"
            align="center"
            px={4}
            zIndex={10}
            boxShadow="0 2px 5px rgba(0,0,0,0.05)"
          >
            <Text
              fontWeight="bold"
              color="blue.600"
              fontSize="lg"
              position="absolute"
              left="50%"
              transform="translateX(-50%)"
              textAlign="center"
            >
              Nexus
            </Text>
          </Flex>

          {/* Logo/Brand area */}
          <Flex
            direction="column"
            align="center"
            justify="center"
            flex="1"
            mt="-100px"
          >
            <MotionBox
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              textAlign="center"
              mb={10}
            >
              <Heading
                as="h1"
                fontSize="3xl"
                fontWeight="bold"
                color="blue.600"
                letterSpacing="tight"
                mb={2}
              >
                Nexus
              </Heading>
              <Text
                fontSize="lg"
                fontWeight="medium"
                color="gray.600"
              >
                AI Search Engine
              </Text>

              {/* Agentic Mode Toggle Buttons for Mobile Initial View */}
              <ButtonGroup size="sm" isAttached variant="outline" mt={6} width="calc(100% - 40px)" maxWidth="300px">
                <Button
                  leftIcon={<Icon as={FiSearch} />}
                  onClick={() => setAgenticSearchMode(false)}
                  isActive={!agenticSearchMode}
                  flex="1"
                  mr="-px"
                  _active={{ bg: initialViewButtonActiveBg, color: initialViewButtonActiveColor }}
                >
                  Standard
                </Button>
                <Button
                  leftIcon={<Icon as={FiBriefcase} color={initialViewResearchIconColor} />}
                  onClick={() => setAgenticSearchMode(true)}
                  isActive={agenticSearchMode}
                  flex="1"
                  _active={{ bg: initialViewButtonActiveBg, color: initialViewButtonActiveColor }}
                >
                  Research
                </Button>
              </ButtonGroup>
            </MotionBox>
          </Flex>

          {/* Fixed bottom search bar */}
          <Box
            position="fixed"
            bottom={0}
            left={0}
            right={0}
            zIndex={10}
          >
            <SearchInput
              onSearch={handleSearch}
              placeholder={agenticSearchMode ? "Ask for in-depth research..." : "Ask anything..."}
              autoFocus
              isMobileLayout={true}
            />
          </Box>
        </Box>
      );
    }

    // Desktop initial view
    return (
      <Box
        minH="100vh"
        w="100%"
        display="flex"
        alignItems="center"
        justifyContent="center"
        pb="100px"
      >
        <Container maxW="container.lg" py={{ base: 0, md: 0 }} marginTop="-120px">
          <VStack spacing={{ base: 16, md: 20 }} align="center">
            {/* Logo/Brand and Headline */}
            <MotionBox
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              textAlign="center"
            >
              <Heading
                as="h1"
                fontSize={{ base: "4xl", md: "5xl" }}
                fontWeight="bold"
                color="blue.600"
                letterSpacing="tight"
                mb={2}
              >
                Nexus
              </Heading>
              <Text
                fontSize={{ base: "xl", md: "2xl" }}
                fontWeight="medium"
                color="gray.600"
              >
                Agentic AI Search Engine
              </Text>

              {/* Agentic Mode Toggle Buttons for Desktop Initial View */}
              <ButtonGroup variant="outline" mt={8} size="md" isAttached>
                <Button
                  leftIcon={<Icon as={FiSearch} />}
                  onClick={() => setAgenticSearchMode(false)}
                  isActive={!agenticSearchMode}
                  _active={{ bg: initialViewButtonActiveBg, color: initialViewButtonActiveColor }}
                  px={6}
                >
                  Standard Search
                </Button>
                <Button
                  leftIcon={<Icon as={FiBriefcase} color={initialViewResearchIconColor} />}
                  onClick={() => setAgenticSearchMode(true)}
                  isActive={agenticSearchMode}
                  _active={{ bg: initialViewButtonActiveBg, color: initialViewButtonActiveColor }}
                  px={6}
                >
                  Deep Research
                </Button>
              </ButtonGroup>
            </MotionBox>

            {/* Search Bar with Enhanced Animation */}
            <MotionBox
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              width="100%"
              maxW="3xl"
            >
              <Box
                borderRadius="xl"
                boxShadow="lg"
                overflow="hidden"
                borderWidth="1px"
                borderColor="gray.200"
                bg="white"
                transition="all 0.2s ease"
                _hover={{ boxShadow: "xl", borderColor: "gray.300" }}
                maxW="900px"
                mx="auto"
              >
                <SearchInput
                  onSearch={handleSearch}
                  placeholder={agenticSearchMode ? "Ask for in-depth research..." : "Ask anything..."}
                  size="lg"
                  autoFocus
                  variant="unstyled"
                  radius="xl"
                  width="100%"
                  isFullWidth={true}
                />
              </Box>
            </MotionBox>

            {/* Suggested Search Examples */}
            <MotionBox
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              textAlign="center"
              width="100%"
              maxW="xl"
            >
              <HStack justify="center" mb={2}>
                <SearchIcon color="gray.500" />
                <Text fontSize="sm" color="gray.500" fontWeight="medium">Try searching for:</Text>
              </HStack>
              <Flex flexWrap="wrap" justifyContent="center" gap={3} mt={4}>
                {[
                  agenticSearchMode ? "What happened to Bill Gates and Jeffrey Epstein?" : "Who is Bill Gates and what's his latest work?",
                  agenticSearchMode ? "Compare Tesla and SpaceX business strategies" : "Show me images of SpaceX rockets",
                  agenticSearchMode ? "How are quantum computers improving AI?" : "Latest AI research breakthroughs",
                  agenticSearchMode ? "What solutions to climate change are most promising?" : "Climate change solutions explained"
                ].map((suggestion, idx) => (
                  <Box
                    key={idx}
                    as="button"
                    px={4}
                    py={2}
                    borderRadius="full"
                    bg="gray.50"
                    color="gray.600"
                    fontSize="sm"
                    fontWeight="medium"
                    _hover={{ bg: "gray.100", transform: "translateY(-2px)" }}
                    transition="all 0.2s"
                    boxShadow="sm"
                    onClick={() => handleSearch(suggestion)}
                  >
                    {suggestion}
                  </Box>
                ))}
              </Flex>
            </MotionBox>
          </VStack>
        </Container>
      </Box>
    );
  }

  // Search Thread View (After first search) - different for mobile and desktop
  // Mobile Thread View
  if (isMobile) {
    return (
      <Box position="relative" minH="100vh">
        {/* Header with Nexus logo and new thread button */}
        <Flex
          position="fixed"
          top={0}
          left={0}
          right={0}
          height="60px"
          bg="white"
          borderBottomWidth="1px"
          borderBottomColor="gray.200"
          justify="space-between"
          align="center"
          px={4}
          zIndex={10}
          boxShadow="0 2px 5px rgba(0,0,0,0.05)"
        >
          <Text fontWeight="bold" color="blue.600" fontSize="lg">
            Nexus
          </Text>

          <Flex align="center">
            <Button
              leftIcon={<AddIcon />}
              size="sm"
              colorScheme="blue"
              variant="outline"
              onClick={handleNewThread}
              borderRadius="full"
              boxShadow="sm"
              px={2}
            >
              New
            </Button>
          </Flex>
        </Flex>

        {/* Scrollable Thread Container - adjust padding to accommodate fixed elements */}
        <Box
          pt="70px"
          pb="80px" // Increased to accommodate taller input
          px={3}
          maxW="100%"
          mx="auto"
          overflowY="auto"
          height="100vh"
        >
          <VStack spacing={4} align="stretch" w="100%">
            {searchThread.map((item, index: number) => (
              <SearchThreadItem
                key={item.id}
                item={item}
                isLatest={index === searchThread.length - 1}
                itemRef={index === searchThread.length - 1 ? lastSearchItemRef : undefined}
                onRelatedSearch={handleRelatedSearch}
              />
            ))}
          </VStack>
        </Box>

        {/* Fixed Bottom Search Bar */}
        <FollowUpSearch
          onSearch={handleSearch}
          isVisible={true}
          onNewThread={handleNewThread}
        />
      </Box>
    );
  }

  // Desktop Search Thread View 
  return (
    <Box position="relative" minH="100vh">
      {/* Header with Nexus logo, and new thread button */}
      <Flex
        position="fixed"
        top={0}
        left={0}
        right={0}
        height="60px"
        bg="white"
        borderBottomWidth="1px"
        borderBottomColor="gray.200"
        justify="space-between"
        align="center"
        px={6}
        zIndex={10}
        boxShadow="0 2px 5px rgba(0,0,0,0.05)"
      >
        <Text fontWeight="bold" color="blue.600" fontSize="lg">
          Nexus
        </Text>

        <Flex align="center">

        </Flex>
      </Flex>

      {/* Scrollable Thread Container */}
      <Box
        ref={threadContainerRef}
        pt="70px"
        pb={{ base: "140px", md: "120px" }}
        px={{ base: 2, md: 4, lg: 2 }}
        maxW={{ base: "100%", xl: "85%" }}
        mx="auto"
        overflowY="auto"
      >
        <VStack spacing={0} align="stretch" w="100%">
          {searchThread.map((item, index: number) => (
            <SearchThreadItem
              key={item.id}
              item={item}
              isLatest={index === searchThread.length - 1}
              itemRef={index === searchThread.length - 1 ? lastSearchItemRef : undefined}
              onRelatedSearch={handleRelatedSearch}
            />
          ))}
        </VStack>
      </Box>

      {/* Floating follow-up search */}
      <Container
        position="fixed"
        bottom={{ base: "70px", md: "30px" }}
        left={{ base: 0, md: "240px" }}
        right={0}
        maxW="container.lg"
        px={{ base: 2, md: 0 }}
        zIndex={999}
        style={{ pointerEvents: "none" }}
      >
        <Box
          style={{ pointerEvents: "auto" }}
          borderRadius="xl"
          boxShadow="lg"
          borderWidth="1px"
          borderColor="gray.200"
          bg="white"
          maxW="900px"
          mx="auto"
          width="100%"
        >
          <FollowUpSearch
            onSearch={handleSearch}
            isVisible={true}
            useFixedPosition={false}
            onNewThread={handleNewThread}
          />
        </Box>
      </Container>
    </Box>
  );
};

export default Home;