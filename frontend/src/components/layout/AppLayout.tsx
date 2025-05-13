import React, { ReactNode } from 'react';
import { Box, Flex, useBreakpointValue, Button, IconButton, Text } from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import Sidebar from './Sidebar';
import MobileNav from './MobileNav';
import { useSearch } from 'context/SearchContext';
import { useLocation } from 'react-router-dom';

interface AppLayoutProps {
  children: ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const isMobile = useBreakpointValue({ base: true, md: false });
  const { clearSession } = useSearch();
  const location = useLocation();
  
  // Check if we're on the home page
  const isHomePage = location.pathname === '/';

  const handleNewThread = () => {
    clearSession();
    // If not already on home page, navigate there
    if (location.pathname !== '/') {
      window.location.href = '/';
    }
  };

  return (
    <Box minH="100vh" bg="gray.50">
      {/* App Logo and New Thread Button for Desktop, and for Mobile on non-Home pages */}
      {(!isHomePage || !isMobile) && (
        <Flex
          position="fixed"
          top={0}
          left={0}
          right={0}
          zIndex="docked"
          p={4}
          justifyContent="space-between"
          alignItems="center"
          bg={isMobile ? "white" : "transparent"}
          boxShadow={isMobile ? "0 1px 2px rgba(0,0,0,0.05)" : "none"}
          ml={isMobile ? 0 : "250px"}
          transition="margin 0.2s"
        >
          <Box
            fontWeight="bold"
            fontSize="xl"
            color="blue.600"
          >
            NEXUS
          </Box>
          
          {isMobile && (
            <Button
              leftIcon={<AddIcon />}
              size="sm"
              colorScheme="blue"
              variant="outline"
              borderRadius="full"
              onClick={handleNewThread}
              boxShadow="sm"
              px={3}
            >
              New
            </Button>
          )}
        </Flex>
      )}

      {/* Sidebar - Desktop */}
      {!isMobile && <Sidebar />}

      {/* Main Content Area */}
      <Box
        ml={isMobile ? 0 : "250px"}
        minH="100vh"
        position="relative"
        transition="margin 0.2s"
      >
        <Box
          pt={isHomePage && isMobile ? "0" : "60px"}
          px={{ base: 2, md: 4, lg: 6 }}
          pb={isMobile ? "60px" : 4}
          maxW="1920px"
          mx="auto"
          width="100%"
          position="relative"
          zIndex={1}
        >
          {children}
        </Box>
      </Box>

      {/* Mobile Navigation - always render on mobile, but use homePageMode prop on home page */}
      {isMobile && (
        <MobileNav homePageMode={isHomePage} />
      )}
    </Box>
  );
};

export default AppLayout;
