<#
    Verify-Fixes.ps1  --  read-only check that the pass-9 corrections are present
                          in a checkout.

    Verifies commit  a6f9bb3dd4647dad5b9546d466d6db8d0c2d3fd1
    ("fix(diagnostics): prove the corrections are issuer-neutral; split the
      third-party refusal; one-shot official URLs").

    Usage (from anywhere; nothing is written):

        powershell -NoProfile -ExecutionPolicy Bypass `
            -File .\engine\tools\Verify-Fixes.ps1

        powershell -NoProfile -ExecutionPolicy Bypass `
            -File .\engine\tools\Verify-Fixes.ps1 -Root "G:\IIPS-IPD-GATE-BUILD-CEC7080"

        powershell -NoProfile -ExecutionPolicy Bypass `
            -File .\engine\tools\Verify-Fixes.ps1 -RunTests

    Design rules
    ------------
      * No conditional-fallback branch and no cleanup clause anywhere in this
        file: every decision is an early return or an early exit.
      * Fail closed.  Exit 0 requires that every REQUIRED check actually RAN and
        passed.  A check that cannot be evaluated (missing file, locked file,
        missing git, missing Python, unexpected exception) is recorded as a
        FAILURE, never as a pass, and the script still reaches its summary.
      * Read-only.  No file is created, moved or deleted; no network call is
        made; no persistent environment variable is set; the process working
        directory is restored.
      * Import-free of repo code.  The script reads source text and calls git /
        python; it never imports the engine, so a broken engine cannot hide the
        verdict.

    Exit codes
    ----------
      0  all REQUIRED checks ran and passed (commit identity included)
      1  at least one REQUIRED check failed or could not be evaluated
      2  -Root does not exist or is not a directory (nothing verified)

    Parameters
    ----------
      -Root        checkout to verify              (default G:\IIPS-IPD-GATE-BUILD-CEC7080)
      -Commit      commit that must be present     (default a6f9bb3...)
      -RunTests    also run the three new/extended pytest suites (~35 s)
      -AllowNoGit     downgrade "git unavailable" from FAIL to WARN, for a checkout
                      shipped as plain files; content checks still decide the verdict
      -AllowNoPython  downgrade "python unavailable" from FAIL to WARN, for a host
                      that only inspects source; content checks still decide
#>

#Requires -Version 5.1

[CmdletBinding()]
param(
    [string] $Root       = 'G:\IIPS-IPD-GATE-BUILD-CEC7080',
    [string] $Commit     = 'a6f9bb3dd4647dad5b9546d466d6db8d0c2d3fd1',
    [switch] $RunTests,
    [switch] $AllowNoGit,
    [switch] $AllowNoPython
)

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'

$script:RootPath     = $Root
$script:Commit       = $Commit
$script:GitExe       = ''
$script:PyExe        = ''
$script:Checks       = 0
$script:RequiredRun  = 0
$script:RequiredFail = 0
$script:AdvisoryRun  = 0
$script:AdvisoryWarn = 0
$script:OldPythonPath = $env:PYTHONPATH

# --------------------------------------------------------------------------
# Result recording.  One entry point, so the counters can never drift.
# --------------------------------------------------------------------------
function Add-Result {
    param(
        [string] $Name,
        [bool]   $Ok,
        [string] $Detail   = '',
        [string] $Category = 'REQUIRED'
    )

    $script:Checks++

    if ($Category -eq 'ADVISORY') {
        $script:AdvisoryRun++
        if ($Ok) {
            Write-Host ('  PASS  {0,-44} {1}' -f $Name, $Detail)
            return
        }
        $script:AdvisoryWarn++
        Write-Host ('  WARN  {0,-44} {1}' -f $Name, $Detail) -ForegroundColor Yellow
        return
    }

    $script:RequiredRun++
    if ($Ok) {
        Write-Host ('  PASS  {0,-44} {1}' -f $Name, $Detail)
        return
    }
    $script:RequiredFail++
    Write-Host ('  FAIL  {0,-44} {1}' -f $Name, $Detail) -ForegroundColor Red
}

function Get-SafeText {
    param([string] $FullPath)
    # Returns the file's text, or $null.  Never throws.
    $text = $null
    try {
        if ([System.IO.File]::Exists($FullPath)) {
            $text = [System.IO.File]::ReadAllText($FullPath)
        }
    } catch {
        $text = $null
    }
    if ($null -eq $text) {
        return $null
    }
    return [string]$text
}

function Test-Marker {
    param(
        [string] $RelPath,
        [string] $Text,
        [string] $Why,
        [string] $Category = 'REQUIRED'
    )

    # Contract: one marker must appear verbatim (ordinal, case-sensitive) in the
    # file's current text.  Missing file, unreadable file or absent marker are
    # all failures -- there is no path from "could not read" to PASS.
    $leaf   = ($RelPath -split '/')[-1]
    $name   = $Why + ' (' + $leaf + ')'
    $full   = Join-Path $script:RootPath ($RelPath.Replace('/', '\'))
    # Early-return style throughout: each decision returns once.
    $content = $null
    try {
        $content = Get-SafeText -FullPath $full
    } catch {
        $content = $null
    }

    if ($null -eq $content) {
        Add-Result -Name $name -Ok $false -Category $Category `
            -Detail ('file missing or unreadable: ' + $RelPath)
        return
    }

    $index = -1
    try {
        $index = $content.IndexOf($Text, [System.StringComparison]::Ordinal)
    } catch {
        $index = -1
    }

    if ($index -ge 0) {
        Add-Result -Name $name -Ok $true -Category $Category `
            -Detail ('marker present: ' + $Text)
        return
    }

    Add-Result -Name $name -Ok $false -Category $Category `
        -Detail ('marker absent: ' + $Text)
}

function Invoke-Git {
    param([string[]] $GitArgs)

    # Returns @{ Code = <exit code, -1 on exception>; Out = <combined output> }
    $code = -1
    $out  = ''

    if ($script:GitExe -eq '') {
        return @{ Code = $code; Out = 'git not available' }
    }

    try {
        $out = (& $script:GitExe -C $script:RootPath @GitArgs 2>&1 | Out-String)
        if ($null -eq $out) {
            $out = ''
        }
        $out = $out.Trim()
        if ($null -eq $LASTEXITCODE) {
            $code = -1
        }
        if ($null -ne $LASTEXITCODE) {
            $code = $LASTEXITCODE
        }
    } catch {
        $code = -1
        $out  = $_.Exception.Message
    }

    return @{ Code = $code; Out = $out }
}

function Find-Python {
    # Returns a usable interpreter path, or ''.  Never throws.
    $found = ''
    try {
        $candidate = Get-Command -Name 'python' -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $candidate) {
            $found = [string]$candidate.Source
            return $found
        }
    } catch {
        $found = ''
    }
    try {
        $venv = Join-Path $script:RootPath '.venv\Scripts\python.exe'
        if ([System.IO.File]::Exists($venv)) {
            return $venv
        }
    } catch {
        $found = ''
    }
    try {
        $candidate = Get-Command -Name 'py' -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $candidate) {
            return [string]$candidate.Source
        }
    } catch {
        $found = ''
    }
    return ''
}

# ==========================================================================
# 0. Header
# ==========================================================================
Write-Host ''
Write-Host '======================================================================'
Write-Host ' Pass-9 fix verification (read-only, fail-closed)'
Write-Host '======================================================================'
Write-Host ('  checkout : ' + $script:RootPath)
Write-Host ('  commit   : ' + $script:Commit)
Write-Host ('  ran at   : ' + (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz'))
Write-Host ''

# ==========================================================================
# 1. The checkout itself.  Nothing further can be verified without it.
# ==========================================================================
$rootIsDir = $false
try {
    $rootIsDir = [System.IO.Directory]::Exists($script:RootPath)
} catch {
    $rootIsDir = $false
}

if (-not $rootIsDir) {
    Write-Host ('  FAIL  checkout not found: ' + $script:RootPath) -ForegroundColor Red
    Write-Host ''
    Write-Host 'VERDICT: FAIL (nothing verified -- the checkout path does not exist)'
    Write-Host ''
    exit 2
}

Write-Host '[1] checkout'
Add-Result -Name 'checkout is a directory' -Ok $true -Detail $script:RootPath
$engineDir = Join-Path $script:RootPath 'engine'
$testsDir  = Join-Path $script:RootPath 'tests'
Add-Result -Name 'engine\ present' -Ok ([System.IO.Directory]::Exists($engineDir)) -Detail $engineDir
Add-Result -Name 'tests\ present'  -Ok ([System.IO.Directory]::Exists($testsDir))  -Detail $testsDir
Write-Host ''

# ==========================================================================
# 2. Commit identity (git).  Missing git is a FAIL unless -AllowNoGit.
# ==========================================================================
Write-Host '[2] commit identity'
try {
    $gitCmd = Get-Command -Name 'git' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $gitCmd) {
        $script:GitExe = [string]$gitCmd.Source
    }
} catch {
    $script:GitExe = ''
}

$gitCategory = 'REQUIRED'
if ($AllowNoGit) {
    $gitCategory = 'ADVISORY'
}
if ($script:GitExe -eq '') {
    Add-Result -Name 'git available' -Ok $false -Category $gitCategory `
        -Detail 'git not on PATH -- commit identity cannot be verified'
}

$repoOk = $false
if ($script:GitExe -ne '') {
    $probe = Invoke-Git -GitArgs @('rev-parse', '--is-inside-work-tree')
    if ($probe.Code -eq 0) {
        if ($probe.Out -eq 'true') {
            $repoOk = $true
        }
    }
    Add-Result -Name 'is a git working tree' -Ok $repoOk -Detail $probe.Out
}

$commitPresent = $false
if ($script:GitExe -ne '') {
    $probe = Invoke-Git -GitArgs @('cat-file', '-e', ($script:Commit + '^{commit}'))
    if ($probe.Code -eq 0) {
        $commitPresent = $true
    }
    $detail = 'object present'
    if (-not $commitPresent) {
        $detail = 'object absent (fetch the branch first)'
    }
    Add-Result -Name 'commit object exists' -Ok $commitPresent -Detail $detail
}

$headOk = $false
if ($script:GitExe -ne '') {
    $probe = Invoke-Git -GitArgs @('rev-parse', 'HEAD')
    Add-Result -Name 'HEAD readable' -Ok ($probe.Code -eq 0) -Detail $probe.Out
    $anc = Invoke-Git -GitArgs @('merge-base', '--is-ancestor', $script:Commit, 'HEAD')
    if ($anc.Code -eq 0) {
        $headOk = $true
    }
    $detail = 'commit is an ancestor of HEAD'
    if (-not $headOk) {
        $detail = 'commit is NOT in HEAD history (checkout is behind or on another branch)'
    }
    Add-Result -Name 'commit in HEAD history' -Ok $headOk -Detail $detail
}
Write-Host ''

# ==========================================================================
# 3. Content markers -- the substantive check.  These are the exact strings
#    the commit introduced; a checkout without them cannot behave like the
#    commit no matter what git says.
# ==========================================================================
Write-Host '[3] corrections present in the files'

Test-Marker -RelPath 'engine/ipo_screening/aggregator_issue_terms.py' `
    -Text 'BID_WINDOW_MAX_DAYS = 31' -Why 'bid-window bound'

Test-Marker -RelPath 'engine/ipo_screening/aggregator_issue_terms.py' `
    -Text 'IDENTITY_WINDOW_UNREADABLE' -Why 'verdict: window unreadable'

Test-Marker -RelPath 'engine/ipo_screening/aggregator_issue_terms.py' `
    -Text 'IDENTITY_UNBOUND' -Why 'verdict: filing unbound'

Test-Marker -RelPath 'engine/ipo_screening/aggregator_issue_terms.py' `
    -Text 'differs from the' -Why 'verdict: both windows stated'

Test-Marker -RelPath 'engine/ipo_screening/extraction/financial_tables.py' `
    -Text 'len(line.split()) <= 6' -Why 'header lines joined (<=6 words)'

Test-Marker -RelPath 'engine/ipo_screening/extraction/financial_tables.py' `
    -Text 'text = " ".join(text.split())' -Why 'header whitespace-normalised'

Test-Marker -RelPath 'engine/tools/ipo_screen.py' `
    -Text '--notice-url' -Why 'one-shot notice flag'

Test-Marker -RelPath 'engine/tools/ipo_screen.py' `
    -Text '--prospectus-url' -Why 'one-shot prospectus flag'

Test-Marker -RelPath 'engine/tools/ipo_screen.py' `
    -Text 'HttpProspectusProvider(mapping)' -Why 'prospectus provider wiring'

Test-Marker -RelPath 'tests/test_aggregator_issue_terms.py' `
    -Text 'IDENTITY_WINDOW_UNREADABLE' -Why 'test: unreadable-window verdict'

Test-Marker -RelPath 'tests/test_aggregator_issue_terms.py' `
    -Text 'IDENTITY_UNBOUND' -Why 'test: unbound verdict'

Test-Marker -RelPath 'tests/test_issue_terms_cli.py' `
    -Text '--prospectus-url' -Why 'test: one-shot CLI flags'

Test-Marker -RelPath 'tests/test_paras_extraction_gaps_20261024.py' `
    -Text 'split_across_lines' -Why 'test: split header read'

$docPath = 'docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md'
Test-Marker -RelPath $docPath -Text 'Revision 12 (2026-10-24)' `
    -Why 'report revision 12 recorded' -Category 'ADVISORY'

$trackerPath = 'handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md'
Test-Marker -RelPath $trackerPath -Text '(revision 14)' `
    -Why 'tracker revision 14 recorded' -Category 'ADVISORY'
Write-Host ''

# ==========================================================================
# 4. The eight files must be byte-identical to the commit (git).  A local edit
#    that kept the markers is still not the commit.
# ==========================================================================
Write-Host '[4] files match the commit byte for byte'
if ($repoOk) {
    $paths = @(
        'docs/investigation/PARAS-INGESTION-FAILURE-2026-10-23.md',
        'engine/ipo_screening/aggregator_issue_terms.py',
        'engine/ipo_screening/extraction/financial_tables.py',
        'engine/tools/ipo_screen.py',
        'handoff/authoritative/IPO_SCREENING_ENGINE_TRACKER.md',
        'tests/test_aggregator_issue_terms.py',
        'tests/test_issue_terms_cli.py',
        'tests/test_paras_extraction_gaps_20261024.py'
    )
    $differing = @()
    $unreadable = @()
    foreach ($p in $paths) {
        $probe = Invoke-Git -GitArgs @('diff', '--quiet', $script:Commit, '--', $p)
        if ($probe.Code -eq 0) {
            continue
        }
        if ($probe.Code -eq 1) {
            $differing += $p
            continue
        }
        $unreadable += $p
    }
    $ok = $false
    if (($differing.Count -eq 0) -and ($unreadable.Count -eq 0)) {
        $ok = $true
    }
    $detail = 'all 8 files identical to the commit'
    if (-not $ok) {
        $detail = 'differ: ' + ($differing -join '; ') + ' unreadable: ' + ($unreadable -join '; ')
    }
    Add-Result -Name 'working tree equals commit (8 files)' -Ok $ok -Detail $detail
}
if (-not $repoOk) {
    Add-Result -Name 'working tree equals commit (8 files)' -Ok $false -Category $gitCategory `
        -Detail 'skipped -- not a git working tree; content markers decided above'
}
Write-Host ''

# ==========================================================================
# 5. Live CLI surface.  Proves the flags are reachable, not just in the source.
# ==========================================================================
Write-Host '[5] CLI surface'
$script:PyExe = Find-Python
$cliCategory = 'REQUIRED'
if ($AllowNoPython) {
    $cliCategory = 'ADVISORY'
}

if ($script:PyExe -eq '') {
    Add-Result -Name 'python available' -Ok $false -Category $cliCategory `
        -Detail 'no python and no .venv found -- CLI not exercised'
    Add-Result -Name 'CLI exposes both one-shot flags' -Ok $false -Category $cliCategory `
        -Detail 'skipped -- no python interpreter'
}

if ($script:PyExe -ne '') {
    $ipoScreen = Join-Path $script:RootPath 'engine\tools\ipo_screen.py'
    $helpText  = ''
    $helpCode  = -1
    try {
        $env:PYTHONPATH = Join-Path $script:RootPath 'engine'
        $helpText = (& $script:PyExe $ipoScreen 'issue-terms' '--help' 2>&1 | Out-String)
        if ($null -eq $helpText) {
            $helpText = ''
        }
        if ($null -ne $LASTEXITCODE) {
            $helpCode = $LASTEXITCODE
        }
    } catch {
        $helpText = $_.Exception.Message
        $helpCode = -1
    }
    $ok = $false
    if ($helpCode -eq 0) {
        if (($helpText.IndexOf('--notice-url', [System.StringComparison]::Ordinal) -ge 0) -and
            ($helpText.IndexOf('--prospectus-url', [System.StringComparison]::Ordinal) -ge 0)) {
            $ok = $true
        }
    }
    $detail = 'issue-terms --help lists --notice-url and --prospectus-url'
    if (-not $ok) {
        $detail = 'help failed or flags absent (exit ' + $helpCode + ')'
    }
    Add-Result -Name 'CLI exposes both one-shot flags' -Ok $ok -Category $cliCategory -Detail $detail
}
Write-Host ''

# ==========================================================================
# 6. Optional: the three suites that exercise this commit (~35 s).
# ==========================================================================
if ($RunTests) {
    Write-Host '[6] pytest suites'
    $ok = $false
    $detail = 'not run -- no python interpreter'
    if ($script:PyExe -ne '') {
        $suiteArgs = @(
            '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
            (Join-Path $script:RootPath 'tests\test_aggregator_issue_terms.py'),
            (Join-Path $script:RootPath 'tests\test_issue_terms_cli.py'),
            (Join-Path $script:RootPath 'tests\test_paras_extraction_gaps_20261024.py')
        )
        $output = ''
        $code   = -1
        Push-Location -LiteralPath $script:RootPath
        try {
            $env:PYTHONPATH = Join-Path $script:RootPath 'engine'
            $output = (& $script:PyExe @suiteArgs 2>&1 | Out-String)
            if ($null -ne $LASTEXITCODE) {
                $code = $LASTEXITCODE
            }
        } catch {
            $output = $_.Exception.Message
            $code   = -1
        }
        Pop-Location
        $tail = ''
        if ($null -ne $output) {
            $lines = ($output.Trim() -split "`r?`n")
            if ($lines.Count -gt 0) {
                $tail = [string]$lines[-1]
            }
        }
        if ($code -eq 0) {
            $ok = $true
        }
        $detail = 'exit ' + $code + ' :: ' + $tail
    }
    Add-Result -Name 'three pass-9 suites pass' -Ok $ok -Detail $detail
    Write-Host ''
}

# ==========================================================================
# Summary and verdict.  Fail closed: an empty run is a failure.
# ==========================================================================
if ($null -eq $script:OldPythonPath) {
    Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
}
if ($null -ne $script:OldPythonPath) {
    $env:PYTHONPATH = $script:OldPythonPath
}

Write-Host '----------------------------------------------------------------------'
Write-Host ('  checks run      : ' + $script:Checks)
Write-Host ('  required passed : ' + ($script:RequiredRun - $script:RequiredFail) + ' / ' + $script:RequiredRun)
Write-Host ('  required failed : ' + $script:RequiredFail)
Write-Host ('  advisories      : ' + $script:AdvisoryWarn + ' warning(s) of ' + $script:AdvisoryRun)
Write-Host ''

if ($script:Checks -eq 0) {
    Write-Host 'VERDICT: FAIL (no check was executed -- the script could not evaluate the checkout)' -ForegroundColor Red
    Write-Host ''
    exit 1
}

if ($script:RequiredFail -gt 0) {
    Write-Host 'VERDICT: FAIL (see FAIL lines above)' -ForegroundColor Red
    Write-Host ''
    exit 1
}

Write-Host 'VERDICT: PASS (all required checks ran and passed)' -ForegroundColor Green
Write-Host ''
exit 0
