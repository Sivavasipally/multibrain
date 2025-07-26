"""
Command Line Interface for RAG Chatbot API Client
"""

import argparse
import json
import sys
import os
from typing import Optional
from python_client import RagChatbotClient


class RagChatbotCLI:
    """Command line interface for RAG Chatbot"""
    
    def __init__(self):
        self.client: Optional[RagChatbotClient] = None
        self.config_file = os.path.expanduser('~/.ragchatbot/config.json')
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    base_url = config.get('base_url', 'http://localhost:5000/api')
                    token = config.get('token')
                    self.client = RagChatbotClient(base_url, token)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    
    def save_config(self, base_url: str, token: str = None):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {'base_url': base_url}
            if token:
                config['token'] = token
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def ensure_client(self, base_url: str = None):
        """Ensure client is initialized"""
        if not self.client:
            url = base_url or 'http://localhost:5000/api'
            self.client = RagChatbotClient(url)
    
    def login(self, args):
        """Login command"""
        self.ensure_client(args.base_url)
        
        try:
            token = self.client.authenticate(args.username, args.password)
            self.save_config(self.client.base_url, token)
            print(f"✅ Successfully logged in as {args.username}")
            print(f"Token saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            sys.exit(1)
    
    def register(self, args):
        """Register command"""
        self.ensure_client(args.base_url)
        
        try:
            result = self.client.register(args.username, args.email, args.password)
            print(f"✅ Successfully registered user {args.username}")
            print("Please login to get an access token")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            sys.exit(1)
    
    def list_contexts(self, args):
        """List contexts command"""
        if not self.client or not self.client.token:
            print("❌ Please login first")
            sys.exit(1)
        
        try:
            contexts = self.client.get_contexts()
            
            if not contexts:
                print("No contexts found")
                return
            
            print(f"\n📁 Found {len(contexts)} contexts:")
            print("-" * 80)
            
            for ctx in contexts:
                status_emoji = {
                    'ready': '✅',
                    'processing': '⏳',
                    'error': '❌',
                    'pending': '⏸️'
                }.get(ctx.status, '❓')
                
                print(f"{status_emoji} {ctx.name} (ID: {ctx.id})")
                print(f"   Type: {ctx.source_type}")
                print(f"   Status: {ctx.status}")
                print(f"   Chunks: {ctx.total_chunks or 0}")
                print(f"   Created: {ctx.created_at}")
                print()
        
        except Exception as e:
            print(f"❌ Failed to list contexts: {e}")
            sys.exit(1)
    
    def create_context(self, args):
        """Create context command"""
        if not self.client or not self.client.token:
            print("❌ Please login first")
            sys.exit(1)
        
        try:
            context = self.client.create_context(
                name=args.name,
                source_type=args.type,
                description=args.description
            )
            
            print(f"✅ Created context '{context.name}' (ID: {context.id})")
            print(f"   Type: {context.source_type}")
            print(f"   Status: {context.status}")
        
        except Exception as e:
            print(f"❌ Failed to create context: {e}")
            sys.exit(1)
    
    def upload_files(self, args):
        """Upload files command"""
        if not self.client or not self.client.token:
            print("❌ Please login first")
            sys.exit(1)
        
        # Check if files exist
        for file_path in args.files:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                sys.exit(1)
        
        try:
            result = self.client.upload_files(args.context_id, args.files)
            print(f"✅ Successfully uploaded {len(args.files)} files to context {args.context_id}")
        
        except Exception as e:
            print(f"❌ Failed to upload files: {e}")
            sys.exit(1)
    
    def chat(self, args):
        """Interactive chat command"""
        if not self.client or not self.client.token:
            print("❌ Please login first")
            sys.exit(1)
        
        try:
            # Create or get chat session
            if args.session_id:
                session = self.client.get_chat_session(args.session_id)
            else:
                session = self.client.create_chat_session(args.title or "CLI Chat")
                print(f"📝 Created new chat session: {session.title} (ID: {session.id})")
            
            print(f"💬 Starting chat session {session.id}")
            print("Type 'quit' or 'exit' to end the session")
            print("-" * 50)
            
            while True:
                try:
                    message = input("\n🧑 You: ").strip()
                    
                    if message.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if not message:
                        continue
                    
                    print("🤖 Assistant: ", end="", flush=True)
                    
                    response = self.client.send_message(
                        session.id,
                        message,
                        context_ids=args.context_ids
                    )
                    
                    print(response.content)
                
                except KeyboardInterrupt:
                    print("\n👋 Chat session ended")
                    break
                except EOFError:
                    print("\n👋 Chat session ended")
                    break
        
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            sys.exit(1)
    
    def health_check(self, args):
        """Health check command"""
        self.ensure_client(args.base_url)
        
        try:
            health = self.client.health_check()
            print(f"✅ API is healthy")
            print(f"Status: {health.get('status', 'unknown')}")
            print(f"Version: {health.get('version', 'unknown')}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='RAG Chatbot CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000/api',
        help='API base URL'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to the API')
    login_parser.add_argument('username', help='Username')
    login_parser.add_argument('password', help='Password')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register new user')
    register_parser.add_argument('username', help='Username')
    register_parser.add_argument('email', help='Email address')
    register_parser.add_argument('password', help='Password')
    
    # List contexts command
    list_parser = subparsers.add_parser('contexts', help='List all contexts')
    
    # Create context command
    create_parser = subparsers.add_parser('create-context', help='Create new context')
    create_parser.add_argument('name', help='Context name')
    create_parser.add_argument('type', choices=['files', 'repo', 'database'], help='Context type')
    create_parser.add_argument('--description', help='Context description')
    
    # Upload files command
    upload_parser = subparsers.add_parser('upload', help='Upload files to context')
    upload_parser.add_argument('context_id', type=int, help='Context ID')
    upload_parser.add_argument('files', nargs='+', help='Files to upload')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat')
    chat_parser.add_argument('--session-id', type=int, help='Existing session ID')
    chat_parser.add_argument('--title', help='Chat session title')
    chat_parser.add_argument('--context-ids', type=int, nargs='+', help='Context IDs to use')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check API health')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = RagChatbotCLI()
    
    # Route to appropriate command handler
    if args.command == 'login':
        cli.login(args)
    elif args.command == 'register':
        cli.register(args)
    elif args.command == 'contexts':
        cli.list_contexts(args)
    elif args.command == 'create-context':
        cli.create_context(args)
    elif args.command == 'upload':
        cli.upload_files(args)
    elif args.command == 'chat':
        cli.chat(args)
    elif args.command == 'health':
        cli.health_check(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
