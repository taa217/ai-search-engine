import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
//import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// API base URL - update this to your actual API endpoint
const API_BASE_URL = 'https://ai-search-engine-qli1.onrender.com' // 'http://localhost:8000' // 'https://ai-search-engine-qli1.onrender.com' //;

// Types
export interface SearchResult {
  content: string;
  type: string;
}

export interface SearchSession {
  id: string;
  queries: string[];
  createdAt: Date;
}

export interface ReasoningStep {
  step: number;
  thought: string;
}

export interface Source {
  url?: string;
  link?: string;
  title: string;
  snippet?: string;
  imageUrl?: string;
  isRelevant?: boolean; // Flag to indicate if this is a highly relevant source
  source?: string;
}

export interface ImageResult {
  url: string;
  title: string;
  source_url?: string;
  alt?: string;
  height?: number;
  width?: number;
  source_name?: string;
}

export interface VideoResult {
  title: string;
  link: string;
  thumbnail: string;
  source?: string;
  duration?: string;
  description?: string;
}

export interface ResearchStep {
  id: string;
  query: string;
  reasoning: string;
  results_count: number;
  timestamp: string;
  execution_time: number;
}

export interface AgenticSearchResponse {
  plan_id: string;
  original_query: string;
  research_steps: ResearchStep[];
  synthesis: string;
  status: string; // "initiated", "in_progress", "completed", "error"
  iterations_completed: number;
  max_iterations: number;
  error?: string;
  conversation_context?: string;
  sources?: Source[]; // Add sources field to match backend response
  related_searches?: string[]; // Add related_searches for agentic response
}

export interface SearchResponse {
  results: SearchResult[];
  reasoning: ReasoningStep[];
  sources: Source[];
  execution_time: number;
  session_id: string;
  image_results?: ImageResult[];
  video_results?: VideoResult[];
  enhanced_query?: string;
  has_images?: boolean;
  has_videos?: boolean;
  conversation_context?: string;
  related_searches?: string[];
}

export interface SearchThreadItem {
  id: string;
  query: string;
  enhancedQuery?: string;
  results: SearchResult[];
  sources: Source[];
  reasoning: ReasoningStep[];
  timestamp: Date;
  isLoading: boolean;
  isError?: boolean;
  imageResults: ImageResult[];
  videoResults: VideoResult[];
  hasImages: boolean;
  hasVideos: boolean;
  isLoadingImages?: boolean; // Flag to indicate images are still loading
  relatedSearches?: string[];
  isAgentic?: boolean; // Flag to indicate if this was an agentic/deep search
}

interface SearchOptions {
  maxResults?: number;
  useWeb?: boolean;
  depth?: number;
  sessionId?: string;
  modalities?: string[];
  useEnhancement?: boolean;
  modelProvider?: string;
  modelName?: string;
}

interface AgenticSearchOptions {
  planId?: string;
  sessionId?: string;
  maxIterations?: number;
  previousContext?: string;
}

interface SearchProviderProps {
  children: ReactNode;
}

interface SearchContextProps {
  query: string;
  setQuery: (query: string) => void;
  isLoading: boolean;
  results: SearchResult[];
  reasoning: ReasoningStep[];
  sources: Source[];
  executionTime: number;
  error: string | null;
  performSearch: (searchQuery?: string, options?: SearchOptions) => Promise<void>;
  performAgenticSearch: (searchQuery?: string, options?: AgenticSearchOptions) => Promise<void>;
  retrySearch: (searchId: string) => Promise<void>;
  sessionHistory: string[];
  sessionId: string | null;
  searchThread: SearchThreadItem[];
  clearSession: () => void;
  imageResults: ImageResult[];
  videoResults: VideoResult[];
  hasImages: boolean;
  hasVideos: boolean;
  enhancedQuery: string | null;
  isConversationMode: boolean;
  setConversationMode: (mode: boolean) => void;
  conversationContext: string;
  relatedSearches: string[];
  agenticSearch: AgenticSearchResponse | null;
  agenticSearchMode: boolean;
  setAgenticSearchMode: (mode: boolean) => void;
}

// Create context
const SearchContext = createContext<SearchContextProps | undefined>(undefined);

// Provider component
export const SearchProvider = ({ children }: SearchProviderProps) => {
  const [query, setQuery] = useState<string>('');
  const [enhancedQuery, setEnhancedQuery] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [reasoning, setReasoning] = useState<ReasoningStep[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [executionTime, setExecutionTime] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionHistory, setSessionHistory] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [imageResults, setImageResults] = useState<ImageResult[]>([]);
  const [videoResults, setVideoResults] = useState<VideoResult[]>([]);
  const [hasImages, setHasImages] = useState<boolean>(false);
  const [hasVideos, setHasVideos] = useState<boolean>(false);
  const [isConversationMode, setConversationMode] = useState<boolean>(true);
  const [conversationContext, setConversationContext] = useState<string>('');
  const [relatedSearches, setRelatedSearches] = useState<string[]>([]);
  const [agenticSearch, setAgenticSearch] = useState<AgenticSearchResponse | null>(null);
  const [agenticSearchMode, setAgenticSearchMode] = useState<boolean>(false);
  
  // Thread of search items to maintain conversation context in UI
  const [searchThread, setSearchThread] = useState<SearchThreadItem[]>([]);

  // Get session ID from localStorage on initial load
  useEffect(() => {
    const savedSessionId = localStorage.getItem('nexus_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      // Try to load existing thread from local storage as well
      const savedThread = localStorage.getItem('nexus_search_thread');
      if (savedThread) {
        try {
          const parsedThread = JSON.parse(savedThread);
          setSearchThread(parsedThread);
        } catch (e) {
          console.error("Failed to parse saved search thread", e);
        }
      }
    }
  }, []);

  // Save session ID and thread to localStorage when they change
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('nexus_session_id', sessionId);
    }
    
    // Save the search thread for persistence
    if (searchThread.length > 0) {
      // Only save last 10 items to avoid localStorage limits
      const threadToSave = searchThread.slice(-10);
      localStorage.setItem('nexus_search_thread', JSON.stringify(threadToSave));
    }
  }, [sessionId, searchThread]);

  // Rewrite retrySearch function to replace the current search
  const retrySearch = async (searchId: string) => {
    // Find the search that needs to be retried
    const searchItemIndex = searchThread.findIndex(item => item.id === searchId);
    if (searchItemIndex === -1) return;
    
    // Get the search item to retry
    const searchItem = searchThread[searchItemIndex];
    const searchTerm = searchItem.query;
    
    try {
      // Update loading state for this item only
      setSearchThread(prev => {
        const updatedThread = [...prev];
        updatedThread[searchItemIndex] = {
          ...updatedThread[searchItemIndex],
          isLoading: true,
          isError: false,
        };
        return updatedThread;
      });
      
      // Set global loading state
      setIsLoading(true);
      setError(null);

      // Direct API call without creating a new thread item
      const response = await axios.post<SearchResponse>(`${API_BASE_URL}/api/search`, {
        query: searchTerm,
        max_results: 10,
        use_web: true,
        depth: 4,
        session_id: sessionId,
        modalities: ["text", "images"],
        use_enhancement: true,
        conversation_mode: isConversationMode
      });

      // Save session ID from response
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Process enhanced sources with images
      const sourcesWithImages = response.data.sources.map(source => {
        return {
          ...source,
          imageUrl: source.imageUrl || `https://via.placeholder.com/300x200/E0E0E0/AAAAAA?text=${encodeURIComponent(source.title || 'Source Image')}`,
          isRelevant: true
        };
      });

      // Update the same search thread item with results
      setSearchThread(prev => {
        const updatedThread = [...prev];
        updatedThread[searchItemIndex] = {
          ...updatedThread[searchItemIndex],
          results: response.data.results,
          sources: sourcesWithImages,
          reasoning: response.data.reasoning,
          isLoading: false,
          isError: false,
          imageResults: response.data.image_results || [],
          videoResults: response.data.video_results || [],
          hasImages: response.data.has_images || false,
          hasVideos: response.data.has_videos || false,
          enhancedQuery: response.data.enhanced_query || searchTerm,
          relatedSearches: response.data.related_searches || [],
        };
        return updatedThread;
      });

      // Update global state with search results
      setResults(response.data.results);
      setReasoning(response.data.reasoning);
      setSources(sourcesWithImages);
      setExecutionTime(response.data.execution_time);
      setQuery(searchTerm);
      setEnhancedQuery(response.data.enhanced_query || null);
      setImageResults(response.data.image_results || []);
      setVideoResults(response.data.video_results || []);
      setHasImages(response.data.has_images || false);
      setHasVideos(response.data.has_videos || false);
      setRelatedSearches(response.data.related_searches || []);
      
      if (response.data.conversation_context) {
        setConversationContext(response.data.conversation_context);
      }
      
    } catch (error) {
      console.error('Retry search error:', error);
      
      // Format error message based on error type
      let errorMessage = 'An unexpected error occurred while searching';
      
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Search request timed out. Please try again.';
        } else if (error.response) {
          // Server responded with an error
          if (error.response.status === 429) {
            errorMessage = 'Too many search requests. Please wait a moment and try again.';
          } else if (error.response.status >= 500) {
            errorMessage = 'Our search servers are experiencing issues. Please try again later.';
          } else {
            errorMessage = `Search failed: ${error.response.data.detail || error.message}`;
          }
        } else if (error.request) {
          // Request was made but no response received
          errorMessage = 'No response from search server. Please check your connection and try again.';
        }
      }
      
      // Update the search thread item with error
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const searchItemIndex = updatedThread.findIndex(item => item.id === searchId);
        
        if (searchItemIndex !== -1) {
          updatedThread[searchItemIndex] = {
            ...updatedThread[searchItemIndex],
            results: [{content: errorMessage, type: 'error'}],
            isLoading: false,
            isError: true,
            isLoadingImages: false
          };
        }
        
        return updatedThread;
      });
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const performAgenticSearch = async (searchQuery?: string, options: AgenticSearchOptions = {}) => {
    const searchTerm = searchQuery || query;
    let newSearchId: string = ''; // Declare newSearchId here

    if (!searchTerm.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      newSearchId = `agentic-search-${Date.now()}`; // Assign newSearchId
      const newSearchItem: SearchThreadItem = {
        id: newSearchId,
        query: searchTerm,
        results: [],
        sources: [],
        reasoning: [],
        timestamp: new Date(),
        isLoading: true,
        isError: false,
        imageResults: [],
        videoResults: [],
        hasImages: false,
        hasVideos: false,
        relatedSearches: [],
        isAgentic: true // Mark as agentic search
      };

      setSearchThread(prev => [...prev, newSearchItem]);
      setIsLoading(true);
      setError(null);
      setAgenticSearch(null);
      setSessionHistory(prev => [...prev, searchTerm]);

      let previousContext = options.previousContext || '';
      if (isConversationMode && searchThread.length > 1) { // Ensure there's a previous item for context
        const contextItems = searchThread.slice(-4, -1); // Get up to 3 items before the current one
        const formattedContext = contextItems.map(item =>
          `Query: ${item.query}\\nAnswer: ${item.results[0]?.content || ''}`
        ).join('\\n\\n');
        previousContext = formattedContext;
        console.log('Applying conversation context to deep research:', {
          contextLength: previousContext.length,
          query: searchTerm
        });
      }

      const response = await axios.post<AgenticSearchResponse>(`${API_BASE_URL}/agentic-search`, {
        query: searchTerm,
        session_id: options.sessionId || sessionId,
        plan_id: options.planId,
        max_iterations: options.maxIterations || 5,
        conversation_context: previousContext,
        conversation_mode: isConversationMode
      });

      console.log('[SearchContext performAgenticSearch] Raw response.data from backend:', response.data);

      setAgenticSearch(response.data);
      setQuery(searchTerm);

      const formattedResult = {
        content: response.data.synthesis,
        type: 'text'
      };
      const formattedReasoning = response.data.research_steps.map((step, index) => ({
        step: index + 1,
        thought: `${step.query} - ${step.reasoning}`
      }));
      const sourcesWithImages = (response.data.sources || []).map(source => ({
        ...source,
        imageUrl: source.imageUrl || `https://via.placeholder.com/300x200/E0E0E0/AAAAAA?text=${encodeURIComponent(source.title || 'Source Image')}`,
        isRelevant: true
      }));
      const agenticRelatedSearches = response.data.related_searches || []; // Get related searches

      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.id === newSearchId);

        console.log('[SearchContext performAgenticSearch INSIDE setSearchThread]:', {
          newSearchId,
          lookingForId: newSearchId, // Explicitly show what ID we are matching
          foundIndex: loadingItemIndex,
          agenticRelatedSearchesAtTimeToUpdate: agenticRelatedSearches, // Crucial: value of this variable here
          responseDotDataDotRelatedSearches: response.data.related_searches, // Value from original response
        });

        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: [formattedResult],
            reasoning: formattedReasoning,
            sources: sourcesWithImages,
            isLoading: false,
            isError: false,
            relatedSearches: agenticRelatedSearches, // Store related searches
            // isAgentic: true, // Already set on creation
          };
        }
        return updatedThread;
      });

      if (response.data.conversation_context) {
        setConversationContext(response.data.conversation_context);
      }
      setSources(sourcesWithImages);
      setRelatedSearches(agenticRelatedSearches); // Also update global state if needed, though thread is primary
      if (response.data.plan_id) {
        console.log(`Research plan created: ${response.data.plan_id}`);
      }

    } catch (error) {
      console.error('Agentic search error:', error);
      let errorMessage = 'An unexpected error occurred during research';
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Research request timed out. Please try again.';
        } else if (error.response) {
          if (error.response.status === 429) {
            errorMessage = 'Too many research requests. Please wait a moment and try again.';
          } else if (error.response.status >= 500) {
            errorMessage = 'Our research servers are experiencing issues. Please try again later.';
          } else {
            errorMessage = `Research failed: ${error.response.data.detail || error.message}`;
          }
        } else if (error.request) {
          errorMessage = 'No response from research server. Please check your connection and try again.';
        }
      }

      setSearchThread(prev => {
        const updatedThread = [...prev];
        // newSearchId is now in scope
        const loadingItemIndex = updatedThread.findIndex(item => item.id === newSearchId); 
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: [{ content: errorMessage, type: 'error' }],
            isLoading: false,
            isError: true,
            isLoadingImages: false, // Ensure this is reset
            // isAgentic: true, // Already set on creation
          };
        }
        return updatedThread;
      });
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const performSearch = async (searchQuery?: string, options: SearchOptions = {}) => {
    const searchTerm = searchQuery || query;
    
    if (!searchTerm.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      // If in agentic search mode, perform agentic search instead
      if (agenticSearchMode) {
        return performAgenticSearch(searchTerm);
      }

      // Create a new search thread item in loading state
      const newSearchId = `search-${Date.now()}`;
      const newSearchItem: SearchThreadItem = {
        id: newSearchId,
        query: searchTerm,
        results: [],
        sources: [],
        reasoning: [],
        timestamp: new Date(),
        isLoading: true,
        isError: false,
        imageResults: [],
        videoResults: [],
        hasImages: false,
        hasVideos: false,
        isLoadingImages: true, // Start with images loading
        relatedSearches: [],
        isAgentic: false // Mark as standard search
      };

      // Add to thread history
      setSearchThread(prev => [...prev, newSearchItem]);
      
      setIsLoading(true);
      setError(null);

      // Add to session history
      setSessionHistory(prev => [...prev, searchTerm]);

      // Split the request into two parts: text first, then images
      // 1. Initial request for text results
      const initialResponse = await axios.post<SearchResponse>(`${API_BASE_URL}/api/search`, {
        query: searchTerm,
        max_results: options.maxResults || 10,
        use_web: options.useWeb !== undefined ? options.useWeb : true,
        depth: options.depth || 2,
        session_id: options.sessionId || sessionId,
        modalities: ["text"], // Only request text first
        use_enhancement: options.useEnhancement !== undefined ? options.useEnhancement : true,
        model_provider: options.modelProvider,
        model_name: options.modelName,
        conversation_mode: isConversationMode
      });

      // Save session ID from response
      if (initialResponse.data.session_id) {
        setSessionId(initialResponse.data.session_id);
      }

      // Process initial sources
      const initialSources = initialResponse.data.sources.map(source => {
        return {
          ...source,
          imageUrl: source.imageUrl || `https://via.placeholder.com/300x200/E0E0E0/AAAAAA?text=${encodeURIComponent(source.title || 'Source Image')}`,
          isRelevant: true
        };
      });

      // Update search thread with initial text results
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.id === newSearchId);
        
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: initialResponse.data.results,
            sources: initialSources,
            reasoning: initialResponse.data.reasoning,
            isLoading: false,
            isError: false,
            isLoadingImages: true, // Still loading images
            enhancedQuery: initialResponse.data.enhanced_query || searchTerm,
            relatedSearches: initialResponse.data.related_searches || [],
            isAgentic: false
          };
        }
        
        return updatedThread;
      });

      // Update global state with initial results
      setResults(initialResponse.data.results);
      setReasoning(initialResponse.data.reasoning);
      setSources(initialSources);
      setExecutionTime(initialResponse.data.execution_time);
      setQuery(searchTerm);
      setEnhancedQuery(initialResponse.data.enhanced_query || null);
      setRelatedSearches(initialResponse.data.related_searches || []);
      
      // Extract conversation context if available
      if (initialResponse.data.conversation_context) {
        setConversationContext(initialResponse.data.conversation_context);
      }
      
      // 2. Second request for images (in parallel or after showing text results)
      try {
        const imageResponse = await axios.post<SearchResponse>(`${API_BASE_URL}/api/search`, {
          query: searchTerm,
          max_results: options.maxResults || 5,
          use_web: true,
          depth: options.depth || 2,
          session_id: initialResponse.data.session_id || sessionId,
          modalities: ["images"], // Only request images in this second call
          use_enhancement: options.useEnhancement !== undefined ? options.useEnhancement : true,
          model_provider: options.modelProvider,
          model_name: options.modelName,
          conversation_mode: isConversationMode
        });
        
        // Update thread with image results
        setSearchThread(prev => {
          const updatedThread = [...prev];
          const searchItemIndex = updatedThread.findIndex(item => item.id === newSearchId);
          
          if (searchItemIndex !== -1) {
            updatedThread[searchItemIndex] = {
              ...updatedThread[searchItemIndex],
              imageResults: imageResponse.data.image_results || [],
              videoResults: imageResponse.data.video_results || [],
              hasImages: imageResponse.data.has_images || false,
              hasVideos: imageResponse.data.has_videos || false,
              isLoadingImages: false // Images are now loaded
            };
          }
          
          return updatedThread;
        });
        
        // Update global state with image results
        setImageResults(imageResponse.data.image_results || []);
        setVideoResults(imageResponse.data.video_results || []);
        setHasImages(imageResponse.data.has_images || false); 
        setHasVideos(imageResponse.data.has_videos || false);
        
      } catch (imageError) {
        console.error('Error fetching images:', imageError);
        
        // Mark images as failed loading but don't show an error message for the whole search
        setSearchThread(prev => {
          const updatedThread = [...prev];
          const searchItemIndex = updatedThread.findIndex(item => item.id === newSearchId);
          
          if (searchItemIndex !== -1) {
            updatedThread[searchItemIndex] = {
              ...updatedThread[searchItemIndex],
              isLoadingImages: false // No longer loading images (even though failed)
            };
          }
          
          return updatedThread;
        });
      }
      
    } catch (error) {
      console.error('Search error:', error);
      
      // Format error message based on error type
      let errorMessage = 'An unexpected error occurred while searching';
      
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Search request timed out. Please try again.';
        } else if (error.response) {
          // Server responded with an error
          if (error.response.status === 429) {
            errorMessage = 'Too many search requests. Please wait a moment and try again.';
          } else if (error.response.status >= 500) {
            errorMessage = 'Our search servers are experiencing issues. Please try again later.';
          } else {
            errorMessage = `Search failed: ${error.response.data.detail || error.message}`;
          }
        } else if (error.request) {
          // Request was made but no response received
          errorMessage = 'No response from search server. Please check your connection and try again.';
        }
      }
      
      // Update the search thread item with error
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.isLoading);
        
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: [{content: errorMessage, type: 'error'}],
            isLoading: false,
            isError: true,
            isLoadingImages: false
          };
        }
        
        return updatedThread;
      });
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSession = useCallback(() => {
    // Clear session from localStorage
    localStorage.removeItem('nexus_session_id');
    localStorage.removeItem('nexus_search_thread');
    
    // Reset all state
    setSessionId(null);
    setSessionHistory([]);
    setSearchThread([]);
    setQuery('');
    setResults([]);
    setReasoning([]);
    setSources([]);
    setImageResults([]);
    setVideoResults([]);
    setHasImages(false);
    setHasVideos(false);
    setEnhancedQuery(null);
    setConversationContext('');
    setRelatedSearches([]);
    setAgenticSearch(null);
    
    // Call the backend to delete the session if we have an ID
    if (sessionId) {
      axios.delete(`${API_BASE_URL}/api/sessions/${sessionId}`)
        .catch(err => console.error('Error deleting session:', err));
    }
  }, [sessionId]);

  const value = {
    query,
    setQuery,
    isLoading,
    results,
    reasoning,
    sources,
    executionTime,
    error,
    performSearch,
    performAgenticSearch,
    retrySearch,
    sessionHistory,
    sessionId,
    searchThread,
    clearSession,
    imageResults,
    videoResults,
    hasImages,
    hasVideos,
    enhancedQuery,
    isConversationMode,
    setConversationMode,
    conversationContext,
    relatedSearches,
    agenticSearch,
    agenticSearchMode,
    setAgenticSearchMode
  };

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
};

// Custom hook to use the search context
export const useSearchContext = () => {
  const context = useContext(SearchContext);
  if (context === undefined) {
    throw new Error('useSearchContext must be used within a SearchProvider');
  }
  return context;
};

// Backward compatibility export
export const useSearch = useSearchContext;
