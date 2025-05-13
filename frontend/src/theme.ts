import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

// Define the color mode configuration
const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

// Define the colors based on black and white primary colors
const colors = {
  brand: {
    50: '#f7f7f7',
    100: '#e6e6e6',
    200: '#cccccc',
    300: '#b3b3b3',
    400: '#999999',
    500: '#808080',
    600: '#666666',
    700: '#4d4d4d',
    800: '#333333',
    900: '#1a1a1a',
  },
  accentBlue: {
    50: '#e6f0ff',
    100: '#b3d1ff',
    200: '#80b3ff',
    300: '#4d94ff',
    400: '#1a75ff',
    500: '#0066ff',
    600: '#0052cc',
    700: '#003d99',
    800: '#002966',
    900: '#001433',
  },
};

// Define the customized theme
const theme = extendTheme({
  config,
  colors,
  fonts: {
    heading: `'Inter', sans-serif`,
    body: `'Inter', sans-serif`,
  },
  components: {
    Button: {
      variants: {
        solid: {
          bg: 'black',
          color: 'white',
          _hover: {
            bg: 'gray.800',
          },
          _active: {
            bg: 'gray.700',
          },
        },
        outline: {
          borderColor: 'black',
          color: 'black',
          _hover: {
            bg: 'gray.100',
          },
        },
        ghost: {
          color: 'black',
          _hover: {
            bg: 'gray.100',
          },
        },
      },
    },
    Input: {
      baseStyle: {
        field: {
          borderColor: 'gray.300',
          _hover: {
            borderColor: 'gray.400',
          },
          _focus: {
            borderColor: 'black',
            boxShadow: '0 0 0 1px black',
          },
        },
      },
    },
  },
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'light' ? 'white' : 'gray.900',
        color: props.colorMode === 'light' ? 'black' : 'white',
      },
    }),
  },
});

export default theme;
