import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { 
  Flex, 
  Box, 
  Icon, 
  Text,
  Tooltip,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  IconButton,
  VStack,
  HStack,
  Divider,
} from '@chakra-ui/react';
import { SearchIcon, InfoIcon, SettingsIcon, StarIcon, TimeIcon, AddIcon, HamburgerIcon } from '@chakra-ui/icons';
import { FaHome } from 'react-icons/fa';
import { useSearch } from 'context/SearchContext';

interface MobileNavProps {
  homePageMode?: boolean;
}

const MobileNav: React.FC<MobileNavProps> = ({ homePageMode = false }) => {
  const location = useLocation();
  const { clearSession } = useSearch();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { name: 'Home', path: '/', icon: FaHome },
    { name: 'History', path: '/search-history', icon: TimeIcon },
    { name: 'About', path: '/about', icon: InfoIcon },
  ];

  const onClose = () => setIsOpen(false);
  const onOpen = () => setIsOpen(true);

  return (
    <>
      {/* Hamburger menu button - always visible */}
      <Box 
        position="fixed" 
        top="16px" 
        left="16px" 
        zIndex={20}  // Increased z-index to be higher than header
      >
        <IconButton
          aria-label="Open menu"
          icon={<HamburgerIcon />}
          onClick={onOpen}
          variant="ghost"
          size="md"
          color="gray.600"
          _hover={{ bg: 'gray.100' }}
          borderRadius="full"
        />
      </Box>

      {/* Drawer for menu items */}
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">
            <Text color="blue.600" fontWeight="bold" fontSize="xl">Nexus</Text>
          </DrawerHeader>
          <DrawerBody p={0}>
            <VStack align="stretch" spacing={0}>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Box 
                    key={item.name}
                    as={RouterLink}
                    to={item.path}
                    p={4}
                    bg={isActive ? "blue.50" : "transparent"}
                    color={isActive ? "blue.600" : "gray.700"}
                    _hover={{ bg: "gray.50", textDecoration: 'none' }}
                    onClick={onClose}
                  >
                    <HStack spacing={3}>
                      <Icon as={item.icon} boxSize={5} />
                      <Text fontWeight={isActive ? "semibold" : "medium"}>
                        {item.name}
                      </Text>
                    </HStack>
                  </Box>
                );
              })}
              <Divider />
              <Box p={4} color="gray.600">
                <Text fontSize="sm">© 2025 Nexus Search</Text>
              </Box>
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Bottom navigation - only displayed when NOT in home page mode */}
      {!homePageMode && (
        <Flex
          position="fixed"
          bottom="0"
          left="0"
          right="0"
          height="60px"
          bg="white"
          boxShadow="0 -2px 10px rgba(0, 0, 0, 0.05)"
          justifyContent="space-around"
          alignItems="center"
          zIndex="999"
        >
          {navItems.map((item) => {
            const isActive = item.path ? location.pathname === item.path : false;

            return (
              <Tooltip key={item.name} label={item.name} placement="top" hasArrow>
                <Box
                  as={RouterLink}
                  to={item.path || '#'}
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  flex="1"
                  py={2}
                  color={isActive ? "blue.600" : "gray.600"}
                  _hover={{
                    textDecoration: 'none',
                    color: "blue.600",
                  }}
                >
                  <Icon as={item.icon} boxSize={5} mb={0.5} />
                  <Text fontSize="xs" fontWeight={isActive ? "semibold" : "normal"}>
                    {item.name}
                  </Text>
                </Box>
              </Tooltip>
            );
          })}
        </Flex>
      )}
    </>
  );
};

export default MobileNav;
