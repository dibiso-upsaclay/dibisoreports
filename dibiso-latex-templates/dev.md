# How to publish a new release

Create a new git tag:

```bash
git tag -a v0.1 -m "initial release"
```

Push it to the repository:

```bash
git push --tags
```

A GitHub action will automatically create the release once the new tag is pushed to the repository.

Romain THOMAS 2025
