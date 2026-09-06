# Release checklist

## One-time setup before 2.0.0

- In the PyPI `mercapy` project's publishing settings, add a trusted publisher
  for owner `jtayped`, repository `mercapy`, workflow `python-publish.yml`, and
  environment `pypi`.
- In GitHub, create the `pypi` environment and add the required manual reviewers.
- Remove the old `PYPI_API_TOKEN` repository or environment secret.

Use the [PyPA trusted-publishing workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
when configuring PyPI and GitHub.

The publish job receives `id-token: write`; every other job and workflow receives
only `contents: read`. The publish job runs on GitHub-hosted Ubuntu, downloads the
already-built distributions, and invokes the PyPA publisher with its default
attestations.

## Every release

- Update `src/mercapy/_version.py` and `CHANGELOG.md`.
- Run Ruff formatting and linting, strict mypy, pytest with branch coverage,
  package build, and `twine check`.
- Build the wheel and install it into a clean virtual environment. Run the README
  migration examples against that installed wheel outside the repository.
- Manually run the `Live smoke` workflow and confirm postcode resolution, search,
  product detail, and categories succeed.
- Create and publish a GitHub release whose tag is exactly `v` followed by the
  package version, for example `v2.0.0`.
- Approve the protected `pypi` environment after the release workflow's quality
  and build jobs pass.
- Confirm the PyPI files, metadata, provenance, and default attestations.

The release workflow builds once. It rejects a release tag that does not match
the package version.
