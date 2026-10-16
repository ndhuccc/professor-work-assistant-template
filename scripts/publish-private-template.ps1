param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9-]+$')][string]$Owner,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.-]+$')][string]$Name,
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$repository = "$Owner/$Name"

Write-Output "Plan: create $repository as PRIVATE, upload this template, enable Template repository."
Write-Output "Source: $taskRoot"
if (-not $Execute) {
    Write-Output 'Preview only. Add -Execute after reviewing the source files and target.'
    exit 0
}

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program failed (exit $LASTEXITCODE). Stop; inspect the last completed step before retrying."
    }
}

Get-Command git, gh, python -ErrorAction Stop | Out-Null
Push-Location -LiteralPath $taskRoot
try {
    $login = & gh api user --jq '.login'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot reach authenticated GitHub. Run gh auth login in this terminal first.' }
    if ($login.Trim() -cne $Owner) { throw "Expected personal account $Owner, but gh is authenticated as $login. No repository created." }
    Invoke-Checked -Program python -Arguments @('scripts/doctor.py', '--template')

    if (-not (Test-Path -LiteralPath '.git')) {
        Invoke-Checked -Program git -Arguments @('init', '--initial-branch=main')
        Invoke-Checked -Program git -Arguments @('add', '--', 'AGENTS.md', 'README.md', 'LICENSE', '.agents', '.github', '.gitignore', '.gitattributes', 'config', 'docs', 'examples', 'scripts', 'templates', 'tests')
        Invoke-Checked -Program git -Arguments @('commit', '-m', 'Create professor work assistant template')
    }
    $changes = & git status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Working tree must be clean. Review and commit intended files first; local/private files must remain ignored.' }
    $branch = & git branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch.Trim() -cne 'main') { throw 'Expected main branch. Stop and review the local branch.' }
    $remotes = & git remote
    if ($LASTEXITCODE -ne 0 -or $remotes) { throw 'This first-publication script requires no existing remotes; stop rather than alter an existing repository.' }

    # Explicit --private is mandatory; this script never changes visibility.
    Invoke-Checked -Program gh -Arguments @('repo', 'create', $repository, '--private', '--source', $taskRoot, '--remote', 'origin', '--push', '--description', 'Portable professor assistant workflows with AGENTS.md and reusable skills')
    Invoke-Checked -Program gh -Arguments @('repo', 'edit', $repository, '--default-branch', 'main', '--template')
    $raw = & gh api "repos/$repository"
    if ($LASTEXITCODE -ne 0) { throw 'Repository operation finished but read-back failed. Verify before retrying.' }
    $metadata = $raw | ConvertFrom-Json
    if (-not $metadata.private -or -not $metadata.is_template -or $metadata.default_branch -cne 'main') {
        throw 'Read-back did not confirm private=true, is_template=true, default_branch=main.'
    }
    $localHead = & git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read local commit.' }
    $remoteHead = & gh api "repos/$repository/git/ref/heads/main" --jq '.object.sha'
    if ($LASTEXITCODE -ne 0 -or $remoteHead.Trim() -cne $localHead.Trim()) { throw 'Remote commit does not match local HEAD; inspect before retrying.' }
    Write-Output "VERIFIED: $($metadata.html_url) (Private, Template repository, main, matching commit)"
}
finally {
    Pop-Location
}
