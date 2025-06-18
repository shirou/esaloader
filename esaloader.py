#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
esa.io Article Downloader CLI Tool

This tool downloads articles from esa.io based on search queries and saves them locally.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
import io


class EsaClient:
    """esa.io API client for article retrieval"""
    
    def __init__(self, access_token: str, team_name: str):
        """
        Initialize the esa.io API client
        
        Args:
            access_token: Personal access token for esa.io
            team_name: Team name in esa.io
        """
        self.access_token = access_token
        self.team_name = team_name
        self.base_url = "https://api.esa.io"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request to esa.io API with retry logic
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            urllib.error.HTTPError: For HTTP errors
            urllib.error.URLError: For network errors
        """
        url = f"{self.base_url}{endpoint}"
        
        if params:
            # Convert params to query string with proper encoding
            query_params = []
            for key, value in params.items():
                if value is not None:
                    # Handle special encoding for search query
                    if key == 'q':
                        encoded_value = urllib.parse.quote(str(value), safe='')
                    else:
                        encoded_value = urllib.parse.quote(str(value))
                    query_params.append(f"{key}={encoded_value}")
            if query_params:
                url += "?" + "&".join(query_params)
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                request = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(request) as response:
                    return json.loads(response.read().decode('utf-8'))
                    
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limit
                    # Get retry after header
                    retry_after = e.headers.get('Retry-After', '60')
                    wait_time = int(retry_after)
                    print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif e.code == 401:
                    print("Authentication error: Invalid access token")
                    sys.exit(1)
                elif e.code == 404:
                    raise e
                elif e.code >= 500:
                    if attempt < max_retries - 1:
                        print(f"Server error ({e.code}). Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise e
                else:
                    raise e
                    
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    print(f"Network error: {e.reason}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise e
                    
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")
        
    def search_posts(self, query: Optional[str] = None, page: int = 1, 
                    per_page: int = 100) -> Dict[str, Any]:
        """
        Search for posts with optional query
        
        Args:
            query: Search query (optional)
            page: Page number
            per_page: Number of items per page (max 100)
            
        Returns:
            API response containing posts and pagination info
        """
        endpoint = f"/v1/teams/{self.team_name}/posts"
        params = {
            "page": page,
            "per_page": min(per_page, 100)
        }
        if query:
            params["q"] = query
            
        return self._request(endpoint, params)
        
    def get_post(self, post_number: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific post
        
        Args:
            post_number: Post number
            
        Returns:
            Post details
        """
        endpoint = f"/v1/teams/{self.team_name}/posts/{post_number}"
        return self._request(endpoint)


class ImageDownloader:
    """Handles downloading and processing images from esa.io articles"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the image downloader
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.downloaded_images = {}  # Cache to avoid duplicate downloads
        
    def extract_images(self, markdown_text: str) -> List[Dict[str, str]]:
        """
        Extract image information from HTML img tags in markdown
        
        Args:
            markdown_text: Markdown text containing HTML img tags
            
        Returns:
            List of image information dictionaries
        """
        # Pattern to match img tags with src and optional width
        pattern = r'<img[^>]*\s+src="([^"]+)"[^>]*(?:\s+width="([^"]+)")?[^>]*>'
        matches = re.findall(pattern, markdown_text, re.IGNORECASE)
        
        images = []
        for match in matches:
            src_url = match[0]
            width = match[1] if match[1] else None
            images.append({
                'src': src_url,
                'width': width,
                'original_tag': re.search(
                    r'<img[^>]*\s+src="' + re.escape(src_url) + r'"[^>]*>',
                    markdown_text,
                    re.IGNORECASE
                ).group(0) if re.search(
                    r'<img[^>]*\s+src="' + re.escape(src_url) + r'"[^>]*>',
                    markdown_text,
                    re.IGNORECASE
                ) else ''
            })
            
        return images
        
    def download_image(self, url: str, target_dir: Path) -> Optional[str]:
        """
        Download image from URL to target directory
        
        Args:
            url: Image URL
            target_dir: Target directory path
            
        Returns:
            Local filename if successful, None if failed
        """
        try:
            # Extract filename from URL
            parsed_url = urllib.parse.urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            
            # If no filename in path, generate one
            if not original_filename or '.' not in original_filename:
                original_filename = f"image_{hash(url) % 10000}.png"
                
            # Ensure unique filename
            filename = original_filename
            counter = 1
            while (target_dir / filename).exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1
                
            target_path = target_dir / filename
            
            # Download image
            request = urllib.request.Request(url)
            with urllib.request.urlopen(request) as response:
                image_data = response.read()
                
            # Save original image temporarily
            with open(target_path, 'wb') as f:
                f.write(image_data)
                
            if self.verbose:
                print(f"Downloaded image: {filename}")
                
            return filename
            
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
            return None
            
    def resize_image(self, image_path: Path, target_width: int) -> bool:
        """
        Resize image to target width while maintaining aspect ratio
        
        Args:
            image_path: Path to image file
            target_width: Target width in pixels
            
        Returns:
            True if successful, False if failed
        """
        try:
            with Image.open(image_path) as img:
                # Calculate new height maintaining aspect ratio
                aspect_ratio = img.height / img.width
                target_height = int(target_width * aspect_ratio)
                
                # Resize image
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                resized_img.save(image_path, optimize=True)
                
                if self.verbose:
                    print(f"Resized image {image_path.name} to {target_width}x{target_height}")
                    
                return True
                
        except Exception as e:
            print(f"Failed to resize image {image_path}: {e}")
            return False
            
    def process_images(self, markdown_text: str, target_dir: Path, 
                      images_subdir: bool = False) -> str:
        """
        Process all images in markdown text
        
        Args:
            markdown_text: Original markdown text
            target_dir: Directory to save images
            images_subdir: If True, save images in 'images' subdirectory
            
        Returns:
            Modified markdown text with updated image links
        """
        images = self.extract_images(markdown_text)
        if not images:
            return markdown_text
            
        # Determine image directory
        if images_subdir:
            image_dir = target_dir / "images"
            image_dir.mkdir(exist_ok=True)
            relative_prefix = "images/"
        else:
            image_dir = target_dir
            relative_prefix = ""
            
        modified_text = markdown_text
        
        for image_info in images:
            url = image_info['src']
            width = image_info['width']
            original_tag = image_info['original_tag']
            
            # Download image
            filename = self.download_image(url, image_dir)
            if not filename:
                continue
                
            image_path = image_dir / filename
            
            # Resize if width is specified
            if width and width.isdigit():
                target_width = int(width)
                self.resize_image(image_path, target_width)
                
            # Create new image tag with local path
            relative_path = relative_prefix + filename
            new_tag = f'<img src="{relative_path}"'
            if width:
                new_tag += f' width="{width}"'
            new_tag += '>'
            
            # Replace original tag with new tag
            modified_text = modified_text.replace(original_tag, new_tag)
            
        return modified_text


class PostDownloader:
    """Handles downloading and saving posts to local filesystem"""
    
    def __init__(self, output_dir: str, verbose: bool = False, images_subdir: bool = False):
        """
        Initialize the downloader
        
        Args:
            output_dir: Output directory path
            verbose: Enable verbose logging
            images_subdir: If True, save images in 'images' subdirectories
        """
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.images_subdir = images_subdir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_downloader = ImageDownloader(verbose)
        
    def sanitize_path(self, path: str) -> str:
        """
        Sanitize file/directory name for filesystem
        
        Args:
            path: Original path
            
        Returns:
            Sanitized path safe for filesystem
        """
        # Replace characters that are invalid in file systems
        replacements = {
            '/': '_',
            '\\': '_',
            ':': '-',
            '*': '_',
            '?': '_',
            '"': "'",
            '<': '(',
            '>': ')',
            '|': '_',
            '\n': ' ',
            '\r': ' ',
            '\t': ' '
        }
        
        for char, replacement in replacements.items():
            path = path.replace(char, replacement)
            
        # Remove leading/trailing spaces and dots
        path = path.strip(' .')
        
        # Ensure the path is not empty
        if not path:
            path = "unnamed"
            
        # Truncate if too long (considering UTF-8 encoding)
        max_bytes = 255
        while len(path.encode('utf-8')) > max_bytes:
            path = path[:-1]
            
        return path
        
    def save_post(self, post: Dict[str, Any]) -> str:
        """
        Save a post to the filesystem
        
        Args:
            post: Post data from API
            
        Returns:
            Path to saved file
        """
        # Extract post details
        number = post['number']
        name = post['name']
        category = post.get('category', '')
        body_md = post.get('body_md', '')
        tags = post.get('tags', [])
        created_at = post.get('created_at', '')
        updated_at = post.get('updated_at', '')
        created_by = post.get('created_by', {}).get('screen_name', '')
        updated_by = post.get('updated_by', {}).get('screen_name', '')
        wip = post.get('wip', False)
        
        # Create directory structure based on category
        if category:
            # Split category and sanitize each part
            category_parts = [self.sanitize_path(part) for part in category.split('/')]
            post_dir = self.output_dir / Path(*category_parts)
        else:
            post_dir = self.output_dir
            
        post_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        sanitized_name = self.sanitize_path(name)
        filename = f"{number}_{sanitized_name}.md"
        filepath = post_dir / filename
        
        # Create frontmatter
        frontmatter = f"""---
number: {number}
title: {name}
tags: {json.dumps(tags, ensure_ascii=False)}
category: {category}
created_at: {created_at}
updated_at: {updated_at}
created_by: {created_by}
updated_by: {updated_by}
wip: {str(wip).lower()}
---

"""
        
        # Process images in body_md
        processed_body = self.image_downloader.process_images(
            body_md, post_dir, self.images_subdir
        )
        
        # Write file
        content = frontmatter + processed_body
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            if self.verbose:
                print(f"Saved: {filepath}")
            return str(filepath)
        except IOError as e:
            print(f"Error saving file {filepath}: {e}")
            raise
            
    def download_all(self, client: EsaClient, query: Optional[str] = None,
                    limit: Optional[int] = None, dry_run: bool = False) -> List[str]:
        """
        Download all posts matching the query
        
        Args:
            client: EsaClient instance
            query: Search query
            limit: Maximum number of posts to download
            dry_run: If True, only list posts without downloading
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        page = 1
        total_downloaded = 0
        
        print(f"Fetching posts{' with query: ' + query if query else ''}...")
        
        while True:
            # Fetch posts
            response = client.search_posts(query=query, page=page)
            posts = response.get('posts', [])
            total_count = response.get('total_count', 0)
            
            if page == 1:
                print(f"Found {total_count} posts")
                if dry_run:
                    print("\nDry run mode - listing posts without downloading:")
                    print("-" * 60)
            
            if not posts:
                break
                
            for post in posts:
                if limit and total_downloaded >= limit:
                    print(f"\nReached limit of {limit} posts")
                    return saved_files
                    
                if dry_run:
                    print(f"[{post['number']}] {post['name']}")
                    if post.get('category'):
                        print(f"    Category: {post['category']}")
                    if post.get('tags'):
                        print(f"    Tags: {', '.join(post['tags'])}")
                else:
                    # Get full post details
                    if self.verbose:
                        print(f"Fetching post {post['number']}: {post['name']}")
                        
                    try:
                        full_post = client.get_post(post['number'])
                        filepath = self.save_post(full_post)
                        saved_files.append(filepath)
                    except Exception as e:
                        print(f"Error processing post {post['number']}: {e}")
                        continue
                        
                total_downloaded += 1
                
            # Check if there are more pages
            next_page = response.get('next_page')
            if not next_page:
                break
                
            page += 1
            
            # Small delay to be nice to the API
            if not dry_run:
                time.sleep(0.5)
                
        if not dry_run:
            print(f"\nDownloaded {len(saved_files)} posts to {self.output_dir}")
            
        return saved_files


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="Download articles from esa.io",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all posts
  %(prog)s -t your_team
  
  # Download posts with specific tag
  %(prog)s -t your_team -q "tag:important"
  
  # Download posts in specific category (Japanese supported)
  %(prog)s -t your_team -q "category:開発/仕様書"
  
  # Dry run to see what would be downloaded
  %(prog)s -t your_team -q "tag:public" --dry-run
"""
    )
    
    parser.add_argument('-t', '--team', required=True,
                       help='esa.io team name')
    parser.add_argument('-q', '--query',
                       help='Search query (supports Japanese)')
    parser.add_argument('-o', '--output', default='./esa_posts',
                       help='Output directory (default: ./esa_posts)')
    parser.add_argument('--dry-run', action='store_true',
                       help='List posts without downloading')
    parser.add_argument('--limit', type=int,
                       help='Maximum number of posts to download')
    parser.add_argument('--images-dir', action='store_true',
                       help='Save images in "images" subdirectory instead of alongside articles')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Get access token from environment
    access_token = os.environ.get('ESA_ACCESS_TOKEN')
    if not access_token:
        print("Error: ESA_ACCESS_TOKEN environment variable not set")
        print("Please set it with your esa.io personal access token")
        sys.exit(1)
        
    # Create client and downloader
    client = EsaClient(access_token, args.team)
    downloader = PostDownloader(args.output, args.verbose, args.images_dir)
    
    try:
        # Download posts
        downloader.download_all(
            client,
            query=args.query,
            limit=args.limit,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()