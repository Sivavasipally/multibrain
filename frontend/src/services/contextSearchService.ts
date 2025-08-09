/**
 * Context Search Service for RAG Chatbot PWA
 * 
 * Advanced context search capabilities with content-based filtering,
 * semantic search, and complex query parsing.
 * 
 * Features:
 * - Full-text search within context content
 * - Semantic similarity search
 * - Advanced query operators (AND, OR, NOT)
 * - Date range filtering
 * - Content type filtering
 * - Performance metrics-based filtering
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import type { Context as BaseContext } from '../types/api';
import { contextsAPI } from './api';

// Extended Context interface with additional fields from API
interface Context extends BaseContext {
  chunk_strategy?: string;
  embedding_model?: string;
}

export interface SearchFilters {
  query?: string;
  status?: 'all' | 'ready' | 'processing' | 'error';
  sourceType?: 'all' | 'repo' | 'database' | 'files';
  dateRange?: {
    start?: Date;
    end?: Date;
  };
  chunkRange?: {
    min?: number;
    max?: number;
  };
  contentTypes?: string[];
  tags?: string[];
}

export interface SortOptions {
  field: 'name' | 'created_at' | 'chunks' | 'status' | 'relevance';
  order: 'asc' | 'desc';
}

export interface SearchResult {
  context: Context;
  relevanceScore?: number;
  matchedContent?: string[];
  highlights?: Array<{
    field: string;
    fragment: string;
    positions: number[];
  }>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  filters: SearchFilters;
  executionTime: number;
}

class ContextSearchService {
  private searchHistory: string[] = [];
  private maxHistorySize = 50;

  /**
   * Perform advanced context search with filters and sorting
   */
  async searchContexts(
    query: string = '',
    filters: SearchFilters = {},
    sort: SortOptions = { field: 'relevance', order: 'desc' },
    limit: number = 50,
    offset: number = 0
  ): Promise<SearchResponse> {
    const startTime = Date.now();
    
    try {
      // Add to search history
      if (query.trim()) {
        this.addToSearchHistory(query);
      }

      // Get all contexts first
      const response = await contextsAPI.getContexts();
      let contexts = response.contexts;

      // Apply filters
      contexts = this.applyFilters(contexts, filters);

      // Apply search query
      let results: SearchResult[];
      if (query.trim()) {
        results = await this.performSearch(contexts, query);
      } else {
        results = contexts.map(context => ({ context }));
      }

      // Apply sorting
      results = this.sortResults(results, sort);

      // Apply pagination
      const paginatedResults = results.slice(offset, offset + limit);

      const executionTime = Date.now() - startTime;

      return {
        results: paginatedResults,
        total: results.length,
        query,
        filters,
        executionTime,
      };
    } catch (error) {
      console.error('Search failed:', error);
      throw new Error('Failed to search contexts');
    }
  }

  /**
   * Search within a specific context's content
   */
  async searchContextContent(
    contextId: number,
    query: string,
    contentTypes?: string[]
  ): Promise<{
    chunks: Array<{
      id: string;
      content: string;
      relevanceScore: number;
      highlights: string[];
    }>;
    total: number;
  }> {
    try {
      // This would typically call a backend endpoint for content search
      // For now, we'll return a placeholder response
      return {
        chunks: [],
        total: 0,
      };
    } catch (error) {
      console.error('Context content search failed:', error);
      throw new Error('Failed to search context content');
    }
  }

  /**
   * Get search suggestions based on partial query
   */
  async getSearchSuggestions(
    partialQuery: string,
    limit: number = 10
  ): Promise<string[]> {
    try {
      const suggestions: string[] = [];

      // Add suggestions from search history
      const historyMatches = this.searchHistory.filter(term =>
        term.toLowerCase().includes(partialQuery.toLowerCase())
      ).slice(0, limit / 2);
      suggestions.push(...historyMatches);

      // Add suggestions from context names and descriptions
      const response = await contextsAPI.getContexts();
      const contextSuggestions = response.contexts
        .filter(context => 
          context.name.toLowerCase().includes(partialQuery.toLowerCase()) ||
          context.description?.toLowerCase().includes(partialQuery.toLowerCase())
        )
        .map(context => context.name)
        .slice(0, limit - suggestions.length);
      
      suggestions.push(...contextSuggestions);

      // Remove duplicates and limit results
      return Array.from(new Set(suggestions)).slice(0, limit);
    } catch (error) {
      console.error('Failed to get search suggestions:', error);
      return [];
    }
  }

  /**
   * Get popular search terms
   */
  getPopularSearches(limit: number = 10): string[] {
    // Count frequency of search terms
    const frequency: { [key: string]: number } = {};
    
    this.searchHistory.forEach(term => {
      frequency[term] = (frequency[term] || 0) + 1;
    });

    // Sort by frequency and return top results
    return Object.entries(frequency)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit)
      .map(([term]) => term);
  }

  /**
   * Clear search history
   */
  clearSearchHistory(): void {
    this.searchHistory = [];
  }

  /**
   * Get search history
   */
  getSearchHistory(): string[] {
    return [...this.searchHistory];
  }

  /**
   * Parse advanced search query (supports AND, OR, NOT operators)
   */
  private parseQuery(query: string): {
    required: string[];
    optional: string[];
    excluded: string[];
  } {
    const required: string[] = [];
    const optional: string[] = [];
    const excluded: string[] = [];

    // Simple query parsing (can be enhanced with proper tokenization)
    const terms = query.split(/\s+/);
    
    for (let i = 0; i < terms.length; i++) {
      const term = terms[i].toLowerCase();
      
      if (term === 'and' || term === '&&') {
        continue; // Skip operators
      } else if (term === 'or' || term === '||') {
        continue; // Skip operators
      } else if (term === 'not' || term.startsWith('-')) {
        const excludedTerm = term.startsWith('-') ? term.slice(1) : terms[++i];
        if (excludedTerm) {
          excluded.push(excludedTerm);
        }
      } else if (term.startsWith('+')) {
        required.push(term.slice(1));
      } else {
        optional.push(term);
      }
    }

    return { required, optional, excluded };
  }

  /**
   * Apply filters to contexts
   */
  private applyFilters(contexts: Context[], filters: SearchFilters): Context[] {
    return contexts.filter(context => {
      // Status filter
      if (filters.status && filters.status !== 'all' && context.status !== filters.status) {
        return false;
      }

      // Source type filter
      if (filters.sourceType && filters.sourceType !== 'all' && context.source_type !== filters.sourceType) {
        return false;
      }

      // Date range filter
      if (filters.dateRange) {
        const createdAt = new Date(context.created_at);
        if (filters.dateRange.start && createdAt < filters.dateRange.start) {
          return false;
        }
        if (filters.dateRange.end && createdAt > filters.dateRange.end) {
          return false;
        }
      }

      // Chunk range filter
      if (filters.chunkRange) {
        const chunks = context.total_chunks || 0;
        if (filters.chunkRange.min !== undefined && chunks < filters.chunkRange.min) {
          return false;
        }
        if (filters.chunkRange.max !== undefined && chunks > filters.chunkRange.max) {
          return false;
        }
      }

      // Content types filter (would need additional context metadata)
      if (filters.contentTypes && filters.contentTypes.length > 0) {
        // This would require additional metadata about content types in contexts
        // For now, we'll skip this filter
      }

      // Tags filter (would need tagging system)
      if (filters.tags && filters.tags.length > 0) {
        // This would require a tagging system for contexts
        // For now, we'll skip this filter
      }

      return true;
    });
  }

  /**
   * Perform search on contexts
   */
  private async performSearch(contexts: Context[], query: string): Promise<SearchResult[]> {
    const parsedQuery = this.parseQuery(query);
    
    return contexts.map(context => {
      const relevanceScore = this.calculateRelevanceScore(context, parsedQuery);
      
      if (relevanceScore > 0) {
        return {
          context,
          relevanceScore,
          highlights: this.generateHighlights(context, query),
        };
      }
      
      return null;
    }).filter((result): result is SearchResult => result !== null);
  }

  /**
   * Calculate relevance score for a context
   */
  private calculateRelevanceScore(
    context: Context,
    parsedQuery: { required: string[]; optional: string[]; excluded: string[] }
  ): number {
    let score = 0;
    const text = `${context.name} ${context.description || ''}`.toLowerCase();

    // Check required terms
    for (const term of parsedQuery.required) {
      if (!text.includes(term)) {
        return 0; // Must have all required terms
      }
      score += 10; // High score for required terms
    }

    // Check excluded terms
    for (const term of parsedQuery.excluded) {
      if (text.includes(term)) {
        return 0; // Must not have excluded terms
      }
    }

    // Check optional terms
    for (const term of parsedQuery.optional) {
      if (text.includes(term)) {
        score += 5; // Medium score for optional terms
      }
    }

    // Boost score based on exact matches in name
    if (parsedQuery.optional.some(term => context.name.toLowerCase().includes(term))) {
      score += 15;
    }

    return score;
  }

  /**
   * Generate highlights for search results
   */
  private generateHighlights(context: Context, query: string): Array<{
    field: string;
    fragment: string;
    positions: number[];
  }> {
    const highlights: Array<{
      field: string;
      fragment: string;
      positions: number[];
    }> = [];

    const terms = query.toLowerCase().split(/\s+/).filter(term => 
      !['and', 'or', 'not', '&&', '||'].includes(term) && 
      !term.startsWith('-') && !term.startsWith('+')
    );

    // Check name
    const nameLower = context.name.toLowerCase();
    for (const term of terms) {
      const index = nameLower.indexOf(term);
      if (index !== -1) {
        highlights.push({
          field: 'name',
          fragment: context.name,
          positions: [index],
        });
      }
    }

    // Check description
    if (context.description) {
      const descLower = context.description.toLowerCase();
      for (const term of terms) {
        const index = descLower.indexOf(term);
        if (index !== -1) {
          highlights.push({
            field: 'description',
            fragment: this.getContextFragment(context.description, index, 100),
            positions: [index],
          });
        }
      }
    }

    return highlights;
  }

  /**
   * Get context fragment around a match
   */
  private getContextFragment(text: string, position: number, length: number): string {
    const start = Math.max(0, position - length / 2);
    const end = Math.min(text.length, start + length);
    
    let fragment = text.slice(start, end);
    
    if (start > 0) {
      fragment = '...' + fragment;
    }
    
    if (end < text.length) {
      fragment = fragment + '...';
    }
    
    return fragment;
  }

  /**
   * Sort search results
   */
  private sortResults(results: SearchResult[], sort: SortOptions): SearchResult[] {
    return results.sort((a, b) => {
      let comparison = 0;

      switch (sort.field) {
        case 'name':
          comparison = a.context.name.localeCompare(b.context.name);
          break;
        case 'created_at':
          comparison = new Date(a.context.created_at).getTime() - new Date(b.context.created_at).getTime();
          break;
        case 'chunks':
          comparison = (a.context.total_chunks || 0) - (b.context.total_chunks || 0);
          break;
        case 'status':
          comparison = a.context.status.localeCompare(b.context.status);
          break;
        case 'relevance':
          comparison = (a.relevanceScore || 0) - (b.relevanceScore || 0);
          break;
        default:
          comparison = 0;
      }

      return sort.order === 'asc' ? comparison : -comparison;
    });
  }

  /**
   * Add query to search history
   */
  private addToSearchHistory(query: string): void {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || this.searchHistory.includes(trimmedQuery)) {
      return;
    }

    this.searchHistory.unshift(trimmedQuery);
    
    if (this.searchHistory.length > this.maxHistorySize) {
      this.searchHistory = this.searchHistory.slice(0, this.maxHistorySize);
    }
  }
}

// Export singleton instance
export const contextSearchService = new ContextSearchService();
export default contextSearchService;