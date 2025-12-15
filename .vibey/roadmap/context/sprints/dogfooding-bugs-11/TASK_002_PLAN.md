# Task Plan: complete command does not accept ULID task IDs

## Bug ID
01KC8FTXZB94YTTB79VPK3SNRM

## Problem Statement
The `roadmap complete` command rejects ULID task IDs with error 'Cannot find track or sprint with ID'. It expects legacy slug format. Should accept both formats.

## Root Cause Analysis
Same as bug 01KCH7051YHKTSVQ21JRB81VM9 - the complete command uses `-task-` string detection.

## Files to Modify
Same as Sprint 10 ULID Support Task 001.

## Implementation Steps
This is a duplicate of 01KCH7051YHKTSVQ21JRB81VM9. The fix implemented for that bug will resolve this one.

## Resolution
**DUPLICATE** - Close as duplicate of 01KCH7051YHKTSVQ21JRB81VM9

When fixing the Sprint 10 bug, verify this specific error case is resolved:
- `vibey roadmap complete 01KC8FTXZB94YTTB79VPK3SNRM` should work

## Estimated Complexity
N/A - Duplicate
