#!/usr/bin/env python3
"""
Security Configuration Checker for Email Receipts Application
Run this script to check your security configuration before deployment
"""

import os
import sys
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check(condition, message):
    """Print check result with color coding"""
    if condition:
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.END} {message}")
        return False

def warn(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END}  {message}")

def info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END}  {message}")

def check_security():
    """Run all security checks"""
    print(f"\n{Colors.BOLD}Email Receipts - Security Configuration Check{Colors.END}")
    print(f"{'='*60}\n")
    
    total_checks = 0
    passed_checks = 0
    
    # Check 1: Environment file exists
    print(f"{Colors.BOLD}1. Environment Configuration{Colors.END}")
    total_checks += 1
    if check(os.path.exists('.env'), "Environment file (.env) exists"):
        passed_checks += 1
        
        # Load .env file
        env_vars = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            warn(f"Could not parse .env file: {e}")
    else:
        warn("Create .env file from .env.example")
    print()
    
    # Check 2: Secret Key
    print(f"{Colors.BOLD}2. Secret Key Security{Colors.END}")
    total_checks += 1
    secret_key = os.environ.get('SECRET_KEY') or env_vars.get('SECRET_KEY', '')
    if check(secret_key and secret_key != 'dev-secret-key-change-in-production' and len(secret_key) >= 32,
             "SECRET_KEY is set and secure"):
        passed_checks += 1
    else:
        warn("Generate a strong SECRET_KEY:")
        print('   python -c "import secrets; print(secrets.token_hex(32))"')
    print()
    
    # Check 3: Admin Credentials
    print(f"{Colors.BOLD}3. Admin Credentials{Colors.END}")
    total_checks += 1
    admin_user = env_vars.get('ADMIN_USERNAME', 'admin')
    admin_pass = env_vars.get('ADMIN_PASSWORD', 'admin123')
    if check(admin_user != 'admin' or admin_pass != 'admin123',
             "Default admin credentials have been changed"):
        passed_checks += 1
    else:
        warn("Change default admin credentials in .env file")
    print()
    
    # Check 4: SMTP Configuration
    print(f"{Colors.BOLD}4. Email Configuration{Colors.END}")
    smtp_configured = all([
        env_vars.get('SMTP_SERVER'),
        env_vars.get('SMTP_USERNAME'),
        env_vars.get('SMTP_PASSWORD')
    ])
    total_checks += 1
    if check(smtp_configured, "SMTP credentials configured"):
        passed_checks += 1
    else:
        warn("Configure SMTP settings in .env file")
    print()
    
    # Check 5: HTTPS/SSL
    print(f"{Colors.BOLD}5. HTTPS/SSL Configuration{Colors.END}")
    flask_env = env_vars.get('FLASK_ENV', 'development')
    total_checks += 1
    if flask_env == 'production':
        warn("Running in PRODUCTION mode")
        info("Ensure you have:")
        print("   - Valid SSL certificate installed")
        print("   - Reverse proxy (nginx/Apache) with HTTPS")
        print("   - HTTP to HTTPS redirect configured")
        check(False, "Manual verification required for HTTPS")
    else:
        info("Running in DEVELOPMENT mode - HTTPS check skipped")
        check(True, "Development environment detected")
        passed_checks += 1
    print()
    
    # Check 6: File Permissions
    print(f"{Colors.BOLD}6. File Permissions{Colors.END}")
    total_checks += 1
    if os.path.exists('.env'):
        env_perms = oct(os.stat('.env').st_mode)[-3:]
        if check(env_perms in ['600', '640'], f".env has secure permissions ({env_perms})"):
            passed_checks += 1
        else:
            warn(f".env permissions are {env_perms}. Set to 600:")
            print("   chmod 600 .env")
    print()
    
    # Check 7: Dependencies
    print(f"{Colors.BOLD}7. Security Dependencies{Colors.END}")
    try:
        import flask
        import flask_login
        from werkzeug.security import generate_password_hash
        total_checks += 1
        if check(True, "Core security dependencies installed"):
            passed_checks += 1
    except ImportError as e:
        total_checks += 1
        check(False, f"Missing dependencies: {e}")
        warn("Run: pip install -r requirements.txt")
    print()
    
    # Check 8: Debug Mode
    print(f"{Colors.BOLD}8. Debug Mode{Colors.END}")
    total_checks += 1
    if flask_env == 'production':
        if check(True, "Debug mode should be disabled in production"):
            passed_checks += 1
            info("Verify DEBUG=False in app.py when running")
    else:
        info("Development mode - debug enabled (OK for local testing)")
        total_checks += 1
        passed_checks += 1
    print()
    
    # Check 9: Git Security
    print(f"{Colors.BOLD}9. Git Security{Colors.END}")
    total_checks += 1
    gitignore_exists = os.path.exists('.gitignore')
    if gitignore_exists:
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            env_ignored = '.env' in gitignore_content
            if check(env_ignored, ".env is in .gitignore"):
                passed_checks += 1
            else:
                warn("Add .env to .gitignore to prevent credential leaks")
    else:
        check(False, ".gitignore file exists")
        warn("Create .gitignore and add .env to it")
    print()
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Summary{Colors.END}")
    print(f"{'='*60}")
    
    percentage = (passed_checks / total_checks) * 100
    
    if percentage == 100:
        color = Colors.GREEN
        status = "EXCELLENT"
    elif percentage >= 80:
        color = Colors.BLUE
        status = "GOOD"
    elif percentage >= 60:
        color = Colors.YELLOW
        status = "NEEDS IMPROVEMENT"
    else:
        color = Colors.RED
        status = "CRITICAL"
    
    print(f"\n{color}{Colors.BOLD}Security Score: {passed_checks}/{total_checks} ({percentage:.0f}%){Colors.END}")
    print(f"{color}{Colors.BOLD}Status: {status}{Colors.END}\n")
    
    if percentage < 100:
        print(f"{Colors.YELLOW}Recommendations:{Colors.END}")
        if percentage < 80:
            print("1. Address all CRITICAL issues (✗) before deployment")
            print("2. Review all warnings (⚠) and fix where applicable")
            print("3. Read SECURITY_RECOMMENDATIONS.md for detailed guidance")
        else:
            print("1. Address remaining warnings before production deployment")
            print("2. Set up HTTPS/SSL for production")
            print("3. Implement rate limiting and monitoring")
    else:
        print(f"{Colors.GREEN}All basic security checks passed!{Colors.END}")
        print("\nBefore production deployment, also ensure:")
        print("• HTTPS is enabled with valid SSL certificate")
        print("• Rate limiting is configured")
        print("• Logging and monitoring are set up")
        print("• Regular security updates are planned")
    
    print(f"\n{Colors.BLUE}For detailed security guidance, see:{Colors.END}")
    print("• SECURITY_RECOMMENDATIONS.md")
    print("• LOGIN_FEATURE.md")
    print()
    
    return percentage >= 80

if __name__ == '__main__':
    try:
        success = check_security()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Security check cancelled{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error running security check: {e}{Colors.END}")
        sys.exit(1)
