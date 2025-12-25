



should we refactor so the model reads from yaml but writes to the database? or should we delete the yaml after the databse is rebuilt? should we integrate the database build/dump into the git process so the database is rebuilt on git pull, then the local yaml is deleted, then git commit the yaml is dumped for the commit and deleted again after the database is rebuilt?

how is vibey managing the assets specitic to an agent platform? is the mcp server automation fully integated into the vibey deploy command for each platform?

user flow
- brew install the CLI utility
- vibey init in the new project










1