#!/usr/bin/env node

/**
 * Endpoint Integration Test Runner
 * Execute this to validate all endpoint integrations
 */

import { testRunner } from './endpoint-integration-test';

async function main() {
  try {
    console.log('🔧 IRIS API Integration System - Endpoint Testing');
    console.log('=================================================');
    console.log('Testing SOC2 Type 2 Compliant Endpoints...\n');
    
    // Run all integration tests
    await testRunner.runAllTests();
    
    console.log('\n✅ Integration testing completed!');
    console.log('Check the report above for detailed results.');
    
  } catch (error) {
    console.error('💥 Test runner failed:', error);
    process.exit(1);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}

export { main as runEndpointTests };