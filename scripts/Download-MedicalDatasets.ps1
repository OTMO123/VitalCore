# HEMA3N Medical Datasets Management - PowerShell Script
# Downloads and manages medical training datasets for LoRA fine-tuning

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("built-in", "external", "huggingface", "medical-public", "all")]
    [string]$DatasetType = "built-in",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("cardiology", "neurology", "emergency", "pulmonology", "pediatric", "infection", "psychiatry", "orthopedic", "general", "all")]
    [string]$Specialty = "all",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "./datasets/medical",
    
    [Parameter(Mandatory=$false)]
    [switch]$ListOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerifyOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$ShowDetails
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header($Title) {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host $Title -ForegroundColor White
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host ""
}

function Test-PythonPackages {
    Write-Info "Checking required Python packages..."
    
    try {
        $result = python -c "
import sys
try:
    import datasets
    print('datasets: OK')
except:
    print('datasets: Missing')

try:
    import transformers
    print('transformers: OK')
except:
    print('transformers: Missing')

try:
    import torch
    print('torch: OK')
except:
    print('torch: Missing')

try:
    from unsloth import FastModel
    print('unsloth: OK')
except:
    print('unsloth: Optional')
" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python packages verified"
            if ($ShowDetails) {
                $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
        } else {
            Write-Warning "Some packages may be missing"
            $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        }
        
        return $true
        
    } catch {
        Write-Error "Failed to check Python packages: $_"
        return $false
    }
}

function Get-BuiltInDatasets {
    Write-Info "Built-in HEMA3N medical datasets:"
    
    $builtInDatasets = @{
        "cardiology" = @{
            "description" = "Heart conditions, MI, arrhythmias, cardiac emergencies"
            "samples" = "500+ curated samples"
            "source" = "HEMA3N medical protocols"
        }
        "neurology" = @{
            "description" = "Stroke, seizures, brain disorders, neurological assessment"
            "samples" = "450+ curated samples"
            "source" = "HEMA3N neurological protocols"
        }
        "emergency" = @{
            "description" = "Trauma, cardiac arrest, shock, ACLS protocols"
            "samples" = "600+ curated samples"
            "source" = "HEMA3N emergency protocols"
        }
        "pulmonology" = @{
            "description" = "Respiratory conditions, lung diseases, ventilation"
            "samples" = "400+ curated samples"
            "source" = "HEMA3N pulmonary protocols"
        }
        "pediatric" = @{
            "description" = "Child medicine, development, pediatric emergencies"
            "samples" = "350+ curated samples"
            "source" = "HEMA3N pediatric protocols"
        }
        "infection" = @{
            "description" = "Sepsis, antimicrobial therapy, infectious diseases"
            "samples" = "400+ curated samples"
            "source" = "HEMA3N infectious disease protocols"
        }
        "psychiatry" = @{
            "description" = "Mental health, behavioral emergencies, crisis intervention"
            "samples" = "300+ curated samples"
            "source" = "HEMA3N psychiatric protocols"
        }
        "orthopedic" = @{
            "description" = "Fractures, joint injuries, bone conditions"
            "samples" = "350+ curated samples"
            "source" = "HEMA3N orthopedic protocols"
        }
        "general" = @{
            "description" = "Primary care, chronic diseases, general medicine"
            "samples" = "500+ curated samples"
            "source" = "HEMA3N general medicine protocols"
        }
    }
    
    foreach ($specialty in $builtInDatasets.Keys) {
        $dataset = $builtInDatasets[$specialty]
        Write-Host ""
        Write-Host "MEDICAL $($specialty.ToUpper())" -ForegroundColor Green
        Write-Host "   Description: $($dataset.description)" -ForegroundColor Cyan
        Write-Host "   Samples: $($dataset.samples)" -ForegroundColor Yellow
        Write-Host "   Source: $($dataset.source)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Success "All built-in datasets are automatically available - no download needed!"
    Write-Info "To use built-in datasets, add --medical-data flag when training"
}

function Get-ExternalDatasets {
    Write-Info "Available external medical datasets:"
    
    $externalDatasets = @{
        "FineTome-100k" = @{
            "description" = "High-quality instruction dataset (100k samples)"
            "source" = "mlabonne/FineTome-100k"
            "size" = "~500MB"
            "type" = "General instruction following"
        }
        "OpenAssistant" = @{
            "description" = "Conversational AI dataset"
            "source" = "OpenAssistant/oasst1"
            "size" = "~200MB"
            "type" = "Conversation"
        }
        "Medical-Meadow" = @{
            "description" = "Medical question-answering dataset"
            "source" = "medalpaca/medical_meadow_medical_flashcards"
            "size" = "~50MB"
            "type" = "Medical Q&A"
        }
        "PubMedQA" = @{
            "description" = "Biomedical question answering from PubMed"
            "source" = "qiaojin/PubMedQA"
            "size" = "~100MB"
            "type" = "Biomedical Q&A"
        }
    }
    
    foreach ($dataset in $externalDatasets.Keys) {
        $info = $externalDatasets[$dataset]
        Write-Host ""
        Write-Host "EXTERNAL $dataset" -ForegroundColor Yellow
        Write-Host "   Description: $($info.description)" -ForegroundColor Cyan
        Write-Host "   Source: $($info.source)" -ForegroundColor Gray
        Write-Host "   Size: $($info.size)" -ForegroundColor Magenta
        Write-Host "   Type: $($info.type)" -ForegroundColor Blue
    }
}

function Download-ExternalDataset {
    param(
        [string]$DatasetName,
        [string]$HuggingFaceId,
        [string]$OutputPath
    )
    
    Write-Info "Downloading $DatasetName from Hugging Face..."
    
    try {
        # Simple Python download script
        # Create a temporary Python file to avoid PowerShell variable conflicts
        $tempPythonFile = [System.IO.Path]::GetTempFileName() + ".py"
        
        $pythonContent = @"
from datasets import load_dataset
import os
import json
import sys

dataset_id = sys.argv[1]
output_path = sys.argv[2] 
dataset_name = sys.argv[3]

try:
    print('Loading dataset:', dataset_id)
    dataset = load_dataset(dataset_id)
    
    os.makedirs(output_path, exist_ok=True)
    
    # Save small sample for testing
    if hasattr(dataset, 'train'):
        train_data = dataset['train'].select(range(min(1000, len(dataset['train']))))
        train_file = os.path.join(output_path, f'{dataset_name}-train-sample.json')
        with open(train_file, 'w') as f:
            json.dump([dict(item) for item in train_data], f, indent=2)
        print('OK Saved training sample:', len(train_data), 'samples')
    
    print('OK Dataset', dataset_name, 'downloaded successfully')
    
except Exception as e:
    print('ERROR downloading', dataset_name, ':', str(e))
    exit(1)
"@
        
        $pythonContent | Out-File -FilePath $tempPythonFile -Encoding UTF8
        $result = python $tempPythonFile $HuggingFaceId $OutputPath $DatasetName 2>&1
        Remove-Item $tempPythonFile -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dataset $DatasetName downloaded successfully"
            if ($ShowDetails) {
                $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
            return $true
        } else {
            Write-Error "Failed to download dataset $DatasetName"
            $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            return $false
        }
        
    } catch {
        Write-Error "Failed to download dataset: $_"
        return $false
    }
}

function Test-DatasetIntegrity {
    Write-Info "Verifying dataset integrity..."
    
    if (-not (Test-Path $OutputDir)) {
        Write-Warning "Dataset directory not found: $OutputDir"
        return $false
    }
    
    $jsonFiles = Get-ChildItem -Path $OutputDir -Filter "*.json" -ErrorAction SilentlyContinue
    
    if ($jsonFiles.Count -eq 0) {
        Write-Warning "No JSON dataset files found in $OutputDir"
        return $false
    }
    
    $totalSamples = 0
    foreach ($file in $jsonFiles) {
        try {
            $content = Get-Content -Path $file.FullName -Raw | ConvertFrom-Json
            $samples = $content.Count
            $totalSamples += $samples
            Write-Host "  OK $($file.Name): $samples samples" -ForegroundColor Green
        } catch {
            Write-Host "  ERROR $($file.Name): Failed to read" -ForegroundColor Red
        }
    }
    
    Write-Success "Total: $($jsonFiles.Count) files, $totalSamples samples"
    return $true
}

function Show-DatasetUsage {
    Write-Header "How to Use Datasets with HEMA3N Training"
    
    Write-Host "1. Built-in Medical Datasets (Recommended):" -ForegroundColor Green
    Write-Host "   .\\scripts\\Train-MedicalAgent.ps1 -Agent cardiology -MedicalData" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "2. External Datasets:" -ForegroundColor Green
    Write-Host "   .\\scripts\\Train-MedicalAgent.ps1 -Agent cardiology" -ForegroundColor Yellow
    Write-Host "   (Uses FineTome-100k by default)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "3. Custom Dataset Path:" -ForegroundColor Green
    Write-Host "   python scripts/finetune_gemma3n_medical.py --dataset-path ./datasets/medical/custom.json" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "4. Mixed Training:" -ForegroundColor Green
    Write-Host "   .\\scripts\\Train-MedicalAgent.ps1 -Agent cardiology -MedicalData -DatasetSize 2000" -ForegroundColor Yellow
    Write-Host "   (Combines built-in + external data)" -ForegroundColor Gray
}

# Main execution
function Main {
    Write-Header "HEMA3N Medical Datasets Management - PowerShell"
    
    if ($ListOnly) {
        if ($DatasetType -eq "built-in" -or $DatasetType -eq "all") {
            Get-BuiltInDatasets
        }
        if ($DatasetType -eq "external" -or $DatasetType -eq "huggingface" -or $DatasetType -eq "all") {
            Get-ExternalDatasets
        }
        Show-DatasetUsage
        return
    }
    
    if ($VerifyOnly) {
        if (Test-Path $OutputDir) {
            Test-DatasetIntegrity
        } else {
            Write-Warning "Dataset directory not found: $OutputDir"
            Write-Info "Run without -VerifyOnly to download datasets first"
        }
        return
    }
    
    # Check prerequisites
    if (-not (Test-PythonPackages)) {
        Write-Warning "Some Python packages may be missing. Consider running Setup-LoRAEnvironment.ps1"
    }
    
    # Handle different dataset types
    switch ($DatasetType) {
        "built-in" {
            Write-Success "Built-in datasets are ready to use!"
            Write-Info "No download needed - datasets are embedded in the training script"
            Get-BuiltInDatasets
        }
        
        "external" {
            Write-Info "Downloading external datasets..."
            New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
            
            $success = Download-ExternalDataset -DatasetName "FineTome-100k" -HuggingFaceId "mlabonne/FineTome-100k" -OutputPath $OutputDir
            if ($success) {
                Test-DatasetIntegrity
            }
        }
        
        "huggingface" {
            Write-Info "Downloading Hugging Face medical datasets..."
            New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
            
            Download-ExternalDataset -DatasetName "Medical-Meadow" -HuggingFaceId "medalpaca/medical_meadow_medical_flashcards" -OutputPath $OutputDir
            Download-ExternalDataset -DatasetName "PubMedQA" -HuggingFaceId "qiaojin/PubMedQA" -OutputPath $OutputDir
            
            Test-DatasetIntegrity
        }
        
        "medical-public" {
            Write-Info "Downloading public medical datasets..."
            New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
            
            Download-ExternalDataset -DatasetName "Medical-Meadow" -HuggingFaceId "medalpaca/medical_meadow_medical_flashcards" -OutputPath $OutputDir
            Download-ExternalDataset -DatasetName "PubMedQA" -HuggingFaceId "qiaojin/PubMedQA" -OutputPath $OutputDir
            Download-ExternalDataset -DatasetName "OpenAssistant" -HuggingFaceId "OpenAssistant/oasst1" -OutputPath $OutputDir
            
            Test-DatasetIntegrity
        }
        
        "all" {
            Write-Info "Setting up all available datasets..."
            Get-BuiltInDatasets
            
            Write-Info "Downloading external datasets..."
            New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
            
            Download-ExternalDataset -DatasetName "FineTome-100k" -HuggingFaceId "mlabonne/FineTome-100k" -OutputPath $OutputDir
            Download-ExternalDataset -DatasetName "Medical-Meadow" -HuggingFaceId "medalpaca/medical_meadow_medical_flashcards" -OutputPath $OutputDir
            
            Test-DatasetIntegrity
        }
    }
    
    Show-DatasetUsage
    Write-Success "Dataset management completed!"
}

# Execute main function
try {
    Main
} catch {
    Write-Error "Dataset management failed: $_"
    Write-Info "Error details: $($_.Exception.Message)"
    exit 1
}