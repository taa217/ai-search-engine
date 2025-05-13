import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box, ChakraProvider } from '@chakra-ui/react';
import Home from './pages/Home';
// import SearchPage from './pages/SearchPage';
// import About from './pages/About';
import { SearchProvider } from './context/SearchContext';
import AppLayout from './components/layout/AppLayout';

function App() {
  return (
    <ChakraProvider>
      <SearchProvider>
        <Router>
          <AppLayout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/search-history" element={<Box p={5}>Search History Page</Box>} />
              <Route path="/favorites" element={<Box p={5}>Favorites Page</Box>} />
              <Route path="/about" element={<Box p={5}>About Page</Box>} />
              <Route path="/settings" element={<Box p={5}>Settings Page</Box>} />
            </Routes>
          </AppLayout>
        </Router>
      </SearchProvider>
    </ChakraProvider>
  );
}

export default App;
