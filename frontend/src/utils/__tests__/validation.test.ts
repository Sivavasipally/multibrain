/**
 * Comprehensive tests for validation utilities
 */

import {
  validateEmail,
  validateUsername,
  validatePassword,
  validateContextName,
  validateRepositoryUrl,
  validateFileUpload,
  validateChatMessage,
  validateSearchQuery
} from '../validation';

describe('Validation Utilities', () => {
  describe('validateEmail', () => {
    it('validates correct email addresses', () => {
      const validEmails = [
        'user@example.com',
        'test.user@domain.co.uk',
        'user+tag@example.org',
        'firstname.lastname@company.com',
        'user123@test-domain.com'
      ];

      validEmails.forEach(email => {
        expect(validateEmail(email)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid email addresses', () => {
      const invalidEmails = [
        '',
        'notanemail',
        '@domain.com',
        'user@',
        'user@.com',
        'user..user@domain.com',
        'user@domain',
        'user name@domain.com'
      ];

      invalidEmails.forEach(email => {
        const result = validateEmail(email);
        expect(result.isValid).toBe(false);
        expect(result.error).toBeTruthy();
      });
    });

    it('handles edge cases', () => {
      expect(validateEmail(null as any)).toEqual({
        isValid: false,
        error: 'Email is required'
      });

      expect(validateEmail(undefined as any)).toEqual({
        isValid: false,
        error: 'Email is required'
      });
    });
  });

  describe('validateUsername', () => {
    it('validates correct usernames', () => {
      const validUsernames = [
        'user123',
        'testuser',
        'user_name',
        'User-Name',
        'a',
        'a' + 'b'.repeat(29) // 30 characters
      ];

      validUsernames.forEach(username => {
        expect(validateUsername(username)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid usernames', () => {
      expect(validateUsername('')).toEqual({
        isValid: false,
        error: 'Username is required'
      });

      expect(validateUsername('ab')).toEqual({
        isValid: false,
        error: 'Username must be at least 3 characters long'
      });

      expect(validateUsername('a'.repeat(31))).toEqual({
        isValid: false,
        error: 'Username must be less than 30 characters long'
      });

      expect(validateUsername('user@domain')).toEqual({
        isValid: false,
        error: 'Username can only contain letters, numbers, hyphens, and underscores'
      });

      expect(validateUsername('user space')).toEqual({
        isValid: false,
        error: 'Username can only contain letters, numbers, hyphens, and underscores'
      });
    });
  });

  describe('validatePassword', () => {
    it('validates strong passwords', () => {
      const validPasswords = [
        'Password123!',
        'MySecureP@ss1',
        'Str0ng_Password',
        'Complex123$',
        'Valid8Password!'
      ];

      validPasswords.forEach(password => {
        expect(validatePassword(password)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects weak passwords', () => {
      expect(validatePassword('')).toEqual({
        isValid: false,
        error: 'Password is required'
      });

      expect(validatePassword('short')).toEqual({
        isValid: false,
        error: 'Password must be at least 8 characters long'
      });

      expect(validatePassword('alllowercase')).toEqual({
        isValid: false,
        error: 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
      });

      expect(validatePassword('ALLUPPERCASE')).toEqual({
        isValid: false,
        error: 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
      });

      expect(validatePassword('NoNumbers!')).toEqual({
        isValid: false,
        error: 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
      });
    });

    it('validates password complexity options', () => {
      const options = { requireSpecialChar: true };

      expect(validatePassword('Password123', options)).toEqual({
        isValid: false,
        error: 'Password must contain at least one special character'
      });

      expect(validatePassword('Password123!', options)).toEqual({
        isValid: true,
        error: null
      });
    });
  });

  describe('validateContextName', () => {
    it('validates correct context names', () => {
      const validNames = [
        'My Context',
        'Project Documentation',
        'API-Reference_v1',
        'Context123',
        'A'
      ];

      validNames.forEach(name => {
        expect(validateContextName(name)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid context names', () => {
      expect(validateContextName('')).toEqual({
        isValid: false,
        error: 'Context name is required'
      });

      expect(validateContextName('   ')).toEqual({
        isValid: false,
        error: 'Context name is required'
      });

      expect(validateContextName('a'.repeat(101))).toEqual({
        isValid: false,
        error: 'Context name must be less than 100 characters long'
      });

      expect(validateContextName('Invalid/Name')).toEqual({
        isValid: false,
        error: 'Context name contains invalid characters'
      });
    });
  });

  describe('validateRepositoryUrl', () => {
    it('validates correct repository URLs', () => {
      const validUrls = [
        'https://github.com/user/repo',
        'https://github.com/user/repo.git',
        'https://gitlab.com/user/project',
        'https://bitbucket.org/user/repository',
        'git@github.com:user/repo.git'
      ];

      validUrls.forEach(url => {
        expect(validateRepositoryUrl(url)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid repository URLs', () => {
      expect(validateRepositoryUrl('')).toEqual({
        isValid: false,
        error: 'Repository URL is required'
      });

      expect(validateRepositoryUrl('not-a-url')).toEqual({
        isValid: false,
        error: 'Please enter a valid repository URL'
      });

      expect(validateRepositoryUrl('http://example.com')).toEqual({
        isValid: false,
        error: 'Please enter a valid Git repository URL'
      });

      expect(validateRepositoryUrl('ftp://github.com/user/repo')).toEqual({
        isValid: false,
        error: 'Please enter a valid Git repository URL'
      });
    });
  });

  describe('validateFileUpload', () => {
    it('validates acceptable files', () => {
      const validFiles = [
        new File(['content'], 'document.txt', { type: 'text/plain' }),
        new File(['content'], 'data.json', { type: 'application/json' }),
        new File(['content'], 'script.py', { type: 'text/x-python' }),
        new File(['content'], 'readme.md', { type: 'text/markdown' }),
        new File(['content'], 'document.pdf', { type: 'application/pdf' })
      ];

      validFiles.forEach(file => {
        expect(validateFileUpload(file)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects files that are too large', () => {
      const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
      const largeFile = new File([largeContent], 'large.txt', { type: 'text/plain' });

      expect(validateFileUpload(largeFile)).toEqual({
        isValid: false,
        error: 'File size must be less than 10MB'
      });
    });

    it('rejects unsupported file types', () => {
      const unsupportedFile = new File(['content'], 'virus.exe', { type: 'application/x-msdownload' });

      expect(validateFileUpload(unsupportedFile)).toEqual({
        isValid: false,
        error: 'Unsupported file type. Please upload text files, documents, or source code.'
      });
    });

    it('handles files without extensions', () => {
      const noExtFile = new File(['content'], 'README', { type: 'text/plain' });

      expect(validateFileUpload(noExtFile)).toEqual({ isValid: true, error: null });
    });

    it('validates with custom options', () => {
      const options = { maxSizeBytes: 1024 * 1024 }; // 1MB
      const largeFile = new File(['x'.repeat(2 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });

      expect(validateFileUpload(largeFile, options)).toEqual({
        isValid: false,
        error: 'File size must be less than 1MB'
      });
    });
  });

  describe('validateChatMessage', () => {
    it('validates correct chat messages', () => {
      const validMessages = [
        'Hello, how are you?',
        'Can you explain this concept?',
        'What is machine learning?',
        'A',
        'Multi-line\nmessage\nwith\nbreaks'
      ];

      validMessages.forEach(message => {
        expect(validateChatMessage(message)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid chat messages', () => {
      expect(validateChatMessage('')).toEqual({
        isValid: false,
        error: 'Message cannot be empty'
      });

      expect(validateChatMessage('   ')).toEqual({
        isValid: false,
        error: 'Message cannot be empty'
      });

      expect(validateChatMessage('a'.repeat(5001))).toEqual({
        isValid: false,
        error: 'Message is too long (maximum 5000 characters)'
      });
    });

    it('validates with custom length limits', () => {
      const options = { maxLength: 100 };
      const longMessage = 'a'.repeat(101);

      expect(validateChatMessage(longMessage, options)).toEqual({
        isValid: false,
        error: 'Message is too long (maximum 100 characters)'
      });
    });
  });

  describe('validateSearchQuery', () => {
    it('validates correct search queries', () => {
      const validQueries = [
        'machine learning',
        'API documentation',
        'python functions',
        'a',
        'search with "quotes"',
        'query-with-dashes'
      ];

      validQueries.forEach(query => {
        expect(validateSearchQuery(query)).toEqual({ isValid: true, error: null });
      });
    });

    it('rejects invalid search queries', () => {
      expect(validateSearchQuery('')).toEqual({
        isValid: false,
        error: 'Search query cannot be empty'
      });

      expect(validateSearchQuery('   ')).toEqual({
        isValid: false,
        error: 'Search query cannot be empty'
      });

      expect(validateSearchQuery('a'.repeat(201))).toEqual({
        isValid: false,
        error: 'Search query is too long (maximum 200 characters)'
      });
    });

    it('validates with custom options', () => {
      const options = { minLength: 3 };

      expect(validateSearchQuery('ab', options)).toEqual({
        isValid: false,
        error: 'Search query must be at least 3 characters long'
      });

      expect(validateSearchQuery('abc', options)).toEqual({
        isValid: true,
        error: null
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('handles null and undefined inputs gracefully', () => {
      expect(validateEmail(null as any).isValid).toBe(false);
      expect(validateUsername(undefined as any).isValid).toBe(false);
      expect(validatePassword(null as any).isValid).toBe(false);
    });

    it('handles special characters in inputs', () => {
      expect(validateContextName('Test 🚀 Context')).toEqual({
        isValid: false,
        error: 'Context name contains invalid characters'
      });
    });

    it('trims whitespace appropriately', () => {
      expect(validateContextName('  Valid Name  ')).toEqual({
        isValid: true,
        error: null
      });
    });
  });
});