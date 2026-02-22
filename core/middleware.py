import logging
import time
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime, timedelta

logger = logging.getLogger('core')


class LoggingMiddleware(MiddlewareMixin):
    """Log all HTTP requests and responses with timing information"""
    
    def process_request(self, request):
        """Log incoming request"""
        request.start_time = time.time()
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.info(f"-> {request.method} {request.path} | User: {user} | IP: {self.get_client_ip(request)}")
        return None
    
    def process_response(self, request, response):
        """Log outgoing response with timing"""
        duration = time.time() - request.start_time if hasattr(request, 'start_time') else 0
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        status = response.status_code
        
        logger.info(f"<- {status} {request.method} {request.path} | Time: {duration:.3f}s | User: {user}")
        
        if status >= 400:
            logger.error(f"ERROR: {status} {request.method} {request.path} | Referrer: {request.META.get('HTTP_REFERER', 'N/A')}")
        
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
    """Control browser cache behavior"""
    
    def process_response(self, request, response):
        """Add cache-control headers to responses"""
        
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        if 'text/html' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=300'
            response['Pragma'] = 'cache'
            expires_time = datetime.utcnow() + timedelta(minutes=5)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
            if 'Last-Modified' not in response:
                current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                response['Last-Modified'] = current_time
        
        elif 'text/css' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        elif 'application/javascript' in response.get('Content-Type', '') or 'text/javascript' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=3600'
            expires_time = datetime.utcnow() + timedelta(hours=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        elif 'image' in response.get('Content-Type', ''):
            response['Cache-Control'] = 'public, max-age=2592000'
            expires_time = datetime.utcnow() + timedelta(days=30)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        else:
            response['Cache-Control'] = 'public, max-age=60'
            expires_time = datetime.utcnow() + timedelta(minutes=1)
            expires_str = expires_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
            response['Expires'] = expires_str
        
        if 'ETag' not in response:
            response['ETag'] = f'"{hash(response.content) % 100000}"'
        
        return response


class NoCacheMiddleware(MiddlewareMixin):
    """Disable caching for sensitive pages"""
    
    def process_response(self, request, response):
        """Add no-cache headers for sensitive pages"""
        
        no_cache_paths = [
            '/login/',
            '/logout/',
            '/dashboard/',
            '/api/',
            '/update/',
        ]
        
        for path in no_cache_paths:
            if request.path.startswith(path):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                break
        
        return response
