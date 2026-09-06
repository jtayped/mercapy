# release process

the repository publishes through pypi trusted publishing. the release workflow
builds the distributions once, stores them as a github artifact, then publishes
that artifact after approval of the protected `pypi` environment.

## repository setup

the pypi `mercapy` project must define a trusted publisher with these values:

| setting | value |
| --- | --- |
| owner | `jtayped` |
| repository | `mercapy` |
| workflow | `python-publish.yml` |
| environment | `pypi` |

github must have a protected `pypi` environment with a required reviewer. the
repository and environment must not contain a `PYPI_API_TOKEN` secret.

the publish job alone receives `id-token: write`. all other workflow jobs receive
`contents: read`. see the [pypa trusted publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
for the identity exchange used by the publish job.

## release checklist

- update `src/mercapy/_version.py`.
- move the pending changelog entries under a version and release date.
- run ruff formatting and linting, strict mypy, pytest with branch coverage, a
  package build, and `twine check`.
- install the wheel into a clean virtual environment outside the repository and
  import `mercapy` there.
- run the readme and migration examples against that installed wheel.
- start the `live smoke` workflow manually. confirm postcode resolution, search,
  product detail, and categories all succeed.
- create a github release. its tag must equal `v` followed by the package version,
  such as `v2.0.1`.
- wait for the release workflow's quality and build jobs.
- review and approve the protected `pypi` deployment.
- confirm the release files, metadata, provenance, and attestations on pypi.

the release workflow rejects a tag that does not match the package version. it
does not rebuild in the privileged publish job.
