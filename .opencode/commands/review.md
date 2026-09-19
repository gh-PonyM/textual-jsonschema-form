---
description: Review the current changes before a commit for a feature
---
Please review the current changes meaning files changed in git. Here is the git status:

!`git status`

Check:

- Does the changes make sense?
- Are best practices in @docs/development/ followed?
- Do we have sufficient test coverage or should a test be added?
- Are there untracked files that need to be added to git?
- Does the corresponding user story if any is up-to-date with what we did or do we update the user story to reflect what has been done?
- If on a feature branch and git is clean, check the diff to main to review the changes
Also think for UI elements what a user should focus on in a manual test. You might suggest some checks that can be done to finish the issue, add them as acceptance criteria to the user story and ask the user if the components behave as expected.

At the end, we want to commit all relevant files and formulate a good commit message. use conventional commmit style.
$1
