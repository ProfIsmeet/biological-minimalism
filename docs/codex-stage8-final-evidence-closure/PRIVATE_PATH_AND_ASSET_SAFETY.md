# Private-path and asset safety

## Asset handling

The research archive and model checkpoint stayed outside the isolated worktree. They were read through the application's supported environment configuration and were never copied, staged, or committed. Reports use only the portable labels `owner-provided local PPG-DaLiA archive` and `owner-provided local Model B checkpoint`.

## Scans

The staged diff and final branch delta were scanned for macOS, Linux, and Windows user-home absolute path patterns. Generated runtime evidence was sanitized before commit, and the manifest verifier independently rejects private absolute paths. Result: no private absolute path committed.

The staged-name and object-size scan found no dataset archive, model checkpoint, browser profile/cache, dependency directory, or unexpected large file. The complete canonical PNG set totals 20,015,640 bytes; the largest single file is 1,189,542 bytes. These are expected review artifacts, not research assets.

Dependency manifests and lockfiles are unchanged from the verified source SHA.
