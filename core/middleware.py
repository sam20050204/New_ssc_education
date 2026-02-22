"""
Cache Control Middleware - Prevents excessive browser caching
Logging Middleware - Comprehensive request/response logging
"""
import logging
import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from datetime import datetime, timedelta

logger = logging.getLogger('core')


class LoggingMiddleware(MiddlewareMixin):
    """
    Log all HTTP requests and responses with timing information.
    Useful for debugging, performance monitoring, and audit trails.
    
    Logs:
    - Request method, path, user, client IP
    - Response status code
    - Total execution time
    - Errors with referrer information
    """
    
    def process_request(self, request):
        """Log incoming request"""
        request.start_time = time.time()
        
        # Log request details
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.info(
            f"→ {request.method} {request.path} | User: {user} | IP: {self.get_client_ip(request)}"
        )
        
        return None
    
    def process_response(self, request, response):
        """Log outgoing response with timing"""
        duration = time.time() - request.start_time if hasattr(request, 'start_time') else 0
        
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        status = response.status_code
        
        # Log response with emoji (green for 2xx, yellow for 3xx, red for 4xx/5xx)
        status_emoji = '✅' if 200 <= status < 300 else '⚠️' if 300 <= status < 400 else '❌'
        
        logger.info(
            f"← {status_emoji} {status} {request.method} {request.path} | "
            f"Time: {duration:.3f}s | User: {user}"
        )
        
        # Log errors
        if status >= 400:
            logger.error(
                f"ERROR: {status} {request.method} {request.path} | "
                f"Referrer: {request.META.get('HTTP_REFERER', 'N/A')}"
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get real client IP address (handles proxies)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to control browser cache behavior.
    Prevents excessive memory usage from browser cache.
    """
    
    def process_response(self, request, response):
        """
        Add cache-control headers to all responses.
        """
        
        # For API/AJAX requests - no cache
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        # For HTML pages - cache for 5 minutes only
        if 'text/html' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
            response['Pragma'] = 'cache'
            
            # Set expires header
            expires_time = datetime.utcnow() + timedelta(minutes=5)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
            
            # Add Last-Modified header for better caching
            if 'Last-Modified' not in response:
                current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                response['Last-Modified'] = current_time
        
        # For CSS files - cache for 1 hour (use versioning for updates)
        elif 'text/css' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hour
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For JavaScript files - cache for 1 hour (use versioning for updates)
        elif 'application/javascript' in response.get('Content-Type', '') or 'text/javascript' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hour
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For images - cache for 30 days (use versioning/CDN in production)
        elif 'image' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=2592000'  # 30 days
            expires_time = datetime.utcnow() + timedelta(days=30)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For all other responses - minimal caching
        else:
            response['Cache-Control'] = 'public, max-age=60'  # 1 minute
            expires_time = datetime.utcnow() + timedelta(minutes=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # Add security headers that help with cache
        if 'ETag' not in response:
            response['ETag'] = f'"{hash(response.content) % 100000}"'
        
        return response


class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware to disable caching for sensitive pages like login/dashboard.
    """
    
    def process_response(self, request, response):
        """
        Add no-cache headers for sensitive pages.
        """
        
        # List of paths that should never be cached
        no_cache_paths = [
            '/login/',
            '/logout/',
            '/dashboard/',
            '/api/',
            '/update/',
        ]
        
        # Check if current path matches any no-cache paths
        for path in no_cache_paths:
            if request.path.startswith(path):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                break
        
        return response

            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        # For HTML pages - cache for 5 minutes only
        if 'text/html' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
            response['Pragma'] = 'cache'
            
            # Set expires header
            expires_time = datetime.utcnow() + timedelta(minutes=5)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
            
            # Add Last-Modified header for better caching
            if 'Last-Modified' not in response:
                current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                response['Last-Modified'] = current_time
        
        # For CSS files - cache for 1 hour (use versioning for updates)
        elif 'text/css' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hour
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For JavaScript files - cache for 1 hour (use versioning for updates)
        elif 'application/javascript' in response.get('Content-Type', '') or 'text/javascript' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'  # 1 hour
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For images - cache for 30 days (use versioning/CDN in production)
        elif 'image' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=2592000'  # 30 days
            expires_time = datetime.utcnow() + timedelta(days=30)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # For all other responses - minimal caching
        else:
            response['Cache-Control'] = 'public, max-age=60'  # 1 minute
            expires_time = datetime.utcnow() + timedelta(minutes=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        # Add security headers that help with cache
        if 'ETag' not in response:
            response['ETag'] = f'"{hash(response.content) % 100000}"'
        
        return response


class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware to disable caching for sensitive pages like login/dashboard.
    """
    
    def process_response(self, request, response):
        """
        Add no-cache headers for sensitive pages.
        """
        
        # List of paths that should never be cached
        no_cache_paths = [
            '/login/',
            '/logout/',
            '/dashboard/',
            '/api/',
            '/update/',
        ]
        
        # Check if current path matches any no-cache paths
        for path in no_cache_paths:
            if request.path.startswith(path):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                break
        
        return response
