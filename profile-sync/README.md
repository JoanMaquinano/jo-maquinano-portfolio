# Profile sync

This folder supports a review-first portfolio update workflow.

Run **Profile sync** manually from the repository's **Actions** tab. The workflow:

1. Fetches public GitHub profile, README, and repository metadata.
2. Reads the manually maintained `linkedin-profile.json` file.
3. Creates a proposed snapshot and a Markdown report.
4. Opens a pull request for review.

The workflow does not run on a schedule and does not publish changes directly. The site changes only after the proposed pull request is reviewed and merged.

LinkedIn does not provide dependable unauthenticated profile access for this workflow, so update `linkedin-profile.json` when your LinkedIn profile changes before running the sync.
