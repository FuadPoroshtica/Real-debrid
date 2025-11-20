#!/usr/bin/env python3
"""
AI-Powered Error Monitor and Auto-Fix System
Uses Claude API to diagnose and fix issues automatically
"""
import os
import sys
import time
import json
import docker
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from anthropic import Anthropic


class AIMonitor:
    """AI-powered monitoring and auto-fix system"""

    def __init__(self, anthropic_api_key: str, auto_fix: bool = True):
        """
        Initialize AI monitor

        Args:
            anthropic_api_key: Anthropic API key for Claude
            auto_fix: Enable automatic fixing
        """
        self.client = Anthropic(api_key=anthropic_api_key)
        self.docker_client = docker.from_env()
        self.auto_fix = auto_fix
        self.services = {
            'jellyfin': {'url': 'http://jellyfin:8096', 'port': 8096},
            'jellyseerr': {'url': 'http://jellyseerr:5055', 'port': 5055},
            'radarr': {'url': 'http://radarr:7878', 'port': 7878},
            'sonarr': {'url': 'http://sonarr:8989', 'port': 8989},
            'prowlarr': {'url': 'http://prowlarr:9696', 'port': 9696},
            'realdebrid-mount': {'url': 'http://realdebrid-mount:9999', 'port': 9999},
        }
        self.error_history = []

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

        # Also save to file
        with open("/logs/ai-monitor.log", "a") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    def check_service_health(self, service_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a service is healthy

        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            container = self.docker_client.containers.get(service_name)

            # Check if container is running
            if container.status != 'running':
                return False, f"Container is {container.status}"

            # Check health status if available
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                if health.get('Status') != 'healthy':
                    return False, f"Health check failed: {health.get('Status')}"

            # Try to connect to service
            if service_name in self.services:
                service_info = self.services[service_name]
                try:
                    response = requests.get(
                        f"{service_info['url']}/health",
                        timeout=5
                    )
                    if response.status_code >= 500:
                        return False, f"Service returned HTTP {response.status_code}"
                except requests.exceptions.RequestException as e:
                    # Some services might not have /health endpoint
                    # Try root endpoint
                    try:
                        requests.get(service_info['url'], timeout=5)
                    except:
                        return False, f"Service not responding: {str(e)}"

            return True, None

        except docker.errors.NotFound:
            return False, "Container not found"
        except Exception as e:
            return False, f"Error checking health: {str(e)}"

    def get_service_logs(self, service_name: str, lines: int = 100) -> str:
        """Get recent logs from a service"""
        try:
            container = self.docker_client.containers.get(service_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            return logs
        except Exception as e:
            return f"Error getting logs: {str(e)}"

    def analyze_with_claude(self, service_name: str, error_msg: str, logs: str) -> Dict:
        """
        Use Claude to analyze the error and suggest fixes

        Returns:
            Dictionary with diagnosis, fix steps, and commands
        """
        self.log(f"🤖 Asking Claude AI to analyze {service_name} error...")

        prompt = f"""You are an expert system administrator and DevOps engineer analyzing a media server stack error.

Service: {service_name}
Error: {error_msg}

Recent Logs:
{logs[-5000:]}  # Last 5000 chars

Please analyze this error and provide:
1. A human-friendly explanation of what went wrong
2. The root cause
3. Step-by-step fix instructions
4. Specific commands to run (if applicable)
5. Whether this can be auto-fixed safely

Respond in JSON format:
{{
    "diagnosis": "Human-friendly explanation",
    "root_cause": "Technical root cause",
    "severity": "low|medium|high|critical",
    "fix_steps": ["step 1", "step 2", ...],
    "commands": ["command 1", "command 2", ...],
    "auto_fixable": true/false,
    "prevention": "How to prevent this in the future"
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                analysis = json.loads(response_text[json_start:json_end])
                return analysis
            else:
                return {
                    "diagnosis": response_text,
                    "root_cause": "Could not parse structured response",
                    "severity": "medium",
                    "fix_steps": ["Manual intervention required"],
                    "commands": [],
                    "auto_fixable": False,
                    "prevention": "N/A"
                }

        except Exception as e:
            self.log(f"❌ Error calling Claude API: {e}", "ERROR")
            return {
                "diagnosis": f"AI analysis failed: {str(e)}",
                "root_cause": "API error",
                "severity": "high",
                "fix_steps": ["Check Anthropic API key", "Verify network connectivity"],
                "commands": [],
                "auto_fixable": False,
                "prevention": "Ensure API key is valid"
            }

    def execute_fix(self, service_name: str, commands: List[str]) -> bool:
        """
        Execute fix commands

        Returns:
            True if successful
        """
        self.log(f"🔧 Attempting to fix {service_name}...")

        for cmd in commands:
            self.log(f"  Running: {cmd}")

            try:
                if cmd.startswith("docker"):
                    # Execute docker commands via docker client
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode != 0:
                        self.log(f"  ❌ Failed: {result.stderr}", "ERROR")
                        return False
                    else:
                        self.log(f"  ✅ Success: {result.stdout[:100]}")

                elif cmd.startswith("restart"):
                    # Restart service
                    container_name = cmd.split()[-1]
                    container = self.docker_client.containers.get(container_name)
                    container.restart()
                    self.log(f"  ✅ Restarted {container_name}")

                else:
                    # Execute other commands
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode != 0:
                        self.log(f"  ❌ Failed: {result.stderr}", "ERROR")
                        return False

            except Exception as e:
                self.log(f"  ❌ Error executing command: {e}", "ERROR")
                return False

        return True

    def handle_error(self, service_name: str, error_msg: str):
        """Handle an error by analyzing with AI and optionally fixing"""
        self.log(f"⚠️  Error detected in {service_name}: {error_msg}", "WARNING")

        # Get logs
        logs = self.get_service_logs(service_name)

        # Analyze with Claude
        analysis = self.analyze_with_claude(service_name, error_msg, logs)

        # Log human-friendly diagnosis
        self.log(f"\n{'='*60}")
        self.log(f"🔍 AI DIAGNOSIS for {service_name}")
        self.log(f"{'='*60}")
        self.log(f"\n📊 Severity: {analysis.get('severity', 'unknown').upper()}")
        self.log(f"\n💡 What happened:\n   {analysis.get('diagnosis', 'Unknown')}")
        self.log(f"\n🎯 Root cause:\n   {analysis.get('root_cause', 'Unknown')}")

        if analysis.get('fix_steps'):
            self.log(f"\n🔧 Fix steps:")
            for i, step in enumerate(analysis.get('fix_steps', []), 1):
                self.log(f"   {i}. {step}")

        if analysis.get('prevention'):
            self.log(f"\n🛡️  Prevention:\n   {analysis.get('prevention')}")

        self.log(f"{'='*60}\n")

        # Store in history
        self.error_history.append({
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'error': error_msg,
            'analysis': analysis
        })

        # Auto-fix if enabled and safe
        if self.auto_fix and analysis.get('auto_fixable'):
            commands = analysis.get('commands', [])

            if commands:
                self.log(f"🤖 Auto-fix is enabled. Attempting to fix...")

                if self.execute_fix(service_name, commands):
                    self.log(f"✅ Successfully fixed {service_name}!", "SUCCESS")

                    # Verify fix
                    time.sleep(5)
                    is_healthy, new_error = self.check_service_health(service_name)

                    if is_healthy:
                        self.log(f"✅ {service_name} is now healthy!", "SUCCESS")
                    else:
                        self.log(f"⚠️  Fix applied but service still unhealthy: {new_error}", "WARNING")
                else:
                    self.log(f"❌ Auto-fix failed for {service_name}", "ERROR")
            else:
                self.log(f"ℹ️  No auto-fix commands available", "INFO")
        else:
            if not self.auto_fix:
                self.log(f"ℹ️  Auto-fix is disabled", "INFO")
            else:
                self.log(f"⚠️  This issue requires manual intervention", "WARNING")

    def monitor_loop(self, interval: int = 60):
        """
        Main monitoring loop

        Args:
            interval: Check interval in seconds
        """
        self.log("🚀 AI Monitor started")
        self.log(f"   Auto-fix: {'Enabled' if self.auto_fix else 'Disabled'}")
        self.log(f"   Check interval: {interval}s")
        self.log("")

        while True:
            try:
                self.log("🔍 Checking all services...")

                all_healthy = True

                for service_name in self.services.keys():
                    is_healthy, error_msg = self.check_service_health(service_name)

                    if is_healthy:
                        self.log(f"  ✅ {service_name}: Healthy")
                    else:
                        self.log(f"  ❌ {service_name}: {error_msg}", "ERROR")
                        all_healthy = False

                        # Handle the error
                        self.handle_error(service_name, error_msg)

                if all_healthy:
                    self.log("✅ All services healthy!")

                self.log("")

                # Wait for next check
                time.sleep(interval)

            except KeyboardInterrupt:
                self.log("🛑 Stopping AI monitor...")
                break
            except Exception as e:
                self.log(f"❌ Error in monitor loop: {e}", "ERROR")
                time.sleep(interval)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AI-Powered Service Monitor")
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--no-auto-fix', action='store_true', help='Disable automatic fixing')
    parser.add_argument('--api-key', help='Anthropic API key (or use ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ Error: No Anthropic API key provided")
        print("   Set ANTHROPIC_API_KEY environment variable or use --api-key")
        sys.exit(1)

    # Create monitor
    monitor = AIMonitor(
        anthropic_api_key=api_key,
        auto_fix=not args.no_auto_fix
    )

    # Start monitoring
    try:
        monitor.monitor_loop(interval=args.interval)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
