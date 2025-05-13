import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { 
  Box, 
  Flex, 
  Text, 
  Link, 
  HStack, 
  IconButton, 
  useDisclosure, 
  Stack,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton
} from '@chakra-ui/react';
import { HamburgerIcon, CloseIcon } from '@chakra-ui/icons';

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  isActive: boolean;
}

const NavLink = ({ to, children, isActive }: NavLinkProps) => (
  <Link
    as={RouterLink}
    to={to}
    px={2}
    py={1}
    rounded={'md'}
    fontWeight={isActive ? 'bold' : 'medium'}
    color={isActive ? 'black' : 'gray.600'}
    position="relative"
    _after={isActive ? {
      content: '""',
      position: 'absolute',
      bottom: '-2px',
      left: '0',
      right: '0',
      height: '2px',
      bg: 'black',
    } : {}}
    _hover={{
      textDecoration: 'none',
      color: 'black',
    }}
  >
    {children}
  </Link>
);

const Header = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const location = useLocation();

  const Links = [
    { name: 'Home', path: '/' },
    { name: 'Search', path: '/search' },
    { name: 'About', path: '/about' },
  ];

  return (
    <Box px={4} boxShadow="sm" bg="white">
      <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
        <IconButton
          size={'md'}
          icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
          aria-label={'Open Menu'}
          display={{ md: 'none' }}
          onClick={isOpen ? onClose : onOpen}
          variant="ghost"
        />
        <HStack spacing={8} alignItems={'center'}>
          <Box>
            <Link as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
              <Text
                fontWeight="bold"
                fontSize="xl"
                letterSpacing="tight"
              >
                NEXUS
              </Text>
            </Link>
          </Box>
          <HStack
            as={'nav'}
            spacing={4}
            display={{ base: 'none', md: 'flex' }}
          >
            {Links.map((link) => (
              <NavLink 
                key={link.name} 
                to={link.path}
                isActive={location.pathname === link.path}
              >
                {link.name}
              </NavLink>
            ))}
          </HStack>
        </HStack>
      </Flex>

      {/* Mobile Nav Drawer */}
      <Drawer
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        size="xs"
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">NEXUS</DrawerHeader>

          <DrawerBody>
            <Stack as={'nav'} spacing={4} mt={4}>
              {Links.map((link) => (
                <NavLink 
                  key={link.name} 
                  to={link.path}
                  isActive={location.pathname === link.path}
                >
                  {link.name}
                </NavLink>
              ))}
            </Stack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default Header;
