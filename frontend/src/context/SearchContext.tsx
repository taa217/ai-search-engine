import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
//import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// API base URL - update this to your actual API endpoint
const API_BASE_URL = 'https://ai-search-engine-qli1.onrender.com'; //'http://localhost:8000'

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
  relatedSearches?: string[];
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
          relatedSearches: response.data.related_searches || []
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
        updatedThread[searchItemIndex] = {
          ...updatedThread[searchItemIndex],
          results: [{content: errorMessage, type: 'error'}],
          isLoading: false,
          isError: true
        };
        return updatedThread;
      });
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const performAgenticSearch = async (searchQuery?: string, options: AgenticSearchOptions = {}) => {
    const searchTerm = searchQuery || query;
    
    if (!searchTerm.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      // Create a new search thread item in loading state, similar to standard search
      const newSearchId = `agentic-search-${Date.now()}`;
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
        relatedSearches: []
      };

      // Add to thread history
      setSearchThread(prev => [...prev, newSearchItem]);
      
      setIsLoading(true);
      setError(null);
      setAgenticSearch(null);

      // Add to session history
      setSessionHistory(prev => [...prev, searchTerm]);

      // Build context from previous searches if in conversation mode
      let previousContext = options.previousContext || '';
      
      // If this is a follow-up question, build context from previous searches
      if (isConversationMode && searchThread.length > 0) {
        // Get the last few search items for context
        const contextItems = searchThread.slice(-3);
        
        // Format context items
        const formattedContext = contextItems.map(item => 
          `Query: ${item.query}\nAnswer: ${item.results[0]?.content || ''}`
        ).join('\n\n');
        
        // Add to context
        previousContext = formattedContext;
        
        // Debug log
        console.log('Applying conversation context to deep research:', {
          contextLength: previousContext.length,
          searchThreadLength: searchThread.length,
          query: searchTerm
        });
      }

      // Connect to the backend API for agentic search
      const response = await axios.post<AgenticSearchResponse>(`${API_BASE_URL}/agentic-search`, {
        query: searchTerm,
        session_id: options.sessionId || sessionId,
        plan_id: options.planId,
        max_iterations: options.maxIterations || 5,
        conversation_context: previousContext,
        conversation_mode: isConversationMode
      });

      // Store the agentic search response
      setAgenticSearch(response.data);
      
      // Set current query
      setQuery(searchTerm);
      
      // Format the agentic search result as a standard search result
      const formattedResult = {
        content: response.data.synthesis,
        type: 'text'
      };
      
      // Format research steps as reasoning steps
      const formattedReasoning = response.data.research_steps.map((step, index) => ({
        step: index + 1,
        thought: `${step.query} - ${step.reasoning}`
      }));
      
      // Update the search thread item with results
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.id === newSearchId);
        
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: [formattedResult],
            reasoning: formattedReasoning,
            isLoading: false,
            isError: false,
            // We don't have image results yet in agentic search
            relatedSearches: [] // We could generate related searches from the synthesis if needed
          };
        }
        
        return updatedThread;
      });
      
      // Store conversation context if available
      if (response.data.conversation_context) {
        setConversationContext(response.data.conversation_context);
        
        // Debug log
        console.log('Received conversation context from deep research:', {
          contextLength: response.data.conversation_context.length,
          query: searchTerm
        });
      }
      
      // Track session ID
      if (response.data.plan_id) {
        // We could track plans here if needed
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
      
      // Update the search thread item with error
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.isLoading);
        
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
            results: [{content: errorMessage, type: 'error'}],
            isLoading: false,
            isError: true
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
        relatedSearches: []
      };

      // Add to thread history
      setSearchThread(prev => [...prev, newSearchItem]);
      
      setIsLoading(true);
      setError(null);

      // Add to session history
      setSessionHistory(prev => [...prev, searchTerm]);

      // Connect to the backend API with enhanced options
      const response = await axios.post<SearchResponse>(`${API_BASE_URL}/api/search`, {
        query: searchTerm,
        max_results: options.maxResults || 5,
        use_web: options.useWeb !== undefined ? options.useWeb : true,
        depth: options.depth || 2,
        session_id: options.sessionId || sessionId,
        modalities: options.modalities || ["text", "images"],
        use_enhancement: options.useEnhancement !== undefined ? options.useEnhancement : true,
        model_provider: options.modelProvider,
        model_name: options.modelName,
        conversation_mode: isConversationMode
      });

      // Save session ID from response
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Process enhanced sources with images
      const sourcesWithImages = response.data.sources.map(source => {
        // Use actual image URLs when available
        return {
          ...source,
          imageUrl: source.imageUrl || `https://via.placeholder.com/300x200/E0E0E0/AAAAAA?text=${encodeURIComponent(source.title || 'Source Image')}`,
          isRelevant: true // Mark all backend sources as relevant
        };
      });

      // Update the search thread item with results
      setSearchThread(prev => {
        const updatedThread = [...prev];
        const loadingItemIndex = updatedThread.findIndex(item => item.id === newSearchId);
        
        if (loadingItemIndex !== -1) {
          updatedThread[loadingItemIndex] = {
            ...updatedThread[loadingItemIndex],
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
            relatedSearches: response.data.related_searches || []
          };
        }
        
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
      
      // Debug related searches from API
      console.log('API related searches:', response.data.related_searches);
      console.log('API response data:', {
        hasRelatedSearches: !!response.data.related_searches && response.data.related_searches.length > 0,
        relatedSearchesCount: response.data.related_searches ? response.data.related_searches.length : 0,
        relatedSearchesSample: response.data.related_searches ? response.data.related_searches.slice(0, 2) : []
      });
      
      // Extract conversation context if available
      if (response.data.conversation_context) {
        setConversationContext(response.data.conversation_context);
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
            isError: true
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
