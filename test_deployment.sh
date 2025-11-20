#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
#  Real-Debrid Media Stack - Comprehensive Test Script
#  Stress test and validation for all components
# ═══════════════════════════════════════════════════════════════════════════

# Don't exit on errors - we want to run all tests
# set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ERRORS=0
WARNINGS=0
PASSED=0

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}  ✅ PASS${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}  ❌ FAIL${NC} $1"
    ((ERRORS++))
}

log_warn() {
    echo -e "${YELLOW}  ⚠️  WARN${NC} $1"
    ((WARNINGS++))
}

print_header() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Real-Debrid Media Stack - Comprehensive Tests             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"
}

# ═══════════════════════════════════════════════════════════════════════════
#  Test Functions
# ═══════════════════════════════════════════════════════════════════════════

test_python_syntax() {
    log_test "Testing Python script syntax..."

    python_files=(
        "setup_wizard.py"
        "rdmount.py"
        "start.py"
        "realdebrid_api.py"
        "realdebrid_fs.py"
        "resolver.py"
        "webdav_server.py"
        "health_manager.py"
        "ai_monitor.py"
        "config_manager.py"
    )

    for file in "${python_files[@]}"; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                log_pass "$file syntax valid"
            else
                log_fail "$file has syntax errors"
            fi
        else
            log_warn "$file not found"
        fi
    done
    echo ""
}

test_bash_syntax() {
    log_test "Testing Bash script syntax..."

    bash_files=(
        "deploy.sh"
        "install.sh"
        "docker-entrypoint.sh"
    )

    for file in "${bash_files[@]}"; do
        if [ -f "$file" ]; then
            if bash -n "$file" 2>/dev/null; then
                log_pass "$file syntax valid"
            else
                log_fail "$file has syntax errors"
            fi
        else
            log_warn "$file not found"
        fi
    done
    echo ""
}

test_html_templates() {
    log_test "Testing HTML templates..."

    templates=(
        "templates/setup.html"
        "templates/deploying.html"
        "templates/complete.html"
    )

    for template in "${templates[@]}"; do
        if [ -f "$template" ]; then
            # Check HTML structure
            if grep -q "<!DOCTYPE html>" "$template" && \
               grep -q "<html" "$template" && \
               grep -q "</html>" "$template"; then
                log_pass "$(basename $template) valid structure"
            else
                log_fail "$(basename $template) invalid structure"
            fi

            # Check balanced div tags
            open_divs=$(grep -o "<div" "$template" | wc -l)
            close_divs=$(grep -o "</div>" "$template" | wc -l)
            if [ "$open_divs" -eq "$close_divs" ]; then
                log_pass "$(basename $template) balanced tags ($open_divs divs)"
            else
                log_fail "$(basename $template) unbalanced tags ($open_divs open, $close_divs close)"
            fi
        else
            log_fail "$template not found"
        fi
    done
    echo ""
}

test_docker_config() {
    log_test "Testing Docker configuration..."

    # Check docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
            log_pass "docker-compose.yml valid YAML"
        else
            log_fail "docker-compose.yml invalid YAML"
        fi

        # Check for required services
        services=("realdebrid-mount" "jellyfin" "jellyseerr" "radarr" "sonarr" "prowlarr" "nginx" "ai-monitor")
        for service in "${services[@]}"; do
            if grep -q "^  $service:" docker-compose.yml; then
                log_pass "Service '$service' defined"
            else
                log_fail "Service '$service' missing"
            fi
        done
    else
        log_fail "docker-compose.yml not found"
    fi

    # Check Dockerfiles
    for dockerfile in Dockerfile Dockerfile.ai-monitor; do
        if [ -f "$dockerfile" ]; then
            if grep -q "FROM" "$dockerfile"; then
                log_pass "$dockerfile valid"
            else
                log_fail "$dockerfile missing FROM instruction"
            fi
        else
            log_fail "$dockerfile not found"
        fi
    done
    echo ""
}

test_nginx_config() {
    log_test "Testing Nginx configuration..."

    if [ -f "nginx.conf" ]; then
        log_pass "nginx.conf exists"

        # Check service routes
        services=("jellyfin" "jellyseerr" "radarr" "sonarr" "prowlarr")
        for service in "${services[@]}"; do
            if grep -q "location.*/$service" nginx.conf; then
                log_pass "$service route configured"
            else
                log_fail "$service route missing"
            fi
        done
    else
        log_fail "nginx.conf not found"
    fi
    echo ""
}

test_file_dependencies() {
    log_test "Testing file dependencies..."

    critical_files=(
        "deploy.sh"
        "setup_wizard.py"
        "docker-compose.yml"
        "Dockerfile"
        "nginx.conf"
        "requirements.txt"
        "README.md"
        "ULTIMATE_DEPLOY.md"
    )

    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            log_pass "$file exists"
        else
            log_fail "$file missing"
        fi
    done
    echo ""
}

test_python_imports() {
    log_test "Testing Python imports..."

    # Test if critical Python modules can import
    python3 << 'EOF'
import sys

modules_to_test = [
    ('realdebrid_api', 'RealDebridAPI'),
    ('realdebrid_fs', 'RealDebridFS'),
]

for module, class_name in modules_to_test:
    try:
        mod = __import__(module)
        if hasattr(mod, class_name):
            print(f"✅ {module}.{class_name} imports successfully")
        else:
            print(f"⚠️  {module} imports but {class_name} not found")
    except Exception as e:
        print(f"❌ {module} import failed: {e}")
EOF
    echo ""
}

test_requirements() {
    log_test "Testing requirements.txt..."

    if [ -f "requirements.txt" ]; then
        log_pass "requirements.txt exists"

        required_packages=(
            "fusepy"
            "requests"
            "rich"
            "inquirer"
            "pyyaml"
            "wsgidav"
            "anthropic"
            "docker"
            "flask"
        )

        for package in "${required_packages[@]}"; do
            if grep -q "$package" requirements.txt; then
                log_pass "$package in requirements"
            else
                log_fail "$package missing from requirements"
            fi
        done
    else
        log_fail "requirements.txt not found"
    fi
    echo ""
}

test_permissions() {
    log_test "Testing file permissions..."

    executable_files=(
        "deploy.sh"
        "install.sh"
        "setup_wizard.py"
        "rdmount.py"
        "start.py"
    )

    for file in "${executable_files[@]}"; do
        if [ -f "$file" ]; then
            if [ -x "$file" ]; then
                log_pass "$file is executable"
            else
                log_warn "$file not executable (will be fixed)"
                chmod +x "$file"
            fi
        fi
    done
    echo ""
}

test_documentation() {
    log_test "Testing documentation..."

    docs=(
        "README.md"
        "ULTIMATE_DEPLOY.md"
        "ADVANCED.md"
        "QUICKSTART_ADVANCED.md"
    )

    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            if [ -s "$doc" ]; then
                log_pass "$doc exists and not empty"
            else
                log_warn "$doc is empty"
            fi
        else
            log_warn "$doc not found"
        fi
    done
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
#  Run All Tests
# ═══════════════════════════════════════════════════════════════════════════

main() {
    print_header

    echo -e "${YELLOW}Running comprehensive tests...${NC}\n"

    test_python_syntax
    test_bash_syntax
    test_html_templates
    test_docker_config
    test_nginx_config
    test_file_dependencies
    test_python_imports
    test_requirements
    test_permissions
    test_documentation

    # Summary
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                        TEST SUMMARY                            ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "  ${RED}Errors:${NC}   $ERRORS"
    echo ""

    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ All critical tests passed!${NC}"
        echo -e "${GREEN}   The deployment is ready to use.${NC}"
        echo ""
        if [ $WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}⚠️  Some warnings were found but they shouldn't affect deployment.${NC}"
        fi
        exit 0
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        echo -e "${RED}   Please fix the errors before deploying.${NC}"
        exit 1
    fi
}

# Run main function
main
