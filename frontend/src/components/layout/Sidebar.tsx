import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { 
  VStack, 
  Link, 
  Text, 
  Icon, 
  Divider,
  Box,
  Tooltip,
  Button
} from '@chakra-ui/react';
import { SearchIcon, InfoIcon, SettingsIcon, StarIcon, TimeIcon, AddIcon } from '@chakra-ui/icons';
import { FaHome } from 'react-icons/fa';
import { useSearch } from 'context/SearchContext';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { clearSession } = useSearch();

  const navItems = [
    { name: 'Home', path: '/', icon: FaHome },
    { name: 'Searches', path: '/search-history', icon: TimeIcon },
    { name: 'Favorites', path: '/favorites', icon: StarIcon },
    { name: 'About', path: '/about', icon: InfoIcon },
    { name: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  const handleNewThread = () => {
    clearSession();
    // If not already on home page, navigate there
    if (location.pathname !== '/') {
      window.location.href = '/';
    }
  };

  return (
    <Box
      position="fixed"
      left={0}
      top={0}
      bottom={0}
      width="250px"
      bg="white"
      borderRight="1px"
      borderColor="gray.200"
      height="100vh"
      overflowY="auto"
      zIndex="sticky"
      css={{
        '&::-webkit-scrollbar': {
          width: '4px',
        },
        '&::-webkit-scrollbar-track': {
          width: '6px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'gray.200',
          borderRadius: '24px',
        },
      }}
    >
      <VStack spacing={8} align="start" pt="60px" height="100%" p={4}>

        {/* New Thread Button */}
        <Button
          leftIcon={<AddIcon />}
          colorScheme="blue"
          variant="outline"
          size="md"
          width="100%"
          onClick={handleNewThread}
          borderRadius="md"
          _hover={{
            bg: "blue.50",
          }}
        >
          New Thread
        </Button>
        {/* Navigation links */}
        <VStack spacing={4} align="start" width="100%">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Tooltip key={item.name} label={item.name} placement="right" hasArrow>
                <Link
                  as={RouterLink}
                  to={item.path}
                  display="flex"
                  alignItems="center"
                  width="100%"
                  py={2}
                  px={3}
                  borderRadius="md"
                  color={isActive ? "blue.600" : "gray.600"}
                  bg={isActive ? "blue.50" : "transparent"}
                  _hover={{
                    textDecoration: 'none',
                    bg: "blue.50",
                    color: "blue.600",
                  }}
                  transition="all 0.2s"
                >
                  <Icon as={item.icon} boxSize={5} mr={3} />
                  <Text fontWeight={isActive ? "semibold" : "medium"}>
                    {item.name}
                  </Text>
                </Link>
              </Tooltip>
            );
          })}
        </VStack>
        
        <Divider />
        
        {/* Credits and version info */}
        <Box px={3} fontSize="xs" color="gray.500" mt="auto">
          <Text mb={1}>Nexus AI Search Engine</Text>
          <Text>Version 1.0.0</Text>
        </Box>
      </VStack>
    </Box>
  );
};

export default Sidebar;
