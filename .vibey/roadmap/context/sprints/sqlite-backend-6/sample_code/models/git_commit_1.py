class GitCommit(BaseModel):
    sha: str                             # Full 40-char SHA
    message: str
    date: datetime
    author: str

    platform: str                        # claude-code, goose, cursor
    submitted_at: datetime
    completes_tickets: List[str] = []    # Extracted from message

    @classmethod
    def from_git(cls, sha: str, repo_path: Path, platform: str) -> 'GitCommit': ...
