Read the most recent email thread the user is referring to using `gmail_read_thread` or `gmail_search_messages`. If the user named a sender or subject, search for it first.

Identify the voice context:
- Look at the thread labels and sender domain
- Work/* labels or databricks.com/a3consulting.com domain → Work/Professional voice
- Financial/Real-Estate/* labels or property/lease/tenant subject → Real Estate voice
- Everything else → Personal voice

Delegate to the personal-voice agent to draft a reply in the identified voice.

Create the draft via `gmail_create_draft`:
- Set the correct `to` address (the sender of the last email in the thread)
- Set `subject` with "Re: " prefix if not already present
- Set `threadId` to keep it in the same thread

Confirm with: "Draft created for '[subject]' in Gmail Drafts."

Do not send. Do not summarize the thread back to the user unless they ask.
