# Fix PostgreSQL Issue - Start Database Container
# This script will start PostgreSQL properly

Write-Host "Fixing PostgreSQL Database Issue" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check existing containers first
Write-Host "`nChecking existing PostgreSQL containers..." -ForegroundColor Cyan

try {
    # List all postgres containers
    $postgresContainers = & docker ps -a --filter "name=postgres" --format "{{.Names}} {{.Status}}"
    
    if ($postgresContainers) {
        Write-Host "Found existing PostgreSQL containers:" -ForegroundColor Yellow
        $postgresContainers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        
        # Try to start existing containers
        Write-Host "`nTrying to start existing PostgreSQL containers..." -ForegroundColor Yellow
        $containerNames = & docker ps -a --filter "name=postgres" --format "{{.Names}}"
        
        foreach ($containerName in $containerNames) {
            Write-Host "Starting container: $containerName" -ForegroundColor Cyan
            & docker start $containerName 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Successfully started $containerName" -ForegroundColor Green
            } else {
                Write-Host "  Failed to start $containerName" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "No existing PostgreSQL containers found." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error checking containers: $($_.Exception.Message)" -ForegroundColor Red
}

# Wait a moment and test connectivity
Write-Host "`nTesting PostgreSQL connectivity..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 3000
    $tcpClient.SendTimeout = 3000
    $tcpClient.Connect("localhost", 5432)
    $tcpClient.Close()
    Write-Host "PostgreSQL is now accessible on port 5432!" -ForegroundColor Green
    
    # Test if we can connect to the database
    Write-Host "`nTesting database connection..." -ForegroundColor Cyan
    
    # Check if psql is available
    $psqlExists = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlExists) {
        Write-Host "Testing with psql..." -ForegroundColor Yellow
        
        # Set environment variables for connection
        $env:PGUSER = "healthcare_user"
        $env:PGPASSWORD = "healthcare_pass"
        $env:PGHOST = "localhost"
        $env:PGPORT = "5432"
        $env:PGDATABASE = "healthcare_db"
        
        $testResult = & psql -c "SELECT version();" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database connection successful!" -ForegroundColor Green
            Write-Host "Database version: $($testResult[2])" -ForegroundColor Gray
        } else {
            Write-Host "Database connection failed - may need to create database" -ForegroundColor Yellow
        }
        
        # Clean up environment variables
        Remove-Item env:PGUSER -ErrorAction SilentlyContinue
        Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
        Remove-Item env:PGHOST -ErrorAction SilentlyContinue
        Remove-Item env:PGPORT -ErrorAction SilentlyContinue
        Remove-Item env:PGDATABASE -ErrorAction SilentlyContinue
    } else {
        Write-Host "psql not available - skipping database test" -ForegroundColor Yellow
    }
    
    exit 0
}
catch {
    Write-Host "PostgreSQL is still not accessible. Trying alternative approaches..." -ForegroundColor Yellow
}

# Try to create a new PostgreSQL container
Write-Host "`nCreating new PostgreSQL container..." -ForegroundColor Cyan

try {
    # Stop and remove any conflicting containers
    Write-Host "Cleaning up conflicting containers..." -ForegroundColor Yellow
    & docker stop healthcare-postgres 2>$null
    & docker rm healthcare-postgres 2>$null
    
    # Create new PostgreSQL container
    Write-Host "Creating new PostgreSQL container..." -ForegroundColor Yellow
    $createResult = & docker run -d `
        --name healthcare-postgres `
        -e POSTGRES_DB=healthcare_db `
        -e POSTGRES_USER=healthcare_user `
        -e POSTGRES_PASSWORD=healthcare_pass `
        -e POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256" `
        -p 5432:5432 `
        postgres:13 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL container created successfully!" -ForegroundColor Green
        Write-Host "Container ID: $createResult" -ForegroundColor Gray
        
        # Wait for PostgreSQL to initialize
        Write-Host "`nWaiting for PostgreSQL to initialize..." -ForegroundColor Cyan
        $maxWait = 30
        $waited = 0
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            
            try {
                $tcpClient = New-Object System.Net.Sockets.TcpClient
                $tcpClient.ReceiveTimeout = 1000
                $tcpClient.SendTimeout = 1000
                $tcpClient.Connect("localhost", 5432)
                $tcpClient.Close()
                
                Write-Host "PostgreSQL is ready! (waited $waited seconds)" -ForegroundColor Green
                break
            }
            catch {
                Write-Host "  Still waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
            }
        }
        
        if ($waited -ge $maxWait) {
            Write-Host "PostgreSQL took too long to start. Check container logs:" -ForegroundColor Red
            Write-Host "  docker logs healthcare-postgres" -ForegroundColor Gray
            exit 1
        }
        
    } else {
        Write-Host "Failed to create PostgreSQL container" -ForegroundColor Red
        
        # Try using the existing docker-compose setup
        Write-Host "`nTrying docker-compose approach..." -ForegroundColor Yellow
        
        # Look for docker-compose file
        $composeFiles = @("docker-compose.yml", "../../docker-compose.yml", "../docker-compose.yml")
        $foundCompose = $false
        
        foreach ($composeFile in $composeFiles) {
            if (Test-Path $composeFile) {
                Write-Host "Found docker-compose file: $composeFile" -ForegroundColor Green
                $foundCompose = $true
                
                if ($composeFile -ne "docker-compose.yml") {
                    $directory = Split-Path $composeFile -Parent
                    Push-Location $directory
                }
                
                # Try to start postgres service
                Write-Host "Starting postgres service with docker-compose..." -ForegroundColor Cyan
                & docker-compose up -d postgres 2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "PostgreSQL started with docker-compose!" -ForegroundColor Green
                } else {
                    Write-Host "docker-compose failed for postgres service" -ForegroundColor Red
                }
                
                if ($composeFile -ne "docker-compose.yml") {
                    Pop-Location
                }
                
                break
            }
        }
        
        if (!$foundCompose) {
            Write-Host "No docker-compose.yml file found" -ForegroundColor Red
            exit 1
        }
    }
}
catch {
    Write-Host "Error creating PostgreSQL container: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Final connectivity test
Write-Host "`nFinal connectivity test..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ReceiveTimeout = 3000
    $tcpClient.SendTimeout = 3000
    $tcpClient.Connect("localhost", 5432)
    $tcpClient.Close()
    
    Write-Host "SUCCESS: PostgreSQL is now running and accessible!" -ForegroundColor Green
    Write-Host "`nContainer status:" -ForegroundColor Cyan
    & docker ps --filter "name=postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Run tests: .\working_test.ps1" -ForegroundColor White
    Write-Host "  2. Start application: python app/main.py" -ForegroundColor White
    Write-Host "  3. If issues persist, check logs: docker logs healthcare-postgres" -ForegroundColor White
    
    exit 0
}
catch {
    Write-Host "FAILED: PostgreSQL is still not accessible" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting steps:" -ForegroundColor Cyan
    Write-Host "  1. Check container logs: docker logs healthcare-postgres" -ForegroundColor White
    Write-Host "  2. Check if port 5432 is in use: netstat -an | findstr :5432" -ForegroundColor White
    Write-Host "  3. Try restarting Docker Desktop" -ForegroundColor White
    Write-Host "  4. Check Windows Firewall settings" -ForegroundColor White
    
    exit 1
}